# 🚀 InfinityAI.Pro Multi-Stage Production Dockerfile
# This builds both frontend and backend with proper static file serving

# ============================================================================
# STAGE 1: Build React Frontend
# ============================================================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY frontend/ ./

# Build production frontend
RUN npm run build

# ============================================================================
# STAGE 2: Python Backend with Frontend Integration
# ============================================================================
FROM python:3.9-slim AS backend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy backend requirements
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/build ./static

# Create static directory structure
RUN mkdir -p static/js static/css static/media

# Ensure static files are in correct locations
RUN if [ -d "./static/static" ]; then \
      cp -r ./static/static/* ./static/ && \
      rm -rf ./static/static; \
    fi

# Create startup script
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

echo "🚀 Starting InfinityAI.Pro Production Server"
echo "📁 Static files:"
find ./static -type f -name "*.js" -o -name "*.css" | head -10

echo "🌐 Server starting on port \$PORT"
uvicorn main:app --host 0.0.0.0 --port \$PORT --workers 1
EOF

RUN chmod +x /app/start.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["/app/start.sh"]