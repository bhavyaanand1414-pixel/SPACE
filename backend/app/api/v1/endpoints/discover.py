"""
Discovery & Clustering API Endpoints (PS 26227 §2.2.4).

Provides unsupervised embedding-based grouping of similar sites and
"find similar" functionality for analyst-driven discovery.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.core.logging import logger
from app.schemas.search import (
    ClusterInfoSchema,
    ClustersResponse,
    DiscoverSimilarRequest,
    SearchResultItem,
    SearchResultsResponse,
)
from app.services.clustering import ClusteringService
from app.services.ingestion import get_vector_index

router = APIRouter(prefix="/discover", tags=["Discovery & Clustering (PS 26227 §2.2.4)"])


@router.get(
    "/clusters",
    response_model=ClustersResponse,
    summary="List All Tile Clusters",
    description=(
        "Group all indexed tiles into clusters of semantically similar imagery. "
        "Enables analysts to discover patterns across the archive without "
        "manually constructing queries."
    ),
)
async def list_clusters(
    method: str = Query("hdbscan", description="Clustering method: hdbscan or kmeans"),
    min_cluster_size: int = Query(5, ge=2, le=100),
    n_clusters: int = Query(20, ge=2, le=200),
):
    """Cluster all indexed tile embeddings."""
    try:
        index = get_vector_index()
        total_tiles = index.total_vectors

        clusters = ClusteringService.cluster_tiles(
            method=method,
            min_cluster_size=min_cluster_size,
            n_clusters=n_clusters,
        )

        return ClustersResponse(
            total_clusters=len(clusters),
            total_tiles=total_tiles,
            method=method,
            clusters=[
                ClusterInfoSchema(
                    cluster_id=c.cluster_id,
                    member_count=c.member_count,
                    representative_tile_ids=c.representative_tile_ids,
                    centroid_lat=c.centroid_lat,
                    centroid_lon=c.centroid_lon,
                    label=c.label,
                    x_proj=c.x_proj,
                    y_proj=c.y_proj,
                )
                for c in clusters
            ],
        )
    except Exception as exc:
        logger.error(f"Clustering error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clustering failed: {str(exc)}",
        )


@router.post(
    "/similar",
    response_model=SearchResultsResponse,
    summary="Find Similar Sites",
    description=(
        "Given a tile ID, find other locations with comparable visual or "
        "semantic characteristics across the archive."
    ),
)
async def find_similar(request: DiscoverSimilarRequest):
    """Find tiles semantically similar to a given tile."""
    try:
        results = ClusteringService.find_similar_sites(
            tile_id=request.tile_id,
            k=request.k,
        )

        return SearchResultsResponse(
            query=f"[similar to: {request.tile_id}]",
            total_results=len(results),
            results=[
                SearchResultItem(
                    tile_id=tid,
                    scene_id=tid.split(":")[0] if ":" in tid else tid,
                    similarity_score=round(score, 4),
                )
                for tid, score in results
            ],
            search_type="similar",
        )
    except Exception as exc:
        logger.error(f"Find similar error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Find similar failed: {str(exc)}",
        )


@router.get(
    "/clusters/{cluster_id}/members",
    summary="Get Cluster Members",
    description="Return all tile IDs belonging to a specific cluster.",
)
async def get_cluster_members(
    cluster_id: int,
    method: str = Query("hdbscan"),
    min_cluster_size: int = Query(5, ge=2),
):
    """Get all tiles in a specific cluster."""
    try:
        members = ClusteringService.get_cluster_members(
            cluster_id=cluster_id,
            method=method,
            min_cluster_size=min_cluster_size,
        )
        return {"cluster_id": cluster_id, "member_count": len(members), "tile_ids": members}
    except Exception as exc:
        logger.error(f"Cluster members error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
