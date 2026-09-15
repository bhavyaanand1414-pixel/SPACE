# 🛰️ SIH1518: AI-Powered Multi-Temporal Satellite Change Intelligence Platform (ISRO)

> **Smart India Hackathon 2024 / 2026 — Problem Statement ID: SIH1518**  
> **Organization:** Indian Space Research Organisation (ISRO)  
> **Theme:** Space Technology / AI & Geospatial Intelligence  
> **Title:** Automated Multi-Temporal Satellite Change Detection, Hierarchical Classification, and Explainable Intelligence

---

## 🌟 Executive Summary

**SIH1518** is an enterprise-grade, end-to-end Earth Observation (EO) intelligence platform engineered to detect, classify, quantify, and explain surface changes across multi-temporal satellite imagery (Sentinel-2 MSI, Sentinel-1 SAR, Landsat 8/9, Resourcesat/Cartosat). 

Combining **PyTorch Siamese U-Net Deep Learning**, **deterministic 2D FFT geospatial co-registration**, **PostGIS spatial polygon storage**, **modular disaster specialists**, a **grounded 20-tool AI Agent**, and **ReportLab automated PDF reporting**, SIH1518 delivers authoritative, publication-ready geospatial intelligence with strict non-hallucination guarantees.

---

## 🏛️ System Architecture

```
                                    🌐 USER INTERFACE
                    (React 18 + TypeScript + MapLibre/Leaflet + Tailwind)
                                         │
                                         ▼ [Port 5173 / 80]
                             [ NGINX REVERSE PROXY ]
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
           / (Static SPA Assets)                   /api/v1/ (FastAPI ASGI)
                                                              │
                                                              ▼
                                                   [ BACKEND SERVICES ]
                    ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
                    ▼                                         ▼                                         ▼
          [ GEOSPATIAL PIPELINE ]                   [ DEEP LEARNING (ML) ]                   [ AGENT & REPORTING ]
          • Rasterio / GDAL Ingestion               • PyTorch Siamese U-Net                  • Grounded AI Agent (20 Tools)
          • 2D FFT Co-Registration (<0.05 px)       • Hierarchical Taxonomy Engine           • Explainability & Reliability (XAI)
          • 2-98% Radiometric Normalization         • Multi-Spectral Indices (NDVI/NDWI)     • ReportLab PDF Dossier Generator
          • Geodesic Area Engine (m² & km²)         • Disaster Specialists (Flood/SAR)       • Human-In-The-Loop Review Queue
                                                              │
                                         ┌────────────────────┴────────────────────┐
                                         ▼                                         ▼
                               [ POSTGIS DATABASE ]                        [ REDIS CACHE ]
                              (Spatial EPSG & Polygons)                   (Async Broker & Cache)
```

---

## 🚀 Key Implemented Capabilities

### 1. Robust Imagery Ingestion & Pre-Flight Validation
- Supports **GeoTIFF, TIFF, Cloud-Optimized GeoTIFF (COG), PNG, and JPEG**.
- Strict security against path traversal, MIME spoofing, and multi-gigabyte upload caps.
- **6-Parameter Compatibility Matrix**: Spatial Overlap, CRS Alignment, GSD Ratio, Band Count, and Temporal Delta.

### 2. Sub-Pixel Preprocessing & Co-Registration
- **Phase Correlation via 2D Fast Fourier Transform (FFT)** for sub-pixel alignment ($\Delta < 0.05\text{ px}$).
- **2%–98% Cumulative Radiometric Percentile Normalization** eliminating atmospheric brightness discrepancies.
- Automated cloud, shadow, and water masking.

### 3. Dual-Engine Change Detection & PyTorch Siamese U-Net
- **PyTorch Siamese U-Net** with twin weight-sharing ResNet-50 feature encoders and feature differencing decoder.
- Optimized with **Combined Binary Cross-Entropy (BCE) + Soft Dice Loss** to conquer severe class imbalance.
- Native hardware autodetection across **NVIDIA CUDA**, **Apple Silicon MPS**, and **Multi-Core CPU**.
- High-speed **Normalized Spectral Difference Baseline** for instant triage.

### 4. Hierarchical Classification Taxonomy (Level-1 & Level-2)
- **Human Activities**: Construction Sites, New Buildings, Road Networks, Mining / Earthworks, Deforestation.
- **Natural Dynamics**: Vegetation Canopy Growth, Seasonal River / Riparian Shift, Wetland Fluctuations.
- **Disaster Events**: Flood Inundation (Optical & Sentinel-1 SAR), Wildfire Burn Scars, Earthquake Deformation, Landslide Bare Earth, Cyclone Damage.
- **Atmospheric Artifacts**: Cloud Cover, Haze, Cloud Shadow.
- **Unknown / Ambiguous**: Staged for human review.

### 5. Multi-Spectral Indices (NDVI, NDWI, NDBI)
- Automatic band availability detection (Red, Green, Blue, NIR, SWIR).
- Safe bypass on RGB imagery without incorrect band calculation.
- Supporting evidence integration into change region properties.

### 6. Multi-Temporal Time-Series Analytics
- Sequence analysis across $>2$ observation dates (e.g. 2020, 2022, 2024, 2026).
- Pairwise delta, sequential growth rates, and category progression curves.

### 7. Explainability (XAI) & Reliability Indicators
- 4-Crop Visual Evidence Matrix: Before Crop, After Crop, Change Mask, Saliency Heatmap.
- **Composite Reliability Score** (`HIGH`, `MEDIUM`, `LOW`) factoring Model Confidence (40%), Registration Quality (35%), and Image Quality (25%).

