# ML Model Training & Deployment Guide

## 🚀 Quick Start

### 1. Train Models via Cloud Build (Recommended)

```bash
# Train both LSTM + DQN models
gcloud builds submit \
  --config=backend/engine-b/cloudbuild.training.yaml \
  --project=galvanic-pulsar-482815-h0 \
  --substitutions=_SYMBOL=NIFTY,_DAYS=730,_LSTM_EPOCHS=100,_DQN_EPISODES=200
```

**Duration:** ~45 minutes
**Output:** Models uploaded to `gs://galvanic-pulsar-482815-h0-models/trained_models/`

### 2. Train via API Endpoint

```bash
# Trigger training via deployed engine-b service
curl -X POST https://engine-b-228557716858.us-central1.run.app/admin/train-models \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NIFTY",
    "days": 730,
    "upload_gcs": true
  }'
```

**Response:**

```json
{
  "status": "training_started",
  "symbol": "NIFTY",
  "message": "Training started in background. Check logs for progress.",
  "estimated_duration_minutes": "20-45",
  "started_at": "2026-01-22T12:00:00Z"
}
```

### 3. Monitor Training Progress

```bash
# View real-time logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=engine-b AND textPayload=~\"Training\"" \
  --limit=50 \
  --format="table(timestamp,textPayload)" \
  --project=galvanic-pulsar-482815-h0
```

---

## 📊 Training Options

### Option A: Cloud Build (Batch Training)

**Pros:**

- Dedicated compute (no interference with API traffic)
- Automatic GCS upload
- Better for large datasets/long training
- Can use high-CPU machines (8+ vCPU)

**Cons:**

- Must manually trigger
- Separate from API service

**Command:**

```bash
gcloud builds submit \
  --config=backend/engine-b/cloudbuild.training.yaml \
  --project=galvanic-pulsar-482815-h0
```

### Option B: API Endpoint (Background Task)

**Pros:**

- Trigger via HTTP (can integrate with UI/scheduler)
- Uses deployed service (no separate build)
- Easy to automate

**Cons:**

- Runs in same container as API (may affect latency)
- Subject to Cloud Run timeout limits
- Limited CPU allocation

**Command:**

```bash
curl -X POST https://engine-b-228557716858.us-central1.run.app/admin/train-models \
  -H "Content-Type: application/json" \
  -d '{"symbol":"NIFTY","upload_gcs":true}'
```

### Option C: Scheduled Weekly Training

**Setup Cloud Scheduler:**

```bash
gcloud scheduler jobs create http train-ml-models-weekly \
  --schedule="0 2 * * 0" \
  --uri="https://engine-b-228557716858.us-central1.run.app/admin/train-models" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{"symbol":"NIFTY","days":730,"upload_gcs":true}' \
  --time-zone="Asia/Kolkata" \
  --location=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --attempt-deadline=3600s
```

**Schedule:** Every Sunday at 2:00 AM IST
**Timeout:** 1 hour

---

## 🗂️ Model Storage Strategy

### Local (Development)

```
./models_local/
├── lstm/
│   ├── NIFTY.h5
│   ├── NIFTY_scalers.json
│   └── NIFTY_training_results.json
└── dqn/
    ├── NIFTY_dqn.h5
    └── NIFTY_training_results.json
```

### Cloud Run Container

```
/app/models/
├── lstm/ (mounted from GCS)
├── dqn/
└── complete_results.json
```

### Google Cloud Storage (Production)

```
gs://galvanic-pulsar-482815-h0-models/
└── trained_models/
    ├── lstm/
    │   ├── NIFTY.h5 (TensorFlow model)
    │   ├── NIFTY_scalers.json (MinMaxScaler params)
    │   └── NIFTY_training_results.json
    ├── dqn/
    │   ├── NIFTY_dqn.h5
    │   └── NIFTY_training_results.json
    └── NIFTY_complete_training_results.json
```

---

## 🔄 Model Lifecycle

### 1. Initial Training

```bash
# First-time training
gcloud builds submit --config=backend/engine-b/cloudbuild.training.yaml
```

### 2. Download to Cloud Run

```bash
# Mount GCS bucket to Cloud Run (optional, but recommended)
gcloud run services update engine-b \
  --add-volume=name=models,type=cloud-storage,bucket=galvanic-pulsar-482815-h0-models \
  --add-volume-mount=volume=models,mount-path=/app/models_gcs \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0
```

Alternatively, download models at container startup:

```bash
# Add to Dockerfile startup script
gsutil -m cp -r gs://galvanic-pulsar-482815-h0-models/trained_models/* /app/models/
```

### 3. Serve Predictions

```bash
# LSTM forecast
curl -X POST https://engine-b-228557716858.us-central1.run.app/api/v1/lstm/predict \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NIFTY",
    "days_ahead": 30,
    "historical_data": []
  }'

# DQN action recommendation
curl -X POST https://engine-b-228557716858.us-central1.run.app/api/v1/dqn/action \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NIFTY",
    "current_price": 21500,
    "position": 0,
    "market_data": {}
  }'
```

### 4. Retrain Periodically

