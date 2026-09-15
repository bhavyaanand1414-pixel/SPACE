"""Pydantic schemas for satellite image upload and response."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ImageUploadResponse(BaseModel):
    """Response returned after a successful image upload."""
    image_id: str = Field(..., description="Unique image identifier (UUID)")
    filename: str = Field(..., description="Sanitized storage filename")
    original_filename: str = Field(..., description="Original uploaded filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="Detected MIME type")
    format: str = Field(..., description="Raster format (GeoTIFF, TIFF, JPEG, PNG)")
    is_georeferenced: bool = Field(..., description="Whether the file contains a valid CRS")
    status: str = Field(default="uploaded", description="Upload processing status")
    checksum_sha256: Optional[str] = Field(None, description="SHA-256 file checksum")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Extracted raster metadata")


class RasterMetadataResponse(BaseModel):
    """Extracted metadata from a raster tile."""
    width: int
    height: int
    band_count: int
    crs: Optional[str] = None
    epsg_code: Optional[int] = None
    resolution_x: Optional[float] = None
    resolution_y: Optional[float] = None
    bounds_min_x: Optional[float] = None
    bounds_min_y: Optional[float] = None
    bounds_max_x: Optional[float] = None
    bounds_max_y: Optional[float] = None
    dtype: Optional[str] = None


class ImageValidationErrorResponse(BaseModel):
    """Error response for image validation failures."""
    error: Dict[str, Any]
