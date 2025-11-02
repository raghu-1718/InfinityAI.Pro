# InfinityAI.Pro Complete Project Structure

## Root Directory

### Configuration Files
- `.env`, `.env.cloud-verified`, `.env.example` - Environment configuration
- `.firebaserc` - Firebase project configuration
- `.gitignore`, `.gitlab-ci.yml` - Version control
- `docker-compose.yml`, `docker-compose.engines.yml` - Container orchestration
- `firebase.json`, `firestore.indexes.json` - Firebase configuration
- `package.json`, `package-lock.json` - Node.js dependencies
- `services.json`, `users.json` - Service and user data
- `config/trading_config.ini` - Trading configuration

### Verification & Monitoring Scripts
- `infinityai_system_verifier.py` - Main system verification tool (with --config support)
- `cloud_verification_suite.py` - Cloud deployment verification
- `real_time_cloud_verifier.py` - Real-time cloud monitoring
- `verify_deployment_status.py` - Deployment status checker
- `platform_monitor.py` - Platform monitoring
- `complete_verification.py` - Comprehensive verification
- Multiple verification reports: `infinityai_verification_report_*.json`

### Analysis & Diagnostics Scripts
- `infinityai_diagnostic.py` - System diagnostics
- `comprehensive_platform_diagnostics.py` - Platform-wide diagnostics
- `analyze_dependencies.py` - Dependency analysis
- `analyze_github_actions.py` - GitHub Actions analysis
- `platform_comprehensive_analysis.py` - Comprehensive platform analysis
- Analysis reports: `dependency_analysis.json`, `github_actions_analysis.json`

### Deployment & Fix Scripts
- `complete_platform_fix.py` - Platform-wide fixes
- `engine_d_recovery_and_ai_fix.py` - Engine D recovery
- `fix_firebase_auth.py` - Firebase authentication fixes
- `setup_firebase_auth.py` - Firebase auth setup
- `test_firebase_auth_flow.py` - Firebase auth testing
- `fix-ci-cd-issues.ps1`, `fix-ci-cd-issues.py` - CI/CD fixes
- `deploy_missing_endpoints.sh` - Endpoint deployment
- `fix_engine_d.sh`, `fix_gcp_services.sh` - Service-specific fixes
- `github_secrets_update.sh`, `generate_report.sh` - Utility scripts

### AI/ML Testing & Integration
- `test-gemini-integration.py` - Gemini API testing
- `ai_analysis_fallback.py` - AI analysis fallback
- `dashboard_ui_refinement.py` - UI refinement
- `gemini-api-config.json`, `gemini-config.env`, `gemini.env` - Gemini configuration
- `gemini-integration-test-report.json` - Integration test report

### Documentation
- `README.md` - Main project documentation
- `CLOUD_DEPLOYMENT_STATUS.md` - Cloud deployment status (updated with billing blocker)
- `ARCHITECTURE_DIAGRAMS.md` - Architecture documentation
- `GCP_IAM_CONFIGURATION.md` - GCP IAM setup
- `GSM_STATUS.md` - Google Secret Manager status
- Multiple completion/status reports: `*_COMPLETE.md`, `*_REPORT.md`, `*_SUMMARY.md`

---

## `.github/` - CI/CD Workflows

### Copilot Instructions
- `copilot-instructions.md` - Project-specific Copilot guidance

### Workflows (`.github/workflows/`)
- `fix-pipeline.yml` ⚡ - **Main diagnostic & deploy workflow** (with billing probe)
- `deploy_production.yml` ⚡ - **Production deployment** (with billing probe)
- `deploy-production.yml` - Production deployment (legacy)
- `ci-build.yml` - CI build pipeline
- `monorepo-ci.yml`, `monorepo-ci-clean.yml` - Monorepo CI
- `verify-cloudrun-engines.yml` - Cloud Run verification
- `trigger-deploy-production-via-push.yml` - Push-triggered deploy
- Per-engine workflows:
  - `engine-a.yaml` - Engine A Market Data
  - `engine-b.yaml` - Engine B AI/ML
  - `engine-c.yaml` - Engine C Execution
  - `engine-d.yaml` - Engine D Orchestrator
  - `deploy-engine-d.yml` - Engine D deployment
