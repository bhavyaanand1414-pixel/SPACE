import os
from pathlib import Path
from typing import Any, Dict, Optional
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import open_clip

try:
    from app.core.logging import logger
except ImportError:
    import logging
    logger = logging.getLogger("sih1518")

class CLIPTrainer:
    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader],
        device: torch.device,
        learning_rate: float = 1e-5,
        weight_decay: float = 0.2,
        checkpoint_dir: str = "./ml/checkpoints/clip_finetuned",
        mixed_precision: bool = True
    ):
        self.model = model.to(device)
        self.device = device
        self.train_loader = train_loader
        self.val_loader = val_loader
        
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Loss & Optimizer
        # CLIP uses symmetric CrossEntropyLoss on logit matrix
        self.loss_img = nn.CrossEntropyLoss()
        self.loss_txt = nn.CrossEntropyLoss()
        
        # We need to optimize model parameters. Some may be frozen depending on setup,
        # but here we assume all parameters that require_grad are optimized.
        params = [p for p in self.model.parameters() if p.requires_grad]
        self.optimizer = torch.optim.AdamW(
            params,
            lr=learning_rate,
            weight_decay=weight_decay,
        )
        
        self.scaler = torch.cuda.amp.GradScaler(enabled=mixed_precision and device.type == "cuda")
        self.mixed_precision = mixed_precision

        self.best_val_loss = float("inf")
        self.start_epoch = 1

    def load_checkpoint(self, checkpoint_path: str):
        if not os.path.exists(checkpoint_path):
            logger.warning(f"Checkpoint {checkpoint_path} not found.")
            return
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.start_epoch = checkpoint["epoch"] + 1
        self.best_val_loss = checkpoint.get("best_val_loss", float("inf"))
        if self.scaler and "scaler_state_dict" in checkpoint:
            self.scaler.load_state_dict(checkpoint["scaler_state_dict"])
        logger.info(f"Loaded checkpoint from {checkpoint_path} (epoch {checkpoint['epoch']})")

    def _compute_loss(self, image_features, text_features, logit_scale):
        # Normalized features
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        # Cosine similarity as logits
        logits_per_image = logit_scale * image_features @ text_features.T
        logits_per_text = logit_scale * text_features @ image_features.T

        labels = torch.arange(logits_per_image.shape[0], device=self.device, dtype=torch.long)
        loss = (self.loss_img(logits_per_image, labels) + self.loss_txt(logits_per_text, labels)) / 2
        return loss

    def train_epoch(self, epoch: int) -> Dict[str, float]:
        self.model.train()
        total_loss = 0.0

        for batch_idx, (images, texts) in enumerate(self.train_loader):
            images = images.to(self.device)
            texts = texts.to(self.device)

            self.optimizer.zero_grad()
            
            with torch.cuda.amp.autocast(enabled=self.mixed_precision and self.device.type == "cuda"):
                image_features, text_features, logit_scale = self.model(images, texts)
                loss = self._compute_loss(image_features, text_features, logit_scale)

            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()

            total_loss += loss.item()

        avg_loss = total_loss / max(1, len(self.train_loader))
        return {"loss": round(avg_loss, 4)}

    def validate(self) -> Dict[str, float]:
        if not self.val_loader:
            return {"val_loss": 0.0}

        self.model.eval()
        total_loss = 0.0

        with torch.no_grad():
            for images, texts in self.val_loader:
                images = images.to(self.device)
                texts = texts.to(self.device)

                with torch.cuda.amp.autocast(enabled=self.mixed_precision and self.device.type == "cuda"):
                    image_features, text_features, logit_scale = self.model(images, texts)
                    loss = self._compute_loss(image_features, text_features, logit_scale)

                total_loss += loss.item()

        avg_loss = total_loss / max(1, len(self.val_loader))
        return {"val_loss": round(avg_loss, 4)}

    def train(self, epochs: int) -> Dict[str, Any]:
        history = {"train_loss": [], "val_loss": []}
        
        logger.info(f"Starting CLIP fine-tuning for {epochs} epochs on {self.device}")
        
        for epoch in range(self.start_epoch, epochs + 1):
            train_metrics = self.train_epoch(epoch)
            val_metrics = self.validate() if self.val_loader else train_metrics
            
            val_loss = val_metrics.get("val_loss", train_metrics["loss"])
            
            history["train_loss"].append(train_metrics["loss"])
            history["val_loss"].append(val_loss)
            
            logger.info(
                f"Epoch [{epoch}/{epochs}] "
                f"Train Loss: {train_metrics['loss']:.4f} | "
                f"Val Loss: {val_loss:.4f}"
            )
            
            # Save best checkpoint
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                best_ckpt_path = self.checkpoint_dir / "clip_best.pt"
                state = {
                    "epoch": epoch,
                    "model_state_dict": self.model.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "best_val_loss": self.best_val_loss,
                }
                if self.scaler:
                    state["scaler_state_dict"] = self.scaler.state_dict()
                torch.save(state, best_ckpt_path)

        return history
