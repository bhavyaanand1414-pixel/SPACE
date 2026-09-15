"""
AI Agent Orchestration Engine (Phase 18 & 19).

STRICT WORKFLOW & SAFETY MANDATE:
C-2 FIX: All response numbers are derived from actual analysis context / tool results.
NEVER hardcode region counts, areas, confidence scores, or category proportions.
If data is unavailable, return "Insufficient data."
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import re

from app.agent.tools import AgentToolRegistry
from app.core.logging import logger


@dataclass
class ToolExecutionStep:
    """Record of a tool call executed during agent reasoning."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    status: str
    execution_time_ms: float = 0.0


@dataclass
class AgentReasoningResult:
    """Final grounded response synthesized from backend tool outputs."""
    query: str
    response_text: str
    intent_detected: str
    tool_trace: List[ToolExecutionStep] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    is_grounded: bool = True
    grounding_notes: str = "Synthesized strictly from deterministic backend GIS/ML tool execution."
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


_INSUFFICIENT = (
    "**Insufficient data**: No completed analysis is loaded in this session.\n\n"
    "Please upload a satellite image pair, run the analysis, then ask your question again."
)


def _stats_from_ctx(ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return ctx.get("statistics") or ctx.get("stats")


def _features_from_ctx(ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    feats = ctx.get("geojson_features") or ctx.get("features") or []
    return [f.get("properties", f) for f in feats]


class AIAgentOrchestrator:
    """
    Intelligent GIS orchestration agent that routes natural-language queries to real backend tools.
    All response numbers are derived exclusively from actual analysis results in context.
    """

    def __init__(self):
        self.registry = AgentToolRegistry()

    def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentReasoningResult:
        """
        Parse user intent, invoke grounded tools, and formulate answer without hallucination.
        All numbers in responses come from `context` (stored analysis) or tool return values.
        """
        q_lower = query.lower().strip()
        trace: List[ToolExecutionStep] = []
        citations: List[Dict[str, Any]] = []
        ctx = context or {}

        stats = _stats_from_ctx(ctx)
        features = _features_from_ctx(ctx)
        has_analysis = stats is not None
        analysis_id = ctx.get("analysis_id", "N/A")

        # -------------------------------------------------------------------
        # Intent: Explain Specific Change Polygon
        # -------------------------------------------------------------------
        match_explain = re.search(r"explain (?:change|region)?\s*#?(\d+)", q_lower)
        if match_explain or ("explain" in q_lower and any(char.isdigit() for char in q_lower)):
            reg_idx = int(match_explain.group(1)) if match_explain else 1
            intent = "EXPLAIN_CHANGE_REGION"

            if not has_analysis:
                text = _INSUFFICIENT
            else:
                region = next((f for f in features if f.get("region_index") == reg_idx), None)
                if region is None:
                    text = (
                        f"Region #{reg_idx} not found in analysis `{analysis_id}`. "
                        f"This analysis has {len(features)} regions (1–{len(features)})."
                    )
                else:
                    ev = region.get("evidence", {})
                    res = self.registry.execute_tool("classify_changes", {
                        k: ev.get(k, 0.0) for k in
                        ["delta_ndbi", "delta_ndvi", "delta_brightness", "elongation", "rectangularity"]
                    })
                    trace.append(ToolExecutionStep(
                        tool_name="classify_changes", arguments={"region_index": reg_idx},
                        result=res, status="success",
                    ))
                    citations.append({
                        "type": "region",
                        "region_id": f"CR-{reg_idx:03d}",
                        "category": region.get("category"),
                        "area_km2": region.get("area_km2", 0.0),
                        "confidence": region.get("mean_confidence", 0.0),
                    })
                    conf_pct = round(float(region.get("mean_confidence", 0)) * 100, 1)
                    text = (
                        f"**Region #CR-{reg_idx:03d}** (Analysis `{analysis_id}`):\n\n"
                        f"• **Category:** `{region.get('category')}` → "
                        f"**{region.get('subcategory', region.get('subtype', 'Unknown'))}** "
                        f"(Confidence: **{conf_pct}%**)\n"
                        f"• **Area:** {region.get('area_km2', 0.0):.4f} km²\n"
                        f"• **ΔNDVI:** {ev.get('delta_ndvi', 'N/A (no NIR band)')}  |  "
                        f"**ΔNDWI:** {ev.get('delta_ndwi', 'N/A')}  |  "
                        f"**ΔRNI:** {ev.get('delta_rni', 'N/A')}\n"
                        f"• **Brightness Δ:** {ev.get('delta_brightness', 'N/A')}  |  "
                        f"**Elongation:** {ev.get('elongation', 'N/A')}  |  "
                        f"**Rectangularity:** {ev.get('rectangularity', 'N/A')}\n"
                        f"• **Decision Rule:** `{ev.get('rule_fired', 'N/A')}`\n"
                        f"• **Spectral Indices Available:** {ev.get('spectral_indices_available', 'N/A')}\n\n"
                        f"> *Output: {region.get('label', 'Baseline / Demo Result')}*"
                    )

        # -------------------------------------------------------------------
        # Intent: Buildings / Construction
        # -------------------------------------------------------------------
        elif any(w in q_lower for w in ["building", "buildings", "housing", "complex", "construction site"]):
            intent = "BUILDINGS_QUERY"
            res = self.registry.execute_tool("query_database", {"query_type": "buildings"})
            trace.append(ToolExecutionStep(
                tool_name="query_database",
                arguments={"category": "HUMAN", "subcategory": "Building"},
                result=res, status="success",
            ))

            if not has_analysis:
                text = _INSUFFICIENT
            else:
                building_regions = [
                    f for f in features
                    if f.get("category") == "HUMAN" and
                    f.get("subcategory", f.get("subtype", "")).lower()
                    in ["building", "urban expansion", "industrial", "construction"]
                ]
                count = len(building_regions)
                total_area = sum(f.get("area_km2", 0.0) for f in building_regions)
                for r in building_regions[:5]:
                    citations.append({
                        "type": "region",
                        "region_id": f"CR-{r.get('region_index', 0):03d}",
                        "category": r.get("category"),
                        "subtype": r.get("subcategory", r.get("subtype")),
                        "area_km2": r.get("area_km2", 0.0),
                        "confidence": r.get("mean_confidence", 0.0),
                    })
                if count == 0:
                    text = (
                        f"No building/urban-expansion regions found in analysis `{analysis_id}` "
                        f"({len(features)} total regions). If images are RGB-only, built-up detection "
                        "requires NIR band for reliable NDVI/RNI evidence."
                    )
                else:
                    top_lines = "\n".join(
                        f"{i+1}. **CR-{r.get('region_index',0):03d}**: "
                        f"{r.get('subcategory', r.get('subtype', 'Building'))} — "
                        f"`{r.get('area_km2',0.0):.4f} km²` "
                        f"({round(float(r.get('mean_confidence',0))*100,1)}%)"
                        for i, r in enumerate(building_regions[:5])
                    )
                    text = (
                        f"**Built-Up Change Regions** (Analysis `{analysis_id}`):\n\n"
                        f"**{count} regions** · **{total_area:.4f} km²** total:\n\n{top_lines}"
                    )

        # -------------------------------------------------------------------
        # Intent: Human activities
        # -------------------------------------------------------------------
        elif "human" in q_lower or "anthropogenic" in q_lower or "activities" in q_lower:
            intent = "HUMAN_ACTIVITIES_QUERY"
            res = self.registry.execute_tool("query_database", {"query_type": "human_activities"})
            trace.append(ToolExecutionStep(
                tool_name="query_database", arguments={"category": "HUMAN"},
                result=res, status="success",
            ))
            if not has_analysis:
                text = _INSUFFICIENT
            else:
                human_regions = [f for f in features if f.get("category") == "HUMAN"]
                human_area = sum(f.get("area_km2", 0.0) for f in human_regions)
                total_changed = stats.get("total_area_changed_km2", 0.0) or 0.0
                pct = round(human_area / total_changed * 100, 1) if total_changed > 0 else 0.0
                subtypes: Dict[str, float] = {}
                for r in human_regions:
                    st = r.get("subcategory", r.get("subtype", "Other"))
                    subtypes[st] = subtypes.get(st, 0.0) + r.get("area_km2", 0.0)
                subtype_lines = "\n".join(
                    f"• **{st}**: {a:.4f} km²"
                    for st, a in sorted(subtypes.items(), key=lambda x: -x[1])
                ) or "• No sub-type breakdown available."
                text = (
                    f"**Human Activity Breakdown** (Analysis `{analysis_id}`):\n\n"
                    f"**{len(human_regions)} regions** · **{human_area:.4f} km²** "
                    f"({pct}% of changed area):\n\n{subtype_lines}"
                )

        # -------------------------------------------------------------------
        # Intent: Largest category
        # -------------------------------------------------------------------
        elif any(w in q_lower for w in ["largest", "biggest", "dominant category", "most area"]):
            intent = "LARGEST_CATEGORY_QUERY"
            res = self.registry.execute_tool("query_database", {"query_type": "categories"})
            trace.append(ToolExecutionStep(
                tool_name="query_database", arguments={"query": "categorical_ranking"},
                result=res, status="success",
            ))
            if not has_analysis:
                text = _INSUFFICIENT
            else:
                area_by_cat = stats.get("area_by_category", {})
                total_changed = stats.get("total_area_changed_km2", 0.0) or 0.0
                ranked = sorted(area_by_cat.items(), key=lambda x: -x[1])
                dominant = ranked[0][0] if ranked else "UNKNOWN"
                lines = "\n".join(
                    f"{i+1}. **{cat}**: **{a:.4f} km²** "
                    f"({round(a/total_changed*100,1) if total_changed>0 else 0}%)"
                    for i, (cat, a) in enumerate(ranked)
                )
                text = (
                    f"**Categorical Area Ranking** (Analysis `{analysis_id}`):\n\n"
                    f"{lines}\n\n**{dominant}** is the primary driver of land-cover change."
                )

        # -------------------------------------------------------------------
        # Intent: Generate Report
        # -------------------------------------------------------------------
        elif any(w in q_lower for w in ["generate report", "report", "pdf", "export report", "create report"]):
            intent = "GENERATE_REPORT_QUERY"
            res = self.registry.execute_tool("generate_report", {
                "analysis_id": analysis_id,
                "title": ctx.get("title", f"Change Intelligence Report ({analysis_id})"),
            })
            trace.append(ToolExecutionStep(
                tool_name="generate_report", arguments={"analysis_id": analysis_id},
                result=res, status="success",
            ))
            text = (
                f"**Report Generated**:\n\n"
                f"• **Report ID:** `{res.get('report_id', 'N/A')}`\n"
                f"• **Title:** {res.get('title', 'N/A')}\n"
                f"• **Status:** {res.get('status', 'Ready for download.')}"
            )

        # -------------------------------------------------------------------
        # Intent: Flood
        # -------------------------------------------------------------------
        elif any(w in q_lower for w in ["flood", "flooded", "inundat", "water extent", "submerge"]):
            intent = "FLOOD_ASSESSMENT"
            res = self.registry.execute_tool("analyze_flood", {"is_sar": False})
            trace.append(ToolExecutionStep(
                tool_name="analyze_flood", arguments={"is_sar": False},
                result=res, status="success",
            ))
            if res.get("status") == "error":
                text = "**Flood Assessment**: Insufficient data — upload a post-event image pair first."
            else:
                text = (
                    f"**Flood Assessment** (Analysis `{analysis_id}`):\n\n"
                    f"• **Inundation Extent:** **{res.get('affected_area_km2', 'N/A')} km²** "
                    f"({res.get('percentage_affected', 'N/A')}% of scene)\n"
                    f"• **Assessment:** {res.get('causality_wording', 'N/A')}\n"
                    f"• **Severity:** {res.get('severity', 'N/A')}\n\n"
                    f"> {res.get('advisory', '')}"
                )

        # -------------------------------------------------------------------
        # Intent: Time-series / timeline
        # -------------------------------------------------------------------
        elif any(w in q_lower for w in ["timeline", "progression", "growth over time", "time series", "over time"]):
            intent = "TIME_SERIES_PROGRESSION"
            res = self.registry.execute_tool("compare_time_series", {})
            trace.append(ToolExecutionStep(
                tool_name="compare_time_series", arguments={}, result=res, status="success",
            ))
            if res.get("status") == "error":
                text = "**Time-Series**: Insufficient data — load multiple dated analyses first."
            else:
                obs = res.get("observations", [])
                obs_lines = "\n".join(
                    f"• **{o.get('date', 'N/A')}**: {o.get('changed_area_km2', 0.0):.4f} km²"
                    for o in obs
                ) or "• No multi-temporal observations available."
                text = (
                    f"**Multi-Temporal Progression** (Analysis `{analysis_id}`):\n\n"
                    f"{obs_lines}\n\n"
                    f"*{res.get('notice', 'Results reflect stored analyses only.')}*"
                )

        # -------------------------------------------------------------------
        # Intent: General change summary
        # -------------------------------------------------------------------
        elif any(w in q_lower for w in ["what changed", "how much area", "area changed", "change", "statistics"]):
            intent = "CHANGE_DETECTION_SUMMARY"
            t1 = self.registry.execute_tool("detect_changes", {})
            trace.append(ToolExecutionStep(
                tool_name="detect_changes", arguments={}, result=t1, status="success",
            ))
            if not has_analysis:
                text = _INSUFFICIENT
            else:
                changed_km2 = stats.get("total_area_changed_km2", 0.0)
                pct = stats.get("percentage_changed", 0.0)
                n_regions = stats.get("region_count", len(features))
                t2 = self.registry.execute_tool(
                    "summarize_analysis",
                    {"changed_area_km2": changed_km2, "percentage_changed": pct},
                )
                trace.append(ToolExecutionStep(
                    tool_name="summarize_analysis",
                    arguments={"changed_area_km2": changed_km2, "percentage_changed": pct},
                    result=t2, status="success",
                ))
                text = (
                    f"**Change Detection Summary** (Analysis `{analysis_id}`):\n\n"
                    f"{t2.get('summary', '')}\n\n"
                    f"• **Total Changed:** **{changed_km2:.4f} km²**\n"
                    f"• **Percentage Changed:** **{pct:.2f}%**\n"
                    f"• **Regions Detected:** **{n_regions}** polygons\n"
                    f"• **Label:** {ctx.get('label', 'Baseline / Demo Result')}"
                )

        # -------------------------------------------------------------------
        # Fallback
        # -------------------------------------------------------------------
        else:
            intent = "GENERAL_QUERY"
            text = (
                "**Insufficient data**: Could not match your query to a GIS operation.\n\n"
                "Try: *'What changed?'*, *'Show all new buildings'*, *'How much area was flooded?'*, "
                "*'Which changes are human activities?'*, *'Explain change #1'*, *'Generate a report'*."
            )

        return AgentReasoningResult(
            query=query,
            response_text=text,
            intent_detected=intent,
            tool_trace=trace,
            citations=citations,
            is_grounded=True,
        )

