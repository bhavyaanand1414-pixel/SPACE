"""
Pydantic Schemas for Human-In-The-Loop (HITL) Review and Active Learning Readiness.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReviewStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    CORRECTED = "CORRECTED"
    REJECTED = "REJECTED"


class HumanCorrectionInput(BaseModel):
    """Payload for correcting or approving a single change region."""
    region_index: int = Field(..., description="Index of the change region within the analysis")
    status: ReviewStatusEnum = Field(default=ReviewStatusEnum.CORRECTED, description="APPROVED, CORRECTED, or REJECTED")
    corrected_category: Optional[str] = Field(None, description="Human corrected Level-1 category (HUMAN, NATURAL, DISASTER, ATMOSPHERIC, UNKNOWN)")
    corrected_subcategory: Optional[str] = Field(None, description="Human corrected Level-2 subcategory (e.g. Building, Road, Flood)")
    reviewer_name: str = Field(default="GIS Analyst", description="Name or ID of reviewer")
    notes: Optional[str] = Field(None, description="Reviewer justification or notes")
    mark_as_training_candidate: bool = Field(default=True, description="Add to active learning candidate training set")


class AnalysisReviewSubmissionRequest(BaseModel):
    """Request payload to submit human reviews for an analysis."""
    reviewer_name: str = Field(default="GIS Expert Reviewer")
    reviews: List[HumanCorrectionInput] = Field(..., min_length=1)


class ReviewItemRecord(BaseModel):
    """Stored human review record with complete audit trail."""
    review_id: str
    analysis_id: str
    region_index: int
    original_category: str
    original_subcategory: str
    original_confidence: float
    corrected_category: Optional[str] = None
    corrected_subcategory: Optional[str] = None
    status: ReviewStatusEnum
    reviewer_name: str
    notes: Optional[str] = None
    model_version: str
    is_active_learning_candidate: bool = True
    created_at: str
    updated_at: str


class ReviewQueueResponse(BaseModel):
    """Response containing pending and reviewed items in queue."""
    total_in_queue: int
    pending_count: int
    corrected_count: int
    approved_count: int
    items: List[ReviewItemRecord]


class ActiveLearningExportResponse(BaseModel):
    """Response from exporting active learning training candidates."""
    status: str = "exported"
    candidate_count: int
    export_path: str
    message: str = "Active learning candidates staged. Production models are NOT automatically retrained without explicit verification."
    timestamp: str
