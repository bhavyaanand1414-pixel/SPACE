"""
Semantic Search Service (PS 26227 §2.2.1).

Provides text-to-image and image-to-image search over the indexed
satellite imagery archive, with post-filtering by AOI, date range,
and sensor metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from shapely.geometry import shape, box

from app.core.config import settings
from app.core.logging import logger
from app.embeddings.clip_encoder import get_encoder
from app.services.ingestion import get_vector_index


@dataclass
class SearchFilters:
    """Metadata filters applied after vector similarity search."""
    aoi_geojson: Optional[Dict] = None        # GeoJSON polygon for spatial filter
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    satellite: Optional[str] = None
    sensor: Optional[str] = None
    min_quality: float = 0.0


@dataclass
class SearchResult:
    """A single search result with similarity score and tile metadata."""
    tile_id: str
    scene_id: str
    similarity_score: float
    bbox: Tuple[float, float, float, float] = (0, 0, 0, 0)  # minx, miny, maxx, maxy
    acquisition_date: Optional[str] = None
    satellite: Optional[str] = None
    sensor: Optional[str] = None
    thumbnail_url: Optional[str] = None
    quality_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SemanticSearchService:
    """
    Multimodal semantic search over the satellite imagery archive.

    Supports:
    - Text-to-image search: natural-language query → ranked tile results
    - Image-to-image search: query tile → visually similar tiles
    - Metadata post-filtering: AOI, date range, sensor
    """

    @staticmethod
    def text_search(
        query: str,
        filters: Optional[SearchFilters] = None,
        k: int = 50,
    ) -> List[SearchResult]:
        """
        Search the archive using a natural-language text query.

        Examples:
        - "newly built structures near a river"
        - "large vehicle concentrations on open ground"
        - "deforested area with exposed soil"

        Returns ranked results by cosine similarity (descending).
        """
        encoder = get_encoder()
        query_embedding = encoder.encode_text(query)

        index = get_vector_index()
        # Over-fetch to account for post-filtering
        raw_results = index.search(query_embedding, k=k * 3)

        results = SemanticSearchService._to_search_results(raw_results)

        if filters:
            results = SemanticSearchService._apply_filters(results, filters)

        return results[:k]

    @staticmethod
    def image_search(
        image: np.ndarray,
        filters: Optional[SearchFilters] = None,
        k: int = 50,
    ) -> List[SearchResult]:
        """
        Search the archive using an image tile as the query.

        Parameters
        ----------
        image : np.ndarray (H, W, 3) uint8
            RGB image tile to use as the visual query.

        Returns ranked results by cosine similarity (descending).
        """
        encoder = get_encoder()
        query_embedding = encoder.encode_image(image)

        index = get_vector_index()
        raw_results = index.search(query_embedding, k=k * 3)

        results = SemanticSearchService._to_search_results(raw_results)

        if filters:
            results = SemanticSearchService._apply_filters(results, filters)

        return results[:k]

    @staticmethod
    def tile_similarity_search(
        tile_id: str,
        filters: Optional[SearchFilters] = None,
        k: int = 50,
    ) -> List[SearchResult]:
        """
        Find tiles visually similar to an existing indexed tile.

        Reconstructs the embedding for *tile_id* directly from the FAISS
        index (no image file needed) and returns ranked neighbours.
        """
        index = get_vector_index()

        # Find the FAISS integer index for this tile_id
        target_idx = None
        for i, tid in enumerate(index._id_map):
            if tid == tile_id:
                target_idx = i
                break

        if target_idx is None:
            logger.warning(f"tile_similarity_search: tile_id '{tile_id}' not found in index")
            return []

        query_embedding = index.get_embedding_by_index(target_idx)
        if query_embedding is None:
            return []

        # Over-fetch, then filter out the query tile itself
        raw_results = index.search(query_embedding, k=k * 3 + 1)
        raw_results = [(tid, score) for tid, score in raw_results if tid != tile_id]

        results = SemanticSearchService._to_search_results(raw_results)

        if filters:
            results = SemanticSearchService._apply_filters(results, filters)

        return results[:k]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_search_results(
        raw_results: List[Tuple[str, float]],
    ) -> List[SearchResult]:
        """Convert FAISS (tile_id, score) tuples to SearchResult objects."""
        results: List[SearchResult] = []
        for tile_id, score in raw_results:
            # tile_id format: "{scene_id}:{tile_index}"
            parts = tile_id.split(":", 1)
            scene_id = parts[0] if len(parts) > 1 else tile_id
            tile_index = parts[1] if len(parts) > 1 else "0"
            results.append(SearchResult(
                tile_id=tile_id,
                scene_id=scene_id,
                similarity_score=round(float(score), 4),
                thumbnail_url=f"/api/v1/tiles/{scene_id}_{tile_index}.jpg"
            ))
        return results

    @staticmethod
    def _apply_filters(
        results: List[SearchResult],
        filters: SearchFilters,
    ) -> List[SearchResult]:
        """
        Apply metadata-based post-filtering to search results.

        Note: In a production deployment these filters would be applied via
        SQL queries against the tiles/scenes tables.  For the current
        in-process prototype we filter in Python.
        """
        filtered: List[SearchResult] = []
        for r in results:
            # Quality filter
            if r.quality_score < filters.min_quality:
                continue

            # Satellite filter
            if filters.satellite and r.satellite:
                if filters.satellite.lower() not in r.satellite.lower():
                    continue

            # Date range filter
            if r.acquisition_date:
                try:
                    acq = datetime.fromisoformat(r.acquisition_date)
                    if filters.date_from and acq < filters.date_from:
                        continue
                    if filters.date_to and acq > filters.date_to:
                        continue
                except (ValueError, TypeError):
                    pass

            # AOI spatial filter
            if filters.aoi_geojson and r.bbox != (0, 0, 0, 0):
                try:
                    aoi_shape = shape(filters.aoi_geojson)
                    tile_box = box(*r.bbox)
                    if not aoi_shape.intersects(tile_box):
                        continue
                except Exception:
                    pass

            filtered.append(r)
        return filtered
