# Engine A — Master Orchestration, Risk & AI Services

<div align="center">

![Engine A](https://img.shields.io/badge/Engine--A-Master%20Orchestrator-brightgreen?style=for-the-badge&logo=googlecloud)
![Runtime](https://img.shields.io/badge/Runtime-Python%203.11%20%2F%20FastAPI-blue?style=for-the-badge&logo=python)
![Cloud Run](https://img.shields.io/badge/Cloud%20Run-asia--south1-orange?style=for-the-badge&logo=googlecloud)
![Identity](https://img.shields.io/badge/IAM-sa--engine--a-purple?style=for-the-badge)

</div>

---

## 🏛️ 1. Engine Role & Responsibilities

**Engine A** is the central orchestrator and autonomous risk authority for the **InfinityAI.Pro** trading platform. It enforces institutional risk management, portfolio sizing, diagnostic readiness, macroeconomic intelligence, and multi-channel telemetry.

### Core Responsibilities:
1. **Dynamic Risk Gates & VaR Sizing:**
   * Computes **99% Parametric EWMA Value-at-Risk (VaR)** and Conditional Value-at-Risk (CVaR).
   * Calculates dynamic Kelly Criterion lot sizes conforming to SEBI 2026 contract lot rules (NIFTY: 65, BANKNIFTY: 30, FINNIFTY: 65, SENSEX: 20).
2. **Pre-Flight Diagnostic Health Clearance (08:15 IST):**
   * Dispatches 7 parallel health probes testing Engines A/B/C, BigQuery Lakehouse, GCS Model Vault, and Dhan Link in ~1,000 ms.
   * Emits pre-flight clearance telemetry to Telegram (`@Raghu1718_bot`).
3. **Pre-Market Macro Radar with Vertex AI Search Grounding (08:30 IST):**
   * Employs **Vertex AI Gemini 2.5 Flash Grounding with Google Search** to mine live GIFT Nifty points, Brent Crude oil percentage changes, and FII/DII institutional cash market flows.
   * Performs canonical gap classification (`expected_gap`) and deterministic narrative reconciliation to eliminate semantic contradictions.
4. **Post-Market EOD Settlement & Multi-Tier AI Journal (15:35 IST):**
   * Generates comprehensive trade reconciliation and post-market review (`eod_trading_journal`).
   * Adheres to the granular multi-tier schema distinguishing `market_hours_scans` (5,045), `directional_model_candidates`, `risk_vetoed_candidates`, `eligible_trade_setups`, and `closed_shadow_trades`.
5. **Multi-Channel Alert Dispatcher:**
   * Dispatches actionable trade alerts, pre-flight telemetry, macro radar, and EOD digests via Telegram and WhatsApp Business API.
   * Implements strict signal filtering to suppress non-actionable `HOLD` / `VETOED` events and maintain zero-noise channels.

---

## ⚙️ 2. Cloud Infrastructure & Service Specs

* **Deployment Target:** Google Cloud Run (`asia-south1`)
* **Service Account:** `sa-engine-a@project-841b7f97-5ee3-4fbe-920.iam.gserviceaccount.com`
* **CPU / Memory Allocation:** 1 vCPU / 512Mi RAM
* **Security & Auth:** Inter-service routing validated via `X-Internal-Token` and Application Default Credentials (ADC).
* **Live Service URL:** `https://engine-a-r2f5flt77q-el.a.run.app`

---

## 📡 3. Key Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status and timestamp. |
| `POST` | `/api/v1/preflight/trigger` | Triggers the 08:15 IST 7-tier pre-flight diagnostic clearance. |
| `POST` | `/api/v1/premarket/briefing` | Triggers the 08:30 IST Vertex AI Search Grounded macro radar. |
| `POST` | `/api/v1/eod-journal/trigger` | Triggers the 15:35 IST EOD settlement and qualitative AI trading journal. |
| `GET` | `/api/v1/macro/news/latest` | Returns the latest grounded macroeconomic telemetry document. |
| `GET` | `/api/v1/greeks/surface/{symbol}` | Calculates analytical Black-Scholes Greeks surface ($\Delta, \Gamma, \Theta, \mathcal{V}$). |

---

<div align="center">
  <sub>InfinityAI.Pro Engine A — Master Orchestration & Institutional Risk Management.</sub>
</div>
