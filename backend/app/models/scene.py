"""
Database models for satellite scenes and tiles (PS 26227 §2.2.6).

Scene represents a full satellite acquisition (GeoTIFF/COG).
Tile represents a fixed-size chip extracted from a scene, with its
CLIP embedding stored in the FAISS vector index and its metadata here.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean, DateTime, Float, Integer, JSON, String, Text, ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, generate_uuid_str


class Scene(Base, TimestampMixin):
    """
    A single satellite acquisition ingested into the archive.

    Preserves full geospatial provenance: source path, CRS, bounds,
    sensor, acquisition date — all required by PS 26227 §2.2.5/§2.2.6.
    """
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    source_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash_sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Sensor metadata
    satellite: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sensor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    acquisition_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Raster properties
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    band_count: Mapped[int] = mapped_column(Integer, nullable=False)
    crs: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    epsg_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolution_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Spatial footprint (PostGIS geometry for spatial queries)
    bounds_geom: Mapped[Optional[str]] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326), nullable=True
    )
    bounds_min_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounds_min_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounds_max_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounds_max_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Quality
    cloud_coverage_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    scl_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Ingestion status
    ingestion_status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True, nullable=False
    )  # pending, processing, completed, failed
    tile_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Provenance (PS 26227 §2.2.5)
    provenance: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    tiles: Mapped[List["Tile"]] = relationship("Tile", back_populates="scene", cascade="all, delete-orphan")


class Tile(Base, TimestampMixin):
    """
    A fixed-size image chip extracted from a Scene, with its embedding
    stored in the FAISS vector index.  Spatial metadata is preserved for
    post-filtering search results by AOI.
    """
    __tablename__ = "tiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    scene_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    tile_index: Mapped[int] = mapped_column(Integer, nullable=False)
    row: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    col: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # FAISS index position (integer ID in the flat array)
    faiss_idx: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Spatial footprint
    bounds_geom: Mapped[Optional[str]] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326), nullable=True
    )
    bbox_min_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_min_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_max_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_max_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Inherited from scene but denormalized for fast filtering
    acquisition_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    satellite: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    sensor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Quality
    cloud_fraction: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Optional thumbnail path for UI display
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Relationships
    scene: Mapped["Scene"] = relationship("Scene", back_populates="tiles")
