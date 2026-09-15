# System Architecture & Technical Specifications

Detailed architectural specifications for **SIH1518: AI-Powered Multi-Temporal Satellite Change Intelligence Platform (ISRO)**.

---

## 1. High-Level System Architecture

```
                                      🌐 CLIENT BROWSER
                          (React 18 + MapLibre/Leaflet + Tailwind)
                                              │
                                              ▼ [Port 5173 / 80]
                                  [ NGINX REVERSE PROXY ]
                                              │
                         ┌────────────────────┴────────────────────┐
                         ▼                                         ▼
                 / (Static SPA Bundle)                  /api/v1/ (FastAPI ASGI)
                                                                   │
                                                                   ▼
                                                       [ FASTAPI CORE ENGINE ]
                                                      • Ingestion & Validation
                                                      • Preprocessing & 2D FFT
                                                      • Siamese U-Net Inference
                                                      • Hierarchical Taxonomy
                                                      • Geospatial Statistics Engine
                                                      • Grounded AI Agent (20 Tools)
                                                      • ReportLab PDF Generator
                                                                   │
                                              ┌────────────────────┴────────────────────┐
                                              ▼                                         ▼
                                    [ POSTGIS DATABASE ]                        [ REDIS CACHE ]
                                   (Port 5432: Polygons)                       (Port 6379: Cache)
```

---

## 2. Layer-by-Layer Breakdown

### Layer 1: Presentation & Visualization Cockpit (Frontend)
- **Framework**: React 18, TypeScript, Vite.
- **Styling**: Tailwind CSS with custom Dark Glassmorphism space design tokens.
- **Cartographic Mapping**: Leaflet & React-Leaflet with dynamic split-swipe slider, GeoJSON vector overlay renderers, and custom color-coded category symbology.
- **State & Communication**: Axios REST client communicating with `/api/v1/` endpoints.

### Layer 2: API Gateway & Application Server (Backend)
- **Framework**: FastAPI (Python 3.11) with asynchronous endpoints (`async/await`) and Pydantic v2 schemas.
- **CORS Management**: Restricted origin boundaries for production environments.
- **Storage Layer**: Modular storage backend interface supporting local filesystem storage with ready expansion hooks for S3 / MinIO.

### Layer 3: Geospatial Processing & Co-Registration Engine
- **Libraries**: GDAL 3.8, Rasterio, Shapely, PyProj, Scipy.
- **Co-Registration**: Sub-pixel phase cross-correlation via 2D Fast Fourier Transform (FFT) on overlapping bounding extents ($\Delta < 0.05\text{ px}$).
- **Radiometric Normalization**: $2\%\text{--}98\%$ cumulative percentile histogram stretching eliminating atmospheric illumination discrepancies.
- **Vectorization**: Morphological contour extraction converting binary change masks into GeoJSON / PostGIS Polygon features.

### Layer 4: Deep Learning & Classification Engine
- **Framework**: PyTorch 2.0+ with Torchvision.
- **Model**: Siamese U-Net with twin weight-sharing ResNet-50 feature encoders and feature differencing decoder.
- **Loss Function**: Combined Binary Cross-Entropy (BCE) + Soft Dice Loss.
- **Classification Engine**: Hierarchical Level-1 (Human, Natural, Disaster, Atmospheric, Unknown) and Level-2 (15+ subcategories) rule-based decision trees grounded in geometric and spectral indices.

### Layer 5: Grounded AI Agent Orchestrator
- **Architecture**: Strict non-hallucination agent with 20 registered deterministic GIS/ML tools.
- **Orchestration**: Direct intent matching and deterministic tool execution returning verified numbers and interactive citations (`[Region #CR-001]`).

### Layer 6: Geospatial Intelligence Dossier Generator
- **Engine**: ReportLab 5.0.1.
- **Output**: Multi-page publication-grade PDF documents with study area summaries, raster metadata, change statistics, spectral findings, visual crops, and mandatory ISRO disclaimers.

### Layer 7: Data Persistence & Spatial Indexing
- **Database**: PostgreSQL 15 with PostGIS 3.3 spatial extension.
- **Geometry**: Polygons stored as `geometry(MultiPolygon, 4326)` indexed with GiST spatial indexes.
- **Cache**: Redis 7 for high-speed query caching and session state.
