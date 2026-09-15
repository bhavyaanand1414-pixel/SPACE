"""
Dataset Configuration and Schema.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class DatasetConfig:
    """Dataset split and path configuration."""
    name: str = "generic_change_detection"
    root_dir: str = "./data/dataset"
    image_size: Tuple[int, int] = (256, 256)
    in_channels: int = 3
    supported_extensions: Tuple[str, ...] = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
    train_split_dirname: str = "train"
    val_split_dirname: str = "val"
    test_split_dirname: str = "test"
    t1_subfolder: str = "A"
    t2_subfolder: str = "B"
    label_subfolder: str = "label"
    normalize_mean: Tuple[float, ...] = (0.485, 0.456, 0.406)
    normalize_std: Tuple[float, ...] = (0.229, 0.224, 0.225)
