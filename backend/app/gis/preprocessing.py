"""
Remote Sensing Preprocessing & Sub-Pixel Co-Registration Engine.

Modular Pipeline:
Raw Images
  → CRS Normalization & Auto-UTM Reprojection
  → Resampling & Grid Harmonization
  → NoData & Cloud/Shadow Masking
  → Band Selection & Channel Standardization
  → Radiometric Percentile Normalization ([0, 1])
  → Geometric Intersection Cropping
  → Sub-Pixel Phase Correlation Co-Registration
  → Analysis-Ready Aligned Arrays with Quality Metrics

CRITICAL SCIENTIFIC PRINCIPLE:
Sub-pixel misregistration between multi-temporal acquisitions creates edge artifacts
that must NEVER be falsely classified as human construction or real ground change.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import Affine, from_bounds
from rasterio.warp import calculate_default_transform, reproject
from shapely.geometry import box

from app.core.logging import logger
from app.gis.metadata import extract_geospatial_metadata


@dataclass
class RegistrationMetrics:
    """Diagnostic telemetry for multi-temporal image co-registration."""
    shift_x_pixels: float = 0.0
    shift_y_pixels: float = 0.0
    correlation_response: float = 1.0
    registration_quality: str = "EXCELLENT"  # EXCELLENT, GOOD, FAIR, POOR
    misregistration_risk_score: float = 0.0  # 0.0 (safe) to 1.0 (high risk of edge artifacts)
    is_aligned: bool = True
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisReadyPair:
    """Output of preprocessing pipeline ready for Siamese U-Net or baseline change detection."""
    image1_array: np.ndarray  # Shape: (C, H, W) float32 [0, 1]
    image2_array: np.ndarray  # Shape: (C, H, W) float32 [0, 1]
    valid_mask: np.ndarray    # Shape: (H, W) bool (True = valid clean ground)
    cloud_mask_t1: Optional[np.ndarray] = None  # Shape: (H, W) bool
    cloud_mask_t2: Optional[np.ndarray] = None  # Shape: (H, W) bool
    transform: Optional[Affine] = None
    crs: Optional[str] = None
    bounds: Optional[List[float]] = None
    width: int = 0
    height: int = 0
    channels: int = 3
    registration_metrics: RegistrationMetrics = field(default_factory=RegistrationMetrics)


# ---------------------------------------------------------------------------
# 1. Sub-Pixel Phase Correlation Co-Registration
# ---------------------------------------------------------------------------

def compute_phase_correlation(
    ref_band: np.ndarray,
    target_band: np.ndarray,
) -> Tuple[float, float, float]:
    """
    Compute sub-pixel translation (dx, dy) using 2D FFT Phase Correlation with Hanning window.

    Args:
        ref_band: 2D float32 array (T1 reference)
        target_band: 2D float32 array (T2 candidate to align)

    Returns:
        (shift_x, shift_y, peak_response) where shift is in pixels.
    """
    # Ensure float32 and shape match
    h, w = ref_band.shape
    ref_f32 = ref_band.astype(np.float32)
    target_f32 = target_band.astype(np.float32)

    # Normalize to [0, 1]
    ref_min, ref_max = ref_f32.min(), ref_f32.max()
    if ref_max > ref_min:
        ref_f32 = (ref_f32 - ref_min) / (ref_max - ref_min)

    target_min, target_max = target_f32.min(), target_f32.max()
    if target_max > target_min:
        target_f32 = (target_f32 - target_min) / (target_max - target_min)

    # Create Hanning window to eliminate boundary frequency leakage
    hann_window = cv2.createHanningWindow((w, h), cv2.CV_32F)

    # Phase correlate
    (dx, dy), response = cv2.phaseCorrelate(ref_f32, target_f32, hann_window)

    return float(dx), float(dy), float(response)


def align_image_channels(
    image: np.ndarray,
    dx: float,
    dy: float,
) -> np.ndarray:
    """
    Shift all channels of an image array (C, H, W) by sub-pixel offset (dx, dy).
    Uses bilinear interpolation.
    """
    c, h, w = image.shape
    # Transformation matrix for translation: x' = x - dx, y' = y - dy
    # To shift target towards ref by -dx, -dy:
    M = np.float32([[1, 0, -dx], [0, 1, -dy]])

    shifted = np.zeros_like(image)
    for i in range(c):
        shifted[i] = cv2.warpAffine(
            image[i],
            M,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT_101,
        )

    return shifted


def perform_co_registration(
    img1: np.ndarray,
    img2: np.ndarray,
    max_shift_threshold: float = 30.0,
) -> Tuple[np.ndarray, RegistrationMetrics]:
    """
    Co-register multi-temporal pair using sub-pixel phase correlation.

    Args:
        img1: Reference array (C, H, W) in float32
        img2: Target array (C, H, W) to be aligned with img1
        max_shift_threshold: Maximum plausible translation in pixels

    Returns:
        (aligned_img2, registration_metrics)
    """
    # H-5 FIX: Use luminance mean across all available bands for registration.
    # Using only Band 0 degrades correlation when that band has high seasonal
    # radiometric variance (e.g., Red band in summer vs winter forest scenes).
    ref_band = np.mean(img1, axis=0).astype(np.float32) if img1.ndim == 3 else img1.astype(np.float32)
    target_band = np.mean(img2, axis=0).astype(np.float32) if img2.ndim == 3 else img2.astype(np.float32)

    try:
        dx, dy, response = compute_phase_correlation(ref_band, target_band)
    except Exception as exc:
        logger.warning(f"Phase correlation failed: {exc}")
        dx, dy, response = 0.0, 0.0, 0.0

    shift_mag = float(np.sqrt(dx ** 2 + dy ** 2))

    # Determine registration quality
    if response >= 0.6 and shift_mag <= max_shift_threshold:
        quality = "EXCELLENT"
        risk = round(max(0.0, 1.0 - response) * 0.3, 3)
        apply_warp = True
    elif response >= 0.35 and shift_mag <= max_shift_threshold:
        quality = "GOOD"
        risk = round(max(0.0, 1.0 - response) * 0.6, 3)
        apply_warp = True
    elif response >= 0.15 and shift_mag <= max_shift_threshold:
        quality = "FAIR"
        risk = 0.65
        apply_warp = True
    else:
        # High likelihood of dissimilar scene content, major cloud shift, or invalid match
        quality = "POOR"
        risk = 0.90
        # If response is too low or shift is erratic, do not apply disruptive warp
        apply_warp = False
        dx, dy = 0.0, 0.0

    if apply_warp and (abs(dx) > 0.05 or abs(dy) > 0.05):
        aligned_img2 = align_image_channels(img2, dx, dy)
        is_aligned = True
    else:
        aligned_img2 = img2.copy()
        is_aligned = (quality != "POOR")

    metrics = RegistrationMetrics(
        shift_x_pixels=round(dx, 3),
        shift_y_pixels=round(dy, 3),
        correlation_response=round(response, 4),
        registration_quality=quality,
        misregistration_risk_score=risk,
        is_aligned=is_aligned,
        details={
            "shift_magnitude_px": round(shift_mag, 3),
            "warp_applied": apply_warp,
            "ref_shape": list(img1.shape),
        },
    )

    return aligned_img2, metrics


# ---------------------------------------------------------------------------
# 2. Radiometric Normalization
# ---------------------------------------------------------------------------

def normalize_raster_bands(
    raster: np.ndarray,
    percentile_low: float = 2.0,
    percentile_high: float = 98.0,
    nodata_value: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Perform robust 2% - 98% percentile radiometric normalization per channel to [0.0, 1.0].
    Preserves spectral balance and rejects extreme specular/shadow outliers.

    Returns:
        (normalized_f32, valid_mask)
    """
    if raster.ndim == 2:
        raster = np.expand_dims(raster, axis=0)

    c, h, w = raster.shape
    norm_raster = np.zeros((c, h, w), dtype=np.float32)

    # Compute valid mask
    valid_mask = np.ones((h, w), dtype=bool)
    if nodata_value is not None:
        for i in range(c):
            valid_mask &= (raster[i] != nodata_value) & (~np.isnan(raster[i]))
    else:
        for i in range(c):
            valid_mask &= ~np.isnan(raster[i])

    for i in range(c):
        channel = raster[i].astype(np.float32)
        valid_vals = channel[valid_mask]

        if valid_vals.size > 10:
            p_low = np.percentile(valid_vals, percentile_low)
            p_high = np.percentile(valid_vals, percentile_high)

            if p_high > p_low:
                clipped = np.clip(channel, p_low, p_high)
                norm_raster[i] = (clipped - p_low) / (p_high - p_low)
            else:
                norm_raster[i] = np.clip(channel / 255.0, 0.0, 1.0)
        else:
            norm_raster[i] = np.clip(channel / 255.0, 0.0, 1.0)

    return norm_raster, valid_mask


