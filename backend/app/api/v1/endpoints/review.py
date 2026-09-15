"""
Human-In-The-Loop (HITL) Review and Active Learning APIs.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.core.logging import logger
from app.schemas.review import (
    ActiveLearningExportResponse,
    AnalysisReviewSubmissionRequest,
    ReviewItemRecord,
    ReviewQueueResponse,
    ReviewStatusEnum,
)
from app.services.review import ReviewService

router = APIRouter(tags=["Human-In-The-Loop Review & Active Learning"])


@router.post(
    "/analyses/{analysis_id}/review",
    response_model=List[ReviewItemRecord],
    summary="Submit Human Review & Taxonomic Corrections for Change Polygons",
    description=(
        "Allows GIS analysts to correct model predictions across Level 1 & Level 2 hierarchies, "
        "approve high-certainty detections, or reject false positives. "
        "Stores complete audit trail: original prediction, human correction, reviewer, model version, timestamp."
    ),
)
async def submit_analysis_review(analysis_id: str, payload: AnalysisReviewSubmissionRequest):
    """Submit human review corrections for an analysis."""
    try:
        updated = ReviewService.submit_reviews(
            analysis_id=analysis_id,
            corrections=payload.reviews,
            reviewer_name=payload.reviewer_name,
        )
        return updated
    except Exception as exc:
        logger.exception(f"Failed to submit review: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit review: {str(exc)}",
        )


@router.get(
    "/analyses/{analysis_id}/reviews",
    response_model=List[ReviewItemRecord],
    summary="Get Human Reviews for an Analysis",
)
async def get_analysis_reviews(analysis_id: str):
    """Get all human review records for a specific analysis."""
    queue = ReviewService.get_review_queue(analysis_id=analysis_id)
    return queue.items


@router.get(
    "/review/queue",
    response_model=ReviewQueueResponse,
    summary="Get Global Review Queue for Human-In-The-Loop Verification",
    description="Lists all low-confidence (<0.80) or ambiguous change regions awaiting expert human verification.",
)
async def get_global_review_queue(
    status_filter: Optional[ReviewStatusEnum] = Query(None, description="Filter by PENDING, APPROVED, CORRECTED, or REJECTED"),
):
    """Get global review queue items."""
    return ReviewService.get_review_queue(status_filter=status_filter)


@router.post(
    "/review/export-candidates",
    response_model=ActiveLearningExportResponse,
    summary="Export Verified Corrections to Active Learning Training Candidate Dataset",
    description="Stages verified human corrections as training candidates. Enforces rule: Does NOT automatically retrain production models.",
)
async def export_active_learning_candidates():
    """Export approved and corrected samples into an active learning dataset."""
    result = ReviewService.export_active_learning_dataset()
    return ActiveLearningExportResponse(**result)
