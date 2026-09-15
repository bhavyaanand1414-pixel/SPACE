from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Float, DateTime, JSON, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, generate_uuid_str


class Analysis(Base, TimestampMixin):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    study_area: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="created", index=True, nullable=False)  # created, queued, processing, completed, failed
    
    # Input Images
    image_before_id: Mapped[str] = mapped_column(String(36), ForeignKey("images.id"), nullable=False)
    image_after_id: Mapped[str] = mapped_column(String(36), ForeignKey("images.id"), nullable=False)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)

    # Model Configuration & Metadata
    model_name: Mapped[str] = mapped_column(String(100), default="siamese_unet", nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.65, nullable=False)
    
    # Validation & Quality metrics
    image_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0 to 100
    registration_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overall_reliability: Mapped[Optional[str]] = mapped_column(String(50), default="HIGH", nullable=True) # LOW, MEDIUM, HIGH

    # Temporal Difference
    temporal_difference_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="analyses")  # type: ignore
    image_before: Mapped["Image"] = relationship("Image", foreign_keys=[image_before_id])      # type: ignore
    image_after: Mapped["Image"] = relationship("Image", foreign_keys=[image_after_id])        # type: ignore
    jobs: Mapped[List["AnalysisJob"]] = relationship("AnalysisJob", back_populates="analysis", cascade="all, delete-orphan")
    detections: Mapped[List["ChangeDetection"]] = relationship("ChangeDetection", back_populates="analysis", cascade="all, delete-orphan")  # type: ignore
    statistics_rel: Mapped[Optional["Statistics"]] = relationship("Statistics", back_populates="analysis", uselist=False, cascade="all, delete-orphan")  # type: ignore
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="analysis", cascade="all, delete-orphan")  # type: ignore


class AnalysisJob(Base, TimestampMixin):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False)
    stage: Mapped[str] = mapped_column(String(100), default="queued", nullable=False)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    stage_durations_sec: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="jobs")
