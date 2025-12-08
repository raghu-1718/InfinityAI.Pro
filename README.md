# InfinityAI.Pro - AI-Powered Algorithmic Trading Platform

<div align="center">

![InfinityAI.Pro](https://img.shields.io/badge/InfinityAI.Pro-Trading%20Platform-blue?style=for-the-badge)
![Version](https://img.shields.io/badge/version-4.0-green?style=for-the-badge)
![Status](https://img.shields.io/badge/status-Production-brightgreen?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-purple?style=for-the-badge)

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

InfinityAI.Pro is a sophisticated, production-grade algorithmic trading platform designed specifically for Indian financial markets. The platform leverages cutting-edge AI/ML technologies, including **Google's Gemini 2.0 Flash** model, ensemble machine learning, and advanced risk management algorithms to provide institutional-grade trading capabilities.

### Key Highlights

| Feature | Specification |
|---------|---------------|
| **Primary AI** | Google Gemini 2.0 Flash (Analysis & Chat) |
| **ML Ensemble** | XGBoost, LightGBM, CatBoost, Random Forest |
| **Broker Integration** | DhanHQ (Full API + OAuth 2.0) |
| **Cloud Platform** | Google Cloud Platform (GCP) |
| **Project ID** | `gen-lang-client-0779271931` |
| **Region** | `us-central1` |
| **Markets** | NSE, BSE, NFO, MCX |
| **Total API Endpoints** | 114 across 3 engines |

---

## 🏗 Architecture

### Three-Engine Distributed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INFINITYAI.PRO PLATFORM v4.0                        │
│                    GCP Project: gen-lang-client-0779271931                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌────────────────┐    ┌────────────────┐    ┌────────────────┐            │
│   │   ENGINE A     │◄──►│   ENGINE B     │◄──►│   ENGINE C     │            │
│   │    v3.7        │    │    v4.0        │    │    v3.5        │            │
│   │                │    │                │    │                │            │
│   │ • Risk Mgmt    │    │ • Gemini 2.0   │    │ • DhanHQ API   │            │
│   │ • VaR/CVaR     │    │ • ML Ensemble  │    │ • OAuth Flow   │            │
│   │ • Kelly Sizing │    │ • AI Signals   │    │ • Execution    │            │
│   │ • 8 Endpoints  │    │ • 63 Endpoints │    │ • 43 Endpoints │            │
│   └────────────────┘    └────────────────┘    └────────────────┘            │
│          │                     │                     │                      │
│          └─────────────────────┼─────────────────────┘                      │
│                                │                                            │
│                    ┌───────────┴───────────┐                                │
│                    │    GCP SERVICES       │                                │
│                    │  ┌─────────────────┐  │                                │
│                    │  │ Secret Manager  │  │                                │
│                    │  │ Cloud Logging   │  │                                │
│                    │  │ Cloud Run       │  │                                │
│                    │  │ Artifact Reg.   │  │                                │
│                    │  └─────────────────┘  │                                │
│                    └───────────────────────┘                                │
│                                │                                            │
│   ┌──────────────────────────────────────────────────────────────┐          │
│   │                        FIREBASE                               │          │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │          │
│   │  │ Firestore  │  │   Auth     │  │  Hosting   │              │          │
│   │  │ (nam5)     │  │ Google SSO │  │ infinityai │              │          │
│   │  │ NATIVE     │  │            │  │   .pro     │              │          │
│   │  └────────────┘  └────────────┘  └────────────┘              │          │
│   │                                                               │          │
│   │  13 Firebase Functions (Cloud Functions Gen 2)               │          │
│   └──────────────────────────────────────────────────────────────┘          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Production Infrastructure

| Component | Service | Version | URL |
|-----------|---------|---------|-----|
| **Engine A** | Cloud Run | v3.7-google-integrations | `engine-a-429140669077.us-central1.run.app` |
| **Engine B** | Cloud Run | v4.0-enhanced-trading-ai | `engine-b-429140669077.us-central1.run.app` |
| **Engine C** | Cloud Run | v3.5-enhanced-execution | `engine-c-429140669077.us-central1.run.app` |
| **Frontend** | Firebase Hosting | v4.0 (Next.js 16) | `infinityai.pro` |
| **Database** | Firestore | NATIVE mode | nam5 (US multi-region) |
| **Auth** | Firebase Auth | v9 | Google SSO |
| **Secrets** | GCP Secret Manager | 9 secrets | us-central1 |
| **Functions** | Firebase Functions | 13 functions | Gen 2 |

---

## ⚙️ Engine Specifications

### Engine A - Risk Management & Analytics
**Version: v3.7-google-integrations** | **Status: ✅ Production** | **Endpoints: 8**

Central risk management hub with portfolio analytics and position sizing.

#### Capabilities
| Feature | Description |
|---------|-------------|
| **VaR Calculation** | Value at Risk (95%, 99% confidence) |
| **CVaR** | Expected Shortfall / Conditional VaR |
| **Sortino Ratio** | Downside risk-adjusted returns |
| **Kelly Criterion** | Optimal position sizing |
| **Max Drawdown** | Portfolio drawdown tracking |
| **Risk Scoring** | Multi-factor risk assessment |
| **Portfolio Risk** | Correlation & diversification analysis |

#### Google Integrations
- ✅ GenAI (Gemini)
- ✅ Cloud Logging
- ✅ Cloud Storage
- ✅ Agent Orchestrator

#### Key Endpoints
```
GET  /health                    - Health check
POST /api/v1/risk/var           - Value at Risk
POST /api/v1/risk/cvar          - Conditional VaR
POST /api/v1/risk/sortino       - Sortino Ratio
POST /api/v1/risk/kelly         - Kelly position sizing
GET  /api/v1/capabilities       - Engine capabilities
```

---

### Engine B - AI/ML Signal Generation
**Version: v4.0-enhanced-trading-ai** | **Status: ✅ Production** | **Endpoints: 63**

Intelligence core with Gemini 2.0 Flash integration and ensemble ML models.

#### Gemini Model Configuration
| Feature | Status |
|---------|--------|
| **Primary Model** | Gemini 2.0 Flash |
| **GenAI Integration** | ✅ Active |
| **Signal Agent** | ✅ Active |
| **Risk Agent** | ✅ Active |
| **Enhanced Trading AI** | ✅ Active |

#### ML Ensemble Stack
| Model | Status | Strength |
|-------|--------|----------|
| XGBoost | ✅ Active | Complex patterns |
| LightGBM | ✅ Active | Speed |
| CatBoost | ✅ Active | Categorical data |
| Random Forest | ✅ Active | Stability |
| Transformers | ✅ Active | NLP/Sentiment |
| NLTK Sentiment | ✅ Active | Text analysis |
| TA-Lib | ✅ Active | Technical indicators |
| yFinance | ✅ Active | Market data |

#### Enhanced Features
- ✅ Indian Market Knowledge
- ✅ SEBI 2025 Compliance
- ✅ Smart Entry/Exit
- ✅ Position Sizing
- ✅ Risk Management

#### Key Endpoints
```
GET  /health                         - Health check
POST /api/v1/gemini/chat             - Free-form Gemini AI chat
POST /api/v1/gemini/analyze          - Gemini analysis
POST /api/v1/finance-ai/signal       - AI trading signal
POST /api/v1/finance-ai/market-analysis - Market analysis
POST /api/v1/finance-ai/options-strategy - Options strategy
POST /api/v1/finance-ai/risk-analysis - Risk analysis
POST /api/v1/signal                  - ML signal generation
POST /api/v1/sentiment               - Sentiment analysis
GET  /api/v1/market/pulse            - Real-time market pulse
```

#### Sample Gemini Chat Response
```json
{
  "status": "success",
  "response": "NIFTY 50 is the flagship index of the National Stock Exchange of India, comprising the 50 largest and most liquid stocks...",
  "model": "gemini-2.0-flash"
}
```

---

### Engine C - Trade Execution & Broker Integration
**Version: v3.5-enhanced-execution** | **Status: ✅ Production** | **Endpoints: 43**

Handles DhanHQ integration with OAuth 2.0, credential management via GCP Secret Manager, and intelligent trade execution.

#### ML Capabilities
- ✅ Slippage Prediction
- ✅ Order Timing Optimization
- ✅ TWAP Splitting
- ✅ VWAP Splitting
- ✅ Execution Analytics

#### Broker Integration
| Feature | Specification |
|---------|---------------|
| **Broker** | DhanHQ |
| **Authentication** | OAuth 2.0 with Secret Manager |
| **Credential Storage** | GCP Secret Manager (per-user) |
| **API Coverage** | 43 endpoints |
| **Order Types** | Market, Limit, SL, SL-M, Cover, Bracket |
| **Segments** | NSE, BSE, NFO, MCX, CDS |

#### Credential Flow
```
User Dashboard → OAuth Connect → DhanHQ Authorization
                      ↓
              Engine C Receives Token
                      ↓
         Store in GCP Secret Manager
              (user-creds-{user_id})
                      ↓
         Firestore Reference Updated
                      ↓
              Trading Enabled ✅
```

#### Key Endpoints
```
GET  /health                         - Health check
GET  /api/v1/dhan/status             - Broker status
GET  /api/v1/user/{client_id}/balance    - Account balance
GET  /api/v1/user/{client_id}/positions  - Open positions
GET  /api/v1/user/{client_id}/orders     - Order book
GET  /api/v1/user/{client_id}/holdings   - Holdings
POST /api/v1/order/place             - Place order
PUT  /api/v1/order/modify            - Modify order
DELETE /api/v1/order/cancel          - Cancel order
```

---

## 🤖 Gemini AI Integration

### Current Model
| Model | Use Case | Status |
|-------|----------|--------|
| **Gemini 2.0 Flash** | Real-time AI chat & analysis | ✅ Active |

### AI Features

#### Gemini Chat (`/api/v1/gemini/chat`)
Free-form AI Q&A for any trading question:
- Market analysis
- Stock research
- Trading strategies
- Risk assessment
- Indian market insights

#### Finance AI Endpoints
| Endpoint | Purpose |
|----------|---------|
| `/api/v1/finance-ai/signal` | AI-powered trading signals |
| `/api/v1/finance-ai/market-analysis` | Comprehensive market analysis |
| `/api/v1/finance-ai/options-strategy` | Options strategy recommendations |
| `/api/v1/finance-ai/risk-analysis` | Portfolio risk assessment |

---

## 📊 GCP Resources

### Enabled APIs (56 total)
| Category | APIs |
|----------|------|
| **AI/ML** | aiplatform, generativelanguage, ml |
| **Compute** | run, cloudfunctions, cloudbuild |
| **Storage** | firestore, storage, secretmanager |
| **Networking** | dns, domains, certificatemanager |
| **Monitoring** | logging, monitoring, cloudtrace |

### Secret Manager
| Secret | Purpose |
|--------|---------|
| `gemini-api-key` | Gemini AI authentication |
| `dhan-client-id` | Dhan OAuth client ID |
| `dhan-access-token` | Dhan API access |
| `encryption-key` | Data encryption |
| `firebase-admin-sdk` | Firebase admin credentials |
| `user-creds-*` | Per-user Dhan credentials (3 users) |

### Firebase Functions (13)
- `analyzeImageWithRoboticsER`
- `analyzePortfolio`
- `getAiSignals`
- `getBatchAiSignals`
- `getDhanOverview`
- `getEngineBStatus`
- `getGeminiAnalysis`
- `getVertexAiAnalysis`
- `saveDhanCredentials`
- `startTrading`
- `stopTrading`
- `submitDhanCredentialsV2`
- `syncHoldings`

---

## 📈 Market Data Accuracy

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

### Current Service Status

| Engine | Version | Status | Health |
|--------|---------|--------|--------|
| Engine A | v3.7-google-integrations | ✅ Active | Healthy |
| Engine B | v4.0-enhanced-trading-ai | ✅ Active | Healthy |
| Engine C | v3.5-enhanced-execution | ✅ Active | Healthy |

### API Endpoints

| Engine | Endpoints | Description |
|--------|-----------|-------------|
| Engine A | 8 | Risk management & analytics |
| Engine B | 63 | AI/ML & signals |
| Engine C | 43 | Execution & broker |
| **Total** | **114** | All endpoints |

### Scalability

| Metric | Value |
|--------|-------|
| Cloud Run Auto-scale | 0-100 instances |
| Region | us-central1 |
| Auto-scale Range | 0-100 instances |
| Region | us-central1 |
| Firestore | nam5 (US multi-region) |

---

## 🔐 Security

### Authentication Flow
```
Firebase Auth (Google SSO)
        ↓
   User Dashboard Access
        ↓
   DhanHQ OAuth 2.0 (per-user)
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

# Verify deployment
./scripts/cloud_health_check.ps1
```

### Required Secrets

| Secret | Description |
|--------|-------------|
| `gemini-api-key` | Google Gemini API key |
| `dhan-client-id` | DhanHQ OAuth client ID |
| `dhan-access-token` | DhanHQ API access token |
| `user-creds-*` | Per-user DhanHQ credentials |
| `firebase-admin-sdk` | Firebase admin credentials |
| `encryption-key` | Data encryption key |

---

## 📁 Project Structure

```
InfinityAI.Pro/
├── backend/
│   ├── engine-a/             # Risk Management (v3.7)
│   ├── engine-b/             # AI/ML Signals (v4.0)
│   ├── engine-c/             # Trade Execution (v3.5)
│   └── shared/               # Common utilities
├── frontend/
│   └── web-app/              # Next.js 16 Dashboard
├── config/                   # Trading configs
├── docs/                     # Documentation
├── infra/
│   ├── gcp/                  # GCP configurations
│   ├── firebase/             # Firebase configs
│   └── ci-cd/                # GitHub Actions
├── monitoring/               # Alert configs
├── scripts/                  # Deployment scripts
├── tests/                    # Test suites
└── .devcontainer/            # Codespaces config
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
![Gemini](https://img.shields.io/badge/Gemini_2.0-8E75B2?style=flat&logo=google&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js_16-000000?style=flat&logo=next.js&logoColor=white)

**Last Updated: December 8, 2025**

</div>
