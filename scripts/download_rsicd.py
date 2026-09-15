"""
Download RSICD (Remote Sensing Image Captioning Dataset) for SIH1518.

Downloads real satellite imagery with captions from HuggingFace.
Saves images to data/scenes/rsicd/images/ and generates dataset.json.
"""

import json
import os
import sys
from pathlib import Path


def main():
    print("=" * 70)
    print("SIH1518 - RSICD Satellite Imagery Dataset Downloader")
    print("=" * 70)

    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    output_dir = project_root / "data" / "scenes" / "rsicd"
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nOutput directory: {output_dir}")
    print("Downloading RSICD from HuggingFace (arampacha/rsicd)...\n")

    try:
        from datasets import load_dataset
    except ImportError:
        print("Installing 'datasets' library...")
        os.system(f"{sys.executable} -m pip install datasets Pillow")
        from datasets import load_dataset

    # Load the dataset
    print("Loading RSICD dataset from HuggingFace...")
    ds = load_dataset("arampacha/rsicd", trust_remote_code=True)

    # Debug: inspect structure
    for split_name in ds.keys():
        split = ds[split_name]
        print(f"\nSplit '{split_name}': {len(split)} samples")
        print(f"  Columns: {split.column_names}")
        if len(split) > 0:
            sample = split[0]
            print(f"  Sample keys: {list(sample.keys())}")
            for k, v in sample.items():
                if k == "image":
                    print(f"    {k}: PIL Image {v.size if hasattr(v, 'size') else type(v)}")
                elif isinstance(v, list):
                    print(f"    {k}: list[{len(v)}] = {v[:2]}...")
                elif isinstance(v, str):
                    print(f"    {k}: '{v[:80]}'")
                else:
                    print(f"    {k}: {type(v).__name__} = {v}")

    all_samples = []
    total_saved = 0

    for split_name in ds.keys():
        split = ds[split_name]
        print(f"\nProcessing split: {split_name} ({len(split)} samples)")

        for i, sample in enumerate(split):
            image = sample.get("image")

            # Get filename - strip any directory prefix and use just the basename
            raw_filename = sample.get("filename", f"{split_name}_{i:05d}.jpg")
            filename = Path(raw_filename).name  # Strip directory prefix
            if not filename.endswith((".jpg", ".png", ".jpeg", ".tif")):
                filename = f"{filename}.jpg"

            # Get captions
            captions = sample.get("captions", sample.get("caption", sample.get("sentences", [])))
            if isinstance(captions, dict):
                # Some datasets wrap captions in {"raw": [...], "tokens": [...]}
                captions = captions.get("raw", captions.get("tokens", [str(captions)]))
            if isinstance(captions, str):
                captions = [captions]
            if not captions:
                captions = [f"Satellite remote sensing image {filename}"]

            img_path = images_dir / filename

            # Save image
            if image is not None and not img_path.exists():
                try:
                    if hasattr(image, "save"):
                        image.save(str(img_path), format="JPEG", quality=95)
                        total_saved += 1
                except Exception as e:
                    if i < 5:
                        print(f"  Warning: Could not save {filename}: {e}")
                    continue

            # Use first caption
            caption = captions[0] if captions else f"Satellite image {filename}"

            all_samples.append({
                "image_path": filename,
                "caption": caption,
                "split": split_name,
                "all_captions": captions,
            })

            if (i + 1) % 1000 == 0:
                print(f"  Processed {i + 1}/{len(split)} images...")

    # Save dataset.json
    dataset_json_path = output_dir / "dataset.json"
    with open(dataset_json_path, "w", encoding="utf-8") as f:
        json.dump(all_samples, f, indent=2, ensure_ascii=False)

    # Count actual images on disk
    actual_images = len(list(images_dir.glob("*.jpg"))) + len(list(images_dir.glob("*.png")))

    print(f"\n{'=' * 70}")
    print(f"Download complete!")
    print(f"  Total samples:  {len(all_samples)}")
    print(f"  Images saved:   {total_saved}")
    print(f"  Images on disk: {actual_images}")
    print(f"  Images dir:     {images_dir}")
    print(f"  Dataset JSON:   {dataset_json_path}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
