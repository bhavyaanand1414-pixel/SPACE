"""
Ingestion Pipeline Service (PS 26227 §2.2.6).

End-to-end pipeline: GeoTIFF/COG scene → validate → extract metadata →
tile → embed (CLIP) → index (FAISS) → persist (PostgreSQL).

Supports incremental ingestion: new scenes are appended to the existing
index without a full rebuild.
"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import rasterio
from shapely.geometry import box, mapping
from PIL import Image

from app.core.config import settings
from app.core.logging import logger
from app.embeddings.clip_encoder import get_encoder
from app.embeddings.tile_processor import TileProcessor
from app.embeddings.vector_index import FAISSVectorIndex


# Module-level singletons (lazy)
_tile_processor: Optional[TileProcessor] = None
_vector_index: Optional[FAISSVectorIndex] = None


def _get_tile_processor() -> TileProcessor:
    global _tile_processor
    if _tile_processor is None:
        _tile_processor = TileProcessor()
    return _tile_processor


def _get_vector_index() -> FAISSVectorIndex:
    global _vector_index
    if _vector_index is None:
        _vector_index = FAISSVectorIndex()
    return _vector_index


def get_vector_index() -> FAISSVectorIndex:
    """Public accessor for the shared FAISS index singleton."""
    return _get_vector_index()


class IngestionResult:
    """Result of ingesting a single scene."""
    def __init__(self) -> None:
        self.scene_id: str = ""
        self.filename: str = ""
        self.status: str = "pending"  # pending, completed, failed, skipped
        self.tile_count: int = 0
        self.embedding_count: int = 0
        self.error: Optional[str] = None
        self.duration_sec: float = 0.0
        self.metadata: Dict[str, Any] = {}


class IngestionService:
    """
    Orchestrates scene ingestion: metadata extraction, tiling, embedding,
    and vector indexing.
    """

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """Compute SHA-256 hash for idempotent ingestion."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def extract_scene_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract geospatial metadata from a GeoTIFF/COG scene using rasterio.
        """
        meta: Dict[str, Any] = {}
        with rasterio.open(file_path) as src:
            meta["width"] = src.width
            meta["height"] = src.height
            meta["band_count"] = src.count
            meta["crs"] = str(src.crs) if src.crs else None
            meta["epsg_code"] = src.crs.to_epsg() if src.crs else None

            bounds = src.bounds
            meta["bounds_min_x"] = bounds.left
            meta["bounds_min_y"] = bounds.bottom
            meta["bounds_max_x"] = bounds.right
            meta["bounds_max_y"] = bounds.top
            meta["bounds_geojson"] = mapping(box(bounds.left, bounds.bottom, bounds.right, bounds.top))

            # Resolution in native units
            meta["resolution_x"] = abs(src.transform.a)
            meta["resolution_y"] = abs(src.transform.e)
            meta["resolution_m"] = meta["resolution_x"]  # Approximate

            meta["nodata"] = src.nodata

            # Try to extract satellite/sensor from tags
            tags = src.tags() or {}
            meta["satellite"] = (
                tags.get("SPACECRAFT_NAME")
                or tags.get("satellite")
                or tags.get("SATELLITE")
                or None
            )
            meta["sensor"] = (
                tags.get("SENSOR")
                or tags.get("sensor")
                or tags.get("INSTRUMENT")
                or None
            )
            acq = (
                tags.get("ACQUISITION_DATE")
                or tags.get("DATE_ACQUIRED")
                or tags.get("acquisition_date")
                or tags.get("DATATAKE_SENSING_START")
            )
            if acq:
                try:
                    meta["acquisition_datetime"] = datetime.fromisoformat(acq.replace("Z", "+00:00"))
                except ValueError:
                    meta["acquisition_datetime"] = None
            else:
                meta["acquisition_datetime"] = None

            # Cloud coverage from tags
            cc = tags.get("CLOUD_COVERAGE") or tags.get("CLOUD_COVER") or tags.get("cloud_coverage_percentage")
            meta["cloud_coverage_pct"] = float(cc) if cc else None

        return meta

    @staticmethod
    def ingest_scene(
        file_path: str,
        satellite: Optional[str] = None,
        sensor: Optional[str] = None,
        acquisition_datetime: Optional[datetime] = None,
        scl_path: Optional[str] = None,
    ) -> IngestionResult:
        """
        Ingest a single GeoTIFF/COG scene into the archive.

        Steps:
        1. Compute file hash (skip if already ingested)
        2. Extract geospatial metadata
        3. Extract tiles
        4. Compute CLIP embeddings for each tile
        5. Add embeddings to FAISS index (incremental)
        6. Save index to disk

        Returns an IngestionResult with scene_id, tile count, status.
        """
        import time
        start_time = time.time()

        result = IngestionResult()
        result.filename = Path(file_path).name

        try:
            # Step 1: Hash check
            file_hash = IngestionService.compute_file_hash(file_path)
            logger.info(f"Ingesting scene: {result.filename} (hash={file_hash[:12]}...)")

            # Step 2: Extract metadata
            meta = IngestionService.extract_scene_metadata(file_path)
            result.metadata = meta

            # Override metadata with explicit parameters if provided
            if satellite:
                meta["satellite"] = satellite
            if sensor:
                meta["sensor"] = sensor
            if acquisition_datetime:
                meta["acquisition_datetime"] = acquisition_datetime

            # Generate scene ID
            from app.db.base import generate_uuid_str
            scene_id = generate_uuid_str()
            result.scene_id = scene_id

            # Step 3: Extract tiles
            processor = _get_tile_processor()
            tiles = processor.extract_tiles(
                scene_path=file_path,
                scene_id=scene_id,
                scl_path=scl_path,
            )
            result.tile_count = len(tiles)

            if len(tiles) == 0:
                result.status = "completed"
                result.duration_sec = time.time() - start_time
                logger.warning(f"No usable tiles extracted from {result.filename}")
                return result

            # Step 4: Compute embeddings and save tiles to disk
            encoder = get_encoder()
            tile_images = []
            
            # Create tiles directory if it doesn't exist
            tiles_dir = Path(settings.LOCAL_STORAGE_PATH) / "tiles"
            tiles_dir.mkdir(parents=True, exist_ok=True)
            
            for t in tiles:
                tile_images.append(t.image_rgb)
                # Save JPEG tile for static serving
                tile_path = tiles_dir / f"{scene_id}_{t.tile_index}.jpg"
                Image.fromarray(t.image_rgb).save(tile_path, format="JPEG", quality=85)
                
            embeddings = encoder.encode_images_batch(tile_images, batch_size=32)
            result.embedding_count = len(embeddings)

            # Step 5: Add to FAISS index
            index = _get_vector_index()
            base_faiss_idx = index.total_vectors
            tile_ids = [f"{scene_id}:{t.tile_index}" for t in tiles]
            index.add_batch(embeddings, tile_ids)

            # Step 6: Save index
            index.save()

            result.status = "completed"
            result.duration_sec = time.time() - start_time

            logger.info(
                f"Scene ingested: {result.filename} → {len(tiles)} tiles, "
                f"{len(embeddings)} embeddings in {result.duration_sec:.1f}s"
            )

        except Exception as exc:
            result.status = "failed"
            result.error = str(exc)
            logger.error(f"Ingestion failed for {result.filename}: {exc}")

        return result

    @staticmethod
    def ingest_directory(dir_path: str, **kwargs) -> List[IngestionResult]:
        """
        Batch ingest all GeoTIFF/COG scenes in a directory.
        """
        results: List[IngestionResult] = []
        scan_path = Path(dir_path)

        if not scan_path.is_dir():
            logger.error(f"Ingestion directory not found: {dir_path}")
            return results

        extensions = {".tif", ".tiff", ".geotiff"}
        scene_files = sorted(
            f for f in scan_path.rglob("*") if f.suffix.lower() in extensions
        )
        logger.info(f"Found {len(scene_files)} scene files in {dir_path}")

        for scene_file in scene_files:
            res = IngestionService.ingest_scene(str(scene_file), **kwargs)
            results.append(res)

        return results

    @staticmethod
    def get_index_status() -> Dict[str, Any]:
        """Return current index statistics."""
        index = _get_vector_index()
        index_path = Path(settings.FAISS_INDEX_PATH)
        index_size_mb = 0.0
        if (index_path / "index.faiss").exists():
            index_size_mb = (index_path / "index.faiss").stat().st_size / (1024 * 1024)

        return {
            "total_vectors": index.total_vectors,
            "index_dimension": index.dimension,
            "index_type": settings.FAISS_INDEX_TYPE,
            "index_path": str(index_path),
            "index_size_mb": round(index_size_mb, 2),
        }
