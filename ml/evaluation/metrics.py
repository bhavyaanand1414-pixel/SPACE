"""
Change Detection Evaluation Metrics.

STRICT PRINCIPLE:
Do not fabricate model metrics. All scores are computed deterministically
from actual prediction masks and ground-truth binary tensors.
"""

from typing import Dict, Union
import numpy as np
import torch


def compute_binary_metrics(
    pred_mask: Union[torch.Tensor, np.ndarray],
    target_mask: Union[torch.Tensor, np.ndarray],
    eps: float = 1e-7,
) -> Dict[str, float]:
    """
    Compute rigorous binary segmentation metrics from real predictions and ground-truth.

    Args:
        pred_mask: Binary prediction array (0 or 1)
        target_mask: Ground-truth binary array (0 or 1)

    Returns:
        Dictionary with:
          - precision
          - recall
          - f1_score / dice
          - iou (Intersection over Union of change class)
          - miou (Mean IoU across change & unchanged classes)
          - accuracy
          - tp, fp, tn, fn pixel counts
    """
    if isinstance(pred_mask, torch.Tensor):
        p = (pred_mask > 0.5).cpu().numpy().astype(bool).flatten()
    else:
        p = (pred_mask > 0.5).astype(bool).flatten()

    if isinstance(target_mask, torch.Tensor):
        t = (target_mask > 0.5).cpu().numpy().astype(bool).flatten()
    else:
        t = (target_mask > 0.5).astype(bool).flatten()

    tp = int(np.sum(p & t))
    fp = int(np.sum(p & (~t)))
    tn = int(np.sum((~p) & (~t)))
    fn = int(np.sum((~p) & t))

    precision = float(tp / (tp + fp + eps)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn + eps)) if (tp + fn) > 0 else 0.0
    f1 = float((2 * precision * recall) / (precision + recall + eps)) if (precision + recall) > 0 else 0.0
    dice = f1  # Dice coefficient is mathematically identical to F1 for binary segmentation

    # Change class IoU
    iou_change = float(tp / (tp + fp + fn + eps)) if (tp + fp + fn) > 0 else 0.0

    # Unchanged background IoU
    iou_unchanged = float(tn / (tn + fp + fn + eps)) if (tn + fp + fn) > 0 else 0.0

    # Mean IoU across both classes
    miou = float((iou_change + iou_unchanged) / 2.0)

    accuracy = float((tp + tn) / (tp + tn + fp + fn + eps))

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "dice": round(dice, 4),
        "iou": round(iou_change, 4),
        "miou": round(miou, 4),
        "accuracy": round(accuracy, 4),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
    }
