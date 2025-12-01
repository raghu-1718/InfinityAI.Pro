# InfinityAI.Pro - Enterprise AI-Powered Trading Platform

<div align="center">

![Version](https://img.shields.io/badge/version-3.7.7--vertexai-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Gemini](https://img.shields.io/badge/Gemini-2.0--flash-4285F4)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![Cloud Run](https://img.shields.io/badge/GCP-Cloud%20Run-4285F4)
![Firebase](https://img.shields.io/badge/Firebase-Firestore%20%2B%20Auth-FFCA28)
![DhanHQ](https://img.shields.io/badge/Broker-DhanHQ-orange)
![Status](https://img.shields.io/badge/status-Production-green)
![License](https://img.shields.io/badge/license-MIT-green)

**An enterprise-grade AI/ML trading platform for Indian markets (NSE/BSE) with real-time Gemini AI, ensemble ML models, risk management, and automated execution**

[Live Platform](https://infinityai.pro) · [Engine-A API](https://engine-a.infinityai.pro/docs) · [Engine-B API](https://engine-b.infinityai.pro/docs) · [Engine-C API](https://engine-c.infinityai.pro/docs)

</div>

---

## 🎯 Platform Overview

InfinityAI.Pro is a **production-ready algorithmic trading platform** combining **Gemini 2.0 Flash AI** with **5+ ensemble ML models** and **DhanHQ brokerage integration** for real-time trading signals and automated order execution. Built on Google Cloud Platform with a microservices architecture.

### ✅ Live Status (December 2, 2025)

| Component | Status | Version | Latency |
|-----------|--------|---------|---------|
| **Engine A** | 🟢 Healthy | 3.7-google-integrations | ~100ms |
| **Engine B** | 🟢 Healthy | 3.7.7-vertexai | ~150ms |
| **Engine C** | 🟢 Healthy | 3.5-enhanced-execution | ~80ms |
| **Firestore** | 🟢 Connected | Native Mode | Real-time |
| **Gemini AI** | 🟢 Active | 2.0-flash | ~2-5s |
| **Dhan Broker** | 🟡 Token Refresh | v2.0.2 | ~200ms |

### 🌟 Key Features

| Feature | Description | Status |
|---------|-------------|--------|
| 🤖 **Gemini 2.0 Flash AI** | Real-time function calling for market data | ✅ Active |
| 📊 **Ensemble ML Models** | XGBoost, LightGBM, CatBoost, Random Forest | ✅ Active |
| 💹 **Real-Time Market Data** | NIFTY at ₹26,175.75, live technical indicators | ✅ Active |
| 📈 **Technical Analysis** | RSI, MACD, Bollinger, MAs, ATR, ADX | ✅ Active |
| 🧠 **Sentiment Analysis** | NLTK VADER + Transformers (77% confidence) | ✅ Active |
| 📰 **News Integration** | RSS from ET, Moneycontrol, Livemint | ✅ Active |
| 🔐 **Firebase Auth** | Google Sign-In + Multi-User | ✅ Active |
| 💾 **Firestore** | Real-time data sync | ✅ Active |
| 📱 **Modern Dashboard** | Next.js 15 + Tailwind + shadcn/ui | ✅ Active |
| 🏦 **Dhan Integration** | Funds, Holdings, Order Execution | ⚠️ Token Refresh |

---

## 🏗️ Live Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    InfinityAI.Pro - Production Architecture v3.7.7                   │
│                              Last Updated: December 2, 2025                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│   ┌────────────────────┐                    ┌──────────────────────────────────────┐ │
│   │    Frontend App    │                    │         Google Cloud Platform         │ │
│   │                    │                    │        Project: after-yesterday-*     │ │
│   │  infinityai.pro    │◄──────────────────►│                                        │ │
│   │   (Next.js 15)     │                    │  ┌─────────────────────────────────┐  │ │
│   │   Firebase Auth    │                    │  │     Cloud Run (us-central1)     │  │ │
│   └────────────────────┘                    │  │                                 │  │ │
│            │                                │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│            ▼                                │  │  │Engine-A │ │Engine-B │ │Engine-C │ │
│   ┌────────────────────┐                    │  │  │  Risk   │→│   AI    │→│ Execute │ │
│   │  Firebase Hosting  │                    │  │  │  Orch   │ │   ML    │ │  Dhan   │ │
│   │   + Firestore DB   │◄───────────────────│  │  │ v3.7    │ │v3.7.7   │ │ v3.5    │ │
│   │   + Real-time Sync │                    │  │  └─────────┘ └─────────┘ └─────────┘ │
│   └────────────────────┘                    │  └─────────────────────────────────┘  │ │
│                                             │                                        │ │
│                                             │  ┌─────────────────────────────────┐  │ │
│   ┌────────────────────┐                    │  │          Vertex AI              │  │ │
│   │      DhanHQ        │◄───────────────────│  │     Gemini 2.0 Flash           │  │ │
│   │   Broker API       │     Engine-C       │  │   (87K GenAI Credits)          │  │ │
│   │   (NSE/BSE/MCX)    │                    │  │  Function Calling Enabled       │  │ │
│   └────────────────────┘                    │  └─────────────────────────────────┘  │ │
│                                             │                                        │ │
│                                             │  ┌─────────────────────────────────┐  │ │
│   ┌────────────────────┐                    │  │       Secret Manager           │  │ │
│   │   Market Data      │                    │  │  12 secrets (encrypted)        │  │ │
│   │                    │                    │  │  - gemini-api-key              │  │ │
│   │  • yfinance (Live) │                    │  │  - dhan-access-token           │  │ │
│   │  • NSE/BSE APIs    │                    │  │  - firebase-admin-key          │  │ │
│   │  • News RSS Feeds  │                    │  └─────────────────────────────────┘  │ │
│   └────────────────────┘                    └──────────────────────────────────────┘ │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Engine Details

### Engine A - Orchestration & Risk Management
**URL:** https://engine-a-bprmddefsa-uc.a.run.app
**Version:** 3.7-google-integrations
**Status:** 🟢 Healthy

Central orchestrator managing authentication, risk calculations, and inter-engine coordination.

#### Capabilities
| Feature | Status |
|---------|--------|
| Risk Scoring | ✅ |
| Position Sizing | ✅ |
| VaR Calculation | ✅ |
| CVaR/Expected Shortfall | ✅ |
| Sortino Ratio | ✅ |
| Kelly Criterion | ✅ |
| Portfolio Risk | ✅ |
| Max Drawdown | ✅ |
| GenAI Integration | ✅ |
| Cloud Logging | ✅ |
| Cloud Storage | ✅ |
| Agent Orchestrator | ✅ |

---

### Engine B - AI/ML Signal Generation
**URL:** https://engine-b-bprmddefsa-uc.a.run.app
**Version:** 3.7.7-vertexai
**Status:** 🟢 Healthy

AI-powered signal generation with Gemini 2.0 Flash and ensemble ML models.

#### ML Models
| Model | Status | Purpose |
|-------|--------|---------|
| XGBoost | ✅ Active | Gradient boosting signals |
| LightGBM | ✅ Active | Fast gradient boosting |
| CatBoost | ✅ Active | Categorical features |
| Random Forest | ✅ Active | Ensemble voting |
| NLTK Sentiment | ✅ Active | News sentiment (77% accuracy) |
| Transformers | ✅ Active | Deep learning NLP |
| TA-Lib | ✅ Active | Technical indicators |
| yfinance | ✅ Active | Live market data |

#### Gemini AI Integration (NEW v3.7.7)
| Feature | Status |
|---------|--------|
| Vertex AI Mode | ✅ Active |
| Function Calling | ✅ Active |
| Real-time Market Data | ✅ Active |
| Trading Signal Agent | ✅ Active |
| Risk Agent | ✅ Active |
| News Aggregation | ✅ Active |

#### Live API Endpoints
```
POST /api/v1/ai/gemini-signal      - Gemini AI trading signal
POST /api/v1/signal                - ML ensemble signal
POST /api/v1/sentiment             - Sentiment analysis
GET  /api/v1/ai/integrations-status - AI status
POST /api/v1/ai/agent-analysis     - Multi-agent analysis
```

---

### Engine C - Trade Execution
**URL:** https://engine-c-bprmddefsa-uc.a.run.app
**Version:** 3.5-enhanced-execution
**Status:** 🟢 Healthy

Direct DhanHQ broker integration for order execution.

#### Capabilities
| Feature | Status |
|---------|--------|
| Slippage Prediction | ✅ |
| Order Timing | ✅ |
| TWAP Splitting | ✅ |
| VWAP Splitting | ✅ |
| Execution Analytics | ✅ |

#### Dhan API Endpoints
```
GET  /api/dhan/funds        - Account funds
GET  /api/dhan/holdings     - Current holdings
GET  /api/dhan/positions    - Open positions
GET  /api/dhan/orders       - Order history
POST /api/dhan/place-order  - Place new order
POST /api/dhan/cancel-order - Cancel order
```

---

## 📊 Live Data Verification

### Current Market Data (December 2, 2025)
```json
{
  "NIFTY": {
    "price": 26175.75,
    "change": "-0.1%",
    "52_week_high": 26325.8,
    "52_week_low": 21743.65
  },
  "RELIANCE": {
    "price": 1566.1,
    "rsi": 80.73,
    "status": "OVERBOUGHT",
    "macd": "BULLISH",
    "trend": "UPTREND"
  }
}
```

### Gemini AI Signal Example
```json
{
  "symbol": "RELIANCE",
  "signal": "HOLD",
  "confidence": 60,
  "stop_loss": 1520,
  "target": 1620,
  "timeframe": "SWING",
  "reasoning": "RSI overbought at 80.73, waiting for pullback..."
}
```

### Sentiment Analysis Example
```json
{
  "text": "Indian stock market rallies as FIIs turn buyers...",
  "sentiment": "POSITIVE",
  "confidence": 0.7739
}
```

---

## 🚀 Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **API Response Time** | 100-200ms | Cold start: 2-3s |
| **Gemini Inference** | 2-5 seconds | With function calling |
| **ML Signal Generation** | 50-100ms | Ensemble voting |
| **Sentiment Analysis** | 200-500ms | NLTK + Transformers |
| **Real-time Data Fetch** | 500ms-1s | yfinance integration |
| **Memory Usage** | 2-4GB | Per engine |
| **CPU Utilization** | 1-2 vCPU | Auto-scaling |

---

## 📈 Application Capabilities

### Strengths 💪
- ✅ **Real-time AI Analysis** - Gemini 2.0 with live market data
- ✅ **Ensemble ML Models** - 5+ models for robust signals
- ✅ **SEBI Compliant** - Indian market regulations built-in
- ✅ **Auto-scaling** - Cloud Run handles traffic spikes
- ✅ **Secure** - Secret Manager, encrypted credentials
- ✅ **Real-time Sync** - Firebase Firestore updates
- ✅ **Multi-user** - Individual trading accounts
- ✅ **Comprehensive Indicators** - 15+ technical indicators

### Areas for Improvement 🔧
- ⚠️ **Dhan Token** - Requires daily refresh (OAuth flow)
- ⚠️ **News API** - RSS only, no premium news sources
- ⚠️ **Options Data** - Simulated OI (needs NSE API)
- ⚠️ **Backtesting** - Not yet implemented
- ⚠️ **Paper Trading** - Simulated only

### Roadmap 🗺️
- 🔲 Auto token refresh for Dhan
- 🔲 Premium news API integration
- 🔲 Live NSE option chain data
- 🔲 Backtesting engine
- 🔲 Strategy builder UI
- 🔲 Mobile app (React Native)

---

## 🏦 SEBI Compliance

### Lot Sizes (Effective December 30, 2025)
| Index | Current | New (Dec 30) |
|-------|---------|--------------|
| NIFTY | 75 | 65 |
| BANKNIFTY | 35 | 30 |
| FINNIFTY | 65 | 60 |
| MIDCPNIFTY | 140 | 120 |

### Weekly Expiry Schedule
| Day | Index |
|-----|-------|
| Monday | MIDCPNIFTY |
| Tuesday | FINNIFTY |
| Wednesday | BANKNIFTY |
| Thursday | NIFTY |
| Friday | SENSEX |

### STT Rates
- Futures: 0.02%
- Options (Sell): 0.1%

---

## 🔧 Technical Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core language |
| FastAPI | 0.122 | API framework |
| google-genai | 1.0+ | Gemini SDK |
| XGBoost | 2.1.1 | ML model |
| LightGBM | 4.3.0 | ML model |
| CatBoost | 1.2+ | ML model |
| Transformers | 4.35+ | NLP |
| yfinance | 0.2.40+ | Market data |
| DhanHQ | 2.0.2 | Broker API |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 15 | React framework |
| TypeScript | 5.0 | Type safety |
| Tailwind CSS | 3.4 | Styling |
| shadcn/ui | Latest | UI components |
| Firebase | 10+ | Auth & Hosting |

### Infrastructure
| Service | Purpose |
|---------|---------|
| Cloud Run | Container hosting |
| Secret Manager | Credentials |
| Cloud Logging | Structured logs |
| Cloud Storage | ML models |
| Firestore | Real-time DB |
| Firebase Hosting | Frontend CDN |

---

## 📁 Project Structure

```
InfinityAI.Pro/
├── backend/
│   ├── engine-core/           # Engine B - AI/ML
│   │   ├── src/
│   │   │   ├── main.py        # FastAPI app (v3.7.7)
│   │   │   ├── google_integrations/
│   │   │   │   ├── enhanced_genai_client.py  # Vertex AI
│   │   │   │   ├── market_data_tools.py      # Function calling
│   │   │   │   ├── news_integration.py       # RSS feeds
│   │   │   │   └── trading_agents.py         # AI agents
│   │   │   └── services/
│   │   │       └── market_knowledge.py       # SEBI rules
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── engine-analytics/      # Engine A - Risk
│   ├── engine-execution/      # Engine C - Dhan
│   └── shared/                # Shared modules
├── frontend/
│   └── web/                   # Next.js dashboard
├── scripts/
│   ├── deploy-engine-b-vertexai.ps1
│   └── test_vertex_ai_integration.py
├── docs/
│   ├── VERTEX_AI_INTEGRATION.md
│   └── ARCHITECTURE.md
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- GCP account with billing
- Dhan trading account

### Local Development
```bash
# Clone repository
git clone https://github.com/raghu-1718/InfinityAI.Pro.git
cd InfinityAI.Pro

# Install backend dependencies
cd backend/engine-core
pip install -r requirements.txt

# Run Engine B locally
uvicorn src.main:app --reload --port 8080

# Install frontend dependencies
cd ../../frontend/web
npm install
npm run dev
```

### Deployment
```powershell
# Deploy Engine B with Vertex AI
.\scripts\deploy-engine-b-vertexai.ps1

# Or manual deployment
gcloud run deploy engine-b \
  --image gcr.io/after-yesterday-473512-k3/engine-b:v3.7.7-vertexai \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2
```

---

## 📞 API Examples

### Get Trading Signal
```bash
curl -X POST https://engine-b-bprmddefsa-uc.a.run.app/api/v1/signal \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE", "price": 1566.1, "rsi": 80.73}'
```

### Get Gemini AI Analysis
```bash
curl -X POST https://engine-b-bprmddefsa-uc.a.run.app/api/v1/ai/gemini-signal \
  -H "Content-Type: application/json" \
  -d '{"symbol": "NIFTY", "current_price": 26175.75}'
```

### Analyze Sentiment
```bash
curl -X POST https://engine-b-bprmddefsa-uc.a.run.app/api/v1/sentiment \
  -H "Content-Type: application/json" \
  -d '{"text": "Indian markets rally on strong FII buying"}'
```

---

## 📊 Credits & Resources

### GenAI Credits
- **Available:** 87,000 GenAI App Builder trial credits
- **Model:** gemini-2.0-flash (cost-efficient)
- **Usage:** ~$0.00025/1K input tokens

### GCP Resources
- **Project:** after-yesterday-473512-k3
- **Region:** us-central1
- **Billing:** Active

---

## 🔒 Security

- All credentials stored in Google Secret Manager
- Firebase Authentication with Google Sign-In
- HTTPS/SSL on all endpoints
- No hardcoded secrets in codebase
- Per-user credential isolation

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Raghu** - [GitHub](https://github.com/raghu-1718)

---

<div align="center">

**InfinityAI.Pro** - *Intelligent Trading for Indian Markets*

🚀 **Version 3.7.7-vertexai** | 📅 December 2, 2025

</div>
