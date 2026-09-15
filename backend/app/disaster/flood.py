"""
Flood Inundation and Water Surface Expansion Analysis Module.

Supports:
1. Optical MSI Multi-Spectral Inundation Mapping (NDWI / Green-NIR)
2. Sentinel-1 SAR Backscatter Drop Inundation Mapping (Specular Reflection)
"""

from typing import Any, Dict, List, Optional, Tuple
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


class FloodInundationAnalyzer(BaseDisasterAnalyzer):
    """
    Analyzes pre-event and post-event satellite imagery to map new flood inundation extents.
    """

    def __init__(self, model_version: str = "1.0.0"):
        super().__init__(disaster_type=DisasterType.FLOOD, model_version=model_version)

    @staticmethod
    def _extract_optical_water_mask(image: np.ndarray) -> np.ndarray:
        """Extract binary water mask from optical multi-spectral/RGB image."""
        c = image.shape[0] if image.ndim == 3 else 1
        h, w = image.shape[-2:]

        if c >= 4:
            # Band 1: Green, Band 3: NIR
            green = image[1].astype(np.float32)
            nir = image[3].astype(np.float32)
            ndwi = (green - nir) / (green + nir + 1e-6)
            water_mask = (ndwi > 0.05).astype(np.uint8) * 255
        elif c == 3:
            # RGB heuristic: two paths
            # Path 1 (clear water): High blue relative to red + low brightness
            # Path 2 (turbid/sediment water): Low brightness + low colour saturation
            # Brahmaputra/Ganga flood water is typically yellowish-brown and fails Path 1 alone.
            red = image[0].astype(np.float32)
            green = image[1].astype(np.float32)
            blue = image[2].astype(np.float32)
            brightness = (red + green + blue) / 3.0
            color_range = np.maximum(np.maximum(red, green), blue) - np.minimum(np.minimum(red, green), blue)
            clear_water = (blue > red) & (brightness < 0.40)
            turbid_water = (brightness < 0.30) & (color_range < 0.20)
            water_mask = (clear_water | turbid_water).astype(np.uint8) * 255
        else:
            # Grayscale dark threshold
            water_mask = (image[0] < 0.25).astype(np.uint8) * 255

        # Morphological filtering to remove small noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        clean_mask = cv2.morphologyEx(water_mask, cv2.MORPH_OPEN, kernel)
        return clean_mask

    @staticmethod
    def _extract_sar_water_mask(sar_image: np.ndarray, threshold_db: float = -15.0) -> np.ndarray:
        """
        Extract water mask from Sentinel-1 SAR backscatter amplitude.
        Smooth water causes specular reflection away from radar sensor, appearing very dark.
        """
        sar_band = sar_image[0] if sar_image.ndim == 3 else sar_image
        # Normalized float in [0, 1] or raw dB
        if np.max(sar_band) <= 1.0:
            water_mask = (sar_band < 0.20).astype(np.uint8) * 255
        else:
            water_mask = (sar_band < threshold_db).astype(np.uint8) * 255

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        return cv2.morphologyEx(water_mask, cv2.MORPH_OPEN, kernel)

    def analyze(
        self,
        image_before: np.ndarray,
        image_after: np.ndarray,
        resolution_m: float = 10.0,
        spatial_transform: Optional[Affine] = None,
        is_sar: bool = False,
        **kwargs,
    ) -> DisasterAssessmentResult:
        """
        Map new flood inundation by subtracting baseline water extent from post-event water extent.
        """
        h, w = image_before.shape[-2:]
        total_pixels = h * w
        pixel_area_m2 = resolution_m * resolution_m
        total_scene_area_m2 = total_pixels * pixel_area_m2

        # 1. Extract Water Extents
        if is_sar:
            modality = "SAR_SENTINEL1"
            water_t1 = self._extract_sar_water_mask(image_before)
            water_t2 = self._extract_sar_water_mask(image_after)
        else:
            modality = "OPTICAL_MSI"
            water_t1 = self._extract_optical_water_mask(image_before)
            water_t2 = self._extract_optical_water_mask(image_after)

        # 2. Isolate New Inundation = Water(T2) AND NOT Water(T1)
        new_flood_mask = cv2.bitwise_and(water_t2, cv2.bitwise_not(water_t1))

        # Morphological close to bridge contiguous inundation zones
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        clean_flood = cv2.morphologyEx(new_flood_mask, cv2.MORPH_CLOSE, kernel)

        # 3. Vectorize Flood Polygons
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(clean_flood, connectivity=8)

        geojson_features: List[Dict[str, Any]] = []
        region_idx = 1

        for label_id in range(1, num_labels):
            area_px = stats[label_id, cv2.CC_STAT_AREA]
            if area_px < 8:  # Minimum 800 m²
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
                        "disaster_type": "FLOOD",
                        "impact_type": "Potential Flood Inundation",
                        "area_m2": round(reg_area_m2, 2),
                        "area_km2": round(reg_area_km2, 4),
                        "confidence": 0.91,
                        "causality_wording": "Potential flood inundation & surface water surge",
                    },
                }
                geojson_features.append(feat)
                region_idx += 1

        total_flood_px = int(np.count_nonzero(clean_flood))
        affected_area_m2 = float(total_flood_px * pixel_area_m2)
        affected_area_km2 = float(affected_area_m2 / 1_000_000.0)
        pct_affected = round((affected_area_m2 / max(1, total_scene_area_m2)) * 100.0, 2)

        if pct_affected > 15.0 or affected_area_km2 > 10.0:
            severity = "CRITICAL"
        elif pct_affected > 5.0 or affected_area_km2 > 2.0:
            severity = "HIGH"
        elif pct_affected > 1.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return DisasterAssessmentResult(
            disaster_type=DisasterType.FLOOD,
            title="Satellite Inundation Assessment",
            affected_area_m2=round(affected_area_m2, 2),
            affected_area_km2=round(affected_area_km2, 4),
            percentage_area_affected=pct_affected,
            severity_level=severity,
            confidence_score=0.91,
            affected_regions_count=len(geojson_features),
            geojson_features=geojson_features,
            modality_used=modality,
            causality_wording="Potential flood-related inundation & surface water surge.",
            advisory_disclaimer=DISASTER_CAUTIONARY_DISCLAIMER,
            evidence_metrics={
                "baseline_water_pixels": int(np.count_nonzero(water_t1)),
                "post_event_water_pixels": int(np.count_nonzero(water_t2)),
                "new_inundation_pixels": total_flood_px,
                "modality": modality,
                "sensor_resolution_m": resolution_m,
            },
            model_version=self.model_version,
        )
