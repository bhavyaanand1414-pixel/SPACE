"""
Unit tests for Hierarchical Change Classification & Remote Sensing Evidence Extraction (Phase 12).
"""

import numpy as np
import pytest
from app.ml.classifier import (
    ClassificationEvidence,
    HierarchicalChangeClassifier,
)


@pytest.fixture
def classifier():
    return HierarchicalChangeClassifier(model_version="1.0.0")


# ─── 1. Human Infrastructure Classification Tests ─────────────────────────────


def test_human_road_classification_high_elongation(classifier):
    """Verify linear high-aspect-ratio corridor is classified as HUMAN: Road."""
    evidence = ClassificationEvidence(
        delta_brightness=0.18,
        elongation=4.8,
        rectangularity=0.62,
        area_m2=45000.0,
    )
    decision = classifier.classify(evidence)

    assert decision.category == "HUMAN"
    assert decision.subcategory == "Road"
    assert decision.confidence >= 0.85
    assert decision.evidence["elongation"] == 4.8
    assert "timestamp" in decision.__dict__


def test_human_building_classification_high_rectangularity(classifier):
    """Verify compact rectangular built-up structure is classified as HUMAN: Building."""
    evidence = ClassificationEvidence(
        delta_ndbi=0.22,
        delta_brightness=0.25,
        rectangularity=0.78,
        compactness=0.82,
        area_m2=12000.0,
    )
    decision = classifier.classify(evidence)

    assert decision.category == "HUMAN"
    assert decision.subcategory == "Building"
    assert decision.confidence >= 0.90
    assert decision.evidence["delta_ndbi"] == 0.22


def test_human_mining_large_irregular_earthwork(classifier):
    """Verify large irregular excavation footprint is classified as HUMAN: Mining."""
    evidence = ClassificationEvidence(
        delta_brightness=0.32,
        compactness=0.25,
        area_m2=150000.0,
    )
    decision = classifier.classify(evidence)

    assert decision.category == "HUMAN"
    assert decision.subcategory == "Mining"
    assert decision.confidence >= 0.80


# ─── 2. Disaster Inundation & Hazard Tests ────────────────────────────────────


def test_disaster_flood_water_surge(classifier):
    """Verify strong positive NDWI water surge is classified as DISASTER: Flood."""
    evidence = ClassificationEvidence(
        delta_ndwi=0.35,
        mean_t2_brightness=0.18,
        area_m2=80000.0,
    )
    decision = classifier.classify(evidence)

    assert decision.category == "DISASTER"
    assert decision.subcategory == "Flood"
    assert decision.confidence >= 0.88


def test_disaster_wildfire_burn_scar(classifier):
    """Verify vegetation collapse with low char albedo is classified as DISASTER: Wildfire."""
    evidence = ClassificationEvidence(
        delta_ndvi=-0.45,
        mean_t2_brightness=0.12,
        spectral_variance=0.08,
        area_m2=200000.0,
    )
    decision = classifier.classify(evidence)

    assert decision.category == "DISASTER"
    assert decision.subcategory == "Wildfire"
    assert decision.confidence >= 0.85


# ─── 3. Natural Environmental Shift Tests ─────────────────────────────────────


def test_natural_vegetation_canopy_surge(classifier):
    """Verify positive NDVI restoration is classified as NATURAL: Vegetation."""
    evidence = ClassificationEvidence(
        delta_ndvi=0.28,
        area_m2=35000.0,
    )
    decision = classifier.classify(evidence)

    assert decision.category == "NATURAL"
    assert decision.subcategory == "Vegetation"
    assert decision.confidence >= 0.85


def test_natural_river_riparian_shift(classifier):
    """Verify elongated waterbody change is classified as NATURAL: River."""
    evidence = ClassificationEvidence(
        delta_ndwi=0.22,
        elongation=3.6,
        mean_t2_brightness=0.45,
    )
    decision = classifier.classify(evidence)

    assert decision.category == "NATURAL"
    assert decision.subcategory == "River"
    assert decision.confidence >= 0.85


# ─── 4. Atmospheric Artifacts & Unknown Fallback ──────────────────────────────


def test_atmospheric_cloud_extreme_brightness(classifier):
    """Verify extreme specular spike is classified as ATMOSPHERIC: Cloud."""
    evidence = ClassificationEvidence(
        delta_brightness=0.55,
        mean_t2_brightness=0.92,
    )
    decision = classifier.classify(evidence)

    assert decision.category == "ATMOSPHERIC"
    assert decision.subcategory == "Cloud"
    assert decision.confidence >= 0.90


def test_unknown_fallback_ambiguous(classifier):
    """Verify ambiguous sub-threshold signal gracefully falls back to UNKNOWN."""
    evidence = ClassificationEvidence(
        delta_ndvi=0.02,
        delta_ndwi=0.01,
        delta_brightness=0.03,
        elongation=1.1,
    )
    decision = classifier.classify(evidence)

    assert decision.category == "UNKNOWN"
    assert decision.subcategory == "Unknown"
    assert decision.confidence == 0.50


# ─── 5. Direct Evidence Extraction from Image Arrays ──────────────────────────


def test_extract_evidence_from_synthetic_raster(classifier):
    """Verify end-to-end evidence extraction from 3-band raster patches."""
    h, w = 64, 64
    t1 = np.full((3, h, w), 0.3, dtype=np.float32)
    t2 = np.full((3, h, w), 0.3, dtype=np.float32)

    # Insert altered rectangle (Building)
    t2[:, 15:45, 15:35] = 0.85
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[15:45, 15:35] = 255

    evidence = classifier.extract_evidence(t1, t2, mask, resolution_m=10.0)

    assert evidence.delta_brightness > 0.1
    assert evidence.area_m2 == float(30 * 20 * 100)
    assert evidence.rectangularity > 0.7

    decision = classifier.classify(evidence)
    assert decision.category == "HUMAN"
    assert decision.subcategory in ["Building", "Urban expansion", "Construction"]
    assert "delta_ndvi" in decision.evidence
    assert decision.model_version == "1.0.0"
