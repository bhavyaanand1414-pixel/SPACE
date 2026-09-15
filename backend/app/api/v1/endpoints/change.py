"""
Archive-Based Change Analysis API (PS 26227 §2.2.2).
"""

from fastapi import APIRouter, HTTPException, status

from app.core.logging import logger
from app.schemas.search import (
    ChangeAnalysisRequest,
    ChangeAnalysisResponse,
    ChangeEventSchema,
)
from app.services.change_archive import ArchiveChangeService

router = APIRouter(prefix="/change", tags=["Change Analysis (PS 26227 §2.2.2)"])


@router.post(
    "/analyze",
    response_model=ChangeAnalysisResponse,
    summary="Archive-Based Multi-Temporal Change Analysis",
    description=(
        "Identify meaningful changes within a specified AOI and time window "
        "by querying the indexed archive. Classifies change types such as "
        "construction, clearance, water-extent variation, and road development."
    ),
)
async def analyze_change(request: ChangeAnalysisRequest):
    """Run change analysis over the indexed archive for an AOI and time window."""
    try:
        result = ArchiveChangeService.analyze_change(
            aoi_geojson=request.aoi_geojson,
            date_from=request.date_from,
            date_to=request.date_to,
            change_types=request.change_types,
        )

        return ChangeAnalysisResponse(
            analysis_id=result.analysis_id,
            total_tiles_analyzed=result.total_tiles_analyzed,
            total_changes_detected=result.total_changes_detected,
            change_events=[
                ChangeEventSchema(
                    change_id=e.change_id,
                    change_type=e.change_type,
                    category=e.category,
                    confidence=e.confidence,
                    area_km2=e.area_km2,
                    earliest_observation=e.earliest_observation,
                    before_tile_id=e.before_tile_id,
                    after_tile_id=e.after_tile_id,
                    before_date=e.before_date,
                    after_date=e.after_date,
                    location=e.location,
                    evidence=e.evidence,
                )
                for e in result.change_events
            ],
            timeline=result.timeline,
            processing_time_sec=round(result.processing_time_sec, 2),
        )
    except Exception as exc:
        logger.error(f"Change analysis error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change analysis failed: {str(exc)}",
        )
