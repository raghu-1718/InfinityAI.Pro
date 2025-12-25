# =====================================================================
# InfinityAI.Pro - Engine A (Orchestration & Risk Management)
# =====================================================================

FROM python:3.11-slim

# System dependencies for numerical optimization (cvxpy solvers)
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libatlas-base-dev \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifest first for layer caching
COPY requirements.txt .

# Install Python dependencies (locked + reproducible)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src ./src

# Environment
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV NUMBA_CACHE_DIR=/tmp/numba_cache

EXPOSE 8080

# Cloud Run best practice: single worker, async I/O
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