- Per-service workflows:
  - `deploy-frontend.yml` - Frontend deployment
  - `deploy-functions.yml` - Firebase Functions deployment
  - `deploy-gcp.yml` - GCP services deployment
  - `deploy-web.yml` - Web deployment

---

## `engines/` - FastAPI Microservices

### Shared Components
- `performance_config.py` - Performance configuration
- `security_middleware.py` - Security middleware

### Engine A - Market Data (`engines/engine-a/`)
**Purpose:** Market data ingestion, WebSocket feeds, option chains  
**Port:** 8100 (local), Cloud Run service `engine-a`

#### Structure
```
engine-a/
├── main.py                    # FastAPI app, health endpoint
├── Dockerfile                 # Container build
├── requirements.txt           # Python dependencies
├── .dockerignore
├── statement.csv, statement.pdf
├── analytics/
│   ├── ta.py                  # Technical analysis
│   └── __init__.py
├── core/
│   ├── logger.py              # Logging utilities
│   ├── security_middleware.py # Security layer
│   ├── utils.py               # Helper functions
│   └── __init__.py
└── providers/
    ├── dhan.py                # Dhan broker integration
    ├── gemini.py              # Gemini AI integration
    ├── huggingface.py         # HuggingFace integration
    └── __init__.py
```

**Key Endpoints:**
- `GET /health` - Health check
- `GET /api/marketdata` - Market snapshot
- `GET /api/optionchain/ai/{index}` - AI-enhanced option chains

---

### Engine B - AI/ML (`engines/engine-b/`)
**Purpose:** Machine learning inference, AI signals, sentiment analysis  
**Port:** 8101 (local), Cloud Run service `engine-b`

#### Structure
```
engine-b/
├── main.py                    # FastAPI app, ML endpoints
├── Dockerfile                 # Container build
├── requirements.txt           # Python dependencies
├── .dockerignore
├── jwt-secret-key.txt         # JWT secret
├── config/
│   └── settings.yaml          # ML model configuration
├── core/
│   ├── logger.py              # Logging
│   ├── utils.py               # Utilities
│   └── __init__.py
├── models/
│   ├── domain.py              # Domain models
│   ├── schemas.py             # API schemas
│   └── __init__.py
├── models_store/
│   ├── lightgbm_model.pkl     # Trained LightGBM model
│   ├── scaler.pkl             # Feature scaler
│   └── ta_features.json       # Technical analysis features
└── services/
    ├── ai_model_service.py    # AI model orchestration
    ├── data_connector.py      # Data connectors
    ├── ensemble_service.py    # Ensemble models
    ├── explainability_service.py # Model explainability
    ├── feature_pipeline.py    # Feature engineering
    ├── model_zoo.py           # Model registry
    ├── sentiment_service.py   # Sentiment analysis
    ├── strategy_engine.py     # Strategy execution
    ├── ta_utils.py            # Technical analysis utilities
    └── __init__.py
```

**Key Endpoints:**
- `GET /health` - Health check
- `GET /api/ai-signals` - AI trading signals
- `GET /api/models/status` - Model status

---

### Engine C - Execution (`engines/engine-c-execution/`)
**Purpose:** Trade execution, risk management, OAuth, kill-switch, portfolio reconciliation  
**Port:** 8102 (local), Cloud Run service `engine-c-execution`

#### Structure
```
engine-c-execution/
├── main.py ⚡                  # FastAPI app with OAuth, trading, metrics, kill-switch
├── main_minimal.py            # Minimal version
├── Dockerfile                 # Container build
├── requirements.txt           # Python dependencies
├── .dockerignore
├── README.md                  # Engine C documentation
├── temp_api_key.txt           # Temporary API key (demo)
├── analytics/
│   ├── ai_signal_model.py     # AI signal integration
│   ├── hedge_agent.py         # Hedging strategies
│   ├── ml_forecaster.py       # ML forecasting
│   └── risk_optimizer.py      # Risk optimization
├── config/
│   └── settings.yaml          # Configuration
├── core/
│   ├── config.py              # Core configuration (get_secret)
│   ├── event_bus.py           # Event broadcasting
│   └── utils.py               # Utilities (sanitize_input, validate_symbol)
├── models/
│   ├── order_models.py        # Order schemas
│   ├── portfolio_models.py    # Portfolio schemas
│   └── trade_models.py        # Trade schemas
└── providers/
    ├── dhan_rest.py           # Dhan REST API
    ├── dhan_ws.py             # Dhan WebSocket provider
    ├── order_manager.py       # Order management
    └── portfolio_reconciler.py # Portfolio reconciliation
```

