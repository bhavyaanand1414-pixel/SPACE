from typing import Dict, Any, Optional
from sqlalchemy import String, Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, generate_uuid_str


class Statistics(Base, TimestampMixin):
    __tablename__ = "statistics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Area Breakdown (in km²)
    total_area_km2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    changed_area_km2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unchanged_area_km2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    percentage_changed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Category Specific Totals (in km²)
    human_area_km2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    natural_area_km2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    disaster_area_km2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    atmospheric_area_km2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unknown_area_km2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Count breakdown
    total_regions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    human_regions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    natural_regions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    disaster_regions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    atmospheric_regions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unknown_regions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Detailed Subtype Breakdown (e.g. {"New Building": {"count": 12, "area_km2": 0.45}})
    subtype_breakdown: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    severity_breakdown: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="statistics_rel")  # type: ignore
