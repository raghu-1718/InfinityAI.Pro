# ML Model Training Guide

## Overview

This directory contains training scripts for InfinityAI.Pro's machine learning models:

1. **LSTM Price Forecaster** - 30-day price predictions using historical OHLCV data
2. **DQN Trading Agent** - Reinforcement learning agent for Buy/Sell/Hold decisions

## Files

```
training/
├── __init__.py              # Module exports
├── data_fetcher.py          # Historical data fetching + technical indicators
├── train_lstm.py            # LSTM training script
├── train_dqn.py             # DQN training script
├── train_all.py             # Master script (trains both models)
└── quick_train.py           # Quick test with small dataset
```

## Requirements

- TensorFlow 2.19+
- NumPy, Pandas, Scikit-learn
- yfinance (for historical data)
- Google Cloud Storage (optional, for model upload)

All dependencies are pre-installed in the Cloud Run `engine-b` container.

## Data Pipeline

### Data Fetcher (`data_fetcher.py`)

Fetches historical data and calculates 20+ technical indicators:

- **Price indicators**: RSI, MACD, Bollinger Bands, ATR
- **Volume indicators**: OBV, Volume Ratio
- **Momentum**: 5/10/20-day returns
- **Moving averages**: SMA(20,50), EMA(12,26)
- **Volatility**: 20-day rolling standard deviation

**Example:**

```python
from training.data_fetcher import get_training_data

# Fetch 2 years of NIFTY data with indicators
data = get_training_data("NIFTY", days=730)
print(data.shape)  # (600+, 25+)
```

## Training Scripts

### 1. LSTM Training (`train_lstm.py`)

**Architecture:**

- Input: 60-day lookback window
- LSTM Layer 1: 128 units
- LSTM Layer 2: 64 units
- Dense layers: 32 → 16 units
- Output: 30-day price forecast

**Command:**

```bash
python train_lstm.py \
  --symbol NIFTY \
  --days 730 \
  --lookback 60 \
  --forecast 30 \
  --epochs 100 \
  --batch-size 32 \
  --model-dir /app/models/lstm
```

**Parameters:**

- `--symbol`: Stock symbol (NIFTY, BANKNIFTY, FINNIFTY)
- `--days`: Historical days to fetch (default: 730)
- `--lookback`: Days used for prediction (default: 60)
- `--forecast`: Days to predict ahead (default: 30)
- `--epochs`: Max training epochs (default: 100)
- `--batch-size`: Batch size (default: 32)
- `--validation-split`: Train/val split (default: 0.2)

**Output:**

- Model file: `{symbol}.h5`
- Scalers: `{symbol}_scalers.json`
- Results: `{symbol}_training_results.json`

**Training Time:** ~5-15 minutes (depends on hardware)

### 2. DQN Training (`train_dqn.py`)

**Architecture:**

- Input: State vector (position, balance, price, indicators)
- Dense layers: 128 → 64 → 32 units
- Output: Q-values for 3 actions (HOLD, BUY, SELL)

**Features:**

- Experience replay buffer (10,000 experiences)
- Target network with soft updates
- Epsilon-greedy exploration (1.0 → 0.01)
- Reward shaping based on Sharpe ratio

**Command:**

```bash
python train_dqn.py \
  --symbol NIFTY \
  --days 730 \
  --episodes 200 \
  --gamma 0.95 \
  --learning-rate 0.001 \
  --batch-size 32 \
  --model-dir /app/models/dqn
```

**Parameters:**

- `--symbol`: Stock symbol
- `--days`: Historical days (default: 730)
- `--episodes`: Training episodes (default: 200)
- `--update-target`: Update target network every N episodes (default: 10)
- `--epsilon`: Initial exploration rate (default: 1.0)
- `--epsilon-decay`: Decay rate (default: 0.995)
- `--gamma`: Discount factor (default: 0.95)
- `--learning-rate`: Adam LR (default: 0.001)

**Output:**

- Model file: `{symbol}_dqn.h5`
- Results: `{symbol}_training_results.json`

**Training Time:** ~10-30 minutes (depends on episodes)

### 3. Master Training (`train_all.py`)

Runs both LSTM and DQN training sequentially, with optional GCS upload.

**Command:**

```bash
python train_all.py \
  --symbol NIFTY \
  --days 730 \
  --lstm-epochs 100 \
  --dqn-episodes 200 \
  --model-dir /app/models \
  --upload-gcs \
  --gcs-bucket galvanic-pulsar-482815-h0-models \
  --gcs-prefix trained_models
```

**Parameters:**

- All LSTM/DQN parameters
- `--upload-gcs`: Upload models to Google Cloud Storage
- `--gcs-bucket`: GCS bucket name
- `--gcs-prefix`: Path prefix in bucket

**Output:**

- Combined results: `{symbol}_complete_training_results.json`
- All model files
- GCS upload manifest (if enabled)

**Training Time:** ~20-45 minutes total

## Quick Testing

For rapid iteration during development:

```bash
python quick_train.py
```

Uses smaller dataset (365 days, 20 LSTM epochs, 50 DQN episodes).
**Time:** ~5-10 minutes
**Output:** `./models_local/`

## Cloud Run Training

### Option 1: One-time Job

Execute training directly in the deployed Cloud Run service:

