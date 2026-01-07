# =====================================================================
# InfinityAI.Pro - Engine C (Trade Execution & Order Optimization)
# ML: Scikit-learn, StatsModels, ARCH (Slippage & Volatility)
# =====================================================================
FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/engine-c/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY backend/shared /app/shared
COPY backend/engine-c/src /app/src

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Use the PORT environment variable set by Cloud Run (default to 8080 if not set)
CMD exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}
