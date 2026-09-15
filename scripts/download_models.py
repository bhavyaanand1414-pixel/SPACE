#!/usr/bin/env python3
"""
Offline Model Downloader (PS 26227 §2.2.7).

Downloads and caches all required pretrained model weights locally
for air-gapped / offline deployment.  Run this script BEFORE
disconnecting network access.

Usage:
    python scripts/download_models.py

Models downloaded:
    1. OpenCLIP ViT-B/32 (laion2b_s34b_b79k) — ~350 MB
       Purpose: Satellite tile and text embedding for semantic search
       Licence: MIT (OpenCLIP), Apache-2.0 (LAION weights)

    2. Siamese U-Net (custom) — already in ml/checkpoints/
       Purpose: Change detection
       Licence: Project-specific
"""

import os
import sys
from pathlib import Path


def download_clip_model():
    """Download and cache OpenCLIP ViT-B/32 weights."""
    try:
        import open_clip
    except ImportError:
        print("ERROR: open-clip-torch not installed. Run: pip install open-clip-torch")
        sys.exit(1)

    cache_dir = Path("ml/checkpoints/clip")
    cache_dir.mkdir(parents=True, exist_ok=True)

    model_name = os.environ.get("EMBEDDING_MODEL_NAME", "ViT-B-32")
    pretrained = os.environ.get("EMBEDDING_PRETRAINED", "laion2b_s34b_b79k")

    print(f"Downloading OpenCLIP {model_name} (pretrained={pretrained})...")
    print(f"Cache directory: {cache_dir.resolve()}")

    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name=model_name,
        pretrained=pretrained,
        cache_dir=str(cache_dir),
    )

    # Verify model loads correctly
    import torch
    dummy = torch.randn(1, 3, 224, 224)
    with torch.no_grad():
        features = model.encode_image(dummy)
    print(f"✅ CLIP model verified — output shape: {features.shape}")
    print(f"   Embedding dimension: {features.shape[-1]}")

    # Save tokenizer test
    tokenizer = open_clip.get_tokenizer(model_name)
    tokens = tokenizer(["test query"])
    with torch.no_grad():
        text_features = model.encode_text(tokens)
    print(f"✅ Text encoder verified — output shape: {text_features.shape}")

    return True


def verify_siamese_unet():
    """Check if Siamese U-Net checkpoint exists."""
    checkpoint_dir = Path("ml/checkpoints")
    checkpoints = list(checkpoint_dir.glob("*.pt")) + list(checkpoint_dir.glob("*.pth"))

    if checkpoints:
        for cp in checkpoints:
            size_mb = cp.stat().st_size / (1024 * 1024)
            print(f"✅ Found checkpoint: {cp.name} ({size_mb:.1f} MB)")
    else:
        print("⚠️  No Siamese U-Net checkpoint found in ml/checkpoints/")
        print("   The system will use the baseline spectral difference detector.")


def write_manifest():
    """Write a model manifest file for provenance tracking."""
    manifest_path = Path("ml/checkpoints/MANIFEST.json")

    import json
    from datetime import datetime, timezone

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "models": [
            {
                "name": "OpenCLIP ViT-B/32",
                "pretrained": "laion2b_s34b_b79k",
                "origin": "https://github.com/mlfoundations/open_clip",
                "licence": "MIT (code), Apache-2.0 (LAION-2B weights)",
                "purpose": "Satellite tile and text embedding for semantic search",
                "local_path": "ml/checkpoints/clip/",
                "embedding_dimension": 512,
            },
            {
                "name": "Siamese U-Net",
                "origin": "Custom trained (SIH1518 project)",
                "licence": "Project-specific",
                "purpose": "Binary change detection on satellite image pairs",
                "local_path": "ml/checkpoints/",
            },
        ],
        "datasets": [
            {
                "name": "Copernicus Sentinel-2",
                "source": "ESA Copernicus Open Access Hub",
                "licence": "Copernicus Sentinel Data Terms",
            },
            {
                "name": "Landsat Collection 2",
                "source": "USGS EarthExplorer",
                "licence": "Public Domain (USGS)",
            },
            {
                "name": "Bhuvan Open EO Data",
                "source": "NRSC/ISRO Bhuvan Portal",
                "licence": "ISRO Open Data Policy",
            },
        ],
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Model manifest written to {manifest_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("SIH1518 — Offline Model Downloader")
    print("PS 26227: Semantic Retrieval & Change Analysis")
    print("=" * 60)
    print()

    print("1/3: Downloading CLIP embedding model...")
    download_clip_model()
    print()

    print("2/3: Verifying Siamese U-Net checkpoint...")
    verify_siamese_unet()
    print()

    print("3/3: Writing model manifest...")
    write_manifest()
    print()

    print("=" * 60)
    print("✅ All models staged for offline operation.")
    print("   You may now disconnect network access.")
    print("=" * 60)
