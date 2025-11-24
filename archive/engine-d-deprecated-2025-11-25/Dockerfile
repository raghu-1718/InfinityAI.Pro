# Archived from `engines/engine-d` on 2025-11-25

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create engines dir and copy shared security middleware
RUN mkdir -p engines
COPY security_middleware.py engines/
COPY __init__.py engines/

# Copy requirements first for better caching (from engine-d subdir relative to build context)
COPY engine-d/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files (from engine-d subdir relative to build context)
COPY engine-d/ .

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the application with Uvicorn (bind to Cloud Run PORT)
CMD ["/bin/sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```