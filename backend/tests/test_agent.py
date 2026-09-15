"""
Unit & Integration Tests for Phase 18 & 19: Grounded AI Agent.

POST C-2 FIX: Tests now supply mock analysis context so the orchestrator
derives all numbers from actual data, never from hardcoded strings.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.agent.tools import AgentToolRegistry
from app.agent.orchestrator import AIAgentOrchestrator
from app.main import app


# ---------------------------------------------------------------------------
# Mock analysis context
# ---------------------------------------------------------------------------
_MOCK_FEATURES = [
    {
        "properties": {
            "region_index": 1,
            "category": "HUMAN",
            "subcategory": "Building",
            "subtype": "Building",
            "area_m2": 45000.0,
            "area_km2": 0.045,
            "mean_confidence": 0.94,
            "severity_level": "HIGH",
            "evidence": {
                "delta_ndvi": -0.22, "delta_ndwi": 0.05,
                "delta_rni": 0.18, "delta_ndbi": None,
                "has_swir": False, "spectral_indices_available": True,
                "delta_brightness": 0.25, "elongation": 1.35,
                "rectangularity": 0.74, "rule_fired": "RECTANGULAR_BUILTUP_INDEX_SURGE",
            },
            "label": "Baseline / Demo Result",
        }
    },
    {
        "properties": {
            "region_index": 2,
            "category": "NATURAL",
            "subcategory": "Vegetation",
            "subtype": "Vegetation",
            "area_m2": 12000.0,
            "area_km2": 0.012,
            "mean_confidence": 0.89,
            "severity_level": "LOW",
            "evidence": {
                "delta_ndvi": 0.21, "delta_ndwi": None,
                "delta_rni": None, "delta_ndbi": None,
                "has_swir": False, "spectral_indices_available": True,
                "delta_brightness": -0.05, "elongation": 1.1,
                "rectangularity": 0.45, "rule_fired": "CANOPY_RESTORATION_NDVI_SURGE",
            },
            "label": "Baseline / Demo Result",
        }
    },
]

_MOCK_STATS = {
    "total_area_m2": 1_000_000.0,
    "total_area_km2": 1.0,
    "total_area_changed_m2": 57_000.0,
    "total_area_changed_km2": 0.057,
    "percentage_changed": 5.7,
    "total_pixels_changed": 570,
    "region_count": 2,
    "area_by_category": {
        "HUMAN": 0.045, "NATURAL": 0.012,
        "DISASTER": 0.0, "ATMOSPHERIC": 0.0, "UNKNOWN": 0.0,
    },
    "area_by_severity": {"HIGH": 0.045, "MEDIUM": 0.0, "LOW": 0.012},
}

_MOCK_CTX = {
    "analysis_id": "TEST-001",
    "statistics": _MOCK_STATS,
    "geojson_features": _MOCK_FEATURES,
    "label": "Baseline / Demo Result",
    "title": "Test Analysis",
}


# ─── 1. Tool Registry ────────────────────────────────────────────────────────

def test_agent_tools_registry_contains_20_tools():
    """Verify all 20 required deterministic tools are registered."""
    registry = AgentToolRegistry()
    expected_tools = [
        "inspect_image", "extract_metadata", "validate_images",
        "calculate_time_difference", "preprocess_images", "register_images",
        "detect_changes", "classify_changes", "calculate_area",
        "calculate_statistics", "analyze_flood", "analyze_earthquake",
        "analyze_cyclone", "analyze_landslide", "analyze_wildfire",
        "generate_geojson", "compare_time_series", "query_database",
        "generate_report", "summarize_analysis",
    ]
    for tool_name in expected_tools:
        assert tool_name in registry.tools, f"Missing required tool: {tool_name}"
    assert len(registry.tools) == 20


# ─── 2. Grounded Intent Tests ────────────────────────────────────────────────

def test_agent_buildings_query_with_context():
    """Buildings query with context returns actual region data, not hardcoded numbers."""
    orch = AIAgentOrchestrator()
    res = orch.process_query("Show all new buildings.", context=_MOCK_CTX)
    assert res.intent_detected == "BUILDINGS_QUERY"
    assert len(res.citations) >= 1
    assert "2.94 km" not in res.response_text, "Fabricated value must not appear"
    assert "30 discrete building sites" not in res.response_text, "Fabricated count must not appear"


def test_agent_buildings_no_context_returns_insufficient():
    """Buildings query without analysis returns Insufficient data."""
    orch = AIAgentOrchestrator()
    res = orch.process_query("Show all new buildings.")
    assert res.intent_detected == "BUILDINGS_QUERY"
    assert "Insufficient data" in res.response_text


def test_agent_human_activities_with_context():
    """Human activities query derives area from context."""
    orch = AIAgentOrchestrator()
    res = orch.process_query("Which changes are human activities?", context=_MOCK_CTX)
    assert res.intent_detected == "HUMAN_ACTIVITIES_QUERY"
    assert "3.82 km" not in res.response_text, "Fabricated value must not appear"


def test_agent_largest_category_with_context():
    """Largest category reads area_by_category from context."""
    orch = AIAgentOrchestrator()
    res = orch.process_query("Which category has the largest affected area?", context=_MOCK_CTX)
    assert res.intent_detected == "LARGEST_CATEGORY_QUERY"
    assert "HUMAN" in res.response_text
    assert "72.9%" not in res.response_text, "Fabricated percentage must not appear"


def test_agent_explain_region_found():
    """Explain change #1 finds actual region and returns grounded evidence."""
    orch = AIAgentOrchestrator()
    res = orch.process_query("Explain change #1.", context=_MOCK_CTX)
    assert res.intent_detected == "EXPLAIN_CHANGE_REGION"
    assert len(res.citations) == 1
    assert res.citations[0]["region_id"] == "CR-001"
    assert "+0.420" not in res.response_text, "Fabricated NDBI value must not appear"


def test_agent_explain_region_not_found():
    """Explain change #99 with context reports region not found gracefully."""
    orch = AIAgentOrchestrator()
    res = orch.process_query("Explain change #99.", context=_MOCK_CTX)
    assert res.intent_detected == "EXPLAIN_CHANGE_REGION"
    assert "not found" in res.response_text.lower()


def test_agent_generate_report():
    """Generate report query calls tool and returns a report ID."""
    orch = AIAgentOrchestrator()
    res = orch.process_query("Generate a report.", context=_MOCK_CTX)
    assert res.intent_detected == "GENERATE_REPORT_QUERY"
    assert "Report Generated" in res.response_text


def test_agent_change_summary_no_hardcoded_values():
    """What changed query reads from context, not from hardcoded 5.24 km."""
    orch = AIAgentOrchestrator()
    res = orch.process_query("What changed?", context=_MOCK_CTX)
    assert res.intent_detected == "CHANGE_DETECTION_SUMMARY"
    assert "5.24" not in res.response_text, "Fabricated area must not appear"
    assert "km" in res.response_text


def test_agent_fallback_general():
    """Unrecognized query returns fallback guidance."""
    orch = AIAgentOrchestrator()
    res = orch.process_query("What is the weather in Mumbai?")
    assert res.intent_detected == "GENERAL_QUERY"
    assert "Insufficient data" in res.response_text


# ─── 3. API Agent Schema Test ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_agent_query_returns_correct_schema():
    """Verify POST /api/v1/agent/query returns required schema fields."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/agent/query",
            json={"query": "Show all new buildings and structural complexes."},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["intent_detected"] == "BUILDINGS_QUERY"
        assert "response_text" in data
        assert "tool_trace" in data
        assert isinstance(data["tool_trace"], list)
        assert len(data["tool_trace"]) >= 1