**Key Endpoints:**
- `GET /health`, `GET /engine-c/health` - Health check (execution_enabled flag)
- `GET /metrics` - Prometheus metrics
- `POST /api/orders/place` - Place order (requires Bearer token)
- `GET /api/orders/status/{order_id}` - Order status
- `GET /api/orders/history` - Order history
- `POST /api/orders/cancel` - Cancel order
- `POST /api/kill-switch` - Emergency kill-switch
- `GET /api/risk/summary` - Risk summary
- **OAuth Flow:**
  - `GET /api/dhan/auth` - Initiate OAuth
  - `GET /api/dhan/callback` - OAuth callback (stores tokens in GSM)
  - `POST /api/dhan/token` - Manual token storage
  - `GET /api/dhan/token-status` - Token status
- `POST /api/webhooks/dhan` - Dhan webhook (HMAC verification)

**Security:**
- `validate_api_key()` - Bearer token validation (placeholder)
- `verify_webhook_signature()` - HMAC verification for webhooks
- Secrets via Google Secret Manager (`get_secret()`)

---

### Engine D - Orchestrator (`engines/engine-d/`)
**Purpose:** WebSocket orchestration, cross-engine coordination, chat/assistant  
**Port:** 8103 (local), Cloud Run service `engine-d`

#### Structure
```
engine-d/
├── main.py                    # FastAPI app, WebSocket hub
├── health_orchestrator.py     # Health aggregation
├── Dockerfile                 # Container build
├── requirements.txt           # Python dependencies
├── .dockerignore
└── services/
    ├── auth_service.py        # Authentication
    ├── event_broadcaster.py   # Cross-engine event broadcasting
    ├── ws_manager.py          # WebSocket connection management
    └── __init__.py
```

**Key Endpoints:**
- `GET /health` - Health check
- `WS /ws` - WebSocket connection
- Cross-engine calls via `ENGINE_A_URL`, `ENGINE_B_URL`, `ENGINE_C_URL`

**Event Broadcasting:**
- Engine C can POST to Engine D `/broadcast/trade` for real-time updates

---

## `frontend/` - React Application

**Purpose:** User interface, trading dashboard, analytics visualization  
**Tech Stack:** React + Vite + TypeScript + Tailwind CSS  
**Port:** 5173 (local dev), Cloud Run service `frontend`

