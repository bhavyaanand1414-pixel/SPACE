# SIH1518: Deployment & Operational Runbook

Comprehensive deployment manual for **SIH1518: AI-Powered Multi-Temporal Satellite Change Intelligence Platform (ISRO)**.

---

## 1. System Architecture Overview

```
                                    CLIENT BROWSER
                         (React + MapLibre/Leaflet + Tailwind)
                                         │
                                         ▼ [Port 5173 / 80]
                             [ NGINX REVERSE PROXY ]
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
            / (Static SPA Bundle)                  /api/v1/ (FastAPI ASGI)
                                                              │
                                                              ▼
                                                 [ BACKEND WORKERS ]
                                                • PyTorch Siamese U-Net
                                                • 2D FFT Co-Registration
                                                • ReportLab PDF Engine
                                                • 20 AI Agent Tools
                                                              │
                                         ┌────────────────────┴────────────────────┐
                                         ▼                                         ▼
                               [ POSTGIS DATABASE ]                        [ REDIS CACHE ]
                              (Port 5432: Spatial EPSG)                   (Port 6379: Broker)
```

---

## 2. Quickstart with Docker Compose (Recommended)

### Prerequisites
- **Docker Engine** $\ge 24.0$ & **Docker Compose** $\ge 2.20$
- Minimum hardware: 4 CPU cores, 8 GB RAM, 20 GB free disk space

### Step 1: Clone Repository & Configure Environment
```bash
git clone https://github.com/organization/SIH1518.git
cd SIH1518
cp .env.example .env
# Edit .env with your custom credentials (do not commit .env to Git)
```

### Step 2: Build & Start Containers
```bash
docker compose up --build -d
```

### Step 3: Verify Running Services
```bash
docker compose ps
```
Expected output:
| Service | Container | Status | Ports |
|---|---|---|---|
| `postgis` | `sih1518_postgis` | Healthy | `0.0.0.0:5432->5432/tcp` |
| `redis` | `sih1518_redis` | Healthy | `0.0.0.0:6379->6379/tcp` |
| `backend` | `sih1518_backend` | Healthy | `0.0.0.0:8000->8000/tcp` |
| `frontend` | `sih1518_frontend` | Healthy | `0.0.0.0:5173->80/tcp` |

### Step 4: Access Application
- **Frontend Web Cockpit**: [http://localhost:5173](http://localhost:5173)
- **FastAPI OpenAPI Swagger**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Backend Health Endpoint**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 3. Native Development & Bare-Metal Setup

### 3.1 Backend Setup (Python 3.11)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Run Database Migrations
```bash
alembic upgrade head
```

#### Start FastAPI Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.2 Frontend Setup (Node.js 20)
```bash
cd frontend
npm install
npm run dev
```

---

## 3. Production Cloud Architecture & Monorepo Deployment Mapping

The SIH1518 monorepo is structured for turnkey multi-cloud deployment:

```
sih1518/
├── frontend/          → 🚀 Vercel (Global Edge CDN SPA)
├── backend/           → ⚡ Render (FastAPI Docker Web Service)
├── ml/                → 🧠 Render (Packaged alongside Backend runtime)
├── data/              → ☁️ Cloudflare R2 / AWS S3 (Satellite Rasters - Zero Egress)
├── reports/           → 📄 Cloudflare R2 / AWS S3 (PDF Reports & XAI Dossiers)
├── docs/              → 📚 GitHub (ISRO Technical Documentation)
├── scripts/           → 🛠️ GitHub / Backend Sync & Healthcheck Tools
├── docker/            → 🐳 Render / Production Docker Packaging
├── docker-compose.yml → 💻 Local Development (PostGIS + Redis + App)
├── .env.example       → 🔑 GitHub (Deployment Environment Blueprint)
└── README.md          → 📖 GitHub (Master System Overview)
```

### A. Deploy Frontend to Vercel (`frontend/`)
1. Connect your GitHub repository in the **Vercel Dashboard**.
2. Set **Root Directory** to `frontend` (or leave as root with `vercel.json`).
3. Set **Framework Preset** to `Vite`.
4. Configure **Environment Variable**:
   ```
   VITE_API_BASE_URL=https://sih1518-backend.onrender.com/api/v1
   ```
5. Click **Deploy**. Vercel will build the SPA bundle with client-side routing.

---

### B. Deploy Backend & ML to Render (`backend/` + `ml/`)
1. In the **Render Dashboard**, click **New > Blueprint** and select your GitHub repo (it reads `render.yaml`).
2. Alternatively, create a **Web Service (Docker runtime)**:
   - **Dockerfile Path**: `./docker/Dockerfile.backend`
   - **Docker Context**: `.`
   - **Region**: `Singapore` (or closest to India)
   - **Health Check Path**: `/api/v1/health`
3. Link your **PostGIS Database** and **Redis** instance.
4. Set production environment variables (e.g., `SECRET_KEY`, `S3_*`).

---

### C. Connect Satellite Data & Reports to Cloudflare R2 / S3 (`data/` & `reports/`)
Cloudflare R2 provides an S3-compatible API with **zero egress fees**, making it optimal for large multi-spectral satellite imagery and high-resolution PDF dossiers.

1. In Cloudflare Dashboard, go to **R2 Object Storage > Create Bucket** named `sih1518-storage`.
2. Generate **R2 API Tokens** (Admin Read/Write).
3. Set in your Render backend environment:
   ```bash
   STORAGE_TYPE=s3
   S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
   S3_ACCESS_KEY_ID=<your_r2_access_key>
   S3_SECRET_ACCESS_KEY=<your_r2_secret_key>
   S3_BUCKET_NAME=sih1518-storage
   S3_REGION_NAME=auto
   ```
4. Sync local baseline rasters to R2 via the sync script:
   ```bash
   python scripts/sync_r2_storage.py --direction upload
   ```

---

## 4. Environment Variables Dictionary

| Variable | Default Value | Description |
|---|---|---|
| `ENVIRONMENT` | `production` | Environment mode (`development`, `staging`, `production`) |
| `DEBUG` | `false` | Enables verbose stack traces when `true` |
| `SECRET_KEY` | *(Random 64-char)* | JWT and internal signing key |
| `BACKEND_PORT` | `8000` | Exposed port for FastAPI ASGI server |
| `FRONTEND_PORT` | `5173` | Exposed port for React Nginx frontend |
| `DATABASE_URL` | `postgresql://...` | PostGIS connection URI |
| `REDIS_URL` | `redis://redis:6379/0` | Redis caching & async broker URI |
| `STORAGE_TYPE` | `local` / `s3` | Storage backend (`local` or `s3` for Cloudflare R2) |
| `S3_ENDPOINT_URL` | *(Cloudflare R2)* | Endpoint URL for R2 / S3 storage |
| `S3_BUCKET_NAME` | `sih1518-storage` | Object storage bucket name |
| `MODEL_DEVICE` | `cpu` | PyTorch inference hardware (`cpu`, `cuda`, `mps`) |
| `CORS_ORIGINS` | `["https://*.vercel.app"]` | Allowed CORS origins JSON list |

---

## 5. Production Security & Hardening Checklist

1. **Zero Secret Leakage**: No passwords or API keys are committed to Git or baked into Docker images.
2. **Non-Root Execution**: Container processes run with restricted privilege isolation.
3. **CORS Boundary Enforcement**: API limits cross-origin access to explicitly declared origins.
4. **Input Sanitization**: File uploads enforce MIME validation, size caps (2 GB), and path traversal sanitization.
5. **Mandatory Scientific Advisory Disclaimers**: All PDF reports, API outputs, and UI cards include non-causal preliminary disclaimers.

