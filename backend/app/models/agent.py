from typing import Optional, List, Dict, Any
from sqlalchemy import String, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, generate_uuid_str


class AgentSession(Base, TimestampMixin):
    __tablename__ = "agent_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    title: Mapped[str] = mapped_column(String(255), default="Satellite Intelligence Q&A", nullable=False)
    analysis_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    system_prompt_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    messages: Mapped[List["AgentMessage"]] = relationship("AgentMessage", back_populates="session", cascade="all, delete-orphan")


class AgentMessage(Base, TimestampMixin):
    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Tool Execution Details
    tool_calls: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
    tool_results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    grounded_evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    session: Mapped["AgentSession"] = relationship("AgentSession", back_populates="messages")
