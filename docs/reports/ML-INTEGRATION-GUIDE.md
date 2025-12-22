# =====================================================================
# InfinityAI.Pro - ML/AI Integration Guide
# =====================================================================
# Complete guide for the Enterprise AI/ML Backend (Engine B)
# =====================================================================

## 🤖 Overview

Engine B has been enhanced with **enterprise-grade ML/AI capabilities** using the following frameworks:

### Integrated Libraries

| Library | Category | Purpose | Status |
|---------|----------|---------|--------|
| **TensorFlow** | Deep Learning | Neural networks, advanced ML | ✅ Integrated |
| **PyTorch** | Deep Learning | Research, dynamic graphs | ✅ Integrated |
| **Keras** | Deep Learning | High-level neural network API | ✅ Integrated |
| **Scikit-learn** | Machine Learning | Classical ML algorithms | ✅ Active |
| **XGBoost** | Gradient Boosting | Optimized gradient boosting | ✅ Active |
| **LightGBM** | Gradient Boosting | Fast gradient boosting | ✅ Active |
| **Transformers** | NLP | Pre-trained language models | ✅ Integrated |
| **OpenCV** | Computer Vision | Image processing | ✅ Integrated |
| **NLTK** | NLP | Natural language processing | ✅ Integrated |
| **spaCy** | NLP | Industrial NLP | ✅ Integrated |
| **MLflow** | ML Platform | Experiment tracking | ✅ Integrated |
| **H2O.ai** | AutoML | Automated machine learning | ✅ Integrated |

---

## 🏗️ Architecture

### ML Model Store

```python
class MLModelStore:
    - random_forest: RandomForestClassifier
    - xgboost: XGBClassifier
    - lightgbm: LGBMClassifier
    - sentiment: Transformers pipeline (NLP)
    - scalers: Feature normalization
```

### Feature Engineering Pipeline

```python
class FeatureEngineer:
    - Technical Indicators (30+ features)
    - Moving Averages (SMA, EMA)
    - Momentum Indicators (RSI, MACD)
    - Volatility Measures (ATR, Bollinger Bands)
    - Volume Analysis (OBV)
    - Pattern Recognition
```

---

## 📡 API Endpoints

### 1. Signal Generation (Primary)

**Endpoint**: `POST /api/v1/signal`

```bash
curl -X POST https://engine-core-xxx.run.app/api/v1/signal \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "fast": false
  }'
```

**Response**:
```json
{
  "symbol": "RELIANCE",
  "signal": "BUY",
  "confidence": 78.5,
  "predicted_price": 2456.32,
  "timestamp": "2025-11-28T10:30:00.000Z",
  "model_version": "ai-ml-3.0-enterprise"
}
```

### 2. Batch Signal Generation

**Endpoint**: `POST /api/v1/signal/batch`

```bash
curl -X POST https://engine-core-xxx.run.app/api/v1/signal/batch \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["RELIANCE", "TCS", "INFY", "HDFCBANK"],
    "fast": true
  }'
```

**Response**:
```json
{
  "signals": [
    {"symbol": "RELIANCE", "signal": "BUY", ...},
    {"symbol": "TCS", "signal": "HOLD", ...}
  ],
  "timestamp": "...",
  "total_symbols": 4
}
```

### 3. Sentiment Analysis

**Endpoint**: `POST /api/v1/sentiment`

```bash
curl -X POST https://engine-core-xxx.run.app/api/v1/sentiment \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Reliance Industries posts record quarterly profits, beats analyst estimates"
  }'
```

**Response**:
```json
{
  "text": "Reliance Industries posts record...",
  "sentiment": "POSITIVE",
  "confidence": 0.95,
  "timestamp": "..."
}
```

### 4. Model Management

**List Models**: `GET /api/v1/models`

```bash
curl https://engine-core-xxx.run.app/api/v1/models
```

**Response**:
```json
[
  {
    "name": "random_forest",
    "type": "ensemble",
    "framework": "scikit-learn",
    "status": "loaded"
  },
  {
    "name": "xgboost",
    "type": "gradient_boosting",
    "framework": "xgboost",
    "status": "loaded"
  }
]
```

### 5. Model Training

**Endpoint**: `POST /api/v1/train`

```bash
curl -X POST https://engine-core-xxx.run.app/api/v1/train \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "historical_days": 30
  }'
```

**Response**:
```json
{
  "status": "training_scheduled",
  "symbol": "RELIANCE",
  "historical_days": 30,
  "message": "Model training started in background"
}
```

### 6. Health & Capabilities

**Endpoint**: `GET /healthz`

```bash
curl https://engine-core-xxx.run.app/healthz
```

**Response**:
```json
{
  "status": "healthy",
  "service": "engine-b-ai-ml",
  "version": "ai-ml-3.0-enterprise",
  "capabilities": {
    "tensorflow": true,
    "pytorch": true,
    "transformers": true,
    "sklearn": true,
    "xgboost": true,
    "lightgbm": true
  },
  "timestamp": "..."
}
```

---

## 🔧 Installation & Setup

### 1. Install Dependencies

```bash
cd backend/engine-core
pip install -r requirements.txt
```

**For GPU support (optional)**:

```bash
# TensorFlow with GPU
pip install tensorflow-gpu>=2.15.0

# PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 2. Download NLP Models (First Run)

```bash
# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 3. Environment Variables

```bash
export GOOGLE_CLOUD_PROJECT="gen-lang-client-0779271931"
export DHAN_CLIENT_ID="<from_secret_manager>"
export DHAN_ACCESS_TOKEN="<from_secret_manager>"
```

