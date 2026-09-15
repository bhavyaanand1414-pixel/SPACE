"""
Semantic Embedding Engine for satellite imagery retrieval (PS 26227 §2.2.1).

Provides CLIP-based encoding of image tiles and text queries into a shared
embedding space for cross-modal semantic search.  All models run locally —
no external API calls.
"""

from app.embeddings.clip_encoder import CLIPEmbeddingEncoder
from app.embeddings.tile_processor import TileProcessor
from app.embeddings.vector_index import FAISSVectorIndex

__all__ = [
    "CLIPEmbeddingEncoder",
    "TileProcessor",
    "FAISSVectorIndex",
]
