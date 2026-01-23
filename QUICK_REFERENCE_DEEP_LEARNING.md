# Deep Learning Integration - Quick Reference

**Project:** InfinityAI.Pro
**Phase:** Options + Deep Learning
**Status:** ✅ Ready for Deployment

---

## File Structure

```
backend/
├── shared/
│   └── analytics/
│       ├── greeks_calculator.py         # 320 lines - Black-Scholes Greeks
│       └── options_strategies.py        # 420 lines - Iron Condor, spreads
│
├── engine-b/
│   ├── src/
│   │   ├── models/
│   │   │   ├── lstm_model.py           # 470 lines - LSTM forecaster
│   │   │   └── dqn_agent.py            # 530 lines - DQN trading agent
│   │   │
│   │   └── main.py                     # Updated - 5 new endpoints
│   │
│   └── requirements.txt                # Updated - tensorflow, keras, scipy

frontend/
└── web-app/
    └── src/
        └── app/(dashboard)/
            ├── options/page.tsx        # 360 lines - Existing
            └── ml/page.tsx             # 440 lines - NEW

docs/
├── DEEP_LEARNING_DEPLOYMENT_PLAN.md         # 50 pages
└── DEEP_LEARNING_IMPLEMENTATION_SUMMARY.md  # 40 pages
```

---

## API Endpoints

### Options Analytics

```bash
# Calculate Greeks
curl -X POST https://engine-b-galvanic-pulsar-482815-h0.us-central1.run.app/api/v1/options/greeks \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NIFTY",
    "spot": 21000,
    "strike": 21500,
    "expiry": "2024-02-28",
    "volatility": 0.18,
    "option_type": "CE"
  }'

# Execute Strategy
curl -X POST https://engine-b-galvanic-pulsar-482815-h0.us-central1.run.app/api/v1/options/strategy \
  -H "Content-Type: application/json" \
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
```

### Deep Learning

```bash
# Model Status
curl https://engine-b-galvanic-pulsar-482815-h0.us-central1.run.app/api/v1/models/deep-learning

# LSTM Forecast (requires trained model)
curl -X POST https://engine-b-galvanic-pulsar-482815-h0.us-central1.run.app/api/v1/lstm/predict \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NIFTY",
    "recent_data": []  # 60 days of OHLCV
  }'

# DQN Action (requires trained agent)
curl -X POST https://engine-b-galvanic-pulsar-482815-h0.us-central1.run.app/api/v1/dqn/action \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NIFTY",
    "current_state": []  # State vector
  }'
```

---

## Python Usage

### Greeks Calculator

```python
from backend.shared.analytics.greeks_calculator import BlackScholesGreeks
from datetime import datetime, timedelta

# Calculate Greeks
greeks = BlackScholesGreeks.calculate_greeks(
    spot=21000,
    strike=21500,
    time_to_expiry=0.25,  # 3 months
    volatility=0.18,
    option_type="CE"
)

print(f"Delta: {greeks['delta']:.4f}")
print(f"Gamma: {greeks['gamma']:.4f}")
print(f"Theta: {greeks['theta']:.2f}")
print(f"Vega: {greeks['vega']:.2f}")
print(f"Rho: {greeks['rho']:.2f}")

# Calculate Implied Volatility
iv = BlackScholesGreeks.calculate_implied_volatility(
    spot=21000,
    strike=21500,
    time_to_expiry=0.25,
    option_price=250,
    option_type="CE"
)
print(f"Implied Volatility: {iv:.2%}")
```

### Options Strategies

```python
from backend.shared.analytics.options_strategies import create_strategy

# Iron Condor
strategy = create_strategy(
    "iron_condor",
    symbol="NIFTY",
    spot_price=21000,
    expiry="2024-02-28",
    call_short_strike=21500,
    call_long_strike=21600,
    put_short_strike=20500,
    put_long_strike=20400,
    lot_size=50
)

# Get Summary
summary = strategy.summary()
print(f"Max Profit: ₹{summary['max_profit']}")
print(f"Max Loss: ₹{summary['max_loss']}")
print(f"Risk/Reward: {summary['risk_reward_ratio']:.2f}")

# Get P&L Chart
pnl_data = strategy.calculate_pnl_range(20000, 22000, steps=50)
# Returns: [{"spot": 20000, "pnl": -3000}, ...]

# Get Breakevens
breakevens = strategy.breakeven_points(20000, 22000)
print(f"Breakeven Points: {breakevens}")
```