### Structure
```
frontend/
├── package.json, package-lock.json  # Dependencies
├── tsconfig.json, tsconfig.node.json # TypeScript config
├── vite.config.ts                   # Vite build config
├── tailwind.config.js               # Tailwind CSS config
├── postcss.config.js                # PostCSS config
├── .eslintrc.cjs                    # ESLint rules
├── .env                             # Environment variables (VITE_ENGINE_* URLs)
├── Dockerfile                       # Container build
├── nginx.conf                       # Production web server
├── index.html                       # HTML entry point
├── deploy.ps1                       # Deployment script
├── README.md, QUICKSTART.md         # Documentation
├── IMPLEMENTATION_SUMMARY.md        # Implementation notes
├── populate_db.cjs                  # Database population
├── dashboard-fixes.js               # Dashboard fixes
├── dist/                            # Production build output
│   ├── index.html
│   └── assets/
│       ├── index-CyIMIkMR.css
│       └── index-DWcCWQOB.js
├── reports/
│   └── platform-health-report.json
├── src/
│   ├── main.tsx                     # React entry point
│   ├── App.tsx                      # Root component
│   ├── index.css                    # Global styles
│   ├── vite-env.d.ts                # Vite types
│   ├── firebase.ts, firebaseConfig.ts # Firebase integration
│   ├── components/
│   │   ├── analysis/
│   │   │   ├── AIMetricsPanel.tsx
│   │   │   ├── BacktestPanel.tsx
│   │   │   ├── CorrelationRadar.tsx
│   │   │   ├── DhanOverviewPanel.tsx
│   │   │   ├── ExchangesPanel.tsx
│   │   │   ├── PLHistoryChart.tsx
│   │   │   ├── SentimentHeatmap.tsx
│   │   │   └── StatementPanel.tsx
│   │   ├── dashboard/
│   │   │   ├── AISignals.tsx
│   │   │   ├── DashboardCard.tsx
│   │   │   ├── EngineHealth.tsx
│   │   │   └── TradeLog.tsx
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   └── Topbar.tsx
│   │   └── strategy/
│   │       └── ExecutionPanel.tsx
│   ├── hooks/                       # React hooks for API calls
│   │   ├── useAIAnalysis.ts
│   │   ├── useDhanIntegration.ts
│   │   ├── useDhanOverview.ts
│   │   ├── useDhanStatement.ts
│   │   ├── useDhanTokenStatus.ts
│   │   ├── useExchanges.ts
│   │   ├── useHoldingsAnalysis.ts
│   │   ├── usePLHistory.ts
│   │   ├── useStrategies.ts
│   │   ├── useTradeExecution.ts ⚡  # Engine C integration
│   │   └── useWebSocketFeed.ts
│   ├── pages/                       # Page components
│   │   ├── Analysis.tsx
│   │   ├── Assistant.tsx
│   │   ├── AuthGate.tsx
│   │   ├── CredentialsForm.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Engines.tsx
│   │   ├── GeminiInsights.tsx
│   │   ├── Navbar.tsx
│   │   ├── Settings.tsx
│   │   ├── Strategies.tsx
│   │   ├── StrategyExecution.tsx
│   │   ├── StrategySelector.tsx
│   │   └── SystemHealth.tsx
│   ├── store/                       # State management
│   │   ├── authStore.ts
│   │   └── tradeStore.ts
│   ├── stores/
│   │   ├── appStore.ts
│   │   └── webSocketStore.ts
│   └── utils/
│       └── constants.ts
└── node_modules/                    # Dependencies (installed)
```

**Environment Variables (`.env`):**
- `VITE_ENGINE_A_URL` - Engine A endpoint
- `VITE_ENGINE_B_URL` - Engine B endpoint
- `VITE_ENGINE_C_URL` - Engine C endpoint ⚡
- `VITE_ENGINE_D_URL` - Engine D endpoint
- Firebase config

---

## `functions/` - Firebase Functions

**Purpose:** Serverless utilities for portfolio analysis, AI tasks, credentials  
**Runtime:** Node.js 20, TypeScript  
**Deployment:** Firebase Functions (us-central1)

### Structure
```
functions/
├── package.json, package-lock.json  # Dependencies
├── tsconfig.json                    # TypeScript config
├── firebase-debug.log               # Debug logs
├── .last_ai_task_doc.txt            # Last AI task doc
├── src/
│   ├── index.ts ⚡                   # Main exports
│   ├── config.ts                    # Configuration
│   ├── analyzePortfolio.ts          # Portfolio analysis function
│   ├── startTrading.ts              # Trading start function
│   └── storeCredentials.ts          # Credentials storage function
├── lib/                             # Compiled JavaScript output
│   ├── index.js, index.js.map
│   ├── config.js, config.js.map
│   ├── analyzePortfolio.js, analyzePortfolio.js.map
│   ├── startTrading.js, startTrading.js.map
│   └── storeCredentials.js, storeCredentials.js.map
└── node_modules/                    # Dependencies
```

**Exported Functions:**
- `analyzePortfolio` - Portfolio analysis
- `startTrading` - Start trading session
- `storeCredentials` - Store user credentials

**Build & Deploy:**
```bash
npm run build --workspace=functions
npm run serve --workspace=functions  # Local emulators
firebase deploy --only functions
```

---

## `infrastructure/` - Infrastructure Configuration

### Files (inferred from conversation context)
- `config.json` - **Production GCP endpoints** (Cloud Run URLs)
- `config.local.json` ⚡ - **Local development endpoints** (localhost:8100-8103, 5173)
- `firestore.rules` - Firestore security rules
- Terraform/IaC files (if present)

