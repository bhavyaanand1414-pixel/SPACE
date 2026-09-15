"""
Configuration schema for Siamese U-Net Deep Learning Model & Training.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ModelConfig:
    """Architecture hyperparameters for SiameseUNet."""
    in_channels: int = 3                # RGB or multi-spectral channels
    out_channels: int = 1               # Binary change probability map
    encoder_name: str = "resnet34"      # resnet18, resnet34, resnet50, or custom_conv
    encoder_weights: Optional[str] = None
    feature_difference_mode: str = "abs_diff_concat"  # abs_diff, concat, abs_diff_concat, attention
    decoder_channels: Tuple[int, ...] = (256, 128, 64, 32, 16)
    dropout_rate: float = 0.2
    use_batchnorm: bool = True
    activation: str = "sigmoid"         # Output activation


@dataclass
class TrainingConfig:
    """Training, optimizer, and loss hyperparameters."""
    batch_size: int = 8
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    epochs: int = 50
    image_size: Tuple[int, int] = (256, 256)
    loss_function: str = "focal_dice"  # bce, focal, dice, focal_dice
    focal_alpha: float = 0.25
    focal_gamma: float = 2.0
    dice_smooth: float = 1.0
    early_stopping_patience: int = 10
    lr_reduce_patience: int = 5
    lr_reduce_factor: float = 0.5
    num_workers: int = 2
    save_checkpoint_interval: int = 5
    checkpoint_dir: str = "./ml/checkpoints"


@dataclass
class AugmentationConfig:
    """Data augmentation configuration for satellite imagery pairs."""
    random_horizontal_flip: bool = True
    random_vertical_flip: bool = True
    random_rotate90: bool = True
    color_jitter: bool = True
    brightness_range: Tuple[float, float] = (0.8, 1.2)
    contrast_range: Tuple[float, float] = (0.8, 1.2)
    gaussian_noise_std: float = 0.01


@dataclass
class DeviceConfig:
    """Device selection configuration."""
    preferred_device: str = "auto"     # auto, cuda, mps, cpu