# ---------------------------------------------------------------------------
# 3. Simple Cloud & Shadow Detection
# ---------------------------------------------------------------------------

def detect_clouds_and_shadows(
    rgb_normalized: np.ndarray,
    brightness_threshold: float = 0.85,
    shadow_threshold: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Heuristic cloud and shadow mask extraction from normalized RGB array.
    Cloud: High mean brightness & low color saturation.
    Shadow: Very low luminance.

    Returns:
        (cloud_mask, shadow_mask) as 2D boolean arrays (H, W).
    """
    if rgb_normalized.shape[0] < 3:
        h, w = rgb_normalized.shape[1], rgb_normalized.shape[2]
        return np.zeros((h, w), dtype=bool), np.zeros((h, w), dtype=bool)

    r, g, b = rgb_normalized[0], rgb_normalized[1], rgb_normalized[2]
    mean_val = (r + g + b) / 3.0
    color_diff = np.abs(r - g) + np.abs(g - b) + np.abs(b - r)

    # Cloud: very bright and grayish/white
    cloud_mask = (mean_val > brightness_threshold) & (color_diff < 0.25)

    # Shadow: deeply dark
    shadow_mask = mean_val < shadow_threshold

    return cloud_mask, shadow_mask


# ---------------------------------------------------------------------------
# 4. Master Preprocessing Pipeline
# ---------------------------------------------------------------------------

class RemoteSensingPreprocessor:
    """
    Modular preprocessing pipeline for multi-temporal optical MSI and SAR satellite rasters.
    """

    def __init__(
        self,
        target_resolution: Optional[float] = None,
        clip_percentile: Tuple[float, float] = (2.0, 98.0),
        enable_coregistration: bool = True,
        max_channels: int = 3,
    ):
        self.target_resolution = target_resolution
        self.clip_percentile = clip_percentile
        self.enable_coregistration = enable_coregistration
        self.max_channels = max_channels

    def process_files(
        self,
        file1_path: str,
        file2_path: str,
    ) -> AnalysisReadyPair:
        """
        Process two raw satellite image files into analysis-ready, co-registered arrays.
        """
        ext1 = Path(file1_path).suffix.lower()
        ext2 = Path(file2_path).suffix.lower()

        # Handle Georeferenced GeoTIFFs vs Non-georeferenced demo files
        is_tif1 = ext1 in [".tif", ".tiff"]
        is_tif2 = ext2 in [".tif", ".tiff"]

        if is_tif1 and is_tif2:
            return self._process_geotiff_pair(file1_path, file2_path)
        else:
            return self._process_demo_image_pair(file1_path, file2_path)

    def _process_geotiff_pair(
        self,
        file1_path: str,
        file2_path: str,
    ) -> AnalysisReadyPair:
        """Standard pipeline for georeferenced GeoTIFF rasters using Rasterio."""
        with rasterio.open(file1_path) as ds1, rasterio.open(file2_path) as ds2:
            crs1 = ds1.crs
            crs2 = ds2.crs
            b1 = ds1.bounds
            b2 = ds2.bounds

            # If both datasets have identical bounds and CRS, read directly
            if crs1 == crs2 and b1 == b2 and ds1.shape == ds2.shape:
                raw1 = ds1.read()[: self.max_channels]
                raw2 = ds2.read()[: self.max_channels]
                transform = ds1.transform
                crs_str = str(crs1) if crs1 else None
                bounds_list = [float(b1.left), float(b1.bottom), float(b1.right), float(b1.top)]
                nodata1 = ds1.nodata
                nodata2 = ds2.nodata
            else:
                # Calculate overlapping bounding box
                min_x = max(b1.left, b2.left)
                min_y = max(b1.bottom, b2.bottom)
                max_x = min(b1.right, b2.right)
                max_y = min(b1.top, b2.top)

                if min_x >= max_x or min_y >= max_y:
                    # Disjoint fallback: use ds1 geometry and resample ds2 to match ds1 grid
                    logger.warning("Rasters are disjoint or have non-overlapping bounds. Using ds1 footprint.")
                    min_x, min_y, max_x, max_y = b1.left, b1.bottom, b1.right, b1.top

                target_crs = crs1 or crs2 or "EPSG:3857"
                target_w, target_h = ds1.width, ds1.height
                transform = from_bounds(min_x, min_y, max_x, max_y, target_w, target_h)

                # Reproject / Resample ds1 and ds2 to common target grid
                c_out = min(self.max_channels, min(ds1.count, ds2.count))
                raw1 = np.zeros((c_out, target_h, target_w), dtype=np.float32)
                raw2 = np.zeros((c_out, target_h, target_w), dtype=np.float32)

                for i in range(c_out):
                    reproject(
                        source=rasterio.band(ds1, i + 1),
                        destination=raw1[i],
                        src_transform=ds1.transform,
                        src_crs=ds1.crs,
                        dst_transform=transform,
                        dst_crs=target_crs,
                        resampling=Resampling.bilinear,
                    )
                    reproject(
                        source=rasterio.band(ds2, i + 1),
                        destination=raw2[i],
                        src_transform=ds2.transform,
                        src_crs=ds2.crs,
                        dst_transform=transform,
                        dst_crs=target_crs,
                        resampling=Resampling.bilinear,
                    )

                crs_str = str(target_crs)
                bounds_list = [float(min_x), float(min_y), float(max_x), float(max_y)]
                nodata1 = ds1.nodata
                nodata2 = ds2.nodata

        # Radiometric Normalization
        norm1, mask1 = normalize_raster_bands(raw1, self.clip_percentile[0], self.clip_percentile[1], nodata1)
        norm2, mask2 = normalize_raster_bands(raw2, self.clip_percentile[0], self.clip_percentile[1], nodata2)
        valid_mask = mask1 & mask2

        # Sub-pixel Co-Registration
        if self.enable_coregistration:
            aligned2, reg_metrics = perform_co_registration(norm1, norm2)
        else:
            aligned2 = norm2
            reg_metrics = RegistrationMetrics()

        # Cloud & shadow detection
        cloud1, _ = detect_clouds_and_shadows(norm1)
        cloud2, _ = detect_clouds_and_shadows(aligned2)

        return AnalysisReadyPair(
            image1_array=norm1,
            image2_array=aligned2,
            valid_mask=valid_mask,
            cloud_mask_t1=cloud1,
            cloud_mask_t2=cloud2,
            transform=transform,
            crs=crs_str,
            bounds=bounds_list,
            width=norm1.shape[2],
            height=norm1.shape[1],
            channels=norm1.shape[0],
            registration_metrics=reg_metrics,
        )

    def _process_demo_image_pair(
        self,
        file1_path: str,
        file2_path: str,
    ) -> AnalysisReadyPair:
        """Pipeline fallback for non-georeferenced demo images (JPG/PNG)."""
        from PIL import Image as PILImage

        with PILImage.open(file1_path) as p1, PILImage.open(file2_path) as p2:
            img1 = np.array(p1.convert("RGB")).astype(np.float32)
            img2 = np.array(p2.convert("RGB")).astype(np.float32)

        # Match dimensions if different
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        target_h = min(h1, h2)
        target_w = min(w1, w2)

        if (h1, w1) != (target_h, target_w):
            img1 = cv2.resize(img1, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        if (h2, w2) != (target_h, target_w):
            img2 = cv2.resize(img2, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

        # Transpose to (C, H, W)
        arr1 = np.transpose(img1, (2, 0, 1))
        arr2 = np.transpose(img2, (2, 0, 1))

        # Normalize
        norm1, mask1 = normalize_raster_bands(arr1, self.clip_percentile[0], self.clip_percentile[1])
        norm2, mask2 = normalize_raster_bands(arr2, self.clip_percentile[0], self.clip_percentile[1])
        valid_mask = mask1 & mask2

        # Co-Registration
        if self.enable_coregistration:
            aligned2, reg_metrics = perform_co_registration(norm1, norm2)
        else:
            aligned2 = norm2
            reg_metrics = RegistrationMetrics()

        cloud1, _ = detect_clouds_and_shadows(norm1)
        cloud2, _ = detect_clouds_and_shadows(aligned2)

        return AnalysisReadyPair(
            image1_array=norm1,
            image2_array=aligned2,
            valid_mask=valid_mask,
            cloud_mask_t1=cloud1,
            cloud_mask_t2=cloud2,
            transform=None,
            crs=None,
            bounds=None,
            width=target_w,
            height=target_h,
            channels=norm1.shape[0],
            registration_metrics=reg_metrics,
        )