**Usage:**
- Verifier defaults to `infrastructure/config.json`
- Override with `--config infrastructure/config.local.json` or `INFRA_CONFIG_PATH` env var

---

## `scripts/` - Automation Scripts

### Files (created during session)
- `local_e2e_verify.ps1` ⚡ - Local end-to-end verification orchestrator
  - Starts Docker Compose (optional `--build`)
  - Waits for engine health endpoints
  - Sets `INFRA_CONFIG_PATH=infrastructure/config.local.json`
  - Runs `infinityai_system_verifier.py` with local config

**Usage:**
```powershell
.\scripts\local_e2e_verify.ps1
.\scripts\local_e2e_verify.ps1 -Rebuild  # Force rebuild containers
```

---

## `docs/` - Documentation

### Files
- `ARCHITECTURE.md` - System architecture
- `FIREBASE_SETUP.md`, `FIREBASE_STATUS.md` - Firebase setup and status
- `FIREBASE_INTEGRATION_EXAMPLES.md` - Integration examples
- `SECRETS_SETUP_GUIDE.md`, `SECRETS_STORAGE.md` - Secrets management
- `README_DHAN_SECRETS.md` - Dhan-specific secrets
- `DHAN_OAUTH_SETTINGS.md` - Dhan OAuth configuration
- `DOMAIN_SETUP.md` - Domain setup
- `CLOUD_RUN_AUDIT.md` - Cloud Run audit
- `CI-GITLAB.md` - GitLab CI documentation
- `ANALYSIS_REPORT.md` - Analysis report
- `CLEANUP_REPORT.md` - Cleanup report
- `MIGRATION_COMPLETION_REPORT.md` - Migration completion

---

## `.vscode/` - VS Code Configuration

### Files
- `settings.json` - Editor settings
- `extensions.json` - Recommended extensions
- `copilot-instructions.json` - Copilot instructions
- `mcp.json` - Model Context Protocol configuration

**Recommended Extensions:**
- Python, Pylance, Jupyter
- Cloud Code, Docker
- ESLint, Prettier
- Gemini Code Assist, GitHub Copilot
- Terraform

---

## `.firebase/` - Firebase Local State

### Files
- `hosting.ZnJvbnRlbmRcZGlzdA.cache` - Hosting cache
- `logs/vsce-debug.log` - Debug logs

---

## `.devcontainer/` - Dev Container Configuration

### Files
- `devcontainer.json` - Dev container setup

---

## `.continue/`, `.idx/`, `.gemini/` - AI/IDE Configuration

### Files
- `.continue/config.json`, `.continue/mcp.json` - Continue.dev configuration
- `.idx/dev.nix`, `.idx/integrations.json`, `.idx/mcp.json` - IDX configuration
- `.gemini/.env`, `.gemini/settings.json` - Gemini CLI configuration

---

## `extensions/` - Firebase Extensions

### Files
- `firestore-multimodal-genai.env` - Multimodal GenAI extension config

---

## `config/` - Application Configuration

### Files
- `trading_config.ini` - Trading configuration

---

## Technology Stack Summary

### Backend (Engines)
- **Language:** Python 3.11
- **Framework:** FastAPI
- **Container:** Docker, Cloud Run
- **Secrets:** Google Secret Manager
- **Monitoring:** Prometheus metrics, Cloud Logging

### Frontend
- **Framework:** React 18 + Vite
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State:** Zustand (stores)
- **Server:** Nginx (production), Vite dev server (local)

### Serverless
- **Platform:** Firebase Functions (Gen2)
- **Runtime:** Node.js 20
- **Language:** TypeScript

### Infrastructure
- **Cloud:** Google Cloud Platform (project: `infinity-ai-5ec7c`)
- **Services:** Cloud Run, Cloud Functions, Cloud Build, Artifact Registry, Secret Manager
- **Region:** us-central1
- **CI/CD:** GitHub Actions
- **Local Dev:** Docker Compose, Firebase Emulators

### AI/ML
- **Models:** LightGBM (stored in `engine-b/models_store/`)
- **Integrations:** Gemini API, OpenAI, Anthropic, HuggingFace
- **Features:** Technical analysis, sentiment analysis, explainability

