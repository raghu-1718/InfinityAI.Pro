# =====================================================================
# InfinityAI.Pro - Engine C (Trade Execution & Order Optimization)
# Standalone Dockerfile for Cloud Run deployment from backend/engine-c
# =====================================================================
FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy shared modules from parent directory
COPY ../shared /app/shared

# Copy engine-c source code
COPY src /app/src

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8080

# Use the PORT environment variable set by Cloud Run
CMD exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}
