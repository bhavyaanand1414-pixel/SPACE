"""
Executable Inference Script for Siamese U-Net Change Detection.

Usage:
  python ml/inference/inference.py --t1 data/sample/t1.tif --t2 data/sample/t2.tif --threshold 0.5
"""

import argparse
import numpy as np
import rasterio

from ml.inference.predictor import SiamesePredictor
from ml.models.base import get_optimal_device


def main():
    parser = argparse.ArgumentParser(description="Run Siamese U-Net Inference")
    parser.add_argument("--t1", type=str, required=True, help="Path to observation T1 raster")
    parser.add_argument("--t2", type=str, required=True, help="Path to observation T2 raster")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to trained checkpoint")
    parser.add_argument("--threshold", type=float, default=0.5, help="Confidence threshold")
    parser.add_argument("--device", type=str, default="auto", help="Hardware device: auto, cuda, mps, cpu")
    parser.add_argument("--output-mask", type=str, default="change_mask.png", help="Output path for change mask")
    args = parser.parse_args()

    device = get_optimal_device(preferred=args.device)

    # Read rasters
    with rasterio.open(args.t1) as ds1, rasterio.open(args.t2) as ds2:
        img1 = ds1.read()[:3].astype(np.float32) / 255.0
        img2 = ds2.read()[:3].astype(np.float32) / 255.0

    predictor = SiamesePredictor(
        checkpoint_path=args.checkpoint,
        device=device,
        confidence_threshold=args.threshold,
    )

    prob_map, binary_mask = predictor.predict(img1, img2)
    print(f"✅ Inference complete. Changed pixels: {np.count_nonzero(binary_mask):,}")


if __name__ == "__main__":
    main()
