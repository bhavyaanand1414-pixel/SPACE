import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.compiler import compiles
from geoalchemy2 import Geometry
import geoalchemy2.admin.dialects.sqlite as sqlite_admin

from app.db.base import Base
from app.db.session import check_db_health
from app.models import (
    User,
    Project,
    Image,
    ImageMetadata,
    Analysis,
    AnalysisJob,
    ChangeDetection,
    ChangeRegion,
    ClassificationResult,
    Statistics,
    Report,
    AgentSession,
    AgentMessage,
    ModelVersion,
    Dataset,
    Annotation,
    ReviewAction,
    ModelRun,
)


@pytest.fixture
def in_memory_db():
    """Create a clean in-memory SQLite database for testing all 18 ORM models."""
    import geoalchemy2.admin
    sqlite_mod = geoalchemy2.admin.select_dialect("sqlite")
    orig_after_create = sqlite_mod.after_create
    orig_before_create = sqlite_mod.before_create
    orig_after_drop = sqlite_mod.after_drop
    orig_before_drop = sqlite_mod.before_drop

    sqlite_mod.after_create = lambda *args, **kwargs: None
    sqlite_mod.before_create = lambda *args, **kwargs: None
    sqlite_mod.after_drop = lambda *args, **kwargs: None
    sqlite_mod.before_drop = lambda *args, **kwargs: None

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        sqlite_mod.after_create = orig_after_create
        sqlite_mod.before_create = orig_before_create
        sqlite_mod.after_drop = orig_after_drop
        sqlite_mod.before_drop = orig_before_drop


def test_database_health_check():
    """Verify check_db_health returns expected dictionary structure."""
    result = check_db_health()
    assert "connected" in result
    assert "status" in result