```bash
# Weekly via Cloud Scheduler (see Option C above)
# Or manually trigger when market regime changes
```

---

## 📈 Training Parameters

### LSTM Parameters

| Parameter    | Default | Range    | Impact                                       |
| ------------ | ------- | -------- | -------------------------------------------- |
| `days`       | 730     | 365-1460 | More data = better generalization            |
| `lookback`   | 60      | 30-120   | Larger window = captures longer trends       |
| `forecast`   | 30      | 7-90     | Prediction horizon                           |
| `epochs`     | 100     | 50-200   | More epochs = better fit (watch overfitting) |
| `batch_size` | 32      | 16-64    | Smaller = slower but more stable             |

### DQN Parameters

| Parameter       | Default    | Range              | Impact                                 |
| --------------- | ---------- | ------------------ | -------------------------------------- |
| `days`          | 730        | 365-1460           | More episodes for exploration          |
| `episodes`      | 200        | 100-500            | More episodes = better policy          |
| `epsilon`       | 1.0 → 0.01 | 0.5-1.0 → 0.01-0.1 | Exploration vs exploitation            |
| `gamma`         | 0.95       | 0.9-0.99           | Discount factor (future reward weight) |
| `learning_rate` | 0.001      | 0.0001-0.01        | Smaller = more stable                  |

---

## ✅ Verification Checklist

### After Training

- [ ] Check training logs for completion

  ```bash
  gcloud logging read \
    "resource.type=cloud_run_revision AND textPayload=~\"Training complete\"" \
    --limit=1
  ```

- [ ] Verify GCS upload

  ```bash
  gsutil ls -r gs://galvanic-pulsar-482815-h0-models/trained_models/
  ```

- [ ] Check model files exist

  ```bash
  gsutil cat gs://galvanic-pulsar-482815-h0-models/trained_models/NIFTY_complete_training_results.json
  ```

- [ ] Test LSTM endpoint

  ```bash
  curl https://engine-b-228557716858.us-central1.run.app/api/v1/models/deep-learning
  ```

- [ ] Test prediction (if models mounted)
  ```bash
  # Should return forecast, not 404
  curl -X POST https://engine-b-228557716858.us-central1.run.app/api/v1/lstm/predict \
    -H "Content-Type: application/json" \
    -d '{"symbol":"NIFTY","days_ahead":30,"historical_data":[]}'
  ```

---

## 🛠️ Troubleshooting

### Issue: "TensorFlow not available"

**Solution:** Training must run in Cloud Run container (has TensorFlow 2.19.1)

```bash
# Verify TensorFlow in container
docker run --rm us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-b:latest \
  python -c "import tensorflow as tf; print(tf.__version__)"
```

### Issue: "Model not found" in prediction endpoint

**Solution:** Download models from GCS to `/app/models/`

```bash
# Option 1: Mount GCS bucket (see "Model Lifecycle" section)

# Option 2: Download at startup (add to startup script)
gsutil -m cp -r gs://galvanic-pulsar-482815-h0-models/trained_models/lstm /app/models/
gsutil -m cp -r gs://galvanic-pulsar-482815-h0-models/trained_models/dqn /app/models/
```

### Issue: "Training timeout"

**Solution:** Increase Cloud Run timeout or use Cloud Build

```bash
# Increase Cloud Run timeout to max (3600s)
gcloud run services update engine-b \
  --timeout=3600 \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0
```

### Issue: "Out of memory"

**Solution:** Increase Cloud Run memory or reduce batch size

```bash
# Increase to 8Gi
gcloud run services update engine-b \
  --memory=8Gi \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0
```

---

## 📌 Current Deployment Status

### Backend (Cloud Run)

- **Service:** engine-b
- **Revision:** engine-b-00037-2jz
- **URL:** https://engine-b-228557716858.us-central1.run.app
- **Memory:** 4Gi
- **CPU:** 2 vCPU
- **Timeout:** 300s (5 minutes)

### Frontend (Firebase)

- **URL:** https://galvanic-pulsar-482815-h0.web.app
- **Routes:** `/ml` (ML Dashboard), `/options` (Greeks & Strategies)

### Models

- **Status:** ⏳ Not yet trained
- **Next Step:** Run Cloud Build training job

---

## 🎯 Next Steps

1. **Create GCS Bucket for Models**

   ```bash
   gsutil mb -p galvanic-pulsar-482815-h0 -c STANDARD -l us-central1 \
     gs://galvanic-pulsar-482815-h0-models/
   ```

2. **Run Initial Training**

   ```bash
   gcloud builds submit \
     --config=backend/engine-b/cloudbuild.training.yaml \
     --project=galvanic-pulsar-482815-h0
   ```

3. **Mount Models to Cloud Run** (or download at startup)

4. **Test Predictions**

5. **Set Up Weekly Retraining** (Cloud Scheduler)

6. **Monitor Performance** (track prediction accuracy over time)

---

**Last Updated:** January 22, 2026
**Project:** InfinityAI.Pro (galvanic-pulsar-482815-h0)
**Documentation:** See `backend/engine-b/src/training/README.md` for detailed training docs
