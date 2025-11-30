# InfinityAI.Pro - Enterprise AI-Powered Trading Platform

<div align="center">

![Version](https://img.shields.io/badge/version-3.5--production-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![Cloud Run](https://img.shields.io/badge/GCP-Cloud%20Run-4285F4)
![Firebase](https://img.shields.io/badge/Firebase-Hosting%20%2B%20Auth-FFCA28)
![DhanHQ](https://img.shields.io/badge/Broker-DhanHQ-orange)
![License](https://img.shields.io/badge/license-MIT-green)

**An enterprise-grade AI/ML trading platform for Indian markets (NSE/BSE) with real-time signal generation, risk management, and automated execution**

[Live Platform](https://infinityai.pro) · [Engine-A API](https://engine-a.infinityai.pro/docs) · [Engine-B API](https://engine-b.infinityai.pro/docs) · [Engine-C API](https://engine-c.infinityai.pro/docs)

</div>

---

## 🎯 Platform Overview

InfinityAI.Pro is a production-ready algorithmic trading platform combining **5+ ensemble ML models** with **DhanHQ brokerage integration** for real-time trading signals and automated order execution. Built on Google Cloud Platform with a microservices architecture.

### Key Features

- 🤖 **AI-Powered Signal Generation** - Ensemble ML (XGBoost, LightGBM, CatBoost, Random Forest)
- 📊 **Advanced Risk Management** - VaR, CVaR, Sharpe, Sortino, Kelly Criterion
- 📈 **Real-Time Trade Execution** - Direct DhanHQ API integration
- 🔐 **Multi-User Authentication** - Firebase Auth + Google Sign-In
- 🌐 **Custom Domain Deployment** - infinityai.pro with SSL
- 💹 **Technical Analysis** - RSI, MACD, ADX, EMA, Bollinger Bands
- 🧠 **NLP Sentiment Analysis** - NLTK VADER + Transformers
- 📱 **Modern Dashboard** - Next.js 15 + Tailwind + shadcn/ui

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         InfinityAI.Pro - Live Architecture                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   ┌───────────────────┐          ┌──────────────────────────────────────────┐   │
│   │   Frontend App    │          │           Google Cloud Platform           │   │
│   │                   │          │                                            │   │
│   │  infinityai.pro   │◄────────►│  ┌────────────────────────────────────┐  │   │
│   │   (Next.js 15)    │          │  │         Cloud Run Engines          │  │   │
│   │                   │          │  │                                    │  │   │
│   └───────────────────┘          │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│           │                      │  │  │Engine-A  │  │Engine-B  │  │Engine-C  │  │
│           ▼                      │  │  │Orchestr. │─►│  AI/ML   │─►│Execution │  │
│   ┌───────────────────┐          │  │  │  + Risk  │  │ Signals  │  │ DhanHQ   │  │
│   │  Firebase Hosting │          │  │  └──────────┘  └──────────┘  └──────────┘  │
│   │    + Auth         │          │  └────────────────────────────────────┘  │   │
│   │    + Firestore    │          │                     │                     │   │
│   └───────────────────┘          │  ┌──────────────────▼───────────────────┐│   │
│                                  │  │       Google Secret Manager          ││   │
│                                  │  │  (User Credentials - Encrypted)      ││   │
│                                  │  └──────────────────────────────────────┘│   │
│                                  └──────────────────────────────────────────┘   │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Live Endpoints

| Component | URL | Description |
|-----------|-----|-------------|
| **Frontend** | https://infinityai.pro | Main trading dashboard |
| **Engine-A** | https://engine-a.infinityai.pro | Orchestration & Risk Management |
| **Engine-B** | https://engine-b.infinityai.pro | AI/ML Signal Generation |
| **Engine-C** | https://engine-c.infinityai.pro | Trade Execution (DhanHQ) |

---

## ⚙️ Engine Details

### Engine A - Orchestration & Risk Management
**Version:** 3.5-advanced-risk

Central orchestrator managing authentication, risk calculations, and inter-engine coordination.

#### ML Capabilities
- Risk Scoring & Position Sizing
- Value at Risk (VaR) - Historical, Parametric, Cornish-Fisher
- Conditional VaR (CVaR) / Expected Shortfall
- Sharpe & Sortino Ratios
- Kelly Criterion for position sizing
- Portfolio Risk (Ledoit-Wolf covariance)
- Maximum Drawdown Analysis

#### Key Endpoints
```
GET  /health                    - Health check
GET  /api/auth/dhan/validate    - Validate Dhan OAuth token
POST /api/v1/risk/score         - Calculate risk score
POST /api/v1/risk/var           - Value at Risk
POST /api/v1/risk/cvar          - Conditional VaR
POST /api/v1/risk/comprehensive - All risk metrics
POST /api/v1/risk/kelly         - Kelly Criterion
POST /api/v1/risk/portfolio     - Portfolio risk
POST /api/v1/trade/start        - Full trade orchestration
```

---

### Engine B - AI/ML Signal Generation
**Version:** v3.5-prod-weighted-ensemble

AI/ML intelligence layer with ensemble models for signal generation.

#### ML Models (Weighted Voting)
| Model | Weight | Purpose |
|-------|--------|---------|
| XGBoost | 40% | Primary gradient boosting |
| LightGBM | 30% | Fast gradient boosting |
| CatBoost | 15% | Categorical features |
| Random Forest | 15% | Ensemble diversity |
| NLTK Sentiment | - | News sentiment |

#### Technical Indicators
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- ADX (Average Directional Index)
- EMA 20/50/200 (Exponential Moving Averages)
- Bollinger Bands

#### Key Endpoints
```
GET  /health                        - Health check with capabilities
GET  /api/v1/market/status          - Current market status
GET  /api/v1/capabilities           - ML framework capabilities
GET  /api/v1/models/ensemble-weights - Model weights
POST /api/v1/signal                 - Single stock signal
POST /api/v1/signal/batch           - Batch signals (multiple stocks)
POST /api/v1/sentiment              - NLP sentiment analysis
POST /api/v1/position/analyze       - AI position analysis
POST /api/v1/portfolio/analyze      - Portfolio-wide analysis
```

#### Signal Response Example
```json
{
  "symbol": "RELIANCE",
  "signal": "HOLD",
  "confidence": 66.0,
  "predicted_price": 1567.5,
  "analysis": {
    "rsi": 72.96,
    "adx": 52.6,
    "trend": "Neutral",
    "key_factors": ["RSI Overbought", "Above EMA 50", "MACD Bullish"]
  },
  "model_version": "v3.5-prod-weighted-ensemble-rules",
  "data_source": "yahoo"
}
```

---

### Engine C - Trade Execution
**Version:** 3.5-enhanced-execution

Trade execution engine with DhanHQ integration and ML-based order optimization.

#### ML Capabilities
- Slippage Prediction
- Order Timing Optimization
- TWAP/VWAP Order Splitting
- Execution Analytics

#### Key Endpoints
```
GET  /health                          - Health check
GET  /api/dhan/funds                  - Account funds
GET  /api/dhan/positions              - Open positions
GET  /api/dhan/holdings               - Holdings
GET  /api/dhan/orders                 - Today's orders
POST /api/dhan/place-order            - Place order
POST /api/dhan/cancel-order           - Cancel order
POST /api/v1/optimize/slippage        - Predict slippage
GET  /api/v1/optimize/timing/{symbol} - Optimal timing
POST /api/v1/optimize/split           - Order splitting
POST /api/v1/user/credentials         - Save user credentials
GET  /api/v1/user/credentials         - Get credential status
POST /api/v1/user/verify              - Verify connection
```

---

## 🖥️ Frontend Dashboard

### Technology Stack
- **Framework:** Next.js 15 (App Router)
- **Styling:** Tailwind CSS + shadcn/ui
- **State:** Zustand + React Query
- **Auth:** Firebase Authentication (Google Sign-In)
- **Charts:** Recharts
- **Hosting:** Firebase Hosting

### Features
- Real-time engine status monitoring
- Live portfolio & positions tracking
- AI-powered position analysis
- ML signal generation dashboard
- Risk metrics visualization
- Order placement with risk check
- Multi-user Dhan account connection

### Pages
| Route | Description |
|-------|-------------|
| `/` | Dashboard with system overview |
| `/trading` | Order placement with risk check |
| `/portfolio` | Holdings & positions with AI analysis |
| `/analytics` | Risk metrics & performance charts |
| `/ai-signals` | ML signal generation |
| `/settings` | Dhan account connection & preferences |

---

## 🔧 Configuration

### Environment Variables

#### Frontend (.env.local)
```env
NEXT_PUBLIC_ENGINE_A_URL=https://engine-a.infinityai.pro
NEXT_PUBLIC_ENGINE_B_URL=https://engine-b.infinityai.pro
NEXT_PUBLIC_ENGINE_C_URL=https://engine-c.infinityai.pro
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
```

#### Backend (Cloud Run Secrets)
```
DHAN_CLIENT_ID        - Admin Dhan Client ID (for market data)
DHAN_ACCESS_TOKEN     - Admin Dhan Access Token
GOOGLE_CLOUD_PROJECT  - GCP Project ID
```

### Multi-User Credentials

User credentials are stored securely in **Firestore** with encryption:

```
/user_credentials/{user_id}
  ├── client_id: "user_dhan_client_id"
  ├── access_token: "encrypted_token"
  ├── api_key: "optional_api_key"
  ├── is_verified: true/false
  └── updated_at: timestamp
```

---

## 🚀 Deployment

### Deploy Engines to Cloud Run

```bash
# Engine A - Orchestration
cd backend/engine-analytics
gcloud builds submit --tag gcr.io/PROJECT_ID/engine-a:latest
gcloud run deploy engine-a --image gcr.io/PROJECT_ID/engine-a:latest --region us-central1

# Engine B - AI/ML
cd backend/engine-core
gcloud builds submit --tag gcr.io/PROJECT_ID/engine-b:latest
gcloud run deploy engine-b --image gcr.io/PROJECT_ID/engine-b:latest --region us-central1

# Engine C - Execution
cd backend/engine-execution
gcloud builds submit --tag gcr.io/PROJECT_ID/engine-c:latest
gcloud run deploy engine-c --image gcr.io/PROJECT_ID/engine-c:latest --region us-central1
```

### Deploy Frontend to Firebase

```bash
cd frontend/web-app
npm run build
firebase deploy --only hosting
```

---

## 📊 API Examples

### Generate ML Signal
```bash
curl -X POST https://engine-b.infinityai.pro/api/v1/signal \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE", "fast": true}'
```

### Calculate Risk Metrics
```bash
curl -X POST https://engine-a.infinityai.pro/api/v1/risk/comprehensive \
  -H "Content-Type: application/json" \
  -d '{"returns": [0.02, -0.01, 0.015, -0.005, 0.03]}'
```

### Batch Signals
```bash
curl -X POST https://engine-b.infinityai.pro/api/v1/signal/batch?fast=true \
  -H "Content-Type: application/json" \
  -d '["RELIANCE", "TCS", "INFY", "HDFCBANK"]'
```

---

## 📁 Project Structure

```
InfinityAI.Pro/
├── backend/
│   ├── engine-analytics/      # Engine A - Orchestration & Risk
│   │   ├── src/main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── engine-core/           # Engine B - AI/ML Signals
│   │   ├── src/main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── engine-execution/      # Engine C - Trade Execution
│       ├── src/main.py
│       ├── src/user_credentials.py
│       ├── requirements.txt
│       └── Dockerfile
├── frontend/
│   └── web-app/              # Next.js Dashboard
│       ├── src/
│       │   ├── app/          # Pages (App Router)
│       │   ├── components/   # React components
│       │   ├── hooks/        # Custom hooks (useApi)
│       │   ├── lib/          # API client, store
│       │   └── contexts/     # Auth context
│       └── package.json
├── firebase.json             # Firebase hosting config
└── README.md
```

---

## 🔐 Security

- **Authentication:** Firebase Auth with Google Sign-In
- **Credentials:** Encrypted storage in Firestore
- **Secrets:** Google Secret Manager for admin tokens
- **HTTPS:** All endpoints secured with SSL
- **CORS:** Configured for allowed origins

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Frontend Load | ~1.4s |
| Engine Health Check | ~0.8s |
| ML Signal Generation | ~0.8s |
| Batch Signals (4 stocks) | <1s |
| Full Trade Orchestration | <1.5s |

---

## 🛡️ SEBI 2025 Compliance

- Updated lot sizes (NIFTY: 75, BANKNIFTY: 30)
- Current expiry schedules
- Market holiday calendar
- Trading session times (Pre-open, Normal, Post-close)
- Margin rules compliance

---

## 📄 License

MIT License

---

<div align="center">

**Built with ❤️ for Indian Traders**

[infinityai.pro](https://infinityai.pro)

</div>