def test_complete_orm_model_lifecycle(in_memory_db):
    """Verify that all 18 models can be inserted, queried, and linked via foreign keys."""
    db = in_memory_db
    now = datetime.now(timezone.utc)

    # 1. User
    user = User(
        email="analyst@isro.gov.in",
        hashed_password="secure_hash_example",
        full_name="Dr. Vikram Sarabhai",
        organization="ISRO Space Applications Centre",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.id is not None
    assert user.email == "analyst@isro.gov.in"

    # 2. Project
    project = Project(
        name="Guwahati Urban Sprawl 2020-2026",
        description="Multi-temporal optical and SAR change detection",
        study_area="Guwahati, Assam",
        owner_id=user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    assert project.id is not None
    assert len(user.projects) == 1

    # 3. Images
    img_before = Image(
        filename="guwahati_2020_b2_b3_b4_b8.tif",
        original_filename="Sentinel2A_20200115.tif",
        file_path="/data/storage/guwahati_2020.tif",
        file_size_bytes=15485760,
    )
    img_after = Image(
        filename="guwahati_2026_b2_b3_b4_b8.tif",
        original_filename="Sentinel2B_20260115.tif",
        file_path="/data/storage/guwahati_2026.tif",
        file_size_bytes=15498240,
    )
    db.add_all([img_before, img_after])
    db.commit()

    # 4. Image Metadata
    meta_before = ImageMetadata(
        image_id=img_before.id,
        satellite="Sentinel-2A",
        sensor="MSI",
        width=1024,
        height=1024,
        band_count=4,
        crs="EPSG:32646",
        epsg_code=32646,
        resolution_x=10.0,
        resolution_y=10.0,
        bounds_min_x=91.60,
        bounds_min_y=26.10,
        bounds_max_x=91.85,
        bounds_max_y=26.25,
        cloud_coverage_percentage=2.4,
    )
    db.add(meta_before)
    db.commit()
    assert img_before.metadata_rel.satellite == "Sentinel-2A"

    # 5. Analysis
    analysis = Analysis(
        title="Guwahati Infrastructure Expansion Analysis",
        study_area="Guwahati, Assam",
        status="completed",
        image_before_id=img_before.id,
        image_after_id=img_after.id,
        project_id=project.id,
        model_name="siamese_unet",
        model_version="1.0.0",
        confidence_threshold=0.70,
        image_quality_score=92.5,
        registration_quality_score=97.0,
        overall_reliability="HIGH",
        temporal_difference_days=2191.0,
    )
    db.add(analysis)
    db.commit()

    # 6. Analysis Job
    job = AnalysisJob(
        analysis_id=analysis.id,
        stage="completed",
        progress_percentage=100,
        status="success",
    )
    db.add(job)
    db.commit()

    # 7. Change Detection
    detection = ChangeDetection(
        analysis_id=analysis.id,
        mask_raster_path="/data/storage/masks/change_mask_1.tif",
        total_pixels_changed=52400,
        total_area_changed_m2=5240000.0,
        total_area_changed_km2=5.24,
        change_percentage=4.99,
        region_count=42,
    )
    db.add(detection)
    db.commit()

    # 8. Change Region
    region = ChangeRegion(
        detection_id=detection.id,
        region_index=1,
        geojson_geometry={"type": "Polygon", "coordinates": [[[91.70, 26.15], [91.72, 26.15], [91.72, 26.17], [91.70, 26.17], [91.70, 26.15]]]},
        centroid_lat=26.16,
        centroid_lon=91.71,
        area_m2=45000.0,
        area_km2=0.045,
        bbox_min_x=91.70,
        bbox_min_y=26.15,
        bbox_max_x=91.72,
        bbox_max_y=26.17,
        severity_level="MEDIUM",
    )
    db.add(region)
    db.commit()

    # 9. Classification Result
    classification = ClassificationResult(
        region_id=region.id,
        category="HUMAN",
        subtype="New Building",
        confidence=0.94,
        spectral_evidence={"NDBI_delta": "+0.38", "NDVI_delta": "-0.42"},
        explanation="Structural built-up signature confirmed with positive NDBI difference.",
    )
    db.add(classification)
    db.commit()

    # 10. Statistics
    stats = Statistics(
        analysis_id=analysis.id,
        total_area_km2=104.85,
        changed_area_km2=5.24,
        unchanged_area_km2=99.61,
        percentage_changed=4.99,
        human_area_km2=3.82,
        natural_area_km2=1.12,
        disaster_area_km2=0.0,
        atmospheric_area_km2=0.30,
        unknown_area_km2=0.0,
        total_regions_count=42,
        human_regions_count=30,
        natural_regions_count=8,
        disaster_regions_count=0,
        atmospheric_regions_count=4,
        unknown_regions_count=0,
    )
    db.add(stats)
    db.commit()

    # 11. Report
    report = Report(
        analysis_id=analysis.id,
        title="Guwahati Change Intelligence Report",
        pdf_file_path="/reports/report_guwahati_2026.pdf",
        file_size_bytes=248500,
        summary_text="Significant human urban expansion detected with 3.82 km² new built-up area.",
    )
    db.add(report)
    db.commit()

    # 12. Agent Session & 13. Agent Message
    session = AgentSession(
        title="Agent Conversation: Guwahati Sprawl",
        analysis_id=analysis.id,
        user_id=user.id,
    )
    db.add(session)
    db.commit()

    msg = AgentMessage(
        session_id=session.id,
        role="user",
        content="What is the total newly constructed area in Guwahati?",
    )
    db.add(msg)
    db.commit()

    # 14. Model Version
    m_ver = ModelVersion(
        model_name="SiameseUNet",
        version_tag="v1.2.0",
        architecture="ResNet50-SiameseUNet",
        weights_path="/ml/checkpoints/siamese_unet_v1.2.0.pt",
        f1_score=0.912,
        iou_score=0.845,
        precision_score=0.930,
        recall_score=0.895,
        is_active_production=True,
    )
    db.add(m_ver)
    db.commit()

    # 15. Dataset & 16. Annotation
    ds = Dataset(
        name="LEVIR-CD-Guwahati-Subset",
        source="Sentinel-2 MSI",
        license="CC-BY-4.0",
        sample_count=250,
        train_split_count=180,
        val_split_count=35,
        test_split_count=35,
    )
    db.add(ds)
    db.commit()

    annot = Annotation(
        dataset_id=ds.id,
        category="HUMAN",
        subtype="New Building",
        geojson_geometry={"type": "Polygon", "coordinates": [[[91.70, 26.15], [91.72, 26.15], [91.72, 26.17], [91.70, 26.17], [91.70, 26.15]]]},
        is_verified=True,
        verified_by_user_id=user.id,
    )
    db.add(annot)
    db.commit()

    # 17. Review Action
    rev = ReviewAction(
        region_id=region.id,
        reviewer_id=user.id,
        original_category="UNKNOWN",
        corrected_category="HUMAN",
        original_subtype="Unknown",
        corrected_subtype="New Building",
        review_notes="Verified against High-Res reference imagery.",
    )
    db.add(rev)
    db.commit()

    # 18. Model Run
    m_run = ModelRun(
        model_version_id=m_ver.id,
        dataset_id=ds.id,
        experiment_name="siamese_unet_levir_finetune_v1",
        epochs_trained=50,
        best_val_loss=0.142,
        best_val_iou=0.845,
    )
    db.add(m_run)
    db.commit()

    # Verification queries
    queried_analysis = db.query(Analysis).filter(Analysis.id == analysis.id).first()
    assert queried_analysis is not None
    assert len(queried_analysis.detections) == 1
    assert queried_analysis.statistics_rel.human_area_km2 == 3.82
    assert queried_analysis.project.owner.email == "analyst@isro.gov.in"
    assert queried_analysis.detections[0].regions[0].classification.category == "HUMAN"
    assert queried_analysis.detections[0].regions[0].classification.subtype == "New Building"
