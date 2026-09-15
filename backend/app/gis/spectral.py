"""
Spectral Index Analysis Engine — NDVI, NDWI, and NDBI.

STRICT PRINCIPLES:
1. Check band availability before calculation.
2. Never calculate an index using incorrect or missing bands.
3. If required bands are missing (e.g. RGB with no NIR/SWIR), return explicit availability flags
   and explanations rather than fabricating results.
4. Use valid indices strictly as physical supporting evidence.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.core.logging import logger


@dataclass
class SingleIndexResult:
    """Result of computing a specific multi-spectral index."""
    index_name: str                 # NDVI, NDWI, NDBI
    is_available: bool              # True if required bands were verified and present
    required_bands: List[str]       # e.g., ["NIR", "Red"]
    missing_bands: List[str] = field(default_factory=list)
    t1_mean: Optional[float] = None
    t2_mean: Optional[float] = None
    delta_mean: Optional[float] = None
    delta_min: Optional[float] = None
    delta_max: Optional[float] = None
    delta_std: Optional[float] = None
    significant_increase_pct: Optional[float] = None  # Percentage of pixels with delta > +0.20
    significant_decrease_pct: Optional[float] = None  # Percentage of pixels with delta < -0.20
    interpretation: str = "Indices unavailable"


@dataclass
class SpectralAnalysisReport:
    """Comprehensive spectral index analysis report across multi-temporal pair."""
    is_multispectral: bool
    band_count_t1: int
    band_count_t2: int
    detected_bands: List[str]
    ndvi: SingleIndexResult
    ndwi: SingleIndexResult
    ndbi: SingleIndexResult
    supporting_evidence_summary: List[str] = field(default_factory=list)


class SpectralIndexAnalyzer:
    """
    Validates band availability and computes NDVI, NDWI, and NDBI multi-temporal shifts.
    """

    @staticmethod
    def identify_band_indices(
        band_count: int,
        sensor_or_satellite: Optional[str] = None,
        band_names: Optional[List[str]] = None,
    ) -> Dict[str, Optional[int]]:
        """
        Identify 0-indexed band channels based on satellite/sensor specifications.
        """
        mapping: Dict[str, Optional[int]] = {
            "blue": None,
            "green": None,
            "red": None,
            "nir": None,
            "swir1": None,
            "swir2": None,
        }

        # If explicit band names provided
        if band_names:
            names_lower = [b.lower() for b in band_names]
            for idx, name in enumerate(names_lower):
                if "blue" in name or name in ["b2", "b02"]:
                    mapping["blue"] = idx
                elif "green" in name or name in ["b3", "b03"]:
                    mapping["green"] = idx
                elif "red" in name or name in ["b4", "b04"]:
                    mapping["red"] = idx
                elif "nir" in name or name in ["b8", "b08", "b5", "b05"]:
                    mapping["nir"] = idx
                elif "swir1" in name or name in ["b11", "b6"]:
                    mapping["swir1"] = idx
                elif "swir2" in name or name in ["b12", "b7"]:
                    mapping["swir2"] = idx
            return mapping

        # Heuristic based on standard channel counts
        sat_str = (sensor_or_satellite or "").lower()

        if "sentinel-2" in sat_str and band_count >= 12:
            # Sentinel-2 full L2A (1-indexed: B2=Blue, B3=Green, B4=Red, B8=NIR, B11=SWIR1)
            mapping["blue"] = 1
            mapping["green"] = 2
            mapping["red"] = 3
            mapping["nir"] = 7
            mapping["swir1"] = 10
            mapping["swir2"] = 11
        elif "landsat" in sat_str and band_count >= 7:
            # Landsat 8/9 OLI (B2=Blue, B3=Green, B4=Red, B5=NIR, B6=SWIR1, B7=SWIR2)
            mapping["blue"] = 1
            mapping["green"] = 2
            mapping["red"] = 3
            mapping["nir"] = 4
            mapping["swir1"] = 5
            mapping["swir2"] = 6
        elif band_count >= 4:
            # Standard 4-band optical (Red, Green, Blue, NIR) or (Blue, Green, Red, NIR)
            mapping["red"] = 0
            mapping["green"] = 1
            mapping["blue"] = 2
            mapping["nir"] = 3
        elif band_count == 3:
            # Standard 3-band RGB (Red=0, Green=1, Blue=2). NO NIR or SWIR available.
            mapping["red"] = 0
            mapping["green"] = 1
            mapping["blue"] = 2
        elif band_count == 1:
            mapping["red"] = 0

        return mapping

    @staticmethod
    def _compute_normalized_diff(
        band_a: np.ndarray,
        band_b: np.ndarray,
        eps: float = 1e-6,
    ) -> np.ndarray:
        """Calculate (A - B) / (A + B) with clipping to [-1.0, 1.0]."""
        num = band_a.astype(np.float32) - band_b.astype(np.float32)
        denom = band_a.astype(np.float32) + band_b.astype(np.float32) + eps
        idx = num / denom
        return np.clip(idx, -1.0, 1.0)

    @classmethod
    def analyze(
        cls,
        image1: np.ndarray,
        image2: np.ndarray,
        metadata_t1: Optional[Dict[str, Any]] = None,
        metadata_t2: Optional[Dict[str, Any]] = None,
    ) -> SpectralAnalysisReport:
        """
        Execute spectral index analysis on multi-temporal rasters.
        """
        c1 = image1.shape[0] if image1.ndim == 3 else 1
        c2 = image2.shape[0] if image2.ndim == 3 else 1

        sat_hint = None
        if metadata_t1 and metadata_t1.get("satellite"):
            sat_hint = metadata_t1.get("satellite")

        band_map = cls.identify_band_indices(min(c1, c2), sensor_or_satellite=sat_hint)
        detected_bands = [k.upper() for k, v in band_map.items() if v is not None]

        is_ms = band_map["nir"] is not None
        evidence_summary: List[str] = []

        # -------------------------------------------------------------------
        # 1. NDVI (Normalized Difference Vegetation Index) = (NIR - Red) / (NIR + Red)
        # -------------------------------------------------------------------
        if band_map["nir"] is not None and band_map["red"] is not None:
            nir_idx = band_map["nir"]
            red_idx = band_map["red"]

            ndvi_1 = cls._compute_normalized_diff(image1[nir_idx], image1[red_idx])
            ndvi_2 = cls._compute_normalized_diff(image2[nir_idx], image2[red_idx])
            delta_ndvi = ndvi_2 - ndvi_1

            inc_pct = float((np.count_nonzero(delta_ndvi > 0.20) / delta_ndvi.size) * 100.0)
            dec_pct = float((np.count_nonzero(delta_ndvi < -0.20) / delta_ndvi.size) * 100.0)

            interp = "Stable vegetation canopy"
            if dec_pct > 5.0:
                interp = f"Significant vegetation loss / clearing detected across {dec_pct:.1f}% of area"
                evidence_summary.append(f"NDVI drop corroborates vegetation loss ({dec_pct:.1f}% area)")
            elif inc_pct > 5.0:
                interp = f"Vegetation regrowth / canopy restoration detected across {inc_pct:.1f}% of area"
                evidence_summary.append(f"NDVI surge corroborates vegetation expansion ({inc_pct:.1f}% area)")

            ndvi_res = SingleIndexResult(
                index_name="NDVI (Vegetation Index)",
                is_available=True,
                required_bands=["NIR", "Red"],
                missing_bands=[],
                t1_mean=round(float(np.mean(ndvi_1)), 4),
                t2_mean=round(float(np.mean(ndvi_2)), 4),
                delta_mean=round(float(np.mean(delta_ndvi)), 4),
                delta_min=round(float(np.min(delta_ndvi)), 4),
                delta_max=round(float(np.max(delta_ndvi)), 4),
                delta_std=round(float(np.std(delta_ndvi)), 4),
                significant_increase_pct=round(inc_pct, 2),
                significant_decrease_pct=round(dec_pct, 2),
                interpretation=interp,
            )
        else:
            missing = []
            if band_map["nir"] is None:
                missing.append("NIR (Near-Infrared)")
            if band_map["red"] is None:
                missing.append("Red")
            ndvi_res = SingleIndexResult(
                index_name="NDVI (Vegetation Index)",
                is_available=False,
                required_bands=["NIR", "Red"],
                missing_bands=missing,
                interpretation=f"NDVI calculation bypassed: missing required {', '.join(missing)} band(s).",
            )

        # -------------------------------------------------------------------
        # 2. NDWI (Normalized Difference Water Index) = (Green - NIR) / (Green + NIR)
        # -------------------------------------------------------------------
        if band_map["green"] is not None and band_map["nir"] is not None:
            green_idx = band_map["green"]
            nir_idx = band_map["nir"]

            ndwi_1 = cls._compute_normalized_diff(image1[green_idx], image1[nir_idx])
            ndwi_2 = cls._compute_normalized_diff(image2[green_idx], image2[nir_idx])
            delta_ndwi = ndwi_2 - ndwi_1

            inc_pct = float((np.count_nonzero(delta_ndwi > 0.20) / delta_ndwi.size) * 100.0)
            dec_pct = float((np.count_nonzero(delta_ndwi < -0.20) / delta_ndwi.size) * 100.0)

            interp = "Stable surface water extent"
            if inc_pct > 3.0:
                interp = f"Water surge / flood inundation detected across {inc_pct:.1f}% of area"
                evidence_summary.append(f"NDWI surge corroborates surface water expansion ({inc_pct:.1f}% area)")
            elif dec_pct > 3.0:
                interp = f"Waterbody recession / drought drying detected across {dec_pct:.1f}% of area"
                evidence_summary.append(f"NDWI drop indicates water recession ({dec_pct:.1f}% area)")

            ndwi_res = SingleIndexResult(
                index_name="NDWI (Water Index)",
                is_available=True,
                required_bands=["Green", "NIR"],
                missing_bands=[],
                t1_mean=round(float(np.mean(ndwi_1)), 4),
                t2_mean=round(float(np.mean(ndwi_2)), 4),
                delta_mean=round(float(np.mean(delta_ndwi)), 4),
                delta_min=round(float(np.min(delta_ndwi)), 4),
                delta_max=round(float(np.max(delta_ndwi)), 4),
                delta_std=round(float(np.std(delta_ndwi)), 4),
                significant_increase_pct=round(inc_pct, 2),
                significant_decrease_pct=round(dec_pct, 2),
                interpretation=interp,
            )
        else:
            missing = []
            if band_map["green"] is None:
                missing.append("Green")
            if band_map["nir"] is None:
                missing.append("NIR (Near-Infrared)")
            ndwi_res = SingleIndexResult(
                index_name="NDWI (Water Index)",
                is_available=False,
                required_bands=["Green", "NIR"],
                missing_bands=missing,
                interpretation=f"NDWI calculation bypassed: missing required {', '.join(missing)} band(s).",
            )

        # -------------------------------------------------------------------
        # 3. NDBI (Normalized Difference Built-Up Index) = (SWIR - NIR) / (SWIR + NIR)
        # -------------------------------------------------------------------
        if band_map["swir1"] is not None and band_map["nir"] is not None:
            swir_idx = band_map["swir1"]
            nir_idx = band_map["nir"]

            ndbi_1 = cls._compute_normalized_diff(image1[swir_idx], image1[nir_idx])
            ndbi_2 = cls._compute_normalized_diff(image2[swir_idx], image2[nir_idx])
            delta_ndbi = ndbi_2 - ndbi_1

            inc_pct = float((np.count_nonzero(delta_ndbi > 0.15) / delta_ndbi.size) * 100.0)
            dec_pct = float((np.count_nonzero(delta_ndbi < -0.15) / delta_ndbi.size) * 100.0)

            interp = "Stable built environment"
            if inc_pct > 2.0:
                interp = f"New built-up infrastructure / urban expansion detected across {inc_pct:.1f}% of area"
                evidence_summary.append(f"NDBI surge corroborates built-up expansion ({inc_pct:.1f}% area)")

            ndbi_res = SingleIndexResult(
                index_name="NDBI (Built-Up Index)",
                is_available=True,
                required_bands=["SWIR1", "NIR"],
                missing_bands=[],
                t1_mean=round(float(np.mean(ndbi_1)), 4),
                t2_mean=round(float(np.mean(ndbi_2)), 4),
                delta_mean=round(float(np.mean(delta_ndbi)), 4),
                delta_min=round(float(np.min(delta_ndbi)), 4),
                delta_max=round(float(np.max(delta_ndbi)), 4),
                delta_std=round(float(np.std(delta_ndbi)), 4),
                significant_increase_pct=round(inc_pct, 2),
                significant_decrease_pct=round(dec_pct, 2),
                interpretation=interp,
            )
        else:
            missing = []
            if band_map["swir1"] is None:
                missing.append("SWIR (Short-Wave Infrared)")
            if band_map["nir"] is None:
                missing.append("NIR (Near-Infrared)")
            ndbi_res = SingleIndexResult(
                index_name="NDBI (Built-Up Index)",
                is_available=False,
                required_bands=["SWIR", "NIR"],
                missing_bands=missing,
                interpretation=f"NDBI calculation bypassed: missing required {', '.join(missing)} band(s).",
            )

        if not is_ms and not evidence_summary:
            evidence_summary.append(
                "RGB Optical 3-Band inputs provided: Spectral indices requiring NIR/SWIR are safely bypassed."
            )

        return SpectralAnalysisReport(
            is_multispectral=is_ms,
            band_count_t1=c1,
            band_count_t2=c2,
            detected_bands=detected_bands,
            ndvi=ndvi_res,
            ndwi=ndwi_res,
            ndbi=ndbi_res,
            supporting_evidence_summary=evidence_summary,
        )
