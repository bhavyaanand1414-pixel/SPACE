"""
Tile Processor — slices large satellite scenes into fixed-size tiles for embedding.

Each GeoTIFF scene is windowed into overlapping tiles, converted to RGB,
and annotated with geo-bounds so the vector index can track provenance
back to the source scene and spatial location.

Handles multi-band → RGB conversion for common sensors:
- Sentinel-2 L2A (13 bands): B4 (Red), B3 (Green), B2 (Blue)
- Landsat 8/9 OLI (7+ bands): B4 (Red), B3 (Green), B2 (Blue)
- Generic 3-band: assumed RGB
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import rasterio
from rasterio.windows import Window
from shapely.geometry import box, mapping

from app.core.config import settings
from app.core.logging import logger


@dataclass
class TileInfo:
    """Metadata and pixel data for a single extracted tile."""
    tile_index: int
    image_rgb: np.ndarray            # (H, W, 3) uint8 RGB
    window: Window                   # rasterio Window
    geo_bounds: Dict                  # GeoJSON polygon of tile footprint
    bbox: Tuple[float, float, float, float]  # (minx, miny, maxx, maxy)
    scene_id: str = ""
    row: int = 0
    col: int = 0
    cloud_fraction: float = 0.0      # fraction of tile covered by cloud/nodata
    quality_score: float = 1.0       # 1.0 = perfect, 0.0 = fully clouded/nodata


class TileProcessor:
    """
    Extracts overlapping RGB tiles from a georeferenced raster scene.

    Parameters are read from ``settings``:
    - TILE_SIZE    (default 256 px)
    - TILE_OVERLAP (default 32 px)
    """

    def __init__(
        self,
        tile_size: Optional[int] = None,
        tile_overlap: Optional[int] = None,
    ) -> None:
        self.tile_size = tile_size or settings.TILE_SIZE
        self.tile_overlap = tile_overlap or settings.TILE_OVERLAP
        self.stride = self.tile_size - self.tile_overlap

    def extract_tiles(
        self,
        scene_path: str,
        scene_id: str = "",
        scl_path: Optional[str] = None,
        max_cloud_fraction: float = 0.5,
    ) -> List[TileInfo]:
        """
        Slice a GeoTIFF/COG scene into overlapping tiles.

        Parameters
        ----------
        scene_path : str
            Absolute path to the scene file (GeoTIFF or COG).
        scene_id : str
            Identifier to embed in each tile's metadata for provenance.
        scl_path : str, optional
            Path to a Sentinel-2 Scene Classification Layer raster.
            If provided, per-tile cloud fraction is computed.
        max_cloud_fraction : float
            Tiles with cloud fraction above this value are discarded.

        Returns
        -------
        List[TileInfo] — tiles that pass the quality filter.
        """
        tiles: List[TileInfo] = []

        with rasterio.open(scene_path) as src:
            height, width = src.height, src.width
            transform = src.transform
            crs = src.crs
            band_count = src.count
            nodata = src.nodata

            # Determine RGB band indices (1-indexed for rasterio)
            rgb_bands = self._resolve_rgb_bands(src, band_count)

            # Optionally open SCL mask
            scl_ds = None
            if scl_path and Path(scl_path).exists():
                scl_ds = rasterio.open(scl_path)

            idx = 0
            for row_off in range(0, height - self.tile_size + 1, self.stride):
                for col_off in range(0, width - self.tile_size + 1, self.stride):
                    window = Window(col_off, row_off, self.tile_size, self.tile_size)

                    # Read RGB bands using windowed I/O (memory efficient)
                    rgb = src.read(rgb_bands, window=window)  # (3, H, W)

                    # Compute nodata/zero fraction
                    valid_mask = np.all(rgb > 0, axis=0) if nodata is None else np.all(rgb != nodata, axis=0)
                    valid_fraction = valid_mask.sum() / valid_mask.size

                    if valid_fraction < 0.5:
                        continue  # Skip mostly-empty tiles

                    # Compute cloud fraction from SCL if available
                    cloud_frac = 0.0
                    if scl_ds is not None:
                        scl_tile = scl_ds.read(1, window=window)
                        # SCL classes 8 (cloud medium), 9 (cloud high), 3 (cloud shadow), 11 (snow/ice)
                        cloud_pixels = np.isin(scl_tile, [3, 8, 9, 10, 11])
                        cloud_frac = float(cloud_pixels.sum() / cloud_pixels.size)

                    if cloud_frac > max_cloud_fraction:
                        continue  # Skip cloudy tiles

                    # Normalise to uint8 RGB (H, W, 3)
                    rgb_hwc = np.moveaxis(rgb, 0, -1)  # (H, W, 3)
                    rgb_uint8 = self._normalise_to_uint8(rgb_hwc)

                    # Compute geo-bounds of this tile
                    tile_transform = rasterio.windows.transform(window, transform)
                    minx = tile_transform.c
                    maxy = tile_transform.f
                    maxx = minx + self.tile_size * tile_transform.a
                    miny = maxy + self.tile_size * tile_transform.e  # e is negative
                    bbox = (minx, miny, maxx, maxy)
                    geo_polygon = mapping(box(*bbox))

                    tiles.append(TileInfo(
                        tile_index=idx,
                        image_rgb=rgb_uint8,
                        window=window,
                        geo_bounds=geo_polygon,
                        bbox=bbox,
                        scene_id=scene_id,
                        row=row_off // self.stride,
                        col=col_off // self.stride,
                        cloud_fraction=cloud_frac,
                        quality_score=round(valid_fraction * (1.0 - cloud_frac), 4),
                    ))
                    idx += 1

            if scl_ds is not None:
                scl_ds.close()

        logger.info(
            f"Extracted {len(tiles)} tiles from {Path(scene_path).name} "
            f"(scene {height}×{width}, tile {self.tile_size}px, stride {self.stride}px)"
        )
        return tiles

    # ------------------------------------------------------------------
    # Band resolution helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_rgb_bands(src, band_count: int) -> List[int]:
        """
        Determine which rasterio band indices correspond to Red, Green, Blue.
        Returns 1-indexed band list [R, G, B].
        """
        descriptions = [
            (src.descriptions[i] or "").lower() if src.descriptions and i < len(src.descriptions) else ""
            for i in range(band_count)
        ]

        # Sentinel-2 L2A (13 bands): B4=Red(idx 4), B3=Green(idx 3), B2=Blue(idx 2)
        if band_count >= 12:
            return [4, 3, 2]  # 1-indexed

        # Landsat 8/9 (7+ bands): B4=Red(idx 4), B3=Green(idx 3), B2=Blue(idx 2)
        if band_count >= 7:
            return [4, 3, 2]

        # 4-band (e.g. R,G,B,NIR): assume first three are RGB
        if band_count == 4:
            return [1, 2, 3]

        # 3-band: assumed RGB
        if band_count == 3:
            return [1, 2, 3]

        # Single band: replicate to 3 channels
        return [1, 1, 1]

    @staticmethod
    def _normalise_to_uint8(rgb: np.ndarray) -> np.ndarray:
        """
        Percentile-stretch multi-spectral reflectance values to 0–255 uint8.
        Uses 2–98% stretch to suppress outlier bright/dark pixels.
        """
        out = np.zeros_like(rgb, dtype=np.uint8)
        for c in range(rgb.shape[2]):
            band = rgb[:, :, c].astype(np.float64)
            p2 = np.percentile(band[band > 0], 2) if np.any(band > 0) else 0
            p98 = np.percentile(band[band > 0], 98) if np.any(band > 0) else 1
            if p98 <= p2:
                p98 = p2 + 1
            stretched = np.clip((band - p2) / (p98 - p2) * 255, 0, 255)
            out[:, :, c] = stretched.astype(np.uint8)
        return out
