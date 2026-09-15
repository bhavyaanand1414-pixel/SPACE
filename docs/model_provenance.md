# Model & Dataset Provenance (PS 26227 §2.2.7)

> All pretrained models and datasets used in this system are publicly available
> under their respective licences.  Model weights are packaged locally for
> offline evaluation as required by PS 26227 §2.2.7.

## Pretrained Models

| Model | Version | Origin | Licence | Purpose | Weights Location | Size |
|---|---|---|---|---|---|---|
| **OpenCLIP ViT-B/32** | laion2b_s34b_b79k | [mlfoundations/open_clip](https://github.com/mlfoundations/open_clip) | MIT (code), Apache-2.0 (LAION-2B weights) | Satellite tile & text embedding for semantic search (PS 26227 §2.2.1) | `ml/checkpoints/clip/` | ~350 MB |
| **Siamese U-Net** | 1.0.0 | Custom trained (SIH1518 project) | Project-specific | Binary change detection on satellite image pairs (PS 26227 §2.2.2) | `ml/checkpoints/siamese_unet.pt` | ~100 MB |

## Libraries with Embedded Models

| Library | Version | Licence | Purpose |
|---|---|---|---|
| `open-clip-torch` | ≥2.24.0 | MIT | CLIP model loading and inference |
| `faiss-cpu` | ≥1.7.4 | MIT | Approximate nearest neighbor vector search |
| `hdbscan` | ≥0.8.33 | BSD-3-Clause | Density-based embedding clustering |
| `sentence-transformers` | ≥2.7.0 | Apache-2.0 | Text encoding utilities |
| `torch` | ≥2.2.1 | BSD-3-Clause | Deep learning framework |
| `rasterio` | ≥1.3.9 | BSD-3-Clause | Geospatial raster I/O |

## Datasets

| Dataset | Source | Licence | Usage |
|---|---|---|---|
| **Copernicus Sentinel-2 L2A** | ESA Copernicus Open Access Hub | Copernicus Sentinel Data Terms (free, open) | Primary optical multispectral imagery |
| **Copernicus Sentinel-1 SAR** | ESA Copernicus Open Access Hub | Copernicus Sentinel Data Terms (free, open) | SAR backscatter for flood/inundation mapping |
| **USGS Landsat Collection 2** | USGS EarthExplorer | Public Domain (USGS) | Multi-temporal optical imagery |
| **NRSC/ISRO Bhuvan** | ISRO Bhuvan Portal | ISRO Open Data Policy | Indian Earth-observation data products |

## Offline Staging Procedure

```bash
# 1. Install dependencies
cd backend && pip install -r requirements.txt

# 2. Download and cache model weights (requires network)
python scripts/download_models.py

# 3. Verify weights are cached
ls ml/checkpoints/clip/
ls ml/checkpoints/siamese_unet.pt

# 4. Network can now be disconnected for evaluation
```

## Provenance Manifest

A machine-readable manifest is auto-generated at `ml/checkpoints/MANIFEST.json`
by the `download_models.py` script.  This file records model origins, licences,
download timestamps, and embedding dimensions.
