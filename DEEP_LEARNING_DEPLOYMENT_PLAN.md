# Deep Learning Integration - Deployment & Verification Plan

**Project:** InfinityAI.Pro
**Phase:** Deep Learning + Options Integration
**GCP Project:** galvanic-pulsar-482815-h0
**Date:** 2025-01-XX
**Status:** Ready for Deployment

---

## Executive Summary

**Scope:** Integrated Options strategies (Greeks calculator, Iron Condor, spreads) + Deep Learning models (LSTM price forecasting, DQN trading agent) into existing ML ensemble.

**Impact:**

- **Options:** Black-Scholes Greeks, 4-leg strategies, P&L analysis
- **LSTM:** 30-day price forecasts using 60-day lookback
- **DQN:** Reinforcement learning Buy/Sell/Hold recommendations
- **Frontend:** New `/options` and `/ml` dashboard pages
- **Backend:** 5 new REST API endpoints in Engine-B

**Timeline:** 2-3 hours for complete deployment + verification

---

## Architecture Overview

### Backend Components (Engine-B)

#### 1. Options Analytics (`backend/shared/analytics/`)

**Files Created:**

- `greeks_calculator.py` (320 lines) - Black-Scholes Greeks calculator
- `options_strategies.py` (400+ lines) - Multi-leg strategies

**Greeks Calculator:**

```python
class BlackScholesGreeks:
    - calculate_greeks() → Delta, Gamma, Theta, Vega, Rho
    - calculate_option_price() → Theoretical price
    - calculate_portfolio_greeks() → Aggregate portfolio Greeks
    - calculate_implied_volatility() → Newton-Raphson IV solver
```

**Options Strategies:**

```python
class IronCondorStrategy:
    - 4-leg neutral strategy
    - Max profit: Net credit
    - Max loss: Strike width - Net credit

class BullCallSpreadStrategy:
    - 2-leg bullish strategy
    - Limited risk/reward

class CoveredCallStrategy:
    - Income generation
    - Sell OTM call on owned stock
```

#### 2. Deep Learning Models (`backend/engine-b/src/models/`)

**Files Created:**

- `lstm_model.py` (450+ lines) - LSTM price forecaster
- `dqn_agent.py` (500+ lines) - DQN trading agent

**LSTM Architecture:**

```
Input: 60-day OHLCV + indicators
├── LSTM Layer 1 (128 units, return sequences)
├── Dropout (0.2)
├── LSTM Layer 2 (64 units)
├── Dropout (0.2)
├── Dense (32 units, ReLU)
├── Dense (16 units, ReLU)
└── Output: 30-day price forecast
```

**DQN Architecture:**

```
State: Position, Balance, Price, Indicators, Momentum
├── Dense (128 units, ReLU)
├── Dropout (0.2)
├── Dense (64 units, ReLU)
├── Dropout (0.2)
├── Dense (32 units, ReLU)
└── Output: Q-values [HOLD, BUY, SELL]

Training: Experience Replay + Target Network
Reward: Sharpe ratio maximization
```

#### 3. API Endpoints (`backend/engine-b/src/main.py`)

**New Routes:**

```python
POST /api/v1/options/greeks           # Calculate Greeks
POST /api/v1/options/strategy         # Execute strategy
POST /api/v1/lstm/predict             # LSTM forecast
POST /api/v1/dqn/action               # DQN recommendation
GET  /api/v1/models/deep-learning     # Model status
```

### Frontend Components

#### 1. Options Dashboard (`frontend/web-app/src/app/(dashboard)/options/page.tsx`)

**Features:**

- Greeks calculator (Delta, Gamma, Theta, Vega, Rho)
- Strategy builder (Iron Condor, Bull/Bear spreads, Covered Call)
- P&L chart (profit/loss at different spot prices)
- Breakeven point calculation
- Risk/reward analysis

**Status:** ✅ Already exists (pre-existing implementation)

