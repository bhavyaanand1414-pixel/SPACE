# Presentation Deck: AI Multi-Temporal Satellite Change Intelligence Platform

Here is the slide-by-slide breakdown for your presentation. You can copy the bullet points directly into PowerPoint or Google Slides.

````carousel
# Slide 1: Title Slide
**AI Multi-Temporal Satellite Change Intelligence Platform**

* **Problem Statement:** SIH1518
* **Organization:** Ministry of Defence (MoD) / DGIS
* **Domain:** Space Tech & Artificial Intelligence
* **Team:** [Your Team Name]

*(Design Tip: Use a high-quality satellite image as the background with bold, centered text.)*

<!-- slide -->
# Slide 2: The Problem
**Why do we need this platform?**

* 🌍 **Massive Data Volume:** Terabytes of satellite imagery are generated daily; humans cannot process it all.
* ⏳ **Time-Consuming Analysis:** Manually comparing "before" and "after" images to find structural changes takes hours or days.
* 🎯 **Strategic Blindspots:** Critical assets (e.g., enemy camps, deforested areas) might be missed in vast landscapes.
* 🚨 **Need for Speed:** Defense & disaster response require real-time, actionable intelligence, not delayed reports.

<!-- slide -->
# Slide 3: Our Solution
**Automated Intelligence at Your Fingertips**

A centralized web platform that automates satellite analysis using Deep Learning.
* **Instant Change Detection:** Automatically highlights differences between temporal image pairs.
* **Semantic Search Engine:** Type "buildings near a river" and the AI instantly fetches matching satellite tiles.
* **Interactive GIS Map:** Visualize geospatial intelligence on an intuitive dashboard.
* **Automated Reporting:** Generate tactical PDF reports with one click.

<!-- slide -->
# Slide 4: System Architecture
**How does it work under the hood?**

* **Frontend (UI):** React.js + Vite + Tailwind CSS (Fast, modern, dark-mode command center UI)
* **Backend (API):** FastAPI + Python (Asynchronous, high-performance API)
* **AI/ML Engine:** PyTorch + OpenCLIP (Vision-Language embeddings)
* **Vector Database:** FAISS (Sub-millisecond retrieval of similar images)
* **Geospatial Processing:** PostGIS + Rasterio (Handling complex coordinates and map tiles)

<!-- slide -->
# Slide 5: Core Feature 1 - Semantic Search
**"Google Search" for Satellite Imagery**

* **The Tech:** We use Zero-Shot Vision-Language models (OpenCLIP).
* **The Process:** 
  1. Massive satellite images are sliced into 256x256 chips.
  2. The AI converts these chips into mathematical vectors.
  3. When an analyst types a query, it is matched against the image vectors.
* **The Result:** Instantly discover military assets, ships, or terrain changes using natural language.

<!-- slide -->
# Slide 6: Core Feature 2 - Change Detection
**Spotting the Invisible**

* **The Tech:** Convolutional Neural Networks (CNN) for Semantic Segmentation.
* **The Process:** 
  1. Upload Image A (e.g., Jan 2023) and Image B (e.g., Jan 2024).
  2. The Deep Learning model compares pixel structures.
* **The Result:** The platform draws precise bounding boxes around newly constructed buildings, destroyed bridges, or moved assets.

<!-- slide -->
# Slide 7: Live Demonstration
**System Walkthrough**

*(For this slide, switch to the live app or show a recorded video of the platform)*

**Key flows to show:**
1. The modern Dashboard interface.
2. Uploading an image.
3. Running the Semantic Search for "buildings near a river".
4. Showing the instant, flawless results grid.

<!-- slide -->
# Slide 8: Future Scope & Impact
**Scaling the Intelligence**

* **Conversational AI:** Adding an LLM Agent to let analysts "chat" with the satellite map.
* **Cloud Scaling:** Migrating to AWS/Azure for processing planet-scale datasets.
* **Strategic Impact:** Reduces analysis time by 90%, increases detection accuracy, and empowers national security forces with immediate intelligence.

<!-- slide -->
# Slide 9: Thank You
**Questions & Answers**

* **Team:** [Your Team Name]
* **Problem Statement:** SIH1518
* *"Transforming Pixels into Tactical Intelligence"*
````
