"""
Base abstract PyTorch class for all Deep Learning Satellite Change Detection Models.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
import torch
import torch.nn as nn

try:
    from app.core.logging import logger
except ImportError:
    import logging
    logger = logging.getLogger("sih1518")


def get_optimal_device(preferred: str = "auto") -> torch.device:
    """
    Automatically select the optimal computing hardware device:
    CUDA (NVIDIA GPU) -> Apple MPS (Apple Silicon GPU) -> CPU.

    Never requires CUDA; runs with native hardware acceleration on macOS MPS or CPU.
    """
    if preferred.lower() == "cuda" and torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info(f"Using NVIDIA CUDA GPU: {torch.cuda.get_device_name(0)}")
        return device

    if preferred.lower() == "mps" and torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("Using Apple Silicon Metal Performance Shaders (MPS) GPU acceleration.")
        return device

    if preferred.lower() == "cpu":
        logger.info("Using standard CPU execution.")
        return torch.device("cpu")

    # Auto discovery
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info(f"Auto-selected CUDA GPU: {torch.cuda.get_device_name(0)}")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("Auto-selected Apple Silicon MPS GPU acceleration.")
    else:
        device = torch.device("cpu")
        logger.info("Auto-selected standard CPU execution.")

    return device


class BaseChangeDetectionModel(nn.Module, ABC):
    """
    Abstract Base Class for multi-temporal deep learning change detection architectures.
    """

    def __init__(self, model_name: str, model_version: str):
        super().__init__()
        self.model_name = model_name
        self.model_version = model_version

    @abstractmethod
    def forward(
        self,
        img1: torch.Tensor,
        img2: torch.Tensor,
    ) -> torch.Tensor:
        """
        Forward pass.
        Args:
            img1: Tensor of shape (B, C, H, W) for observation T1
            img2: Tensor of shape (B, C, H, W) for observation T2
        Returns:
            Change probability map of shape (B, 1, H, W) with values in [0.0, 1.0]
        """
        ...

    def count_parameters(self) -> int:
        """Return total number of trainable model parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def save_checkpoint(
        self,
        path: str,
        optimizer: Optional[torch.optim.Optimizer] = None,
        epoch: int = 0,
        val_loss: float = 0.0,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save weights, optimizer state, and training metadata."""
        checkpoint = {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "epoch": epoch,
            "val_loss": val_loss,
            "metrics": metrics or {},
            "state_dict": self.state_dict(),
            "optimizer_state_dict": optimizer.state_dict() if optimizer else None,
        }
        torch.save(checkpoint, path)
        logger.info(f"Saved model checkpoint to: {path}")

    def load_checkpoint(
        self,
        path: str,
        optimizer: Optional[torch.optim.Optimizer] = None,
        device: Optional[torch.device] = None,
    ) -> Dict[str, Any]:
        """Load weights and training state from checkpoint file."""
        map_location = device or torch.device("cpu")
        checkpoint = torch.load(path, map_location=map_location)
        self.load_state_dict(checkpoint["state_dict"])
        if optimizer and checkpoint.get("optimizer_state_dict"):
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        logger.info(f"Loaded model checkpoint from: {path} (Epoch: {checkpoint.get('epoch', 0)})")
        return checkpoint
