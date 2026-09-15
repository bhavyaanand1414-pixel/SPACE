# SIH1518 — AI-Powered Multi-Temporal Satellite Change Intelligence Platform
## Master Project Plan & Architecture Roadmap

**Problem Statement ID:** SIH1518  
**Title:** Change Detection Due to Human Activities  
**Organization:** ISRO (Indian Space Research Organisation)  
**Category:** Space Technology  
**Type:** Software  

---

## 1. System Architecture Overview

The platform is designed around strict separation of concerns, decoupling GIS and ML computations from LLM-based agent reasoning.

```
                                  +-----------------------+
                                  |    Web Client (React) |
                                  | TypeScript, Leaflet/GL|
                                  +-----------+-----------+
                                              |
                                              v (REST / WebSockets)
                                  +-----------------------+
                                  |   FastAPI Gateway     |
                                  | Auth, Jobs, Validation|
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  | Analysis Orchestrator |
                                  +---+-------+-------+---+
                                      |       |       |
                 +--------------------+       |       +--------------------+
                 |                            |                            |
                 v                            v                            v
      +---------------------+      +---------------------+      +---------------------+
      |   Remote Sensing &  |      |   AI/ML Inference   |      |  Data & Persistence |
      |     GIS Engine      |      |       Engine        |      |       Engine        |
      |---------------------|      |---------------------|      |---------------------|
      | * Rasterio / GDAL   |      | * Baseline Detector |      | * PostgreSQL/PostGIS|
      | * CRS Normalization |      | * Siamese U-Net     |      | * Object Storage    |
      | * Co-registration   |      | * Object Detection  |      | * Metadata Catalog  |
      | * Spectral Indices  |      | * Hierarchical      |      | * Active Learning DB|
      | * Vectorization     |      |   Classification    |      | * Reports & History |
      +----------+----------+      +----------+----------+      +----------+----------+
                 |                            |                            |
                 +--------------------+       |       +--------------------+
                                      |       |       |
                                      v       v       v
                                  +-----------------------+
                                  |    AI Agent Engine    |
                                  | Tools, Natural Q&A,   |
                                  | Multi-temporal Explain|
                                  +-----------------------+
```

---

## 2. Hierarchical Change Taxonomy

```
LEVEL 1: CATEGORIES          LEVEL 2: SUBTYPES
-------------------------------------------------------------------------------
1. HUMAN ACTIVITY            -> New Building, Demolition, Expansion, Road
                                Construction, Road Widening, Bridge Construction,
                                Infrastructure, Construction Site, Industrial/Factory,
                                Mining/Quarrying, Urban Expansion.
2. NATURAL / ENVIRONMENTAL   -> Seasonal Vegetation, Vegetation Growth/Loss,
                                Water-Level Change, River-Course Change,
                                Soil Moisture/Erosion, Terrain Change.
3. DISASTER                  -> Flood Inundation, Potential Earthquake Damage,
                                Cyclone Damage, Landslide Scar, Wildfire/Burn Scar.
4. ATMOSPHERIC / ARTIFACT    -> Cloud, Cloud Shadow, Haze, Sensor Artifact,
                                Registration Misalignment.
5. UNKNOWN                   -> Unclassified Significant Spectral Disruption.
```

---

## 3. The 23 Implementation Phases

