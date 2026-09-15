"""
Deterministic Baseline Change Detector.

Implements multi-spectral difference, adaptive Otsu thresholding,
morphological filtering, and PostGIS/GeoJSON polygon vectorization.

IMPORTANT SCIENTIFIC LABELING:
Output is clearly tagged as:
"Baseline / Demo Result"
"Never present baseline output as trained AI performance."
"""

from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from rasterio.transform import Affine
from shapely.geometry import Polygon, mapping

from app.core.logging import logger
from app.ml.base import BaseChangeDetector, ChangeDetectionResult, ChangeRegionFeature
from app.ml.classifier import HierarchicalChangeClassifier


class BaselineChangeDetector(BaseChangeDetector):
    """
    Deterministic spectral difference change detector.
    Serves as an explainable baseline before deep learning Siamese models.
    """

    def __init__(
        self,
        model_name: str = "Spectral Baseline Difference",
        model_version: str = "0.9.0",
        min_region_pixels: int = 6,
        morphological_kernel_size: int = 3,
    ):
        super().__init__(model_name=model_name, model_version=model_version)
        self.min_region_pixels = min_region_pixels
        self.classifier = HierarchicalChangeClassifier(model_version=model_version)
        self.kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (morphological_kernel_size, morphological_kernel_size)
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
        Execute spectral difference change detection.

        Args:
            image1: Reference image tensor (C, H, W) in float32 [0, 1]
            image2: Target image tensor (C, H, W) in float32 [0, 1]
            spatial_transform: Affine raster geotransform
            crs: CRS string (e.g. 'EPSG:32646')
            resolution_m: Ground sampling distance in meters
            confidence_threshold: Threshold cutoff (0.0 to 1.0)
        """
        c, h, w = image1.shape
        total_pixels = h * w
        pixel_area_m2 = resolution_m * resolution_m
        total_area_m2 = total_pixels * pixel_area_m2
        total_area_km2 = total_area_m2 / 1_000_000.0

        # 1. Multi-spectral Euclidean difference magnitude
        diff_sq = np.zeros((h, w), dtype=np.float32)
        for i in range(c):
            diff_sq += (image1[i] - image2[i]) ** 2
        diff_mag = np.sqrt(diff_sq / max(1, c))

        # 2. Probability Map [0.0, 1.0]
        prob_map = np.clip(diff_mag, 0.0, 1.0).astype(np.float32)

        # 3. Thresholding
        diff_u8 = (prob_map * 255.0).astype(np.uint8)

        if confidence_threshold > 0.0:
            threshold_val = int(confidence_threshold * 255)
            _, raw_mask = cv2.threshold(diff_u8, threshold_val, 255, cv2.THRESH_BINARY)
        else:
            # Adaptive Otsu thresholding
            otsu_val, raw_mask = cv2.threshold(diff_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            threshold_val = otsu_val

        # 4. Morphological Filtering (Opening to remove speckle, Closing to fill holes)
        opened = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, self.kernel)
        filtered_mask = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, self.kernel)

        # 5. Connected Component Area Filtering & Vectorization
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            filtered_mask, connectivity=8
        )

        clean_mask = np.zeros_like(filtered_mask)
        regions: List[ChangeRegionFeature] = []
        region_idx = 1

        for label_id in range(1, num_labels):
            area_px = stats[label_id, cv2.CC_STAT_AREA]
            if area_px < self.min_region_pixels:
                continue

            # Keep valid region in binary mask
            clean_mask[labels == label_id] = 255

            # Find contours for this specific region
            component_mask = (labels == label_id).astype(np.uint8) * 255
            contours, _ = cv2.findContours(
                component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for cnt in contours:
                if len(cnt) < 3:
                    continue

                # Simplify polygon
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

                # Close polygon ring
                if coords[0] != coords[-1]:
                    coords.append(coords[0])

                poly = Polygon(coords)
                if not poly.is_valid or poly.area <= 0:
                    continue

                # Centroid
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

                # L-1 FIX: spectral_difference = actual spectral diff magnitude (independent of confidence)
                # Use diff_mag (pre-normalization magnitude) for a physically meaningful metric.
                mean_spectral_diff = float(np.mean(diff_mag[poly_mask > 0])) if np.any(poly_mask > 0) else 0.0

                evidence = self.classifier.extract_evidence(
                    t1_patch=image1,
                    t2_patch=image2,
                    polygon_mask=poly_mask,
                    poly_geom=poly,
                    resolution_m=resolution_m,
                )
                decision = self.classifier.classify(evidence)

                # Severity level based on area and spectral difference
                if region_area_m2 > 100_000 or mean_conf > 0.85:
                    sev = "HIGH"
                elif region_area_m2 > 20_000 or mean_conf > 0.65:
                    sev = "MEDIUM"
                else:
                    sev = "LOW"

                min_x, min_y, max_x, max_y = poly.bounds

                # H-4 FIX: Compute perimeter in pixel space then scale by resolution_m.
                # poly.length returns geographic-unit length (degrees for EPSG:4326),
                # so we use the contour arc-length instead.
                perim_px = cv2.arcLength(cnt, True)
                perimeter_m_val = float(perim_px * resolution_m)

                feature = ChangeRegionFeature(
                    region_index=region_idx,
                    geojson_geometry=mapping(poly),
                    centroid_lat=round(cent_geo_y, 6),
                    centroid_lon=round(cent_geo_x, 6),
                    area_m2=round(region_area_m2, 2),
                    area_km2=round(region_area_km2, 4),
                    perimeter_m=round(perimeter_m_val, 2),      # H-4: pixel-space perimeter × GSD
                    bbox=[round(min_x, 6), round(min_y, 6), round(max_x, 6), round(max_y, 6)],
                    mean_confidence=round(mean_conf, 3),
                    spectral_difference=round(mean_spectral_diff, 3),  # L-1: actual diff magnitude
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
            label="Baseline / Demo Result",
            disclaimer="Generated using deterministic spectral differencing baseline. Never present baseline output as trained AI performance.",
            metadata={
                "threshold_applied": round(float(threshold_val) / 255.0, 3),
                "min_region_pixels": self.min_region_pixels,
                "crs": crs,
                "resolution_m": resolution_m,
            },
        )
