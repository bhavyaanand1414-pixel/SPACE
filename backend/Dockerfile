# ==============================================================================
# SIH1518 — Backend Dockerfile (Multi-Stage Production Build)
# ==============================================================================

FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system geospatial libraries & build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    gdal-bin \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specifications
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Runtime Stage
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH" \
    PYTHONPATH="/app:/app/backend:/app/ml:$PATH" \
    GDAL_DATA="/usr/share/gdal" \
    PROJ_LIB="/usr/share/proj"

# Install runtime shared libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local

# Create persistent storage directories
RUN mkdir -p /app/data/storage /app/data/storage/reports /app/ml/checkpoints

# Copy application source code
COPY . .

EXPOSE 8000

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Entrypoint launches FastAPI Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