#### 2. ML Dashboard (`frontend/web-app/src/app/(dashboard)/ml/page.tsx`)

**Features:**

- LSTM 30-day forecast chart
- DQN action recommendation (BUY/SELL/HOLD)
- Q-value visualization
- Model status dashboard
- Integration guide

**Status:** ✅ Created (new implementation)

---

## Dependencies Added

### Backend (`backend/engine-b/requirements.txt`)

```txt
# Deep Learning
tensorflow>=2.13.0
keras>=2.13.0

# Scientific Computing
scipy>=1.10.0
```

**Note:** TensorFlow is **large** (~500MB). Docker image will increase from ~1.5GB to ~2GB.

---

## Deployment Plan

### Phase 1: Backend Deployment (Engine-B)

**Step 1: Update Engine-B Image**

```bash
# Navigate to Engine-B directory
cd c:\workspace\InfinityAI.Pro\backend\engine-b

# Build new Docker image with TensorFlow
gcloud builds submit --config=cloudbuild.yaml --project=galvanic-pulsar-482815-h0

# Expected build time: 10-15 minutes (TensorFlow compilation)
```

**Verification:**

```bash
# Check Cloud Build logs
gcloud builds log --project=galvanic-pulsar-482815-h0

# Verify image exists
gcloud container images list --repository=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai --project=galvanic-pulsar-482815-h0
```

**Step 2: Deploy to Cloud Run**

```bash
# Deploy updated Engine-B
gcloud run deploy engine-b \
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-b:latest \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --platform=managed \
  --allow-unauthenticated \
  --min-instances=1 \
  --max-instances=10 \
  --cpu=2 \
  --memory=4Gi \
  --timeout=300 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0"

# Expected deployment time: 3-5 minutes
```

**Memory Increase Justification:**

- **Previous:** 2Gi RAM
- **New:** 4Gi RAM (TensorFlow models + LSTM/DQN inference)
- **Cost Impact:** ~$10-15/month increase (minimal for production trading)

**Step 3: Verify Engine-B Endpoints**

```bash
# Set Engine-B URL
$ENGINE_B_URL = "https://engine-b-galvanic-pulsar-482815-h0.us-central1.run.app"

# Test health endpoint
curl "$ENGINE_B_URL/health"

# Test Greeks calculator
curl -X POST "$ENGINE_B_URL/api/v1/options/greeks" `
  -H "Content-Type: application/json" `
  -d '{
    "symbol": "NIFTY",
    "spot": 21000,
    "strike": 21500,
    "expiry": "2024-02-28",
    "volatility": 0.18,
    "option_type": "CE"
  }'

# Expected output: {"status":"success", "greeks":{"delta":0.45,"gamma":0.0001,...}}

# Test strategy execution
curl -X POST "$ENGINE_B_URL/api/v1/options/strategy" `
  -H "Content-Type: application/json" `
  -d '{
    "strategy_type": "iron_condor",
    "symbol": "NIFTY",
    "spot_price": 21000,
    "expiry": "2024-02-28",
    "parameters": {
      "call_short_strike": 21500,
      "call_long_strike": 21600,
      "put_short_strike": 20500,
      "put_long_strike": 20400,
      "lot_size": 50
    }
  }'

# Expected output: {"status":"success", "strategy":{"max_profit":5000,"max_loss":3000,...}}

# Test deep learning status
curl "$ENGINE_B_URL/api/v1/models/deep-learning"

# Expected output: {"status":"success", "lstm_models":{"count":0,...}}
```

**Note:** LSTM/DQN endpoints will return errors until models are trained. This is expected for initial deployment.

---

### Phase 2: Frontend Deployment

**Step 1: Build Next.js Application**

```bash
# Navigate to frontend directory
cd c:\workspace\InfinityAI.Pro\frontend\web-app

# Install dependencies (if new packages needed)
npm install recharts  # Chart library (likely already installed)

# Build production bundle
npm run build

# Expected build time: 2-3 minutes
```

