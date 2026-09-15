"""
Pydantic schemas for multi-temporal analysis, baseline execution & GeoJSON delivery.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CheckStatusEnum(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    UNAVAILABLE = "UNAVAILABLE"


class ValidationCheckItem(BaseModel):
    """Single diagnostic verification item."""
    name: str = Field(..., description="Check name (e.g. Spatial Overlap, CRS Alignment)")
    status: CheckStatusEnum = Field(..., description="PASS, WARNING, FAIL, or UNAVAILABLE")
    score_deduction: int = Field(default=0, description="Score impact points deducted")
    message: str = Field(..., description="Human-readable diagnostic summary")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic parameters")


class AnalysisValidationRequest(BaseModel):
    """Request payload for validating a multi-temporal satellite image pair."""
    image_before_id: Optional[str] = Field(None, description="UUID or filename of baseline image (T1)")
    image_after_id: Optional[str] = Field(None, description="UUID or filename of comparison image (T2)")
    image_before_path: Optional[str] = Field(None, description="Direct file path of baseline image (T1)")
    image_after_path: Optional[str] = Field(None, description="Direct file path of comparison image (T2)")
    satellite: Optional[str] = Field(None, description="Expected satellite source hint")


class AnalysisValidationResponse(BaseModel):
    """Response payload for multi-temporal satellite pair compatibility."""
    is_valid: bool = Field(..., description="True if pair passes minimal criteria for inference")
    data_quality_score: int = Field(..., ge=0, le=100, description="Overall Data Quality Score (0 - 100)")
    recommendation: str = Field(
        ..., description="READY_FOR_INFERENCE, REQUIRES_PREPROCESSING, or INCOMPATIBLE_PAIR"
    )
    spatial_overlap_percentage: Optional[float] = Field(None, description="Intersection area percentage")
    temporal_delta_days: Optional[int] = Field(None, description="Acquisition interval in days (T2 - T1)")
    checks_matrix: List[ValidationCheckItem] = Field(
        ..., description="Complete compatibility diagnostic matrix"
    )
    image1_metadata: Dict[str, Any] = Field(..., description="Extracted metadata for Image 1")
    image2_metadata: Dict[str, Any] = Field(..., description="Extracted metadata for Image 2")


class AnalysisRunRequest(BaseModel):
    """Optional configuration parameters when triggering change detection."""
    image_before_id: Optional[str] = None
    image_after_id: Optional[str] = None
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    model_name: Optional[str] = "Spectral Baseline Difference"


class ChangeStatisticsSchema(BaseModel):
    """Aggregated change statistics."""
    total_area_m2: float
    total_area_km2: float
    total_area_changed_m2: float
    total_area_changed_km2: float
    percentage_changed: float
    total_pixels_changed: int
    region_count: int


class SingleIndexDetailSchema(BaseModel):
    """Details and statistics for a single spectral index (NDVI, NDWI, NDBI)."""
    index_name: str
    is_available: bool
    required_bands: List[str]
    missing_bands: List[str] = Field(default_factory=list)
    t1_mean: Optional[float] = None
    t2_mean: Optional[float] = None
    delta_mean: Optional[float] = None
    delta_min: Optional[float] = None
    delta_max: Optional[float] = None
    delta_std: Optional[float] = None
    significant_increase_pct: Optional[float] = None
    significant_decrease_pct: Optional[float] = None
    interpretation: str = "Index evaluation unavailable"


class SpectralAnalysisSchema(BaseModel):
    """Complete spectral index evaluation results."""
    is_multispectral: bool
    band_count_t1: int
    band_count_t2: int
    detected_bands: List[str] = Field(default_factory=list)
    ndvi: SingleIndexDetailSchema
    ndwi: SingleIndexDetailSchema
    ndbi: SingleIndexDetailSchema
    supporting_evidence_summary: List[str] = Field(default_factory=list)


class AnalysisDetailResponse(BaseModel):
    """Complete analysis record with statistics, spectral indices and metadata."""
    id: str
    title: str
    status: str
    model_name: str
    model_version: str
    label: str = "Baseline / Demo Result"
    disclaimer: str
    image_before_id: Optional[str] = None
    image_after_id: Optional[str] = None
    statistics: Optional[ChangeStatisticsSchema] = None
    registration_metrics: Optional[Dict[str, Any]] = None
    spectral_analysis: Optional[SpectralAnalysisSchema] = None
    created_at: Optional[str] = None


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature representation of a localized change polygon."""
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]


class ChangeRegionsGeoJSONResponse(BaseModel):
    """GeoJSON FeatureCollection representing all detected change boundaries."""
    type: str = "FeatureCollection"
    analysis_id: str
    model_name: str
    label: str = "Baseline / Demo Result"
    statistics: ChangeStatisticsSchema
    spectral_analysis: Optional[SpectralAnalysisSchema] = None
    features: List[GeoJSONFeature]
