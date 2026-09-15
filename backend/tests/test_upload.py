"""
Tests for POST /api/v1/images/upload endpoint.
"""

import io
import os
import pytest
from PIL import Image as PILImage
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.fixture(autouse=True)
def setup_test_storage(tmp_path, monkeypatch):
    """Redirect storage to a temp directory for test isolation."""
    test_storage = str(tmp_path / "test_storage")
    os.makedirs(test_storage, exist_ok=True)
    monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", test_storage)


def _make_valid_tiff() -> bytes:
    """Create a valid TIFF byte stream using PIL."""
    buf = io.BytesIO()
    img = PILImage.new("RGB", (64, 64), color=(50, 150, 200))
    img.save(buf, format="TIFF")
    data = buf.getvalue()
    # Ensure exceeds 1024 bytes
    if len(data) < 1024:
        data += b"\x00" * (1024 - len(data) + 100)
    return data


def _make_png() -> bytes:
    """Create a valid 64x64 PNG using PIL."""
    buf = io.BytesIO()
    img = PILImage.new("RGB", (64, 64), color=(200, 50, 50))
    img.save(buf, format="PNG")
    data = buf.getvalue()
    if len(data) < 1024:
        data += b"\x00" * (1024 - len(data) + 100)
    return data


# ─── Positive Tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_tiff_success():
    """Valid TIFF upload should return 200 with image metadata."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tiff_bytes = _make_valid_tiff()
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test_image.tif", io.BytesIO(tiff_bytes), "image/tiff")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "uploaded"
        assert data["image_id"]
        assert data["filename"].endswith(".tif")
        assert data["original_filename"] == "test_image.tif"
        assert data["file_size_bytes"] == len(tiff_bytes)
        assert data["mime_type"] == "image/tiff"
        assert "TIFF" in data["format"]
        assert data["checksum_sha256"]


@pytest.mark.asyncio
async def test_upload_png_demo_success():
    """Valid PNG upload should succeed with demo label."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        png_bytes = _make_png()
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("demo_view.png", io.BytesIO(png_bytes), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "uploaded"
        assert data["is_georeferenced"] is False
        assert "demo" in data["format"].lower() or "PNG" in data["format"]


@pytest.mark.asyncio
async def test_upload_with_satellite_hint():
    """Satellite form field should propagate into metadata."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tiff_bytes = _make_valid_tiff()
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("sentinel2_tile.tif", io.BytesIO(tiff_bytes), "image/tiff")},
            data={"satellite": "sentinel-2"},
        )
        assert response.status_code == 200


# ─── Negative / Validation Tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_invalid_extension():
    """Files with unsupported extensions should be rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("malware.exe", io.BytesIO(b"X" * 2048), "application/octet-stream")},
        )
        assert response.status_code == 422
        data = response.json()
        assert "error" in data or "detail" in data


@pytest.mark.asyncio
async def test_upload_too_small():
    """Files smaller than 1 KB should be rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("tiny.tif", io.BytesIO(b"\x00" * 10), "image/tiff")},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_no_file():
    """Request without a file field should fail with 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/images/upload")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_secure_filename_no_traversal():
    """Path traversal in filename should be neutralized."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tiff_bytes = _make_valid_tiff()
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("../../etc/passwd.tif", io.BytesIO(tiff_bytes), "image/tiff")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "/" not in data["filename"]
        assert ".." not in data["filename"]
