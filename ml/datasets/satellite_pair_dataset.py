"""
PyTorch Dataset and DataLoader pipelines for Multi-Temporal Satellite Pairs.
"""

from typing import Callable, List, Optional, Tuple
import numpy as np
import torch
from torch.utils.data import Dataset


class SatellitePairDataset(Dataset):
    """
    Dataset yielding (img1, img2, label_mask) tuples.
    """

    def __init__(
        self,
        samples: List[Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]],
        transform: Optional[Callable] = None,
        is_train: bool = True,
    ):
        self.samples = samples
        self.transform = transform
        self.is_train = is_train

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        img1, img2, label = self.samples[idx]

        # Convert to float32
        t1 = img1.astype(np.float32)
        t2 = img2.astype(np.float32)

        if label is None:
            mask = np.zeros((1, t1.shape[1], t1.shape[2]), dtype=np.float32)
        elif label.ndim == 2:
            mask = np.expand_dims(label.astype(np.float32), axis=0)
        else:
            mask = label.astype(np.float32)

        # Apply spatial augmentations synchronously across (T1, T2, mask)
        if self.is_train and self.transform is not None:
            t1, t2, mask = self.transform(t1, t2, mask)
        elif self.is_train:
            # Default native spatial augmentations
            if np.random.rand() > 0.5:
                t1 = np.flip(t1, axis=2).copy()  # Horizontal flip
                t2 = np.flip(t2, axis=2).copy()
                mask = np.flip(mask, axis=2).copy()
            if np.random.rand() > 0.5:
                t1 = np.flip(t1, axis=1).copy()  # Vertical flip
                t2 = np.flip(t2, axis=1).copy()
                mask = np.flip(mask, axis=1).copy()

        t1_tensor = torch.from_numpy(t1).float()
        t2_tensor = torch.from_numpy(t2).float()
        mask_tensor = torch.from_numpy(mask).float()

        return t1_tensor, t2_tensor, mask_tensor


def create_synthetic_training_dataset(
    num_samples: int = 16,
    height: int = 128,
    width: int = 128,
    channels: int = 3,
) -> SatellitePairDataset:
    """
    Generate synthetic multi-temporal satellite samples for testing & rapid validation.
    """
    samples = []
    rng = np.random.RandomState(42)

    for i in range(num_samples):
        # Base background terrain
        base = rng.uniform(0.1, 0.7, (channels, height, width)).astype(np.float32)
        img1 = base + rng.normal(0, 0.02, base.shape).astype(np.float32)
        img2 = base + rng.normal(0, 0.02, base.shape).astype(np.float32)
        mask = np.zeros((height, width), dtype=np.float32)

        # Insert 1 or 2 ground change shapes in T2
        if rng.rand() > 0.3:
            rx = rng.randint(20, width - 40)
            ry = rng.randint(20, height - 40)
            rw = rng.randint(15, 30)
            rh = rng.randint(15, 30)
            img2[:, ry : ry + rh, rx : rx + rw] = rng.uniform(0.7, 0.95)
            mask[ry : ry + rh, rx : rx + rw] = 1.0

        img1 = np.clip(img1, 0.0, 1.0)
        img2 = np.clip(img2, 0.0, 1.0)
        samples.append((img1, img2, mask))

    return SatellitePairDataset(samples, is_train=True)
