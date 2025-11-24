# backend/engine-analytics/README.md

## Engine Analytics - ML/AI Signals Generation

**Purpose**: Machine learning-based price predictions, sentiment analysis, and AI trading signals using TensorFlow and Gemini API.

**Technology**: Python, FastAPI, TensorFlow, Google Gemini, Firestore

### Directory Structure

```
engine-analytics/
├── src/
│   ├── api/
│   │   ├── routes_public/    # Signal endpoints, prediction API
│   │   └── routes_internal/  # Health, internal coordination
│   ├── services/
│   │   ├── ml_models/        # TensorFlow models for price prediction
│   │   ├── sentiment/        # Sentiment analysis pipeline
│   │   ├── orchestrators/    # Coordination with other engines
│   │   ├── firestore/        # Firestore R/W
│   │   └── gemini/           # Gemini API integration
│   ├── models/               # Pydantic schemas, signal definitions
│   ├── config/               # Config loading, model paths
│   └── __init__.py
├── tests/
│   ├── unit/                 # ML model unit tests
│   └── integration/          # Integration with Firestore, Gemini
├── models/                   # Trained TensorFlow model files (.h5, .pb)
├── Dockerfile
├── cloudrun.yaml
├── requirements.txt
└── README.md
```

### Environment Variables

```bash
# Development (.env)
PORT=8001
DEBUG=true
FIRESTORE_PROJECT=after-yesterday-473512-k3
GEMINI_API_KEY=your-gemini-key
ENGINE_CORE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Production (from Secret Manager)
GEMINI_API_KEY=<from Secret Manager: gemini-api-key>
ENGINE_CORE_URL=https://infinityai-engine-core-{hash}.a.run.app
```

### API Endpoints

#### Public
- `GET /api/ai-signals/{symbol}` - AI trading signals (BUY, SELL, HOLD)
- `GET /api/predictions/{symbol}` - ML price predictions (1h, 4h, 1d horizons)
- `POST /api/sentiment` - Sentiment analysis for news/social data
- `GET /api/recommendations` - Portfolio recommendations based on signals

#### Internal
- `GET /health` - Health check with model status

### Local Development

```bash
# Setup
cp config/env/dev/engine-analytics.env.example .env
pip install -r requirements.txt

# Download/prepare models (first run)
python src/config/download_models.py

# Run server
python src/main.py

# Run tests
pytest tests/
```

### Cloud Run Deployment

```bash
gcloud run deploy engine-analytics \
  --source . \
  --region us-central1 \
  --set-env-vars="GEMINI_API_KEY=projects/after-yesterday-473512-k3/secrets/gemini-api-key/versions/latest"
```

### ML Models

Pre-trained models stored in `models/`:
- `nifty_lstm.h5` - LSTM model for Nifty50 predictions
- `sensex_xgboost.pkl` - XGBoost for Sensex
- `banknifty_ensemble.h5` - Ensemble model for BankNifty

### Integration Points

- **Fetches from**: Engine Core (`/api/market-data/*`)
- **Sends to**: Engine Execution (`/api/signals/subscribe`), Frontend (WebSocket via Engine Execution)
- **External APIs**: Google Gemini for advanced analysis
- **Firestore**: Stores predictions, signals, model performance metrics

### Signal Format

```json
{
  "symbol": "NIFTY",
  "signal": "BUY",
  "confidence": 0.92,
  "price_target": 19250.50,
  "stop_loss": 18950.00,
  "reason": "Bullish divergence, Gemini sentiment positive",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Monitoring

```bash
# Check signal freshness
curl http://localhost:8001/api/ai-signals/NIFTY | jq '.timestamp'

# Monitor model accuracy
curl http://localhost:8001/health | jq '.components.models.accuracy'
```

### Troubleshooting

- **Model loading timeout**: Check model file sizes; may need to increase Cloud Run memory to 2GB
- **Gemini API errors**: Verify API key in Secret Manager; check quota limits
- **Stale signals**: Ensure Engine Core is running and providing fresh market data
- **High prediction latency**: Consider running on CPU vs GPU; adjust batch size in config