**Step 2: Deploy to Vercel (Recommended) OR Cloud Run**

**Option A: Vercel (Recommended)**

```bash
# Install Vercel CLI (if not already)
npm install -g vercel

# Deploy
vercel --prod

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_ENGINE_B_URL=https://engine-b-galvanic-pulsar-482815-h0.us-central1.run.app
```

**Option B: Cloud Run**

```bash
# Build Docker image
cd c:\workspace\InfinityAI.Pro\frontend\web-app
docker build -t us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/web-app:latest .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/web-app:latest

# Deploy to Cloud Run
gcloud run deploy web-app \
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/web-app:latest \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --platform=managed \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=5 \
  --cpu=1 \
  --memory=512Mi \
  --set-env-vars="NEXT_PUBLIC_ENGINE_B_URL=https://engine-b-galvanic-pulsar-482815-h0.us-central1.run.app"
```

**Step 3: Verify Frontend Pages**

```bash
# Get frontend URL (Vercel or Cloud Run)
$FRONTEND_URL = "https://your-frontend-url.vercel.app"  # Or Cloud Run URL

# Test ML dashboard
Start-Process "$FRONTEND_URL/ml"

# Test Options dashboard
Start-Process "$FRONTEND_URL/options"

# Expected: Both pages load without errors, API status cards show data
```

---

## Model Training (Optional - Post-Deployment)

**LSTM Training:**

```python
# In Engine-B Cloud Run container (or locally)
from src.models.lstm_model import LSTMPriceForecaster
import pandas as pd

# Load historical data (1 year minimum)
data = fetch_historical_data("NIFTY", days=365)  # Would use DhanHQ or yfinance

# Train LSTM
forecaster = LSTMPriceForecaster("NIFTY")
metrics = forecaster.train(data, epochs=100)

# Save model (auto-saved to models/lstm/NIFTY.h5)
```

**DQN Training:**

```python
# Train DQN agent
from src.models.dqn_agent import train_dqn_agent

metrics = train_dqn_agent(
    symbol="NIFTY",
    historical_data=data,
    episodes=100
)

# Save model (auto-saved to models/dqn/NIFTY_dqn.h5)
```

**Note:** Training can be done asynchronously via Cloud Build or Cloud Run Job. Not required for initial deployment verification.

---

## End-to-End Verification Checklist

### Backend Tests

- [ ] **Health Check:** `GET /health` returns 200 OK
- [ ] **Greeks Calculator:** `POST /api/v1/options/greeks` returns Greeks (Delta, Gamma, Theta, Vega, Rho)
- [ ] **Strategy Execution:** `POST /api/v1/options/strategy` returns P&L chart + breakevens
- [ ] **Model Status:** `GET /api/v1/models/deep-learning` returns LSTM + DQN counts
- [ ] **LSTM Endpoint:** `POST /api/v1/lstm/predict` (returns 404 until trained - EXPECTED)
- [ ] **DQN Endpoint:** `POST /api/v1/dqn/action` (returns 404 until trained - EXPECTED)

### Frontend Tests

- [ ] **Options Page:** `/options` loads successfully
  - [ ] Greeks calculator form renders
  - [ ] Strategy selector form renders
  - [ ] Calculate Greeks button functional
  - [ ] Execute Strategy button functional
  - [ ] Greeks results display after calculation
  - [ ] P&L chart renders after strategy execution

- [ ] **ML Dashboard:** `/ml` loads successfully
  - [ ] Model status cards show data
  - [ ] Symbol selector functional
  - [ ] LSTM forecast tab renders
  - [ ] DQN agent tab renders
  - [ ] Integration guide card visible

### Integration Tests

- [ ] **Options → Backend:**
  - [ ] Calculate Greeks for NIFTY 21500 CE
  - [ ] Verify Delta between 0-1 for Call
  - [ ] Verify Theta is negative (time decay)
  - [ ] Execute Iron Condor strategy
  - [ ] Verify max_profit > 0
  - [ ] Verify P&L chart has 50+ data points

