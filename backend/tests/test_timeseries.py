"""
Unit & Integration Tests for Phase 15: Multi-Temporal Time-Series Analysis.

STRICT PRINCIPLES:
1. Supports sequence of >= 2 satellite acquisitions.
2. Enforces availability disclaimer: "Analysis interval depends on available satellite observations."
3. Computes area-over-time, human growth, and natural shifts without fabricating observation availability.
"""

import pytest
import numpy as np
from httpx import AsyncClient, ASGITransport

from app.timeseries.engine import (
    TimeSeriesEngine,
    TimeSeriesObservation,
    TIMELINE_AVAILABILITY_DISCLAIMER,
)
from app.main import app


# ─── 1. Multi-Date Sequence Engine Tests (5-Date Progression) ─────────────────


def test_timeseries_engine_multi_date_sequence():
    """Verify 5-observation timeline (2020 -> 2021 -> 2022 -> 2024 -> 2026)."""
    h, w = 32, 32
    obs = [
        TimeSeriesObservation(
            observation_id="OBS-2020",
            timestamp_iso="2020-01-15T10:00:00Z",
            label="2020 Baseline",
            image_array=np.full((3, h, w), 0.2, dtype=np.float32),
            resolution_m=10.0,
        ),
        TimeSeriesObservation(
            observation_id="OBS-2021",
            timestamp_iso="2021-01-15T10:00:00Z",
            label="2021 T2",
            image_array=np.full((3, h, w), 0.35, dtype=np.float32),
            resolution_m=10.0,
        ),
        TimeSeriesObservation(
            observation_id="OBS-2022",
            timestamp_iso="2022-01-15T10:00:00Z",
            label="2022 T3",
            image_array=np.full((3, h, w), 0.48, dtype=np.float32),
            resolution_m=10.0,
        ),
        TimeSeriesObservation(
            observation_id="OBS-2024",
            timestamp_iso="2024-01-15T10:00:00Z",
            label="2024 T4",
            image_array=np.full((3, h, w), 0.65, dtype=np.float32),
            resolution_m=10.0,
        ),
        TimeSeriesObservation(
            observation_id="OBS-2026",
            timestamp_iso="2026-01-15T10:00:00Z",
            label="2026 T5",
            image_array=np.full((3, h, w), 0.85, dtype=np.float32),
            resolution_m=10.0,
        ),
    ]

    engine = TimeSeriesEngine()
    report = engine.analyze_sequence(obs, timeseries_id="TS-GUWAHATI-5YR", title="Guwahati 5-Year Dynamics")

    assert report.observation_count == 5
    assert len(report.sequential_steps) == 4
    assert len(report.area_over_time_series) == 5
    assert len(report.category_over_time_series) == 5
    assert report.total_duration_days > 2100.0
    assert report.availability_notice == TIMELINE_AVAILABILITY_DISCLAIMER
    assert "depends on available satellite observations" in report.availability_notice


# ─── 2. Interval Formatter Diagnostic Tests ───────────────────────────────────


def test_timeseries_interval_formatting():
    """Verify human-readable interval formatting across hours, days, weeks, months, years."""
    engine = TimeSeriesEngine()

    assert "hours" in engine._format_interval_human_readable(0.25)
    assert "days" in engine._format_interval_human_readable(5.0)
    assert "weeks" in engine._format_interval_human_readable(21.0)
    assert "months" in engine._format_interval_human_readable(90.0)
    assert "years" in engine._format_interval_human_readable(730.0)


def test_timeseries_requires_at_least_two_observations():
    """Verify ValueError is raised if < 2 observations are provided."""
    engine = TimeSeriesEngine()
    obs = [
        TimeSeriesObservation(
            observation_id="OBS-SINGLE",
            timestamp_iso="2020-01-15T10:00:00Z",
            label="Single",
            image_array=np.zeros((3, 10, 10), dtype=np.float32),
        )
    ]
    with pytest.raises(ValueError, match="at least 2 distinct"):
        engine.analyze_sequence(obs)


# ─── 3. End-to-End API Tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_timeseries_analyze_and_retrieve():
    """Verify POST /api/v1/timeseries/analyze and GET /api/v1/timeseries/{id}."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        req_payload = {
            "timeseries_id": "TS-TEST-001",
            "title": "Multi-Temporal Benchmark Sequence",
            "observations": [
                {
                    "observation_id": "OBS-2020",
                    "timestamp_iso": "2020-01-15T00:00:00Z",
                    "label": "2020 Baseline",
                    "satellite": "Sentinel-2 MSI",
                },
                {
                    "observation_id": "OBS-2022",
                    "timestamp_iso": "2022-01-15T00:00:00Z",
                    "label": "2022 Phase 1",
                    "satellite": "Sentinel-2 MSI",
                },
                {
                    "observation_id": "OBS-2026",
                    "timestamp_iso": "2026-01-15T00:00:00Z",
                    "label": "2026 Current",
                    "satellite": "Sentinel-2 MSI",
                },
            ],
        }

        res = await client.post("/api/v1/timeseries/analyze", json=req_payload)
        assert res.status_code == 200
        data = res.json()

        assert data["timeseries_id"] == "TS-TEST-001"
        assert data["observation_count"] == 3
        assert len(data["sequential_steps"]) == 2
        assert len(data["area_over_time_series"]) == 3
        assert "availability_notice" in data
        assert "Analysis interval depends on available satellite observations" in data["availability_notice"]

        # Retrieve cached
        get_res = await client.get("/api/v1/timeseries/TS-TEST-001")
        assert get_res.status_code == 200
        assert get_res.json()["timeseries_id"] == "TS-TEST-001"
