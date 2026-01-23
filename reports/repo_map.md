# InfinityAI.Pro - Repository Canonical Map

**Generated:** 2026-01-21
**Project ID:** galvanic-pulsar-482815-h0
**Repository Root:** C:/workspace/InfinityAI.Pro
**Last Commit:** ecf7f16666d5838f6215a1bbe2333b3324ca9445 (2026-01-21 14:36:08 +0530)
**Commit Message:** "docs: Complete subdomain routing configuration for Cloud Run engines"

---

## Executive Summary

**InfinityAI.Pro** is a multi-cloud, production-grade **algorithmic trading platform** for Indian equity, derivatives, and commodity markets. It leverages Google Cloud Platform (Firebase + Cloud Run), DhanHQ broker integration, and real-time ML-powered signal generation for LIVE trading.

### Key Statistics

- **Total Files:** 90,700
- **Total Directories:** 12,941
- **Languages:** Python, TypeScript/JavaScript, Markdown, YAML
- **Primary Cloud:** Google Cloud Platform (project: galvanic-pulsar-482815-h0)
- **Broker:** DhanHQ API v2.2.0
- **Trading Mode:** LIVE (real-money, market hours 9:15-15:30 IST)

---

## 1. Project Architecture Overview

### 1.1 Platform Type

**Multi-Engine Algorithmic Trading System with AI/ML Integration**

- **Frontend:** Next.js 16 SPA with Firebase Hosting
- **Backend:** 3 Cloud Run Python microservices (Engine-A, Engine-B, Engine-C)
- **Functions:** 16+ Firebase Cloud Functions (TypeScript)
- **Database:** Google Firestore (NoSQL, serverless)
- **Real-time:** Ably Realtime + WebSockets
- **Broker:** DhanHQ REST + WebSocket APIs
- **ML/AI:** Google Vertex AI + Custom LightGBM models

### 1.2 Service Boundaries

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                            │
│  Next.js 16 SPA (infinityai.pro) → Firebase Hosting             │
│  - Dashboard, Trading UI, Charts, Settings                       │
│  - Ably Realtime subscriptions                                   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    FIREBASE FUNCTIONS LAYER                      │
│  16 Cloud Functions (TypeScript) deployed as Cloud Run          │
│  - verifycoupon, storeusercredentials, starttrading             │
│  - fetchaccountdata, analyzeportfolio, getaisignals             │
│  - getgeminianalysis, getvertexaianalysis                       │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                       ORCHESTRATION LAYER                        │
│  Engine-A (orchestrator.infinityai.pro) → Cloud Run             │
│  - Risk management, position limits, circuit breakers           │
│  - Audit logging, session management                            │
│  - Gemini AI integration for trade analysis                     │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                     ML SIGNALS LAYER                             │
│  Engine-B (signals.infinityai.pro) → Cloud Run                  │
│  - LightGBM, LSTM, Technical Analysis models                    │
│  - Sentiment analysis (news integration)                        │
│  - Feature engineering (70+ indicators)                         │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                      EXECUTION LAYER                             │
│  Engine-C (api.infinityai.pro) → Cloud Run                      │
│  - LIVE Trading via DhanHQ API                                  │
│  - Order management, portfolio reconciliation                   │
│  - Trading guardrails (order caps ₹500k, symbol whitelist)     │
│  - Paper trading mode, backtesting                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                        BROKER LAYER                              │
│  DhanHQ API v2.2.0 (dhanhq==2.0.2)                              │
│  - NSE/BSE/MCX market data                                      │
│  - Order placement/modification/cancellation                    │
│  - Portfolio, positions, holdings                               │
│  - WebSocket real-time quotes                                   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                       DATA STORAGE                               │
│  Google Firestore: users, credentials, sessions, orders         │
│  Cloud Storage: historical data, backtest results               │
│  Secret Manager: API keys, broker credentials (AES-256-GCM)     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure (Core Components)

### 2.1 Backend Services

