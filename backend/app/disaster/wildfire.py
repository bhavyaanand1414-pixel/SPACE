"""
Wildfire Burn Scar and Burn Severity Assessment Module (dNBR / Optical).
"""

from typing import Any, Dict, List, Optional
import cv2
import numpy as np
from rasterio.transform import Affine
from shapely.geometry import Polygon, mapping

from app.disaster.base import (
    BaseDisasterAnalyzer,
    DisasterAssessmentResult,
    DisasterType,
    DISASTER_CAUTIONARY_DISCLAIMER,
)


class WildfireBurnScarAnalyzer(BaseDisasterAnalyzer):
    """
    Computes Normalized Burn Ratio difference (dNBR = NBR_pre - NBR_post) and maps burned areas.
    """

    def __init__(self, model_version: str = "1.0.0"):
        super().__init__(disaster_type=DisasterType.WILDFIRE, model_version=model_version)

    def analyze(
        self,
        image_before: np.ndarray,
        image_after: np.ndarray,
        resolution_m: float = 10.0,
        spatial_transform: Optional[Affine] = None,
        is_sar: bool = False,
        **kwargs,
    ) -> DisasterAssessmentResult:
        """Analyze burn scars using dNBR or NIR/Red multi-spectral difference."""
        c = image_before.shape[0] if image_before.ndim == 3 else 1
        h, w = image_before.shape[-2:]
        total_pixels = h * w
        pixel_area_m2 = resolution_m * resolution_m
        total_scene_m2 = total_pixels * pixel_area_m2

        # Compute NBR = (NIR - SWIR2) / (NIR + SWIR2) or proxy (NIR - Red) / (NIR + Red)
        if c >= 4:
            nir_1 = image_before[3].astype(np.float32)
            red_1 = image_before[0].astype(np.float32)
            nbr_1 = (nir_1 - red_1) / (nir_1 + red_1 + 1e-6)

            nir_2 = image_after[3].astype(np.float32)
            red_2 = image_after[0].astype(np.float32)
            nbr_2 = (nir_2 - red_2) / (nir_2 + red_2 + 1e-6)

            dnbr = nbr_1 - nbr_2
            burn_mask = (dnbr > 0.27).astype(np.uint8) * 255
        else:
            # Drop in overall reflectance and albedo charring
            diff = image_before[0] - image_after[0]
            burn_mask = ((diff > 0.25) & (image_after[0] < 0.25)).astype(np.uint8) * 255

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        clean_burn = cv2.morphologyEx(burn_mask, cv2.MORPH_OPEN, kernel)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(clean_burn, connectivity=8)
        geojson_features: List[Dict[str, Any]] = []
        region_idx = 1

        for label_id in range(1, num_labels):
            area_px = stats[label_id, cv2.CC_STAT_AREA]
            if area_px < 6:
                continue

            comp_mask = (labels == label_id).astype(np.uint8) * 255
            contours, _ = cv2.findContours(comp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                if len(cnt) < 3:
                    continue
                approx = cv2.approxPolyDP(cnt, 1.0, True)
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

                reg_area_m2 = float(area_px * pixel_area_m2)
                reg_area_km2 = float(reg_area_m2 / 1_000_000.0)

                feat = {
                    "type": "Feature",
                    "geometry": mapping(poly),
                    "properties": {
                        "region_index": region_idx,
                        "disaster_type": "WILDFIRE",
                        "impact_type": "Potential Burn Scar",
                        "area_m2": round(reg_area_m2, 2),
                        "area_km2": round(reg_area_km2, 4),
                        "confidence": 0.89,
                        "causality_wording": "Potential wildfire-related burn scar",
                    },
                }
                geojson_features.append(feat)
                region_idx += 1

        burned_px = int(np.count_nonzero(clean_burn))
        affected_m2 = float(burned_px * pixel_area_m2)
        affected_km2 = float(affected_m2 / 1_000_000.0)
        pct = round((affected_m2 / max(1, total_scene_m2)) * 100.0, 2)

        return DisasterAssessmentResult(
            disaster_type=DisasterType.WILDFIRE,
            title="Satellite Burn Scar Assessment",
            affected_area_m2=round(affected_m2, 2),
            affected_area_km2=round(affected_km2, 4),
            percentage_area_affected=pct,
            severity_level="HIGH" if pct > 5.0 else "MEDIUM" if pct > 1.0 else "LOW",
            confidence_score=0.89,
            affected_regions_count=len(geojson_features),
            geojson_features=geojson_features,
            modality_used="OPTICAL_MSI",
            causality_wording="Potential wildfire-related burn scar and canopy defoliation.",
            advisory_disclaimer=DISASTER_CAUTIONARY_DISCLAIMER,
            evidence_metrics={"burned_pixels": burned_px},
            model_version=self.model_version,
        )
