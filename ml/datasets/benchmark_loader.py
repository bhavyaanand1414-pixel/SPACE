"""
Standardized Remote Sensing Change Detection Benchmark Dataset Loader (LEVIR-CD, WHU-CD, DSIFN-CD).

Handles train, validation, and test splits with strict dataset directory structure validation.
Fails gracefully with actionable instructions if dataset is missing.
"""

import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

from ml.configs.dataset_config import DatasetConfig


class DatasetNotFoundError(FileNotFoundError):
    """Raised when the specified dataset path is missing or invalid."""
    pass


class BenchmarkCDDataset(Dataset):
    """
    Standardized dataset for multi-temporal change detection benchmarks.
    Loads paired files from:
      root_dir / split / A (T1 image)
      root_dir / split / B (T2 image)
      root_dir / split / label (Ground-truth mask)
    """

    def __init__(
        self,
        root_dir: str,
        split: str = "train",
        config: Optional[DatasetConfig] = None,
        transform: Optional[Callable] = None,
    ):
        self.root_path = Path(root_dir).resolve()
        self.split = split.lower()
        self.config = config or DatasetConfig()
        self.transform = transform

        self.split_dir = self.root_path / self.split
        self.t1_dir = self.split_dir / self.config.t1_subfolder
        self.t2_dir = self.split_dir / self.config.t2_subfolder
        self.label_dir = self.split_dir / self.config.label_subfolder

        self._validate_directory_structure()
        self.samples: List[Tuple[Path, Path, Optional[Path]]] = self._collect_paired_files()

    def _validate_directory_structure(self) -> None:
        """Validate that all required subdirectories exist."""
        if not self.root_path.exists():
            raise DatasetNotFoundError(
                f"\n❌ DATASET NOT FOUND AT: '{self.root_path}'\n\n"
                f"Please ensure you have prepared a benchmark change detection dataset.\n"
                f"Expected directory structure:\n"
                f"  {self.root_path}/\n"
                f"    ├── train/ (with 'A', 'B', 'label' subfolders)\n"
                f"    ├── val/   (with 'A', 'B', 'label' subfolders)\n"
                f"    └── test/  (with 'A', 'B', 'label' subfolders)\n\n"
                f"To train with a synthetic demo dataset instead, pass '--synthetic'.\n"
                f"Refer to docs/dataset.md for download links to LEVIR-CD, WHU-CD, and DSIFN-CD."
            )

        if not self.split_dir.exists():
            raise DatasetNotFoundError(
                f"\n❌ Split directory '{self.split}' not found at: '{self.split_dir}'\n"
                f"Expected '{self.root_path}/{self.split}/' containing subfolders 'A', 'B', and 'label'."
            )

        if not self.t1_dir.exists() or not self.t2_dir.exists():
            raise DatasetNotFoundError(
                f"\n❌ Missing required subfolders in '{self.split_dir}'.\n"
                f"Must have:\n"
                f"  - '{self.t1_dir}' (Observation T1)\n"
                f"  - '{self.t2_dir}' (Observation T2)\n"
            )

    def _collect_paired_files(self) -> List[Tuple[Path, Path, Optional[Path]]]:
        """Collect matching (T1, T2, label) filenames."""
        valid_exts = set(self.config.supported_extensions)
        t1_files = sorted([f for f in self.t1_dir.iterdir() if f.suffix.lower() in valid_exts])

        if len(t1_files) == 0:
            raise DatasetNotFoundError(
                f"\n❌ No valid image files found in '{self.t1_dir}'. Supported formats: {valid_exts}"
            )

        pairs = []
        for t1_p in t1_files:
            t2_p = self.t2_dir / t1_p.name
            if not t2_p.exists():
                # Try matching without extension
                t2_candidates = list(self.t2_dir.glob(f"{t1_p.stem}.*"))
                if t2_candidates:
                    t2_p = t2_candidates[0]
                else:
                    continue  # Unmatched file

            label_p = self.label_dir / t1_p.name if self.label_dir.exists() else None
            if label_p and not label_p.exists():
                label_candidates = list(self.label_dir.glob(f"{t1_p.stem}.*"))
                label_p = label_candidates[0] if label_candidates else None

            pairs.append((t1_p, t2_p, label_p))

        return pairs

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        t1_path, t2_path, label_path = self.samples[idx]

        # Read images using OpenCV (RGB)
        img1 = cv2.imread(str(t1_path), cv2.IMREAD_COLOR)
        img2 = cv2.imread(str(t2_path), cv2.IMREAD_COLOR)

        if img1 is None or img2 is None:
            raise IOError(f"Failed to read image pair: {t1_path} or {t2_path}")

        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

        if label_path and label_path.exists():
            label = cv2.imread(str(label_path), cv2.IMREAD_GRAYSCALE)
            if label is not None:
                mask = (label > 127).astype(np.float32)
            else:
                mask = np.zeros((img1.shape[0], img1.shape[1]), dtype=np.float32)
        else:
            mask = np.zeros((img1.shape[0], img1.shape[1]), dtype=np.float32)

        # Transpose to (C, H, W)
        t1_tensor = torch.from_numpy(img1.transpose(2, 0, 1)).float()
        t2_tensor = torch.from_numpy(img2.transpose(2, 0, 1)).float()
        mask_tensor = torch.from_numpy(mask).unsqueeze(0).float()

        return t1_tensor, t2_tensor, mask_tensor
