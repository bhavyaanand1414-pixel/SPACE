"""
Unit tests for Remote Sensing Preprocessing & Sub-Pixel Co-Registration Engine (Phase 7).
"""

import io
import os
import pytest
import numpy as np
from PIL import Image as PILImage
from app.gis.preprocessing import (
    RemoteSensingPreprocessor,
    compute_phase_correlation,
    align_image_channels,
    perform_co_registration,
    normalize_raster_bands,
    detect_clouds_and_shadows,
)


def _create_synthetic_geotiff(
    path: str,
    width: int = 128,
    height: int = 128,
    bands: int = 3,
    crs: str = "EPSG:32646",
    left: float = 770000.0,
    bottom: float = 2890000.0,
    resolution: float = 10.0,
    base_pattern: np.ndarray = None,
):
    """Create a GeoTIFF tile with recognizable terrain patterns."""
    import rasterio
    from rasterio.transform import from_origin

    transform = from_origin(left, bottom + height * resolution, resolution, resolution)

    if base_pattern is None:
        # Create a textured pattern with high spatial frequency
        x = np.linspace(0, 4 * np.pi, width)
        y = np.linspace(0, 4 * np.pi, height)
        xx, yy = np.meshgrid(x, y)
        pattern = (np.sin(xx) * np.cos(yy) * 100 + 128).astype(np.uint8)
        data = np.stack([pattern, pattern // 2, pattern * 3 // 4], axis=0)
    else:
        data = base_pattern

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=bands,
        dtype=data.dtype,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(data)


# ─── 1. Sub-Pixel Phase Correlation Tests ─────────────────────────────────────


def test_phase_correlation_exact_shift():
    """Verify that FFT phase correlation detects artificial sub-pixel translation."""
    h, w = 128, 128
    # High frequency textured base
    rng = np.random.RandomState(42)
    base = rng.uniform(0.1, 0.9, (h, w)).astype(np.float32)

    # Shift target by (dx=3.0, dy=-2.0)
    import cv2
    dx_true, dy_true = 3.0, -2.0
    M = np.float32([[1, 0, dx_true], [0, 1, dy_true]])
    target = cv2.warpAffine(base, M, (w, h), borderMode=cv2.BORDER_REFLECT_101)

    dx_est, dy_est, response = compute_phase_correlation(base, target)

    assert abs(dx_est - dx_true) < 0.5
    assert abs(dy_est - dy_true) < 0.5
    assert response > 0.4


def test_co_registration_alignment():
    """Verify that perform_co_registration shifts target back to reference."""
    h, w = 100, 100
    rng = np.random.RandomState(123)
    img1 = rng.uniform(0.1, 0.9, (3, h, w)).astype(np.float32)

    # Shift img2
    import cv2
    M = np.float32([[1, 0, 4.0], [0, 1, 2.0]])
    img2 = np.zeros_like(img1)
    for c in range(3):
        img2[c] = cv2.warpAffine(img1[c], M, (w, h), borderMode=cv2.BORDER_REFLECT_101)

    aligned_img2, metrics = perform_co_registration(img1, img2)

    assert metrics.is_aligned is True
    assert metrics.registration_quality in ["EXCELLENT", "GOOD"]
    assert metrics.misregistration_risk_score <= 0.6
    assert abs(metrics.shift_x_pixels - 4.0) < 0.5
    assert abs(metrics.shift_y_pixels - 2.0) < 0.5


# ─── 2. Radiometric Normalization Tests ────────────────────────────────────────


def test_radiometric_normalization():
    """12-bit remote sensing values should be clipped and normalized to [0.0, 1.0]."""
    raw_12bit = np.random.randint(200, 8000, size=(3, 64, 64)).astype(np.float32)
    # Add a specular outlier
    raw_12bit[0, 0, 0] = 65000.0

    normalized, valid_mask = normalize_raster_bands(raw_12bit, 2.0, 98.0)

    assert normalized.dtype == np.float32
    assert normalized.shape == (3, 64, 64)
    assert normalized.min() >= 0.0
    assert normalized.max() <= 1.0
    assert valid_mask.all()


# ─── 3. Cloud and Shadow Heuristics Tests ──────────────────────────────────────


def test_cloud_and_shadow_detection():
    """Verify detection of high-brightness clouds and low-luminance shadows."""
    rgb = np.zeros((3, 50, 50), dtype=np.float32)
    # Cloud region: very bright white (0.95)
    rgb[:, 10:20, 10:20] = 0.95
    # Shadow region: pitch black (0.01)
    rgb[:, 30:40, 30:40] = 0.01

    cloud_mask, shadow_mask = detect_clouds_and_shadows(rgb, brightness_threshold=0.85, shadow_threshold=0.05)

    assert cloud_mask[15, 15] == True
    assert cloud_mask[0, 0] == False
    assert shadow_mask[35, 35] == True
    assert shadow_mask[0, 0] == True  # 0.0 is also dark shadow


# ─── 4. Master Preprocessor Pipeline Tests ────────────────────────────────────


def test_full_preprocessing_pipeline_geotiff(tmp_path):
    """End-to-end processing of dual GeoTIFFs into analysis-ready arrays."""
    t1_path = str(tmp_path / "obs_2020.tif")
    t2_path = str(tmp_path / "obs_2026.tif")

    _create_synthetic_geotiff(t1_path, width=96, height=96)
    _create_synthetic_geotiff(t2_path, width=96, height=96)

    preprocessor = RemoteSensingPreprocessor(enable_coregistration=True)
    pair = preprocessor.process_files(t1_path, t2_path)

    assert pair.image1_array.shape == (3, 96, 96)
    assert pair.image2_array.shape == (3, 96, 96)
    assert pair.image1_array.dtype == np.float32
    assert pair.image2_array.dtype == np.float32
    assert pair.valid_mask.shape == (96, 96)
    assert pair.crs is not None
    assert pair.bounds is not None
    assert pair.registration_metrics.registration_quality in ["EXCELLENT", "GOOD", "FAIR"]


def test_full_preprocessing_pipeline_demo_png(tmp_path):
    """End-to-end fallback processing on non-georeferenced demo PNG images."""
    p1 = str(tmp_path / "demo_t1.png")
    p2 = str(tmp_path / "demo_t2.png")

    img = PILImage.new("RGB", (80, 80), color=(100, 150, 200))
    img.save(p1)
    img.save(p2)

    preprocessor = RemoteSensingPreprocessor(enable_coregistration=True)
    pair = preprocessor.process_files(p1, p2)

    assert pair.image1_array.shape == (3, 80, 80)
    assert pair.image2_array.shape == (3, 80, 80)
    assert pair.valid_mask.shape == (80, 80)
    assert pair.registration_metrics is not None