### 8. Human-In-The-Loop (HITL) & Active Learning Staging
- Automated routing of low-confidence detections ($<80\%$) to the Review Queue.
- Full analyst audit trail (original label, human correction, reviewer ID, timestamp).
- **Safety Policy**: Human corrections are staged as training candidates; production models are **never automatically retrained**.

### 9. Grounded AI Agent (20 Deterministic Tools)
- Zero-hallucination conversational intelligence orchestrating 20 actual GIS and ML tools.
- Never invents coordinates, dates, areas, or confidences. Returns `"Insufficient data"` when ungrounded.
- Clickable interactive region citations (`[Region #CR-001]`).

### 10. Publication-Grade ReportLab PDF Reports
- Automated multi-page PDF compilation with executive summary, metadata tables, change statistics, spectral analysis, disaster findings, high-resolution visual evidence maps, and mandatory ISRO disclaimers.

---

## 🌐 Production Cloud Deployment Architecture

The repository is organized for automated modular deployment across cloud providers:

```
sih1518/
├── frontend/          → 🚀 Vercel (Edge CDN React SPA)
├── backend/           → ⚡ Render (FastAPI Docker Web Service)
├── ml/                → 🧠 Render (PyTorch Models & Weights in Backend runtime)
├── data/              → ☁️ Cloudflare R2 / AWS S3 (Satellite Rasters - Zero Egress)
├── reports/           → 📄 Cloudflare R2 / AWS S3 (PDF Dossiers & XAI Reports)
├── docs/              → 📚 GitHub (ISRO Technical Documentation)
├── scripts/           → 🛠️ GitHub / Backend Sync & Healthcheck Tools
├── docker/            → 🐳 Render / Production Docker Packaging
├── docker-compose.yml → 💻 Local Development (PostGIS + Redis + App)
├── .env.example       → 🔑 GitHub (Deployment Blueprint)
└── README.md          → 📖 GitHub (Master System Overview)
```

| Component | Target Platform | Purpose | Configuration |
|---|---|---|---|
| **`frontend/`** | **Vercel** | Interactive GIS Dashboard & AI Chat UI | `frontend/vercel.json`, `VITE_API_BASE_URL` |
| **`backend/`** | **Render** | FastAPI ASGI API & GIS Engines | `render.yaml`, `docker/Dockerfile.backend` |
| **`ml/`** | **Render** | PyTorch Siamese U-Net & Checkpoints | Bundled inside Render backend container |
| **`data/`** | **Cloudflare R2** | Satellite Imagery & Tile Cache | S3-Compatible API (zero egress fees) |
| **`reports/`** | **Cloudflare R2** | Generated PDF Dossiers | Public / Presigned Download URLs |
| **`docker-compose.yml`** | **Local Development** | Offline Full-Stack Suite | PostGIS + Redis + Backend + Frontend |

---

## ⚡ Quickstart Guide

### Option A: Running with Docker Compose (Recommended)
```bash
# 1. Clone repository
git clone https://github.com/organization/SIH1518.git
cd SIH1518

# 2. Configure environment
cp .env.example .env

# 3. Launch all services (PostGIS, Redis, Backend, Frontend)
docker compose up --build -d

# 4. Access Application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/api/v1/docs
```

### Option B: Cloudflare R2 / S3 Sync
```bash
# Upload local dataset rasters & reports to Cloudflare R2
python scripts/sync_r2_storage.py --direction upload

# Download dataset rasters from Cloudflare R2
python scripts/sync_r2_storage.py --direction download
```

---

## 🧪 Comprehensive Verification & Test Results

| Test Suite | Framework | Total Tests | Pass Rate | Execution Time |
|---|---|---|---|---|
| **Backend Unit & Integration** | `pytest` | **84** | **100% (84/84)** | 11.51s |
| **Frontend UI & Components** | `Vitest + React Testing Library` | **10** | **100% (10/10)** | 1.24s |
| **End-to-End (E2E) Mission** | `pytest AsyncClient` | **1** (10 Steps) | **100% (1/1)** | 0.13s |
| **Frontend Production Build** | `tsc && vite build` | **2,405 Modules** | **0 Errors** | 2.35s |

To run the complete test suite:
```bash
# Run backend tests
cd backend && pytest tests/ -v

# Run frontend tests
cd ../frontend && npm test
```

---

## 📚 Technical Documentation Index

- 📐 [System Architecture & Data Flow](file:///Users/sunnykumar/SIH1518/docs/architecture.md)
- 🧠 [PyTorch ML Pipeline & Siamese U-Net](file:///Users/sunnykumar/SIH1518/docs/ml-pipeline.md)
- 🗺️ [Geospatial & PostGIS Processing](file:///Users/sunnykumar/SIH1518/docs/gis.md)
- 🤖 [Grounded AI Agent & 20 Tool Specifications](file:///Users/sunnykumar/SIH1518/docs/ai-agent.md)
- 📊 [Benchmark Datasets & Augmentation](file:///Users/sunnykumar/SIH1518/docs/dataset.md)
- 🔌 [Complete REST API Reference](file:///Users/sunnykumar/SIH1518/docs/api.md)
- 🧪 [Testing & Validation Matrices](file:///Users/sunnykumar/SIH1518/docs/testing.md)
- 🚀 [Production Deployment Manual](file:///Users/sunnykumar/SIH1518/docs/deployment.md)
- 🏆 [SIH Grand Finale Presentation Pitch](file:///Users/sunnykumar/SIH1518/SIH_PRESENTATION.md)

---

## 📜 Scientific Advisory Disclaimer
*All detected changes, categorizations, and disaster impact summaries generated by SIH1518 are system/model-derived indicators for rapid triage and operational planning. Final regulatory or disaster declarations must be corroborated with official ground-truth verification and authorized ISRO/government agencies.*
