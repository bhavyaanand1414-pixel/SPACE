"""
Archive-Based Multi-Temporal Change Analysis (PS 26227 §2.2.2).

Identifies meaningful changes within a specified AOI and time window
by querying the indexed archive, selecting tile pairs, running the
existing change detection pipeline, and estimating the earliest
observation date at which the change is supported.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.core.logging import logger
from app.services.ingestion import get_vector_index


@dataclass
class ChangeEvent:
    """A detected change between two observations."""
    change_id: str
    change_type: str           # construction, clearance, water_change, road_development, etc.
    category: str              # HUMAN, NATURAL, DISASTER
    confidence: float
    area_km2: float = 0.0
    earliest_observation: Optional[str] = None  # ISO timestamp of earliest detection
    before_tile_id: str = ""
    after_tile_id: str = ""
    before_date: Optional[str] = None
    after_date: Optional[str] = None
    location: Dict[str, Any] = field(default_factory=dict)  # GeoJSON point or polygon
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeAnalysisResult:
    """Complete result of an archive-based change analysis."""
    analysis_id: str
    aoi: Dict[str, Any]
    date_from: str
    date_to: str
    total_tiles_analyzed: int = 0
    total_changes_detected: int = 0
    change_events: List[ChangeEvent] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    processing_time_sec: float = 0.0
    provenance: Dict[str, Any] = field(default_factory=dict)


class ArchiveChangeService:
    """
    Orchestrates multi-temporal change analysis over the indexed archive.

    Given an AOI polygon and time window, the service:
    1. Queries the archive for all tiles overlapping the AOI
    2. Groups tiles by spatial location and sorts by date
    3. Runs pairwise change detection on sequential observations
    4. Classifies detected changes
    5. Estimates the earliest observation supporting each change
    """

    @staticmethod
    def analyze_change(
        aoi_geojson: Dict[str, Any],
        date_from: str,
        date_to: str,
        change_types: Optional[List[str]] = None,
    ) -> ChangeAnalysisResult:
        """
        Run change analysis over the archive for the given AOI and time window.

        Parameters
        ----------
        aoi_geojson : dict
            GeoJSON polygon defining the area of interest.
        date_from : str
            Start date (ISO format).
        date_to : str
            End date (ISO format).
        change_types : list, optional
            Filter for specific change types (e.g. ["construction", "clearance"]).

        Returns
        -------
        ChangeAnalysisResult with detected changes and timeline.
        """
        import time
        from app.db.base import generate_uuid_str

        start_time = time.time()
        analysis_id = generate_uuid_str()

        logger.info(
            f"Archive change analysis: AOI={_summarize_aoi(aoi_geojson)}, "
            f"window={date_from} to {date_to}"
        )

        result = ChangeAnalysisResult(
            analysis_id=analysis_id,
            aoi=aoi_geojson,
            date_from=date_from,
            date_to=date_to,
        )

        # Step 1: Find tiles overlapping the AOI in the time window
        # In a full implementation this queries PostGIS; for now we use
        # metadata stored alongside the FAISS index.
        matching_tiles = ArchiveChangeService._find_tiles_in_aoi(
            aoi_geojson, date_from, date_to
        )

        if len(matching_tiles) < 2:
            logger.warning("Fewer than 2 tiles found for the AOI/time window — cannot detect change")
            result.processing_time_sec = time.time() - start_time
            return result

        result.total_tiles_analyzed = len(matching_tiles)

        # Step 2: Group by spatial location and sort by date
        location_groups = ArchiveChangeService._group_by_location(matching_tiles)

        # Step 3: Pairwise change detection on sequential observations
        change_events: List[ChangeEvent] = []
        timeline_entries: List[Dict[str, Any]] = []

        for loc_key, tile_group in location_groups.items():
            # Sort by acquisition date
            tile_group.sort(key=lambda t: t.get("acquisition_date", ""))

            for i in range(len(tile_group) - 1):
                before_tile = tile_group[i]
                after_tile = tile_group[i + 1]

                # Run change detection (using existing baseline detector interface)
                change = ArchiveChangeService._detect_change_pair(
                    before_tile, after_tile, analysis_id, len(change_events)
                )

                if change is not None:
                    if change_types:
                        if change.change_type.lower() not in [ct.lower() for ct in change_types]:
                            continue
                    change_events.append(change)

                    timeline_entries.append({
                        "date": after_tile.get("acquisition_date", ""),
                        "change_type": change.change_type,
                        "area_km2": change.area_km2,
                        "confidence": change.confidence,
                        "tile_id": after_tile.get("tile_id", ""),
                    })

        result.change_events = change_events
        result.total_changes_detected = len(change_events)
        result.timeline = sorted(timeline_entries, key=lambda x: x.get("date", ""))
        result.processing_time_sec = time.time() - start_time

        # Provenance
        result.provenance = {
            "pipeline_version": "1.0.0",
            "change_detector": "baseline_spectral_diff",
            "tiles_analyzed": result.total_tiles_analyzed,
            "tile_ids": [t.get("tile_id", "") for t in matching_tiles],
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Archive change analysis complete: {result.total_changes_detected} changes "
            f"across {result.total_tiles_analyzed} tiles in {result.processing_time_sec:.1f}s"
        )
        return result

    @staticmethod
    def estimate_earliest_change(
        aoi_geojson: Dict[str, Any],
        change_event: ChangeEvent,
    ) -> Optional[str]:
        """
        Estimate the earliest observation date at which a change is visible.

        Uses binary search through available observations: for each midpoint,
        check if the change is present compared to the baseline.
        """
        # This would query the archive for all observations at this location
        # sorted by date, then binary search for the transition point.
        # Placeholder implementation returns the detected before_date.
        logger.info(f"Estimating earliest change date for event {change_event.change_id}")
        return change_event.before_date

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_tiles_in_aoi(
        aoi_geojson: Dict,
        date_from: str,
        date_to: str,
    ) -> List[Dict[str, Any]]:
        """
        Query the archive for tiles overlapping the AOI within the time window.

        In a full implementation, this queries PostGIS using ST_Intersects
        on the tile geometry and filters by acquisition_datetime.  For the
        current prototype, we return metadata from the FAISS ID map.
        """
        # Placeholder: In production, this queries the tiles table via:
        # SELECT * FROM tiles
        # WHERE ST_Intersects(bounds_geom, ST_GeomFromGeoJSON(:aoi))
        #   AND acquisition_datetime BETWEEN :date_from AND :date_to
        #   AND quality_score > 0.3
        # ORDER BY acquisition_datetime
        index = get_vector_index()
        tiles: List[Dict[str, Any]] = []
        for i in range(index.total_vectors):
            tile_id = index.get_tile_id_by_index(i)
            if tile_id:
                tiles.append({
                    "tile_id": tile_id,
                    "faiss_idx": i,
                    "scene_id": tile_id.split(":")[0] if ":" in tile_id else tile_id,
                    "acquisition_date": "",
                })
        return tiles

    @staticmethod
    def _group_by_location(
        tiles: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group tiles by their spatial location (scene_id as proxy)."""
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for tile in tiles:
            # Use scene_id as location grouping key
            loc_key = tile.get("scene_id", "default")
            groups.setdefault(loc_key, []).append(tile)
        return groups

    @staticmethod
    def _detect_change_pair(
        before: Dict, after: Dict, analysis_id: str, idx: int
    ) -> Optional[ChangeEvent]:
        """
        Run change detection between two tile observations.

        In a full implementation this loads the actual raster data and runs
        the Siamese U-Net or baseline detector.  For the prototype, we
        return a placeholder that demonstrates the data flow.
        """
        # Placeholder — the actual implementation would:
        # 1. Load tile rasters from disk
        # 2. Run RemoteSensingPreprocessor for co-registration
        # 3. Run BaselineChangeDetector or SiameseUNet inference
        # 4. Classify via HierarchicalChangeClassifier
        # This structure is ready for integration with existing ML pipeline.
        return None


def _summarize_aoi(aoi: Dict) -> str:
    """Human-readable AOI summary for logging."""
    coords = aoi.get("coordinates", [[]])
    if coords and coords[0]:
        n_points = len(coords[0])
        return f"polygon({n_points} vertices)"
    return "unknown"
