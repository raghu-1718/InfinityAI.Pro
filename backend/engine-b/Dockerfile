# =====================================================================
# InfinityAI.Pro - Engine B (AI/ML Signal Generation)
# Production-grade Cloud Run image
# =====================================================================

FROM python:3.11-slim

# --------------------------------------------------
# System dependencies (ML runtime)
# --------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Environment (Robust pip download settings)
# --------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=1000 \
    PIP_RETRIES=10 \
    PYTHONPATH=/app

WORKDIR /app

# --------------------------------------------------
# Python dependencies (cached layer with CPU PyTorch index)
# --------------------------------------------------
COPY backend/engine-b/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 --retries=10 \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        -r requirements.txt

# Download NLTK data directly during build (Pre-cached in image)
RUN python -m nltk.downloader vader_lexicon punkt stopwords -d /usr/local/share/nltk_data

# --------------------------------------------------
# Shared library & Application source
# --------------------------------------------------
COPY backend/shared /app/shared
COPY backend/engine-b/src /app/src

# --------------------------------------------------
# Runtime directories
# --------------------------------------------------
RUN mkdir -p /app/models

# --------------------------------------------------
# Non-root user (Cloud Run best practice)
# --------------------------------------------------
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# --------------------------------------------------
# Expose & health
# --------------------------------------------------
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl -f http://localhost:8080/health || exit 1

# --------------------------------------------------
# Start service
# --------------------------------------------------
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
