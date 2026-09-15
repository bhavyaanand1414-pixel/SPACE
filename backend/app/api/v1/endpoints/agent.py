"""
AI Agent API Endpoints — Natural Language Querying with Grounded Tool Calling.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status

from app.agent.orchestrator import AIAgentOrchestrator
from app.agent.tools import AgentToolRegistry
from app.core.logging import logger
from app.schemas.agent import (
    AgentQueryRequest,
    AgentQueryResponse,
    AgentToolInfo,
    ToolExecutionStepSchema,
)

router = APIRouter(prefix="/agent", tags=["Intelligent Grounded AI Agent"])


@router.post(
    "/query",
    response_model=AgentQueryResponse,
    summary="Ask Natural-Language Satellite Change Question",
    description=(
        "Orchestrates 20 grounded backend tools across GIS metadata, co-registration, Siamese change detection, "
        "hierarchical classification, disaster specialists, and time-series engines. "
        "Enforces strict anti-hallucination policies and outputs 'Insufficient data' when ungrounded."
    ),
)
async def query_ai_agent(payload: AgentQueryRequest):
    """Execute grounded agent query with tool calling."""
    try:
        orchestrator = AIAgentOrchestrator()
        result = orchestrator.process_query(payload.query, context=payload.context)

        trace_pydantic = [
            ToolExecutionStepSchema(
                tool_name=step.tool_name,
                arguments=step.arguments,
                result=step.result,
                status=step.status,
                execution_time_ms=step.execution_time_ms,
            )
            for step in result.tool_trace
        ]

        return AgentQueryResponse(
            query=result.query,
            response_text=result.response_text,
            intent_detected=result.intent_detected,
            tool_trace=trace_pydantic,
            citations=result.citations,
            is_grounded=result.is_grounded,
            grounding_notes=result.grounding_notes,
            timestamp=result.timestamp,
        )

    except Exception as exc:
        logger.exception(f"Agent query processing failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent processing failed: {str(exc)}",
        )


@router.get(
    "/tools",
    response_model=List[AgentToolInfo],
    summary="List All 20 Grounded Backend Agent Tools",
    description="Returns full catalogue of deterministic tools available for agent invocation.",
)
async def list_agent_tools():
    """List registered backend tools."""
    registry = AgentToolRegistry()
    return [
        AgentToolInfo(
            name=tool["name"],
            description=tool["description"],
            parameters=tool["parameters"],
        )
        for tool in registry.tools.values()
    ]
