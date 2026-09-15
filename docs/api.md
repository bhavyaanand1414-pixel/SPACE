# REST API Reference & Endpoint Specifications

Base Path: `/api/v1`

---

## 1. System Diagnostics & Health

### `GET /health`
Returns the status of backend components, database connectivity, and hardware acceleration device.

---

## 2. Satellite Imagery Ingestion

### `POST /images/upload`
Uploads a satellite raster (GeoTIFF, COG, TIFF, PNG, JPEG) and extracts geospatial metadata.
- **Request**: `multipart/form-data` with `file` and optional `satellite` hint.
- **Response**: `ImageUploadResponse` (image_id, filename, CRS, resolution, bounds).

### `GET /images/{image_id}`
Retrieves extracted metadata and bounding box for a stored raster.

---

## 3. Pre-Flight Pair Validation

### `POST /analyses/validate`
Executes a 6-parameter compatibility check between baseline (T1) and comparison (T2) images.
- **Checks**: Spatial Overlap, CRS Alignment, GSD Ratio, Band Count, and Acquisition Delta.
- **Response**: `AnalysisValidationResponse` with `data_quality_score` [0–100] and recommendation (`READY_FOR_INFERENCE`, `REQUIRES_PREPROCESSING`, `INCOMPATIBLE_PAIR`).

---

## 4. Change Detection & Analysis

### `POST /analyses/{analysis_id}/run`
Triggers co-registration, Siamese neural inference / baseline detection, and hierarchical classification.
- **Request Body**:
  ```json
  {
    "image1_id": "image_t1.tif",
    "image2_id": "image_t2.tif",
    "confidence_threshold": 0.50,
    "enable_coregistration": true
  }
  ```
- **Response**: `AnalysisDetailResponse` with status `completed`, statistics, registration metrics, and spectral indices.

### `GET /analyses/{analysis_id}`
Fetches analysis summary, model version, and aggregated change statistics.

### `GET /analyses/{analysis_id}/changes`
Retrieves detected change boundaries as a GeoJSON `FeatureCollection` with Level-1 & Level-2 classification properties.

---

## 5. Explainability & Uncertainty (XAI)

### `GET /analyses/{analysis_id}/explain/{region_index}`
Generates the 4-crop visual evidence matrix and composite reliability indicator (`HIGH`, `MEDIUM`, `LOW`) for a specific detected polygon.

---

## 6. Multi-Temporal Time-Series Analytics

### `POST /timeseries/analyze`
Processes $>2$ multi-temporal observation rasters (e.g. 2020, 2022, 2024, 2026) to calculate pairwise deltas, growth progressions, and category trends over time.

---

## 7. Modular Disaster Specialists

### `POST /disasters/flood`
Executes optical / SAR flood inundation mapping comparing baseline and post-disaster rasters.

### `POST /disasters/wildfire`
Evaluates post-fire NBR (Normalized Burn Ratio) and dNBR burn severity zones.

### `POST /disasters/earthquake`
Detects potential surface deformation and structural disruption.

### `POST /disasters/landslide`
Identifies bare-earth slope displacement scars.

### `POST /disasters/cyclone`
Analyzes vegetation stripping and coastal storm surge inundation.

---

## 8. Human-In-The-Loop (HITL) Review

### `GET /review/queue`
Fetches all low-confidence ($<80\%$) and ambiguous detections awaiting human verification.

### `POST /analyses/{analysis_id}/review`
Submits analyst classification corrections and logs audit trail.

### `POST /review/export-candidates`
Stages verified corrections into the active learning training candidate dataset.

---

## 9. Grounded AI Agent

### `GET /agent/tools`
Returns the catalogue of all 20 registered deterministic tools.

### `POST /agent/query`
Sends a natural language question (e.g., *"What changed?"*, *"Show all new buildings."*, *"How much area was flooded?"*).
- **Response**: Tool execution trace, citations to analysis regions, and grounded answers.

---

## 10. Geospatial PDF Reports

### `POST /analyses/{analysis_id}/report`
Compiles an automated ReportLab PDF intelligence dossier.

### `GET /reports/{report_id}`
Streams the binary PDF report (`application/pdf`).

### `GET /reports/{report_id}/metadata`
Retrieves metadata and generation timestamps for a compiled report.
