from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Float, JSON, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, generate_uuid_str


class ModelVersion(Base, TimestampMixin):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    model_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # SiameseUNet, BaselineDetector, ChangeFormer
    version_tag: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g., v1.2.0
    architecture: Mapped[str] = mapped_column(String(100), nullable=False)
    weights_path: Mapped[str] = mapped_column(String(512), nullable=False)
    
    # Benchmark Metrics
    f1_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    iou_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precision_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    hyperparameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    is_active_production: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Dataset(Base, TimestampMixin):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(255), default="ISRO / Sentinel-2 / LEVIR-CD", nullable=False)
    license: Mapped[str] = mapped_column(String(100), default="Open Access", nullable=False)
    resolution_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    train_split_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    val_split_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    test_split_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spatial_separation_strategy: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    annotations: Mapped[List["Annotation"]] = relationship("Annotation", back_populates="dataset", cascade="all, delete-orphan")


class Annotation(Base, TimestampMixin):
    __tablename__ = "annotations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    image_pair_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subtype: Mapped[str] = mapped_column(String(100), nullable=False)
    geojson_geometry: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="annotations")


class ReviewAction(Base, TimestampMixin):
    __tablename__ = "review_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    region_id: Mapped[str] = mapped_column(String(36), ForeignKey("change_regions.id", ondelete="CASCADE"), index=True, nullable=False)
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    original_category: Mapped[str] = mapped_column(String(50), nullable=False)
    corrected_category: Mapped[str] = mapped_column(String(50), nullable=False)
    original_subtype: Mapped[str] = mapped_column(String(100), nullable=False)
    corrected_subtype: Mapped[str] = mapped_column(String(100), nullable=False)
    
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    added_to_active_learning_queue: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    region: Mapped["ChangeRegion"] = relationship("ChangeRegion", back_populates="review_actions")  # type: ignore
    reviewer: Mapped[Optional["User"]] = relationship("User", back_populates="reviews")             # type: ignore


class ModelRun(Base, TimestampMixin):
    __tablename__ = "model_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_str)
    model_version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True)
    dataset_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    
    experiment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    epochs_trained: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_val_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    best_val_iou: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metrics_history: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    training_artifacts_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
