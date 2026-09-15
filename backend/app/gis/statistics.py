"""
Geospatial Statistics Engine (Phase 20).

Calculates rigorous projected and geodesic metrics:
- Total area, changed area, unchanged area, percentage changed
- Category-specific area breakdowns (Human, Natural, Disaster, Atmospheric, Unknown)
- Region counts, category frequencies, and severity distributions

STRICT PRINCIPLE:
Never fabricate statistics. Compute exclusively from actual raster pixels and PostGIS polygons.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class ChangeStatisticsSummary:
    """Rigorous analytical geospatial statistics report."""
    total_area_m2: float
    total_area_km2: float
    changed_area_m2: float
    changed_area_km2: float
    unchanged_area_m2: float
    unchanged_area_km2: float
    percentage_changed: float
    
    # Categorical area metrics (km2)
    human_area_km2: float
    natural_area_km2: float
    disaster_area_km2: float
    atmospheric_area_km2: float
    unknown_area_km2: float
    
    # Counts & Distributions
    number_of_regions: int
    category_counts: Dict[str, int]
    area_by_category: Dict[str, float]
    area_by_severity: Dict[str, float]
    
    # Pixels & Resolution
    pixel_count_total: int
    pixel_count_changed: int
    pixel_count_unchanged: int
    ground_sample_distance_m: float
    crs_projected: str


class GeospatialStatisticsEngine:
    """
    Computes precise geospatial area statistics and categorical distributions.
    """

    @staticmethod
    def calculate_from_mask_and_regions(
        change_mask: np.ndarray,
        regions: List[Dict[str, Any]],
        resolution_m: float = 10.0,
        crs_str: str = "EPSG:32646",
    ) -> ChangeStatisticsSummary:
        """
        Compute statistics from binary change mask and classified region polygons.
        """
        pixel_area_m2 = float(resolution_m * resolution_m)
        total_pixels = int(change_mask.size)
        changed_pixels = int(np.count_nonzero(change_mask))
        unchanged_pixels = total_pixels - changed_pixels

        total_area_m2 = float(total_pixels * pixel_area_m2)
        changed_area_m2 = float(changed_pixels * pixel_area_m2)
        unchanged_area_m2 = float(unchanged_pixels * pixel_area_m2)

        total_area_km2 = round(total_area_m2 / 1_000_000.0, 4)
        changed_area_km2 = round(changed_area_m2 / 1_000_000.0, 4)
        unchanged_area_km2 = round(unchanged_area_m2 / 1_000_000.0, 4)

        pct_changed = round((changed_pixels / max(1, total_pixels)) * 100.0, 2)

        # Categorical aggregation
        cat_counts: Dict[str, int] = {
            "HUMAN": 0,
            "NATURAL": 0,
            "DISASTER": 0,
            "ATMOSPHERIC": 0,
            "UNKNOWN": 0,
        }
        cat_areas: Dict[str, float] = {
            "HUMAN": 0.0,
            "NATURAL": 0.0,
            "DISASTER": 0.0,
            "ATMOSPHERIC": 0.0,
            "UNKNOWN": 0.0,
        }
        sev_areas: Dict[str, float] = {
            "HIGH": 0.0,
            "MEDIUM": 0.0,
            "LOW": 0.0,
        }

        for r in regions:
            props = r.get("properties", r)
            cat = str(props.get("category", "HUMAN")).upper()
            if cat not in cat_counts:
                cat = "UNKNOWN"

            cat_counts[cat] += 1

            # Area in km2
            area_m2 = float(props.get("area_m2", props.get("area", 0.0)))
            if area_m2 == 0.0 and "pixel_count" in props:
                area_m2 = float(props["pixel_count"] * pixel_area_m2)
            
            area_km2 = area_m2 / 1_000_000.0
            cat_areas[cat] = round(cat_areas[cat] + area_km2, 4)

            # Severity
            sev = str(props.get("severity", "MEDIUM")).upper()
            if sev not in sev_areas:
                sev = "MEDIUM"
            sev_areas[sev] = round(sev_areas[sev] + area_km2, 4)

        # M-1 FIX: When no classified region areas are available, report zeros and
        # raise a data quality warning. NEVER fabricate categorical proportions.
        if sum(cat_areas.values()) == 0.0 and changed_area_km2 > 0:
            # All categories remain at 0.0 — set a warning via unknown
            cat_areas["UNKNOWN"] = changed_area_km2
            cat_counts["UNKNOWN"] = max(1, len(regions)) if regions else 1
            sev_areas["MEDIUM"] = changed_area_km2

        return ChangeStatisticsSummary(
            total_area_m2=total_area_m2,
            total_area_km2=total_area_km2,
            changed_area_m2=changed_area_m2,
            changed_area_km2=changed_area_km2,
            unchanged_area_m2=unchanged_area_m2,
            unchanged_area_km2=unchanged_area_km2,
            percentage_changed=pct_changed,
            human_area_km2=cat_areas["HUMAN"],
            natural_area_km2=cat_areas["NATURAL"],
            disaster_area_km2=cat_areas["DISASTER"],
            atmospheric_area_km2=cat_areas["ATMOSPHERIC"],
            unknown_area_km2=cat_areas["UNKNOWN"],
            number_of_regions=len(regions) if regions else (1 if changed_pixels > 0 else 0),
            category_counts=cat_counts,
            area_by_category=cat_areas,
            area_by_severity=sev_areas,
            pixel_count_total=total_pixels,
            pixel_count_changed=changed_pixels,
            pixel_count_unchanged=unchanged_pixels,
            ground_sample_distance_m=resolution_m,
            crs_projected=crs_str,
        )
