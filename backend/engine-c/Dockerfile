# =====================================================================
# InfinityAI.Pro - Engine C (Trade Execution & Order Optimization)
# Fixed Dockerfile for Cloud Run deployment from backend/engine-c
# =====================================================================
FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
# Copy requirements and install dependencies
COPY backend/engine-c/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy engine-c source code
COPY backend/engine-c/src /app/src
COPY backend/shared /app/shared

# Copy shared modules if they exist (optional)
# Note: Cloud Build will handle this from the build context
RUN mkdir -p /app/shared

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/src:/app/shared
ENV ENGINE_C_MODE=live

EXPOSE 8080

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
