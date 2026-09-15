# Model & Dataset Provenance Declaration (PS 26227 §2.2.7)

This document declares all pretrained models, their origins, licences, and datasets used in the SIH1518 platform, as required by the problem statement constraint that *"pretrained public models may be used provided that their origin and licence are declared and the required weights are packaged for offline use."*

## Pretrained Models

| Model | Origin | License | Purpose | Offline Packaged |
|-------|--------|---------|---------|-----------------|
| OpenCLIP ViT-B/32 (laion2B-s34B-b79K) | [LAION / OpenCLIP](https://github.com/mlfoundations/open_clip) | MIT License | Semantic image/text embedding for retrieval (§2.2.1) | ✅ Yes — `ml/checkpoints/clip/` |
| FAISS (Facebook AI Similarity Search) | [Meta Research](https://github.com/facebookresearch/faiss) | MIT License | Approximate nearest-neighbor vector search (§2.2.6) | ✅ Yes — installed via pip |
| scikit-learn (PCA, KMeans) | [scikit-learn](https://github.com/scikit-learn/scikit-learn) | BSD 3-Clause | Dimensionality reduction & clustering (§2.2.4) | ✅ Yes — installed via pip |
| HDBSCAN | [hdbscan](https://github.com/scikit-learn-contrib/hdbscan) | BSD 3-Clause | Density-based clustering (§2.2.4) | ✅ Yes — installed via pip |

## Datasets

| Dataset | Source | License | Usage |
|---------|--------|---------|-------|
| Copernicus Sentinel-2 | [ESA Copernicus Open Access Hub](https://scihub.copernicus.eu/) | Copernicus Open Licence | Primary optical satellite imagery |
| USGS Landsat Collection 2 | [USGS EarthExplorer](https://earthexplorer.usgs.gov/) | Public Domain (US Government) | Secondary multi-spectral imagery |
| LAION-2B | [LAION](https://laion.ai/) | CC-BY-4.0 | Used for pretraining the OpenCLIP model (not redistributed) |

## Offline Operation Compliance

All model weights are pre-downloaded and stored in `ml/checkpoints/` for complete offline operation. The system does **not** make any network calls during inference or evaluation. All dependencies are installed locally via `pip` and `npm`.
