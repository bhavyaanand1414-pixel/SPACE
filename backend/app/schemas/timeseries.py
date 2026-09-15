"""
Pydantic Schemas for Multi-Temporal Time-Series Analysis.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.timeseries.engine import TIMELINE_AVAILABILITY_DISCLAIMER


class ObservationInputSchema(BaseModel):
    """Input parameters for a single satellite observation slice."""
    observation_id: str = Field(..., description="Unique ID for this temporal acquisition")
    timestamp_iso: str = Field(..., description="Acquisition datetime in ISO format (e.g. 2020-01-15T10:00:00Z)")
    label: str = Field(..., description="Human readable label (e.g. T1 - 2020 Baseline)")
    image_id_or_path: Optional[str] = Field(None, description="Image ID or file path in storage")
    satellite: Optional[str] = Field(None, description="Satellite sensor (e.g. Sentinel-2, Landsat-8)")
    resolution_m: float = Field(default=10.0, description="Spatial resolution in meters")


class TimeSeriesAnalysisRequest(BaseModel):
    """Request payload for running time-series progression analysis."""
    timeseries_id: Optional[str] = None
    title: Optional[str] = "Multi-Temporal Satellite Timeline Analysis"
    observations: List[ObservationInputSchema] = Field(
        ..., min_length=2, description="Ordered sequence of >= 2 satellite observations"
    )


class TimeSeriesStepSchema(BaseModel):
    """Change statistics between sequential observations."""
    step_index: int
    from_observation_id: str
    to_observation_id: str
    from_timestamp: str
    to_timestamp: str
    interval_days: float
    interval_human_readable: str
    changed_area_m2: float
    changed_area_km2: float
    percentage_changed: float
    human_growth_km2: float
    natural_progression_km2: float
    disaster_progression_km2: float
    atmospheric_artifacts_km2: float
    regions_count: int
    dominant_category: str
    geojson_features: List[Dict[str, Any]] = Field(default_factory=list)


class TimeSeriesAnalysisResponse(BaseModel):
    """Complete time-series progression report with area and category trajectories."""
    timeseries_id: str
    title: str
    observation_count: int
    observations_summary: List[Dict[str, Any]]
    total_duration_days: float
    overall_human_growth_km2: float
    overall_natural_shift_km2: float
    overall_disaster_impact_km2: float
    sequential_steps: List[TimeSeriesStepSchema]
    area_over_time_series: List[Dict[str, Any]]
    category_over_time_series: List[Dict[str, Any]]
    availability_notice: str = TIMELINE_AVAILABILITY_DISCLAIMER
    model_version: str = "1.0.0"
    created_at: str