```
backend/
├── engine-a/                   # Risk Orchestrator (Cloud Run)
│   ├── src/
│   │   ├── main.py            # FastAPI entrypoint
│   │   ├── services/
│   │   │   ├── risk_manager.py
│   │   │   ├── audit_logger.py
│   │   │   ├── session_manager.py
│   │   │   ├── circuit_breaker.py
│   │   │   └── autonomous_trader.py
│   │   ├── providers/
│   │   │   ├── gemini.py      # Gemini AI integration
│   │   │   ├── dhan.py
│   │   │   └── huggingface.py
│   │   └── analytics/
│   ├── Dockerfile
│   ├── cloudbuild.yaml
│   └── requirements.txt
│
├── engine-b/                   # ML Signals Generator (Cloud Run)
│   ├── src/
│   │   ├── main.py            # FastAPI entrypoint
│   │   ├── services/
│   │   │   ├── ai_model_service.py
│   │   │   ├── feature_engineer.py
│   │   │   ├── sentiment_service.py
│   │   │   ├── model_zoo.py
│   │   │   ├── ensemble_service.py
│   │   │   └── ta_utils.py  # Technical analysis
│   │   ├── models_store/
│   │   │   ├── lightgbm_model.pkl
│   │   │   ├── scaler.pkl
│   │   │   └── ta_features.json
│   │   └── providers/
│   │       └── dhan_data_async.py
│   ├── Dockerfile
│   ├── cloudbuild.yaml
│   └── requirements.txt
│
├── engine-c/                   # Execution Engine (Cloud Run)
│   ├── src/
│   │   ├── main.py            # FastAPI entrypoint ⚡ LIVE TRADING
│   │   ├── trading_guardrails.py  # Risk controls
│   │   ├── paper_trading.py
│   │   ├── dhan_credentials_endpoints.py
│   │   ├── user_credentials.py
│   │   ├── secret_manager_credentials.py
│   │   ├── market_data_fallback.py
│   │   ├── options_strategy_api.py
│   │   ├── super_order_api.py   # Advanced order types
│   │   ├── providers/
│   │   │   ├── dhan_rest.py
│   │   │   ├── dhan_ws.py       # WebSocket real-time
│   │   │   ├── order_manager.py
│   │   │   └── portfolio_reconciler.py
│   │   ├── analytics/
│   │   │   ├── ml_forecaster.py
│   │   │   ├── risk_optimizer.py
│   │   │   └── ai_signal_model.py
│   │   └── models/
│   │       ├── trade_models.py
│   │       ├── order_models.py
│   │       └── portfolio_models.py
│   ├── Dockerfile
│   ├── cloudbuild.yaml
│   └── requirements.txt        # dhanhq==2.0.2 ✅
│
├── market-data-ingestion/      # Cloud Run service
│   └── src/main.py
│
├── news-ingestion/             # Cloud Run service
│   └── src/main.py
│
├── shared/                     # Common utilities
│   ├── providers/              # Market data adapters
│   │   ├── nse_api.py
│   │   ├── marketstack.py
│   │   ├── newsapi.py
│   │   └── alpha_vantage.py
│   ├── google_integrations/
│   │   ├── genai_client.py    # Gemini integration
│   │   ├── cloud_storage.py
│   │   ├── cloud_logging.py
│   │   └── reasoning_engine_client.py
│   └── performance/
│       ├── rate_limiter.py
│       ├── cache.py
│       └── connection_pool.py
│
├── strategies/                 # Trading strategies
│   ├── ma_crossover.py
│   ├── enhanced_rsi.py
│   ├── gift_nifty_signals.py
│   └── hybrid_selector.py
│
├── options/                    # Options analytics
│   ├── option_chain.py
│   ├── iv_surface.py
│   ├── scenario_analysis.py
│   └── strategies/
│       ├── iron_condor.py
│       ├── bull_call_spread.py
│       └── covered_call.py
│
└── tools/                      # Admin/DevOps scripts
    ├── verification/
    │   ├── verify_full_system.py
    │   ├── check_credentials.py
    │   └── test_100_percent.py
    └── data/
        ├── fetch_dhan_data.py
        └── ingest_yahoo_historical.py
```

### 2.2 Frontend Application

```
frontend/
├── web-app/                    # Next.js 16 SPA
│   ├── src/
│   │   ├── app/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── page.tsx           # Main dashboard
│   │   │   │   ├── trading/page.tsx
│   │   │   │   ├── portfolio/page.tsx
│   │   │   │   ├── signals/page.tsx
│   │   │   │   ├── ai/page.tsx
│   │   │   │   ├── analytics/page.tsx
│   │   │   │   ├── options/page.tsx
│   │   │   │   ├── settings/page.tsx
│   │   │   │   └── history/page.tsx
│   │   │   ├── login/page.tsx
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── dashboard/
│   │   │   │   ├── portfolio-summary.tsx
│   │   │   │   ├── engine-status.tsx
│   │   │   │   ├── quick-trade.tsx
│   │   │   │   ├── signals-card.tsx
│   │   │   │   ├── gemini-chat.tsx
│   │   │   │   └── auto-trading.tsx
│   │   │   ├── layout/
│   │   │   │   ├── sidebar.tsx
│   │   │   │   ├── header.tsx
│   │   │   │   └── global-data-poller.tsx
│   │   │   ├── ai-agent/
│   │   │   │   └── AIAgentComponents.tsx
│   │   │   └── ui/               # shadcn/ui components
│   │   ├── contexts/
│   │   │   ├── AuthContext.tsx
│   │   │   ├── CouponAuthContext.tsx
│   │   │   ├── DualAuthContext.tsx
│   │   │   └── AblyContext.tsx
│   │   ├── hooks/
│   │   │   ├── useApi.ts
│   │   │   ├── useAbly.ts
│   │   │   ├── useDhanData.ts
│   │   │   └── useRealtimeTrading.ts
│   │   └── lib/
│   │       ├── firebase.ts        # Firebase SDK init
│   │       ├── api.ts
│   │       ├── ably.ts            # Ably Realtime
│   │       └── cloudFunctions.ts
│   ├── package.json               # Next 16, React 19
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── Dockerfile
│
└── functions/                  # Firebase Cloud Functions
    ├── src/
    │   ├── index.ts               # Exports all functions
    │   ├── verifyCoupon.ts
    │   ├── storeCredentials.ts
    │   ├── startTrading.ts
    │   ├── accountData.ts
    │   ├── analyzePortfolio.ts
    │   ├── getAiSignals.js
    │   ├── getGeminiAnalysis.js
    │   └── getVertexAiAnalysis.js
    ├── package.json
    └── tsconfig.json
```

