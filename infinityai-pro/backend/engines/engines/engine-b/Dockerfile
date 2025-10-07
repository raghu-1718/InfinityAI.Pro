# Use PyTorch CUDA base image for GPU support
FROM pytorch/pytorch:latest

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV CUDA_DEVICE_ORDER=PCI_BUS_ID

# Create non-root user
RUN groupadd -r infinityai && useradd -r -g infinityai -d /app infinityai

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Create models directory
RUN mkdir -p /app/models

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to infinityai user
RUN chown -R infinityai:infinityai /app
USER infinityai

# Health check (honor PORT if provided)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD bash -c 'curl -f http://127.0.0.1:${PORT:-8000}/health || exit 1'

# Expose default port (Cloud Run may ignore EXPOSE but keep for clarity)
EXPOSE 8000

# Run the application (honor $PORT, default 8000)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]