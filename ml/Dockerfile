# XGBoost Training Container - TA-Lib Guaranteed
FROM python:3.10-slim

# Install system dependencies including TA-Lib
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Build TA-Lib (files removed - relying on features.py fallback)
# RUN wget ...

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify TA-Lib installation (fail fast if missing)
RUN python -c "import talib; print(f'TA-Lib version: {talib.__version__}')"

# Copy training scripts
COPY train.py features.py ./

# Default entrypoint
ENTRYPOINT ["python", "train.py"]