### 2.3 Infrastructure as Code

```
infra/
├── gcp/
│   ├── main.tf                 # Terraform for Cloud Run, IAM
│   ├── variables.tf
│   ├── outputs.tf
│   └── cloudbuild.yaml
│
├── firebase/
│   ├── firestore.rules         # Security rules
│   ├── firestore.indexes.json
│   └── firebase.json
│
└── ci-cd/
    ├── scripts/cloudbuild.yaml
    └── README.md
```

### 2.4 Configuration & Secrets

```
config/
├── strategy_config.json
├── indian_market_config.json
├── commodity_markets_config.json
├── indian_symbols.json
└── symbol_map.json

.env (not tracked, template only)
.env.example
firebase.json
.firebaserc                     # project: galvanic-pulsar-482815-h0
auth-config.json
```

### 2.5 Data & ML

```
data/
├── yahoo_historical/
│   ├── NIFTY/
│   ├── BANKNIFTY/
│   ├── SENSEX/
│   ├── GOLD/
│   └── CRUDEOIL/
├── instruments_master.csv
├── system_verification_results.json
└── gcs_backtest_results_1y.json

ml/
├── train.py
├── create_baseline_model.py
├── features.py
├── requirements.txt
├── Dockerfile
└── cloudbuild.yaml
```

### 2.6 CI/CD & GitHub Workflows

```
.github/
└── workflows/
    ├── deploy-production.yml   # Main production deployment
    └── pr-validation.yml        # PR checks
```

---

## 3. Technology Stack

### 3.1 Languages & Frameworks

#### Frontend

- **Framework:** Next.js 16.0.7 (React 19.2.0, App Router)
- **Language:** TypeScript 5.6.3
- **UI Library:** Radix UI + shadcn/ui + Tailwind CSS
- **Charts:** Recharts 3.6.0
- **Real-time:** Ably Realtime 1.2.47
- **State Management:** Zustand 5.0.9
- **Data Fetching:** TanStack Query 5.90.11
- **Styling:** Tailwind CSS 4 with PostCSS

#### Backend Services (Python)

- **Framework:** FastAPI 0.100+
- **Server:** Uvicorn (ASGI)
- **Python Version:** 3.11.0
- **HTTP Client:** httpx, aiohttp (async)
- **Validation:** Pydantic 2.0+

#### Firebase Functions (TypeScript)

- **Runtime:** Node.js 24.9.0
- **SDK:** firebase-functions 6.6.0, firebase-admin 12.5.0

### 3.2 Cloud Services (GCP)

#### Compute

- **Cloud Run:** 21+ services (Engine-A/B/C, 16 Firebase Functions, market-data-ingestion, websocket-streamer)
- **Regions:** us-central1 (primary)
- **Scaling:** Auto-scale 0-100 instances

#### Storage

- **Firestore:** Primary database (users, credentials, sessions, orders, signals)
- **Cloud Storage:** Historical data, backtest results, ML models
- **Secret Manager:** API keys, broker credentials (encrypted AES-256-GCM)

#### Networking

- **Cloud Load Balancer:** Global HTTPS LB with Serverless NEGs
- **IP:** 34.107.213.171
- **SSL:** Google-managed SAN certificate (api/orchestrator/signals.infinityai.pro)
- **Firebase Hosting:** Frontend at infinityai.pro

#### AI/ML

- **Vertex AI:** Gemini Pro integration
- **Custom Models:** LightGBM (deployed in Engine-B)

#### Monitoring & Logging

- **Cloud Logging:** Structured logs from all services
- **Cloud Monitoring:** Metrics, dashboards, alerts

### 3.3 Third-Party Integrations

#### Broker

- **DhanHQ API v2.2.0:** REST + WebSocket
- **Package:** dhanhq==2.0.2 (Python)
- **Markets:** NSE, BSE, MCX (equities, F&O, commodities)

#### Real-time Data

- **Ably Realtime:** WebSocket pub/sub (frontend ↔ backend)
- **DhanHQ WebSocket:** Live market quotes

