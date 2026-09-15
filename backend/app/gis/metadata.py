"""
Geospatial metadata extraction module using Rasterio/GDAL.

STRICT PRINCIPLE:
Never fabricate metadata. If any parameter (sensor, acquisition datetime, CRS, resolution, bounds)
is absent in the raster tags or geospatial headers, return None / null.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from app.core.logging import logger


def parse_acquisition_datetime(tags: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract ISO acquisition datetime, date, and time strings from raster metadata tags.
    Returns (iso_datetime, iso_date, iso_time) or (None, None, None).
    """
    candidates = [
        "DATETIME",
        "TIFFTAG_DATETIME",
        "ACQUISITION_DATE",
        "ACQUISITION_DATETIME",
        "ACQUISITIONTIME",
        "PRODUCT_STOP_TIME",
        "PRODUCT_START_TIME",
        "SENSING_TIME",
        "DATE_ACQUIRED",
        "SCENE_CENTER_TIME",
        "IMAGE_DATE",
        "Date",
        "acquisition_date",
    ]

    raw_val = None
    for key in candidates:
        if key in tags and tags[key]:
            raw_val = str(tags[key]).strip()
            break

    if not raw_val:
        return None, None, None

    # Try common remote sensing date formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%Y%m%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(raw_val, fmt)
            return dt.isoformat(), dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")
        except ValueError:
            continue

    # Return raw string if unparseable but present
    return raw_val, raw_val.split("T")[0] if "T" in raw_val else raw_val.split(" ")[0], None


