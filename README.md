# InfinityAI.Pro — Institutional Algorithmic Trading Platform

<div align="center">

![InfinityAI.Pro](https://img.shields.io/badge/InfinityAI.Pro-Institutional%20Production-brightgreen?style=for-the-badge&logo=googlecloud)
![Version](https://img.shields.io/badge/version-v11.0%20Live%20Production-blue?style=for-the-badge)
![Cloud](https://img.shields.io/badge/GCP-100%25%20Cloud%20Run%20%2B%20Firebase-orange?style=for-the-badge&logo=googlecloud)
![AI](https://img.shields.io/badge/AI-BQML%20%2B%20Tri--Model%20%2B%20Vertex%20AI%20Gemini%202.5%20Flash-purple?style=for-the-badge&logo=google)
![Broker](https://img.shields.io/badge/Broker-DhanHQ%20v2%20API%20(AES--256%20Vault)-blueviolet?style=for-the-badge)
![Telemetry](https://img.shields.io/badge/Telemetry-Telegram%20%2B%20WhatsApp%20Alerts-2CA5E0?style=for-the-badge&logo=telegram)
![License](https://img.shields.io/badge/license-Proprietary-red?style=for-the-badge)

### 🚀 100% Autonomous Multi-Engine Algorithmic Trading Platform for Indian Capital Markets (NSE / BSE / MCX)

**[Live Trading Dashboard](https://project-841b7f97-5ee3-4fbe-920.web.app)** | **GCP Project**: `project-841b7f97-5ee3-4fbe-920` | **Primary Region**: `asia-south1` (Mumbai)  
**Static Cloud NAT Egress IP**: `8.234.94.95` | **Engine B (Inference)**: `https://engine-b-r2f5flt77q-el.a.run.app` | **Telegram Bot**: `@Raghu1718_bot`

</div>

---

## 📋 1. Executive Summary & Core Purpose

**InfinityAI.Pro** is an institutional-grade algorithmic trading platform executing real-money and high-fidelity shadow trading on Indian capital markets (NSE equity derivatives, index options, BSE, and MCX). Built **100% natively on Google Cloud Platform (GCP) and Firebase**, the architecture leverages a **Tri-Model MLOps Ensemble (CatBoost, LightGBM, XGBoost)** combined with **BigQuery ML Boosted Trees** and **Vertex AI Gemini 2.5 Flash Grounding with Google Search** for real-time macroeconomic synthesis.

### 🌟 Key Architectural Pillars
* **Strict Infrastructure Boundary:** 100% GCP serverless architecture (Cloud Run, Cloud Storage, BigQuery, Pub/Sub, Cloud Secret Manager, Cloud Schedulers, and Cloud Firestore).
* **Deterministic Risk & Capital Preservation:** Parametric 99% EWMA VaR limits, dynamic Kelly position sizing, and an automated **14-period Wilder's ADX $< 25.0$ Capital Preservation Veto Gate** that blocks option buying during sideways chop to prevent theta decay.
* **Tri-Model MLOps & BigQuery ML:** 3-Class inference ($P_{\text{SELL}}, P_{\text{HOLD}}, P_{\text{BUY}}$) executed natively in BigQuery (`ML.PREDICT` on `infinity_dataset.xgboost_live_model`) and synchronized with 48 GCS-vaulted gradient boosting models (`gs://infinity-ai-models-vault`).
* **Vertex AI Google Search Grounding:** Daily 08:30 IST pre-market macro radar mining live GIFT Nifty, Brent Crude, US 10Y yields, and FII/DII cash flow data with canonical bidirectional reconciliation.
* **Cryptographic Vault & DhanHQ Integration:** DhanHQ API v2 client routed via direct Serverless VPC Access to a Static Cloud NAT IP (`8.234.94.95`), secured with AES-256-GCM encrypted credential vaulting in Firestore (`user_credentials/raghu_primary`).

---

## 🏛️ 2. End-to-End System Topology

```mermaid
flowchart TB
    subgraph Presentation ["1. Frontend & Client (Firebase Hosting)"]
        UI["Next.js 16 App Router<br/>(project-841b7f97-5ee3-4fbe-920.web.app)"]
        CapSlider["One-Input Autonomous Capital Controller<br/>(₹10,000 – ₹5,00,000)"]
        Telemetry["Real-Time Orderbook, Greeks & Trailing SL Ladder"]
        PayoffVis["Black-Scholes Options Payoff & IV Smile Visualizer"]
        JournalVis["Vertex AI Gemini 2.5 Multi-Tier EOD Journal Viewer"]
    end

    subgraph DataPipeline ["2. Real-Time Ingestion & Storage"]
        DhanTicks["DhanHQ WebSocket Stream"] --> PubSub["GCP Pub/Sub<br/>Topic: market-ticks"]
        PubSub --> BQ_Live["BigQuery Live Ticks<br/>(market_data.live_ticks)"]
        PubSub --> BQ_Options["BigQuery Options Ticks<br/>(market_data.options_ticks)"]
        PubSub --> BQ_Hist["BigQuery Historical Vault<br/>(infinity_dataset.market_ticks_history)<br/>60,998+ Golden Historical Ticks"]
    end

    subgraph Intelligence ["3. Engine B — AI & ML Core (Cloud Run asia-south1)"]
        GCS["GCS Model Vault<br/>(gs://infinity-ai-models-vault)<br/>48 Model Artifacts"] --> Ensemble["Tri-Model Ensemble (CatBoost, LightGBM, XGBoost)"]
        BQ_Hist --> BQML["BigQuery ML.PREDICT<br/>(infinity_dataset.xgboost_live_model)"]
        BQML --> 3Class["3-Class Probability Triplet (P_SELL, P_HOLD, P_BUY)"]
        Ensemble --> 3Class
        3Class --> VetoFilter["Institutional Risk Gate<br/>(ADX < 25.0 Theta Decay VETO)"]
        VetoFilter --> AlphaSignal["Consensus Alpha Signal (BUY / SELL / HOLD)"]
    end

    subgraph Orchestration ["4. Engine A — Risk Orchestrator (Cloud Run asia-south1)"]
        AlphaSignal --> RiskEngine["Dynamic 99% EWMA VaR & CVaR (2.5% Max Risk)"]
        RiskEngine --> KellySizing["Margin-Aware Dynamic Lot Sizing"]
        KellySizing --> GreeksEngine["Black-Scholes Greeks Engine<br/>(Analytical Δ, Γ, Θ, Vega & IV Smile)"]
        GreeksEngine --> PremarketRadar["Vertex AI Gemini 2.5 Flash Macro Radar<br/>(08:30 IST Google Search Grounding)"]
        GreeksEngine --> EODJournal["Multi-Tier EOD AI Journal Service<br/>(15:35 IST Trade & Scan Accounting)"]
        GreeksEngine --> AlertDispatch["Multi-Channel Alert Dispatcher<br/>(Telegram @Raghu1718_bot & WhatsApp)"]
        GreeksEngine --> ClearedOrder["Autonomous Strategy Ticket + Correlation ID"]
    end

    subgraph Execution ["5. Engine C — Execution & Broker Gateway (Cloud Run asia-south1)"]
        ClearedOrder --> Guardrails["Execution Guardrails<br/>• aiolimiter (9 req/s)<br/>• correlationId (max 30c)<br/>• Market Hours (08:55–15:45 IST)"]
        Guardrails --> Vault["Firestore Credential Vault<br/>(AES-256-GCM Decryption)"]
        Vault --> MultiLeg["Multi-Leg Strategy Engine<br/>(Spreads, Condors, Straddles, ITM-1 Options)"]
        MultiLeg --> DhanPool["DhanClientPool (Session Pool + Circuit Breaker)"]
        DhanPool --> VPC["Serverless VPC Access<br/>Static Cloud NAT (8.234.94.95)"]
        VPC --> DhanHQ["DhanHQ API v2 Gateway<br/>(NSE / BSE / MCX)"]
        DhanHQ --> TrailingDaemon["3-Tier Trailing Stop Daemon<br/>(+8% Breakeven / +12% Lock / +15% Dynamic Exit)"]
    end

    subgraph MultiChannelAlerts ["6. Real-Time Telemetry & Alert Channels"]
        AlertDispatch --> TG["Telegram Bot (@Raghu1718_bot)<br/>• 08:15 IST Pre-Flight Clearance<br/>• 08:30 IST Pre-Market Macro Radar<br/>• Live High-Conviction BUY/SELL Signals<br/>• 15:35 IST Vertex AI Gemini EOD Journal"]
        AlertDispatch --> WA["WhatsApp Business API Gateway"]
    end

    UI <--> EngineA
    UI <--> EngineC
```

---

## ⚙️ 3. Engine Roles & Cloud Infrastructure Boundary

| Subsystem / Resource | Deployment Target | Core Functionality | Security, Limits & Specs |
| :--- | :--- | :--- | :--- |
| **Engine A (Orchestrator)** | Cloud Run (`asia-south1`) | Dynamic 99% VaR, Pre-Flight Health, Macro Radar, EOD AI Journal, Telegram Alerts | Identity: `sa-engine-a`, CPU: 1, Memory: 512Mi |
| **Engine B (ML Intelligence)**| Cloud Run (`asia-south1`) | 3-Class BQML inference, GCS Tri-Model Ensemble, ADX Veto Gate, NLTK sentiment | Identity: `sa-engine-b`, CPU: 2, Memory: 2Gi *(ML Ops)* |
| **Engine C (Broker Gateway)** | Cloud Run (`asia-south1`) | DhanHQ API v2 proxy, WebSocket multiplexer, AES-256-GCM Vault, Trailing Stops | Identity: `sa-engine-c`, Static NAT IP: `8.234.94.95` |
| **Frontend Web App** | Firebase Hosting | Next.js 16 App Router SSR dashboard with real-time reactive Firestore listeners | URL: `project-841b7f97-5ee3-4fbe-920.web.app` |
| **BigQuery Lakehouse** | BigQuery (`asia-south1`) | 60,998 historical golden ticks (`market_ticks_history`), streaming `live_ticks` | Direct Pub/Sub BigQuery Sink Subscription |
| **Cloud Storage Vault** | Cloud Storage | 48 model artifacts (CatBoost, LightGBM, XGBoost, HMM, Kalman Filter, Scalers) | Bucket: `gs://infinity-ai-models-vault/` |
| **Secret Manager** | Secret Manager | Zero plaintext credentials: `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `USER_CREDENTIALS_KEY` | Dynamic runtime resolution |
| **Cloud Schedulers** | Cloud Scheduler | 12 automated crons (08:15 Preflight, 08:30 Macro Radar, 1-min Options Streamer, 15:35 EOD) | HTTP targets with OIDC service authentication |

---

## 🛡️ 4. Strict Security & Guardrails

1. **Execution Rate Limiting:** All broker API calls are strictly throttled via `aiolimiter` capped at exactly **9 req/s** (Dhan limit: 10 req/s).
2. **Idempotency & Audit Trail:** Every trade execution carries an immutable, strictly validated `correlationId` (max 30 characters).
3. **Market Hours Enforcement:** Hardcoded HTTP 403 blocks for any trade execution attempts outside **08:55–15:45 IST**.
4. **Zero Static Secrets:** Never hardcode credentials. All tokens are resolved dynamically from GCP Secret Manager and stored using AES-256-GCM authenticated encryption (`12-byte IV` + `16-byte Auth Tag`) in Firestore (`user_credentials/raghu_primary`).
5. **Static NAT Whitelisting:** All outbound connections to DhanHQ API v2 are routed through Google Cloud Serverless VPC Access to the Static Cloud NAT IP: `8.234.94.95`.

---

## 🚀 5. Automated CI/CD & Deployment Workflow

Deployment is 100% automated via Google Cloud Build and GitHub Actions. **Manual server deployments are strictly prohibited.**

```bash
# Push changes to GitHub main branch to trigger automated CI/CD:
git add .
git commit -m "feat: institutional upgrade for production stack"
git push origin main
```

Google Cloud Build triggers build, containerize, and deploy steps across `engine-a`, `engine-b`, `engine-c`, and Firebase Hosting automatically with zero downtime and 100% traffic migration upon passing health probes.

---

<div align="center">
  <sub>Built with 🧠 Vertex AI & ⚡ Google Cloud Platform for Institutional Quantitative Trading.</sub>
</div>
