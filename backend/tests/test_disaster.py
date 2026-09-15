"""
Unit & Integration Tests for Phase 14: Disaster Analysis Modules (Flood, Wildfire, Earthquake, Landslide, Cyclone).
"""

import os
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from httpx import AsyncClient, ASGITransport

from app.disaster.base import DisasterType, DISASTER_CAUTIONARY_DISCLAIMER
from app.disaster.flood import FloodInundationAnalyzer
from app.disaster.wildfire import WildfireBurnScarAnalyzer
from app.disaster.earthquake import EarthquakeDamageAnalyzer
from app.disaster.landslide import LandslideScarAnalyzer
from app.disaster.cyclone import CycloneImpactAnalyzer
from app.main import app
from app.core.config import settings


@pytest.fixture(autouse=True)
def setup_test_storage(tmp_path, monkeypatch):
    test_storage = str(tmp_path / "test_storage")
    os.makedirs(test_storage, exist_ok=True)
    monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", test_storage)
    return test_storage


# ─── 1. Flood Inundation Module Tests ─────────────────────────────────────────


def test_flood_analyzer_optical():
    """Verify optical flood inundation isolates new flood extent and includes non-causal wording."""
    h, w = 50, 50
    # Channel 0: Red, 1: Green, 2: Blue, 3: NIR
    t1 = np.full((4, h, w), 0.4, dtype=np.float32)
    # Baseline permanent river in columns 0:10
    t1[1, :, 0:10] = 0.5   # Green
    t1[3, :, 0:10] = 0.05  # Low NIR (Water)

    t2 = np.full((4, h, w), 0.4, dtype=np.float32)
    # Expanded flood water in columns 0:30
    t2[1, :, 0:30] = 0.5   # Green
    t2[3, :, 0:30] = 0.05  # Low NIR (Water)

    analyzer = FloodInundationAnalyzer()
    result = analyzer.analyze(t1, t2, resolution_m=10.0)

    assert result.disaster_type == DisasterType.FLOOD
    assert result.affected_area_m2 > 0.0
    assert result.percentage_area_affected > 10.0
    assert "Potential flood" in result.causality_wording
    assert DISASTER_CAUTIONARY_DISCLAIMER in result.advisory_disclaimer
    assert result.evidence_metrics["new_inundation_pixels"] > 0


def test_flood_analyzer_sar_sentinel1():
    """Verify Sentinel-1 SAR specular reflection drop mapping."""
    h, w = 40, 40
    sar_t1 = np.full((1, h, w), 0.6, dtype=np.float32) # Dry land
    sar_t2 = np.full((1, h, w), 0.6, dtype=np.float32)
    sar_t2[0, 10:30, 10:30] = 0.08  # SAR dark specular open water

    analyzer = FloodInundationAnalyzer()
    result = analyzer.analyze(sar_t1, sar_t2, is_sar=True)

    assert result.disaster_type == DisasterType.FLOOD
    assert result.modality_used == "SAR_SENTINEL1"
    assert result.affected_area_m2 > 0.0


# ─── 2. Wildfire, Earthquake, Landslide & Cyclone Tests ───────────────────────


def test_wildfire_burn_scar_analyzer():
    """Verify dNBR burn scar extraction with cautionary wording."""
    h, w = 40, 40
    t1 = np.full((4, h, w), 0.2, dtype=np.float32)
    t1[3] = 0.7  # NIR healthy vegetation

    t2 = np.full((4, h, w), 0.2, dtype=np.float32)
    t2[3, 10:30, 10:30] = 0.1  # Severe NIR drop / char

    analyzer = WildfireBurnScarAnalyzer()
    result = analyzer.analyze(t1, t2)

    assert result.disaster_type == DisasterType.WILDFIRE
    assert result.affected_area_m2 > 0.0
    assert "Potential wildfire" in result.causality_wording


