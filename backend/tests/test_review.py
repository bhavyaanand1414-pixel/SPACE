"""
Unit & Integration Tests for Phase 17: Human-In-The-Loop (HITL) Review Workflow & Active Learning Readiness.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.schemas.review import HumanCorrectionInput, ReviewStatusEnum
from app.services.review import ReviewService, REVIEW_RECORDS_STORE
from app.main import app


@pytest.fixture(autouse=True)
def clean_review_store():
    REVIEW_RECORDS_STORE.clear()
    yield
    REVIEW_RECORDS_STORE.clear()


# ─── 1. Review Queue Flagging Tests ───────────────────────────────────────────


def test_review_queue_initialization_low_confidence():
    """Verify low-confidence (<0.80) or ambiguous regions are flagged for review."""
    regions = [
        {"properties": {"region_index": 1, "category": "HUMAN", "subtype": "Building", "mean_confidence": 0.95}},
        {"properties": {"region_index": 2, "category": "UNKNOWN", "subtype": "Unknown", "mean_confidence": 0.62}},
        {"properties": {"region_index": 3, "category": "NATURAL", "subtype": "Vegetation", "mean_confidence": 0.72}},
    ]

    flagged = ReviewService.initialize_review_queue_from_analysis(
        analysis_id="AN-TEST-REVIEW",
        regions=regions,
        model_version="1.0.0",
    )

    assert len(flagged) == 2
    assert flagged[0].region_index == 2
    assert flagged[0].status == ReviewStatusEnum.PENDING
    assert flagged[0].original_category == "UNKNOWN"
    assert flagged[1].region_index == 3
    assert flagged[1].original_confidence == 0.72


# ─── 2. Human Correction Audit Trail Tests ────────────────────────────────────


def test_submit_human_correction_audit_trail():
    """Verify human correction preserves full audit logging."""
    # Seed queue item
    ReviewService.initialize_review_queue_from_analysis(
        analysis_id="AN-AUDIT-01",
        regions=[{"properties": {"region_index": 1, "category": "UNKNOWN", "mean_confidence": 0.65}}],
    )

    corrections = [
        HumanCorrectionInput(
            region_index=1,
            status=ReviewStatusEnum.CORRECTED,
            corrected_category="HUMAN",
            corrected_subcategory="Road",
            reviewer_name="Senior Analyst Rao",
            notes="Confirmed linear asphalt corridor on high-res optical validation.",
        )
    ]

    updated = ReviewService.submit_reviews(
        analysis_id="AN-AUDIT-01",
        corrections=corrections,
        reviewer_name="Senior Analyst Rao",
    )

    assert len(updated) == 1
    rec = updated[0]
    assert rec.status == ReviewStatusEnum.CORRECTED
    assert rec.original_category == "UNKNOWN"
    assert rec.corrected_category == "HUMAN"
    assert rec.corrected_subcategory == "Road"
    assert rec.reviewer_name == "Senior Analyst Rao"
    assert rec.notes == "Confirmed linear asphalt corridor on high-res optical validation."
    assert rec.is_active_learning_candidate is True
    assert "timestamp" in rec.created_at or "Z" in rec.created_at or "+" in rec.created_at


# ─── 3. Active Learning Dataset Export Safety Test ────────────────────────────


def test_export_active_learning_dataset_safety(tmp_path):
    """Verify active learning candidates export without automatic retraining."""
    # Add an approved correction
    ReviewService.submit_reviews(
        analysis_id="AN-AL-01",
        corrections=[
            HumanCorrectionInput(
                region_index=1,
                status=ReviewStatusEnum.APPROVED,
                corrected_category="HUMAN",
                corrected_subcategory="Building",
            )
        ],
    )

    export_res = ReviewService.export_active_learning_dataset(export_dir=str(tmp_path / "al_export"))

    assert export_res["status"] == "exported"
    assert export_res["candidate_count"] == 1
    assert "NOT automatically retrained" in export_res["message"]


# ─── 4. End-to-End API Review Endpoints Test ──────────────────────────────────


@pytest.mark.asyncio
async def test_api_review_endpoints():
    """Verify POST review submission, GET queue, and POST export candidate APIs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Submit review
        post_res = await client.post(
            "/api/v1/analyses/AN-API-REV-01/review",
            json={
                "reviewer_name": "ISRO Analyst",
                "reviews": [
                    {
                        "region_index": 1,
                        "status": "CORRECTED",
                        "corrected_category": "HUMAN",
                        "corrected_subcategory": "Building",
                        "notes": "Verified new construction complex.",
                    }
                ],
            },
        )
        assert post_res.status_code == 200
        records = post_res.json()
        assert len(records) == 1
        assert records[0]["corrected_category"] == "HUMAN"

        # 2. Get global queue
        queue_res = await client.get("/api/v1/review/queue")
        assert queue_res.status_code == 200
        queue_data = queue_res.json()
        assert queue_data["total_in_queue"] >= 1
        assert queue_data["corrected_count"] >= 1

        # 3. Export active learning candidates
        export_res = await client.post("/api/v1/review/export-candidates")
        assert export_res.status_code == 200
        export_data = export_res.json()
        assert export_data["candidate_count"] >= 1
        assert "NOT automatically retrained" in export_data["message"]
