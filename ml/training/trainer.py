"""
Training and Validation Engine for Siamese U-Net Change Detection.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

try:
    from app.core.logging import logger
except ImportError:
    import logging
    logger = logging.getLogger("sih1518")
from ml.configs.config import TrainingConfig
from ml.evaluation.metrics import compute_binary_metrics
from ml.models.base import BaseChangeDetectionModel, get_optimal_device
from ml.models.losses import CombinedFocalDiceLoss


class SiameseTrainer:
    """
    Orchestrates training, validation, metric tracking, and checkpointing for SiameseUNet.
    """

    def __init__(
        self,
        model: BaseChangeDetectionModel,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        config: Optional[TrainingConfig] = None,
        device: Optional[torch.device] = None,
    ):
        self.config = config or TrainingConfig()
        self.device = device or get_optimal_device()
        self.model = model.to(self.device)
        self.train_loader = train_loader
        self.val_loader = val_loader

        # Loss & Optimizer
        self.criterion = CombinedFocalDiceLoss(
            focal_alpha=self.config.focal_alpha,
            focal_gamma=self.config.focal_gamma,
            dice_smooth=self.config.dice_smooth,
        )
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode="min",
            factor=self.config.lr_reduce_factor,
            patience=self.config.lr_reduce_patience,
        )

        # Checkpoint directory
        self.checkpoint_dir = Path(self.config.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.best_val_loss = float("inf")
        self.best_f1 = 0.0

    def train_epoch(self, epoch: int) -> Dict[str, float]:
        """Run one training epoch."""
        self.model.train()
        total_loss = 0.0
        all_preds = []
        all_targets = []

        for batch_idx, (t1, t2, mask) in enumerate(self.train_loader):
            t1 = t1.to(self.device)
            t2 = t2.to(self.device)
            mask = mask.to(self.device)

            self.optimizer.zero_grad()
            prob_map = self.model(t1, t2)
            loss = self.criterion(prob_map, mask)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()

            total_loss += loss.item()
            all_preds.append(prob_map.detach().cpu())
            all_targets.append(mask.detach().cpu())

        avg_loss = total_loss / max(1, len(self.train_loader))
        preds_cat = torch.cat(all_preds, dim=0)
        targets_cat = torch.cat(all_targets, dim=0)
        metrics = compute_binary_metrics(preds_cat, targets_cat)
        metrics["loss"] = round(avg_loss, 4)
        return metrics

    def validate(self) -> Dict[str, float]:
        """Run validation evaluation."""
        if not self.val_loader:
            return {"val_loss": 0.0, "f1_score": 0.0, "iou": 0.0}

        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for t1, t2, mask in self.val_loader:
                t1 = t1.to(self.device)
                t2 = t2.to(self.device)
                mask = mask.to(self.device)

                prob_map = self.model(t1, t2)
                loss = self.criterion(prob_map, mask)

                total_loss += loss.item()
                all_preds.append(prob_map.cpu())
                all_targets.append(mask.cpu())

        avg_loss = total_loss / max(1, len(self.val_loader))
        preds_cat = torch.cat(all_preds, dim=0)
        targets_cat = torch.cat(all_targets, dim=0)
        metrics = compute_binary_metrics(preds_cat, targets_cat)
        metrics["val_loss"] = round(avg_loss, 4)
        return metrics

    def train(self, num_epochs: Optional[int] = None) -> Dict[str, Any]:
        """Execute full training loop with early stopping and checkpointing."""
        epochs = num_epochs or self.config.epochs
        history: Dict[str, list] = {"train_loss": [], "val_loss": [], "f1_score": [], "iou": []}
        patience_counter = 0

        logger.info(f"Starting Siamese U-Net training for {epochs} epochs on {self.device}")

        for epoch in range(1, epochs + 1):
            train_metrics = self.train_epoch(epoch)
            val_metrics = self.validate() if self.val_loader else train_metrics

            val_loss = val_metrics.get("val_loss", train_metrics["loss"])
            self.scheduler.step(val_loss)

            history["train_loss"].append(train_metrics["loss"])
            history["val_loss"].append(val_loss)
            history["f1_score"].append(val_metrics.get("f1_score", 0.0))
            history["iou"].append(val_metrics.get("iou", 0.0))

            logger.info(
                f"Epoch [{epoch}/{epochs}] "
                f"Train Loss: {train_metrics['loss']:.4f} | "
                f"Val Loss: {val_loss:.4f} | "
                f"F1: {val_metrics.get('f1_score', 0):.4f} | "
                f"IoU: {val_metrics.get('iou', 0):.4f}"
            )

            # Checkpoint on best validation loss
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                best_ckpt_path = self.checkpoint_dir / "siamese_unet_best.pt"
                self.model.save_checkpoint(
                    str(best_ckpt_path),
                    optimizer=self.optimizer,
                    epoch=epoch,
                    val_loss=val_loss,
                    metrics=val_metrics,
                )
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= self.config.early_stopping_patience:
                    logger.info(f"Early stopping triggered at epoch {epoch}")
                    break

        return history
