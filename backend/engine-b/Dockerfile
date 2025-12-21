# =====================================================================
# InfinityAI.Pro - Engine B (AI/ML Signal Generation)
# Production-grade Cloud Run image
# =====================================================================

FROM python:3.11-slim

# --------------------------------------------------
# System dependencies (ML runtime)
# --------------------------------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Environment
# --------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# --------------------------------------------------
# Python dependencies (cached layer)
# --------------------------------------------------
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# --------------------------------------------------
# NLTK assets (explicit + resilient)
# --------------------------------------------------
RUN python - <<EOF
import nltk
for pkg in ["punkt", "punkt_tab", "stopwords", "vader_lexicon"]:
    try:
        nltk.download(pkg, quiet=True)
    except Exception as e:
        print(f"NLTK download failed for {pkg}: {e}")
EOF

# --------------------------------------------------
# Application source
# --------------------------------------------------
COPY src /app/src

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
