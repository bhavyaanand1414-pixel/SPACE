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
    def _diversify_results(results: List[SearchResult], max_per_scene: int = 3) -> List[SearchResult]:
        """Ensure a single scene doesn't dominate the top results."""
        diversified = []
        scene_counts = {}
        for r in results:
            count = scene_counts.get(r.scene_id, 0)
            if count < max_per_scene:
                diversified.append(r)
                scene_counts[r.scene_id] = count + 1
        return diversified

    @staticmethod
    def text_search(
        query: str,
        filters: Optional[SearchFilters] = None,
        k: int = 50,
    ) -> List[SearchResult]:
        """
        Search the archive using a natural-language text query.
        """
        encoder = get_encoder()
        query_embedding = encoder.encode_text(query)

        index = get_vector_index()
        # Over-fetch massively to account for post-filtering and diversification
        raw_results = index.search(query_embedding, k=k * 5)

        results = SemanticSearchService._to_search_results(raw_results, is_image_query=False)

        if filters:
            results = SemanticSearchService._apply_filters(results, filters)
            
        results = SemanticSearchService._diversify_results(results, max_per_scene=2)

        return results[:k]

    @staticmethod
    def image_search(
        image: np.ndarray,
        filters: Optional[SearchFilters] = None,
        k: int = 50,
    ) -> List[SearchResult]:
        """
        Search the archive using an image tile as the query.
        """
        encoder = get_encoder()
        query_embedding = encoder.encode_image(image)

        index = get_vector_index()
        raw_results = index.search(query_embedding, k=k * 5)

        results = SemanticSearchService._to_search_results(raw_results, is_image_query=True)

        if filters:
            results = SemanticSearchService._apply_filters(results, filters)
            
        results = SemanticSearchService._diversify_results(results, max_per_scene=2)

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

        results = SemanticSearchService._to_search_results(raw_results, is_image_query=True)

        if filters:
            results = SemanticSearchService._apply_filters(results, filters)

        return results[:k]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_search_results(
        raw_results: List[Tuple[str, float]],
        is_image_query: bool = False
    ) -> List[SearchResult]:
        """Convert FAISS (tile_id, score) tuples to SearchResult objects."""
        results: List[SearchResult] = []
        for tile_id, score in raw_results:
            # tile_id format: "{scene_id}:{tile_index}"
            parts = tile_id.split(":", 1)
            scene_id = parts[0] if len(parts) > 1 else tile_id
            tile_index = parts[1] if len(parts) > 1 else "0"
            
            raw = float(score)
            if is_image_query:
                # Image-to-image embeddings have higher baseline cosine similarity.
                # Usually ~0.50 is unrelated, ~0.80+ is highly similar.
                normalized = max(0.0, min(1.0, (raw - 0.55) / 0.35))
            else:
                # Text-to-image typical bounds
                normalized = max(0.0, min(1.0, (raw - 0.18) / 0.14))
            
            results.append(SearchResult(
                tile_id=tile_id,
                scene_id=scene_id,
                similarity_score=round(normalized, 4),
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
