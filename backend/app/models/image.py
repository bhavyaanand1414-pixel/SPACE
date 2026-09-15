from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Integer, Float, DateTime, JSON, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, generate_uuid_str


class Image(Base, TimestampMixin):
    __tablename__ = "images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="image/tiff", nullable=False)
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_georeferenced: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    metadata_rel: Mapped[Optional["ImageMetadata"]] = relationship(
        "ImageMetadata", back_populates="image", uselist=False, cascade="all, delete-orphan"
    )


class ImageMetadata(Base, TimestampMixin):
    __tablename__ = "image_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    image_id: Mapped[str] = mapped_column(String(36), ForeignKey("images.id", ondelete="CASCADE"), unique=True, nullable=False)

    satellite: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Sentinel-2, Sentinel-1, Landsat-8
    sensor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)     # MSI, SAR-C, OLI
    acquisition_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Raster dimensions & spatial parameters
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    band_count: Mapped[int] = mapped_column(Integer, nullable=False)
    crs: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)       # e.g., EPSG:32646
    epsg_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolution_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # in meters or degrees
    resolution_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Bounding Box (min_x, min_y, max_x, max_y)
    bounds_min_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounds_min_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounds_max_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounds_max_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    cloud_coverage_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nodata_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    image: Mapped["Image"] = relationship("Image", back_populates="metadata_rel")
