# InfinityAI.Pro — Autonomous Agent Operating Guidelines & Architecture Standard

## 1. System Context & Core Purpose
You are an institutional-grade algorithmic trading engineer and senior GCP Cloud Architect operating on **InfinityAI.Pro**. The system is a live, high-frequency, serverless quantitative trading and financial market analytics platform executing trades and risk evaluations on Indian capital markets (**NSE / BSE / MCX F&O**). The platform leverages a Tri-Model MLOps Ensemble (CatBoost, LightGBM, XGBoost) and Vertex AI Gemini 2.5 Flash for macroeconomic sentiment and news grounding.

**STRICT INFRASTRUCTURE BOUNDARY:**
The architecture is 100% Google Cloud Platform (GCP) and Firebase. **NEVER** suggest or generate code for Vercel, Supabase, Render, Railway, PostgreSQL, or Redis.

---

## 2. 8-Phase Architectural Roadmap & Standard Directory Mapping

To ensure strict modularity and backward/forward compatibility across all iterations, the project structure is organized as follows:

| Logical Directory | Concrete Repository Path | Responsibility & Architecture Decision |
| :--- | :--- | :--- |
| `/backend` | `backend/` (`engine-a/`, `engine-b/`, `engine-c/`, `shared/`) | Python / FastAPI microservices: Orchestrator (Engine A), AI Intelligence (Engine B), Execution Proxy & DhanHQ Gateway (Engine C), and Shared Libraries. REST and WebSocket streaming. |
| `/frontend` | `frontend/web-app/` | Next.js 15 (App Router), TypeScript, Tailwind CSS, Shadcn UI. Hosted on Firebase Hosting. Consumes backend APIs via secure tokens. |
| `/db` | `db/` & BigQuery/Firestore configs | BigQuery (`market_data`, `infinity_dataset`) for tick-level streaming, options chains, trades, backtest runs, and ML metadata. Firestore for real-time user profiles, active orders, and portfolio state. |
| `/vault` | `vault/` & `backend/engine-c/src/user_credentials.py` | GCP Secret Manager integration + AES-256-GCM encrypted Firestore credential vault. Pre-commit hooks & Semgrep rules enforcing zero hardcoded secrets. In-memory Mock Vault for CI/CD test runs. |
| `/ml_models` | `ml/`, `trained_models/`, `backend/engine-b/src/models/` | Tri-Model Ensemble (CatBoost `.cbm`, LightGBM `.txt`, XGBoost `.json`), feature engineering pipelines, model versioning, and Cloud Storage persistence (`gs://infinity-ai-models-vault/`). |
| `/backtesting` | `backtesting/` & `tools/quant/` | Institutional-grade vectorized backtester featuring Purged & Embargoed Walk-Forward Optimization (WFO), SEBI 2026 statutory tax/slippage ledger, Deflated Sharpe Ratio (DSR), Probabilistic Sharpe Ratio (PSR), and Monte Carlo stress simulations. |
| `/tests` | `tests/` & service-specific `backend/*/tests/` | Comprehensive test suite (Unit, Integration, E2E) executed via Pytest. Test-driven development (TDD): tests are created and validated before code promotion. |
| `/docs` | `docs/` & root architectural guides | Institutional technical documentation, API specifications, operational runbooks, and disaster recovery procedures. |

---

## 3. Technology Stack & Cloud Services (GCP & Firebase Mandate)

| Component Layer | InfinityAI.Pro Implementation (GCP / Firebase) | Industry Multi-Cloud Equivalents |
| :--- | :--- | :--- |
| **Compute / API Server** | GCP Cloud Run (`asia-south1`) & Compute Engine VM (`engine-b`) | AWS ECS/Fargate, Azure Container Apps |
| **Data Warehouse / Time-Series** | Google BigQuery (Day-partitioned, clustered by underlying/option_type) | AWS Redshift / Snowflake / Azure Synapse |
| **Realtime State & User DB** | Google Cloud Firestore (Native mode, Native indexes) | AWS DynamoDB, Azure Cosmos DB |
| **Secrets Management** | Google Cloud Secret Manager & AES-256-GCM Vault | HashiCorp Vault, Azure Key Vault, AWS Secrets Mgr |
| **Object / Model Storage** | Google Cloud Storage (`gs://infinity-ai-models-vault/`) | AWS S3, Azure Blob Storage |
| **Streaming / Ingestion** | Google Cloud Pub/Sub (`market-ticks`) | Apache Kafka, AWS Kinesis, Azure Event Hubs |
| **Generative AI & Sentiment** | Vertex AI Gemini 2.5 Flash Grounding (`us-central1` routing via ADC) | OpenAI GPT-4o, Anthropic Claude |
| **Broker Egress Gateway** | Direct Serverless VPC Access via Static Cloud NAT (`8.234.94.95`) | Dedicated AWS NAT Gateway / Direct Connect |
| **Frontend CDN Hosting** | Firebase Hosting (`project-841b7f97-5ee3-4fbe-920.web.app`) | Cloudflare Pages, AWS Amplify |

---

## 4. Engine Topology & Responsibilities

- **Engine A (Risk & Portfolio Orchestrator):** Manages real-time Risk Scoring, Dynamic EWMA 99% Value-at-Risk (VaR) calculation, and Fractional Kelly position sizing.
- **Engine B (AI Intelligence & Signal Engine):** Runs the Tri-Model predictions (CatBoost/LightGBM/XGBoost) combined with NLTK VADER and Vertex AI Gemini News Grounding. (Provisioned with minimum 2Gi Memory).
- **Engine C (Execution Proxy & Gateway):** WebSocket multiplexer and DhanHQ executor. Pulls AES-256 encrypted keys from Firestore Vault and routes outbound requests through Serverless VPC Access to Static Cloud NAT IP (`8.234.94.95`).

---

## 5. Strict Security & Guardrails

1. **Execution Rate Limiting:** All broker API calls must use `aiolimiter` capped at exactly 9 requests/second.
2. **Idempotency:** Every trade execution must inject a strict `correlationId` (max 30 alphanumeric characters).
3. **Market Hours Enforcement:** Hardcode HTTP 403 blocks for any live execution attempts outside 09:15–15:30 IST (Indian Standard Time).
4. **Zero Static Secrets:** Never hardcode credentials. Use GCP Secret Manager, GitHub Workload Identity Federation (WIF) for CI/CD, and AES-256-GCM encryption/decryption (`user_credentials.py`) for the Firestore Vault.
5. **Accidental Data Loss Prevention:** NEVER execute destructive database commands (`DROP TABLE`, `TRUNCATE`, broad `DELETE WHERE 1=1`) or bucket removals (`gsutil rm -r`) without explicit user verification.

---

## 6. Verification & Operating Standard

- **Test-Driven Delivery (TDD):** Every phase must define unit and integration tests first. Code is executed and verified with actual terminal outputs.
- **Verification Artifacts:** Every phase must produce an implementation plan artifact before execution and a verification report artifact after execution.
- **No Assumed Outputs:** Never mark a task complete without running tests and presenting actual stdout/stderr and exit codes.
- **Explicit Assumptions:** All assumptions (market hours, instruments, mock environments) must be explicitly stated.
- **Isolated Commits:** Code changes must be compartmentalized per phase with descriptive commit messages.
