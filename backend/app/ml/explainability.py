"""
Uncertainty Quantification & Explainable AI (XAI) Engine.

STRICT PRINCIPLES:
1. Ground every explanation strictly in physical model activations, spectral deltas, and GIS geometry.
2. Never hallucinate explanations or claim causality without data.
3. Clearly label metrics as automated system/model indicators.
4. Provide crop matrices, change masks, and saliency heatmaps for significant detections.
"""

import base64
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from app.core.logging import logger


@dataclass
class ReliabilityAssessment:
    """System and model reliability indicator score bundle."""
    model_confidence_pct: float
    image_quality_pct: float
    registration_quality_pct: float
    overall_reliability: str           # "HIGH", "MEDIUM", "LOW"
    overall_score: float               # [0, 100]
    formula_basis: str = "Composite: 0.40*ModelConf + 0.35*RegQual + 0.25*ImgQual"


@dataclass
class RegionExplanation:
    """Detailed explainability card for a localized change polygon ('Why was this detected?')."""
    region_index: int
    category: str
    subcategory: str
    confidence_pct: float
    spectral_evidence: Dict[str, Any]
    geometric_evidence: Dict[str, Any]
    decision_rule: str
    explanation_narrative: str
    t1_crop_data_url: Optional[str] = None
    t2_crop_data_url: Optional[str] = None
    mask_crop_data_url: Optional[str] = None
    saliency_heatmap_data_url: Optional[str] = None
    reliability: Optional[ReliabilityAssessment] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ExplainabilityEngine:
    """
    Computes composite reliability scores and generates grounded XAI diagnostics with image crops and saliency.
    """

    @staticmethod
    def calculate_reliability(
        model_confidence: float,       # [0.0, 1.0]
        data_quality_score: float,     # [0, 100]
        registration_correlation: float, # [0.0, 1.0]
    ) -> ReliabilityAssessment:
        """
        Calculate composite reliability from model certainty, raster metadata quality, and co-registration fit.
        """
        conf_pct = round(float(np.clip(model_confidence, 0.0, 1.0) * 100.0), 1)
        img_pct = round(float(np.clip(data_quality_score, 0.0, 100.0)), 1)
        reg_pct = round(float(np.clip(registration_correlation, 0.0, 1.0) * 100.0), 1)

        composite_score = round(0.40 * conf_pct + 0.35 * reg_pct + 0.25 * img_pct, 1)

        if composite_score >= 85.0:
            level = "HIGH"
        elif composite_score >= 65.0:
            level = "MEDIUM"
        else:
            level = "LOW"

        return ReliabilityAssessment(
            model_confidence_pct=conf_pct,
            image_quality_pct=img_pct,
            registration_quality_pct=reg_pct,
            overall_reliability=level,
            overall_score=composite_score,
        )

    @staticmethod
    def _array_to_png_data_url(arr: np.ndarray) -> str:
        """Convert 2D or 3D numpy array to PNG base64 data URI."""
        if arr.ndim == 3 and arr.shape[0] in [1, 3, 4]:
            if arr.shape[0] == 1:
                img_data = arr[0]
            else:
                img_data = np.transpose(arr[:3], (1, 2, 0))
        else:
            img_data = arr

        # Normalize to uint8
        if img_data.dtype != np.uint8:
            img_norm = np.clip(img_data * 255.0 if np.max(img_data) <= 1.0 else img_data, 0, 255).astype(np.uint8)
        else:
            img_norm = img_data

        pil_img = Image.fromarray(img_norm)
        # Resize small crops for clean UI preview
        if pil_img.width < 120 or pil_img.height < 120:
            pil_img = pil_img.resize((max(128, pil_img.width * 2), max(128, pil_img.height * 2)), Image.NEAREST)

        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    @classmethod
    def generate_explanation(
        cls,
        region_index: int,
        category: str,
        subcategory: str,
        confidence: float,
        evidence: Dict[str, Any],
        t1_patch: np.ndarray,
        t2_patch: np.ndarray,
        mask_patch: np.ndarray,
        data_quality_score: float = 88.0,
        registration_correlation: float = 0.96,
    ) -> RegionExplanation:
        """
        Generate grounded explainability bundle with visual crops, difference saliency, and spectral evidence.
        """
        conf_pct = round(confidence * 100.0, 1)

        # 1. Separate spectral & geometric evidence
        spectral_keys = ["delta_ndvi", "delta_ndwi", "delta_ndbi", "delta_brightness", "mean_t1_brightness", "mean_t2_brightness", "spectral_variance"]
        geom_keys = ["elongation", "compactness", "rectangularity", "area_m2", "perimeter_m"]

        spectral_dict = {k: evidence.get(k) for k in spectral_keys if k in evidence}
        geom_dict = {k: evidence.get(k) for k in geom_keys if k in evidence}
        rule_fired = str(evidence.get("rule_fired", "SPECTRAL_DIFFERENCE_THRESHOLD"))

        # 2. Formulate grounded narrative based on actual metrics
        d_b = evidence.get("delta_brightness", 0.0)
        d_ndvi = evidence.get("delta_ndvi", 0.0)
        d_ndwi = evidence.get("delta_ndwi", 0.0)
        d_ndbi = evidence.get("delta_ndbi", 0.0)
        elong = evidence.get("elongation", 1.0)
        rect = evidence.get("rectangularity", 0.0)

        narrative_parts = []
        if category == "HUMAN":
            if subcategory == "Road" or elong >= 3.8:
                narrative_parts.append(f"Linear transport corridor detected with high elongation aspect ratio ({elong:.2f}x).")
            elif subcategory == "Building" or rect >= 0.55:
                narrative_parts.append(f"High geometric rectangularity ({rect:.2f}) and positive built-up response (ΔNDBI: {d_ndbi:+.3f}) indicate structured man-made construction.")
            else:
                narrative_parts.append(f"Ground surface radiometric alteration (ΔBrightness: {d_b:+.3f}) matches human site development.")
        elif category == "DISASTER":
            if subcategory == "Flood" or d_ndwi > 0.2:
                narrative_parts.append(f"Significant positive water index surge (ΔNDWI: {d_ndwi:+.3f}) indicates potential flood inundation.")
            elif subcategory == "Wildfire" or d_ndvi < -0.3:
                narrative_parts.append(f"Severe canopy vegetation collapse (ΔNDVI: {d_ndvi:+.3f}) with low char albedo matches potential wildfire burn.")
            else:
                narrative_parts.append(f"Acute hazard anomaly detected via multi-spectral difference.")
        elif category == "NATURAL":
            if d_ndvi > 0.15:
                narrative_parts.append(f"Positive vegetation index recovery (ΔNDVI: {d_ndvi:+.3f}) indicates seasonal agricultural growth or canopy restoration.")
            elif d_ndwi > 0.15:
                narrative_parts.append(f"Riparian waterbody channel boundary fluctuation (ΔNDWI: {d_ndwi:+.3f}).")
            else:
                narrative_parts.append(f"Natural environmental baseline variance without human structural markers.")
        elif category == "ATMOSPHERIC":
            narrative_parts.append(f"Specular radiometric albedo saturation (ΔBrightness: {d_b:+.3f}) matches transient cloud or shadow projection.")
        else:
            narrative_parts.append("Spectral difference exceeded detection threshold with ambiguous categorical indicators.")

        narrative = " ".join(narrative_parts)

        # 3. Generate Visual Crops
        t1_url = cls._array_to_png_data_url(t1_patch)
        t2_url = cls._array_to_png_data_url(t2_patch)
        mask_url = cls._array_to_png_data_url(mask_patch)

        # 4. Generate Saliency / Difference Heatmap
        diff_patch = np.abs(t2_patch.astype(np.float32) - t1_patch.astype(np.float32))
        diff_2d = np.mean(diff_patch, axis=0) if diff_patch.ndim == 3 else diff_patch
        diff_norm = np.clip(diff_2d * 255.0, 0, 255).astype(np.uint8)
        heatmap_colored = cv2.applyColorMap(diff_norm, cv2.COLORMAP_JET)
        heatmap_url = cls._array_to_png_data_url(cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB))

        # 5. Reliability Assessment
        reliability = cls.calculate_reliability(
            model_confidence=confidence,
            data_quality_score=data_quality_score,
            registration_correlation=registration_correlation,
        )

        return RegionExplanation(
            region_index=region_index,
            category=category,
            subcategory=subcategory,
            confidence_pct=conf_pct,
            spectral_evidence=spectral_dict,
            geometric_evidence=geom_dict,
            decision_rule=rule_fired,
            explanation_narrative=narrative,
            t1_crop_data_url=t1_url,
            t2_crop_data_url=t2_url,
            mask_crop_data_url=mask_url,
            saliency_heatmap_data_url=heatmap_url,
            reliability=reliability,
        )