def parse_satellite_sensor(tags: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract satellite mission and sensor/instrument name from metadata tags.
    Returns (satellite, sensor) or (None, None).
    """
    sat_candidates = ["SPACECRAFT_NAME", "MISSION", "SATELLITE", "PLATFORM", "MISSION_ID", "satellite"]
    sensor_candidates = ["INSTRUMENT_NAME", "SENSOR", "SENSOR_ID", "INSTRUMENT", "sensor"]

    satellite = None
    for k in sat_candidates:
        if k in tags and tags[k]:
            satellite = str(tags[k]).strip()
            break

    sensor = None
    for k in sensor_candidates:
        if k in tags and tags[k]:
            sensor = str(tags[k]).strip()
            break

    return satellite, sensor


def parse_cloud_coverage(tags: Dict[str, Any]) -> Optional[float]:
    """Extract cloud cover percentage (0-100) if documented in tags."""
    cloud_candidates = [
        "CLOUDY_PIXEL_PERCENTAGE",
        "CLOUD_COVER",
        "CLOUD_COVERAGE_PERCENTAGE",
        "CLOUD_COVERAGE",
        "CLOUD_PERCENT",
    ]
    for k in cloud_candidates:
        if k in tags and tags[k] is not None:
            try:
                val = float(tags[k])
                return round(val, 2)
            except (ValueError, TypeError):
                continue
    return None


def extract_geospatial_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract all geospatial metadata from a satellite raster file using rasterio.

    Returns structured dictionary with:
      - satellite (str or None)
      - sensor (str or None)
      - acquisition_datetime (ISO string or None)
      - acquisition_date (YYYY-MM-DD or None)
      - acquisition_time (HH:MM:SS or None)
      - crs (WKT / PROJ string or None)
      - epsg_code (int or None)
      - bounds ([min_x, min_y, max_x, max_y] or None)
      - width (int)
      - height (int)
      - resolution_x (float or None)
      - resolution_y (float or None)
      - band_count (int)
      - nodata_value (float or None)
      - cloud_coverage_percentage (float or None)
      - is_georeferenced (bool)
      - dtype (str)
      - tags (dict)
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext not in [".tif", ".tiff", ".jp2", ".vrt"]:
        # Non-georeferenced demo file fallback
        return _extract_non_georeferenced_metadata(file_path)

    try:
        import rasterio
        with rasterio.open(file_path) as dataset:
            tags = dataset.tags() or {}
            # Also check specific namespaces if available
            try:
                tags.update(dataset.tags(ns="IMAGE_STRUCTURE") or {})
            except Exception:
                pass

            satellite, sensor = parse_satellite_sensor(tags)
            acq_dt, acq_date, acq_time = parse_acquisition_datetime(tags)
            cloud_pct = parse_cloud_coverage(tags)

            # CRS & EPSG
            crs_str = None
            epsg_code = None
            is_georeferenced = False

            if dataset.crs:
                crs_str = str(dataset.crs)
                try:
                    epsg_code = dataset.crs.to_epsg()
                except Exception:
                    epsg_code = None
                is_georeferenced = True

            # Bounds
            bounds_list = None
            if dataset.bounds and is_georeferenced:
                bounds_list = [
                    float(dataset.bounds.left),
                    float(dataset.bounds.bottom),
                    float(dataset.bounds.right),
                    float(dataset.bounds.top),
                ]

            # Resolution
            res_x = None
            res_y = None
            if dataset.res and is_georeferenced:
                res_x = float(abs(dataset.res[0]))
                res_y = float(abs(dataset.res[1]))

            # NoData
            nodata = dataset.nodata
            if nodata is not None:
                try:
                    nodata = float(nodata)
                except (ValueError, TypeError):
                    nodata = None

            return {
                "satellite": satellite,
                "sensor": sensor,
                "acquisition_datetime": acq_dt,
                "acquisition_date": acq_date,
                "acquisition_time": acq_time,
                "crs": crs_str,
                "epsg_code": epsg_code,
                "bounds": bounds_list,
                "bounds_min_x": bounds_list[0] if bounds_list else None,
                "bounds_min_y": bounds_list[1] if bounds_list else None,
                "bounds_max_x": bounds_list[2] if bounds_list else None,
                "bounds_max_y": bounds_list[3] if bounds_list else None,
                "width": int(dataset.width),
                "height": int(dataset.height),
                "resolution_x": res_x,
                "resolution_y": res_y,
                "band_count": int(dataset.count),
                "nodata_value": nodata,
                "cloud_coverage_percentage": cloud_pct,
                "is_georeferenced": is_georeferenced,
                "dtype": str(dataset.dtypes[0]) if dataset.dtypes else "unknown",
                "tags": {k: str(v) for k, v in list(tags.items())[:20]},
            }

    except Exception as exc:
        logger.warning(f"Failed to read raster metadata from {file_path}: {exc}")
        return _extract_non_georeferenced_metadata(file_path)


def _extract_non_georeferenced_metadata(file_path: str) -> Dict[str, Any]:
    """Fallback metadata for standard non-georeferenced images (PNG/JPEG)."""
    try:
        from PIL import Image as PILImage
        with PILImage.open(file_path) as img:
            w, h = img.size
            bands = len(img.getbands())
            return {
                "satellite": None,
                "sensor": None,
                "acquisition_datetime": None,
                "acquisition_date": None,
                "acquisition_time": None,
                "crs": None,
                "epsg_code": None,
                "bounds": None,
                "bounds_min_x": None,
                "bounds_min_y": None,
                "bounds_max_x": None,
                "bounds_max_y": None,
                "width": int(w),
                "height": int(h),
                "resolution_x": None,
                "resolution_y": None,
                "band_count": int(bands),
                "nodata_value": None,
                "cloud_coverage_percentage": None,
                "is_georeferenced": False,
                "dtype": str(img.mode),
                "tags": {},
            }
    except Exception as exc:
        logger.error(f"Failed to extract basic image dimensions: {exc}")
        return {
            "satellite": None,
            "sensor": None,
            "acquisition_datetime": None,
            "acquisition_date": None,
            "acquisition_time": None,
            "crs": None,
            "epsg_code": None,
            "bounds": None,
            "bounds_min_x": None,
            "bounds_min_y": None,
            "bounds_max_x": None,
            "bounds_max_y": None,
            "width": 0,
            "height": 0,
            "resolution_x": None,
            "resolution_y": None,
            "band_count": 0,
            "nodata_value": None,
            "cloud_coverage_percentage": None,
            "is_georeferenced": False,
            "dtype": "unknown",
            "tags": {},
        }