### Data & Messaging
- **Database:** Firestore
- **Real-time:** WebSockets (Engine D hub, Engine A/B feeds)
- **Events:** Event bus (Engine C → Engine D)

---

## Key Entry Points

### Local Development
1. **Start engines:** `docker compose up` (or `docker-compose.yml`)
2. **Start frontend:** `cd frontend && npm run dev` (http://localhost:5173)
3. **Start functions emulators:** `firebase emulators:start --only functions,firestore` (requires Node/Java on PATH)
4. **Run local verification:** `.\scripts\local_e2e_verify.ps1` or `python infinityai_system_verifier.py --config infrastructure/config.local.json`

### Cloud Deployment
1. **Fix billing:** Link active billing account in GCP console
2. **Deploy via CI:** Push to main → triggers `fix-pipeline.yml` or `deploy_production.yml`
3. **Verify deployment:** `python infinityai_system_verifier.py` (uses production config)

### Engine Health Checks
- Engine A: `http://localhost:8100/health` (local) or `https://engine-a-<hash>.run.app/health` (cloud)
- Engine B: `http://localhost:8101/health` (local) or `https://engine-b-<hash>.run.app/health` (cloud)
- Engine C: `http://localhost:8102/health` (local) or `https://engine-c-execution-<hash>.run.app/health` (cloud)
- Engine D: `http://localhost:8103/health` (local) or `https://engine-d-<hash>.run.app/health` (cloud)

---

## Current Blockers

### ❌ Cloud Deployment
- **Issue:** GCP billing delinquent (all 3 billing accounts `OPEN: False`)
- **Impact:** Cloud Build, Cloud Run, Cloud Functions deploys fail with 403/BILLING_DISABLED
- **Resolution:** Create/reopen active billing account in GCP console, link to `infinity-ai-5ec7c`
- **CI Guardrail:** Billing writability probe added to workflows (fails fast with clear message)

### ❌ Local Emulators (Firebase Functions/Firestore)
- **Issue:** Node.js and Java not on PATH in VS Code terminal
- **Impact:** `firebase emulators:start` fails (can't find node.exe or Java)
- **Resolution:** 
  - Java: Install OpenJDK 17 (done via winget), set `JAVA_HOME`, add to PATH (works in fresh PowerShell)
  - Node: Install via `winget install OpenJS.NodeJS.LTS` or fix NVM for Windows PATH
  - **Restart VS Code terminal** after PATH changes

### ✅ Local Docker Engines
- **Status:** Ready to run
- **Usage:** `docker compose up` (fixed build contexts in docker-compose.yml)

### ✅ Local Verification
- **Status:** Ready to run (after engines start)
- **Usage:** `.\scripts\local_e2e_verify.ps1` or `python infinityai_system_verifier.py --config infrastructure/config.local.json`

---

## Next Steps

1. **Unblock local emulators:**
   - Fix Node.js PATH: `winget install OpenJS.NodeJS.LTS`, restart terminal
   - Verify: `node --version`, `npm --version`
   - Test: `firebase emulators:start --only functions,firestore`

2. **Run local verification:**
   - Start engines: `docker compose up`
   - Run verifier: `.\scripts\local_e2e_verify.ps1`
   - Review results: Check console output and JSON report

3. **Unblock cloud deployment:**
   - Fix billing in GCP console (link active billing account)
   - Re-run CI: Push to main or manually trigger workflow
   - Verify: Run `python infinityai_system_verifier.py` (production config)

4. **Update documentation:**
   - Update `CLOUD_DEPLOYMENT_STATUS.md` after successful cloud deploy
   - Document any new issues/fixes in relevant markdown files

---

## File Counts by Type

- **Python:** 40+ files (engines, scripts, verification, diagnostics)
- **TypeScript/JavaScript:** 50+ files (frontend, functions)
- **Markdown:** 30+ documentation files
- **JSON:** 25+ config/report files
- **YAML:** 15+ workflow/config files
- **Docker:** 4 Dockerfiles (engines), 2 docker-compose files
- **Shell/PowerShell:** 10+ automation scripts

---

**Generated:** 2024-12-XX  
**Tool:** GitHub Copilot structure analysis  
**Session Context:** Post-billing-delinquency diagnosis, local fallback setup complete