def test_earthquake_damage_analyzer():
    """Verify structural damage assessment with cautionary wording."""
    h, w = 40, 40
    t1 = np.full((3, h, w), 0.2, dtype=np.float32)
    t2 = np.full((3, h, w), 0.2, dtype=np.float32)
    t2[:, 15:35, 15:35] = 0.8  # Major structural disruption

    analyzer = EarthquakeDamageAnalyzer()
    result = analyzer.analyze(t1, t2)

    assert result.disaster_type == DisasterType.EARTHQUAKE
    assert "Potential earthquake" in result.causality_wording


def test_landslide_scar_analyzer():
    """Verify landslide terrain scar assessment with cautionary wording."""
    h, w = 40, 40
    t1 = np.full((4, h, w), 0.2, dtype=np.float32)
    t1[3] = 0.6  # NIR canopy
    t2 = np.full((4, h, w), 0.2, dtype=np.float32)
    t2[3, 10:30, 10:25] = 0.1  # Canopy loss
    t2[0, 10:30, 10:25] = 0.6  # Bare earth soil exposure

    analyzer = LandslideScarAnalyzer()
    result = analyzer.analyze(t1, t2)

    assert result.disaster_type == DisasterType.LANDSLIDE
    assert "Potential landslide" in result.causality_wording


def test_cyclone_impact_analyzer():
    """Verify cyclone multi-hazard assessment with cautionary wording."""
    h, w = 40, 40
    t1 = np.full((4, h, w), 0.2, dtype=np.float32)
    t1[3] = 0.6
    t2 = np.full((4, h, w), 0.2, dtype=np.float32)
    t2[3, 10:35, :] = 0.15  # Widespread defoliation path

    analyzer = CycloneImpactAnalyzer()
    result = analyzer.analyze(t1, t2)

    assert result.disaster_type == DisasterType.CYCLONE
    assert "Potential cyclone" in result.causality_wording


# ─── 3. API End-to-End Tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_disaster_endpoints(tmp_path):
    """Test POST /api/v1/disaster/analyze and POST /api/v1/disaster/flood."""
    test_storage = str(tmp_path / "test_storage")
    os.makedirs(test_storage, exist_ok=True)

    t1_p = os.path.join(test_storage, "disaster_t1.tif")
    t2_p = os.path.join(test_storage, "disaster_t2.tif")

    transform = from_origin(770000.0, 2891000.0, 10.0, 10.0)
    data1 = np.full((3, 50, 50), 100, dtype=np.uint8)
    data2 = np.full((3, 50, 50), 100, dtype=np.uint8)
    data2[:, 10:35, 10:35] = 20  # Water drop

    with rasterio.open(t1_p, "w", driver="GTiff", height=50, width=50, count=3, dtype=np.uint8, crs="EPSG:32646", transform=transform) as d1:
        d1.write(data1)
    with rasterio.open(t2_p, "w", driver="GTiff", height=50, width=50, count=3, dtype=np.uint8, crs="EPSG:32646", transform=transform) as d2:
        d2.write(data2)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test generic disaster analyze endpoint
        res = await client.post(
            "/api/v1/disaster/analyze",
            json={
                "image_before_id": "disaster_t1.tif",
                "image_after_id": "disaster_t2.tif",
                "disaster_type": "FLOOD",
            },
        )
        assert res.status_code == 200
        payload = res.json()
        assert payload["disaster_type"] == "FLOOD"
        assert "affected_area_m2" in payload
        assert "advisory_disclaimer" in payload
        assert "Potential flood" in payload["causality_wording"]

        # Test dedicated flood endpoint
        flood_res = await client.post(
            "/api/v1/disaster/flood",
            json={
                "image_before_id": "disaster_t1.tif",
                "image_after_id": "disaster_t2.tif",
            },
        )
        assert flood_res.status_code == 200
        flood_payload = flood_res.json()
        assert flood_payload["disaster_type"] == "FLOOD"
