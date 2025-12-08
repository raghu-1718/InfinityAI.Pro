# InfinityAI.Pro - AI-Powered Algorithmic Trading Platform

<div align="center">

![InfinityAI.Pro](https://img.shields.io/badge/InfinityAI.Pro-Trading%20Platform-blue?style=for-the-badge)
![Version](https://img.shields.io/badge/version-4.2.0-green?style=for-the-badge)
![Status](https://img.shields.io/badge/status-Production-brightgreen?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Gemini%202.5%20Pro-purple?style=for-the-badge)

**🚀 Next-Generation AI Trading for Indian Markets**

[Live Platform](https://infinityai.pro) | [Documentation](./docs/) | [Architecture](./docs/ARCHITECTURE.md)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Engine Specifications](#-engine-specifications)
- [AI/ML Capabilities](#-aiml-capabilities)
- [Gemini Integration](#-gemini-integration)
- [Market Data Accuracy](#-market-data-accuracy)
- [Performance Metrics](#-performance-metrics)
- [API Reference](#-api-reference)
- [Security](#-security)
- [Deployment](#-deployment)

---

## 🎯 Overview

InfinityAI.Pro is a sophisticated, production-grade algorithmic trading platform designed specifically for Indian financial markets. The platform leverages cutting-edge AI/ML technologies, including **Google's Gemini 2.5 Pro** model, ensemble machine learning, and advanced risk management algorithms to provide institutional-grade trading capabilities.

### Key Highlights

| Feature | Specification |
|---------|---------------|
| **Primary AI** | Google Gemini 2.5 Pro (Advanced Analysis) |
| **Fast AI** | Google Gemini 2.5 Flash (High-Speed Signals) |
| **ML Ensemble** | XGBoost, LightGBM, CatBoost, Random Forest |
| **Broker Integration** | DhanHQ (Full API + OAuth 2.0) |
| **Response Time** | 750-1000ms (including AI processing) |
| **Uptime** | 99.9% (Cloud Run auto-scaling) |
| **Markets** | NSE, BSE, NFO, MCX |
| **AI Credits** | ₹1,16,054.27 Available |

---

## 🏗 Architecture

### Three-Engine Distributed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INFINITYAI.PRO PLATFORM v4.2.0                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌────────────────┐    ┌────────────────┐    ┌────────────────┐            │
│   │   ENGINE A     │◄──►│   ENGINE B     │◄──►│   ENGINE C     │            │
│   │ v4.0.0-gemini  │    │ v4.2.0-stable  │    │ v4.1-robust    │            │
│   │                │    │                │    │                │            │
│   │ • Orchestration│    │ • Gemini 2.5   │    │ • DhanHQ API   │            │
│   │ • Risk Mgmt    │    │ • ML Ensemble  │    │ • OAuth Flow   │            │
│   │ • Coordination │    │ • Signals      │    │ • Execution    │            │
│   └────────────────┘    └────────────────┘    └────────────────┘            │
│          │                     │                     │                      │
│          └─────────────────────┼─────────────────────┘                      │
│                                │                                            │
│                    ┌───────────┴───────────┐                                │
│                    │    GCP SERVICES       │                                │
│                    │  ┌─────────────────┐  │                                │
│                    │  │ Secret Manager  │  │                                │
│                    │  │ Cloud Logging   │  │                                │
│                    │  │ Cloud Storage   │  │                                │
│                    │  │ Vertex AI       │  │                                │
│                    │  └─────────────────┘  │                                │
│                    └───────────────────────┘                                │
│                                │                                            │
│   ┌──────────────────────────────────────────────────────────────┐          │
│   │                        FIREBASE                               │          │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │          │
│   │  │ Firestore  │  │   Auth     │  │  Hosting   │              │          │
│   │  │ User Data  │  │ Google SSO │  │ infinityai │              │          │
│   │  │ Credentials│  │ Coupon     │  │   .pro     │              │          │
│   │  └────────────┘  └────────────┘  └────────────┘              │          │
│   └──────────────────────────────────────────────────────────────┘          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Production Infrastructure

| Component | Service | Version | URL |
|-----------|---------|---------|-----|
| **Engine A** | Cloud Run | v4.0.0-gemini3pro | `engine-a.infinityai.pro` |
| **Engine B** | Cloud Run | v4.2.0-stable | `engine-b.infinityai.pro` |
| **Engine C** | Cloud Run | v4.1-robust-parsing | `engine-c.infinityai.pro` |
| **Frontend** | Firebase Hosting | Latest | `infinityai.pro` |
| **Database** | Firestore | Native mode | us-central1 |
| **Auth** | Firebase Auth | v9 | Google + Coupon |
| **Secrets** | GCP Secret Manager | v1 | us-central1 |

---

## ⚙️ Engine Specifications

### Engine A - Orchestration & Risk Management
**Version: v4.0.0-gemini3pro** | **Status: ✅ Production**

Central orchestrator and risk management hub coordinating all trading operations.

#### Capabilities
| Feature | Description |
|---------|-------------|
| **OAuth Management** | DhanHQ OAuth 2.0 flow orchestration |
| **VaR Calculation** | Value at Risk (95%, 99% confidence) |
| **CVaR** | Expected Shortfall / Conditional VaR |
| **Sortino Ratio** | Downside risk-adjusted returns |
| **Kelly Criterion** | Optimal position sizing |
| **Max Drawdown** | Portfolio drawdown tracking |
| **Engine Coordination** | Multi-engine orchestration |

#### Key Endpoints
```
GET  /health                    - Health check
POST /api/v1/risk/var           - Value at Risk
POST /api/v1/risk/kelly         - Kelly position sizing
POST /api/v1/orchestrate        - Trading pipeline
GET  /api/v1/capabilities       - Engine capabilities
```

---

### Engine B - AI/ML Signal Generation
**Version: v4.2.0-stable** | **Status: ✅ Production**

Intelligence core with Gemini 2.5 Pro integration and ensemble ML models.

#### Gemini Model Configuration
| Task | Model | Rate Limit | Use Case |
|------|-------|------------|----------|
| **Fast** | gemini-2.5-flash-lite | 4,000 RPM | High-volume signals |
| **Standard** | gemini-2.5-flash | 1,000 RPM | Real-time analysis |
| **Quality** | gemini-2.5-pro | 15 RPM | Complex reasoning |
| **Advanced** | gemini-2.5-pro | 15 RPM | Deep analysis |
| **Experimental** | gemini-2.0-pro-exp | 150 RPM | Cutting-edge features |

#### ML Ensemble Stack
| Model | Accuracy | Latency | Strength |
|-------|----------|---------|----------|
| XGBoost | 72% | 15ms | Complex patterns |
| LightGBM | 70% | 8ms | Speed |
| CatBoost | 71% | 12ms | Categorical data |
| Random Forest | 68% | 20ms | Stability |
| **Ensemble** | **74%** | **25ms** | **Combined strength** |

#### Key Endpoints
```
GET  /api/v1/ai/available-models     - List AI models
POST /api/v1/ai/gemini3-analysis     - Gemini 2.5 Pro analysis
POST /api/v1/ai/enhanced-signal      - Enhanced trading signal
GET  /api/v1/ai/integrations-status  - AI integration status
GET  /api/v1/ai/usage-stats          - Token usage & costs
GET  /api/v1/market/pulse            - Real-time market pulse
POST /api/v1/signal                  - ML signal generation
POST /api/v1/sentiment               - Sentiment analysis
```

#### Sample Gemini Analysis Output
```json
{
  "status": "success",
  "response": "**Signal:** BUY with 65% confidence\n**Entry:** ₹1540-1545\n**Stop Loss:** ₹1520\n**Target:** ₹1580\n**Risk:Reward:** 1:2.4\n\n**Technical Analysis:**\n- RSI at 58.81 (NEUTRAL)\n- Above 21-day EMA & 50-day SMA (BULLISH)\n- MACD showing consolidation...",
  "model": "gemini-2.5-pro",
  "analysis_type": "advanced",
  "token_usage": {
    "input": 2989,
    "output": 1484,
    "total": 5150
  }
}
```

---

### Engine C - Trade Execution & Broker Integration
**Version: v4.1-robust-parsing** | **Status: ✅ Production**

Handles DhanHQ integration with OAuth 2.0, credential management via GCP Secret Manager, and trade execution.

#### Broker Integration
| Feature | Specification |
|---------|---------------|
| **Broker** | DhanHQ |
| **Authentication** | OAuth 2.0 with Secret Manager |
| **Credential Storage** | GCP Secret Manager (encrypted) |
| **API Coverage** | 40+ endpoints |
| **Order Types** | Market, Limit, SL, SL-M, Cover, Bracket |
| **Segments** | NSE, BSE, NFO, MCX, CDS |

#### Credential Flow
```
User Dashboard → OAuth Connect → DhanHQ Authorization
                      ↓
              Engine C Receives Token
                      ↓
         Store in GCP Secret Manager
              (user-creds-{firebase_id})
                      ↓
         Firestore Reference Updated
                      ↓
              Trading Enabled ✅
```

#### Key Endpoints
```
GET  /api/v1/user/{client_id}/balance    - Account balance
GET  /api/v1/user/{client_id}/positions  - Open positions
GET  /api/v1/user/{client_id}/orders     - Order book
POST /api/v1/order/place                 - Place order
PUT  /api/v1/order/modify                - Modify order
DELETE /api/v1/order/cancel              - Cancel order
GET  /api/v1/dhan/status                 - Broker status
```

---

## 🤖 Gemini Integration

### Available Models

| Model | Capabilities | Best For |
|-------|-------------|----------|
| **gemini-2.5-pro** | Deep reasoning, multi-factor analysis | Complex trading decisions |
| **gemini-2.5-flash** | Fast, efficient | Real-time signals |
| **gemini-2.5-flash-lite** | Ultra-fast, high-volume | Batch processing |
| **gemini-2.0-pro-exp** | Experimental features | R&D, testing |

### Credits & Usage

| Credit Type | Amount | Expiry |
|-------------|--------|--------|
| Gen App Builder Trial | ₹89,272.51 | Dec 2026 |
| Free Trial | ₹26,781.76 | Dec 14, 2025 |
| **Total Available** | **₹1,16,054.27** | - |

### AI Capabilities

- **Multi-Factor Analysis**: Technical + Fundamental + Sentiment fusion
- **Market Context**: Indian market timing, holidays, regulations
- **Risk Scenarios**: Best/Worst/Expected case modeling
- **Position Sizing**: Kelly Criterion recommendations
- **Entry/Exit Signals**: Precise price levels with reasoning

---

## 📊 Market Data Accuracy

### Index Specifications (Updated December 2025)

| Index | Lot Size | Tick Size | Weekly Expiry | Monthly Expiry |
|-------|----------|-----------|---------------|----------------|
| NIFTY | **75** | 0.05 | Tuesday | Last Thursday |
| BANKNIFTY | **35** | 0.05 | Wednesday | Last Wednesday |
| FINNIFTY | **65** | 0.05 | Tuesday | Last Tuesday |
| MIDCPNIFTY | **140** | 0.05 | Monday | Last Monday |
| SENSEX | **20** | 0.05 | Friday | Last Friday |
| BANKEX | **30** | 0.05 | Monday | Last Monday |

### Market Hours (IST)

| Session | Time |
|---------|------|
| Pre-Open | 09:00 - 09:15 |
| Normal Trading | 09:15 - 15:30 |
| Post-Close | 15:40 - 16:00 |

---

## ⚡ Performance Metrics

### Response Times (Production)

| Engine | Endpoint | P50 | P95 |
|--------|----------|-----|-----|
| Engine A | /health | 765ms | 900ms |
| Engine B | /health | 764ms | 950ms |
| Engine B | /ai/gemini3-analysis | 1.5s | 2.5s |
| Engine C | /health | 759ms | 800ms |
| Engine C | /user/balance | 500ms | 800ms |

### Scalability

| Metric | Value |
|--------|-------|
| Max Concurrent Users | 10,000 |
| Auto-scale Range | 0-100 instances |
| Cold Start Time | ~3s |
| AI Requests/Minute | 4,000+ |

---

## 🔐 Security

### Authentication Flow
```
Firebase Auth (Google SSO)
        ↓
   Coupon Verification (INFINITY2025)
        ↓
   DhanHQ OAuth 2.0
        ↓
   GCP Secret Manager Storage
```

### Security Features

- ✅ Zero hardcoded credentials
- ✅ GCP Secret Manager for all secrets
- ✅ HTTPS/TLS 1.3 encryption
- ✅ OAuth 2.0 token management
- ✅ Rate limiting on all endpoints
- ✅ CORS policy enforcement
- ✅ Audit logging enabled

---

## 🚀 Deployment

### CI/CD Pipeline

```
Push to main
    ↓
Build Docker Images (Cloud Build)
    ↓
Deploy to Cloud Run (Blue-Green)
    ↓
Health Check Validation
    ↓
DNS Routing (Cloudflare)
```

### Quick Deploy

```powershell
# Clone repository
git clone https://github.com/raghu-1718/InfinityAI.Pro.git
cd InfinityAI.Pro

# Configure GCP
gcloud auth login
gcloud config set project gen-lang-client-0779271931

# Deploy all engines
./scripts/deploy-3-engine-architecture.ps1

# Verify deployment
./scripts/cloud_health_check.ps1
```

### Required Secrets

| Secret | Description |
|--------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `user-creds-*` | Per-user DhanHQ credentials |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase admin credentials |

---

## 📁 Project Structure

```
InfinityAI.Pro/
├── backend/
│   ├── engine-a/             # Orchestration & Risk
│   ├── engine-b/             # AI/ML Signals
│   ├── engine-c/             # Trade Execution
│   └── shared/               # Common utilities
├── frontend/
│   └── web-app/              # Next.js Dashboard
├── config/                   # Trading configs
├── docs/                     # Documentation
├── infra/
│   ├── gcp/                  # GCP configurations
│   ├── firebase/             # Firebase configs
│   └── ci-cd/                # GitHub Actions
├── monitoring/               # Alert configs
├── scripts/                  # Deployment scripts
└── tests/                    # Test suites
```

---

## 📞 Contact

- **Platform**: [infinityai.pro](https://infinityai.pro)
- **GitHub**: [raghu-1718/InfinityAI.Pro](https://github.com/raghu-1718/InfinityAI.Pro)

---

## 📜 License

Copyright © 2025 InfinityAI.Pro. All rights reserved.

---

<div align="center">

**Built with ❤️ for Indian Traders**

![GCP](https://img.shields.io/badge/Google_Cloud-4285F4?style=flat&logo=google-cloud&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=flat&logo=firebase&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5-8E75B2?style=flat&logo=google&logoColor=white)

**Last Updated: December 8, 2025**

</div>
