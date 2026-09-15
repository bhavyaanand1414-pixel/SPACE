"""
Tests for Geospatial Metadata Extraction and Pair Compatibility Validation (Phase 6).
"""

import io
import os
import pytest
import numpy as np
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.gis.metadata import extract_geospatial_metadata
from app.gis.validator import validate_raster_pair, calculate_spatial_overlap


@pytest.fixture(autouse=True)
def setup_test_storage(tmp_path, monkeypatch):
    """Redirect storage to a temporary directory."""
    test_storage = str(tmp_path / "test_storage")
    os.makedirs(test_storage, exist_ok=True)
    monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", test_storage)
    return test_storage


def _create_synthetic_geotiff(
    path: str,
    width: int = 100,
    height: int = 100,
    bands: int = 3,
    crs: str = "EPSG:32646",
    left: float = 770000.0,
    bottom: float = 2890000.0,
    resolution: float = 10.0,
    nodata: float = 0.0,
    tags: dict = None,
):
    """Create a real valid GeoTIFF with explicit geospatial transform and metadata tags."""
    import rasterio
    from rasterio.transform import from_origin

    transform = from_origin(left, bottom + height * resolution, resolution, resolution)
    data = np.random.randint(1, 255, (bands, height, width), dtype=np.uint8)

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=bands,
        dtype=data.dtype,
        crs=crs,
        transform=transform,
        nodata=nodata,
    ) as dst:
        dst.write(data)
        if tags:
            dst.update_tags(**tags)


# ─── 1. Metadata Extraction Tests ─────────────────────────────────────────────


def test_metadata_extraction_geotiff(tmp_path):
    """Verify that GeoTIFF metadata is accurately extracted without fabrication."""
    tif_path = str(tmp_path / "sentinel2_tile.tif")
    _create_synthetic_geotiff(
        tif_path,
        width=200,
        height=150,
        bands=4,
        crs="EPSG:32646",
        left=770000.0,
        bottom=2890000.0,
        resolution=10.0,
        nodata=0.0,
        tags={
            "SPACECRAFT_NAME": "Sentinel-2A",
            "INSTRUMENT_NAME": "MSI",
            "DATETIME": "2026-01-15 10:30:00",
            "CLOUDY_PIXEL_PERCENTAGE": "4.5",
        },
    )

    meta = extract_geospatial_metadata(tif_path)

    assert meta["is_georeferenced"] is True
    assert meta["width"] == 200
    assert meta["height"] == 150
    assert meta["band_count"] == 4
    assert meta["epsg_code"] == 32646
    assert meta["resolution_x"] == 10.0
    assert meta["resolution_y"] == 10.0
    assert meta["nodata_value"] == 0.0
    assert meta["satellite"] == "Sentinel-2A"
    assert meta["sensor"] == "MSI"
    assert meta["acquisition_date"] == "2026-01-15"
    assert meta["cloud_coverage_percentage"] == 4.5
    assert meta["bounds"] is not None


def test_metadata_no_fabrication_on_clean_tiff(tmp_path):
    """When tags are missing, metadata fields must return None, never fabricated."""
    tif_path = str(tmp_path / "anonymous_tile.tif")
    _create_synthetic_geotiff(tif_path, width=50, height=50, bands=3)

    meta = extract_geospatial_metadata(tif_path)

    assert meta["is_georeferenced"] is True
    assert meta["satellite"] is None
    assert meta["sensor"] is None
    assert meta["acquisition_date"] is None
    assert meta["cloud_coverage_percentage"] is None


# ─── 2. Spatial Overlap & Compatibility Validator Tests ───────────────────────


def test_validator_perfect_pair(tmp_path):
    """Two matching overlapping images should return high Data Quality Score and PASS."""
    t1_path = str(tmp_path / "img_2020.tif")
    t2_path = str(tmp_path / "img_2026.tif")

    _create_synthetic_geotiff(
        t1_path,
        left=770000.0,
        bottom=2890000.0,
        tags={"DATETIME": "2020-01-15", "CLOUDY_PIXEL_PERCENTAGE": "2.0"},
    )
    _create_synthetic_geotiff(
        t2_path,
        left=770000.0,
        bottom=2890000.0,
        tags={"DATETIME": "2026-01-15", "CLOUDY_PIXEL_PERCENTAGE": "3.5"},
    )

    result = validate_raster_pair(t1_path, t2_path)

    assert result["is_valid"] is True
    assert result["data_quality_score"] >= 90
    assert result["recommendation"] == "READY_FOR_INFERENCE"
    assert result["spatial_overlap_percentage"] == 100.0
    assert result["temporal_delta_days"] == 2192

    # Check diagnostic matrix
    names = [c["name"] for c in result["checks_matrix"]]
    assert "Spatial Overlap" in names
    assert "CRS Alignment" in names
    assert "Spatial Resolution" in names
    assert "Band Compatibility" in names
    assert "Cloud Coverage" in names
    assert "Temporal Progression" in names


def test_validator_disjoint_images_fail(tmp_path):
    """Disjoint (non-overlapping) images must fail validation."""
    t1_path = str(tmp_path / "guwahati.tif")
    t2_path = str(tmp_path / "delhi.tif")

    _create_synthetic_geotiff(t1_path, left=770000.0, bottom=2890000.0)
    _create_synthetic_geotiff(t2_path, left=200000.0, bottom=1500000.0)  # Far away

    result = validate_raster_pair(t1_path, t2_path)

    assert result["is_valid"] is False
    assert result["recommendation"] == "INCOMPATIBLE_PAIR"
    overlap_check = next(c for c in result["checks_matrix"] if c["name"] == "Spatial Overlap")
    assert overlap_check["status"] == "FAIL"


# ─── 3. API Endpoint Tests (POST /api/v1/analyses/validate) ──────────────────


@pytest.mark.asyncio
async def test_api_validate_endpoint_success(tmp_path):
    """API endpoint returns 200 with structured validation payload."""
    t1_path = str(tmp_path / "t1_tile.tif")
    t2_path = str(tmp_path / "t2_tile.tif")

    _create_synthetic_geotiff(t1_path, tags={"DATETIME": "2022-05-01"})
    _create_synthetic_geotiff(t2_path, tags={"DATETIME": "2024-05-01"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analyses/validate",
            json={
                "image_before_path": t1_path,
                "image_after_path": t2_path,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "data_quality_score" in data
    assert "recommendation" in data
    assert "checks_matrix" in data
    assert len(data["checks_matrix"]) >= 6
    assert data["image1_metadata"]["is_georeferenced"] is True
    assert data["image2_metadata"]["is_georeferenced"] is True


@pytest.mark.asyncio
async def test_api_validate_missing_image_404():
    """API endpoint returns 404 when referenced images do not exist."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analyses/validate",
            json={
                "image_before_id": "non_existent_image_1",
                "image_after_id": "non_existent_image_2",
            },
        )

    assert response.status_code == 404
