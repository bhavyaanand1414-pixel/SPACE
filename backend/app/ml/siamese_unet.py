"""
Backend Integration Wrapper for Siamese U-Net Deep Learning Change Detector.
"""

from typing import Any, Dict, List, Optional
import cv2
import numpy as np
from rasterio.transform import Affine
from shapely.geometry import Polygon, mapping

from app.core.config import settings
from app.core.logging import logger
from app.ml.base import BaseChangeDetector, ChangeDetectionResult, ChangeRegionFeature
from app.ml.classifier import HierarchicalChangeClassifier
from ml.inference.predictor import SiamesePredictor


class SiameseUNetDetector(BaseChangeDetector):
    """
    Deep learning Siamese U-Net Change Detector implementing BaseChangeDetector.
    """

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        confidence_threshold: float = 0.5,
        min_region_pixels: int = 6,
        base_filters: int = 32,
    ):
        super().__init__(
            model_name="Siamese U-Net Deep Learning",
            model_version="1.0.0",
        )
        self.min_region_pixels = min_region_pixels
        self.classifier = HierarchicalChangeClassifier(model_version=self.model_version)
        self.predictor = SiamesePredictor(
            checkpoint_path=checkpoint_path or settings.MODEL_CHECKPOINT_DIR + "/siamese_unet_best.pt",
            confidence_threshold=confidence_threshold,
            base_filters=base_filters,
        )

    def detect_change(
        self,
        image1: np.ndarray,
        image2: np.ndarray,
        spatial_transform: Optional[Affine] = None,
        crs: Optional[str] = None,
        resolution_m: float = 10.0,
        confidence_threshold: float = 0.5,
        **kwargs,
    ) -> ChangeDetectionResult:
        """
        Execute deep-learning Siamese change detection on preprocessed tensors.
        """
        c, h, w = image1.shape
        total_pixels = h * w
        pixel_area_m2 = resolution_m * resolution_m
        total_area_m2 = total_pixels * pixel_area_m2
        total_area_km2 = total_area_m2 / 1_000_000.0

        # Run Siamese U-Net neural network
        prob_map, raw_mask = self.predictor.predict(
            image1, image2, threshold=confidence_threshold
        )

        # Morphological clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        clean_mask = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel)
        clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_CLOSE, kernel)

        # Connected components and vectorization
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            clean_mask, connectivity=8
        )

        regions: List[ChangeRegionFeature] = []
        region_idx = 1

        for label_id in range(1, num_labels):
            area_px = stats[label_id, cv2.CC_STAT_AREA]
            if area_px < self.min_region_pixels:
                clean_mask[labels == label_id] = 0
                continue

            comp_mask = (labels == label_id).astype(np.uint8) * 255
            contours, _ = cv2.findContours(
                comp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for cnt in contours:
                if len(cnt) < 3:
                    continue

                epsilon = 0.01 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, max(0.5, epsilon), True)
                if len(approx) < 3:
                    continue

                coords = []
                for pt in approx:
                    px_x, px_y = float(pt[0][0]), float(pt[0][1])
                    if spatial_transform is not None:
                        geo_x = spatial_transform.c + px_x * spatial_transform.a + px_y * spatial_transform.b
                        geo_y = spatial_transform.f + px_x * spatial_transform.d + px_y * spatial_transform.e
                    else:
                        geo_x, geo_y = px_x * resolution_m, px_y * resolution_m
                    coords.append((geo_x, geo_y))

                if coords[0] != coords[-1]:
                    coords.append(coords[0])

                poly = Polygon(coords)
                if not poly.is_valid or poly.area <= 0:
                    continue

                cent_px_x = float(centroids[label_id][0])
                cent_px_y = float(centroids[label_id][1])
                if spatial_transform is not None:
                    cent_geo_x = spatial_transform.c + cent_px_x * spatial_transform.a + cent_px_y * spatial_transform.b
                    cent_geo_y = spatial_transform.f + cent_px_x * spatial_transform.d + cent_px_y * spatial_transform.e
                else:
                    cent_geo_x, cent_geo_y = cent_px_x * resolution_m, cent_px_y * resolution_m

                region_area_m2 = float(area_px * pixel_area_m2)
                region_area_km2 = float(region_area_m2 / 1_000_000.0)

                poly_mask = (labels == label_id).astype(np.uint8)
                mean_conf = float(np.mean(prob_map[poly_mask > 0])) if np.any(poly_mask > 0) else 0.8
                evidence = self.classifier.extract_evidence(
                    t1_patch=image1,
                    t2_patch=image2,
                    polygon_mask=poly_mask,
                    poly_geom=poly,
                    resolution_m=resolution_m,
                )
                decision = self.classifier.classify(evidence)

                if region_area_m2 > 100_000 or mean_conf > 0.85:
                    sev = "HIGH"
                elif region_area_m2 > 20_000 or mean_conf > 0.65:
                    sev = "MEDIUM"
                else:
                    sev = "LOW"

                min_x, min_y, max_x, max_y = poly.bounds

                feature = ChangeRegionFeature(
                    region_index=region_idx,
                    geojson_geometry=mapping(poly),
                    centroid_lat=round(cent_geo_y, 6),
                    centroid_lon=round(cent_geo_x, 6),
                    area_m2=round(region_area_m2, 2),
                    area_km2=round(region_area_km2, 4),
                    perimeter_m=round(float(poly.length), 2),
                    bbox=[round(min_x, 6), round(min_y, 6), round(max_x, 6), round(max_y, 6)],
                    mean_confidence=round(mean_conf, 3),
                    spectral_difference=round(mean_conf, 3),
                    category=decision.category,
                    subtype=decision.subcategory,
                    subcategory=decision.subcategory,
                    severity_level=sev,
                    evidence=decision.evidence,
                    model_version=self.model_version,
                )
                regions.append(feature)
                region_idx += 1

        total_changed_px = int(np.count_nonzero(clean_mask))
        total_changed_m2 = float(total_changed_px * pixel_area_m2)
        total_changed_km2 = float(total_changed_m2 / 1_000_000.0)
        pct_changed = round((total_changed_px / max(1, total_pixels)) * 100.0, 2)

        return ChangeDetectionResult(
            change_mask=clean_mask,
            probability_map=prob_map,
            total_pixels_changed=total_changed_px,
            total_area_m2=round(total_area_m2, 2),
            total_area_km2=round(total_area_km2, 4),
            total_area_changed_m2=round(total_changed_m2, 2),
            total_area_changed_km2=round(total_changed_km2, 4),
            percentage_changed=pct_changed,
            region_count=len(regions),
            regions=regions,
            model_name=self.model_name,
            model_version=self.model_version,
            label="Trained Siamese U-Net Neural Network Result",
            disclaimer="Inference executed using deep learning Siamese U-Net weight-sharing architecture.",
            metadata={
                "device": str(self.predictor.device),
                "threshold_applied": confidence_threshold,
                "crs": crs,
                "resolution_m": resolution_m,
            },
        )