- [ ] **ML → Backend:**
  - [ ] Fetch model status
  - [ ] Verify LSTM count >= 0
  - [ ] Verify DQN count >= 0
  - [ ] Try LSTM forecast (may fail if not trained)
  - [ ] Try DQN action (may fail if not trained)

### Complete User Flow

- [ ] **Login** → Dashboard
- [ ] **Navigate** → Options page
- [ ] **Calculate Greeks** for NIFTY 21500 CE expiry 2024-02-28
- [ ] **Verify Greeks** display correctly
- [ ] **Execute Iron Condor** strategy (NIFTY spot 21000)
  - Call short: 21500, Call long: 21600
  - Put short: 20500, Put long: 20400
- [ ] **Verify P&L chart** shows profit zone between strikes
- [ ] **Navigate** → ML Dashboard
- [ ] **Select NIFTY** from watchlist
- [ ] **View Model Status** (LSTM/DQN counts)
- [ ] **Check Integration Guide** (ensemble + new models)

---

## Performance Metrics

### Backend (Engine-B)

**Expected Latency:**

- Greeks calculation: **<100ms** (pure computation)
- Strategy execution: **<200ms** (multiple Greeks + P&L calc)
- Model status: **<50ms** (file system check)
- LSTM forecast: **<500ms** (inference on trained model)
- DQN action: **<100ms** (forward pass through small network)

**Resource Usage:**

- CPU: 1-2 vCPUs (normal load), 2-4 vCPUs (training)
- Memory: 2-3Gi (inference), 4Gi+ (training)
- Cold start: 10-15s (TensorFlow load penalty)

### Frontend

**Expected Load Times:**

- Options page: **<2s** (initial render)
- ML dashboard: **<2s** (initial render)
- Greeks calculation: **<300ms** (round-trip to Engine-B)
- Strategy execution: **<400ms** (round-trip + chart render)

---

## Rollback Plan

**If deployment fails:**

### Backend Rollback

```bash
# Revert to previous Engine-B revision
gcloud run services update-traffic engine-b \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0
```

### Frontend Rollback (Vercel)

```bash
# Vercel dashboard: Deployments → Previous deployment → Promote to Production
```

### Frontend Rollback (Cloud Run)

```bash
# Revert to previous web-app revision
gcloud run services update-traffic web-app \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0
```

---

## Security & Compliance

### API Security

- ✅ All endpoints require HTTPS (enforced by Cloud Run)
- ✅ CORS configured for frontend domain only
- ✅ No authentication required for read-only endpoints (Options Greeks, Model status)
- ⚠️ Training endpoints should be protected (future: require API key)

### Data Privacy

- ✅ No PII in Greeks calculator (only symbol, strikes, expiry)
- ✅ No order placement in options strategies (analysis only)
- ✅ LSTM/DQN models trained on public market data (no user data)

### SEBI Compliance

- ✅ Options strategies are **advisory only** (no auto-execution)
- ✅ P&L charts show **theoretical** values (backtested, not live)
- ✅ DQN recommendations are **AI suggestions** (user must approve)
- ✅ Risk disclosure: Max loss displayed prominently in strategies

---

## Cost Analysis

### Incremental Costs (Monthly)

**Engine-B (Deep Learning):**

- Memory increase: 2Gi → 4Gi = **+$8/month** (assuming 50% utilization)
- TensorFlow image size: +500MB = **+$2/month** (Artifact Registry storage)

**Frontend (ML Dashboard):**

- New page: No incremental cost (same Next.js app)

**Total:** **~$10/month** increase

**ROI Justification:**

- Options Greeks: Industry-standard tool for traders (high user value)
- LSTM forecasts: 30-day predictions improve signal accuracy
- DQN agent: Reinforcement learning for optimal action selection
- **Expected:** Improved trading performance > $10/month cost

---

## Monitoring & Alerts

### Cloud Logging Queries

**Options API Errors:**

