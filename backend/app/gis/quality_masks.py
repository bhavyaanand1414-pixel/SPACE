"""
Quality Mask Parsing (PS 26227 §2.2.3).

Parses Sentinel-2 Scene Classification Layer (SCL) and Landsat QA_PIXEL
bit-mask bands to identify cloud, shadow, snow, haze, and water pixels.
Used to suppress false-alarm change detections caused by atmospheric
and seasonal confounding factors.
"""

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np

from app.core.logging import logger


# --- Sentinel-2 SCL class definitions ---
# See: https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm
SCL_LABELS = {
    0: "no_data",
    1: "saturated_defective",
    2: "topographic_shadow",     # Not a false alarm source, but dark
    3: "cloud_shadow",
    4: "vegetation",
    5: "not_vegetated",          # Bare soil, rock, etc.
    6: "water",
    7: "unclassified",
    8: "cloud_medium_prob",
    9: "cloud_high_prob",
    10: "thin_cirrus",
    11: "snow_ice",
}

# Pixels to mask as "bad quality" — these should NOT be reported as change
SCL_BAD_CLASSES = {0, 1, 3, 8, 9, 10, 11}

# --- Landsat QA_PIXEL bit positions ---
# See: https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands
LANDSAT_QA_BITS = {
    "fill":          0,
    "dilated_cloud": 1,
    "cirrus":        2,
    "cloud":         3,
    "cloud_shadow":  4,
    "snow":          5,
    "clear":         6,
    "water":         7,
}


@dataclass
class QualityMask:
    """
    Per-pixel quality classification for a satellite image tile.

    Attributes
    ----------
    clear : np.ndarray (bool)
        True where pixel is usable (not cloud/shadow/snow/haze).
    cloud : np.ndarray (bool)
    cloud_shadow : np.ndarray (bool)
    snow_ice : np.ndarray (bool)
    water : np.ndarray (bool)
    haze : np.ndarray (bool)
    clear_fraction : float
        Fraction of pixels that are clear (0.0 – 1.0).
    """
    clear: np.ndarray
    cloud: np.ndarray
    cloud_shadow: np.ndarray
    snow_ice: np.ndarray
    water: np.ndarray
    haze: np.ndarray
    clear_fraction: float


def parse_sentinel2_scl(scl_band: np.ndarray) -> QualityMask:
    """
    Parse a Sentinel-2 Scene Classification Layer (SCL) band into a QualityMask.

    Parameters
    ----------
    scl_band : np.ndarray (H, W) — uint8 or int
        The SCL band from a Sentinel-2 L2A product.

    Returns
    -------
    QualityMask with per-pixel classification.
    """
    cloud = np.isin(scl_band, [8, 9])
    cloud_shadow = (scl_band == 3)
    snow_ice = (scl_band == 11)
    water = (scl_band == 6)
    haze = (scl_band == 10)  # thin cirrus as haze proxy

    # Clear = not any of the above bad classes
    bad = np.isin(scl_band, list(SCL_BAD_CLASSES))
    clear = ~bad

    clear_fraction = float(clear.sum() / clear.size) if clear.size > 0 else 0.0

    logger.debug(
        f"SCL quality mask: clear={clear_fraction:.1%}, "
        f"cloud={cloud.sum()}, shadow={cloud_shadow.sum()}, "
        f"snow={snow_ice.sum()}, haze={haze.sum()}"
    )

    return QualityMask(
        clear=clear,
        cloud=cloud,
        cloud_shadow=cloud_shadow,
        snow_ice=snow_ice,
        water=water,
        haze=haze,
        clear_fraction=clear_fraction,
    )


def parse_landsat_qa(qa_band: np.ndarray) -> QualityMask:
    """
    Parse a Landsat Collection 2 QA_PIXEL band into a QualityMask.

    Parameters
    ----------
    qa_band : np.ndarray (H, W) — uint16
        The QA_PIXEL band from a Landsat Collection 2 product.

    Returns
    -------
    QualityMask with per-pixel classification.
    """
    def _bit_set(arr: np.ndarray, bit: int) -> np.ndarray:
        return ((arr >> bit) & 1).astype(bool)

    cloud = _bit_set(qa_band, LANDSAT_QA_BITS["cloud"]) | _bit_set(qa_band, LANDSAT_QA_BITS["dilated_cloud"])
    cloud_shadow = _bit_set(qa_band, LANDSAT_QA_BITS["cloud_shadow"])
    snow_ice = _bit_set(qa_band, LANDSAT_QA_BITS["snow"])
    water = _bit_set(qa_band, LANDSAT_QA_BITS["water"])
    haze = _bit_set(qa_band, LANDSAT_QA_BITS["cirrus"])
    fill = _bit_set(qa_band, LANDSAT_QA_BITS["fill"])

    clear = ~(cloud | cloud_shadow | snow_ice | haze | fill)
    clear_fraction = float(clear.sum() / clear.size) if clear.size > 0 else 0.0

    logger.debug(
        f"Landsat QA mask: clear={clear_fraction:.1%}, "
        f"cloud={cloud.sum()}, shadow={cloud_shadow.sum()}, "
        f"snow={snow_ice.sum()}, haze={haze.sum()}"
    )

    return QualityMask(
        clear=clear,
        cloud=cloud,
        cloud_shadow=cloud_shadow,
        snow_ice=snow_ice,
        water=water,
        haze=haze,
        clear_fraction=clear_fraction,
    )


def apply_quality_mask(
    change_mask: np.ndarray,
    quality_mask: QualityMask,
) -> np.ndarray:
    """
    Suppress change detections in pixels affected by cloud, shadow, snow, or haze.

    This is the key PS 26227 §2.2.3 requirement: confounding factors must NOT
    be reported as change.  By masking these pixels, we favour precision over
    indiscriminate recall.

    Parameters
    ----------
    change_mask : np.ndarray (H, W) — bool or uint8
        Binary change mask from the change detector.
    quality_mask : QualityMask
        Quality classification from SCL or QA band parsing.

    Returns
    -------
    np.ndarray (H, W) — filtered change mask with false alarms suppressed.
    """
    filtered = change_mask.copy().astype(bool)
    # Zero out change detections in bad-quality pixels
    filtered &= quality_mask.clear

    original_count = int(change_mask.astype(bool).sum())
    filtered_count = int(filtered.sum())
    suppressed = original_count - filtered_count

    if suppressed > 0:
        logger.info(
            f"Quality mask suppressed {suppressed} false-alarm pixels "
            f"({original_count} → {filtered_count})"
        )

    return filtered.astype(np.uint8)


def compute_seasonal_baseline(
    ndvi_values: np.ndarray,
    dates: np.ndarray,
    target_doy: int,
    window_days: int = 30,
) -> float:
    """
    Compute historical seasonal baseline NDVI for a given day-of-year.

    Used to subtract seasonal vegetation signal from change detection,
    preventing seasonal variation from being reported as change
    (PS 26227 §2.2.3).

    Parameters
    ----------
    ndvi_values : np.ndarray
        Historical NDVI values for this location.
    dates : np.ndarray
        Corresponding dates (as day-of-year integers).
    target_doy : int
        Day-of-year to compute baseline for (1–365).
    window_days : int
        Half-window size for smoothing.

    Returns
    -------
    float — baseline NDVI value for this time of year.
    """
    # Circular distance for day-of-year
    doy_diff = np.abs(dates - target_doy)
    doy_diff = np.minimum(doy_diff, 365 - doy_diff)
    within_window = doy_diff <= window_days

    if within_window.sum() == 0:
        return float(np.nanmean(ndvi_values))

    return float(np.nanmean(ndvi_values[within_window]))