| Phase | Description | Deliverables | Milestone |
|:---|:---|:---|:---|
| **Phase 1** | Project Architecture & Environment Setup | Directory structure, docs, configs, base schemas, docker files | Initialized Base |
| **Phase 2** | React Frontend Shell | Dashboard UI, Navigation, Space-Tech Dark Theme, Upload forms | Visual Framework |
| **Phase 3** | FastAPI Backend Architecture | App factory, routers, schemas, CORS, error handling, healthcheck | API Core |
| **Phase 4** | PostgreSQL & PostGIS Database | SQLAlchemy models, Alembic migrations, spatial tables | Data Persistence |
| **Phase 5** | Image Ingestion & Metadata Validation | Multi-sensor validation, CRS check, overlap check, Quality Score | Ingestion Pipeline |
| **Phase 6** | Raster Preprocessing & Co-Registration | Rasterio warping, reprojection, resampling, phase correlation | GIS Preprocessor |
| **Phase 7** | Baseline Change Detector & Vectorization | Spectral difference, Otsu threshold, morphological clean, GeoJSON | Working Baseline |
| **Phase 8** | Interactive GIS Map & Comparison Viewer | Leaflet/MapLibre split viewer, vector overlays, dynamic legend | Spatial UI |
| **Phase 9** | Siamese U-Net Deep Learning Engine | PyTorch model, feature encoder/decoder, device auto-detect | Deep Learning Core |
| **Phase 10** | Hierarchical Change Classifier | Rule + ML classification, Spectral indices (NDVI/NDWI/NDBI) | Taxonomy Engine |
| **Phase 11** | Modular Disaster Detection Services | Flood inundation, landslide scar, wildfire burn mapping | Disaster Suite |
| **Phase 12** | Multi-Temporal Time-Series Engine | N-image comparison, progression tracking, area-over-time | Temporal Analytics |
| **Phase 13** | Uncertainty & Data Quality Scoring | Multi-factor reliability calculation, uncertainty maps | Scientific Rigor |
| **Phase 14** | Human-in-the-Loop & Active Learning | Review queue, manual annotation tool, retraining candidate queue | Feedback Loop |
| **Phase 15** | AI Agent Tool Infrastructure | Deterministic GIS/ML agent tools, LangGraph orchestration | Tool Registry |
| **Phase 16** | AI Agent Chat UI & Querying | Natural language Q&A bound strictly to verified analysis data | Agent Chat |
| **Phase 17** | Automated PDF Report Generator | ReportLab PDF compilation, charts, change maps, disclaimers | Export System |
| **Phase 18** | End-to-End Dashboard Integration | Full state synchronization, job polling, reactive UI | Complete System |
| **Phase 19** | Testing Suite & Verification | Backend pytest, Frontend Vitest, GIS accuracy tests, E2E flow | Verification Pass |
| **Phase 20** | Containerization & Docker Compose | Multi-container setup (API, PostGIS, Redis, UI) | Container Bundle |
| **Phase 21** | Deployment & Production Hardening | Security headers, rate limiting, S3/local storage abstraction | Production Ready |
| **Phase 22** | Technical Documentation & Manuals | Architectural, ML, GIS, API, and deployment documentation | Docs Suite |
| **Phase 23** | SIH Presentation & Demonstration Mode | Curated ISRO demo workflows, sample datasets, pitch deck | SIH Ready |

---

## 4. Dependencies & Prerequisites

### System Requirements
- Python 3.10+
- Node.js 18+ and npm
- GDAL / PROJ native libraries (or containerized equivalents)
- PostgreSQL 15+ with PostGIS extension (or Docker container)

### Hardware Acceleration
- Automatically detects and falls back gracefully:
  `CUDA (NVIDIA) -> MPS (Apple Silicon) -> CPU`

---

## 5. Risk Assessment & Mitigation

| Risk | Impact | Mitigation Strategy |
|:---|:---|:---|
| **Misalignment / Registration Artifacts** | High (false change detection) | Robust sub-pixel image registration and registration quality scoring. |
| **Cloud / Shadow Interference** | Medium | Cloud mask generation, atmospheric category labeling rather than false human change. |
| **Large Raster Memory Consumption** | High (OOM crashes) | Windowed reading with Rasterio, tiled inference, patch-based model processing. |
| **LLM Hallucinations** | Critical (scientific invalidity) | Strict tool-grounded AI agent where LLM never predicts pixels or fabricates statistics. |
| **CRS & Incompatible Projections** | High | Automated geospatial reprojection to common UTM projected CRS before processing. |
