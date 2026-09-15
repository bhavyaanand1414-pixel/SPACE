from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Float, JSON, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.db.base import Base, TimestampMixin, generate_uuid_str


class ChangeDetection(Base, TimestampMixin):
    __tablename__ = "change_detections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Raster Mask Artifact Paths
    mask_raster_path: Mapped[str] = mapped_column(String(512), nullable=False)
    probability_map_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    overlay_image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Global detection statistics
    total_pixels_changed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_area_changed_m2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_area_changed_km2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    change_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    region_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="detections")  # type: ignore
    regions: Mapped[List["ChangeRegion"]] = relationship("ChangeRegion", back_populates="detection", cascade="all, delete-orphan")


class ChangeRegion(Base, TimestampMixin):
    __tablename__ = "change_regions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    detection_id: Mapped[str] = mapped_column(String(36), ForeignKey("change_detections.id", ondelete="CASCADE"), index=True, nullable=False)
    region_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # PostGIS Spatial Geometry (WGS84 EPSG:4326) with SQLite JSON variant fallback
    geom = mapped_column(Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True).with_variant(JSON, "sqlite"), nullable=True)
    
    # Pre-computed GeoJSON representation for immediate API delivery
    geojson_geometry: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Spatial properties
    centroid_lat: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_lon: Mapped[float] = mapped_column(Float, nullable=False)
    area_m2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    area_km2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    perimeter_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_min_x: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_min_y: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_max_x: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_max_y: Mapped[float] = mapped_column(Float, nullable=False)

    # Severity & Review Status
    severity_level: Mapped[str] = mapped_column(String(20), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Crop Artifacts for Explainable AI
    crop_before_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    crop_after_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    crop_mask_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    detection: Mapped["ChangeDetection"] = relationship("ChangeDetection", back_populates="regions")
    classification: Mapped[Optional["ClassificationResult"]] = relationship(
        "ClassificationResult", back_populates="region", uselist=False, cascade="all, delete-orphan"
    )
    review_actions: Mapped[List["ReviewAction"]] = relationship("ReviewAction", back_populates="region")  # type: ignore


class ClassificationResult(Base, TimestampMixin):
    __tablename__ = "classification_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    region_id: Mapped[str] = mapped_column(String(36), ForeignKey("change_regions.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Hierarchical Taxonomy
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # HUMAN, NATURAL, DISASTER, ATMOSPHERIC, UNKNOWN
    subtype: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # e.g., New Building, Flood, Road Construction
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)   # 0.0 to 1.0

    # Spectral & Model Evidence
    spectral_evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)

    # Human Override
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    original_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    original_subtype: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    region: Mapped["ChangeRegion"] = relationship("ChangeRegion", back_populates="classification")
