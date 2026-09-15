"""
Siamese U-Net Deep Learning Change Detection Architecture.

Twin weight-sharing hierarchical encoder
  → Multi-scale absolute feature difference fusion (|F1 - F2| + Concat)
  → Skip-connected upsampling decoder
  → Pixel-wise Change Probability Map in [0.0, 1.0]
"""

from typing import List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F

from ml.models.base import BaseChangeDetectionModel


class ConvBlock(nn.Module):
    """Double 3x3 Conv with BatchNorm and ReLU."""

    def __init__(self, in_channels: int, out_channels: int, dropout: float = 0.0):
        super().__init__()
        layers = [
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        ]
        if dropout > 0:
            layers.append(nn.Dropout2d(dropout))
        self.conv = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x)


class FeatureDifferenceFusion(nn.Module):
    """
    Fuses multi-scale twin encoder features using absolute difference and concatenation.
    Out = Conv1x1([|F1 - F2|, F1, F2])
    """

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        # Input channels: |F1 - F2| (C) + F1 (C) + F2 (C) = 3C
        self.fusion_conv = nn.Sequential(
            nn.Conv2d(in_channels * 3, out_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, f1: torch.Tensor, f2: torch.Tensor) -> torch.Tensor:
        abs_diff = torch.abs(f1 - f2)
        concat = torch.cat([abs_diff, f1, f2], dim=1)
        return self.fusion_conv(concat)


class DecoderBlock(nn.Module):
    """Upsampling stage with skip-connection concatenation."""

    def __init__(self, in_channels: int, skip_channels: int, out_channels: int, dropout: float = 0.0):
        super().__init__()
        self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
        self.conv = ConvBlock(in_channels // 2 + skip_channels, out_channels, dropout=dropout)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        # Pad if odd dimensions
        if x.shape[-2:] != skip.shape[-2:]:
            diff_y = skip.size(2) - x.size(2)
            diff_x = skip.size(3) - x.size(3)
            x = F.pad(x, [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2])
        x = torch.cat([x, skip], dim=1)
        return self.conv(x)


class SiameseUNetChangeDetector(BaseChangeDetectionModel):
    """
    Siamese U-Net Change Detection Model.
    Accepts two multi-spectral satellite rasters (T1, T2) and outputs pixel-wise change probability.
    """

    def __init__(
        self,
        in_channels: int = 3,
        out_channels: int = 1,
        base_filters: int = 32,
        dropout_rate: float = 0.1,
        model_name: str = "Siamese U-Net v1.0",
        model_version: str = "1.0.0",
    ):
        super().__init__(model_name=model_name, model_version=model_version)
        self.in_channels = in_channels
        self.out_channels = out_channels

        # -------------------------------------------------------------------
        # 1. Twin Weight-Sharing Encoder
        # -------------------------------------------------------------------
        f = base_filters  # e.g., 32
        self.enc1 = ConvBlock(in_channels, f, dropout=0.0)             # (B, f, H, W)
        self.pool1 = nn.MaxPool2d(2)

        self.enc2 = ConvBlock(f, f * 2, dropout=dropout_rate)         # (B, 2f, H/2, W/2)
        self.pool2 = nn.MaxPool2d(2)

        self.enc3 = ConvBlock(f * 2, f * 4, dropout=dropout_rate)     # (B, 4f, H/4, W/4)
        self.pool3 = nn.MaxPool2d(2)

        self.enc4 = ConvBlock(f * 4, f * 8, dropout=dropout_rate)     # (B, 8f, H/8, W/8)
        self.pool4 = nn.MaxPool2d(2)

        # Bottleneck
        self.bottleneck = ConvBlock(f * 8, f * 16, dropout=dropout_rate)  # (B, 16f, H/16, W/16)

        # -------------------------------------------------------------------
        # 2. Multi-Scale Difference Fusion Modules
        # -------------------------------------------------------------------
        self.fuse1 = FeatureDifferenceFusion(f, f)
        self.fuse2 = FeatureDifferenceFusion(f * 2, f * 2)
        self.fuse3 = FeatureDifferenceFusion(f * 4, f * 4)
        self.fuse4 = FeatureDifferenceFusion(f * 8, f * 8)
        self.fuse_bot = FeatureDifferenceFusion(f * 16, f * 16)

        # -------------------------------------------------------------------
        # 3. Skip-Connected Upsampling Decoder
        # -------------------------------------------------------------------
        self.dec4 = DecoderBlock(f * 16, f * 8, f * 8, dropout=dropout_rate)
        self.dec3 = DecoderBlock(f * 8, f * 4, f * 4, dropout=dropout_rate)
        self.dec2 = DecoderBlock(f * 4, f * 2, f * 2, dropout=dropout_rate)
        self.dec1 = DecoderBlock(f * 2, f, f, dropout=0.0)

        # -------------------------------------------------------------------
        # 4. Change Probability Output Head
        # -------------------------------------------------------------------
        self.head = nn.Sequential(
            nn.Conv2d(f, out_channels, kernel_size=1),
            nn.Sigmoid(),
        )

    def _encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Extract multi-scale hierarchical feature maps."""
        e1 = self.enc1(x)
        p1 = self.pool1(e1)

        e2 = self.enc2(p1)
        p2 = self.pool2(e2)

        e3 = self.enc3(p2)
        p3 = self.pool3(e3)

        e4 = self.enc4(p3)
        p4 = self.pool4(e4)

        bot = self.bottleneck(p4)
        return e1, e2, e3, e4, bot

    def forward(self, img1: torch.Tensor, img2: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for change detection.
        Args:
            img1: (B, C, H, W) float32 [0.0, 1.0] for T1
            img2: (B, C, H, W) float32 [0.0, 1.0] for T2
        Returns:
            prob_map: (B, 1, H, W) float32 [0.0, 1.0]
        """
        # 1. Twin Shared-Weight Feature Extraction
        e1_t1, e2_t1, e3_t1, e4_t1, bot_t1 = self._encode(img1)
        e1_t2, e2_t2, e3_t2, e4_t2, bot_t2 = self._encode(img2)

        # 2. Multi-Scale Difference Fusion
        d_bot = self.fuse_bot(bot_t1, bot_t2)
        d4 = self.fuse4(e4_t1, e4_t2)
        d3 = self.fuse3(e3_t1, e3_t2)
        d2 = self.fuse2(e2_t1, e2_t2)
        d1 = self.fuse1(e1_t1, e1_t2)

        # 3. Upsampling Decoder
        x = self.dec4(d_bot, d4)
        x = self.dec3(x, d3)
        x = self.dec2(x, d2)
        x = self.dec1(x, d1)

        # 4. Output Probability Map
        prob_map = self.head(x)
        return prob_map
