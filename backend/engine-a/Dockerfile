# =====================================================================
# InfinityAI.Pro - Engine A (Orchestration & Risk Management)
# Cloud Run Optimized
# =====================================================================

FROM python:3.11-slim

# -----------------------------------------------------
# System dependencies (Numerical / ML / Optimization)
# -----------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libopenblas-dev \
    liblapack-dev \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------
# Application setup
# -----------------------------------------------------
WORKDIR /app

# Environment
ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=1000 \
    PIP_RETRIES=10 \
    PYTHONPATH=/app \
    NUMBA_CACHE_DIR=/tmp/numba_cache

# Copy dependency manifest first (layer caching)
COPY backend/engine-a/requirements.txt .

# Upgrade pip + install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --default-timeout=1000 --retries=10 -r requirements.txt

# COPY shared library (from parent backend context)
COPY backend/shared ./shared

# Copy application source
COPY backend/engine-a/src ./src

EXPOSE 8080

# -----------------------------------------------------
# Cloud Run entrypoint
# Single worker, async I/O (correct for FastAPI)
# -----------------------------------------------------
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
