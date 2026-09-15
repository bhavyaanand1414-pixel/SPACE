"""
Unit & Integration Tests for Phase 13: Spectral Index Analysis (NDVI, NDWI, NDBI).

STRICT PRINCIPLES:
1. Check band availability before calculation.
2. Never calculate an index using incorrect bands.
3. If required bands are missing (e.g. 3-band RGB), safely bypass without fabrication.
"""

import os
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from httpx import AsyncClient, ASGITransport

from app.gis.spectral import SpectralIndexAnalyzer, SpectralAnalysisReport
from app.main import app
from app.core.config import settings


@pytest.fixture(autouse=True)
def setup_test_storage(tmp_path, monkeypatch):
    test_storage = str(tmp_path / "test_storage")
    os.makedirs(test_storage, exist_ok=True)
    monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", test_storage)
    return test_storage


# ─── 1. 4-Band Multi-Spectral Tests (RGB + NIR) ───────────────────────────────


def test_spectral_index_4band_multispectral():
    """Verify NDVI and NDWI computation on 4-band satellite raster (RGB + NIR)."""
    h, w = 40, 40
    # Channel 0: Red, Channel 1: Green, Channel 2: Blue, Channel 3: NIR
    t1 = np.full((4, h, w), 0.2, dtype=np.float32)
    t1[3, :, :] = 0.6  # High NIR baseline (dense vegetation)

    t2 = np.full((4, h, w), 0.2, dtype=np.float32)
    t2[3, :, :] = 0.15 # Drop in NIR in T2 (vegetation clearing)

    report = SpectralIndexAnalyzer.analyze(t1, t2)

    assert report.is_multispectral is True
    assert report.band_count_t1 == 4
    assert "NIR" in report.detected_bands
    assert "RED" in report.detected_bands

    # 1. NDVI Test
    assert report.ndvi.is_available is True
    assert report.ndvi.t1_mean > 0.4
    assert report.ndvi.t2_mean < 0.0
    assert report.ndvi.delta_mean < -0.3
    assert "Significant vegetation loss" in report.ndvi.interpretation

    # 2. NDWI Test
    assert report.ndwi.is_available is True

    # 3. NDBI Test (SWIR missing in 4-band -> safely bypassed)
    assert report.ndbi.is_available is False
    assert "SWIR" in report.ndbi.missing_bands[0]


# ─── 2. 3-Band RGB Input Safe Bypass Test (No Fabrication) ────────────────────


def test_spectral_index_3band_rgb_safe_bypass():
    """Verify that on 3-band RGB imagery (no NIR/SWIR), indices are safely bypassed without fabrication."""
    h, w = 32, 32
    t1 = np.full((3, h, w), 0.5, dtype=np.float32)
    t2 = np.full((3, h, w), 0.8, dtype=np.float32)

    report = SpectralIndexAnalyzer.analyze(t1, t2)

    assert report.is_multispectral is False
    assert report.band_count_t1 == 3

    # All indices requiring NIR/SWIR must be marked unavailable
    assert report.ndvi.is_available is False
    assert "NIR (Near-Infrared)" in report.ndvi.missing_bands
    assert report.ndvi.t1_mean is None

    assert report.ndwi.is_available is False
    assert report.ndwi.t1_mean is None

    assert report.ndbi.is_available is False
    assert report.ndbi.t1_mean is None

    assert len(report.supporting_evidence_summary) >= 1
    assert "safely bypassed" in report.supporting_evidence_summary[0]


# ─── 3. 12-Band Sentinel-2 Ingest (RGB + NIR + SWIR1 + SWIR2) ─────────────────


def test_spectral_index_12band_sentinel2():
    """Verify full Sentinel-2 multi-spectral support with NDVI, NDWI, and NDBI all active."""
    h, w = 30, 30
    t1 = np.full((12, h, w), 0.2, dtype=np.float32)
    t2 = np.full((12, h, w), 0.2, dtype=np.float32)

    # Sentinel-2 indices: Green=2, Red=3, NIR=7, SWIR1=10
    t1[7, :, :] = 0.5   # T1 NIR
    t2[7, :, :] = 0.2   # T2 NIR drop
    t2[10, :, :] = 0.7  # T2 SWIR1 surge (Built-up expansion)

    report = SpectralIndexAnalyzer.analyze(t1, t2, metadata_t1={"satellite": "Sentinel-2"})

    assert report.is_multispectral is True
    assert report.ndvi.is_available is True
    assert report.ndwi.is_available is True
    assert report.ndbi.is_available is True
    assert report.ndbi.delta_mean > 0.2
    assert "built-up" in report.ndbi.interpretation.lower()


# ─── 4. End-to-End API Analysis with Spectral Results ─────────────────────────


@pytest.mark.asyncio
async def test_api_analysis_includes_spectral_report(tmp_path):
    """Verify POST /api/v1/analyses/{id}/run returns spectral index report in response."""
    test_storage = str(tmp_path / "test_storage")
    os.makedirs(test_storage, exist_ok=True)

    t1_p = os.path.join(test_storage, "spec_t1.tif")
    t2_p = os.path.join(test_storage, "spec_t2.tif")

    transform = from_origin(770000.0, 2891000.0, 10.0, 10.0)
    data1 = np.full((3, 50, 50), 60, dtype=np.uint8)
    data2 = np.full((3, 50, 50), 180, dtype=np.uint8)

    with rasterio.open(t1_p, "w", driver="GTiff", height=50, width=50, count=3, dtype=np.uint8, crs="EPSG:32646", transform=transform) as d1:
        d1.write(data1)
    with rasterio.open(t2_p, "w", driver="GTiff", height=50, width=50, count=3, dtype=np.uint8, crs="EPSG:32646", transform=transform) as d2:
        d2.write(data2)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/analyses/AN-SPECTRAL-01/run",
            json={
                "image_before_id": "spec_t1.tif",
                "image_after_id": "spec_t2.tif",
            },
        )
        assert res.status_code == 200
        payload = res.json()
        assert "spectral_analysis" in payload
        assert "ndvi" in payload["spectral_analysis"]
        assert "ndwi" in payload["spectral_analysis"]
        assert "ndbi" in payload["spectral_analysis"]
        assert payload["spectral_analysis"]["band_count_t1"] == 3