```bash
# SSH into Cloud Run container
gcloud run services proxy engine-b \
  --region=asia-south1 \
  --project=galvanic-pulsar-482815-h0

# Inside container:
cd /app/src
python -m training.train_all \
  --symbol NIFTY \
  --upload-gcs \
  --gcs-bucket galvanic-pulsar-482815-h0-models
```

### Option 2: Cloud Build Training Job

Create a dedicated training Cloud Build job:

```yaml
# cloudbuild.training.yaml
steps:
  - name: "gcr.io/cloud-builders/docker"
    args:
      - "run"
      - "--rm"
      - "--network=host"
      - "asia-south1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-b:latest"
      - "python"
      - "-m"
      - "training.train_all"
      - "--symbol=NIFTY"
      - "--days=730"
      - "--lstm-epochs=100"
      - "--dqn-episodes=200"
      - "--upload-gcs"
timeout: 3600s # 1 hour
```

**Run:**

```bash
gcloud builds submit \
  --config=cloudbuild.training.yaml \
  --project=galvanic-pulsar-482815-h0
```

### Option 3: Scheduled Training (Cloud Scheduler)

Retrain models weekly/monthly:

```bash
# Create Cloud Scheduler job
gcloud scheduler jobs create http train-ml-models-weekly \
  --schedule="0 2 * * 0" \
  --uri="https://engine-b-r2f5flt77q-el.a.run.app/admin/train-models" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{"symbol":"NIFTY","days":730,"upload_gcs":true}' \
  --time-zone="Asia/Kolkata" \
  --location=asia-south1 \
  --project=galvanic-pulsar-482815-h0
```

## Model Storage

### Local (Development)

- Directory: `./models_local/`
- Used for quick testing

### Container (Production)

- Directory: `/app/models/`
- Mounted volume: `/app/models` → GCS bucket (optional)

### Google Cloud Storage (Recommended)

- Bucket: `galvanic-pulsar-482815-h0-models`
- Structure:
  ```
  trained_models/
  ├── lstm/
  │   ├── NIFTY.h5
  │   ├── NIFTY_scalers.json
  │   └── NIFTY_training_results.json
  ├── dqn/
  │   ├── NIFTY_dqn.h5
  │   └── NIFTY_training_results.json
  └── NIFTY_complete_training_results.json
  ```

## Model Loading in Production

The FastAPI endpoints automatically load models from `/app/models/`:

```python
# In main.py
@app.post("/api/v1/lstm/predict")
async def lstm_predict(request: LSTMRequest):
    from models.lstm_model import get_lstm_forecast

    # Loads from /app/models/lstm/NIFTY.h5
    forecast = get_lstm_forecast(
        symbol=request.symbol,
        recent_data=recent_data_df,
        model_dir="/app/models/lstm"
    )
    return forecast
```

## Monitoring Training

### Local Logs

```bash
tail -f training.log
```

### Cloud Run Logs

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=engine-b AND textPayload=~\"Training\"" \
  --limit=100 \
  --project=galvanic-pulsar-482815-h0
```

### Training Metrics

LSTM metrics (saved in results JSON):

- `final_loss`: MSE on training set
- `final_val_loss`: MSE on validation set
- `final_mae`: Mean Absolute Error
- `epochs_trained`: Actual epochs run
- `best_epoch`: Epoch with lowest validation loss

DQN metrics:

- `avg_reward`: Average reward per episode
- `avg_win_rate`: Percentage of profitable trades
- `total_return_pct`: Portfolio return percentage
- `final_epsilon`: Final exploration rate

## Troubleshooting

### Issue: "TensorFlow not available"

- **Cause**: Local environment doesn't have TensorFlow
- **Solution**: Train in Cloud Run container (has TensorFlow 2.19.1)

### Issue: "Insufficient data"

- **Cause**: `days` parameter too low or symbol has limited history
- **Solution**: Increase `--days` to 730+ for better model performance

### Issue: "Model not converging"

- **LSTM**: Increase `--epochs` or reduce `--batch-size`
- **DQN**: Increase `--episodes` or adjust `--learning-rate`

### Issue: "Out of memory"

- **Cause**: Batch size too large
- **Solution**: Reduce `--batch-size` to 16 or 8

### Issue: "GCS upload failed"

- **Cause**: Missing credentials or bucket permissions
- **Solution**: Ensure service account has Storage Object Creator role

## Next Steps

1. **Train models**: Run `train_all.py` in Cloud Run
2. **Upload to GCS**: Use `--upload-gcs` flag
3. **Test endpoints**: Call `/api/v1/lstm/predict` and `/api/v1/dqn/action`
4. **Schedule retraining**: Set up Cloud Scheduler for weekly updates
5. **Monitor performance**: Track prediction accuracy over time

## References

- LSTM Paper: [Hochreiter & Schmidhuber, 1997](https://www.bioinf.jku.at/publications/older/2604.pdf)
- DQN Paper: [Mnih et al., 2015](https://www.nature.com/articles/nature14236)
- Technical Indicators: [TA-Lib Documentation](https://mrjbq7.github.io/ta-lib/)

---

**Last Updated:** January 22, 2026
**Version:** 1.0.0
**Project:** InfinityAI.Pro (galvanic-pulsar-482815-h0)
