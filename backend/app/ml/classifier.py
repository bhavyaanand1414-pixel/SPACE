"""
Hierarchical Change Classifier grounded in Remote Sensing and Geometric ML/GIS Evidence.

Taxonomy Hierarchy:
  • HUMAN:
      Building, Road, Construction, Bridge, Industrial, Mining, Urban expansion, Other
  • NATURAL:
      Vegetation, Water, Soil, Terrain, River, Other
  • DISASTER:
      Flood, Earthquake, Cyclone, Landslide, Wildfire, Other
  • ATMOSPHERIC:
      Cloud, Shadow, Haze, Artifact
  • UNKNOWN:
      Unknown

STRICT PRINCIPLE:
Do not use the LLM as the image classifier.
All classifications are computed deterministically from multispectral indices and morphological GIS features.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
from shapely.geometry import Polygon


@dataclass
class ClassificationEvidence:
    """Quantitative GIS and Spectral Evidence."""
    # NDVI / NDWI — available only when NIR band is present (c >= 4)
    delta_ndvi: Optional[float] = None          # Vegetation shift (NIR - Red) / (NIR + Red)
    delta_ndwi: Optional[float] = None          # Water shift (Green - NIR) / (Green + NIR)
    # C-3 FIX: Standard NDBI requires SWIR band. Without SWIR we compute a
    # Custom Red-NIR Index (RNI) instead. It is NOT presented as NDBI.
    delta_rni: Optional[float] = None           # Red-NIR Index (custom): (Red - NIR) / (Red + NIR + ε)
    has_swir: bool = False                      # True only if SWIR band (band 5+) is present
    delta_ndbi: Optional[float] = None          # True NDBI: available only when has_swir=True
    delta_brightness: float = 0.0    # Mean radiometric brightness change
    mean_t1_brightness: float = 0.0
    mean_t2_brightness: float = 0.0
    elongation: float = 1.0          # Length-to-width aspect ratio
    compactness: float = 1.0         # 4 * pi * Area / Perimeter^2 (1.0 = perfect circle)
    rectangularity: float = 0.0      # Area / BoundingBox Area
    area_m2: float = 0.0
    perimeter_m: float = 0.0
    spectral_variance: float = 0.0
    rule_fired: str = "DEFAULT"
    spectral_indices_available: bool = True      # False for RGB-only inputs


@dataclass
class ClassificationDecision:
    """Final hierarchical classification decision with full evidence audit trail."""
    category: str                    # HUMAN, NATURAL, DISASTER, ATMOSPHERIC, UNKNOWN
    subcategory: str                 # Building, Road, Vegetation, Flood, etc.
    confidence: float                # Confidence score in [0.0, 1.0]
    evidence: Dict[str, Any]         # Extracted quantitative evidence dictionary
    model_version: str = "1.0.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HierarchicalChangeClassifier:
    """
    Modular remote-sensing change classifier based on spectral indices & morphological evidence.
    """

    VALID_TAXONOMY = {
        "HUMAN": [
            "Building", "Road", "Construction", "Bridge", "Industrial",
            "Mining", "Urban expansion", "Other",
        ],
        "NATURAL": [
            "Vegetation", "Water", "Soil", "Terrain", "River", "Other",
        ],
        "DISASTER": [
            "Flood", "Earthquake", "Cyclone", "Landslide", "Wildfire", "Other",
        ],
        "ATMOSPHERIC": [
            "Cloud", "Shadow", "Haze", "Artifact",
        ],
        "UNKNOWN": [
            "Unknown",
        ],
    }

    def __init__(self, model_version: str = "1.0.0"):
        self.model_version = model_version

    def extract_evidence(
        self,
        t1_patch: np.ndarray,
        t2_patch: np.ndarray,
        polygon_mask: np.ndarray,
        poly_geom: Optional[Polygon] = None,
        resolution_m: float = 10.0,
    ) -> ClassificationEvidence:
        """
        Extract quantitative remote sensing indices and geometric features within the polygon.
        """
        # Ensure (C, H, W)
        c = t1_patch.shape[0] if t1_patch.ndim == 3 else 1
        mask_bool = polygon_mask > 0

        if not np.any(mask_bool):
            return ClassificationEvidence()

        # Mean pixel values in T1 and T2
        if t1_patch.ndim == 3:
            t1_masked = [t1_patch[i][mask_bool] for i in range(c)]
            t2_masked = [t2_patch[i][mask_bool] for i in range(c)]

            t1_mean_bands = [float(np.mean(b)) if len(b) > 0 else 0.0 for b in t1_masked]
            t2_mean_bands = [float(np.mean(b)) if len(b) > 0 else 0.0 for b in t2_masked]

                    # Approximate RGB / NIR bands (Red=0, Green=1, Blue=2)
            red_1 = t1_mean_bands[0]
            green_1 = t1_mean_bands[1] if c > 1 else t1_mean_bands[0]
            blue_1 = t1_mean_bands[2] if c > 2 else t1_mean_bands[0]

            red_2 = t2_mean_bands[0]
            green_2 = t2_mean_bands[1] if c > 1 else t2_mean_bands[0]
            blue_2 = t2_mean_bands[2] if c > 2 else t2_mean_bands[0]

            # C-4 FIX: Only compute spectral indices when actual NIR is present (c >= 4).
            # Synthesizing NIR as red * 1.2 is radiometrically invalid.
            has_nir = c > 3
            has_swir = c > 4  # SWIR needed for true NDBI

            if has_nir:
                nir_1 = t1_mean_bands[3]
                nir_2 = t2_mean_bands[3]

                ndvi_1 = (nir_1 - red_1) / (nir_1 + red_1 + 1e-6)
                ndvi_2 = (nir_2 - red_2) / (nir_2 + red_2 + 1e-6)
                delta_ndvi: Optional[float] = float(ndvi_2 - ndvi_1)

                ndwi_1 = (green_1 - nir_1) / (green_1 + nir_1 + 1e-6)
                ndwi_2 = (green_2 - nir_2) / (green_2 + nir_2 + 1e-6)
                delta_ndwi: Optional[float] = float(ndwi_2 - ndwi_1)

                # C-3 FIX: RNI (Red-NIR Index) for built-up proxy — labelled correctly, not as NDBI
                rni_1 = (red_1 - nir_1) / (red_1 + nir_1 + 1e-6)
                rni_2 = (red_2 - nir_2) / (red_2 + nir_2 + 1e-6)
                delta_rni: Optional[float] = float(rni_2 - rni_1)

                # True NDBI only with SWIR band
                delta_ndbi: Optional[float] = None
                if has_swir:
                    swir_1 = t1_mean_bands[4]
                    swir_2 = t2_mean_bands[4]
                    ndbi_1 = (swir_1 - nir_1) / (swir_1 + nir_1 + 1e-6)
                    ndbi_2 = (swir_2 - nir_2) / (swir_2 + nir_2 + 1e-6)
                    delta_ndbi = float(ndbi_2 - ndbi_1)
            else:
                # RGB-only: spectral indices unavailable
                delta_ndvi = None
                delta_ndwi = None
                delta_rni = None
                delta_ndbi = None
                has_swir = False
        else:
            t1_vals = t1_patch[mask_bool]
            t2_vals = t2_patch[mask_bool]
            red_1 = green_1 = blue_1 = float(np.mean(t1_vals))
            red_2 = green_2 = blue_2 = float(np.mean(t2_vals))
            # Single-band: no NIR available
            has_nir = False
            has_swir = False
            delta_ndvi = None
            delta_ndwi = None
            delta_rni = None
            delta_ndbi = None

        # Mean brightness inside polygon mask
        if t1_patch.ndim == 3:
            t1_masked_all = t1_patch[:, mask_bool]
            t2_masked_all = t2_patch[:, mask_bool]
            mean_t1_b = float(np.mean(t1_masked_all))
            mean_t2_b = float(np.mean(t2_masked_all))
            spectral_var = float(np.var(t2_masked_all))
        else:
            t1_vals_l = t1_patch[mask_bool]
            t2_vals_l = t2_patch[mask_bool]
            mean_t1_b = float(np.mean(t1_vals_l))
            mean_t2_b = float(np.mean(t2_vals_l))
            spectral_var = float(np.var(t2_vals_l))

        delta_brightness = float(mean_t2_b - mean_t1_b)

        # 2. Geometric & Morphological Features
        area_px = int(np.count_nonzero(mask_bool))
        area_m2 = float(area_px * (resolution_m ** 2))

        # Find contours for shape analysis
        contours, _ = cv2.findContours(polygon_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        perimeter_m = 0.0
        elongation = 1.0
        compactness = 0.5
        rectangularity = 0.5

        if contours and len(contours[0]) >= 3:
            cnt = contours[0]
            perim_px = cv2.arcLength(cnt, True)
            perimeter_m = float(perim_px * resolution_m)

            # Compactness = 4 * pi * Area / Perimeter^2
            if perim_px > 0:
                compactness = float((4.0 * np.pi * area_px) / (perim_px ** 2))

            # Minimum area bounding box for elongation & rectangularity
            rect = cv2.minAreaRect(cnt)
            (w_box, h_box) = rect[1]
            if w_box > 0 and h_box > 0:
                major = max(w_box, h_box)
                minor = max(1.0, min(w_box, h_box))
                elongation = float(major / minor)
                box_area = w_box * h_box
                rectangularity = float(min(1.0, area_px / box_area))

        return ClassificationEvidence(
            delta_ndvi=round(delta_ndvi, 4) if delta_ndvi is not None else None,
            delta_ndwi=round(delta_ndwi, 4) if delta_ndwi is not None else None,
            delta_rni=round(delta_rni, 4) if delta_rni is not None else None,
            delta_ndbi=round(delta_ndbi, 4) if delta_ndbi is not None else None,
            has_swir=has_swir,
            delta_brightness=round(delta_brightness, 4),
            mean_t1_brightness=round(mean_t1_b, 4),
            mean_t2_brightness=round(mean_t2_b, 4),
            elongation=round(elongation, 2),
            compactness=round(compactness, 4),
            rectangularity=round(rectangularity, 4),
            area_m2=round(area_m2, 2),
            perimeter_m=round(perimeter_m, 2),
            spectral_variance=round(spectral_var, 4),
            spectral_indices_available=(delta_ndvi is not None),
        )

    def classify(
        self,
        evidence: ClassificationEvidence,
    ) -> ClassificationDecision:
        """
        Classify change region using hierarchical decision logic based on quantitative evidence.

        Rules are only evaluated if the required spectral indices are available.
        For RGB-only images (no NIR band), only brightness and geometric rules fire.
        """
        e = evidence
        cat = "UNKNOWN"
        subcat = "Unknown"
        conf = 0.65
        rule = "DEFAULT_UNKNOWN"

        si = e.spectral_indices_available  # shorthand: True when NIR band present

        # -------------------------------------------------------------------
        # 1. Atmospheric Checks (High Brightness / Deep Shadow Spike)
        # These rely only on brightness — always available.
        # -------------------------------------------------------------------
        if e.delta_brightness > 0.45 and e.mean_t2_brightness > 0.85:
            cat = "ATMOSPHERIC"
            subcat = "Cloud"
            conf = 0.92
            rule = "EXTREME_BRIGHTNESS_SPIKE"
        elif e.delta_brightness < -0.45 and e.mean_t2_brightness < 0.15:
            cat = "ATMOSPHERIC"
            subcat = "Shadow"
            conf = 0.89
            rule = "EXTREME_SHADOW_DROP"

        # -------------------------------------------------------------------
        # 2. Disaster Checks — require spectral indices
        # -------------------------------------------------------------------
        elif si and e.delta_ndwi is not None and e.delta_ndwi > 0.25 and e.mean_t2_brightness < 0.35:
            cat = "DISASTER"
            subcat = "Flood"
            conf = 0.90
            rule = "SURGE_WATER_INDEX_INUNDATION"
        elif (
            si
            and e.delta_ndvi is not None
            and e.delta_ndvi < -0.30
            and e.mean_t2_brightness < 0.15  # M-3 FIX: charred surface is darker, not brighter
            and e.spectral_variance > 0.05
        ):
            cat = "DISASTER"
            subcat = "Wildfire"
            conf = 0.88
            rule = "CHAR_CANOPY_COLLAPSE_BURN_SCAR"
        elif (
            si
            and e.delta_ndvi is not None
            and e.delta_ndvi < -0.25
            and e.elongation > 2.5
            and e.delta_brightness > 0.20  # M-3 FIX: landslide exposes bright bare soil
        ):
            cat = "DISASTER"
            subcat = "Landslide"
            conf = 0.85
            rule = "SLOPE_EXPOSURE_HIGH_ELONGATION"

        # -------------------------------------------------------------------
        # 3. Human Activity Checks (Infrastructure, Built-Up, Roads, Mining)
        # -------------------------------------------------------------------
        elif e.elongation >= 3.8 and e.rectangularity > 0.35:
            cat = "HUMAN"
            subcat = "Road"
            conf = 0.91
            rule = "HIGH_ELONGATION_LINEAR_CORRIDOR"
        elif (
            # C-3 FIX: Use delta_rni (custom Red-NIR ratio) as built-up proxy
            # when SWIR is absent. Only fire if RNI gain is meaningfully positive.
            (e.has_swir and e.delta_ndbi is not None and e.delta_ndbi > 0.10)
            or (not e.has_swir and e.delta_rni is not None and e.delta_rni > 0.10)
            or e.delta_brightness > 0.20
        ) and e.rectangularity >= 0.55:
            cat = "HUMAN"
            if e.area_m2 > 100_000:
                subcat = "Industrial"
            elif e.area_m2 > 30_000:
                subcat = "Urban expansion"
            else:
                subcat = "Building"
            conf = 0.93
            rule = "RECTANGULAR_BUILTUP_INDEX_SURGE"
        elif e.delta_brightness > 0.25 and e.area_m2 > 50_000 and e.compactness < 0.4:
            cat = "HUMAN"
            subcat = "Mining"
            conf = 0.86
            rule = "LARGE_IRREGULAR_EARTHWORK_EXCAVATION"
        elif e.delta_brightness > 0.15 and si and e.delta_ndvi is not None and e.delta_ndvi < -0.10:
            cat = "HUMAN"
            subcat = "Construction"
            conf = 0.84
            rule = "SOIL_CLEARING_CONSTRUCTION_PREPARATION"

        # -------------------------------------------------------------------
        # 4. Natural / Environmental Checks (Vegetation, Water, River, Soil)
        # Require spectral indices for vegetation / water rules.
        # -------------------------------------------------------------------
        elif si and e.delta_ndvi is not None and e.delta_ndvi > 0.18:
            cat = "NATURAL"
            subcat = "Vegetation"
            conf = 0.89
            rule = "CANOPY_RESTORATION_NDVI_SURGE"
        elif si and e.delta_ndvi is not None and e.delta_ndvi < -0.18 and (e.delta_rni is None or e.delta_rni < 0.05):
            cat = "NATURAL"
            subcat = "Vegetation"
            conf = 0.85
            rule = "NATURAL_VEGETATION_CLEARING_SEASONAL"
        elif si and e.delta_ndwi is not None and e.delta_ndwi > 0.15:
            cat = "NATURAL"
            subcat = "River" if e.elongation > 3.0 else "Water"
            conf = 0.88
            rule = "NATURAL_WATERBODY_RIPARIAN_SHIFT"
        elif abs(e.delta_brightness) > 0.10:
            cat = "NATURAL"
            subcat = "Soil"
            conf = 0.75
            rule = "SOIL_MOISTURE_OR_EROSION_DRIFT"

        # 5. Fallback Unknown
        else:
            cat = "UNKNOWN"
            subcat = "Unknown"
            conf = 0.50
            rule = "AMBIGUOUS_SPECTRAL_EVIDENCE"

        e.rule_fired = rule

        evidence_dict = {
            "delta_ndvi": e.delta_ndvi,
            "delta_ndwi": e.delta_ndwi,
            "delta_rni": e.delta_rni,
            "delta_ndbi": e.delta_ndbi,
            "has_swir": e.has_swir,
            "spectral_indices_available": e.spectral_indices_available,
            "delta_brightness": e.delta_brightness,
            "mean_t1_brightness": e.mean_t1_brightness,
            "mean_t2_brightness": e.mean_t2_brightness,
            "elongation": e.elongation,
            "compactness": e.compactness,
            "rectangularity": e.rectangularity,
            "area_m2": e.area_m2,
            "perimeter_m": e.perimeter_m,
            "spectral_variance": e.spectral_variance,
            "rule_fired": e.rule_fired,
        }

        return ClassificationDecision(
            category=cat,
            subcategory=subcat,
            confidence=conf,
            evidence=evidence_dict,
            model_version=self.model_version,
        )