#### Market Data Providers (Fallback/Historical)

- **Yahoo Finance:** Historical data (yfinance)
- **Alpha Vantage:** Alternative market data
- **NSE API:** Direct NSE scraping
- **Marketstack:** Backup provider

#### News Sources

- **NewsAPI.org**
- **NewsData.io**
- **Indian News API**

### 3.4 ML/AI Stack

#### Models

- **LightGBM:** Primary ML model (stored in Engine-B)
- **LSTM:** Time series forecasting
- **Gemini Pro (Google):** LLM for trade analysis
- **Sentiment Analysis:** NLP via NLTK + custom models

#### Feature Engineering

- **Technical Indicators:** 70+ (RSI, MACD, Bollinger, ATR, ADX, etc.)
- **Sentiment Features:** News sentiment scores
- **Market Regime:** Volatility clustering, trend detection

#### Training Infrastructure

- **ml/train.py:** Local training scripts
- **ml/cloudbuild.yaml:** Cloud Build for automated retraining
- **Data Sources:** Historical data from Cloud Storage

### 3.5 Package Managers & Build Tools

- **Python:** pip (requirements.txt)
- **Node.js:** npm (package.json, workspaces)
- **Docker:** Multi-stage builds for all services
- **Firebase:** firebase-tools CLI
- **gcloud:** Cloud SDK (latest)

---

## 4. Service Inventory (Production Deployment)

### 4.1 Cloud Run Services (21 total)

| Service Name            | Type             | URL                                                     | Status   | Custom Domain               |
| ----------------------- | ---------------- | ------------------------------------------------------- | -------- | --------------------------- |
| **engine-a**            | Orchestrator     | https://engine-a-3acobgd3qa-uc.a.run.app                | ✅ Ready | orchestrator.infinityai.pro |
| **engine-b**            | ML Signals       | https://engine-b-3acobgd3qa-uc.a.run.app                | ✅ Ready | signals.infinityai.pro      |
| **engine-c**            | Execution (LIVE) | https://engine-c-3acobgd3qa-uc.a.run.app                | ✅ Ready | api.infinityai.pro          |
| market-data-ingestion   | Data Pipeline    | https://market-data-ingestion-3acobgd3qa-uc.a.run.app   | ✅ Ready | -                           |
| websocket-streamer      | Real-time Stream | https://websocket-streamer-3acobgd3qa-uc.a.run.app      | ✅ Ready | -                           |
| live-data-ingestion     | Data Pipeline    | https://live-data-ingestion-3acobgd3qa-uc.a.run.app     | ✅ Ready | -                           |
| analyzeportfolio        | Function         | https://analyzeportfolio-3acobgd3qa-uc.a.run.app        | ✅ Ready | -                           |
| fetchaccountdata        | Function         | https://fetchaccountdata-3acobgd3qa-uc.a.run.app        | ✅ Ready | -                           |
| getaisignals            | Function         | https://getaisignals-3acobgd3qa-uc.a.run.app            | ✅ Ready | -                           |
| getbatchaisignals       | Function         | https://getbatchaisignals-3acobgd3qa-uc.a.run.app       | ✅ Ready | -                           |
| getgeminianalysis       | Function         | https://getgeminianalysis-3acobgd3qa-uc.a.run.app       | ✅ Ready | -                           |
| getvertexaianalysis     | Function         | https://getvertexaianalysis-3acobgd3qa-uc.a.run.app     | ✅ Ready | -                           |
| getdhanoverview         | Function         | https://getdhanoverview-3acobgd3qa-uc.a.run.app         | ✅ Ready | -                           |
| storeusercredentials    | Function         | https://storeusercredentials-3acobgd3qa-uc.a.run.app    | ✅ Ready | -                           |
| verifycoupon            | Function         | https://verifycoupon-3acobgd3qa-uc.a.run.app            | ✅ Ready | -                           |
| starttrading            | Function         | https://starttrading-3acobgd3qa-uc.a.run.app            | ✅ Ready | -                           |
| stoptrading             | Function         | https://stoptrading-3acobgd3qa-uc.a.run.app             | ✅ Ready | -                           |
| get-live-prices         | Function         | https://get-live-prices-3acobgd3qa-uc.a.run.app         | ✅ Ready | -                           |
| get-price-history       | Function         | https://get-price-history-3acobgd3qa-uc.a.run.app       | ✅ Ready | -                           |
| get-latest-signals      | Function         | https://get-latest-signals-3acobgd3qa-uc.a.run.app      | ✅ Ready | -                           |
| detect-momentum-signals | Function         | https://detect-momentum-signals-3acobgd3qa-uc.a.run.app | ✅ Ready | -                           |

**Total Revisions Deployed:** 300+ (Engine-C alone: 87 revisions)

### 4.2 Firebase Hosting Sites (2)

