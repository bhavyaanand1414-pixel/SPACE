"""
Loss functions optimized for class-imbalanced satellite change detection.

Implements:
1. Focal Loss (tackles severe foreground-background pixel imbalance, where change < 5%)
2. Soft Dice Loss (directly maximizes region overlap & F1 boundary accuracy)
3. Combined Focal + Dice Loss
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """
    Binary Focal Loss for severe satellite class imbalance.
    FL(p_t) = -alpha * (1 - p_t)^gamma * log(p_t)
    """

    def __init__(self, alpha: float = 0.25, gamma: float = 2.0, reduction: str = "mean"):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        # pred in [0, 1], target in {0, 1}
        eps = 1e-7
        pred = torch.clamp(pred, eps, 1.0 - eps)

        pt = torch.where(target == 1, pred, 1.0 - pred)
        alpha_t = torch.where(target == 1, self.alpha, 1.0 - self.alpha)

        loss = -alpha_t * torch.pow(1.0 - pt, self.gamma) * torch.log(pt)

        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        return loss


class DiceLoss(nn.Module):
    """
    Differentiable Soft Dice Loss for binary change segmentation.
    DL = 1 - (2 * |X ∩ Y| + smooth) / (|X| + |Y| + smooth)
    """

    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        # Flatten spatial dimensions
        pred_flat = pred.contiguous().view(pred.shape[0], -1)
        target_flat = target.contiguous().view(target.shape[0], -1)

        intersection = (pred_flat * target_flat).sum(dim=1)
        cardinality = pred_flat.sum(dim=1) + target_flat.sum(dim=1)

        dice = (2.0 * intersection + self.smooth) / (cardinality + self.smooth)
        return (1.0 - dice).mean()


class CombinedFocalDiceLoss(nn.Module):
    """
    Weighted combination of Binary Focal Loss and Soft Dice Loss.
    """

    def __init__(
        self,
        focal_alpha: float = 0.25,
        focal_gamma: float = 2.0,
        dice_smooth: float = 1.0,
        focal_weight: float = 0.5,
        dice_weight: float = 0.5,
    ):
        super().__init__()
        self.focal_loss = FocalLoss(alpha=focal_alpha, gamma=focal_gamma)
        self.dice_loss = DiceLoss(smooth=dice_smooth)
        self.focal_weight = focal_weight
        self.dice_weight = dice_weight

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        focal = self.focal_loss(pred, target)
        dice = self.dice_loss(pred, target)
        return self.focal_weight * focal + self.dice_weight * dice
