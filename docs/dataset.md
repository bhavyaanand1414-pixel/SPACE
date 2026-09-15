# Public Remote Sensing Change Detection Benchmark Datasets

This document catalogs premier, publicly available, and standardized remote sensing change detection benchmark datasets used for training and evaluating deep learning models (such as Siamese U-Net) in the **SIH1518 Platform**.

---

## 1. Catalog of Open Benchmark Datasets

| Dataset | Sensor / Platform | Spatial Resolution | Image Format / Size | Primary Focus / Classes | Access & Licensing |
|---|---|---|---|---|---|
| **LEVIR-CD** | Very-High-Resolution Google Earth Optical | 0.5 m/px | 637 patch pairs ($1024 \times 1024$) | Building growth, urban construction, land use change (5-14 year span) | Open Access for Research (Beihang University) |
| **WHU-CD** | Aerial Photogrammetry | 0.075 m/px | 1 large pair split to $512 \times 512$ patches | High-precision building construction & demolition | Open Access (Wuhan University) |
| **DSIFN-CD** | Multi-satellite High Resolution (GF-2, JL-1, Sentinel) | 0.5 – 2.5 m/px | 6 large dual-temporal scenes ($512 \times 512$ tiles) | Urban infrastructure, road network expansion, land-cover transitions | Open Access for Research (Beihang University) |
| **OSCD** | Sentinel-2 MSI Multi-Spectral (13 bands) | 10 m / 20 m / 60 m | 24 global city areas ($600 \times 600$) | Multi-spectral urban expansion and environmental changes | Open Access (ONERA / IEEE GRSS) |
| **SECOND** | Aerial & Spaceborne Sensor Suite | 0.5 – 3.0 m/px | 4,662 pairs ($512 \times 512$) | Semantic Multi-Class Change (6 land cover categories) | Open Access (Wuhan University) |
| **Season-Varying (CDD)** | Google Earth Multi-Seasonal Imagery | 0.03 – 1.0 m/px | 16,000 patch pairs ($256 \times 256$) | Seasonal variance robust change detection (leaves, snow, solar angle) | Open Access (Lebedev et al.) |

---

## 2. Standardized Dataset Directory Hierarchy

The SIH1518 training pipeline expects datasets organized in the standard three-way split structure:

```text
data/
└── benchmark_dataset/
    ├── train/
    │   ├── A/        # Temporal Observation T1 (Baseline images)
    │   ├── B/        # Temporal Observation T2 (Current images)
    │   └── label/    # Ground-truth binary change masks (0 = unchanged, 255/1 = changed)
    ├── val/
    │   ├── A/
    │   ├── B/
    │   └── label/
    └── test/
        ├── A/
        ├── B/
        └── label/
```

---

## 3. Spatial & Temporal Leakage Prevention Guidelines

1. **Spatial Blocking (No Random Overlapping Patches)**:
   - Never randomly split adjacent overlapping tiles between `train` and `test`. Entire contiguous geographical scenes or blocks must be isolated to either `train`, `val`, or `test`.
2. **Temporal Consistency**:
   - Pair observations must maintain strict temporal sequence ($T_1 < T_2$) or explicitly declare bi-directional invariance.
3. **No Metric Fabrication**:
   - Model accuracy, IoU, Precision, Recall, and F1 scores must always be evaluated strictly against ground truth masks from the isolated `test/` partition.

---

## 4. Setting Up a Dataset for Training

To train the Siamese U-Net model on your local dataset:

1. Download your preferred open dataset (e.g., LEVIR-CD from official repository).
2. Extract into `data/LEVIR-CD/` matching the directory structure above.
3. Run the training pipeline:
   ```bash
   python ml/training/train.py --dataset-dir ./data/LEVIR-CD --epochs 50 --batch-size 8 --device auto
   ```
4. If no dataset is present locally, the pipeline will display structured guidance and provide a `--synthetic` demo option for smoke-testing.
