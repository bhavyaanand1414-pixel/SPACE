# Machine Learning & AI Inference Pipeline

## 1. Remote Sensing Preprocessing & Data Flow

```
Raw GeoTIFF (T1) ──┐
                   ├──> CRS / Reprojection ──> Resampling ──> Percentile Norm ──> Sub-Pixel FFT Alignment ──> (C, H, W) [0, 1] Tensor
Raw GeoTIFF (T2) ──┘
```

### Scientific Preprocessing Principles:
1. **Analysis-Ready Inputs**: Deep neural networks require radiometric calibration and normalized range $[0.0, 1.0]$.
2. **Sub-Pixel Misregistration Invariance**: Small spatial offsets ($\Delta x, \Delta y < 2\text{px}$) are corrected prior to deep feature subtraction so the Siamese encoder detects semantic structural change rather than border parallax.
3. **NoData & Occlusion Gating**: Invalid pixels and cloud occlusions are masked so loss functions and inference metrics operate solely on valid surface terrain.

---

## 2. Change Detection Architectures

### A. Siamese U-Net (`SiameseUNetChangeDetector`)
The primary deep learning model utilizes a twin-branch weight-sharing encoder to extract multi-scale spatial representations from Image $T_1$ and Image $T_2$:
- **Encoder**: Twin ResNet/VGG-style backbone extracting hierarchical features $F_1^{(l)}$ and $F_2^{(l)}$ across 4 spatial scales.
- **Difference Module**: Absolute difference $|F_1^{(l)} - F_2^{(l)}|$ combined with channel concatenation.
- **Decoder**: Skip-connected upsampling layers producing a pixel-wise change probability map $P(\text{Change} \mid T_1, T_2) \in [0, 1]^{H \times W}$.
- **Loss Function**: Combined Focal Loss + Dice Loss:
  $$\mathcal{L}_{\text{total}} = \alpha \mathcal{L}_{\text{Focal}} + (1 - \alpha) \mathcal{L}_{\text{Dice}}$$

### B. Spectral Difference Baseline (`BaselineChangeDetector`)
Deterministic baseline combining:
1. Relative radiometric normalization.
2. Multi-spectral difference Euclidean distance $\Delta S = \sqrt{\sum_i (B_{1,i} - B_{2,i})^2}$.
3. Adaptive Otsu thresholding + morphological opening/closing + connected component area filtering.

---

## 3. Hierarchical Classification Engine

Detections are passed through a multi-factor classifier integrating:
- **Level 1 (Major Class)**:
  - `HUMAN`: Anthropogenic structural development (Buildings, Roads, Industrial, Quarrying).
  - `NATURAL`: Environmental phenology, vegetation cycles, natural river meanders.
  - `DISASTER`: Floods, landslides, wildfire burn scars, earthquake debris.
  - `ATMOSPHERIC`: Cloud motion, shadow artifacts, sensor noise.
  - `UNKNOWN`: Unclassified spectral shifts requiring human analyst verification.
- **Level 2 (Subtype)**:
  - New Building, Demolition, Road Construction, Urban Sprawl, Crop Rotation, Water Expansion, Flood Inundation Scar.
- **Spectral Index Corroboration**:
  - $\text{NDVI} = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}$ (Vegetation growth/loss)
  - $\text{NDBI} = \frac{\text{SWIR} - \text{NIR}}{\text{SWIR} + \text{NIR}}$ (Built-up infrastructure increase)
  - $\text{NDWI} = \frac{\text{Green} - \text{NIR}}{\text{Green} + \text{NIR}}$ (Water level and flood extent)

---

## 4. Evaluation & Benchmarks
- **Intersection over Union (IoU)**: $\frac{|A \cap B|}{|A \cup B|}$
- **F1-Score / Dice**: $\frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$
- **Precision & Recall** across all 5 Level-1 classes.
