"""
Image upload API endpoint — POST /api/v1/images/upload
"""

from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from app.services.image import process_image_upload
from app.schemas.image import ImageUploadResponse

router = APIRouter(prefix="/images", tags=["Satellite Imagery"])


@router.post(
    "/upload",
    response_model=ImageUploadResponse,
    summary="Upload a satellite image tile",
    description=(
        "Upload a GeoTIFF/TIFF satellite raster tile for change detection analysis. "
        "JPEG and PNG files are also accepted as clearly labeled non-georeferenced demo inputs. "
        "The endpoint validates file extension, MIME type, file size, and extracts raster metadata."
    ),
)
async def upload_image(
    file: UploadFile = File(..., description="Satellite imagery file (GeoTIFF, TIFF, JPEG, or PNG)"),
    satellite: Optional[str] = Form(None, description="Satellite source (e.g., sentinel-2, sentinel-1, landsat)"),
):
    """
    Upload and validate a satellite image tile.

    Steps performed:
    1. Validate file extension (.tif, .tiff, .jpg, .jpeg, .png)
    2. Validate MIME type and file size (max 2 GB)
    3. Generate secure filename (prevent path traversal)
    4. Compute SHA-256 checksum
    5. Store file via storage abstraction layer
    6. Extract raster metadata (dimensions, bands, CRS, resolution, bounds) for GeoTIFF
    7. Return image_id, filename, size, format, and status

    AI analysis is NOT triggered — use the analysis endpoints for that.
    """
    content = await file.read()

    result = await process_image_upload(
        file_content=content,
        original_filename=file.filename or "unknown.tif",
        content_type=file.content_type,
    )

    # Add satellite hint if provided
    if satellite and result.get("metadata"):
        result["metadata"]["satellite"] = satellite

    return ImageUploadResponse(**result)
