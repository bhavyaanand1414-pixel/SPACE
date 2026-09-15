# Grounded AI Agent & Deterministic Tool Orchestration

Technical specifications for the **SIH1518 Grounded AI Agent Orchestrator**.

---

## 1. Core Architecture & Anti-Hallucination Guardrails

The SIH1518 AI Agent is designed with strict **zero-hallucination guardrails**:
1. **No direct LLM classification**: The agent never predicts satellite land cover from imagination.
2. **Deterministic Tool Execution**: The agent routes queries through 20 deterministic backend GIS and ML tools.
3. **No invented facts**: If coordinates, dates, or areas are not present in the database or raster headers, the agent responds with `"Insufficient data"`.
4. **Clickable Citations**: Detections referenced in agent answers include interactive region links (e.g. `[Region #CR-001]`).

---

## 2. Catalogue of the 20 Registered Tools

| # | Tool Name | Category | Functionality |
|---|---|---|---|
| 1 | `inspect_image` | Ingestion | Reads raster dimensions, band counts, and data types |
| 2 | `extract_metadata` | Ingestion | Extracts EPSG CRS, GSD resolution, and bounding extents |
| 3 | `validate_images` | Validation | Validates spatial overlap, CRS match, and temporal delta |
| 4 | `calculate_time_difference` | Temporal | Calculates acquisition delta in days, months, and years |
| 5 | `preprocess_images` | Preprocessing | Applies 2-98% radiometric normalization and cloud masking |
| 6 | `register_images` | Preprocessing | Executes 2D FFT sub-pixel phase correlation alignment |
| 7 | `detect_changes` | ML Engine | Triggers Siamese neural change detection or baseline difference |
| 8 | `classify_changes` | Taxonomy | Categorizes polygons into Human, Natural, Disaster, etc. |
| 9 | `calculate_area` | GIS Engine | Computes geodesic and projected area ($m^2$ and $km^2$) |
| 10 | `calculate_statistics` | Statistics | Aggregates area changed, percentage, and severity metrics |
| 11 | `analyze_flood` | Disaster | Generates flood inundation extents for optical / SAR data |
| 12 | `analyze_earthquake` | Disaster | Evaluates potential structural and surface deformation |
| 13 | `analyze_cyclone` | Disaster | Identifies coastal vegetation loss and storm surge inundation |
| 14 | `analyze_landslide` | Disaster | Maps bare-earth slope displacement scars |
| 15 | `analyze_wildfire` | Disaster | Computes dNBR burn scar extents and severity classes |
| 16 | `generate_geojson` | GIS Engine | Formats detected change boundaries as GeoJSON FeatureCollection |
| 17 | `compare_time_series` | Temporal | Evaluates multi-temporal sequence growth rates and trajectories |
| 18 | `query_database` | Persistence | Queries PostGIS database for change records and metrics |
| 19 | `generate_report` | Reporting | Compiles publication-grade ReportLab PDF dossiers |
| 20 | `summarize_analysis` | Intelligence | Generates executive mission intelligence summaries |

---

## 3. Supported Natural Language Inquiry Patterns

- **"What changed?"** $\rightarrow$ Summarizes total area changed, top categories, and key findings.
- **"Show all new buildings."** $\rightarrow$ Filters PostGIS features by Level-2 `New Building` category with clickable citations.
- **"How much area changed?"** $\rightarrow$ Returns verified total area changed ($km^2$) and percentage of study area.
- **"How much area was flooded?"** $\rightarrow$ Routes to `analyze_flood` specialist and reports inundated area ($km^2$).
- **"Which changes are human activities?"** $\rightarrow$ Isolates Level-1 `Human` detections (construction, roads, mining, deforestation).
- **"What changed between 2020 and 2026?"** $\rightarrow$ Executes multi-temporal time-series comparison across observation interval.
- **"Which category has the largest affected area?"** $\rightarrow$ Compares category area aggregates and reports the dominant driver.
- **"Explain change #12."** $\rightarrow$ Fetches 4-crop evidence and reliability breakdown for region index 12.
- **"Generate a report."** $\rightarrow$ Triggers ReportLab PDF generation and returns download stream link.
