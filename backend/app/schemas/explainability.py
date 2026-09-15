"""
Pydantic Schemas for Explainability and Uncertainty Diagnostics.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ReliabilitySchema(BaseModel):
    """System & model composite reliability score indicator."""
    model_confidence_pct: float = Field(..., description="Model classification confidence percentage")
    image_quality_pct: float = Field(..., description="Data Quality Score percentage")
    registration_quality_pct: float = Field(..., description="Co-registration correlation percentage")
    overall_reliability: str = Field(..., description="HIGH, MEDIUM, or LOW")
    overall_score: float = Field(..., description="Weighted composite reliability score [0-100]")
    formula_basis: str = Field(default="Composite: 0.40*ModelConf + 0.35*RegQual + 0.25*ImgQual")


class RegionExplanationResponse(BaseModel):
    """Complete 'Why was this detected?' explanation payload."""
    region_index: int
    category: str
    subcategory: str
    confidence_pct: float
    spectral_evidence: Dict[str, Any] = Field(default_factory=dict)
    geometric_evidence: Dict[str, Any] = Field(default_factory=dict)
    decision_rule: str
    explanation_narrative: str
    t1_crop_data_url: Optional[str] = None
    t2_crop_data_url: Optional[str] = None
    mask_crop_data_url: Optional[str] = None
    saliency_heatmap_data_url: Optional[str] = None
    reliability: Optional[ReliabilitySchema] = None
    timestamp: str
