"""
Discovery & Clustering Service (PS 26227 §2.2.4).

Provides unsupervised embedding-based grouping of similar satellite tiles
so an analyst who identifies one location of interest can discover other
locations with comparable visual or semantic characteristics.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.core.logging import logger
from app.services.ingestion import get_vector_index


@dataclass
class ClusterInfo:
    """Metadata for a single cluster of similar tiles."""
    cluster_id: int
    member_count: int
    representative_tile_ids: List[str] = field(default_factory=list)
    centroid_lat: float = 0.0
    centroid_lon: float = 0.0
    label: str = ""
    # 2D projection coordinates for visualization
    x_proj: float = 0.0
    y_proj: float = 0.0


class ClusteringService:
    """
    Clusters tile embeddings using HDBSCAN or K-Means and provides
    "find similar sites" via k-NN in embedding space.
    """

    @staticmethod
    def cluster_tiles(
        method: str = "hdbscan",
        min_cluster_size: int = 5,
        n_clusters: int = 20,
    ) -> List[ClusterInfo]:
        """
        Cluster all indexed tile embeddings.

        Parameters
        ----------
        method : str
            Clustering algorithm: "hdbscan" (density-based) or "kmeans".
        min_cluster_size : int
            Minimum cluster size for HDBSCAN.
        n_clusters : int
            Number of clusters for K-Means.

        Returns
        -------
        List of ClusterInfo with member counts and representative tiles.
        """
        index = get_vector_index()
        n = index.total_vectors
        if n < min_cluster_size:
            logger.warning(f"Not enough vectors ({n}) for clustering (min={min_cluster_size})")
            return []

        # Extract all embeddings
        embeddings = index.get_all_embeddings()
        if embeddings.shape[0] == 0:
            return []

        # Dimensionality reduction for clustering stability
        from sklearn.decomposition import PCA
        n_components = min(50, embeddings.shape[1], embeddings.shape[0])
        pca = PCA(n_components=n_components)
        reduced = pca.fit_transform(embeddings)

        # Cluster
        if method.lower() == "hdbscan":
            import hdbscan
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=max(2, min_cluster_size // 2),
                metric="euclidean",
            )
            labels = clusterer.fit_predict(reduced)
        else:
            from sklearn.cluster import KMeans
            actual_k = min(n_clusters, n)
            clusterer = KMeans(n_clusters=actual_k, random_state=42, n_init=10)
            labels = clusterer.fit_predict(reduced)

        # 2D projection for visualization
        projections_2d = ClusteringService._compute_2d_projection(reduced)

        # Build cluster info
        unique_labels = set(labels)
        unique_labels.discard(-1)  # HDBSCAN noise label

        clusters: List[ClusterInfo] = []
        for label in sorted(unique_labels):
            member_indices = np.where(labels == label)[0]
            member_tile_ids = [
                index.get_tile_id_by_index(int(i)) or f"idx-{i}"
                for i in member_indices
            ]

            # Representatives: tiles closest to cluster centroid
            cluster_embeddings = embeddings[member_indices]
            centroid = cluster_embeddings.mean(axis=0)
            dists = np.linalg.norm(cluster_embeddings - centroid, axis=1)
            closest_indices = np.argsort(dists)[:5]
            representatives = [member_tile_ids[int(i)] for i in closest_indices]

            # Projection centroid
            cluster_proj = projections_2d[member_indices]
            proj_centroid = cluster_proj.mean(axis=0)

            clusters.append(ClusterInfo(
                cluster_id=int(label),
                member_count=len(member_indices),
                representative_tile_ids=representatives,
                x_proj=float(proj_centroid[0]),
                y_proj=float(proj_centroid[1]),
            ))

        logger.info(
            f"Clustering complete: {len(clusters)} clusters from {n} tiles "
            f"(method={method}, noise={int(np.sum(labels == -1))})"
        )
        return clusters

    @staticmethod
    def find_similar_sites(
        tile_id: str,
        k: int = 20,
    ) -> List[Tuple[str, float]]:
        """
        Given a tile_id, find the k most similar tiles in the archive.

        This enables the PS 26227 requirement that an analyst who identifies
        one location of interest can discover comparable sites without
        manually constructing a new query.

        Returns
        -------
        List of (tile_id, similarity_score) tuples.
        """
        index = get_vector_index()

        # Find the FAISS integer index for this tile_id
        tile_faiss_idx = None
        for i in range(index.total_vectors):
            if index.get_tile_id_by_index(i) == tile_id:
                tile_faiss_idx = i
                break

        if tile_faiss_idx is None:
            logger.warning(f"Tile {tile_id} not found in FAISS index")
            return []

        # Reconstruct its embedding and search
        embedding = index.get_embedding_by_index(tile_faiss_idx)
        if embedding is None:
            return []

        results = index.search(embedding, k=k + 1)
        # Remove self from results
        return [(tid, score) for tid, score in results if tid != tile_id][:k]

    @staticmethod
    def get_cluster_members(
        cluster_id: int,
        method: str = "hdbscan",
        min_cluster_size: int = 5,
        n_clusters: int = 20,
    ) -> List[str]:
        """Return all tile_ids belonging to a specific cluster."""
        index = get_vector_index()
        n = index.total_vectors
        if n < min_cluster_size:
            return []

        embeddings = index.get_all_embeddings()
        from sklearn.decomposition import PCA
        n_components = min(50, embeddings.shape[1], embeddings.shape[0])
        reduced = PCA(n_components=n_components).fit_transform(embeddings)

        if method.lower() == "hdbscan":
            import hdbscan
            labels = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=max(2, min_cluster_size // 2),
            ).fit_predict(reduced)
        else:
            from sklearn.cluster import KMeans
            labels = KMeans(n_clusters=min(n_clusters, n), random_state=42).fit_predict(reduced)

        member_indices = np.where(labels == cluster_id)[0]
        return [
            index.get_tile_id_by_index(int(i)) or f"idx-{i}"
            for i in member_indices
        ]

    @staticmethod
    def _compute_2d_projection(embeddings: np.ndarray) -> np.ndarray:
        """Project embeddings to 2D for scatter-plot visualization."""
        if embeddings.shape[0] < 5:
            from sklearn.decomposition import PCA
            return PCA(n_components=2).fit_transform(embeddings)

        try:
            import umap
            reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=min(15, embeddings.shape[0] - 1))
            return reducer.fit_transform(embeddings)
        except ImportError:
            from sklearn.decomposition import PCA
            return PCA(n_components=2).fit_transform(embeddings)
