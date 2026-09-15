"""
Pydantic Schemas for Disaster Assessment APIs.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.disaster.base import DisasterType, DISASTER_CAUTIONARY_DISCLAIMER


class DisasterAssessmentRequest(BaseModel):
    """Request payload for disaster hazard assessment."""
    image_before_id: Optional[str] = None
    image_after_id: Optional[str] = None
    image_before_path: Optional[str] = None
    image_after_path: Optional[str] = None
    disaster_type: DisasterType = DisasterType.FLOOD
    is_sar: bool = Field(default=False, description="Set to True if input rasters are Sentinel-1 SAR amplitude")
    resolution_m: float = Field(default=10.0, description="Spatial resolution in meters")


class DisasterAssessmentResponse(BaseModel):
    """Standard response schema for disaster assessment with non-causal disclaimer."""
    disaster_type: DisasterType
    title: str
    affected_area_m2: float
    affected_area_km2: float
    percentage_area_affected: float
    severity_level: str
    confidence_score: float
    affected_regions_count: int
    modality_used: str
    causality_wording: str
    advisory_disclaimer: str = DISASTER_CAUTIONARY_DISCLAIMER
    evidence_metrics: Dict[str, Any] = Field(default_factory=dict)
    geojson_features: List[Dict[str, Any]] = Field(default_factory=list)
    model_version: str = "1.0.0"
    timestamp: str
