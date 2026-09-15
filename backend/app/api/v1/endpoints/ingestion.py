"""
Ingestion API Endpoints (PS 26227 §2.2.6).

Upload and ingest GeoTIFF/COG satellite scenes into the archive with
incremental vector indexing.
"""

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.logging import logger
from app.schemas.search import (
    DirectoryIngestionRequest,
    IndexStatusResponse,
    IngestionRequest,
    IngestionResultSchema,
)
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/ingest", tags=["Ingestion Pipeline (PS 26227 §2.2.6)"])


@router.post(
    "/scene",
    response_model=IngestionResultSchema,
    summary="Ingest a Single Scene",
    description=(
        "Ingest a GeoTIFF/COG scene from a server-side path: extract metadata, "
        "tile, embed (CLIP), and add to FAISS index incrementally."
    ),
)
async def ingest_scene(request: IngestionRequest):
    """Ingest a single scene by server-side file path."""
    import os
    if not os.path.exists(request.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {request.file_path}",
        )

    try:
        result = IngestionService.ingest_scene(
            file_path=request.file_path,
            satellite=request.satellite,
            sensor=request.sensor,
            acquisition_datetime=request.acquisition_datetime,
            scl_path=request.scl_path,
        )

        return IngestionResultSchema(
            scene_id=result.scene_id,
            filename=result.filename,
            status=result.status,
            tile_count=result.tile_count,
            embedding_count=result.embedding_count,
            error=result.error,
            duration_sec=round(result.duration_sec, 2),
        )
    except Exception as exc:
        logger.error(f"Scene ingestion API error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(exc)}",
        )


@router.post(
    "/directory",
    summary="Batch Ingest Directory",
    description="Ingest all GeoTIFF/COG scenes in a server-side directory.",
)
async def ingest_directory(request: DirectoryIngestionRequest):
    """Batch ingest all scenes in a directory."""
    import os
    if not os.path.isdir(request.directory_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Directory not found: {request.directory_path}",
        )

    try:
        results = IngestionService.ingest_directory(
            dir_path=request.directory_path,
            satellite=request.satellite,
            sensor=request.sensor,
        )

        return {
            "total_scenes": len(results),
            "completed": sum(1 for r in results if r.status == "completed"),
            "failed": sum(1 for r in results if r.status == "failed"),
            "total_tiles": sum(r.tile_count for r in results),
            "results": [
                IngestionResultSchema(
                    scene_id=r.scene_id,
                    filename=r.filename,
                    status=r.status,
                    tile_count=r.tile_count,
                    embedding_count=r.embedding_count,
                    error=r.error,
                    duration_sec=round(r.duration_sec, 2),
                )
                for r in results
            ],
        }
    except Exception as exc:
        logger.error(f"Directory ingestion API error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch ingestion failed: {str(exc)}",
        )


@router.post(
    "/upload",
    response_model=IngestionResultSchema,
    summary="Upload and Ingest Scene",
    description="Upload a GeoTIFF file and ingest it into the archive.",
)
async def upload_and_ingest(
    file: UploadFile = File(..., description="GeoTIFF or COG scene file"),
    satellite: Optional[str] = Form(None),
    sensor: Optional[str] = Form(None),
):
    """Upload a scene file and ingest it into the archive."""
    import os
    import tempfile
    from pathlib import Path
    from app.core.config import settings

    # Save uploaded file to scenes storage
    scenes_dir = Path(settings.SCENES_STORAGE_PATH)
    scenes_dir.mkdir(parents=True, exist_ok=True)
    dest = scenes_dir / file.filename

    try:
        content = await file.read()
        dest.write_bytes(content)

        result = IngestionService.ingest_scene(
            file_path=str(dest),
            satellite=satellite,
            sensor=sensor,
        )

        return IngestionResultSchema(
            scene_id=result.scene_id,
            filename=result.filename,
            status=result.status,
            tile_count=result.tile_count,
            embedding_count=result.embedding_count,
            error=result.error,
            duration_sec=round(result.duration_sec, 2),
        )
    except Exception as exc:
        logger.error(f"Upload ingestion error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload ingestion failed: {str(exc)}",
        )


@router.get(
    "/status",
    response_model=IndexStatusResponse,
    summary="Index Status",
    description="Get current FAISS index statistics.",
)
async def index_status():
    """Return current vector index statistics."""
    return IngestionService.get_index_status()
