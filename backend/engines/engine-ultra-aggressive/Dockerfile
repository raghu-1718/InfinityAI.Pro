# Standardized Dockerfile for Ultra Aggressive Engine (Cloud Run)
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8080 ENVIRONMENT=production ULTRA_AGGRESSIVE_MODE=true
WORKDIR /app
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir fastapi uvicorn[standard] python-multipart websockets redis celery pandas numpy aiohttp python-dotenv
COPY backend/ultra_aggressive_main.py backend/real_ultra_aggressive_trader.py ./
RUN mkdir -p /app/logs && chmod +x ultra_aggressive_main.py
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl -f http://localhost:${PORT}/health || exit 1
EXPOSE ${PORT}
# Use shell form so ${PORT} is expanded at container runtime by the platform
CMD ["sh", "-c", "python -m uvicorn ultra_aggressive_main:app --host 0.0.0.0 --port ${PORT}"]
