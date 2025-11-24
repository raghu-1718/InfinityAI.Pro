# InfinityAI.Pro - AI-Powered Trading Platform for Indian Markets

Production-ready AI trading platform optimized for NSE/BSE/MCX with real-time market data aggregation, ML-powered signals, secure trade execution, and real-time WebSocket dashboard.

**Live**: https://infinityai.pro | **Status**: Production Ready ✅

## 🎯 Project Overview

InfinityAI.Pro is architected as **3 independently deployable microservices** on Google Cloud Run:

| Engine | Purpose | Port (Local) | Cloud Run |
|--------|---------|--------------|-----------|
| **Core** (Engine A) | Market data ingestion & technical analysis | 8000 | `infinityai-engine-core-{hash}.a.run.app` |
| **Analytics** (Engine B) | ML/AI signal generation (TensorFlow, Gemini) | 8001 | `infinityai-engine-analytics-{hash}.a.run.app` |
| **Execution** (Engine C) | Trade execution, WebSocket, Chatbot (formerly D merged) | 8002 | `infinityai-engine-execution-{hash}.a.run.app` |

**Frontend**: React + Vite dashboard on Firebase Hosting at https://infinityai.pro

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+, Node 18+, Docker
- GCP project: `after-yesterday-473512-k3`
- `gcloud auth login` (configured)

### Local Development (3 terminals)

```bash
# Terminal 1: Engine Core
cd backend/engine-core && python -m pip install -r requirements.txt && python src/main.py

# Terminal 2: Engine Analytics
cd backend/engine-analytics && python -m pip install -r requirements.txt && python src/main.py

# Terminal 3: Engine Execution
cd backend/engine-execution && python -m pip install -r requirements.txt && python src/main.py

# Terminal 4: Frontend
cd frontend/web && npm install && npm run dev
# Open http://localhost:5173
```

### Docker Compose (All Services)

```bash
docker-compose -f docker-compose.engines.yml up -d
sleep 10  # Wait for startup
curl http://localhost:8000/health  # Verify
```

### Verify All Systems

```bash
cd verification/suite
python infinityai_verification_suite.py --environment development
```

---

## 📁 Project Structure

```
InfinityAI.Pro/
├── backend/
│   ├── engine-core/              # Market data ingestion (Port 8000)
│   │   └── src/ {api, services, models, config, __init__.py}
│   ├── engine-analytics/         # ML/AI signals (Port 8001)
│   │   └── src/ {api, services, models, config, __init__.py}
│   ├── engine-execution/         # Trade execution + WebSocket (Port 8002)
│   │   └── src/ {api, services, models, config, __init__.py}
│   └── shared/                   # Common utilities, clients, models
│       └── {clients, utils, models, config, setup.py}
├── frontend/
│   └── web/                      # React dashboard
│       ├── src/ {pages, components, hooks, lib, store}
│       ├── .env.example
│       └── firebase.json
├── infra/
│   ├── firebase/                 # Firestore rules, indexes
│   ├── gcp/                      # Terraform (Cloud Run, IAM, secrets)
│   │   └── {cloudrun, iam, networking, secrets}
│   └── ci-cd/                    # GitHub Actions, deployment scripts
│       └── {github/workflows, scripts}
├── verification/
│   ├── suite/                    # E2E verification checks
│   │   └── {checks, config, conftest.py}
│   └── reports/                  # Test results
│       └── {latest, archive}
├── config/
│   └── env/                      # Environment templates
│       ├── dev/ {engine-*.env.example, firebase.env.example}
│       └── prod/ {engine-*.env.example, firebase.env.example}
├── docker-compose.engines.yml
└── README.md
```

---

## 🏗️ Architecture

### Data Flow

```
Market Feeds → Engine Core (Ingestion)
                ↓
             Firestore (market_data)
                ↓
           Engine Analytics (ML predictions)
                ↓
             Firestore (signals)
                ↓
         Engine Execution (Order execution)
                ↓
           Firestore + WebSocket
                ↓
          Frontend (Real-time Dashboard)
```

### Engine Responsibilities

**Engine Core (Market Data)**
- NSE/BSE/MCX data ingestion
- Technical analysis (SMA, EMA, RSI, MACD, Bollinger Bands)
- Firestore persistence
- Real-time data broadcasting

**Engine Analytics (AI Signals)**
- TensorFlow LSTM/XGBoost models
- Google Gemini API integration
- Price predictions (1h, 4h, 1d)
- Sentiment analysis
- Signal confidence scoring