| Site ID                           | Default URL                                       | Custom Domain      | App ID                                    |
| --------------------------------- | ------------------------------------------------- | ------------------ | ----------------------------------------- |
| galvanic-pulsar-482815-h0         | https://galvanic-pulsar-482815-h0.web.app         | -                  | 1:228557716858:web:d3ae59af1254d4b893aac3 |
| galvanic-pulsar-482815-h0-web-app | https://galvanic-pulsar-482815-h0-web-app.web.app | **infinityai.pro** | -                                         |

### 4.3 Custom Domain Configuration

**Domain:** infinityai.pro (Namecheap)

**DNS Records:**

```
A       @               199.36.158.100          (Firebase Hosting - Frontend)
A       www             199.36.158.100          (Firebase Hosting - Frontend)
A       api             34.107.213.171          (Cloud Load Balancer)
A       orchestrator    34.107.213.171          (Cloud Load Balancer)
A       signals         34.107.213.171          (Cloud Load Balancer)
TXT     @               hosting-site=galvanic-pulsar-482815-h0-web-app
TXT     @               v=spf1 include:spf.privateemail.com ~all
TXT     @               google-site-verification=Wds5z0TqEo8F_Gowq5WGzvKlFHPABLrx8S6QFH5wW7w
```

**SSL Certificates:**

- **Frontend:** Google-managed (infinityai.pro, ACTIVE)
- **API Subdomains:** Google-managed SAN cert (infinityai-apis-ssl, ACTIVE)
  - api.infinityai.pro
  - orchestrator.infinityai.pro
  - signals.infinityai.pro

**Load Balancer:** infinityai-https-forwarding-rule (IP: 34.107.213.171)

---

## 5. Data Schemas & Storage

### 5.1 Firestore Collections

Based on codebase inspection:

```
users/
  {userId}/
    - email, name, status
    - created_at, last_login
    - coupon_code, subscription_tier

credentials/
  {userId}/
    - dhan_client_id (encrypted)
    - dhan_access_token (encrypted)
    - encryption_metadata
    - last_updated

sessions/
  {sessionId}/
    - user_id
    - engine (a/b/c)
    - status (active/paused/stopped)
    - created_at, updated_at
    - risk_profile

orders/
  {orderId}/
    - user_id, session_id
    - symbol, side, quantity, price
    - order_type, status
    - broker_order_id
    - execution_timestamp
    - trading_mode (LIVE/PAPER)

signals/
  {signalId}/
    - symbol, direction
    - confidence, model_version
    - features (technical indicators)
    - timestamp

portfolio/
  {userId}/
    - positions[]
    - holdings[]
    - pnl_realized, pnl_unrealized
    - last_sync_timestamp

audit_logs/
  {logId}/
    - user_id, session_id
    - event_type
    - details
    - timestamp
```

### 5.2 Cloud Storage Buckets

```
galvanic-pulsar-482815-h0.appspot.com/
  historical_data/
    yahoo/
    dhan/
  backtest_results/
  ml_models/
    lightgbm/
    lstm/
  logs/
```

### 5.3 Secret Manager

```
projects/galvanic-pulsar-482815-h0/secrets/
  DHAN_CLIENT_ID
  DHAN_ACCESS_TOKEN
  ABLY_API_KEY
  GEMINI_API_KEY
  NEWSAPI_KEY
  FIREBASE_PRIVATE_KEY
  ENCRYPTION_KEY (AES-256-GCM master key)
```

---

## 6. Configuration Files

### 6.1 Root Level

| File          | Purpose                                                          |
| ------------- | ---------------------------------------------------------------- |
| package.json  | Monorepo workspace config (frontend/web-app, frontend/functions) |
| firebase.json | Firebase Hosting + Functions + Firestore config                  |
| .firebaserc   | GCP project binding (galvanic-pulsar-482815-h0)                  |
| tsconfig.json | TypeScript base config                                           |
| .gitignore    | Exclude node_modules, .env, **pycache**, etc.                    |
| .gcloudignore | Exclude from Cloud Build uploads                                 |

### 6.2 Backend Engine Configs

| File             | Location                         | Purpose                      |
| ---------------- | -------------------------------- | ---------------------------- |
| requirements.txt | backend/engine-{a,b,c}/          | Python dependencies          |
| Dockerfile       | backend/engine-{a,b,c}/          | Container build instructions |
| cloudbuild.yaml  | backend/engine-{a,b,c}/          | Cloud Build deployment       |
| settings.yaml    | backend/engine-{b,c}/src/config/ | Service-specific settings    |

### 6.3 Frontend Configs

| File               | Location          | Purpose                      |
| ------------------ | ----------------- | ---------------------------- |
| package.json       | frontend/web-app/ | Next.js dependencies         |
| next.config.ts     | frontend/web-app/ | Next.js build config         |
| tailwind.config.ts | frontend/web-app/ | Tailwind CSS theming         |
| components.json    | frontend/web-app/ | shadcn/ui component registry |
| eslint.config.mjs  | frontend/web-app/ | ESLint 9 flat config         |

