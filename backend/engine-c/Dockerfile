# =====================================================================
# InfinityAI.Pro - Engine C (Trade Execution & Order Optimization)
# Fixed Dockerfile for Cloud Run deployment from backend/engine-c
# =====================================================================
FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Environment variables
ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=1000 \
    PIP_RETRIES=10 \
    PYTHONPATH=/app:/app/src:/app/shared \
    ENGINE_C_MODE=live

# Copy requirements and install dependencies
COPY backend/engine-c/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 --retries=10 -r requirements.txt

# Copy engine-c source code & shared
COPY backend/engine-c/src /app/src
COPY backend/shared /app/shared

RUN mkdir -p /app/shared

EXPOSE 8080

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