### LSTM Forecaster

```python
from src.models.lstm_model import LSTMPriceForecaster
import pandas as pd

# Create forecaster
forecaster = LSTMPriceForecaster("NIFTY")

# Train model
data = pd.read_csv("nifty_1year.csv")  # OHLCV + indicators
metrics = forecaster.train(data, epochs=100)

# Generate forecast
recent_data = data.tail(60)  # Last 60 days
forecast = forecaster.predict(recent_data)

print(f"Current Price: ₹{forecast['current_price']}")
print(f"30-Day Prediction: ₹{forecast['predicted_price_30d']}")
print(f"Price Change: ₹{forecast['price_change']} ({forecast['price_change_pct']:.2f}%)")
```

### DQN Agent

```python
from src.models.dqn_agent import train_dqn_agent, get_dqn_action
import numpy as np

# Train agent
metrics = train_dqn_agent(
    symbol="NIFTY",
    historical_data=data,
    episodes=100
)

# Get action recommendation
state = np.array([...])  # Current state vector
action = get_dqn_action("NIFTY", state)

print(f"Recommended Action: {action['recommended_action']}")
print(f"Confidence: {action['confidence']:.2f}")
print(f"Q-Values: {action['q_values']}")
```

---

## Frontend Usage

### Options Page

```typescript
// Navigate to /options
// Use Greeks calculator tab:
// - Enter symbol, spot, strike, expiry, volatility, option_type
// - Click "Calculate Greeks"
// - View Delta, Gamma, Theta, Vega, Rho

// Use Strategies tab:
// - Select strategy type (Iron Condor, Bull Call Spread, etc.)
// - Enter parameters (strikes, lot size)
// - Click "Execute Strategy"
// - View P&L chart, max profit/loss, breakevens
```

### ML Dashboard

```typescript
// Navigate to /ml
// View model status cards (LSTM count, DQN count)

// LSTM Forecast tab:
// - Select symbol from watchlist
// - Click "Generate Forecast"
// - View 30-day forecast chart
// - View current price, predicted price, % change

// DQN Agent tab:
// - Select symbol from watchlist
// - Click "Get Recommendation"
// - View recommended action (BUY/SELL/HOLD)
// - View Q-values for all actions
```

---

## Deployment Commands

### Backend (Engine-B)

```powershell
# Build Docker image
cd c:\workspace\InfinityAI.Pro\backend\engine-b
gcloud builds submit --config=cloudbuild.yaml --project=galvanic-pulsar-482815-h0

# Deploy to Cloud Run
gcloud run deploy engine-b `
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-b:latest `
  --region=us-central1 `
  --project=galvanic-pulsar-482815-h0 `
  --platform=managed `
  --allow-unauthenticated `
  --min-instances=1 `
  --max-instances=10 `
  --cpu=2 `
  --memory=4Gi `
  --timeout=300 `
  --set-env-vars="GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0"
```

### Frontend (Vercel)

```powershell
cd c:\workspace\InfinityAI.Pro\frontend\web-app

# Install dependencies
npm install

# Build
npm run build

# Deploy
vercel --prod

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_ENGINE_B_URL=https://engine-b-galvanic-pulsar-482815-h0.us-central1.run.app
```

---

## Testing Checklist

### Backend

- [ ] GET /health → 200 OK
- [ ] POST /api/v1/options/greeks → Returns Greeks
- [ ] POST /api/v1/options/strategy → Returns P&L chart
- [ ] GET /api/v1/models/deep-learning → Returns model counts

### Frontend

- [ ] /options → Loads without errors
- [ ] /ml → Loads without errors
- [ ] Greeks calculator → Calculates and displays
- [ ] Strategy builder → Executes and displays P&L chart
- [ ] ML dashboard → Shows model status

---

## Common Issues

### Issue: TensorFlow ImportError

```bash
Error: ModuleNotFoundError: No module named 'tensorflow'

