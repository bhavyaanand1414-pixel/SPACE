"""
Pydantic Schemas for AI Agent Tool Calling and Conversational Reasoning.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    """Request payload for querying the grounded AI agent."""
    query: str = Field(..., min_length=2, description="Natural language satellite analysis question")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session context (image IDs, analysis IDs)")


class ToolExecutionStepSchema(BaseModel):
    """Execution step record for a single tool call."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    status: str
    execution_time_ms: float = 0.0


class AgentQueryResponse(BaseModel):
    """Complete grounded AI Agent response with execution tool trace and region citations."""
    query: str
    response_text: str
    intent_detected: str
    tool_trace: List[ToolExecutionStepSchema] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    is_grounded: bool = True
    grounding_notes: str = "Synthesized strictly from deterministic backend GIS/ML tool execution."
    timestamp: str


class AgentToolInfo(BaseModel):
    """Metadata describing a registered backend tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