**Engine Execution (Trading + Coordination)**
- Dhan broker OAuth flow
- Order placement and tracking
- Risk management (position limits, stop loss)
- WebSocket aggregation from Core & Analytics
- AI Chatbot for user queries
- Multi-engine health orchestration

### Frontend (React + Firebase)

- Real-time market charts
- AI signal feed
- Order management UI
- Portfolio tracking
- WebSocket connection to Engine Execution
- Firebase Auth (email/password, OAuth)

---

## 🔧 Configuration

### Environment Variables

```bash
# Copy dev templates
cp config/env/dev/engine-core.env.example backend/engine-core/.env
cp config/env/dev/engine-analytics.env.example backend/engine-analytics/.env
cp config/env/dev/engine-execution.env.example backend/engine-execution/.env
cp config/env/dev/firebase.env.example frontend/web/.env.development

# Edit .env files with local values
# For production: use Cloud Run env vars + Secret Manager
```

### Secrets Management

All production secrets stored in **Google Cloud Secret Manager**:

```bash
# View secrets
gcloud secrets list --project=after-yesterday-473512-k3

# Required secrets:
# - dhan-api-key, dhan-client-secret
# - gemini-api-key
# - jwt-secret-key
# - firebase-config
```

---

## 🚢 Deployment

### Automatic (via GitHub Actions)

```bash
# Push to main → CI/CD deploys to production
git add .
git commit -m "feat: new trading signal"
git push origin main
```

### Manual (Terraform)

```bash
cd infra/gcp
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

### Cloud Run URLs

- Engine Core: `https://infinityai-engine-core-{hash}.a.run.app`
- Engine Analytics: `https://infinityai-engine-analytics-{hash}.a.run.app`
- Engine Execution: `https://infinityai-engine-execution-{hash}.a.run.app`
- Frontend: `https://infinityai.pro`

---

## 🧪 Testing & Verification

### Unit Tests

```bash
# Backend
cd backend/engine-core && pytest tests/
cd backend/engine-analytics && pytest tests/
cd backend/engine-execution && pytest tests/

# Frontend
cd frontend/web && npm run test
```

### End-to-End Verification

```bash
cd verification/suite

# Development
python infinityai_verification_suite.py --environment development

# Production (requires GCP credentials)
python infinityai_verification_suite.py --environment production
```

**Checks performed**:
- ✅ All 3 engines `/health` endpoints
- ✅ Firestore read/write operations
- ✅ Firebase authentication flow
- ✅ Frontend availability & SSL
- ✅ WebSocket connectivity
- ✅ Dhan OAuth configuration
- ✅ Gemini API accessibility

Reports saved to: `verification/reports/latest/`

---

## 📊 API Endpoints

### Engine Core - Market Data

```bash
GET /health                         # Health check
GET /api/market-data/{SYMBOL}       # OHLCV data (e.g., NIFTY)
GET /api/symbols                    # Available symbols
GET /api/indices                    # Index data
```

### Engine Analytics - AI Signals

```bash
GET /health                         # Health + model status
GET /api/ai-signals/{SYMBOL}        # Trading signal (BUY/SELL/HOLD)
GET /api/predictions/{SYMBOL}       # Price predictions
POST /api/sentiment                 # Sentiment analysis
```

### Engine Execution - Trading

```bash
GET /health                         # Multi-engine health check
POST /api/orders                    # Place order
GET /api/orders/{ORDER_ID}          # Order status
WS /ws/dashboard                    # Real-time WebSocket feed
GET /api/dhan/authorize             # Initiate OAuth
GET /api/dhan/callback              # OAuth callback endpoint
```

---

## 🔐 Security

- **JWT Authentication**: All internal APIs require valid JWT tokens
- **CORS**: Strict origin whitelist (production only)
- **HTTPS**: Enforced on all production endpoints
- **Secrets**: Via Google Cloud Secret Manager (never hardcoded)
- **Audit Logging**: All trades logged to Firestore
- **Risk Management**: Position limits, stop loss enforcement, daily drawdown checks

---

## 📈 Monitoring & Alerts

### Health Checks (Every 5 minutes)

```bash
# Automated via GitHub Actions
.github/workflows/health-check.yml
```

### Access Logs

```bash
# Cloud Logging (GCP Console)
gcloud run services log read engine-core --limit 50
gcloud run services log read engine-analytics --limit 50
gcloud run services log read engine-execution --limit 50
```

### Performance Metrics

- Market data latency: < 500ms
- Signal generation: < 1s
- Order execution: < 2s
- WebSocket ping: < 100ms

---

## 🐛 Troubleshooting

### Engines won't start locally

