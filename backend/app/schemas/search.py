"""
Pydantic schemas for semantic search (PS 26227 §2.2.1).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchFiltersSchema(BaseModel):
    """Metadata filters for refining search results."""
    aoi_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON polygon for spatial filter")
    date_from: Optional[datetime] = Field(None, description="Start date (ISO 8601)")
    date_to: Optional[datetime] = Field(None, description="End date (ISO 8601)")
    satellite: Optional[str] = Field(None, description="Satellite filter (e.g. sentinel-2, landsat)")
    sensor: Optional[str] = Field(None, description="Sensor filter (e.g. MSI, OLI)")
    min_quality: float = Field(0.0, ge=0.0, le=1.0, description="Minimum tile quality score")


class TextSearchRequest(BaseModel):
    """Request body for text-to-image semantic search."""
    query: str = Field(..., min_length=1, max_length=500, description="Natural-language search query")
    filters: Optional[SearchFiltersSchema] = None
    limit: int = Field(50, ge=1, le=200, description="Maximum results to return")


class ImageSearchRequest(BaseModel):
    """Request body for image-to-image search (image sent as multipart)."""
    filters: Optional[SearchFiltersSchema] = None
    limit: int = Field(50, ge=1, le=200)


class SearchResultItem(BaseModel):
    """A single search result."""
    tile_id: str
    scene_id: str
    similarity_score: float = Field(..., description="Cosine similarity score (0–1)")
    bbox: List[float] = Field(default_factory=list, description="[minx, miny, maxx, maxy]")
    acquisition_date: Optional[str] = None
    satellite: Optional[str] = None
    sensor: Optional[str] = None
    thumbnail_url: Optional[str] = None
    quality_score: float = 1.0


class SearchResultsResponse(BaseModel):
    """Response for semantic search queries."""
    query: Optional[str] = None
    total_results: int
    results: List[SearchResultItem]
    search_type: str = "text"  # text or image
    latency_ms: float = 0.0


class DiscoverSimilarRequest(BaseModel):
    """Request to find similar sites given a tile ID."""
    tile_id: str = Field(..., description="Source tile ID to find similar sites for")
    k: int = Field(20, ge=1, le=100, description="Number of similar sites to return")


class ClusterInfoSchema(BaseModel):
    """A single cluster of similar tiles."""
    cluster_id: int
    member_count: int
    representative_tile_ids: List[str] = Field(default_factory=list)
    centroid_lat: float = 0.0
    centroid_lon: float = 0.0
    label: str = ""
    x_proj: float = 0.0
    y_proj: float = 0.0


class ClustersResponse(BaseModel):
    """Response for clustering endpoint."""
    total_clusters: int
    total_tiles: int
    method: str
    clusters: List[ClusterInfoSchema]


class ChangeAnalysisRequest(BaseModel):
    """Request for archive-based change analysis."""
    aoi_geojson: Dict[str, Any] = Field(..., description="GeoJSON polygon for AOI")
    date_from: str = Field(..., description="Start date (ISO 8601)")
    date_to: str = Field(..., description="End date (ISO 8601)")
    change_types: Optional[List[str]] = Field(None, description="Filter by change type")


class ChangeEventSchema(BaseModel):
    """A single detected change event."""
    change_id: str
    change_type: str
    category: str
    confidence: float
    area_km2: float = 0.0
    earliest_observation: Optional[str] = None
    before_tile_id: str = ""
    after_tile_id: str = ""
    before_date: Optional[str] = None
    after_date: Optional[str] = None
    location: Dict[str, Any] = Field(default_factory=dict)
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Cosine similarity, change magnitude, quality mask info")


class ChangeAnalysisResponse(BaseModel):
    """Response for archive-based change analysis."""
    analysis_id: str
    total_tiles_analyzed: int
    total_changes_detected: int
    change_events: List[ChangeEventSchema]
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time_sec: float = 0.0


class IngestionRequest(BaseModel):
    """Request to ingest a scene from a server-side path."""
    file_path: str = Field(..., description="Server-side path to GeoTIFF/COG file")
    satellite: Optional[str] = None
    sensor: Optional[str] = None
    acquisition_datetime: Optional[datetime] = None
    scl_path: Optional[str] = Field(None, description="Path to SCL quality mask raster")


class DirectoryIngestionRequest(BaseModel):
    """Request to batch ingest all scenes in a directory."""
    directory_path: str = Field(..., description="Server-side directory path")
    satellite: Optional[str] = None
    sensor: Optional[str] = None


class IngestionResultSchema(BaseModel):
    """Result of ingesting a single scene."""
    scene_id: str
    filename: str
    status: str
    tile_count: int = 0
    embedding_count: int = 0
    error: Optional[str] = None
    duration_sec: float = 0.0


class IndexStatusResponse(BaseModel):
    """Current state of the FAISS vector index."""
    total_vectors: int
    index_dimension: int
    index_type: str
    index_path: str
    index_size_mb: float = 0.0
