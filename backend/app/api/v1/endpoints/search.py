"""
Semantic Search API Endpoints (PS 26227 §2.2.1).

Provides text-to-image and image-to-image search over the indexed
satellite imagery archive.
"""

import io
import time
from typing import Optional

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from PIL import Image as PILImage

from app.core.logging import logger
from app.schemas.search import (
    ChangeAnalysisRequest,
    ChangeAnalysisResponse,
    ChangeEventSchema,
    SearchFiltersSchema,
    SearchResultItem,
    SearchResultsResponse,
    TextSearchRequest,
)
from app.services.search import SearchFilters, SemanticSearchService

router = APIRouter(prefix="/search", tags=["Semantic Search (PS 26227 §2.2.1)"])


@router.post(
    "/text",
    response_model=SearchResultsResponse,
    summary="Text-to-Image Semantic Search",
    description=(
        "Search the satellite imagery archive using a natural-language query. "
        "Example queries: 'newly built structures near a river', "
        "'large vehicle concentrations on open ground'."
    ),
)
async def text_search(request: TextSearchRequest):
    """Search archive tiles by natural-language text query."""
    start = time.time()

    filters = None
    if request.filters:
        filters = SearchFilters(
            aoi_geojson=request.filters.aoi_geojson,
            date_from=request.filters.date_from,
            date_to=request.filters.date_to,
            satellite=request.filters.satellite,
            sensor=request.filters.sensor,
            min_quality=request.filters.min_quality,
        )

    try:
        results = SemanticSearchService.text_search(
            query=request.query,
            filters=filters,
            k=request.limit,
        )
    except Exception as exc:
        logger.error(f"Text search error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(exc)}",
        )

    latency = (time.time() - start) * 1000

    return SearchResultsResponse(
        query=request.query,
        total_results=len(results),
        results=[
            SearchResultItem(
                tile_id=r.tile_id,
                scene_id=r.scene_id,
                similarity_score=r.similarity_score,
                bbox=list(r.bbox),
                acquisition_date=r.acquisition_date,
                satellite=r.satellite,
                sensor=r.sensor,
                thumbnail_url=r.thumbnail_url,
                quality_score=r.quality_score,
            )
            for r in results
        ],
        search_type="text",
        latency_ms=round(latency, 2),
    )


@router.post(
    "/image",
    response_model=SearchResultsResponse,
    summary="Image-to-Image Visual Search",
    description="Search for visually similar satellite tiles by uploading a query image.",
)
async def image_search(
    file: UploadFile = File(..., description="Query image (PNG, JPEG, or TIFF)"),
    limit: int = Form(50, ge=1, le=200),
    satellite: Optional[str] = Form(None),
    date_from: Optional[str] = Form(None),
    date_to: Optional[str] = Form(None),
):
    """Search archive tiles by visual similarity to an uploaded image."""
    start = time.time()

    # Read and decode the uploaded image
    try:
        content = await file.read()
        pil_image = PILImage.open(io.BytesIO(content)).convert("RGB")
        image_array = np.array(pil_image)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not decode uploaded image: {str(exc)}",
        )

    filters = SearchFilters(satellite=satellite)
    if date_from:
        from datetime import datetime
        try:
            filters.date_from = datetime.fromisoformat(date_from)
        except ValueError:
            pass
    if date_to:
        from datetime import datetime
        try:
            filters.date_to = datetime.fromisoformat(date_to)
        except ValueError:
            pass

    try:
        results = SemanticSearchService.image_search(
            image=image_array,
            filters=filters,
            k=limit,
        )
    except Exception as exc:
        logger.error(f"Image search error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(exc)}",
        )

    latency = (time.time() - start) * 1000

    return SearchResultsResponse(
        query=f"[image: {file.filename}]",
        total_results=len(results),
        results=[
            SearchResultItem(
                tile_id=r.tile_id,
                scene_id=r.scene_id,
                similarity_score=r.similarity_score,
                bbox=list(r.bbox),
                acquisition_date=r.acquisition_date,
                satellite=r.satellite,
                sensor=r.sensor,
                quality_score=r.quality_score,
            )
            for r in results
        ],
        search_type="image",
        latency_ms=round(latency, 2),
    )
