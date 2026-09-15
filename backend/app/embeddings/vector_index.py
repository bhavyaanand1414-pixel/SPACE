"""
FAISS Vector Index — approximate nearest-neighbor search for tile embeddings.

Provides incremental add() without full index rebuild, disk persistence,
and thread-safe concurrent read/write access.  Satisfies PS 26227 §2.2.6
(efficient vector indexing, incremental ingestion).
"""

import os
import threading
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from app.core.config import settings
from app.core.logging import logger


class FAISSVectorIndex:
    """
    Wrapper around FAISS for satellite tile embedding search.

    Supports three index types (configured via ``settings.FAISS_INDEX_TYPE``):
    - ``Flat``    : Exact brute-force search (best for < 100k vectors)
    - ``IVFFlat`` : Inverted file index (good for 100k–10M vectors)
    - ``HNSW``    : Hierarchical navigable small world graph (fast, memory-heavy)

    All operations are thread-safe via a read-write lock.
    """

    def __init__(
        self,
        dimension: Optional[int] = None,
        index_path: Optional[str] = None,
    ) -> None:
        import faiss

        self._faiss = faiss
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.index_path = Path(index_path or settings.FAISS_INDEX_PATH)
        self.index_path.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._index: Optional[faiss.Index] = None
        self._id_map: List[str] = []  # Maps FAISS integer ID → tile_id string

        # Try to load existing index from disk
        self._load_or_create()

    # ------------------------------------------------------------------
    # Index lifecycle
    # ------------------------------------------------------------------

    def _load_or_create(self) -> None:
        """Load a persisted index or create a fresh one."""
        import faiss

        index_file = self.index_path / "index.faiss"
        idmap_file = self.index_path / "id_map.npy"

        if index_file.exists():
            logger.info(f"Loading FAISS index from {index_file}")
            self._index = faiss.read_index(str(index_file))
            if idmap_file.exists():
                self._id_map = list(np.load(str(idmap_file), allow_pickle=True))
            logger.info(f"FAISS index loaded — {self._index.ntotal} vectors")
        else:
            self._index = self._build_empty_index()
            logger.info(
                f"Created empty FAISS {settings.FAISS_INDEX_TYPE} index "
                f"(dim={self.dimension})"
            )

    def _build_empty_index(self):
        """Build an empty FAISS index of the configured type."""
        import faiss

        idx_type = settings.FAISS_INDEX_TYPE.upper()

        if idx_type == "HNSW":
            index = faiss.IndexHNSWFlat(self.dimension, 32)
            index.hnsw.efConstruction = 200
            index.hnsw.efSearch = 128
        elif idx_type == "IVFFLAT":
            # IVF requires training, so wrap with IndexIDMap for now
            # and fall back to Flat until enough vectors exist for training
            index = faiss.IndexFlatIP(self.dimension)
        else:  # Flat (exact)
            index = faiss.IndexFlatIP(self.dimension)

        return index

    def save(self) -> None:
        """Persist the index and ID map to disk."""
        import faiss

        with self._lock:
            index_file = self.index_path / "index.faiss"
            idmap_file = self.index_path / "id_map.npy"

            faiss.write_index(self._index, str(index_file))
            np.save(str(idmap_file), np.array(self._id_map, dtype=object))

            logger.info(
                f"FAISS index saved — {self._index.ntotal} vectors → {index_file}"
            )

    # ------------------------------------------------------------------
    # Incremental add (PS 26227 §2.2.6)
    # ------------------------------------------------------------------

    def add(self, embedding: np.ndarray, tile_id: str) -> None:
        """
        Add a single embedding to the index incrementally.

        Parameters
        ----------
        embedding : np.ndarray of shape (dim,)
            L2-normalised embedding vector.
        tile_id : str
            Unique identifier for the tile (used for result lookup).
        """
        with self._lock:
            vec = embedding.reshape(1, -1).astype(np.float32)
            self._index.add(vec)
            self._id_map.append(tile_id)

    def add_batch(self, embeddings: np.ndarray, tile_ids: List[str]) -> None:
        """
        Add a batch of embeddings incrementally.

        Parameters
        ----------
        embeddings : np.ndarray of shape (N, dim)
        tile_ids : list of N tile ID strings
        """
        assert len(embeddings) == len(tile_ids), "Embeddings and tile_ids must have equal length"
        with self._lock:
            vecs = embeddings.astype(np.float32)
            self._index.add(vecs)
            self._id_map.extend(tile_ids)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self, query_vector: np.ndarray, k: int = 20
    ) -> List[Tuple[str, float]]:
        """
        Find the k nearest neighbors to a query vector.

        Parameters
        ----------
        query_vector : np.ndarray of shape (dim,)
            L2-normalised query embedding.
        k : int
            Number of results.

        Returns
        -------
        List of (tile_id, similarity_score) tuples, sorted by descending similarity.
        """
        with self._lock:
            if self._index.ntotal == 0:
                return []

            k = min(k, self._index.ntotal)
            vec = query_vector.reshape(1, -1).astype(np.float32)
            scores, indices = self._index.search(vec, k)

            results: List[Tuple[str, float]] = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:
                    continue
                if 0 <= idx < len(self._id_map):
                    results.append((self._id_map[idx], float(score)))

            return results

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @property
    def total_vectors(self) -> int:
        """Number of vectors currently in the index."""
        with self._lock:
            return self._index.ntotal if self._index else 0

    def get_all_embeddings(self) -> np.ndarray:
        """
        Reconstruct all embeddings from the index.
        Only works with Flat or IVFFlat indexes.
        """
        import faiss

        with self._lock:
            n = self._index.ntotal
            if n == 0:
                return np.empty((0, self.dimension), dtype=np.float32)

            vecs = np.zeros((n, self.dimension), dtype=np.float32)
            for i in range(n):
                try:
                    vecs[i] = self._index.reconstruct(i)
                except RuntimeError:
                    # Reconstruction not supported for this index type
                    break
            return vecs

    def get_embedding_by_index(self, idx: int) -> Optional[np.ndarray]:
        """Reconstruct a single embedding by its FAISS integer index."""
        with self._lock:
            if 0 <= idx < self._index.ntotal:
                try:
                    return self._index.reconstruct(idx).astype(np.float32)
                except RuntimeError:
                    return None
            return None

    def get_tile_id_by_index(self, idx: int) -> Optional[str]:
        """Look up a tile_id by its FAISS integer index."""
        with self._lock:
            if 0 <= idx < len(self._id_map):
                return self._id_map[idx]
            return None

    def clear(self) -> None:
        """Reset the index to empty."""
        with self._lock:
            self._index = self._build_empty_index()
            self._id_map = []
