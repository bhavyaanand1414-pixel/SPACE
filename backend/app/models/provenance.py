"""
Provenance and audit trail model (PS 26227 §2.2.5).

Tracks the complete processing history for every entity in the system
(scene, tile, analysis, change detection result) so exported results
retain source-scene and processing provenance.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, generate_uuid_str


class ProvenanceRecord(Base, TimestampMixin):
    """
    Immutable audit record tracking every processing step applied to an entity.

    Each record captures: what was done, when, with which model version,
    and from which source scene — satisfying the PS 26227 requirement that
    exported results retain source-scene and processing provenance.
    """
    __tablename__ = "provenance"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)

    # What entity this provenance record belongs to
    entity_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # scene, tile, analysis, change
    entity_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    # Source lineage
    source_scene_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    source_scene_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Processing details
    pipeline_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    processing_steps: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, default=list, nullable=True
    )
    # Each step: {"name": "...", "timestamp": "...", "parameters": {...}, "output_summary": "..."}

    # Model info
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model_weights_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Human review actions (for audit trail)
    reviewer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    review_action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # approved, corrected, rejected
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ReviewRecord(Base, TimestampMixin):
    """
    Persistent review record replacing the in-memory REVIEW_RECORDS_STORE.

    Stores human-in-the-loop decisions with full audit trail as required
    by PS 26227 §2.2.5.
    """
    __tablename__ = "review_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    review_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    region_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Original ML prediction
    original_category: Mapped[str] = mapped_column(String(100), nullable=False)
    original_subcategory: Mapped[str] = mapped_column(String(100), nullable=False)
    original_confidence: Mapped[float] = mapped_column(nullable=False)

    # Human correction
    corrected_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    corrected_subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status and reviewer
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String(100), default="Unassigned", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Model and training metadata
    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    is_active_learning_candidate: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Source provenance
    source_scene_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    processing_history: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
