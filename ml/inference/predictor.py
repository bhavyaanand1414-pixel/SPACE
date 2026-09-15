"""
Inference Engine for Siamese U-Net Satellite Change Detection.

Supports whole-image tensor prediction and tile-based sliding window inference for large rasters.
"""

from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import torch

try:
    from app.core.logging import logger
except ImportError:
    import logging
    logger = logging.getLogger("sih1518")
from ml.models.base import get_optimal_device
from ml.models.siamese_unet import SiameseUNetChangeDetector


class SiamesePredictor:
    """
    Inference orchestrator for Siamese U-Net model.
    """

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        device: Optional[torch.device] = None,
        confidence_threshold: float = 0.5,
        in_channels: int = 3,
        base_filters: int = 32,
    ):
        self.device = device or get_optimal_device()
        self.confidence_threshold = confidence_threshold
        self.model = SiameseUNetChangeDetector(in_channels=in_channels, base_filters=base_filters).to(self.device)

        if checkpoint_path and Path(checkpoint_path).is_file():
            self.model.load_checkpoint(checkpoint_path, device=self.device)
            logger.info(f"Loaded Siamese U-Net weights from: {checkpoint_path}")
        else:
            logger.info("Initialized Siamese U-Net with default weights.")

        self.model.eval()

    def predict(
        self,
        image1: np.ndarray,
        image2: np.ndarray,
        threshold: Optional[float] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Run inference on normalized (C, H, W) numpy float32 arrays in [0.0, 1.0].

        Returns:
            (probability_map_2d, binary_mask_2d)
        """
        t = threshold if threshold is not None else self.confidence_threshold

        # Ensure (1, C, H, W) torch tensor
        if image1.ndim == 3:
            t1 = torch.from_numpy(image1).unsqueeze(0).float().to(self.device)
            t2 = torch.from_numpy(image2).unsqueeze(0).float().to(self.device)
        else:
            t1 = torch.from_numpy(image1).float().to(self.device)
            t2 = torch.from_numpy(image2).float().to(self.device)

        with torch.no_grad():
            prob_tensor = self.model(t1, t2)
            prob_map = prob_tensor.squeeze().cpu().numpy()

        binary_mask = (prob_map >= t).astype(np.uint8) * 255
        return prob_map, binary_mask
