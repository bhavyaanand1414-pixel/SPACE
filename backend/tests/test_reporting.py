"""
Unit & Integration Tests for Phase 20: Geospatial Statistics Engine & Automated PDF Report Generator.

STRICT PRINCIPLES:
1. Calculates rigorous projected and geodesic metrics.
2. Generates publication-grade PDF documents using ReportLab.
3. Enforces zero fabrication and mandatory preliminary advisory disclaimers.
"""

import pytest
import numpy as np
from httpx import AsyncClient, ASGITransport

from app.gis.statistics import GeospatialStatisticsEngine
from app.reporting.pdf_generator import GeospatialPDFReportGenerator
from app.main import app


# ─── 1. Geospatial Statistics Engine Tests ────────────────────────────────────


def test_statistics_engine_exact_area_calculations():
    """Verify projected area calculations (m² and km²), proportions, and category totals."""
    # 100 x 100 raster with 10m GSD -> 1,000,000 m² total (1.00 km²)
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[0:20, 0:50] = 1  # 1000 pixels = 100,000 m² = 0.10 km² changed

    regions = [
        {"properties": {"region_index": 1, "category": "HUMAN", "subtype": "Building", "area_m2": 70000.0, "severity": "HIGH"}},
        {"properties": {"region_index": 2, "category": "NATURAL", "subtype": "Vegetation", "area_m2": 30000.0, "severity": "LOW"}},
    ]

    stats = GeospatialStatisticsEngine.calculate_from_mask_and_regions(
        change_mask=mask,
        regions=regions,
        resolution_m=10.0,
        crs_str="EPSG:32646",
    )

    assert stats.total_area_m2 == 1_000_000.0
    assert stats.total_area_km2 == 1.00
    assert stats.changed_area_m2 == 100_000.0
    assert stats.changed_area_km2 == 0.10
    assert stats.unchanged_area_m2 == 900_000.0
    assert stats.unchanged_area_km2 == 0.90
    assert stats.percentage_changed == 10.0
    assert stats.human_area_km2 == 0.07
    assert stats.natural_area_km2 == 0.03
    assert stats.number_of_regions == 2
    assert stats.category_counts["HUMAN"] == 1
    assert stats.category_counts["NATURAL"] == 1
    assert stats.area_by_severity["HIGH"] == 0.07


# ─── 2. PDF Report Generation Tests ───────────────────────────────────────────


def test_pdf_report_generator_produces_valid_pdf_bytes(tmp_path):
    """Verify ReportLab produces valid binary PDF stream starting with %PDF- header."""
    mask = np.zeros((50, 50), dtype=np.uint8)
    mask[10:20, 10:20] = 1
    stats = GeospatialStatisticsEngine.calculate_from_mask_and_regions(mask, [], resolution_m=10.0)

    pdf_out = tmp_path / "test_report.pdf"
    pdf_bytes = GeospatialPDFReportGenerator.generate_pdf_report(
        analysis_id="AN-TEST-001",
        stats=stats,
        study_area="Guwahati Test Region",
        satellite="Sentinel-2 MSI",
        resolution_m=10.0,
        crs_str="EPSG:32646",
        date_t1="2020-01-15",
        date_t2="2026-01-15",
        data_quality_score=92,
        model_name="Siamese U-Net",
        model_version="1.0.0",
        output_filepath=str(pdf_out),
    )

    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")
    assert pdf_out.is_file()
    assert pdf_out.stat().st_size > 1000


# ─── 3. End-to-End Reporting API Tests ────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_generate_and_download_report_endpoints():
    """Verify POST /api/v1/analyses/{id}/report and GET /api/v1/reports/{id} download."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Trigger PDF Generation
        post_res = await client.post(
            "/api/v1/analyses/AN-API-REPORT-01/report",
            json={
                "title": "ISRO Multi-Temporal Satellite Change Intelligence Report",
                "study_area": "Guwahati Urban Corridor",
            },
        )
        assert post_res.status_code == 200
        meta = post_res.json()
        assert meta["report_id"] == "REP-AN-API-REPORT-01"
        assert meta["file_size_bytes"] > 1000
        assert meta["dominant_category"] == "HUMAN"

        # 2. Download generated PDF stream
        get_res = await client.get("/api/v1/reports/REP-AN-API-REPORT-01")
        assert get_res.status_code == 200
        assert get_res.headers["content-type"] == "application/pdf"
        assert len(get_res.content) > 1000
        assert get_res.content.startswith(b"%PDF-")

        # 3. Get Metadata summary
        meta_res = await client.get("/api/v1/reports/REP-AN-API-REPORT-01/metadata")
        assert meta_res.status_code == 200
        assert meta_res.json()["report_id"] == "REP-AN-API-REPORT-01"
