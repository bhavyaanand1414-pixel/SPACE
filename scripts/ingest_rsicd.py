"""
Ingest downloaded RSICD satellite images into the SIH1518 FAISS vector index.

Reads images from data/scenes/rsicd/images/ and uploads each one via
the /api/v1/ingest/upload endpoint.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

API_BASE = "http://localhost:8000/api/v1"


def main():
    print("=" * 70)
    print("SIH1518 - RSICD Satellite Imagery Ingestion Pipeline")
    print("=" * 70)

    project_root = Path(__file__).resolve().parent.parent
    rsicd_dir = project_root / "data" / "scenes" / "rsicd"
    images_dir = rsicd_dir / "images"
    dataset_json = rsicd_dir / "dataset.json"

    # Check backend health
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        health = r.json()
        print(f"\nBackend status: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"\nBackend not reachable: {e}")
        print("Make sure the backend is running (docker compose up -d)")
        sys.exit(1)

    # Check current index status
    try:
        r = requests.get(f"{API_BASE}/ingest/status", timeout=5)
        idx = r.json()
        print(f"Current index: {idx.get('total_vectors', 0)} vectors")
    except Exception:
        print("Could not fetch index status")

    # Load dataset metadata
    if dataset_json.exists():
        with open(dataset_json, "r", encoding="utf-8") as f:
            samples = json.load(f)
        print(f"\nLoaded {len(samples)} samples from dataset.json")
    else:
        # Fall back to scanning images directory
        samples = []
        if images_dir.exists():
            for img_file in sorted(images_dir.iterdir()):
                if img_file.suffix.lower() in (".jpg", ".jpeg", ".png", ".tif", ".tiff"):
                    samples.append({
                        "image_path": img_file.name,
                        "caption": f"Satellite image {img_file.stem}",
                    })
        print(f"\nFound {len(samples)} images in {images_dir}")

    if not samples:
        print("No images found! Run download_rsicd.py first.")
        sys.exit(1)

    # Ingest images
    print(f"\nIngesting {len(samples)} satellite images...\n")

    total_tiles = 0
    total_embeddings = 0
    success_count = 0
    fail_count = 0
    start_time = time.time()

    for i, sample in enumerate(samples):
        img_path = images_dir / sample["image_path"]

        if not img_path.exists():
            continue

        # Determine satellite type from caption
        caption = sample.get("caption", "").lower()
        satellite = "sentinel-2"  # default
        if any(w in caption for w in ["airport", "bridge", "stadium", "parking", "building"]):
            satellite = "sentinel-2"
        elif any(w in caption for w in ["farm", "forest", "mountain", "river", "lake"]):
            satellite = "landsat"

        try:
            with open(img_path, "rb") as f:
                files = {"file": (img_path.name, f, "image/jpeg")}
                data = {"satellite": satellite, "sensor": "MSI"}
                resp = requests.post(
                    f"{API_BASE}/ingest/upload",
                    files=files,
                    data=data,
                    timeout=120,
                )

            if resp.status_code == 200:
                result = resp.json()
                tiles = result.get("tile_count", 0)
                embeds = result.get("embedding_count", 0)
                total_tiles += tiles
                total_embeddings += embeds
                success_count += 1
            else:
                fail_count += 1
                if i < 3:  # Only show first few errors
                    print(f"  [{i+1}] FAIL HTTP {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            fail_count += 1
            if i < 3:
                print(f"  [{i+1}] ERROR: {e}")

        # Progress update every 100 images
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            eta = (len(samples) - i - 1) / rate if rate > 0 else 0
            print(
                f"  [{i+1}/{len(samples)}] "
                f"{success_count} ok, {fail_count} fail | "
                f"{total_tiles} tiles, {total_embeddings} embeds | "
                f"{rate:.1f} img/s, ETA {eta:.0f}s"
            )

    elapsed = time.time() - start_time

    # Final status
    print(f"\n{'=' * 70}")
    print(f"Ingestion Complete!")
    print(f"  Total images:     {len(samples)}")
    print(f"  Successful:       {success_count}")
    print(f"  Failed:           {fail_count}")
    print(f"  Total tiles:      {total_tiles}")
    print(f"  Total embeddings: {total_embeddings}")
    print(f"  Time elapsed:     {elapsed:.1f}s")

    try:
        r = requests.get(f"{API_BASE}/ingest/status", timeout=5)
        idx = r.json()
        print(f"  Index vectors:    {idx.get('total_vectors', 0)}")
        print(f"  Index dimension:  {idx.get('index_dimension', 'N/A')}")
    except Exception:
        pass

    print(f"{'=' * 70}")
    print(f"\nYou can now search at http://localhost:5175/search")


if __name__ == "__main__":
    main()