### 6.4 Infrastructure Configs

| File                   | Location           | Purpose                   |
| ---------------------- | ------------------ | ------------------------- |
| main.tf                | infra/gcp/         | Terraform Cloud Run + IAM |
| firestore.rules        | infra/firebase/    | Security rules            |
| firestore.indexes.json | root               | Composite indexes         |
| deploy-production.yml  | .github/workflows/ | GitHub Actions CI/CD      |

---

## 7. Environment Variables & Secrets

### 7.1 Required Environment Variables (from .env.example pattern)

**Backend (Engine-C LIVE Trading):**

```bash
ENGINE_C_MODE=live                      # CRITICAL: live | paper
DHAN_CLIENT_ID=<from_secret_manager>
DHAN_ACCESS_TOKEN=<from_secret_manager>
GCP_PROJECT_ID=galvanic-pulsar-482815-h0
FIRESTORE_DATABASE=(default)
ENCRYPTION_KEY=<from_secret_manager>
TRADING_MARKET_HOURS_START=09:15
TRADING_MARKET_HOURS_END=15:30
TRADING_ORDER_CAP_INR=500000
TRADING_SYMBOL_WHITELIST=NIFTY,BANKNIFTY,SENSEX,RELIANCE,...
```

**Frontend (web-app/.env.local):**

```bash
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=galvanic-pulsar-482815-h0.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=galvanic-pulsar-482815-h0
NEXT_PUBLIC_ABLY_API_KEY=...
NEXT_PUBLIC_ENGINE_A_URL=https://orchestrator.infinityai.pro
NEXT_PUBLIC_ENGINE_B_URL=https://signals.infinityai.pro
NEXT_PUBLIC_ENGINE_C_URL=https://api.infinityai.pro
```

**Firebase Functions:**

```bash
GEMINI_API_KEY=<from_secret_manager>
GCP_PROJECT_ID=galvanic-pulsar-482815-h0
```

### 7.2 Secrets Management

- **Storage:** Google Secret Manager (NOT .env files)
- **Access:** IAM service account permissions per Cloud Run service
- **Encryption:** AES-256-GCM for user credentials in Firestore
- **Rotation:** Manual via Secret Manager versioning

---

## 8. CI/CD & Deployment

### 8.1 GitHub Actions Workflows

**deploy-production.yml:**

- Trigger: Push to `main` branch
- Steps:
  1. Authenticate with GCP (workload identity)
  2. Build Docker images (Engine-A/B/C)
  3. Push to Artifact Registry
  4. Deploy to Cloud Run (gcloud run deploy)
  5. Update Firebase Hosting
  6. Deploy Firebase Functions

**pr-validation.yml:**

- Trigger: Pull requests
- Steps: Lint, type check, unit tests

### 8.2 Cloud Build Configurations

**cloudbuild-engines.yaml:** Deploy all 3 engines in parallel
**cloudbuild-c-only.yaml:** Fast deploy for Engine-C hotfixes
**cloudbuild-deploy.yaml:** Full stack deployment

### 8.3 Deployment Commands (Manual)

```bash
# Frontend
cd frontend/web-app
npm run build
firebase deploy --only hosting

# Firebase Functions
cd frontend/functions
npm run build
firebase deploy --only functions

# Engine-C (LIVE Trading)
cd backend/engine-c
gcloud run deploy engine-c \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --project galvanic-pulsar-482815-h0 \
  --set-env-vars ENGINE_C_MODE=live
```

---

## 9. Testing & Verification

### 9.1 Test Suites

**Backend Tests:**

```
backend/tests/
  evaluation/framework.py        # Evaluation harness
backend/engine-c/tests/
  test_dhan_integration.py       # DhanHQ API tests
tools/verification/
  test_100_percent.py            # Full system E2E test
  verify_full_system.py
  check_credentials.py
  test_dhan_sandbox.py
  test_deployed_sandbox.py
```

**Frontend Tests:**

```
frontend/web-app/package.json:
  "test": "echo \"Frontend test placeholder: always passes.\" && exit 0"
```

⚠️ **Note:** Frontend tests are placeholder (auto-pass)

### 9.2 E2E Test Scripts

```
e2e-test.py                    # End-to-end integration test
load-test.py                   # Load testing script
monitor_24h.py                 # 24-hour monitoring script
```

**Results:**

- e2e-test-results-20260119-162458.json
- load-test-results-20260119-162327.json
- load_test_results.json

### 9.3 Verification Tools

```
tools/verification/
  verify_full_system.py         # Comprehensive system check
  check_credentials.py          # Credential validation
  verify_dhan_connection.py     # DhanHQ connectivity test
  verify_realtime_data.py       # WebSocket data flow
  verify_trading_active.py      # Trading system health
  check_firestore_creds.py      # Firestore credential audit
  diagnose_live_user.py         # Live user debugging
```

