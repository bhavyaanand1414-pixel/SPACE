"""
CLIP Embedding Encoder — local multimodal encoder for satellite imagery.

Uses OpenCLIP (open-source CLIP implementation) to encode imagery tiles and
natural-language queries into a shared 512-d embedding space.  The model runs
entirely on-device (CPU or CUDA) with no external API calls, satisfying the
PS 26227 §2.2.7 offline operation constraint.

Supported workflows:
- encode_image(tile) → 512-d vector  (for indexing and image-to-image search)
- encode_text(query) → 512-d vector  (for text-to-image semantic search)
"""

import threading
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import torch
from PIL import Image as PILImage

from app.core.config import settings
from app.core.logging import logger

# Lazy-loaded to avoid import-time GPU allocation
_encoder_lock = threading.Lock()
_encoder_instance: Optional["CLIPEmbeddingEncoder"] = None


def get_encoder() -> "CLIPEmbeddingEncoder":
    """Thread-safe singleton accessor for the CLIP encoder."""
    global _encoder_instance
    if _encoder_instance is None:
        with _encoder_lock:
            if _encoder_instance is None:
                _encoder_instance = CLIPEmbeddingEncoder()
    return _encoder_instance


class CLIPEmbeddingEncoder:
    """
    Encodes satellite image tiles and text queries using OpenCLIP.

    Parameters are read from ``app.core.config.settings``:
    - EMBEDDING_MODEL_NAME   (default: ViT-B-32)
    - EMBEDDING_PRETRAINED   (default: laion2b_s34b_b79k)
    - EMBEDDING_WEIGHTS_PATH (local cache directory for offline use)
    - MODEL_DEVICE           (auto / cuda / cpu)
    """

    def __init__(self) -> None:
        import open_clip

        self.device = self._resolve_device()

        cache_dir = Path(settings.EMBEDDING_WEIGHTS_PATH)
        cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Loading CLIP model {settings.EMBEDDING_MODEL_NAME} "
            f"(pretrained={settings.EMBEDDING_PRETRAINED}) on {self.device}"
        )

        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name=settings.EMBEDDING_MODEL_NAME,
            pretrained=settings.EMBEDDING_PRETRAINED,
            cache_dir=str(cache_dir),
        )
        self.tokenizer = open_clip.get_tokenizer(settings.EMBEDDING_MODEL_NAME)
        self.model = self.model.to(self.device).eval()

        self.embedding_dim: int = settings.EMBEDDING_DIMENSION
        logger.info(
            f"CLIP encoder ready — dim={self.embedding_dim}, device={self.device}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @torch.no_grad()
    def encode_image(self, image: Union[np.ndarray, PILImage.Image]) -> np.ndarray:
        """
        Encode a single image tile into a unit-normalised embedding vector.

        Parameters
        ----------
        image : np.ndarray (H, W, 3) uint8  or  PIL.Image
            RGB image tile.  Multi-band satellite imagery should be
            pre-converted to 3-channel RGB before calling this method.

        Returns
        -------
        np.ndarray of shape (embedding_dim,) — float32, L2-normalised.
        """
        if isinstance(image, np.ndarray):
            image = PILImage.fromarray(image.astype(np.uint8))

        tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        features = self.model.encode_image(tensor)
        features = features / features.norm(dim=-1, keepdim=True)
        return features.cpu().numpy().flatten().astype(np.float32)

    @torch.no_grad()
    def encode_images_batch(
        self, images: List[Union[np.ndarray, PILImage.Image]], batch_size: int = 32
    ) -> np.ndarray:
        """
        Encode a batch of images, returning an (N, dim) array of embeddings.
        """
        all_embeddings: List[np.ndarray] = []

        for start in range(0, len(images), batch_size):
            batch = images[start : start + batch_size]
            pil_imgs = [
                PILImage.fromarray(img.astype(np.uint8)) if isinstance(img, np.ndarray) else img
                for img in batch
            ]
            tensors = torch.stack([self.preprocess(img) for img in pil_imgs]).to(self.device)
            features = self.model.encode_image(tensors)
            features = features / features.norm(dim=-1, keepdim=True)
            all_embeddings.append(features.cpu().numpy().astype(np.float32))

        return np.vstack(all_embeddings)

    @torch.no_grad()
    def encode_text(self, query: str) -> np.ndarray:
        """
        Encode a natural-language query into the same embedding space as images.

        Returns
        -------
        np.ndarray of shape (embedding_dim,) — float32, L2-normalised.
        """
        tokens = self.tokenizer([query]).to(self.device)
        features = self.model.encode_text(tokens)
        features = features / features.norm(dim=-1, keepdim=True)
        return features.cpu().numpy().flatten().astype(np.float32)

    @torch.no_grad()
    def encode_texts_batch(self, queries: List[str]) -> np.ndarray:
        """Encode multiple text queries, returning (N, dim) embeddings."""
        tokens = self.tokenizer(queries).to(self.device)
        features = self.model.encode_text(tokens)
        features = features / features.norm(dim=-1, keepdim=True)
        return features.cpu().numpy().astype(np.float32)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_device() -> str:
        device = settings.MODEL_DEVICE.lower()
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        return device
