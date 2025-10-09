# Engine B - AI Signal Processing Service
# InfinityAI.Pro Trading Platform
# Multi-stage Docker build with GPU support for Google Cloud

ARG PYTHON_VERSION=3.11
ARG BUILD_DATE
ARG GIT_COMMIT
ARG VERSION=1.0.0

# Build stage with GPU support (PyTorch CUDA 11.8 + cuDNN)
FROM pytorch/pytorch:2.1.1-cuda11.8-cudnn8-devel as builder

# Set build arguments
ARG BUILD_DATE
ARG GIT_COMMIT
ARG VERSION

# Avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    pkg-config \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    libjpeg-dev \
    libpng-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .

# Install Python dependencies (torch is preinstalled in base image)
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -r requirements.txt

# Production stage (PyTorch CUDA runtime)
FROM pytorch/pytorch:2.1.1-cuda11.8-cudnn8-runtime as production

# Set build arguments
ARG BUILD_DATE
ARG GIT_COMMIT
ARG VERSION

# Add labels for metadata
LABEL maintainer="InfinityAI.Pro Team" \
      version="${VERSION}" \
      description="Engine B - AI Signal Processing Service (GPU-Accelerated)" \
      build-date="${BUILD_DATE}" \
      git-commit="${GIT_COMMIT}" \
      component="ai-signal-processing-gpu"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libopenblas0-pthread \
    liblapack3 \
    libgomp1 \
    libjpeg62-turbo \
    libpng16-16 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r infinityai && useradd -r -g infinityai -s /bin/bash infinityai

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories for models and data
RUN mkdir -p /app/logs /app/data /app/tmp /app/models && \
    chown -R infinityai:infinityai /app

# Switch to non-root user
USER infinityai

# Set environment variables for GPU
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    INFINITYAI_ENV=production \
    LOG_LEVEL=INFO \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    USE_GPU=true \
    CUDA_VISIBLE_DEVICES=0 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${API_PORT}/health || exit 1

# Expose port (Cloud Run will set PORT; default to 8080)
EXPOSE 8080

# Default command (honor $PORT if provided)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

# Development stage (optional)
FROM production as development

# Switch back to root for development packages
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    vim \
    git \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python development tools
RUN pip install --no-cache-dir \
    jupyter \
    ipython \
    matplotlib \
    seaborn \
    plotly

# Switch back to non-root user
USER infinityai

# Override CMD for development
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]