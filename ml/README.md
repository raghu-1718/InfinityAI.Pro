# ML Training Pipeline

Production-ready machine learning training pipeline for InfinityAI.Pro trading models.

## Overview

This directory contains the automated retraining pipeline for XGBoost models used in Engine B inference. Training runs weekly via Cloud Scheduler, with versioned models stored in Google Cloud Storage.

## Architecture

```
Cloud Scheduler (Weekly)
     ↓
Cloud Build Trigger
     ↓
Docker Build (TA-Lib guaranteed)
     ↓
Train XGBoost Model
     ↓
Upload to GCS (gs://gen-lang-client-0779271931-ml-models/)
     ↓
Engine B loads latest model on startup
```

## Files

- **`features.py`**: Feature engineering (RSI, EMA, MACD, ATR, returns)
- **`train.py`**: XGBoost training script with GCS integration
- **`requirements.txt`**: Python dependencies
- **`Dockerfile`**: Container with TA-Lib pre-installed
- **`cloudbuild.yaml`**: CI/CD pipeline configuration

## Manual Training

```bash
# Build Docker image
docker build -t xgb-trainer .

# Run training locally
docker run --rm \
  -v ~/.config/gcloud:/root/.config/gcloud \
  xgb-trainer \
  --dataset=gs://gen-lang-client-0779271931-ml-models/data/ohlcv_latest.csv \
  --model_uri=gs://gen-lang-client-0779271931-ml-models/xgb/model_manual.json
```

## Cloud Build Training

```bash
# Trigger Cloud Build
gcloud builds submit . --config=cloudbuild.yaml
```

## Automated Retraining

Weekly retraining runs every Sunday at 2 AM UTC via Cloud Scheduler.

**Setup:**
```bash
# Create Cloud Build trigger
gcloud builds triggers create manual retrain-xgb \
  --region=us-central1 \
  --build-config=ml/cloudbuild.yaml \
  --repo=https://github.com/YOUR_REPO \
  --branch=main

# Create Cloud Scheduler job
gcloud scheduler jobs create http retrain-xgb \
  --schedule="0 2 * * 0" \
  --location=us-central1 \
  --uri="https://cloudbuild.googleapis.com/v1/projects/gen-lang-client-0779271931/triggers/TRIGGER_ID:run" \
  --http-method=POST \
  --oauth-service-account-email=429140669077@cloudbuild.gserviceaccount.com
```

## Model Versioning

Models are saved with timestamps:
- **Versioned:** `gs://.../xgb/model_$BUILD_ID.json`
- **Latest:** `gs://.../xgb/latest.json` (symlink)
- **Metadata:** `gs://.../xgb/model_$BUILD_ID_metadata.json`

## Engine B Integration

Engine B loads the latest model on startup:

```python
from google.cloud import storage
import xgboost as xgb

# Download latest model
client = storage.Client()
bucket = client.bucket("gen-lang-client-0779271931-ml-models")
bucket.blob("xgb/latest.json").download_to_filename("/tmp/model.json")

# Load model
model = xgb.XGBClassifier()
model.load_model("/tmp/model.json")
```

## Features

The model uses the following technical indicators:
- RSI (14)
- EMA (10, 20, 50)
- MACD
- ATR (14)
- Bollinger Bands
- Price returns (1-day, 5-day, 10-day)
- Volume ratio
- Volatility (20-day)

**Target:** Next candle direction (binary: up/down)

## Monitoring

**View training logs:**
```bash
gcloud logging read 'resource.type="cloud_build"' --limit=20
```

**Check model accuracy:**
```bash
gsutil cat gs://gen-lang-client-0779271931-ml-models/xgb/latest_metadata.json
```

## Cost

- Cloud Build: ~$0.50/month (4 runs @ 10 min each)
- Cloud Storage: ~$0.03/month (10 MB models)
- Cloud Scheduler: ~$0.10/month

**Total: ~$0.63/month**

## Support

For issues or questions, see main README or contact the Infrastructure team.
