"""
SIH1518 Training Pipeline — Siamese U-Net Satellite Change Detection.

Saves:
  - Checkpoint (.pt)
  - Training configuration (config.json)
  - Final metrics (metrics.json)
  - Model version metadata (model_version.json)

Usage:
  # With real dataset:
  python ml/training/train.py --dataset-dir ./data/LEVIR-CD --epochs 50 --batch-size 8

  # With synthetic demo dataset (for smoke tests / development):
  python ml/training/train.py --synthetic --epochs 5 --batch-size 4
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import torch
from torch.utils.data import DataLoader

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.configs.config import TrainingConfig
from ml.datasets.benchmark_loader import BenchmarkCDDataset, DatasetNotFoundError
from ml.datasets.satellite_pair_dataset import create_synthetic_training_dataset
from ml.models.base import get_optimal_device
from ml.models.siamese_unet import SiameseUNetChangeDetector
from ml.training.trainer import SiameseTrainer


def parse_args():
    parser = argparse.ArgumentParser(description="Train Siamese U-Net Change Detector")
    parser.add_argument("--dataset-dir", type=str, default="./data/LEVIR-CD", help="Path to benchmark dataset root")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic dataset for quick testing")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--device", type=str, default="auto", help="Device: auto, cuda, mps, cpu")
    parser.add_argument("--checkpoint-dir", type=str, default="./ml/checkpoints", help="Output directory")
    parser.add_argument("--model-version", type=str, default="1.0.0", help="Model version identifier")
    return parser.parse_args()


def main():
    args = parse_args()
    device = get_optimal_device(preferred=args.device)
    ckpt_dir = Path(args.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("🛰️  SIH1518: SIAMESE U-NET SATELLITE CHANGE DETECTION TRAINING")
    print("=" * 70)
    print(f"• Target Device     : {device}")
    print(f"• Target Epochs     : {args.epochs}")
    print(f"• Batch Size        : {args.batch_size}")
    print(f"• Learning Rate     : {args.lr}")
    print(f"• Model Version     : {args.model_version}")
    print(f"• Checkpoint Dir    : {ckpt_dir.resolve()}")
    print("=" * 70)

    # 1. Load Data
    if args.synthetic:
        print("ℹ️  Using synthetic dataset for development / smoke testing.")
        train_dataset = create_synthetic_training_dataset(num_samples=16, height=128, width=128)
        val_dataset = create_synthetic_training_dataset(num_samples=8, height=128, width=128)
    else:
        try:
            print(f"📂 Loading benchmark dataset from: {args.dataset_dir}")
            train_dataset = BenchmarkCDDataset(root_dir=args.dataset_dir, split="train")
            val_dataset = BenchmarkCDDataset(root_dir=args.dataset_dir, split="val")
            print(f"✅ Loaded {len(train_dataset)} training pairs and {len(val_dataset)} validation pairs.")
        except DatasetNotFoundError as exc:
            print(exc)
            sys.exit(1)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)

    # 2. Instantiate Model & Config
    model = SiameseUNetChangeDetector(in_channels=3, base_filters=16, model_version=args.model_version)
    config = TrainingConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        checkpoint_dir=str(ckpt_dir),
    )

    trainer = SiameseTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config=config,
        device=device,
    )

    # 3. Execute Training Loop
    history = trainer.train()

    # 4. Save Final Artifacts
    # Save Config
    config_path = ckpt_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(
            {
                "model_name": model.model_name,
                "model_version": args.model_version,
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "learning_rate": args.lr,
                "loss_function": config.loss_function,
                "device": str(device),
                "dataset_source": "synthetic" if args.synthetic else str(args.dataset_dir),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            f,
            indent=2,
        )

    # Save Metrics
    metrics_path = ckpt_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(
            {
                "best_val_loss": trainer.best_val_loss,
                "history": history,
                "final_train_loss": history["train_loss"][-1] if history["train_loss"] else 0.0,
                "final_val_loss": history["val_loss"][-1] if history["val_loss"] else 0.0,
                "final_f1_score": history["f1_score"][-1] if history["f1_score"] else 0.0,
                "final_iou": history["iou"][-1] if history["iou"] else 0.0,
            },
            f,
            indent=2,
        )

    # Save Model Version Metadata
    version_path = ckpt_dir / "model_version.json"
    with open(version_path, "w") as f:
        json.dump(
            {
                "version": args.model_version,
                "model_name": "Siamese U-Net",
                "framework": "PyTorch",
                "torch_version": torch.__version__,
                "trainable_parameters": model.count_parameters(),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            f,
            indent=2,
        )

    print("\n" + "=" * 70)
    print("🎉 TRAINING SUCCESSFULLY COMPLETED")
    print(f"• Best Validation Loss : {trainer.best_val_loss:.4f}")
    print(f"• Saved Checkpoint     : {ckpt_dir / 'siamese_unet_best.pt'}")
    print(f"• Saved Config         : {config_path}")
    print(f"• Saved Metrics        : {metrics_path}")
    print(f"• Saved Model Version  : {version_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
