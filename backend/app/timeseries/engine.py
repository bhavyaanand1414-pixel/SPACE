"""
Multi-Temporal Time-Series Analysis Engine.

STRICT PRINCIPLES:
1. Supports sequences of >= 2 satellite observations (e.g., T1 -> T2 -> T3 -> ... -> Tn).
2. Never claims satellite imagery exists at an unacquired time point.
3. Enforces the disclaimer: "Analysis interval depends on available satellite observations."
4. Computes area-over-time trajectories, human expansion curves, natural shifts, and disaster progression.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np

from app.core.logging import logger
from app.ml.baseline import BaselineChangeDetector
from app.ml.classifier import HierarchicalChangeClassifier


TIMELINE_AVAILABILITY_DISCLAIMER = (
    "Analysis interval depends on available satellite observations. "
    "Interpolated temporal intervals represent discrete satellite acquisition timestamps."
)


@dataclass
class TimeSeriesObservation:
    """Single temporal observation slice in a multi-date sequence."""
    observation_id: str
    timestamp_iso: str                  # e.g., "2020-01-15T10:30:00Z"
    label: str                          # e.g., "T1 (2020-01-15)"
    image_array: np.ndarray             # (C, H, W)
    resolution_m: float = 10.0
    satellite: Optional[str] = None
    cloud_coverage_pct: Optional[float] = None


@dataclass
class TimeSeriesStepResult:
    """Step change results between sequential observations (T_i -> T_{i+1})."""
    step_index: int
    from_observation_id: str
    to_observation_id: str
    from_timestamp: str
    to_timestamp: str
    interval_days: float
    interval_human_readable: str        # e.g., "365 days (~1.0 year)"
    changed_area_m2: float
    changed_area_km2: float
    percentage_changed: float
    human_growth_km2: float
    natural_progression_km2: float
    disaster_progression_km2: float
    atmospheric_artifacts_km2: float
    regions_count: int
    dominant_category: str
    geojson_features: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TimeSeriesAnalysisReport:
    """Complete multi-temporal progression report across full image timeline."""
    timeseries_id: str
    title: str
    observation_count: int
    observations_summary: List[Dict[str, Any]]
    total_duration_days: float
    overall_human_growth_km2: float
    overall_natural_shift_km2: float
    overall_disaster_impact_km2: float
    sequential_steps: List[TimeSeriesStepResult]
    area_over_time_series: List[Dict[str, Any]]       # [{timestamp, label, cumulative_change_km2, interval_change_km2}]
    category_over_time_series: List[Dict[str, Any]]   # [{timestamp, human_km2, natural_km2, disaster_km2}]
    availability_notice: str = TIMELINE_AVAILABILITY_DISCLAIMER
    model_version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TimeSeriesEngine:
    """
    Orchestrates sequential and pairwise change detection across multi-temporal image sequences.
    """

    def __init__(self, model_version: str = "1.0.0"):
        self.model_version = model_version
        self.detector = BaselineChangeDetector(model_version=model_version)
        self.classifier = HierarchicalChangeClassifier(model_version=model_version)

    @staticmethod
    def _format_interval_human_readable(delta_days: float) -> str:
        """Format elapsed days into hours, days, weeks, months, or years."""
        if delta_days < 1.0:
            hours = round(delta_days * 24.0, 1)
            return f"{hours} hours"
        elif delta_days < 14.0:
            return f"{round(delta_days, 1)} days"
        elif delta_days < 60.0:
            weeks = round(delta_days / 7.0, 1)
            return f"{weeks} weeks ({int(delta_days)} days)"
        elif delta_days < 365.0:
            months = round(delta_days / 30.4375, 1)
            return f"{months} months ({int(delta_days)} days)"
        else:
            years = round(delta_days / 365.25, 2)
            return f"{years} years ({int(delta_days)} days)"

    def analyze_sequence(
        self,
        observations: List[TimeSeriesObservation],
        timeseries_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> TimeSeriesAnalysisReport:
        """
        Analyze an ordered sequence of >= 2 satellite observations.
        """
        if len(observations) < 2:
            raise ValueError("Time-series analysis requires at least 2 distinct satellite observations.")

        # Sort observations chronologically
        sorted_obs = sorted(
            observations,
            key=lambda o: datetime.fromisoformat(o.timestamp_iso.replace("Z", "+00:00")),
        )

        ts_id = timeseries_id or f"TS-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        ts_title = title or f"Multi-Temporal Progression ({len(sorted_obs)} Observations)"

        # Parse observation metadata
        obs_summaries = []
        for o in sorted_obs:
            obs_summaries.append({
                "observation_id": o.observation_id,
                "timestamp": o.timestamp_iso,
                "label": o.label,
                "satellite": o.satellite or "Satellite Sensor",
                "resolution_m": o.resolution_m,
                "cloud_coverage_pct": o.cloud_coverage_pct,
            })

        dt_first = datetime.fromisoformat(sorted_obs[0].timestamp_iso.replace("Z", "+00:00"))
        dt_last = datetime.fromisoformat(sorted_obs[-1].timestamp_iso.replace("Z", "+00:00"))
        total_duration_days = (dt_last - dt_first).total_seconds() / 86400.0

        sequential_steps: List[TimeSeriesStepResult] = []
        area_over_time = []
        category_over_time = []

        cumulative_human_km2 = 0.0
        cumulative_natural_km2 = 0.0
        cumulative_disaster_km2 = 0.0
        cumulative_changed_km2 = 0.0

        # Baseline timestamp zero point
        area_over_time.append({
            "timestamp": sorted_obs[0].timestamp_iso,
            "label": sorted_obs[0].label,
            "cumulative_change_km2": 0.0,
            "interval_change_km2": 0.0,
            "percentage_changed": 0.0,
        })
        category_over_time.append({
            "timestamp": sorted_obs[0].timestamp_iso,
            "label": sorted_obs[0].label,
            "human_growth_km2": 0.0,
            "natural_shift_km2": 0.0,
            "disaster_impact_km2": 0.0,
        })

        # Process sequential pairs: (T_i -> T_{i+1})
        for i in range(len(sorted_obs) - 1):
            obs_from = sorted_obs[i]
            obs_to = sorted_obs[i + 1]

            dt_from = datetime.fromisoformat(obs_from.timestamp_iso.replace("Z", "+00:00"))
            dt_to = datetime.fromisoformat(obs_to.timestamp_iso.replace("Z", "+00:00"))
            interval_days = max(0.001, (dt_to - dt_from).total_seconds() / 86400.0)

            # Execute baseline change detection between the consecutive pair
            det_res = self.detector.detect_change(
                image1=obs_from.image_array,
                image2=obs_to.image_array,
                resolution_m=obs_to.resolution_m,
            )

            # Categorical breakdown aggregation
            step_human_km2 = 0.0
            step_natural_km2 = 0.0
            step_disaster_km2 = 0.0
            step_atmo_km2 = 0.0

            step_features: List[Dict[str, Any]] = []
            for r in det_res.regions:
                cat = r.category.upper()
                if cat == "HUMAN":
                    step_human_km2 += r.area_km2
                elif cat == "NATURAL":
                    step_natural_km2 += r.area_km2
                elif cat == "DISASTER":
                    step_disaster_km2 += r.area_km2
                elif cat == "ATMOSPHERIC":
                    step_atmo_km2 += r.area_km2

                step_features.append({
                    "type": "Feature",
                    "geometry": r.geojson_geometry,
                    "properties": {
                        "region_index": r.region_index,
                        "category": r.category,
                        "subtype": r.subtype,
                        "subcategory": r.subcategory,
                        "area_m2": r.area_m2,
                        "area_km2": r.area_km2,
                        "confidence": r.mean_confidence,
                        "severity_level": r.severity_level,
                        "step_interval": f"{obs_from.label} → {obs_to.label}",
                    },
                })

            # Determine dominant category
            cat_map = {
                "HUMAN": step_human_km2,
                "NATURAL": step_natural_km2,
                "DISASTER": step_disaster_km2,
                "ATMOSPHERIC": step_atmo_km2,
            }
            dom_cat = max(cat_map, key=cat_map.get) if det_res.total_area_changed_km2 > 0 else "NONE"

            step_res = TimeSeriesStepResult(
                step_index=i + 1,
                from_observation_id=obs_from.observation_id,
                to_observation_id=obs_to.observation_id,
                from_timestamp=obs_from.timestamp_iso,
                to_timestamp=obs_to.timestamp_iso,
                interval_days=round(interval_days, 2),
                interval_human_readable=self._format_interval_human_readable(interval_days),
                changed_area_m2=det_res.total_area_changed_m2,
                changed_area_km2=det_res.total_area_changed_km2,
                percentage_changed=det_res.percentage_changed,
                human_growth_km2=round(step_human_km2, 4),
                natural_progression_km2=round(step_natural_km2, 4),
                disaster_progression_km2=round(step_disaster_km2, 4),
                atmospheric_artifacts_km2=round(step_atmo_km2, 4),
                regions_count=len(step_features),
                dominant_category=dom_cat,
                geojson_features=step_features,
            )
            sequential_steps.append(step_res)

            cumulative_changed_km2 += det_res.total_area_changed_km2
            cumulative_human_km2 += step_human_km2
            cumulative_natural_km2 += step_natural_km2
            cumulative_disaster_km2 += step_disaster_km2

            area_over_time.append({
                "timestamp": obs_to.timestamp_iso,
                "label": obs_to.label,
                "cumulative_change_km2": round(cumulative_changed_km2, 4),
                "interval_change_km2": round(det_res.total_area_changed_km2, 4),
                "percentage_changed": det_res.percentage_changed,
            })
            category_over_time.append({
                "timestamp": obs_to.timestamp_iso,
                "label": obs_to.label,
                "human_growth_km2": round(cumulative_human_km2, 4),
                "natural_shift_km2": round(cumulative_natural_km2, 4),
                "disaster_impact_km2": round(cumulative_disaster_km2, 4),
            })

        return TimeSeriesAnalysisReport(
            timeseries_id=ts_id,
            title=ts_title,
            observation_count=len(sorted_obs),
            observations_summary=obs_summaries,
            total_duration_days=round(total_duration_days, 2),
            overall_human_growth_km2=round(cumulative_human_km2, 4),
            overall_natural_shift_km2=round(cumulative_natural_km2, 4),
            overall_disaster_impact_km2=round(cumulative_disaster_km2, 4),
            sequential_steps=sequential_steps,
            area_over_time_series=area_over_time,
            category_over_time_series=category_over_time,
            availability_notice=TIMELINE_AVAILABILITY_DISCLAIMER,
            model_version=self.model_version,
        )
