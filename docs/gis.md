# GIS & Geospatial Processing Specifications

## 1. Scientific Preprocessing Assumptions & Principles

### A. Sub-Pixel Co-Registration & Misregistration Elimination
- **Scientific Axiom**: Sub-pixel spatial misalignment between multi-temporal acquisitions creates artificial edge discrepancies along high-contrast boundaries (e.g. coastlines, building edges, road corridors). **Misregistration must NEVER be falsely classified as human construction or real ground change.**
- **Phase Correlation Method**: 2D Fast Fourier Transform (FFT) phase correlation with a 2D Hanning window function:
  $$R(u, v) = \frac{F_1(u, v) \cdot F_2^*(u, v)}{|F_1(u, v) \cdot F_2^*(u, v)|}$$
  $$\text{Peak Response } \rho = \max(\mathcal{F}^{-1}\{R(u, v)\})$$
- **Registration Quality & Risk Telemetry**:
  - `EXCELLENT` ($\rho \ge 0.6$): Confident sub-pixel alignment ($\Delta x, \Delta y$), minimal edge false-positive risk.
  - `GOOD` ($0.35 \le \rho < 0.6$): Reliable sub-pixel translation applied via bilinear warping.
  - `FAIR` ($0.15 \le \rho < 0.35$): Sub-pixel translation applied with elevated risk score flag.
  - `POOR` ($\rho < 0.15$): Scene content too dissimilar (e.g. extensive cloud cover, extreme disaster inundation); warp is bypassed to prevent geometric destruction.

### B. Coordinate Reference Systems (CRS) & Projections
1. **Input CRS Verification**: Raster inputs are inspected via `rasterio.crs.CRS` and EPSG codes.
2. **Auto-UTM Normalization**: All multi-temporal pairs are reprojected to a common Universal Transverse Mercator (UTM) or target projected coordinate system with bilinear resampling for continuous radiance bands.
3. **Geodesic Area Calculation**: Change polygon surface areas are computed via Shapely/PyProj geodesic ellipsoidal equations (WGS 84 ellipsoid), preventing longitudinal distortion errors across variable latitudes.

### C. Overlap & Bounding Box Intersection
- Both rasters are clipped to their common geometric bounding box intersection:
  $$\text{Bounds}_{\text{common}} = [\max(x_{1,\min}, x_{2,\min}), \max(y_{1,\min}, y_{2,\min}), \min(x_{1,\max}, x_{2,\max}), \min(y_{1,\max}, y_{2,\max})]$$
- Disjoint acquisitions (<50% overlap) trigger explicit validation failure `INCOMPATIBLE_PAIR`.

---

## 2. Radiometric Normalization & Artifact Masking

1. **Percentile Clipping (2% - 98%)**:
   - Outlier radiances (specular reflections on metallic roofs, solar glint on water bodies) are clipped per spectral band prior to scaling:
     $$I_{\text{norm}}(x, y) = \text{clip}\left(\frac{I(x, y) - P_2}{P_{98} - P_2}, 0.0, 1.0\right)$$
2. **NoData Propagation**:
   - Pixels marked with sensor NoData ($0$ or $-9999$) are tracked in a unified binary boolean mask `valid_mask` and excluded from change score calculations.
3. **Cloud & Cloud Shadow Detection**:
   - Bright white spectral response ($\bar{I}_{\text{RGB}} > 0.85, \sum |\Delta \text{RGB}| < 0.25$) is segregated into atmospheric cloud masks to prevent cloud motion from masquerading as new urban infrastructure.

---

## 3. Vectorization & PostGIS Pipeline

1. **Binary change probability mask** $\rightarrow$ Contouring via `cv2.findContours` or `rasterio.features.shapes`.
2. **Douglas-Peucker polygon simplification** ($\epsilon = 0.0001^{\circ}$ or 1 pixel) to produce compact GIS vector polygons.
3. **Feature enrichment**: Centroid geographic coordinates $(\text{Lat}, \text{Lon})$, bounding box, perimeter, area ($\text{m}^2$ and $\text{km}^2$), and category subtype.
4. **GeoJSON export and PostGIS spatial indexing** (`GIST(geom)`), enabling high-speed bounding box intersection queries.
