"""
Unit tests for PyTorch Siamese U-Net Deep Learning Model, Losses, Trainer, and Inference (Phase 10).
"""

import os
import pytest
import numpy as np
import torch
from torch.utils.data import DataLoader

from ml.configs.config import TrainingConfig
from ml.datasets.satellite_pair_dataset import create_synthetic_training_dataset
from ml.evaluation.metrics import compute_binary_metrics
from ml.inference.predictor import SiamesePredictor
from ml.models.base import get_optimal_device
from ml.models.losses import CombinedFocalDiceLoss, DiceLoss, FocalLoss
from ml.models.siamese_unet import SiameseUNetChangeDetector
from ml.training.trainer import SiameseTrainer
from app.ml.siamese_unet import SiameseUNetDetector


# ─── 1. Model Forward Pass & Tensor Shapes ────────────────────────────────────


def test_siamese_unet_forward_shape():
    """Verify SiameseUNet processes multi-temporal pair and outputs (B, 1, H, W)."""
    device = get_optimal_device()
    model = SiameseUNetChangeDetector(in_channels=3, base_filters=16).to(device)

    b, c, h, w = 2, 3, 64, 64
    t1 = torch.rand(b, c, h, w, device=device)
    t2 = torch.rand(b, c, h, w, device=device)

    out = model(t1, t2)

    assert out.shape == (b, 1, h, w)
    assert out.min() >= 0.0
    assert out.max() <= 1.0


# ─── 2. Loss Functions ────────────────────────────────────────────────────────


def test_loss_functions():
    """Verify Focal, Dice, and Combined loss computation."""
    pred = torch.tensor([[[[0.9, 0.1], [0.8, 0.2]]]], dtype=torch.float32)
    target = torch.tensor([[[[1.0, 0.0], [1.0, 0.0]]]], dtype=torch.float32)

    focal = FocalLoss()(pred, target)
    dice = DiceLoss()(pred, target)
    combined = CombinedFocalDiceLoss()(pred, target)

    assert isinstance(focal.item(), float)
    assert isinstance(dice.item(), float)
    assert isinstance(combined.item(), float)
    assert combined.item() > 0.0


# ─── 3. Hardware Device Discovery ─────────────────────────────────────────────


def test_optimal_device_selection():
    """Verify device selection prioritizes CUDA -> MPS -> CPU without crashing."""
    dev_auto = get_optimal_device("auto")
    dev_cpu = get_optimal_device("cpu")

    assert isinstance(dev_auto, torch.device)
    assert dev_cpu.type == "cpu"


# ─── 4. Checkpoint Serialization ──────────────────────────────────────────────


def test_checkpoint_save_and_load(tmp_path):
    """Verify saving and loading model weights state dict."""
    ckpt_file = str(tmp_path / "test_model.pt")
    model = SiameseUNetChangeDetector(in_channels=3, base_filters=16)

    # Save
    model.save_checkpoint(ckpt_file, epoch=5, val_loss=0.25)
    assert os.path.isfile(ckpt_file)

    # Load
    new_model = SiameseUNetChangeDetector(in_channels=3, base_filters=16)
    ckpt = new_model.load_checkpoint(ckpt_file)
    assert ckpt["epoch"] == 5
    assert ckpt["val_loss"] == 0.25


# ─── 5. Evaluation Metrics & Trainer ──────────────────────────────────────────


def test_metrics_no_fabrication():
    """Verify binary metrics are calculated accurately without fabrication."""
    pred = np.array([[1, 0], [1, 1]])
    target = np.array([[1, 0], [0, 1]])

    metrics = compute_binary_metrics(pred, target)

    assert metrics["true_positives"] == 2
    assert metrics["false_positives"] == 1
    assert metrics["true_negatives"] == 1
    assert metrics["false_negatives"] == 0
    assert metrics["recall"] == 1.0
    assert metrics["precision"] == round(2 / 3, 4)


def test_trainer_mini_epoch(tmp_path):
    """Run 1 training epoch on synthetic dataset."""
    dataset = create_synthetic_training_dataset(num_samples=8, height=64, width=64)
    loader = DataLoader(dataset, batch_size=4)

    model = SiameseUNetChangeDetector(in_channels=3, base_filters=8)
    config = TrainingConfig(epochs=1, batch_size=4, checkpoint_dir=str(tmp_path))

    trainer = SiameseTrainer(model=model, train_loader=loader, config=config)
    metrics = trainer.train_epoch(epoch=1)

    assert "loss" in metrics
    assert "f1_score" in metrics


# ─── 6. Backend Siamese Detector Wrapper ──────────────────────────────────────


def test_backend_siamese_detector_wrapper(tmp_path):
    """Verify backend wrapper executes Siamese inference and produces GeoJSON polygons."""
    # Fast train on 4 samples with a distinct change block
    dataset = create_synthetic_training_dataset(num_samples=8, height=64, width=64)
    loader = DataLoader(dataset, batch_size=4)

    model = SiameseUNetChangeDetector(in_channels=3, base_filters=16)
    trainer = SiameseTrainer(
        model=model,
        train_loader=loader,
        config=TrainingConfig(epochs=2, batch_size=4, checkpoint_dir=str(tmp_path)),
    )
    trainer.train(num_epochs=2)

    ckpt_path = str(tmp_path / "siamese_unet_best.pt")
    detector = SiameseUNetDetector(checkpoint_path=ckpt_path, confidence_threshold=0.4, base_filters=16)

    h, w = 64, 64
    img1 = np.full((3, h, w), 0.2, dtype=np.float32)
    img2 = np.full((3, h, w), 0.2, dtype=np.float32)
    img2[:, 15:45, 15:45] = 0.95  # Clear bright change

    result = detector.detect_change(img1, img2, confidence_threshold=0.4)

    assert result.model_name == "Siamese U-Net Deep Learning"
    assert result.total_area_m2 > 0.0
    assert result.probability_map.shape == (h, w)
