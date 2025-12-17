# InfinityAI.Pro - AI-Powered Algorithmic Trading Platform

<div align="center">

![InfinityAI.Pro](https://img.shields.io/badge/InfinityAI.Pro-Trading%20Platform-blue?style=for-the-badge)
![Version](https://img.shields.io/badge/version-4.0-green?style=for-the-badge)
![Status](https://img.shields.io/badge/status-Production-brightgreen?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-purple?style=for-the-badge)
![Verified](https://img.shields.io/badge/Verified-December%202025-success?style=for-the-badge)

**🚀 Next-Generation AI Trading for Indian Markets**

[Live Platform](https://infinityai.pro) | [Documentation](./docs/) | [Architecture](./docs/ARCHITECTURE.md)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Engine Specifications](#-engine-specifications)
- [Background Trading](#-background-trading)
- [AI/ML Capabilities](#-aiml-capabilities)
- [Gemini Integration](#-gemini-integration)
- [Activity Logging](#-activity-logging)
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
| **Region** | `us-central1` (Unified) |
| **Markets** | NSE, BSE, NFO, MCX |
| **Total API Endpoints** | 114+ across 3 engines |
| **Background Trading** | ✅ Fully Automated |
| **Activity Logging** | ✅ Real-time to Firestore |

---

## 🏗 Architecture

### Three-Engine Distributed Architecture (Unified us-central1)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         INFINITYAI.PRO PLATFORM v4.0                            │
│                    GCP Project: gen-lang-client-0779271931                      │
│                         Region: us-central1 (Unified)                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌────────────────┐    ┌────────────────┐    ┌────────────────┐                │
│   │   ENGINE A     │◄──►│   ENGINE B     │◄──►│   ENGINE C     │                │
│   │    v3.7        │    │    v4.0        │    │    v3.7        │                │
│   │   ~322 MB      │    │   ~1.03 GB     │    │   ~325 MB      │                │
│   │                │    │                │    │                │                │
│   │ • Risk Mgmt    │    │ • Gemini 2.0   │    │ • DhanHQ API   │                │
│   │ • VaR/CVaR     │    │ • ML Ensemble  │    │ • OAuth Flow   │                │
│   │ • Kelly Sizing │    │ • AI Signals   │    │ • Background   │                │
│   │ • 8 Endpoints  │    │ • 63 Endpoints │    │   Trading      │                │
│   │                │    │                │    │ • 43+ Endpts   │                │
│   └────────────────┘    └────────────────┘    └────────────────┘                │
│          │                     │                     │                          │
│          └─────────────────────┼─────────────────────┘                          │
│                                │                                                │
│   ┌────────────────────────────┴────────────────────────────┐                   │
│   │                    GCP SERVICES                          │                   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │                   │
│   │  │   Secret    │  │   Cloud     │  │  Artifact   │       │                   │
│   │  │   Manager   │  │   Logging   │  │  Registry   │       │                   │
│   │  │  9 secrets  │  │   Enabled   │  │  10 repos   │       │                   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘       │                   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │                   │
│   │  │   Cloud     │  │   Cloud     │  │   Cloud     │       │                   │
│   │  │   Run       │  │   Storage   │  │  Scheduler  │       │                   │
│   │  │ 16 services │  │  3 buckets  │  │  2 jobs     │       │                   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘       │                   │
│   └─────────────────────────────────────────────────────────┘                   │
│                                │                                                │
│   ┌──────────────────────────────────────────────────────────────┐              │
│   │                        FIREBASE                               │              │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │              │
│   │  │ Firestore  │  │   Auth     │  │  Hosting   │              │              │
│   │  │ (nam5)     │  │ Google SSO │  │ infinityai │              │              │
│   │  │ NATIVE     │  │            │  │   .pro     │              │              │
│   │  │ 9 colls    │  │            │  │            │              │              │
│   │  └────────────┘  └────────────┘  └────────────┘              │              │
│   │                                                               │              │
│   │  13 Firebase Functions (Cloud Functions Gen 2)               │              │
│   └──────────────────────────────────────────────────────────────┘              │
│                                                                                  │
│   ┌──────────────────────────────────────────────────────────────┐              │
│   │                 CUSTOM DOMAINS (Cloudflare)                   │              │
│   │  engine-a.infinityai.pro → Engine A (us-central1)            │              │
│   │  engine-b.infinityai.pro → Engine B (us-central1)            │              │
│   │  engine-c.infinityai.pro → Engine C (us-central1)            │              │
│   │  infinityai.pro → Firebase Hosting                            │              │
│   └──────────────────────────────────────────────────────────────┘              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Production Infrastructure

| Component | Service | Version | Size | URL |
|-----------|---------|---------|------|-----|
| **Engine A** | Cloud Run | v3.7-google-integrations | ~322 MB | `engine-a.infinityai.pro` |
| **Engine B** | Cloud Run | v4.0-enhanced-trading-ai | ~1.03 GB | `engine-b.infinityai.pro` |
| **Engine C** | Cloud Run | v3.7-performance-optimized | ~325 MB | `engine-c.infinityai.pro` |
| **Frontend** | Firebase Hosting | v4.0 (Next.js 16) | - | `infinityai.pro` |
| **Database** | Firestore | NATIVE mode | - | nam5 (US multi-region) |
| **Auth** | Firebase Auth | v9 | - | Google SSO |
| **Secrets** | GCP Secret Manager | 9 secrets | - | us-central1 |
| **Functions** | Firebase Functions | 13 functions | - | Gen 2 |
| **Scheduler** | Cloud Scheduler | 2 jobs | - | asia-south1 |

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
**Version: v3.7-performance-optimized** | **Status: ✅ Production** | **Endpoints: 43+**

Handles DhanHQ integration with OAuth 2.0, credential management via GCP Secret Manager, intelligent trade execution, **and fully automated background trading**.

#### ML Capabilities
- ✅ Slippage Prediction
- ✅ Order Timing Optimization
- ✅ TWAP Splitting
- ✅ VWAP Splitting
- ✅ Execution Analytics

#### Background Trading (NEW)
| Feature | Specification |
|---------|---------------|
| **Status** | ✅ Fully Operational |
| **Mode** | Autonomous AI-Driven |
| **Strategy** | AI Signals (Engine B Integration) |
| **Risk Management** | 2% max per trade |
| **Daily Limit** | 10 trades max |
| **Confidence Threshold** | 70% minimum |
| **Instruments** | Equities |
| **Activity Logging** | Real-time to Firestore |

#### Broker Integration
| Feature | Specification |
|---------|---------------|
| **Broker** | DhanHQ |
| **Authentication** | OAuth 2.0 with Secret Manager |
| **Credential Storage** | GCP Secret Manager (per-user) |
| **API Coverage** | 43+ endpoints |
| **Order Types** | Market, Limit, SL, SL-M, Cover, Bracket |
| **Segments** | NSE, BSE, NFO, MCX, CDS |
| **Connected Users** | Active (e.g., <DHAN_CLIENT_ID>) |

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
GET  /health                                  - Health check
GET  /api/v1/dhan/status                      - Broker status
GET  /api/v1/user/{client_id}/balance         - Account balance
GET  /api/v1/user/{client_id}/positions       - Open positions
GET  /api/v1/user/{client_id}/orders          - Order book
GET  /api/v1/user/{client_id}/holdings        - Holdings
POST /api/v1/order/place                      - Place order
PUT  /api/v1/order/modify                     - Modify order
DELETE /api/v1/order/cancel                   - Cancel order
GET  /api/v1/background-trading/status/{uid}  - Background trading status
POST /api/v1/background-trading/start/{uid}   - Start background trading
POST /api/v1/background-trading/stop/{uid}    - Stop background trading
POST /api/v1/background-trading/config/{uid}  - Update config
GET  /api/v1/trading/activity/{uid}           - Activity logs
```

---

## 🤖 Background Trading

### Automated Trading System

Engine C includes a fully automated background trading system that executes trades based on AI signals from Engine B.

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKGROUND TRADING FLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐            │
│   │ Cloud      │───►│ Engine C   │───►│ Engine B   │            │
│   │ Scheduler  │    │ Trigger    │    │ AI Signal  │            │
│   │ (cron)     │    │            │    │ Generation │            │
│   └────────────┘    └────────────┘    └────────────┘            │
│        │                                      │                  │
│        │                                      ▼                  │
│        │              ┌─────────────────────────┐                │
│        │              │   Signal Evaluation     │                │
│        │              │   • Confidence ≥ 70%    │                │
│        │              │   • Risk check          │                │
│        │              │   • Daily limit check   │                │
│        │              └─────────────────────────┘                │
│        │                          │                              │
│        │                          ▼                              │
│        │              ┌─────────────────────────┐                │
│        │              │   Order Execution       │                │
│        │              │   • DhanHQ API          │                │
│        │              │   • Position sizing     │                │
│        │              │   • Slippage control    │                │
│        │              └─────────────────────────┘                │
│        │                          │                              │
│        ▼                          ▼                              │
│   ┌────────────────────────────────────────────┐                │
│   │              FIRESTORE LOGGING              │                │
│   │  • Activity logs (users/{uid}/activity)    │                │
│   │  • Trading state (users/{uid}/trading)     │                │
│   │  • Performance metrics                      │                │
│   └────────────────────────────────────────────┘                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_daily_trades` | 10 | Maximum trades per day |
| `max_risk_per_trade` | 0.02 (2%) | Maximum risk per trade |
| `min_confidence` | 0.7 (70%) | Minimum AI confidence |
| `trading_amount` | 1000 | Base trading amount (INR) |
| `strategy` | ai-signals | Trading strategy |
| `instruments` | ["equities"] | Allowed instruments |

### Cloud Scheduler Jobs

| Job | Schedule | Target | Purpose |
|-----|----------|--------|---------|
| `trading-signal-trigger` | `*/5 9-15 * * 1-5` | Engine C | Trigger trading signals (every 5 min during market hours) |
| `engine-health-check` | `*/10 * * * *` | Engine C | Health monitoring (every 10 min) |

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

### Cloud Run Services (16 total in us-central1)

| Service | Version | Purpose |
|---------|---------|---------|
| engine-a | v3.7-google-integrations | Risk Management |
| engine-b | v4.0-enhanced-trading-ai | AI/ML Signals |
| engine-c | v3.7-performance-optimized | Trade Execution |
| analyzeportfolio | Firebase Function | Portfolio Analysis |
| getaisignals | Firebase Function | AI Signals |
| getbatchaisignals | Firebase Function | Batch Signals |
| getdhanoverview | Firebase Function | Dhan Overview |
| getenginebstatus | Firebase Function | Engine B Status |
| getgeminianalysis | Firebase Function | Gemini Analysis |
| getvertexaianalysis | Firebase Function | Vertex AI |
| savedhantocloud | Firebase Function | Save Dhan Data |
| starttrading | Firebase Function | Start Trading |
| stoptrading | Firebase Function | Stop Trading |
| submitdhancredentialsv2 | Firebase Function | Credentials |
| syncholdingstocloud | Firebase Function | Sync Holdings |
| analyzeImageWithRoboticsER | Firebase Extension | Image Analysis |

### Artifact Registry (10 repositories)

| Repository | Images | Size |
|------------|--------|------|
| engine-a | 6 | ~1.1 GB |
| engine-b | 5 | ~4.5 GB |
| engine-c | 2 | ~650 MB |
| cloud-run-source-deploy | 12 | Various |
| gcf-artifacts | 14 | Firebase Functions |

### Enabled APIs (56 total)
| Category | APIs |
|----------|------|
| **AI/ML** | aiplatform, generativelanguage, ml |
| **Compute** | run, cloudfunctions, cloudbuild |
| **Storage** | firestore, storage, secretmanager |
| **Networking** | dns, domains, certificatemanager |
| **Monitoring** | logging, monitoring, cloudtrace |

### Secret Manager (9 secrets)
| Secret | Purpose |
|--------|---------|
| `gemini-api-key` | Gemini AI authentication |
| `dhan-client-id` | Dhan OAuth client ID |
| `dhan-access-token` | Dhan API access |
| `encryption-key` | Data encryption |
| `firebase-admin-sdk` | Firebase admin credentials |
| `user-creds-<DHAN_CLIENT_ID>` | User Dhan credentials |
| `user-creds-*` | Additional per-user credentials |

### Cloud Storage (3 buckets)
| Bucket | Purpose |
|--------|---------|
| gcf-sources-* | Cloud Functions source |
| gen-lang-client-*-gcf-upload-* | Firebase upload staging |
| gen-lang-client-*-firebaseapphosting | Firebase hosting |

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

### Firestore Collections (9)
| Collection | Purpose |
|------------|---------|
| `users` | User profiles and settings |
| `users/{uid}/activity` | Activity logs |
| `users/{uid}/trading` | Trading state |
| `users/{uid}/holdings` | Portfolio holdings |
| `activity_logs` | System activity |
| `background_trading_config` | Trading config |
| `trading_sessions` | Session data |
| `signals` | Trading signals |
| `orders` | Order history |

---

## 📝 Activity Logging

### Real-time Activity Tracking

All trading activities are logged to Firestore in real-time for transparency and auditing.

### Activity Log Structure

```json
{
  "timestamp": "2025-12-15T10:30:00.000Z",
  "type": "TRADE_EXECUTED",
  "action": "BUY",
  "symbol": "RELIANCE",
  "quantity": 10,
  "price": 2450.50,
  "status": "SUCCESS",
  "confidence": 0.85,
  "strategy": "ai-signals",
  "details": {
    "signal_source": "engine-b",
    "order_id": "ORD123456",
    "execution_time_ms": 150
  }
}
```

### Activity Types

| Type | Description |
|------|-------------|
| `TRADE_EXECUTED` | Trade successfully executed |
| `TRADE_SKIPPED` | Trade skipped (low confidence) |
| `SIGNAL_GENERATED` | AI signal generated |
| `TRADING_STARTED` | Background trading started |
| `TRADING_STOPPED` | Background trading stopped |
| `ERROR` | Error occurred |
| `CONFIG_UPDATED` | Configuration changed |

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

### Current Service Status (Verified December 15, 2025)

| Engine | Version | Status | Health | Size |
|--------|---------|--------|--------|------|
| Engine A | v3.7-google-integrations | ✅ Active | Healthy | ~322 MB |
| Engine B | v4.0-enhanced-trading-ai | ✅ Active | Healthy | ~1.03 GB |
| Engine C | v3.7-performance-optimized | ✅ Active | Healthy | ~325 MB |

### Verified Health Responses

**Engine A:**
```json
{
  "status": "healthy",
  "service": "engine-a-orchestrator",
  "version": "3.7-google-integrations",
  "ml_capabilities": ["risk_scoring", "position_sizing", "var_calculation",
                      "cvar_calculation", "sortino_ratio", "kelly_criterion",
                      "portfolio_risk", "max_drawdown"]
}
```

**Engine B:**
```json
{
  "status": "healthy",
  "service": "engine-b-ai-ml-prod",
  "version": "4.0-enhanced-trading-ai",
  "capabilities": {
    "xgboost": true, "lightgbm": true, "catboost": true,
    "random_forest": true, "transformers": true, "nltk_sentiment": true,
    "ta_lib": true, "yfinance": true, "weighted_voting": true
  },
  "dhan_connected": true
}
```

**Engine C:**
```json
{
  "status": "healthy",
  "service": "engine-c-execution",
  "broker": "DhanHQ",
  "version": "3.7-performance-optimized",
  "ml_capabilities": ["slippage_prediction", "order_timing",
                      "twap_splitting", "vwap_splitting", "execution_analytics"]
}
```

### API Endpoints

| Engine | Endpoints | Description |
|--------|-----------|-------------|
| Engine A | 8 | Risk management & analytics |
| Engine B | 63 | AI/ML & signals |
| Engine C | 43+ | Execution, broker & background trading |
| **Total** | **114+** | All endpoints |

### Scalability

| Metric | Value |
|--------|-------|
| Cloud Run Auto-scale | 0-100 instances |
| Region | us-central1 (Unified) |
| Firestore | nam5 (US multi-region) |
| Domain Mappings | 3 custom domains |
| SSL/TLS | Auto-managed certificates |

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
│   ├── engine-core/          # Engine A - Risk Management (v3.7)
│   ├── engine-analytics/     # Shared analytics
│   ├── engine-execution/     # Engine C - Trade Execution (v3.7)
│   ├── strategies/           # Engine B AI strategies
│   └── shared/               # Common utilities
├── frontend/
│   └── web/                  # Next.js 16 Dashboard
├── config/
│   ├── trading_config.ini    # Trading configuration
│   └── env/                  # Environment configs
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md
│   ├── FIREBASE_SETUP.md
│   ├── DHAN_OAUTH_SETTINGS.md
│   └── ...
├── infra/
│   ├── gcp/                  # GCP configurations
│   ├── firebase/             # Firebase configs
│   └── ci-cd/                # CI/CD configs
├── monitoring/               # Alert configs
│   ├── alert-error-rate.json
│   ├── alert-high-latency.json
│   └── dashboard-config.json
├── scripts/                  # Deployment & utility scripts
│   ├── cloud_health_check.ps1
│   ├── deploy-3-engine-architecture.ps1
│   └── ...
├── tests/                    # Test suites
├── extensions/               # Firebase extensions
├── verification/             # Verification reports
└── firebase.json             # Firebase config
```

---

## 🔄 Recent Updates (December 2025)

### Version History

| Date | Change | Details |
|------|--------|---------|
| Dec 15, 2025 | Engine C v3.7 | Performance optimized, background trading |
| Dec 15, 2025 | Unified Region | All engines now in us-central1 |
| Dec 15, 2025 | Activity Logging | Real-time Firestore logging |
| Dec 14, 2025 | Background Trading | Automated trading system |
| Dec 8, 2025 | Engine B v4.0 | Enhanced trading AI |
| Dec 6, 2025 | Domain Mappings | Custom domains configured |

### Audit Status

✅ **Full GCP Audit Completed** - December 15, 2025
- All 16 Cloud Run services verified
- 10 Artifact Registry repositories audited
- 9 Secret Manager secrets confirmed
- 3 Cloud Storage buckets verified
- 2 Cloud Scheduler jobs active
- 9 Firestore collections operational
- No duplicate services (unified us-central1)
- All domain mappings active

---

## 📞 Contact

- **Platform**: [infinityai.pro](https://infinityai.pro)
- **GitHub**: [raghu-1718/InfinityAI.Pro](https://github.com/raghu-1718/InfinityAI.Pro)
- **Engine A**: [engine-a.infinityai.pro](https://engine-a.infinityai.pro)
- **Engine B**: [engine-b.infinityai.pro](https://engine-b.infinityai.pro)
- **Engine C**: [engine-c.infinityai.pro](https://engine-c.infinityai.pro)

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
![DhanHQ](https://img.shields.io/badge/DhanHQ-00C853?style=flat&logo=stockx&logoColor=white)

**Last Updated: December 15, 2025** | **Verified & Audited ✅**

</div>