Fix:
pip install tensorflow>=2.13.0 keras>=2.13.0
```

### Issue: LSTM/DQN Endpoint Returns 404

```json
{"error": "Model not trained", "symbol": "NIFTY"}

Reason: Models not trained yet (expected)
Fix: Train models (Phase 3) or show placeholder message in UI
```

### Issue: Greeks Calculator Returns Infinity

```bash
Error: ZeroDivisionError in Black-Scholes formula

Reason: time_to_expiry = 0 (expired option)
Fix: Add validation: time_to_expiry > 0
```

---

## Performance Benchmarks

**Expected Latencies:**

- Greeks calculation: **<100ms**
- Strategy execution: **<200ms**
- LSTM inference: **<500ms**
- DQN action: **<100ms**
- Model status: **<50ms**

**Resource Usage:**

- Engine-B: 2-3Gi RAM (inference), 4Gi+ (training)
- Cold start: 10-15s (TensorFlow load penalty)
- Image size: ~2GB (with TensorFlow)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                   │
│  ┌──────────────┐                  ┌──────────────┐    │
│  │   Options    │                  │      ML      │    │
│  │  Dashboard   │                  │  Dashboard   │    │
│  └──────────────┘                  └──────────────┘    │
└──────────────────────┬─────────────────┬────────────────┘
                       │                 │
                       │   REST API      │
                       │                 │
┌──────────────────────┴─────────────────┴────────────────┐
│                Engine-B (FastAPI)                        │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────┐ │
│  │    Options     │  │      LSTM      │  │    DQN    │ │
│  │   Analytics    │  │   Forecaster   │  │   Agent   │ │
│  ├────────────────┤  ├────────────────┤  ├───────────┤ │
│  │ Greeks Calc    │  │ 60d → 30d      │  │ BUY/SELL  │ │
│  │ Iron Condor    │  │ Price Forecast │  │   HOLD    │ │
│  │ Bull/Bear      │  │                │  │           │ │
│  └────────────────┘  └────────────────┘  └───────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Existing ML Ensemble (No Changes)          │ │
│  │  XGBoost (40%) + LightGBM (30%) + CatBoost (15%)  │ │
│  │  + RandomForest (15%)                              │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## Key Files Summary

| File                    | Purpose              | Lines | Status      |
| ----------------------- | -------------------- | ----- | ----------- |
| `greeks_calculator.py`  | Black-Scholes Greeks | 320   | ✅ Complete |
| `options_strategies.py` | Multi-leg strategies | 420   | ✅ Complete |
| `lstm_model.py`         | LSTM forecaster      | 470   | ✅ Complete |
| `dqn_agent.py`          | DQN trading agent    | 530   | ✅ Complete |
| `main.py` (Engine-B)    | API endpoints        | +180  | ✅ Complete |
| `options/page.tsx`      | Options UI           | 360   | ✅ Existing |
| `ml/page.tsx`           | ML dashboard         | 440   | ✅ Complete |

**Total:** 2,720 lines of new/updated code

---

## Next Actions

1. **Review** implementation summary
2. **Review** deployment plan
3. **Authorize** backend deployment
4. **Authorize** frontend deployment
5. **Execute** E2E verification
6. **Plan** Phase 3 (model training)

---

**Quick Links:**

- [Implementation Summary](./DEEP_LEARNING_IMPLEMENTATION_SUMMARY.md)
- [Deployment Plan](./DEEP_LEARNING_DEPLOYMENT_PLAN.md)
- [Engine-B API](https://engine-b-galvanic-pulsar-482815-h0.us-central1.run.app)
- [Frontend (TBD)](https://your-frontend-url.vercel.app)

**Support:** GitHub Copilot AI Agent
