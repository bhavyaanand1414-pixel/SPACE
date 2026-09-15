"""
Unit & Integration Tests for Phase 11: Dataset Pipeline, train.py, evaluate.py, and infer.py.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
import cv2
import numpy as np
import pytest

from ml.datasets.benchmark_loader import BenchmarkCDDataset, DatasetNotFoundError


def _create_mock_dataset_on_disk(root_dir: Path):
    """Create minimal directory structure with train/val/test splits."""
    for split in ["train", "val", "test"]:
        split_path = root_dir / split
        for sub in ["A", "B", "label"]:
            (split_path / sub).mkdir(parents=True, exist_ok=True)

        for i in range(3):
            fn = f"sample_{i}.png"
            img1 = np.full((64, 64, 3), 50 + i * 20, dtype=np.uint8)
            img2 = np.full((64, 64, 3), 50 + i * 20, dtype=np.uint8)
            mask = np.zeros((64, 64), dtype=np.uint8)

            # Alter region
            img2[10:30, 10:30] = 220
            mask[10:30, 10:30] = 255

            cv2.imwrite(str(split_path / "A" / fn), img1)
            cv2.imwrite(str(split_path / "B" / fn), img2)
            cv2.imwrite(str(split_path / "label" / fn), mask)


def test_dataset_not_found_graceful_error():
    """Verify that non-existent dataset paths raise clean DatasetNotFoundError with instructions."""
    with pytest.raises(DatasetNotFoundError) as exc_info:
        BenchmarkCDDataset(root_dir="./non_existent_satellite_data_dir_123", split="train")

    assert "DATASET NOT FOUND AT" in str(exc_info.value)
    assert "Expected directory structure" in str(exc_info.value)


def test_benchmark_dataset_loader(tmp_path):
    """Verify BenchmarkCDDataset accurately loads paired images and binary masks from disk."""
    dataset_dir = tmp_path / "test_cd_dataset"
    _create_mock_dataset_on_disk(dataset_dir)

    ds_train = BenchmarkCDDataset(root_dir=str(dataset_dir), split="train")
    assert len(ds_train) == 3

    t1, t2, mask = ds_train[0]
    assert t1.shape == (3, 64, 64)
    assert t2.shape == (3, 64, 64)
    assert mask.shape == (1, 64, 64)
    assert mask.max() == 1.0


def test_train_cli_pipeline(tmp_path):
    """Test train.py end-to-end execution and artifact generation."""
    ckpt_dir = tmp_path / "checkpoints"
    cmd = [
        sys.executable,
        "ml/training/train.py",
        "--synthetic",
        "--epochs", "2",
        "--batch-size", "4",
        "--checkpoint-dir", str(ckpt_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).resolve().parent.parent.parent))
    assert res.returncode == 0
    assert "TRAINING SUCCESSFULLY COMPLETED" in res.stdout

    # Verify all 4 required artifacts were saved
    assert (ckpt_dir / "siamese_unet_best.pt").is_file()
    assert (ckpt_dir / "config.json").is_file()
    assert (ckpt_dir / "metrics.json").is_file()
    assert (ckpt_dir / "model_version.json").is_file()

    with open(ckpt_dir / "metrics.json") as f:
        metrics_data = json.load(f)
        assert "final_f1_score" in metrics_data


def test_evaluate_cli_pipeline(tmp_path):
    """Test evaluate.py calculation of mIoU, IoU, F1, Dice, Precision, Recall."""
    ckpt_dir = tmp_path / "checkpoints"
    ckpt_path = ckpt_dir / "siamese_unet_best.pt"

    # Train fast 1-epoch model
    train_cmd = [
        sys.executable,
        "ml/training/train.py",
        "--synthetic",
        "--epochs", "1",
        "--batch-size", "4",
        "--checkpoint-dir", str(ckpt_dir),
    ]
    subprocess.run(train_cmd, capture_output=True, text=True, cwd=str(Path(__file__).resolve().parent.parent.parent))

    out_json = tmp_path / "eval_results.json"
    eval_cmd = [
        sys.executable,
        "ml/evaluation/evaluate.py",
        "--checkpoint", str(ckpt_path),
        "--synthetic",
        "--output-json", str(out_json),
    ]
    eval_res = subprocess.run(eval_cmd, capture_output=True, text=True, cwd=str(Path(__file__).resolve().parent.parent.parent))
    assert eval_res.returncode == 0
    assert "BENCHMARK TEST EVALUATION RESULTS" in eval_res.stdout

    assert out_json.is_file()
    with open(out_json) as f:
        eval_data = json.load(f)
        m = eval_data["metrics"]
        assert "miou" in m
        assert "f1_score" in m
        assert "dice" in m
        assert "precision" in m
        assert "recall" in m


def test_infer_cli_pipeline(tmp_path):
    """Test infer.py CLI inference on image pair."""
    t1_p = tmp_path / "t1.png"
    t2_p = tmp_path / "t2.png"
    out_mask_p = tmp_path / "mask_out.png"

    cv2.imwrite(str(t1_p), np.full((64, 64, 3), 40, dtype=np.uint8))
    cv2.imwrite(str(t2_p), np.full((64, 64, 3), 200, dtype=np.uint8))

    cmd = [
        sys.executable,
        "ml/inference/infer.py",
        "--t1", str(t1_p),
        "--t2", str(t2_p),
        "--checkpoint", "none",
        "--output-mask", str(out_mask_p),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).resolve().parent.parent.parent))
    assert res.returncode == 0
    assert "INFERENCE COMPLETE" in res.stdout
    assert out_mask_p.is_file()