---

## 🎯 Feature Engineering

### Technical Indicators Generated

```python
features = [
    # Moving Averages
    'sma_5', 'sma_10', 'sma_20', 'sma_50',
    'ema_5', 'ema_10', 'ema_20',

    # Momentum
    'rsi_14', 'rsi_7',
    'macd', 'macd_signal', 'macd_histogram',
    'momentum_10', 'momentum_20',
    'roc_10', 'roc_20',

    # Volatility
    'atr_14',
    'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_position',

    # Stochastic
    'stoch_k', 'stoch_d',

    # Volume
    'obv', 'volume_sma_20', 'volume_ratio',

    # Returns
    'daily_return', 'log_return',

    # Trends
    'trend_5_20', 'trend_10_50'
]
```

### Usage Example

```python
from services.feature_engineer import feature_engineer
import pandas as pd

# Load OHLCV data
df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# Generate all features
features = feature_engineer.generate_all_features(df)

# Select top 10 most important features
top_features = feature_engineer.select_top_features(
    X=features[feature_engineer.get_feature_columns()],
    y=labels,
    n_features=10
)
```

---

## 🧠 Model Training Workflow

### 1. Prepare Training Data

```python
import numpy as np
import pandas as pd
from services.ml_model_manager import model_manager

# Load historical data
df = pd.read_csv('historical_data.csv')

# Generate features
features = feature_engineer.generate_all_features(df)

# Prepare X (features) and y (labels)
X = features[feature_engineer.get_feature_columns()].values
y = (df['close'].shift(-1) > df['close']).astype(int).values  # 1 = price up, 0 = price down
```

### 2. Train Models

```python
# Train all models
results = model_manager.train_models(X, y)

print(results)
# Output:
# {
#   'random_forest': {'train_accuracy': 0.85, 'test_accuracy': 0.78},
#   'xgboost': {'train_accuracy': 0.88, 'test_accuracy': 0.82},
#   'lightgbm': {'train_accuracy': 0.87, 'test_accuracy': 0.81}
# }
```

### 3. Make Predictions

```python
# Single model prediction
predictions = model_manager.predict(X_new, model_name='xgboost')

# Ensemble prediction (weighted voting)
ensemble_pred = model_manager.ensemble_predict(
    X_new,
    model_names=['random_forest', 'xgboost', 'lightgbm'],
    weights=[0.3, 0.4, 0.3]
)
```

---

## 🚀 Production Deployment

### Docker Build with ML Libraries

```bash
cd backend/engine-core

# Build image (includes all ML dependencies)
docker build -t gcr.io/gen-lang-client-0779271931/engine-core:ml-v3 .

# Push to GCR
docker push gcr.io/gen-lang-client-0779271931/engine-core:ml-v3

# Deploy to Cloud Run (requires 2GB+ memory for ML models)
gcloud run deploy engine-core \
  --image=gcr.io/gen-lang-client-0779271931/engine-core:ml-v3 \
  --platform=managed \
  --region=us-central1 \
  --memory=4Gi \
  --cpu=2 \
  --timeout=300 \
  --set-secrets="DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest"
```

### Resource Requirements

| Configuration | Memory | CPU | Use Case |
|--------------|--------|-----|----------|
| **Minimum** | 2Gi | 1 | Basic inference |
| **Recommended** | 4Gi | 2 | Production ML |
| **High Load** | 8Gi | 4 | Deep learning + NLP |

---

## 📊 Performance Optimization

### 1. Model Caching

Models are loaded once on startup and cached in memory:

```python
MODEL_STORE = MLModelStore()  # Global singleton
```

### 2. Batch Processing

Use batch endpoints for multiple symbols:

```python
# ✅ Efficient
POST /api/v1/signal/batch with 10 symbols

# ❌ Inefficient
10 x POST /api/v1/signal
```

### 3. Fast Mode

Use `fast=true` for low-latency predictions:

```json
{
  "symbol": "RELIANCE",
  "fast": true
}
```

---

## 🔬 Advanced Features

### MLflow Integration (Coming Soon)

```python
import mlflow

# Track experiments
mlflow.start_run()
mlflow.log_param("model", "xgboost")
mlflow.log_metric("accuracy", 0.82)
mlflow.sklearn.log_model(model, "model")
mlflow.end_run()
```

### H2O AutoML (Coming Soon)

```python
import h2o
from h2o.automl import H2OAutoML

# Auto-train best model
aml = H2OAutoML(max_runtime_secs=300)
aml.train(x=features, y='target', training_frame=train_df)
```

---

## 📚 Reference Documentation

- **Scikit-learn**: https://scikit-learn.org/
- **XGBoost**: https://xgboost.readthedocs.io/
- **LightGBM**: https://lightgbm.readthedocs.io/
- **Transformers**: https://huggingface.co/docs/transformers/
- **TensorFlow**: https://www.tensorflow.org/
- **PyTorch**: https://pytorch.org/

---

## 🐛 Troubleshooting

### Issue: "ImportError: No module named tensorflow"

```bash
pip install tensorflow>=2.15.0
```

### Issue: "Sentiment analysis not available"

```bash
pip install transformers>=4.35.0
python -c "from transformers import pipeline; pipeline('sentiment-analysis')"
```

### Issue: "Memory exceeded in Cloud Run"

Increase memory allocation:
```bash
gcloud run services update engine-core --memory=4Gi
```

---

**Status**: Production Ready ✅
**Version**: 3.0-enterprise
**Last Updated**: November 28, 2025
