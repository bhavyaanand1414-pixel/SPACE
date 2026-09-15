"""
Unit & Integration Tests for Phase 8: Baseline Change Detection & GeoJSON API.
"""

import os
import pytest
import numpy as np
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.ml.baseline import BaselineChangeDetector
from rasterio.transform import from_origin


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
    change_rect: tuple = None,
):
    """Create a GeoTIFF with optional altered rectangular region."""
    import rasterio

    transform = from_origin(770000.0, 2891000.0, 10.0, 10.0)
    data = np.full((3, height, width), 50, dtype=np.uint8)

    if change_rect:
        x1, y1, x2, y2 = change_rect
        data[:, y1:y2, x1:x2] = 230  # High brightness change

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=3,
        dtype=np.uint8,
        crs="EPSG:32646",
        transform=transform,
    ) as dst:
        dst.write(data)


# ─── 1. Baseline Change Detector Direct Tests ─────────────────────────────────


def test_baseline_change_detector_direct():
    """Verify BaselineChangeDetector accurately localizes an artificial change square."""
    h, w = 100, 100
    img1 = np.full((3, h, w), 0.2, dtype=np.float32)
    img2 = np.full((3, h, w), 0.2, dtype=np.float32)

    # Insert a 20x20 change block in img2 (simulating new building)
    img2[:, 30:50, 30:50] = 0.85

    transform = from_origin(770000.0, 2891000.0, 10.0, 10.0)
    detector = BaselineChangeDetector(min_region_pixels=10)

    result = detector.detect_change(
        image1=img1,
        image2=img2,
        spatial_transform=transform,
        crs="EPSG:32646",
        resolution_m=10.0,
        confidence_threshold=0.4,
    )

    assert result.label == "Baseline / Demo Result"
    assert "Never present baseline output as trained AI performance" in result.disclaimer
    assert result.total_pixels_changed >= 300
    assert result.region_count >= 1
    assert result.percentage_changed > 3.0

    # Verify first region properties
    first_reg = result.regions[0]
    assert first_reg.area_m2 > 30000.0
    assert first_reg.geojson_geometry["type"] == "Polygon"
    assert len(first_reg.geojson_geometry["coordinates"][0]) >= 4


def test_baseline_speckle_noise_removal():
    """Verify that isolated 1-pixel noise is filtered out by morphological operations."""
    h, w = 80, 80
    img1 = np.full((3, h, w), 0.3, dtype=np.float32)
    img2 = np.full((3, h, w), 0.3, dtype=np.float32)

    # Add isolated 1-pixel spikes
    img2[:, 10, 10] = 0.95
    img2[:, 25, 25] = 0.95

    detector = BaselineChangeDetector(min_region_pixels=6)
    result = detector.detect_change(img1, img2, confidence_threshold=0.5)

    # Speckles should be suppressed
    assert result.region_count == 0
    assert result.total_pixels_changed == 0


# ─── 2. End-to-End API Analysis Execution Tests ───────────────────────────────


@pytest.mark.asyncio
async def test_api_baseline_analysis_lifecycle(tmp_path):
    """Test full API lifecycle: run analysis -> get details -> get GeoJSON changes."""
    test_storage = str(tmp_path / "test_storage")
    os.makedirs(test_storage, exist_ok=True)

    t1_path = os.path.join(test_storage, "sat_t1.tif")
    t2_path = os.path.join(test_storage, "sat_t2.tif")

    _create_synthetic_geotiff(t1_path, change_rect=None)
    _create_synthetic_geotiff(t2_path, change_rect=(20, 20, 45, 45))

    analysis_id = "AN-TEST-001"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Trigger analysis run
        run_res = await client.post(
            f"/api/v1/analyses/{analysis_id}/run",
            json={
                "image_before_id": "sat_t1.tif",
                "image_after_id": "sat_t2.tif",
                "confidence_threshold": 0.4,
            },
        )
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert run_data["status"] == "completed"
        assert run_data["label"] == "Baseline / Demo Result"
        assert run_data["statistics"]["region_count"] >= 1
        assert run_data["statistics"]["total_area_changed_m2"] > 0

        # 2. Query analysis details
        detail_res = await client.get(f"/api/v1/analyses/{analysis_id}")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["status"] == "completed"
        assert detail_data["model_name"] == "Spectral Baseline Difference"

        # 3. Retrieve GeoJSON FeatureCollection
        geojson_res = await client.get(f"/api/v1/analyses/{analysis_id}/changes")
        assert geojson_res.status_code == 200
        geo_data = geojson_res.json()
        assert geo_data["type"] == "FeatureCollection"
        assert len(geo_data["features"]) >= 1
        feat = geo_data["features"][0]
        assert feat["type"] == "Feature"
        assert feat["geometry"]["type"] == "Polygon"
        assert "area_m2" in feat["properties"]
        assert feat["properties"]["label"] == "Baseline / Demo Result"
