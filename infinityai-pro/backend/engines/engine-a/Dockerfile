# InfinityAI.Pro - Engine A (Market Data Ingestion Service)
# Multi-stage build for production optimization

ARG PYTHON_VERSION=3.11
ARG BUILD_DATE
ARG GIT_COMMIT
ARG VERSION=1.0.0

# Build stage
FROM python:${PYTHON_VERSION}-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG GIT_COMMIT 
ARG VERSION

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libcurl4-openssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:${PYTHON_VERSION}-slim as production

# Set build arguments
ARG BUILD_DATE
ARG GIT_COMMIT
ARG VERSION

# Add metadata labels
LABEL maintainer="InfinityAI.Pro Team"
LABEL version="${VERSION}"
LABEL build-date="${BUILD_DATE}"
LABEL git-commit="${GIT_COMMIT}"
LABEL description="Engine A - High-performance market data ingestion service"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    libssl3 \
    libffi8 \
    libcurl4 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r infinityai && useradd -r -g infinityai -s /bin/bash infinityai

WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
# Ensure dynamic libs path
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"

# Copy application code
COPY . .

# Create required directories and set ownership
RUN mkdir -p /app/logs /app/data /app/tmp && \
    chown -R infinityai:infinityai /app

# Set environment variables
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER infinityai

# Expose port
EXPOSE 8000

# Default command for production (use app logging setup; no external log-config file)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

# Note: Development stage removed to ensure production image is built by default.