---

## 10. Documentation Inventory

### 10.1 Primary Guides (200+ Markdown files)

**Deployment & Setup:**

- 00_START_HERE.md
- DEPLOYMENT_RUNBOOK.md
- DEPLOYMENT_SUCCESS.md
- FRESH_DEPLOYMENT_STATUS.md
- INFRASTRUCTURE_DEPLOYMENT_REPORT.md

**Trading System:**

- LIVE_TRADING_DEPLOYMENT_VERIFICATION.md
- LIVE_TRADING_READY.md
- BACKTESTING_GUIDE.md
- EXECUTION_REFERENCE.md
- TRADING_MONITORING_GUIDE.md

**Integrations:**

- DHAN_V2_2_0_INTEGRATION.md
- DHAN_VERIFICATION_START_HERE.md
- DHAN_CREDENTIALS_QUICK_REFERENCE.md
- ABLY_IMPLEMENTATION_COMPLETE.md
- MARKET_DATA_FALLBACK_GUIDE.md

**Domain & DNS:**

- CUSTOM_DOMAIN_INTEGRATION_GUIDE.md
- NAMECHEAP_DNS_CONFIGURATION.md
- SUBDOMAIN_ROUTING_FINAL.md
- DOMAIN_INTEGRATION_VERIFICATION_REPORT.md

**Security & Compliance:**

- KMS_CREDENTIAL_ENCRYPTION_SETUP.md
- FIREBASE_AUTH_FIX_URGENT.md
- PRIORITY_1_SECURITY_FIXES_TODAY.md

**Phase Documentation:**

- PHASE7_DEPLOYMENT_COMPLETE.md
- PHASE6_SECURITY_HARDENING_EXECUTIVE_SUMMARY.md
- PHASE5_PERFORMANCE_TESTING_RESULTS.md
- PHASE4_COMPLETION_REPORT.md
- PHASE3_VERIFICATION_REPORT.md

**Quick References:**

- QUICK_START.md
- QUICK_REFERENCE.md
- QUICK_REFERENCE_COMMANDS.md
- CONFIG_AND_URLS.md
- SERVICE_URLS_REFERENCE.md

### 10.2 Technical Documentation

**Backend:**

- backend/engine-c/README.md
- backend/engine-c/DEPLOYMENT_GUIDE.md
- backend/engine-a/README.md
- backend/engine-b/README.md
- backend/shared/README.md

**Frontend:**

- frontend/web-app/README.md

**Infrastructure:**

- infra/gcp/README.md
- infra/firebase/README.md
- infra/ci-cd/README.md

**Tools:**

- tools/smoke_tests/README.md

---

## 11. Key Dependencies

### 11.1 Backend (Python)

**Core:**

- fastapi >= 0.100.0
- uvicorn[standard] >= 0.23.0
- pydantic >= 2.0.0
- python-dotenv >= 1.0.0

**Broker Integration:**

- dhanhq == 2.0.2 ✅ (CRITICAL)

**GCP:**

- google-cloud-firestore >= 2.11.0
- google-cloud-secret-manager >= 2.16.0
- google-cloud-storage >= 2.10.0

**HTTP:**

- httpx >= 0.24.0
- aiohttp >= 3.9.0
- websocket-client >= 1.7.0

**Data Science:**

- numpy >= 1.24.0
- pandas >= 2.0.0
- scikit-learn >= 1.3.0
- scipy >= 1.11.0
- statsmodels >= 0.14.0

**Security:**

- cryptography >= 41.0.0

**Options/Finance:**

- investpy >= 1.0.0

### 11.2 Frontend (Node.js)

**Core:**

- next == 16.0.7
- react == 19.2.0
- react-dom == 19.2.0
- typescript == 5.6.3

**Firebase:**

- firebase == 12.6.0

**Real-time:**

- ably == 1.2.47

**State Management:**

- zustand == 5.0.9
- @tanstack/react-query == 5.90.11

**UI Components:**

- @radix-ui/\* (14 packages)
- lucide-react == 0.555.0
- recharts == 3.6.0

**Styling:**

- @tailwindcss/postcss == 4.0
- tailwind-merge == 3.4.0
- class-variance-authority == 0.7.1

### 11.3 Firebase Functions

**Runtime:**

- firebase-functions == 6.6.0
- firebase-admin == 12.5.0

---

## 12. File Type Distribution (Top 20)

Based on workspace scan (90,700 files):

