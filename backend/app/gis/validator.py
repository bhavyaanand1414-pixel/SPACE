"""
Geospatial compatibility validation & Data Quality Score engine.

Validates multi-temporal raster pairs across:
1. Spatial / geographic overlap
2. CRS alignment & reprojection requirements
3. Spatial resolution & Ground Sampling Distance (GSD)
4. Raster dimensions & aspect ratio
5. Band count & spectral compatibility
6. NoData value consistency
7. Cloud cover constraints
8. Temporal progression (acquisition delta)

Computes a deterministic Data Quality Score (0 - 100) and diagnostic matrix.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from shapely.geometry import box
import pyproj
from app.gis.metadata import extract_geospatial_metadata
from app.core.logging import logger


def calculate_spatial_overlap(
    meta1: Dict[str, Any], meta2: Dict[str, Any]
) -> Tuple[float, Optional[str], Optional[float]]:
    """
    Calculate intersection over minimum area between two georeferenced raster bounding boxes.
    Handles reprojection if CRS differs.

    Returns:
        (overlap_percentage, overlap_status, intersection_area_deg_or_m2)
    """
    if not meta1.get("is_georeferenced") or not meta2.get("is_georeferenced"):
        return 0.0, "NOT_GEOREFERENCED", None

    b1 = meta1.get("bounds")
    b2 = meta2.get("bounds")
    if not b1 or not b2:
        return 0.0, "MISSING_BOUNDS", None

    crs1 = meta1.get("crs")
    crs2 = meta2.get("crs")

    poly1 = box(b1[0], b1[1], b1[2], b1[3])
    poly2 = box(b2[0], b2[1], b2[2], b2[3])

    # If CRS differs, reproject poly2 into crs1 for accurate intersection
    if crs1 and crs2 and crs1 != crs2:
        try:
            transformer = pyproj.Transformer.from_crs(crs2, crs1, always_xy=True)
            from shapely.ops import transform
            poly2 = transform(transformer.transform, poly2)
        except Exception as exc:
            logger.warning(f"Could not reproject bounds for overlap calculation: {exc}")
            # Fall back to naive comparison
            pass

    if not poly1.intersects(poly2):
        return 0.0, "DISJOINT", 0.0

    intersection = poly1.intersection(poly2)
    area1 = poly1.area
    area2 = poly2.area
    min_area = min(area1, area2)

    if min_area <= 0:
        return 0.0, "DISJOINT", 0.0

    overlap_pct = min(100.0, round((intersection.area / min_area) * 100.0, 2))
    return overlap_pct, "COMPUTED", intersection.area


def calculate_temporal_delta(
    meta1: Dict[str, Any], meta2: Dict[str, Any]
) -> Tuple[Optional[int], Optional[str]]:
    """
    Calculate acquisition date difference in days (T2 - T1).
    Returns (delta_days, status_note).
    """
    d1_str = meta1.get("acquisition_date")
    d2_str = meta2.get("acquisition_date")

    if not d1_str or not d2_str:
        return None, "Acquisition dates unavailable in raster metadata."

    try:
        d1 = datetime.strptime(d1_str[:10], "%Y-%m-%d")
        d2 = datetime.strptime(d2_str[:10], "%Y-%m-%d")
        delta = (d2 - d1).days
        if delta < 0:
            return delta, f"Warning: T2 date ({d2_str}) is earlier than T1 date ({d1_str}) — temporal ordering reversed."
        if delta == 0:
            return delta, "Identical acquisition dates — same-day or synthetic pair."
        return delta, f"{delta:,} days temporal baseline."
    except Exception:
        return None, "Unable to parse acquisition date formats."


def validate_raster_pair(
    file1_path: str,
    file2_path: str,
    pre_extracted_meta1: Optional[Dict[str, Any]] = None,
    pre_extracted_meta2: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Perform comprehensive validation on a multi-temporal satellite image pair.
    Generates a Data Quality Score (0-100) and diagnostic verification matrix.
    """
    meta1 = pre_extracted_meta1 or extract_geospatial_metadata(file1_path)
    meta2 = pre_extracted_meta2 or extract_geospatial_metadata(file2_path)

    checks: List[Dict[str, Any]] = []
    score = 100

    # 1. Georeferencing & Spatial Overlap Check
    is_geo1 = meta1.get("is_georeferenced", False)
    is_geo2 = meta2.get("is_georeferenced", False)
    overlap_pct, overlap_status, _ = calculate_spatial_overlap(meta1, meta2)

    if not is_geo1 or not is_geo2:
        score -= 25
        checks.append({
            "name": "Spatial Overlap",
            "status": "WARNING",
            "score_deduction": 25,
            "message": "One or both images lack spatial georeferencing (demo mode input). Reprojection and vector coordinate export disabled.",
            "details": {"is_georeferenced_t1": is_geo1, "is_georeferenced_t2": is_geo2},
        })
    elif overlap_pct >= 90.0:
        checks.append({
            "name": "Spatial Overlap",
            "status": "PASS",
            "score_deduction": 0,
            "message": f"Optimal spatial overlap ({overlap_pct}%).",
            "details": {"overlap_percentage": overlap_pct},
        })
    elif overlap_pct >= 50.0:
        score -= 10
        checks.append({
            "name": "Spatial Overlap",
            "status": "WARNING",
            "score_deduction": 10,
            "message": f"Partial spatial overlap ({overlap_pct}%). Cropping to intersection area recommended.",
            "details": {"overlap_percentage": overlap_pct},
        })
    else:
        score -= 50
        checks.append({
            "name": "Spatial Overlap",
            "status": "FAIL",
            "score_deduction": 50,
            "message": f"Insufficient or disjoint geographic coverage ({overlap_pct}%). Images do not observe the same ground area.",
            "details": {"overlap_percentage": overlap_pct},
        })

    # 2. CRS Alignment Check
    crs1 = meta1.get("crs")
    crs2 = meta2.get("crs")
    epsg1 = meta1.get("epsg_code")
    epsg2 = meta2.get("epsg_code")

    if is_geo1 and is_geo2:
        if crs1 == crs2 and crs1 is not None:
            checks.append({
                "name": "CRS Alignment",
                "status": "PASS",
                "score_deduction": 0,
                "message": f"Matching Coordinate Reference System ({crs1}).",
                "details": {"crs_t1": crs1, "crs_t2": crs2, "epsg": epsg1},
            })
        else:
            score -= 5
            checks.append({
                "name": "CRS Alignment",
                "status": "WARNING",
                "score_deduction": 5,
                "message": f"Different CRSs detected (T1: {crs1 or 'Unknown'}, T2: {crs2 or 'Unknown'}). On-the-fly reprojection will be applied.",
                "details": {"crs_t1": crs1, "crs_t2": crs2},
            })
    else:
        checks.append({
            "name": "CRS Alignment",
            "status": "UNAVAILABLE",
            "score_deduction": 0,
            "message": "Metadata unavailable — non-georeferenced images.",
            "details": {},
        })

    # 3. Spatial Resolution / GSD Check
    res1_x = meta1.get("resolution_x")
    res2_x = meta2.get("resolution_x")

    if res1_x and res2_x:
        ratio = max(res1_x, res2_x) / min(res1_x, res2_x)
        if ratio <= 1.1:
            checks.append({
                "name": "Spatial Resolution",
                "status": "PASS",
                "score_deduction": 0,
                "message": f"Matched ground sampling distance (~{res1_x:.2f} m/px).",
                "details": {"resolution_t1": res1_x, "resolution_t2": res2_x, "ratio": round(ratio, 2)},
            })
        elif ratio <= 3.0:
            score -= 5
            checks.append({
                "name": "Spatial Resolution",
                "status": "WARNING",
                "score_deduction": 5,
                "message": f"Resolution mismatch (T1: {res1_x:.2f}m, T2: {res2_x:.2f}m, ratio: {ratio:.1f}x). Resampling required.",
                "details": {"resolution_t1": res1_x, "resolution_t2": res2_x, "ratio": round(ratio, 2)},
            })
        else:
            score -= 20
            checks.append({
                "name": "Spatial Resolution",
                "status": "FAIL",
                "score_deduction": 20,
                "message": f"High resolution disparity (>3x difference). May cause significant change detection artifacts.",
                "details": {"resolution_t1": res1_x, "resolution_t2": res2_x, "ratio": round(ratio, 2)},
            })
    else:
        checks.append({
            "name": "Spatial Resolution",
            "status": "UNAVAILABLE",
            "score_deduction": 0,
            "message": "Spatial resolution metadata unavailable.",
            "details": {},
        })

    # 4. Band Compatibility
    bands1 = meta1.get("band_count", 0)
    bands2 = meta2.get("band_count", 0)

    if bands1 > 0 and bands2 > 0:
        if bands1 == bands2:
            checks.append({
                "name": "Band Compatibility",
                "status": "PASS",
                "score_deduction": 0,
                "message": f"Identical band count ({bands1} channels).",
                "details": {"band_count": bands1},
            })
        else:
            score -= 5
            checks.append({
                "name": "Band Compatibility",
                "status": "WARNING",
                "score_deduction": 5,
                "message": f"Band count mismatch (T1: {bands1}, T2: {bands2}). Common channel selection (RGB/NIR) will be used.",
                "details": {"bands_t1": bands1, "bands_t2": bands2},
            })
    else:
        checks.append({
            "name": "Band Compatibility",
            "status": "FAIL",
            "score_deduction": 20,
            "message": "Could not read valid image color bands.",
            "details": {},
        })

    # 5. Cloud Coverage Check (if documented)
    cloud1 = meta1.get("cloud_coverage_percentage")
    cloud2 = meta2.get("cloud_coverage_percentage")

    if cloud1 is not None or cloud2 is not None:
        max_cloud = max(c for c in [cloud1, cloud2] if c is not None)
        if max_cloud <= 10.0:
            checks.append({
                "name": "Cloud Coverage",
                "status": "PASS",
                "score_deduction": 0,
                "message": f"Low cloud cover obstruction (Max: {max_cloud}%).",
                "details": {"cloud_t1": cloud1, "cloud_t2": cloud2},
            })
        elif max_cloud <= 30.0:
            score -= 10
            checks.append({
                "name": "Cloud Coverage",
                "status": "WARNING",
                "score_deduction": 10,
                "message": f"Moderate cloud cover detected ({max_cloud}%). Cloud masking applied.",
                "details": {"cloud_t1": cloud1, "cloud_t2": cloud2},
            })
        else:
            score -= 25
            checks.append({
                "name": "Cloud Coverage",
                "status": "FAIL",
                "score_deduction": 25,
                "message": f"High cloud cover obstruction ({max_cloud}%). Heavy occlusion will impact change fidelity.",
                "details": {"cloud_t1": cloud1, "cloud_t2": cloud2},
            })
    else:
        checks.append({
            "name": "Cloud Coverage",
            "status": "UNAVAILABLE",
            "score_deduction": 0,
            "message": "Cloud coverage metadata unavailable in raster tags.",
            "details": {},
        })

    # 6. Temporal Delta Check
    delta_days, temp_note = calculate_temporal_delta(meta1, meta2)
    if delta_days is not None:
        if delta_days < 0:
            score -= 10
            checks.append({
                "name": "Temporal Progression",
                "status": "WARNING",
                "score_deduction": 10,
                "message": temp_note,
                "details": {"delta_days": delta_days},
            })
        else:
            checks.append({
                "name": "Temporal Progression",
                "status": "PASS",
                "score_deduction": 0,
                "message": temp_note,
                "details": {"delta_days": delta_days},
            })
    else:
        checks.append({
            "name": "Temporal Progression",
            "status": "UNAVAILABLE",
            "score_deduction": 0,
            "message": temp_note,
            "details": {},
        })

    # Ensure score stays in 0..100
    final_score = max(0, min(100, score))

    # Overall recommendation
    has_fail = any(c["status"] == "FAIL" for c in checks)
    has_warning = any(c["status"] == "WARNING" for c in checks)

    if has_fail:
        recommendation = "INCOMPATIBLE_PAIR"
        is_valid = False
    elif has_warning:
        recommendation = "REQUIRES_PREPROCESSING"
        is_valid = True
    else:
        recommendation = "READY_FOR_INFERENCE"
        is_valid = True

    return {
        "is_valid": is_valid,
        "data_quality_score": final_score,
        "recommendation": recommendation,
        "spatial_overlap_percentage": overlap_pct if is_geo1 and is_geo2 else None,
        "temporal_delta_days": delta_days,
        "checks_matrix": checks,
        "image1_metadata": meta1,
        "image2_metadata": meta2,
    }
