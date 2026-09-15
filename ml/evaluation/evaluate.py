"""
SIH1518 Evaluation Pipeline — Siamese U-Net Benchmark Evaluation on Test Split.

STRICT PRINCIPLE:
Never invent evaluation scores. All metrics are computed strictly against ground-truth masks.

Usage:
  python ml/evaluation/evaluate.py --checkpoint ./ml/checkpoints/siamese_unet_best.pt --dataset-dir ./data/LEVIR-CD
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.datasets.benchmark_loader import BenchmarkCDDataset, DatasetNotFoundError
from ml.datasets.satellite_pair_dataset import create_synthetic_training_dataset
from ml.evaluation.metrics import compute_binary_metrics
from ml.models.base import get_optimal_device
from ml.models.siamese_unet import SiameseUNetChangeDetector


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Siamese U-Net on Test Dataset")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to model checkpoint (.pt)")
    parser.add_argument("--dataset-dir", type=str, default="./data/LEVIR-CD", help="Path to benchmark dataset root")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic dataset for evaluation smoke test")
    parser.add_argument("--threshold", type=float, default=0.5, help="Classification decision threshold")
    parser.add_argument("--batch-size", type=int, default=4, help="Evaluation batch size")
    parser.add_argument("--device", type=str, default="auto", help="Target device")
    parser.add_argument("--output-json", type=str, default="./ml/evaluation/evaluation_results.json")
    return parser.parse_args()


def main():
    args = parse_args()
    device = get_optimal_device(preferred=args.device)

    print("=" * 70)
    print("🛰️  SIH1518: SIAMESE U-NET BENCHMARK TEST EVALUATION")
    print("=" * 70)
    print(f"• Target Device     : {device}")
    print(f"• Model Checkpoint  : {args.checkpoint}")
    print(f"• Decision Cutoff   : {args.threshold}")
    print("=" * 70)

    # 1. Load Dataset
    if args.synthetic:
        print("ℹ️  Evaluating on synthetic test partition.")
        test_dataset = create_synthetic_training_dataset(num_samples=8, height=128, width=128)
    else:
        try:
            print(f"📂 Loading test partition from: {args.dataset_dir}/test")
            test_dataset = BenchmarkCDDataset(root_dir=args.dataset_dir, split="test")
            print(f"✅ Loaded {len(test_dataset)} test image pairs.")
        except DatasetNotFoundError as exc:
            print(exc)
            sys.exit(1)

    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    # 2. Load Model & Weights
    model = SiameseUNetChangeDetector(in_channels=3, base_filters=16)
    if Path(args.checkpoint).is_file():
        model.load_checkpoint(args.checkpoint, device=device)
    else:
        print(f"⚠️ Checkpoint '{args.checkpoint}' not found on disk. Evaluating with initialized model.")

    model = model.to(device)
    model.eval()

    # 3. Inference & Accumulation
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for t1, t2, mask in test_loader:
            t1 = t1.to(device)
            t2 = t2.to(device)
            prob_map = model(t1, t2)
            binary_pred = (prob_map >= args.threshold).float()
            all_preds.append(binary_pred.cpu())
            all_targets.append(mask.cpu())

    preds_cat = torch.cat(all_preds, dim=0)
    targets_cat = torch.cat(all_targets, dim=0)

    # 4. Strict Metrics Calculation
    metrics = compute_binary_metrics(preds_cat, targets_cat)

    print("\n" + "=" * 70)
    print("📊 BENCHMARK TEST EVALUATION RESULTS")
    print("=" * 70)
    print(f"  • Precision (Positive Predictive Value) : {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
    print(f"  • Recall (Sensitivity / Detection Rate) : {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
    print(f"  • F1 Score (Harmonic Mean)              : {metrics['f1_score']:.4f} ({metrics['f1_score']*100:.2f}%)")
    print(f"  • Dice Similarity Coefficient           : {metrics['dice']:.4f}")
    print(f"  • IoU (Intersection over Union)         : {metrics['iou']:.4f} ({metrics['iou']*100:.2f}%)")
    print(f"  • mIoU (Mean Class IoU)                 : {metrics['miou']:.4f} ({metrics['miou']*100:.2f}%)")
    print(f"  • Overall Pixel Accuracy                : {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print("-" * 70)
    print(f"  • Confusion Matrix : TP={metrics['true_positives']:,} | FP={metrics['false_positives']:,} | TN={metrics['true_negatives']:,} | FN={metrics['false_negatives']:,}")
    print("=" * 70)

    # 5. Save Output JSON
    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results_payload = {
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "checkpoint": str(args.checkpoint),
        "threshold": args.threshold,
        "test_samples": len(test_dataset),
        "metrics": metrics,
    }
    with open(out_path, "w") as f:
        json.dump(results_payload, f, indent=2)

    print(f"📁 Evaluation results written to: {out_path.resolve()}\n")


if __name__ == "__main__":
    main()