```bash
# Check Python version
python --version  # 3.9+ required

# Fresh install
cd backend/engine-core
rm -rf .venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### Firestore permission denied

```bash
gcloud auth login
gcloud config set project after-yesterday-473512-k3
gcloud iam service-accounts list
```

### WebSocket connection fails

```bash
# Check Engine Execution health
curl https://infinityai-engine-execution-{hash}.a.run.app/health

# View logs
gcloud run services log read engine-execution --limit 20
```

---

## 📚 Documentation

- `backend/engine-core/README.md` - Engine Core details
- `backend/engine-analytics/README.md` - Engine Analytics & ML models
- `backend/engine-execution/README.md` - Engine Execution & WebSocket
- `frontend/web/README.md` - Frontend architecture
- `infra/gcp/README.md` - GCP deployment & Terraform
- `infra/ci-cd/README.md` - CI/CD workflows
- `verification/suite/README.md` - Testing & verification
- `.github/copilot-instructions.md` - AI development guidelines

---

## 🔄 Development Workflow

1. Create feature branch: `git checkout -b feat/my-feature`
2. Make changes and add tests
3. Verify locally: `pytest && npm run test`
4. Push to GitHub: `git push origin feat/my-feature`
5. Create Pull Request → CI/CD runs tests
6. Maintainers review and merge
7. **Automatic deployment to production** ✅

---

## 📞 Support & Contact

- **Issues**: GitHub Issues tab
- **Documentation**: See `/docs` and README files in each directory
- **Team**: InfinityAI Team
- **Repository**: https://github.com/raghu-1718/InfinityAI.Pro

---

**Version**: 3.0.0 (3-engine architecture, Engine D merged into Engine C)
**Last Updated**: 2025-01-15
**Status**: Production Ready ✅

---

## Security and secrets

- No hardcoded secrets. All credentials are stored in Google Cloud Secret Manager and loaded at runtime using `get_secret()`.
- Dhan OAuth secrets and access tokens are managed via Secret Manager; Engine C reads them on demand.
- JWTs are issued by Engine D for authenticated frontend calls.
- CORS is configured for the frontend origin.

---

## Verification status (Nov 6, 2025)

- 150/150 tasks verified (see reports below)
- Automated test suite: 19/19 PASS (100%)
- Engines A–D: Healthy (A 344ms, B 341ms avg latency)
- Frontend: Live with SSL at https://infinityai.pro
- Dhan: Live integration confirmed (balance/positions/orders verified)

Reports and scripts:
- COMPLETE_150_VERIFICATION_REPORT.md (full details)
- FINAL_150_SUMMARY.md (quick stats)
- PLATFORM_STATUS.md (task matrix)
- VERIFICATION_SUMMARY.md (exec summary)
- verification-results-20251106-195434.json (automation output)
- scripts/complete-150-verification.ps1 (re-runs non-auth checks)

Run the automated verification (Windows PowerShell):

```powershell
pwsh -File .\scripts\complete-150-verification.ps1
```

---

## Local development

Prereqs: Python 3.10+, Node 18+, Google Cloud SDK, Firebase CLI.

Install backend deps (repeat per engine):

```powershell
pip install -r engines/engine-a/requirements.txt
```

Run engines locally (examples):

```powershell
cd engines/engine-a; python main.py
cd engines/engine-b; python main.py
cd engines/engine-c-execution; python main.py
cd engines/engine-d; python main.py
```

Install and run frontend:

```powershell
npm install --prefix frontend
npm run dev --prefix frontend
```

---

## Deployment and operations

Cloud Run (us-central1) with Cloud Build; Firebase Hosting for frontend.

Quick verification commands (already executed during platform audit):

```powershell
# GCP
gcloud run services list --region=us-central1
gcloud dns managed-zones list
gcloud dns record-sets list --zone=infinityai-pro-zone
gcloud secrets list
gcloud builds list --limit=10
gcloud iam service-accounts list

# Firebase
firebase projects:list
firebase functions:list --project=after-yesterday-473512-k3
firebase firestore:indexes --project=after-yesterday-473512-k3
```

---

## Risk and trading controls

Engine C enforces conservative risk parameters and authorization checks before trade execution. Callback URLs and webhooks are restricted to the production domain and validated with shared secrets.

---

## Folder structure (top-level)

- engines/ — Engine A/B/C/D microservices
- frontend/ — React + Vite frontend
- functions/ — Firebase Functions (callable)
- scripts/ — Automation (verification, deployment, diagnostics)
- config/ — Environment/config references (no secrets)
- docs/ — Architecture and project documentation
- reports/*.md — Generated audit and verification reports

---

## License

Copyright © InfinityAI. All rights reserved.
