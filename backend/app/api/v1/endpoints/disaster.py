"""
Disaster Assessment API Endpoints — Flood, Wildfire, Landslide, Earthquake, and Cyclone.
"""

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.logging import logger
from app.disaster.base import DisasterType
from app.disaster.cyclone import CycloneImpactAnalyzer
from app.disaster.earthquake import EarthquakeDamageAnalyzer
from app.disaster.flood import FloodInundationAnalyzer
from app.disaster.landslide import LandslideScarAnalyzer
from app.disaster.wildfire import WildfireBurnScarAnalyzer
from app.gis.preprocessing import RemoteSensingPreprocessor
from app.schemas.disaster import DisasterAssessmentRequest, DisasterAssessmentResponse

router = APIRouter(prefix="/disaster", tags=["Disaster & Emergency Assessment"])


def _resolve_image_path(image_id_or_path: Optional[str]) -> Optional[str]:
    """Resolve image identifier or filename to an existing file in storage."""
    if not image_id_or_path:
        return None

    p = Path(image_id_or_path)
    if p.is_file():
        return str(p)

    storage_root = Path(settings.LOCAL_STORAGE_PATH).resolve()
    exact = storage_root / p.name
    if exact.is_file():
        return str(exact)

    for f in storage_root.glob(f"*{image_id_or_path}*"):
        if f.is_file():
            return str(f)

    return None


@router.post(
    "/analyze",
    response_model=DisasterAssessmentResponse,
    summary="Execute Multi-Hazard Disaster Damage Assessment",
    description=(
        "Executes specialized damage and hazard extent mapping for Flood, Wildfire, "
        "Earthquake, Landslide, or Cyclone events. Returns affected area metrics, severity grades, "
        "vectorized polygons, and mandatory cautionary advisory disclaimers."
    ),
)
async def analyze_disaster_event(payload: DisasterAssessmentRequest):
    """Run disaster hazard assessment."""
    path1 = payload.image_before_path or _resolve_image_path(payload.image_before_id)
    path2 = payload.image_after_path or _resolve_image_path(payload.image_after_id)

    if not path1 or not path2:
        storage_root = Path(settings.LOCAL_STORAGE_PATH).resolve()
        files = [str(f) for f in storage_root.glob("*.*") if f.suffix.lower() in [".tif", ".tiff", ".png", ".jpg"]]
        if len(files) >= 2:
            path1 = path1 or files[0]
            path2 = path2 or files[1]

    if not path1 or not path2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two satellite images (pre-event and post-event) are required for disaster assessment.",
        )

    try:
        # Preprocessing & Co-Registration
        preprocessor = RemoteSensingPreprocessor(enable_coregistration=True)
        ready_pair = preprocessor.process_files(path1, path2)

        # Dispatch to appropriate analyzer
        if payload.disaster_type == DisasterType.FLOOD:
            analyzer = FloodInundationAnalyzer()
        elif payload.disaster_type == DisasterType.WILDFIRE:
            analyzer = WildfireBurnScarAnalyzer()
        elif payload.disaster_type == DisasterType.EARTHQUAKE:
            analyzer = EarthquakeDamageAnalyzer()
        elif payload.disaster_type == DisasterType.LANDSLIDE:
            analyzer = LandslideScarAnalyzer()
        elif payload.disaster_type == DisasterType.CYCLONE:
            analyzer = CycloneImpactAnalyzer()
        else:
            analyzer = FloodInundationAnalyzer()

        result = analyzer.analyze(
            image_before=ready_pair.image1_array,
            image_after=ready_pair.image2_array,
            resolution_m=payload.resolution_m,
            spatial_transform=ready_pair.transform,
            is_sar=payload.is_sar,
        )

        return DisasterAssessmentResponse(
            disaster_type=result.disaster_type,
            title=result.title,
            affected_area_m2=result.affected_area_m2,
            affected_area_km2=result.affected_area_km2,
            percentage_area_affected=result.percentage_area_affected,
            severity_level=result.severity_level,
            confidence_score=result.confidence_score,
            affected_regions_count=result.affected_regions_count,
            modality_used=result.modality_used,
            causality_wording=result.causality_wording,
            advisory_disclaimer=result.advisory_disclaimer,
            evidence_metrics=result.evidence_metrics,
            geojson_features=result.geojson_features,
            model_version=result.model_version,
            timestamp=result.timestamp,
        )

    except Exception as exc:
        logger.exception(f"Disaster analysis failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Disaster analysis failed: {str(exc)}",
        )


@router.post(
    "/flood",
    response_model=DisasterAssessmentResponse,
    summary="Rapid Flood & Inundation Mapping (Optical & Sentinel-1 SAR)",
    description="Dedicated rapid mapping endpoint for flood inundation and surface water surge.",
)
async def analyze_flood_event(payload: DisasterAssessmentRequest):
    """Dedicated rapid flood mapping endpoint."""
    payload.disaster_type = DisasterType.FLOOD
    return await analyze_disaster_event(payload)