1. **.js** - JavaScript source/transpiled
2. **.ts** - TypeScript source
3. **.py** - Python source
4. **.md** - Markdown documentation
5. **.json** - Config/data files
6. **.yaml** / **.yml** - Cloud Build, config
7. **.csv** - Historical market data
8. **.txt** - Logs, results, notes
9. **.tsx** - TypeScript React components
10. **.map** - Source maps
11. **.png** / **.svg** - Icons, logos
12. **.Dockerfile** - Container definitions
13. **.gitignore** / **.gcloudignore**
14. **.pkl** - Pickled ML models
15. **.lock** - Dependency lock files
16. **.rules** - Firestore security rules
17. **.mjs** - ES module JavaScript
18. **.css** - Stylesheets
19. **.ico** - Favicons
20. **.tf** - Terraform infrastructure

---

## 13. Git Repository Metadata

**Repository Root:** C:/workspace/InfinityAI.Pro
**Last Commit Hash:** ecf7f16666d5838f6215a1bbe2333b3324ca9445
**Commit Date:** 2026-01-21 14:36:08 +0530
**Commit Author:** GitHub Copilot
**Commit Message:** "docs: Complete subdomain routing configuration for Cloud Run engines"

**Branch:** main (inferred)

---

## 14. Production Readiness Assessment

### 14.1 Deployment Status: ✅ LIVE

- **Frontend:** infinityai.pro (HTTPS, Firebase Hosting)
- **API Endpoints:** api/orchestrator/signals.infinityai.pro (HTTPS via Cloud Load Balancer)
- **SSL:** Valid Google-managed certificates, HSTS enabled
- **DNS:** Fully propagated (Namecheap → GCP)
- **Trading Mode:** LIVE (real-money trading active)
- **Broker:** DhanHQ connected
- **Market Hours:** 9:15-15:30 IST (Mon-Fri)

### 14.2 Trading Guardrails

✅ **Active:**

- Order cap: ₹500,000 per order
- Symbol whitelist enforcement
- Market hours validation (reject orders outside 9:15-15:30 IST)
- Risk limits per session
- Circuit breakers for max daily loss
- Audit logging (all order attempts logged to Firestore)

### 14.3 Security Posture

✅ **Implemented:**

- AES-256-GCM encryption for broker credentials
- Google Secret Manager for API keys
- Firestore security rules
- HTTPS-only communication
- CORS policies configured
- IAM least privilege per service

### 14.4 Monitoring & Observability

✅ **Configured:**

- Cloud Logging (structured logs)
- Cloud Monitoring (metrics dashboards)
- Real-time health checks (/health endpoints)
- Ably Realtime for frontend telemetry
- Error tracking (logged to Firestore)

---

## 15. Known Issues & Technical Debt

### 15.1 Frontend Testing

⚠️ **Low Priority:** Frontend tests are placeholder (auto-pass). No Jest/Vitest/Playwright suite exists.

### 15.2 Documentation Volume

⚠️ **Medium Priority:** 200+ Markdown files with significant overlap/redundancy. Needs consolidation.

### 15.3 Environment Variable Management

⚠️ **Medium Priority:** Some services rely on manual env var injection vs. Secret Manager automation.

### 15.4 Monorepo Complexity

⚠️ **Low Priority:** 90K+ files (includes node_modules, **pycache**). Consider workspace optimization.

---

## 16. Recommendations for Future Analysis

### 16.1 Architecture Inference (Task 2)

- Map API call graphs (frontend → functions → engines)
- Document WebSocket data flows (DhanHQ → Engine-C → Ably → Frontend)
- Visualize Firestore collection relationships

### 16.2 Cloud Verification (Task 3)

- Audit IAM roles per service
- Verify Secret Manager access patterns
- Check Cloud Logging retention policies
- Review Cloud Monitoring alert configurations

### 16.3 Performance Analysis (Task 5)

- Measure Cloud Run cold start latencies
- Analyze Firestore query performance (missing indexes?)
- Profile ML model inference times (Engine-B)
- Test WebSocket concurrency limits

### 16.4 Trading Enhancements (Task 7)

- Options strategy backtesting framework
- Advanced order types (iceberg, OCO, bracket)
- Multi-broker support (Zerodha, Upstox)
- Enhanced risk analytics (Value-at-Risk, Greeks)

---

## 17. Appendix: Critical File Paths

**Live Trading Entrypoint:**

```
backend/engine-c/src/main.py:L1
```

**Trading Guardrails:**

```
backend/engine-c/src/trading_guardrails.py:L1-L142
```

**Frontend Dashboard:**

```
frontend/web-app/src/app/(dashboard)/page.tsx:L1
```

**Firestore Rules:**

```
infra/firebase/firestore.rules:L1
```

**Production Deployment Workflow:**

```
.github/workflows/deploy-production.yml:L1
```

**Load Balancer SSL Certificate:**

```
gcloud compute ssl-certificates describe infinityai-apis-ssl
```

**Engine-C Health Check:**

```
GET https://api.infinityai.pro/health
```

---

## Document Version

**Version:** 1.0
**Status:** Initial Discovery Complete
**Next Steps:** Proceed to Task 2 (Architecture Inference)

---

**END OF REPOSITORY CANONICAL MAP**
