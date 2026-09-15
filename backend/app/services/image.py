"""
Image upload service — validation, secure naming, metadata extraction, and persistence.
"""

import os
import re
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.core.errors import ImageValidationError
from app.core.logging import logger
from app.storage.local import get_storage_backend, compute_sha256
from app.gis.metadata import extract_geospatial_metadata

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_GEOTIFF_EXTENSIONS = {".tif", ".tiff"}
ALLOWED_DEMO_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_EXTENSIONS = ALLOWED_GEOTIFF_EXTENSIONS | ALLOWED_DEMO_EXTENSIONS

MIME_MAP = {
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB
MIN_FILE_SIZE_BYTES = 1024  # 1 KB (reject trivially empty uploads)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize_filename(original: str) -> str:
    """
    Create a secure filename that prevents path traversal and collisions.
    Format: <uuid>_<cleaned_basename><ext>
    """
    basename = Path(original).stem
    ext = Path(original).suffix.lower()
    cleaned = re.sub(r"[^\w\-]", "_", basename)[:80]
    unique_id = uuid.uuid4().hex[:12]
    return f"{unique_id}_{cleaned}{ext}"


def detect_mime_type(filename: str, content_type: Optional[str]) -> str:
    """Return canonical MIME type from extension."""
    ext = Path(filename).suffix.lower()
    return MIME_MAP.get(ext, content_type or "application/octet-stream")


def detect_format_label(ext: str, is_georeferenced: bool = False) -> str:
    """Return a human-readable format label."""
    ext = ext.lower()
    if ext in (".tif", ".tiff"):
        return "GeoTIFF" if is_georeferenced else "TIFF"
    if ext in (".jpg", ".jpeg"):
        return "JPEG (demo — non-georeferenced)"
    if ext == ".png":
        return "PNG (demo — non-georeferenced)"
    return "Unknown"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_upload(
    original_filename: str,
    content_type: Optional[str],
    file_size: int,
) -> Tuple[str, str]:
    """
    Validate file extension, MIME type, and file size.
    Returns (ext, mime_type) on success; raises ImageValidationError on failure.
    """
    ext = Path(original_filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise ImageValidationError(
            message=f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            details={"extension": ext, "allowed": sorted(ALLOWED_EXTENSIONS)},
        )

    mime = detect_mime_type(original_filename, content_type)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ImageValidationError(
            message=f"File size ({file_size:,} bytes) exceeds maximum ({MAX_FILE_SIZE_BYTES:,} bytes).",
            details={"file_size": file_size, "max_size": MAX_FILE_SIZE_BYTES},
        )

    if file_size < MIN_FILE_SIZE_BYTES:
        raise ImageValidationError(
            message="File is too small — appears to be empty or corrupted.",
            details={"file_size": file_size, "min_size": MIN_FILE_SIZE_BYTES},
        )

    return ext, mime


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def process_image_upload(
    file_content: bytes,
    original_filename: str,
    content_type: Optional[str],
) -> Dict[str, Any]:
    """
    Full upload pipeline:
    1. Validate extension, MIME, file size
    2. Sanitize filename
    3. Compute SHA-256 checksum
    4. Store file via storage backend
    5. Extract geospatial metadata via Rasterio
    6. Return structured response dict
    """
    file_size = len(file_content)
    ext, mime = validate_upload(original_filename, content_type, file_size)

    safe_filename = sanitize_filename(original_filename)

    # Compute checksum
    file_obj = BytesIO(file_content)
    checksum = compute_sha256(file_obj)

    # Store through abstraction layer
    storage = get_storage_backend()
    stored_path = storage.save(file_obj, safe_filename)

    # Extract metadata using Rasterio / PIL
    metadata = extract_geospatial_metadata(stored_path)
    is_georeferenced = metadata.get("is_georeferenced", False)
    format_label = detect_format_label(ext, is_georeferenced)

    image_id = str(uuid.uuid4())

    return {
        "image_id": image_id,
        "filename": safe_filename,
        "original_filename": original_filename,
        "file_size_bytes": file_size,
        "mime_type": mime,
        "format": format_label,
        "is_georeferenced": is_georeferenced,
        "status": "uploaded",
        "checksum_sha256": checksum,
        "file_path": stored_path,
        "metadata": metadata,
    }
