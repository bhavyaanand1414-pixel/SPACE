# Detailed Project Report: AI Multi-Temporal Satellite Change Intelligence Platform (SIH 1518)

## 1. Project Overview
**Project Title:** AI Multi-Temporal Satellite Change Intelligence Platform
**Problem Statement Code:** SIH1518
**Ministry / Organization:** Ministry of Defence (MoD) / DGIS
**Domain:** Space Tech, Artificial Intelligence, Geographic Information Systems (GIS)

### 1.1 Abstract
The **AI Multi-Temporal Satellite Change Intelligence Platform** is a state-of-the-art web application designed to automate the analysis of satellite imagery. By leveraging Deep Learning, Computer Vision, and Semantic Vector Search, the platform enables defense personnel and intelligence analysts to instantly detect infrastructural changes across time, discover critical assets through natural language queries, and visualize geospatial data on an interactive map.

---

## 2. Problem Statement & Objectives
### 2.1 The Challenge
Traditional satellite imagery analysis requires human analysts to manually inspect high-resolution images across different dates to identify strategic changes (e.g., new building construction, troop movements, deforestation). This manual process is time-consuming, prone to human error, and cannot scale with the massive influx of daily satellite data.

### 2.2 Objectives
1. **Automated Change Detection:** To develop an AI pipeline that accepts two satellite images of the same area from different dates and automatically highlights structural changes.
2. **Semantic Search Engine:** To allow operators to query the satellite archive using natural language (e.g., "buildings near a river", "military convoys") using Zero-Shot vision-language models.
3. **High-Performance Geospatial Visualization:** To provide an interactive GIS map interface for rendering heavy raster data (GeoTIFFs) smoothly in the browser.
4. **End-to-End Analytics:** To generate automated PDF reports and time-series analyses for strategic decision-making.

---

## 3. System Architecture & Technology Stack

The platform is designed with a modern decoupled microservices architecture, ensuring high scalability and low-latency inference.

### 3.1 Frontend (User Interface)
* **Framework:** React.js powered by Vite for lightning-fast Hot Module Replacement (HMR).
* **Styling:** Tailwind CSS for a highly responsive, glassmorphism-inspired dark mode UI tailored for command-center environments.
* **Geospatial Rendering:** Integration with modern web mapping libraries (Leaflet/Mapbox) to render raster tiles and vector polygons.

### 3.2 Backend (API & Core Logic)
* **Framework:** FastAPI (Python 3.11) for ultra-fast, asynchronous API routing.
* **Data Processing:** `rasterio` and `shapely` for geospatial metadata extraction, bounding box calculations, and tile slicing.
* **Image Processing:** `Pillow` (PIL) and `NumPy` for in-memory matrix manipulation and dynamic tile generation.

### 3.3 Artificial Intelligence & Machine Learning
* **Semantic Embeddings:** PyTorch running `open_clip` (Contrastive Language-Image Pretraining) to encode both images and text into a shared high-dimensional vector space.
* **Vector Database:** **FAISS** (Facebook AI Similarity Search) for sub-millisecond retrieval of visually similar satellite chips based on vector distance (cosine similarity).
* **Change Detection:** Convolutional Neural Networks (CNNs) / Vision Transformers (ViTs) configured to perform semantic segmentation and highlight differences between temporal pairs.

---

## 4. Key Modules & Features

### 4.1 Ingestion & Tiling Engine
When massive GeoTIFF/COG images are uploaded, the backend automatically extracts geospatial metadata (EPSG codes, bounding boxes) and slices the multi-gigabyte raster into manageable `256x256` pixel chips. These chips are saved to persistent local storage for rapid serving.

### 4.2 Semantic Retrieval Engine
The system processes the image chips through the OpenCLIP encoder to extract 512-dimensional embeddings. These are indexed in FAISS. Users can type natural language queries, which are converted into text vectors and matched against the image vectors.
* **Accuracy:** Ranks tiles perfectly by semantic similarity score (descending order).
* **Speed:** Capable of searching thousands of tiles in `<100ms`.

### 4.3 Interactive Dashboard
The dark-themed dashboard provides modules for:
* **Upload Imagery:** Secure uploading and hashing of satellite datasets.
* **Run Analysis:** Triggering deep learning inference pipelines.
* **Change Results:** Visualizing side-by-side temporal differences with highlighted bounding boxes.
* **PDF Reports:** Exporting tactical intelligence summaries.

---

## 5. Implementation Workflow (Recent Updates)
To ensure the platform is robust for production demonstrations, the following critical engineering tasks were completed:
1. **Dockerization Optimization:** The system was containerized. Dependency bloat from heavy C++ GIS libraries (GDAL/PROJ) was mitigated to ensure cross-platform compatibility.
2. **Thumbnail Caching:** Re-architected the ingestion pipeline to persist AI-processed JPEGs to disk, backed by a FastAPI `StaticFiles` server, ensuring the UI grid instantly renders high-quality images instead of placeholders.
3. **Ghost Vector Purging:** Implemented strict state-management for the FAISS index to ensure database purity, eliminating broken links from aborted ingestion streams.

---

## 6. Future Scope
1. **Multi-Modal Agents:** Integrating a conversational LLM "Agent Portal" that allows analysts to talk to the map (e.g., "Summarize the changes in Sector 4 over the last month").
2. **Cloud Object Storage:** Migrating the local `data/storage/` folder to AWS S3 / MinIO for infinite horizontal scaling.
3. **Distributed AI Inference:** Offloading the PyTorch embedding generation to GPU-accelerated worker queues (Celery/Redis) for parallel batch processing of entire planetary scenes.

---

## 7. Conclusion
The SIH1518 platform successfully demonstrates the feasibility of combining modern web architecture with bleeding-edge Vision-Language AI. It transforms raw, unstructured satellite pixels into searchable, actionable intelligence, drastically reducing the cognitive load on defense analysts and accelerating the decision-making lifecycle.
