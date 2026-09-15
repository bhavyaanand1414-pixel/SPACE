"""
SIH1518 Inference Pipeline — Siamese U-Net Satellite Change Detection on Image Pairs.

Usage:
  python ml/inference/infer.py --t1 /path/to/t1.png --t2 /path/to/t2.png --checkpoint ./ml/checkpoints/siamese_unet_best.pt
"""

import argparse
import sys
from pathlib import Path
import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.inference.predictor import SiamesePredictor
from ml.models.base import get_optimal_device


def parse_args():
    parser = argparse.ArgumentParser(description="Run Siamese U-Net Inference on Image Pair")
    parser.add_argument("--t1", type=str, required=True, help="Path to observation T1 image (PNG, JPG, TIF)")
    parser.add_argument("--t2", type=str, required=True, help="Path to observation T2 image (PNG, JPG, TIF)")
    parser.add_argument("--checkpoint", type=str, default="./ml/checkpoints/siamese_unet_best.pt", help="Path to model checkpoint")
    parser.add_argument("--threshold", type=float, default=0.5, help="Confidence threshold")
    parser.add_argument("--device", type=str, default="auto", help="Target device")
    parser.add_argument("--output-mask", type=str, default="./ml/inference/change_mask_output.png", help="Output path for binary change mask")
    parser.add_argument("--base-filters", type=int, default=16, help="Model base filters")
    return parser.parse_args()


def main():
    args = parse_args()
    device = get_optimal_device(preferred=args.device)

    print("=" * 70)
    print("🛰️  SIH1518: SIAMESE U-NET SATELLITE INFERENCE")
    print("=" * 70)
    print(f"• Baseline T1 Image : {args.t1}")
    print(f"• Current T2 Image  : {args.t2}")
    print(f"• Model Checkpoint  : {args.checkpoint}")
    print(f"• Target Device     : {device}")
    print("=" * 70)

    # Read inputs
    img1 = cv2.imread(args.t1, cv2.IMREAD_COLOR)
    img2 = cv2.imread(args.t2, cv2.IMREAD_COLOR)

    if img1 is None:
        print(f"❌ Error: Unable to read T1 image at: {args.t1}")
        sys.exit(1)
    if img2 is None:
        print(f"❌ Error: Unable to read T2 image at: {args.t2}")
        sys.exit(1)

    img1_rgb = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    img2_rgb = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

    t1_arr = img1_rgb.transpose(2, 0, 1)
    t2_arr = img2_rgb.transpose(2, 0, 1)

    predictor = SiamesePredictor(
        checkpoint_path=args.checkpoint,
        device=device,
        confidence_threshold=args.threshold,
        base_filters=args.base_filters,
    )

    prob_map, binary_mask = predictor.predict(t1_arr, t2_arr, threshold=args.threshold)

    total_px = binary_mask.size
    changed_px = int(np.count_nonzero(binary_mask))
    pct = (changed_px / max(1, total_px)) * 100.0

    out_p = Path(args.output_mask)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_p), binary_mask)

    print("\n" + "=" * 70)
    print("✅ INFERENCE COMPLETE")
    print(f"• Total Pixels Processed : {total_px:,}")
    print(f"• Changed Pixels Detected: {changed_px:,} ({pct:.2f}%)")
    print(f"• Mean Change Confidence : {float(np.mean(prob_map)):.4f}")
    print(f"• Output Mask Saved To   : {out_p.resolve()}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
