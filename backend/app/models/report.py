from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, generate_uuid_str


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    pdf_file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    summary_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_interpretation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    
    # Disclaimer and verification watermark
    disclaimer: Mapped[str] = mapped_column(
        Text,
        default="Results are AI/model-derived and should be validated against authoritative remote-sensing and GIS data before operational decision-making.",
        nullable=False,
    )

    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="reports")  # type: ignore
