"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-30 01:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, default=False),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. projects
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("study_area", sa.String(length=255), nullable=True),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)

    # 3. images
    op.create_table(
        "images",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("is_georeferenced", sa.Boolean(), nullable=False, default=True),
        sa.Column("thumbnail_path", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. image_metadata
    op.create_table(
        "image_metadata",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("image_id", sa.String(length=36), nullable=False),
        sa.Column("satellite", sa.String(length=100), nullable=True),
        sa.Column("sensor", sa.String(length=100), nullable=True),
        sa.Column("acquisition_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("band_count", sa.Integer(), nullable=False),
        sa.Column("crs", sa.String(length=100), nullable=True),
        sa.Column("epsg_code", sa.Integer(), nullable=True),
        sa.Column("resolution_x", sa.Float(), nullable=True),
        sa.Column("resolution_y", sa.Float(), nullable=True),
        sa.Column("bounds_min_x", sa.Float(), nullable=True),
        sa.Column("bounds_min_y", sa.Float(), nullable=True),
        sa.Column("bounds_max_x", sa.Float(), nullable=True),
        sa.Column("bounds_max_y", sa.Float(), nullable=True),
        sa.Column("cloud_coverage_percentage", sa.Float(), nullable=True),
        sa.Column("nodata_value", sa.Float(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["image_id"], ["images.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("image_id"),
    )

    # 5. analyses
    op.create_table(
        "analyses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("study_area", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("image_before_id", sa.String(length=36), nullable=False),
        sa.Column("image_after_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("confidence_threshold", sa.Float(), nullable=False),
        sa.Column("image_quality_score", sa.Float(), nullable=True),
        sa.Column("registration_quality_score", sa.Float(), nullable=True),
        sa.Column("overall_reliability", sa.String(length=50), nullable=True),
        sa.Column("temporal_difference_days", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["image_after_id"], ["images.id"]),
        sa.ForeignKeyConstraint(["image_before_id"], ["images.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analyses_status"), "analyses", ["status"], unique=False)

    # 6. analysis_jobs
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("stage", sa.String(length=100), nullable=False),
        sa.Column("progress_percentage", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stage_durations_sec", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_jobs_analysis_id"), "analysis_jobs", ["analysis_id"], unique=False)

    # 7. change_detections
    op.create_table(
        "change_detections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("mask_raster_path", sa.String(length=512), nullable=False),
        sa.Column("probability_map_path", sa.String(length=512), nullable=True),
        sa.Column("overlay_image_path", sa.String(length=512), nullable=True),
        sa.Column("total_pixels_changed", sa.Integer(), nullable=False),
        sa.Column("total_area_changed_m2", sa.Float(), nullable=False),
        sa.Column("total_area_changed_km2", sa.Float(), nullable=False),
        sa.Column("change_percentage", sa.Float(), nullable=False),
        sa.Column("region_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_change_detections_analysis_id"), "change_detections", ["analysis_id"], unique=False)

    # 8. change_regions
    op.create_table(
        "change_regions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("detection_id", sa.String(length=36), nullable=False),
        sa.Column("region_index", sa.Integer(), nullable=False),
        sa.Column("geojson_geometry", sa.JSON(), nullable=False),
        sa.Column("centroid_lat", sa.Float(), nullable=False),
        sa.Column("centroid_lon", sa.Float(), nullable=False),
        sa.Column("area_m2", sa.Float(), nullable=False),
        sa.Column("area_km2", sa.Float(), nullable=False),
        sa.Column("perimeter_m", sa.Float(), nullable=True),
        sa.Column("bbox_min_x", sa.Float(), nullable=False),
        sa.Column("bbox_min_y", sa.Float(), nullable=False),
        sa.Column("bbox_max_x", sa.Float(), nullable=False),
        sa.Column("bbox_max_y", sa.Float(), nullable=False),
        sa.Column("severity_level", sa.String(length=20), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column("is_reviewed", sa.Boolean(), nullable=False),
        sa.Column("crop_before_path", sa.String(length=512), nullable=True),
        sa.Column("crop_after_path", sa.String(length=512), nullable=True),
        sa.Column("crop_mask_path", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["detection_id"], ["change_detections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_change_regions_detection_id"), "change_regions", ["detection_id"], unique=False)

    # 9. classification_results
    op.create_table(
        "classification_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("region_id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("subtype", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("spectral_evidence", sa.JSON(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("is_overridden", sa.Boolean(), nullable=False),
        sa.Column("original_category", sa.String(length=50), nullable=True),
        sa.Column("original_subtype", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["change_regions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("region_id"),
    )
    op.create_index(op.f("ix_classification_results_category"), "classification_results", ["category"], unique=False)
    op.create_index(op.f("ix_classification_results_subtype"), "classification_results", ["subtype"], unique=False)

    # 10. statistics
    op.create_table(
        "statistics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("total_area_km2", sa.Float(), nullable=False),
        sa.Column("changed_area_km2", sa.Float(), nullable=False),
        sa.Column("unchanged_area_km2", sa.Float(), nullable=False),
        sa.Column("percentage_changed", sa.Float(), nullable=False),
        sa.Column("human_area_km2", sa.Float(), nullable=False),
        sa.Column("natural_area_km2", sa.Float(), nullable=False),
        sa.Column("disaster_area_km2", sa.Float(), nullable=False),
        sa.Column("atmospheric_area_km2", sa.Float(), nullable=False),
        sa.Column("unknown_area_km2", sa.Float(), nullable=False),
        sa.Column("total_regions_count", sa.Integer(), nullable=False),
        sa.Column("human_regions_count", sa.Integer(), nullable=False),
        sa.Column("natural_regions_count", sa.Integer(), nullable=False),
        sa.Column("disaster_regions_count", sa.Integer(), nullable=False),
        sa.Column("atmospheric_regions_count", sa.Integer(), nullable=False),
        sa.Column("unknown_regions_count", sa.Integer(), nullable=False),
        sa.Column("subtype_breakdown", sa.JSON(), nullable=True),
        sa.Column("severity_breakdown", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_id"),
    )

    # 11. reports
    op.create_table(
        "reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("pdf_file_path", sa.String(length=512), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("ai_interpretation", sa.Text(), nullable=True),
        sa.Column("metadata_snapshot", sa.JSON(), nullable=True),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_analysis_id"), "reports", ["analysis_id"], unique=False)

    # 12. agent_sessions
    op.create_table(
        "agent_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("system_prompt_snapshot", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 13. agent_messages
    op.create_table(
        "agent_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls", sa.JSON(), nullable=True),
        sa.Column("tool_results", sa.JSON(), nullable=True),
        sa.Column("grounded_evidence", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_messages_session_id"), "agent_messages", ["session_id"], unique=False)

    # 14. model_versions
    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("version_tag", sa.String(length=50), nullable=False),
        sa.Column("architecture", sa.String(length=100), nullable=False),
        sa.Column("weights_path", sa.String(length=512), nullable=False),
        sa.Column("f1_score", sa.Float(), nullable=True),
        sa.Column("iou_score", sa.Float(), nullable=True),
        sa.Column("precision_score", sa.Float(), nullable=True),
        sa.Column("recall_score", sa.Float(), nullable=True),
        sa.Column("hyperparameters", sa.JSON(), nullable=True),
        sa.Column("is_active_production", sa.Boolean(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_tag"),
    )
    op.create_index(op.f("ix_model_versions_model_name"), "model_versions", ["model_name"], unique=False)

    # 15. datasets
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("license", sa.String(length=100), nullable=False),
        sa.Column("resolution_m", sa.Float(), nullable=True),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("train_split_count", sa.Integer(), nullable=False),
        sa.Column("val_split_count", sa.Integer(), nullable=False),
        sa.Column("test_split_count", sa.Integer(), nullable=False),
        sa.Column("spatial_separation_strategy", sa.String(length=255), nullable=True),
        sa.Column("metadata_info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 16. annotations
    op.create_table(
        "annotations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("image_pair_id", sa.String(length=36), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("subtype", sa.String(length=100), nullable=False),
        sa.Column("geojson_geometry", sa.JSON(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("verified_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_annotations_dataset_id"), "annotations", ["dataset_id"], unique=False)

    # 17. review_actions
    op.create_table(
        "review_actions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("region_id", sa.String(length=36), nullable=False),
        sa.Column("reviewer_id", sa.String(length=36), nullable=True),
        sa.Column("original_category", sa.String(length=50), nullable=False),
        sa.Column("corrected_category", sa.String(length=50), nullable=False),
        sa.Column("original_subtype", sa.String(length=100), nullable=False),
        sa.Column("corrected_subtype", sa.String(length=100), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("added_to_active_learning_queue", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["change_regions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_review_actions_region_id"), "review_actions", ["region_id"], unique=False)

    # 18. model_runs
    op.create_table(
        "model_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_version_id", sa.String(length=36), nullable=True),
        sa.Column("dataset_id", sa.String(length=36), nullable=True),
        sa.Column("experiment_name", sa.String(length=255), nullable=False),
        sa.Column("epochs_trained", sa.Integer(), nullable=False),
        sa.Column("best_val_loss", sa.Float(), nullable=True),
        sa.Column("best_val_iou", sa.Float(), nullable=True),
        sa.Column("metrics_history", sa.JSON(), nullable=True),
        sa.Column("training_artifacts_path", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("model_runs")
    op.drop_index(op.f("ix_review_actions_region_id"), table_name="review_actions")
    op.drop_table("review_actions")
    op.drop_index(op.f("ix_annotations_dataset_id"), table_name="annotations")
    op.drop_table("annotations")
    op.drop_table("datasets")
    op.drop_index(op.f("ix_model_versions_model_name"), table_name="model_versions")
    op.drop_table("model_versions")
    op.drop_index(op.f("ix_agent_messages_session_id"), table_name="agent_messages")
    op.drop_table("agent_messages")
    op.drop_table("agent_sessions")
    op.drop_index(op.f("ix_reports_analysis_id"), table_name="reports")
    op.drop_table("reports")
    op.drop_table("statistics")
    op.drop_index(op.f("ix_classification_results_subtype"), table_name="classification_results")
    op.drop_index(op.f("ix_classification_results_category"), table_name="classification_results")
    op.drop_table("classification_results")
    op.drop_index(op.f("ix_change_regions_detection_id"), table_name="change_regions")
    op.drop_table("change_regions")
    op.drop_index(op.f("ix_change_detections_analysis_id"), table_name="change_detections")
    op.drop_table("change_detections")
    op.drop_index(op.f("ix_analysis_jobs_analysis_id"), table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
    op.drop_index(op.f("ix_analyses_status"), table_name="analyses")
    op.drop_table("analyses")
    op.drop_table("image_metadata")
    op.drop_table("images")
    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_table("projects")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