```
resource.type="cloud_run_revision"
resource.labels.service_name="engine-b"
textPayload=~"Greeks calculation error|Strategy execution error"
severity>=ERROR
```

**Deep Learning API Errors:**

```
resource.type="cloud_run_revision"
resource.labels.service_name="engine-b"
textPayload=~"LSTM prediction error|DQN action error"
severity>=ERROR
```

### Cloud Monitoring Metrics

- Engine-B CPU utilization: Alert if >80% for 5 minutes
- Engine-B Memory utilization: Alert if >90% for 5 minutes
- Engine-B Request latency: Alert if P95 >2s
- Engine-B Error rate: Alert if >5% over 5 minutes

---

## Next Steps (Post-Deployment)

### Phase 3: Model Training

1. **Collect Training Data:**
   - Fetch 1 year of historical OHLCV data for NIFTY, BANKNIFTY (DhanHQ or yfinance)
   - Calculate 20+ technical indicators (RSI, MACD, ATR, etc.)
   - Store in Cloud Storage or Firestore

2. **Train LSTM Models:**
   - Train for each watchlist symbol (7 symbols × 15 min/symbol = ~2 hours)
   - Save models to Cloud Storage (`gs://galvanic-pulsar-482815-h0-ml-models/lstm/`)
   - Deploy to Engine-B models directory

3. **Train DQN Agents:**
   - Train for each symbol (100 episodes × 7 symbols = ~3 hours)
   - Save agents to Cloud Storage (`gs://galvanic-pulsar-482815-h0-ml-models/dqn/`)
   - Deploy to Engine-B models directory

### Phase 4: Enhanced Integration

1. **Signals Page Enhancement:**
   - Add LSTM 30-day forecast to signal cards
   - Add DQN recommended action badge
   - Show confidence scores

2. **Auto-Trading Integration:**
   - Allow DQN agent to suggest position sizing
   - Combine DQN + XGBoost ensemble signals
   - Backtest DQN strategies

3. **Portfolio Greeks:**
   - Calculate aggregate Greeks for user's entire options portfolio
   - Real-time Greeks tracking (Delta, Gamma, Theta decay)
   - Hedging suggestions based on portfolio Greeks

### Phase 5: Advanced Features

1. **IV Surface Visualization:**
   - 3D implied volatility surface chart
   - Skew analysis (put/call IV difference)
   - Term structure (near-term vs far-term IV)

2. **Greeks Hedging:**
   - Delta-neutral position suggestions
   - Gamma scalping opportunities
   - Vega hedging (long/short vol positions)

3. **LSTM Enhancements:**
   - Multi-step forecasting (1d, 7d, 30d, 90d)
   - Confidence intervals (±1σ, ±2σ bands)
   - Feature importance (which indicators drive predictions)

4. **DQN Enhancements:**
   - Position sizing optimization (not just buy/sell)
   - Multi-asset portfolio management
   - Continuous action space (buy X shares vs binary buy/hold)

---

## Conclusion

**Deployment Readiness:** ✅ READY

**Risk Level:** LOW

- No changes to existing ML ensemble (XGBoost, LightGBM, CatBoost, RF)
- New endpoints are isolated (Options, LSTM, DQN)
- Frontend pages are new (no risk to existing dashboard)

**Expected Outcome:**

- ✅ Options Greeks calculator fully functional
- ✅ Options strategies (Iron Condor, spreads) working
- ✅ LSTM/DQN endpoints available (models pending training)
- ✅ ML dashboard displaying model status
- ⚠️ LSTM forecasts + DQN actions require model training (Phase 3)

**Timeline:**

- Backend deployment: 30 minutes
- Frontend deployment: 20 minutes
- E2E verification: 30 minutes
- **Total:** ~1.5 hours (excluding model training)

**Approval Required:** YES (Principal Cloud Solutions Architect)

---

**Prepared by:** GitHub Copilot AI Agent
**Review Status:** Pending
**Deployment Authorization:** Pending
