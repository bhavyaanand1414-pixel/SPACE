"""
Unit & Integration Tests for Phase 16: Uncertainty Quantification & Explainable AI (XAI).
"""

import pytest
import numpy as np
from httpx import AsyncClient, ASGITransport

from app.ml.explainability import ExplainabilityEngine, ReliabilityAssessment
from app.main import app


# ─── 1. Reliability Indicator Composite Tests ─────────────────────────────────


def test_reliability_score_calculation():
    """Verify system reliability weighted composite indicator."""
    engine = ExplainabilityEngine()

    # High reliability: 95% conf, 90% img quality, 96% reg
    high_rel = engine.calculate_reliability(0.95, 90.0, 0.96)
    assert high_rel.overall_reliability == "HIGH"
    assert high_rel.overall_score >= 85.0
    assert high_rel.model_confidence_pct == 95.0

    # Medium reliability
    med_rel = engine.calculate_reliability(0.70, 70.0, 0.75)
    assert med_rel.overall_reliability == "MEDIUM"

    # Low reliability
    low_rel = engine.calculate_reliability(0.40, 50.0, 0.50)
    assert low_rel.overall_reliability == "LOW"


# ─── 2. Grounded Explanation & Crop Generation Tests ──────────────────────────


def test_generate_grounded_explanation_human_road():
    """Verify grounded explanation generation for linear human road corridor."""
    h, w = 32, 32
    t1 = np.full((3, h, w), 0.2, dtype=np.float32)
    t2 = np.full((3, h, w), 0.7, dtype=np.float32)
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[12:20, :] = 255

    evidence = {
        "delta_brightness": 0.50,
        "elongation": 4.5,
        "rectangularity": 0.65,
        "rule_fired": "HIGH_ELONGATION_LINEAR_CORRIDOR",
    }

    engine = ExplainabilityEngine()
    exp = engine.generate_explanation(
        region_index=1,
        category="HUMAN",
        subcategory="Road",
        confidence=0.94,
        evidence=evidence,
        t1_patch=t1,
        t2_patch=t2,
        mask_patch=mask,
    )

    assert exp.region_index == 1
    assert exp.category == "HUMAN"
    assert exp.confidence_pct == 94.0
    assert "Linear transport corridor" in exp.explanation_narrative
    assert exp.t1_crop_data_url.startswith("data:image/png;base64,")
    assert exp.t2_crop_data_url.startswith("data:image/png;base64,")
    assert exp.mask_crop_data_url.startswith("data:image/png;base64,")
    assert exp.saliency_heatmap_data_url.startswith("data:image/png;base64,")
    assert exp.reliability.overall_reliability in ["HIGH", "MEDIUM"]


def test_generate_grounded_explanation_disaster_flood():
    """Verify grounded flood explanation with water index narrative."""
    h, w = 32, 32
    t1 = np.full((3, h, w), 0.4, dtype=np.float32)
    t2 = np.full((3, h, w), 0.1, dtype=np.float32)
    mask = np.full((h, w), 255, dtype=np.uint8)

    evidence = {
        "delta_ndwi": 0.35,
        "delta_brightness": -0.30,
        "rule_fired": "DISASTER_FLOOD_WATER_SURGE",
    }

    engine = ExplainabilityEngine()
    exp = engine.generate_explanation(
        region_index=4,
        category="DISASTER",
        subcategory="Flood",
        confidence=0.91,
        evidence=evidence,
        t1_patch=t1,
        t2_patch=t2,
        mask_patch=mask,
    )

    assert "water index surge" in exp.explanation_narrative.lower()
    assert exp.spectral_evidence["delta_ndwi"] == 0.35


# ─── 3. End-to-End API Explainability Diagnostics Test ────────────────────────


@pytest.mark.asyncio
async def test_api_explain_endpoint():
    """Verify GET /api/v1/analyses/{analysis_id}/explain/{region_index} returns grounded diagnostics."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/analyses/AN-DEMO-01/explain/1")
        assert res.status_code == 200
        data = res.json()

        assert data["region_index"] == 1
        assert "category" in data
        assert "explanation_narrative" in data
        assert "t1_crop_data_url" in data
        assert "t2_crop_data_url" in data
        assert "mask_crop_data_url" in data
        assert "saliency_heatmap_data_url" in data
        assert data["t1_crop_data_url"].startswith("data:image/png;base64,")
        assert data["reliability"]["overall_reliability"] in ["HIGH", "MEDIUM", "LOW"]
