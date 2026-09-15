"""
Comprehensive End-to-End (E2E) Integration Test (Phase 21).

Complete Mission Lifecycle:
1. Upload Image T1 & Image T2 (GeoTIFF rasters)
2. Extract Metadata & Validate Pair Compatibility (Overlap, CRS, Resolution)
3. Preprocess & Co-Register (2D FFT Sub-Pixel Alignment)
4. Execute Change Detection (Siamese U-Net / Baseline Detector)
5. Classify Detected Changes (Level 1 & Level 2 Hierarchical Taxonomy)
6. Calculate Rigorous Projected Area & Categorical Statistics
7. Retrieve Complete Analysis Detail & Grounded Explainability Diagnostic
8. Generate Publication-Grade PDF Intelligence Report
9. Submit Human-In-The-Loop (HITL) Verification & Overrides
10. Query Grounded AI Agent with Live Session Context

STRICT SCIENTIFIC PRINCIPLES:
- Zero fabrication of metadata, coordinates, dates, or areas.
- Complete execution of actual backend tools and algorithms.
"""

import io
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from httpx import AsyncClient, ASGITransport

from app.main import app


def _create_in_memory_geotiff(
    width: int = 50,
    height: int = 50,
    bands: int = 3,
    crs: str = "EPSG:32646",
    value: float = 0.5,
) -> bytes:
    """Helper to generate a valid in-memory GeoTIFF raster."""
    mem_file = io.BytesIO()
    transform = from_origin(500000.0, 2900000.0, 10.0, 10.0)
    data = np.full((bands, height, width), value, dtype=np.float32)

    with rasterio.open(
        mem_file,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=bands,
        dtype=rasterio.float32,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(data)

    return mem_file.getvalue()


@pytest.mark.asyncio
async def test_complete_satellite_analysis_e2e_pipeline():
    """
    Execute full end-to-end mission lifecycle through FastAPI HTTP interface.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ---------------------------------------------------------------------
        # Step 1: Health & System Diagnostics
        # ---------------------------------------------------------------------
        health_res = await client.get("/api/v1/health")
        assert health_res.status_code == 200
        assert health_res.json()["status"] == "ok"

        # ---------------------------------------------------------------------
        # Step 2: Upload Image T1 (Pre-Event) & Image T2 (Post-Event)
        # ---------------------------------------------------------------------
        t1_bytes = _create_in_memory_geotiff(width=40, height=40, bands=3, value=0.2)
        t2_bytes = _create_in_memory_geotiff(width=40, height=40, bands=3, value=0.8)

        upload_t1 = await client.post(
            "/api/v1/images/upload",
            files={"file": ("guwahati_2020_t1.tif", t1_bytes, "image/tiff")},
        )
        assert upload_t1.status_code in [200, 201]
        img1_data = upload_t1.json()
        img1_id = img1_data["image_id"]
        assert img1_data["metadata"]["crs"] is not None
        assert img1_data["metadata"]["epsg_code"] == 32646

        upload_t2 = await client.post(
            "/api/v1/images/upload",
            files={"file": ("guwahati_2026_t2.tif", t2_bytes, "image/tiff")},
        )
        assert upload_t2.status_code in [200, 201]
        img2_data = upload_t2.json()
        img2_id = img2_data["image_id"]

        # ---------------------------------------------------------------------
        # Step 3: Validate Raster Pair Compatibility
        # ---------------------------------------------------------------------
        val_res = await client.post(
            "/api/v1/analyses/validate",
            json={"image_before_id": img1_data["filename"], "image_after_id": img2_data["filename"]},
        )
        assert val_res.status_code == 200
        val_data = val_res.json()
        assert val_data["is_valid"] is True
        assert val_data["data_quality_score"] >= 80

        # ---------------------------------------------------------------------
        # Step 4: Run Baseline / Siamese Change Detection Analysis
        # ---------------------------------------------------------------------
        run_res = await client.post(
            "/api/v1/analyses/AN-E2E-MISSION-01/run",
            json={
                "image_before_id": img1_data["filename"],   # M-2 FIX: match schema field names
                "image_after_id": img2_data["filename"],
                "confidence_threshold": 0.50,
                "enable_coregistration": True,
            },
        )
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert run_data["status"].lower() == "completed"
        assert run_data["statistics"]["total_area_changed_km2"] >= 0.0
        assert "Baseline / Demo Result" in run_data["label"]

        # ---------------------------------------------------------------------
        # Step 5: Retrieve Detailed Analysis & PostGIS Change Features
        # ---------------------------------------------------------------------
        detail_res = await client.get("/api/v1/analyses/AN-E2E-MISSION-01")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["status"].lower() == "completed"
        assert detail_data["statistics"]["total_area_changed_km2"] >= 0.0

        changes_res = await client.get("/api/v1/analyses/AN-E2E-MISSION-01/changes")
        assert changes_res.status_code == 200
        changes_data = changes_res.json()
        assert changes_data["type"] == "FeatureCollection"

        # ---------------------------------------------------------------------
        # Step 6: Explainability Diagnostic for Region #1
        # ---------------------------------------------------------------------
        explain_res = await client.get("/api/v1/analyses/AN-E2E-MISSION-01/explain/1")
        assert explain_res.status_code == 200
        explain_data = explain_res.json()
        assert explain_data["reliability"]["overall_reliability"] in ["HIGH", "MEDIUM", "LOW"]
        assert "data:image/png;base64," in explain_data["mask_crop_data_url"]

        # ---------------------------------------------------------------------
        # Step 7: Generate Publication-Grade PDF Report
        # ---------------------------------------------------------------------
        report_res = await client.post(
            "/api/v1/analyses/AN-E2E-MISSION-01/report",
            json={
                "title": "ISRO E2E Mission Intelligence Dossier",
                "study_area": "Guwahati Urban Corridor",
            },
        )
        assert report_res.status_code == 200
        rep_meta = report_res.json()
        assert rep_meta["report_id"] == "REP-AN-E2E-MISSION-01"
        assert rep_meta["file_size_bytes"] > 1000

        # Download PDF
        pdf_download = await client.get(f"/api/v1/reports/{rep_meta['report_id']}")
        assert pdf_download.status_code == 200
        assert pdf_download.headers["content-type"] == "application/pdf"
        assert pdf_download.content.startswith(b"%PDF-")

        # ---------------------------------------------------------------------
        # Step 8: Human-In-The-Loop (HITL) Verification Submission
        # ---------------------------------------------------------------------
        review_res = await client.post(
            "/api/v1/analyses/AN-E2E-MISSION-01/review",
            json={
                "reviewer_name": "ISRO Senior Specialist",
                "reviews": [
                    {
                        "region_index": 1,
                        "status": "APPROVED",
                        "corrected_category": "HUMAN",
                        "corrected_subcategory": "Building",
                        "notes": "Verified new residential expansion on high-res baseline.",
                    }
                ],
            },
        )
        assert review_res.status_code == 200
        review_records = review_res.json()
        assert len(review_records) == 1
        assert review_records[0]["status"] == "APPROVED"

        # ---------------------------------------------------------------------
        # Step 9: Grounded AI Agent Natural-Language Query
        # ---------------------------------------------------------------------
        agent_res = await client.post(
            "/api/v1/agent/query",
            json={
                "query": "What changed between 2020 and 2026 and how much area is human infrastructure?",
                "context": {"analysis_id": "AN-E2E-MISSION-01"},
            },
        )
        assert agent_res.status_code == 200
        agent_data = agent_res.json()
        assert agent_data["is_grounded"] is True
        assert len(agent_data["tool_trace"]) >= 1
        assert "response_text" in agent_data
