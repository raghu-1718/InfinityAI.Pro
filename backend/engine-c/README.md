# Engine C — Broker Gateway, Execution & Cryptographic Vault

<div align="center">

![Engine C](https://img.shields.io/badge/Engine--C-Broker%20Execution%20Gateway-brightgreen?style=for-the-badge&logo=googlecloud)
![Runtime](https://img.shields.io/badge/Runtime-Python%203.11%20%2F%20FastAPI-blue?style=for-the-badge&logo=python)
![Cloud Run](https://img.shields.io/badge/Cloud%20Run-asia--south1%20(VPC%20NAT)-orange?style=for-the-badge&logo=googlecloud)
![Static IP](https://img.shields.io/badge/Static%20NAT-8.234.94.95-blueviolet?style=for-the-badge)
![Identity](https://img.shields.io/badge/IAM-sa--engine--c-purple?style=for-the-badge)

</div>

---

## 📡 1. Engine Role & Responsibilities

**Engine C** is the secure execution proxy, broker gateway, and WebSocket multiplexer for **InfinityAI.Pro**. It interfaces directly with **DhanHQ API v2**, manages the cryptographic credential vault, enforces network-level IP whitelisting, and oversees automated trade execution.

### Core Responsibilities:
1. **DhanHQ API v2 Client & Session Pool:**
   * Interfaces with DhanHQ REST and WebSocket marketfeed endpoints.
   * Manages 24/7 keepalive token renewals (`dhan-token-keepalive-job` at 06:00 and 18:00 IST).
2. **Cryptographic Credential Vault (`user_credentials.py`):**
   * Implements authenticated **AES-256-GCM encryption/decryption** with a random 12-byte initialization vector (`IV`), 16-byte authentication tag, and zero plaintext exposure in Firestore (`user_credentials/raghu_primary`).
   * Dynamic Secret Manager key resolution from `USER_CREDENTIALS_KEY`.
3. **Strict Network & Execution Guardrails:**
   * **Static Cloud NAT IP Egress:** All outbound Dhan traffic routes via Serverless VPC Access to `8.234.94.95` (Dhan server IP whitelisted).
   * **Rate Limiting:** Enforces `aiolimiter` strictly throttled to **9 req/s** (below broker 10 req/s threshold).
   * **Idempotency:** Generates and validates 30-character alphanumeric `correlationId` on every trade ticket.
   * **Market Hours Protection:** Hardcodes HTTP 403 blocks for order placement outside **08:55–15:45 IST**.
4. **Three-Tier Dynamic Trailing Stop Engine:**
   * Monitors live LTP and executes automated profit locks:
     * `Tier 1 (+8% Gain)` $\to$ Moves Stop-Loss to Breakeven.
     * `Tier 2 (+12% Gain)` $\to$ Trailing Lock at $+6\%$ Net Profit.
     * `Tier 3 (+15% Gain)` $\to$ Dynamic Trail / Runner Expansion.
5. **SEBI 2026 Statutory Tax & Charge Calculator:**
   * Computes exchange turnover, STT, SEBI regulatory fees, stamp duty, and GST ($18\%$) on every potential setup to enforce a positive net edge before trade release.

---

## ⚙️ 2. Cloud Infrastructure & Service Specs

* **Deployment Target:** Google Cloud Run (`asia-south1`)
* **Service Account:** `sa-engine-c@project-841b7f97-5ee3-4fbe-920.iam.gserviceaccount.com`
* **Static Egress NAT IP:** `8.234.94.95` (Serverless VPC Access connector)
* **CPU / Memory Allocation:** 1 vCPU / 512Mi RAM
* **Live Service URL:** `https://engine-c-r2f5flt77q-el.a.run.app`

---

## 📡 3. Key Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status and Dhan gateway readiness. |
| `GET` | `/api/dhan/connection/status` | Live 24/7 probe verifying active Dhan authentication & token validity. |
| `GET` | `/api/dhan/funds` | Live available margin, SOD limit, collateral, and withdrawable balance. |
| `GET` | `/api/dhan/positions` | Real-time open positions, quantities, and MTM unrealized P&L. |
| `GET` | `/api/dhan/holdings` | Equity holdings, invested value, current value, and day's P&L. |
| `GET` | `/api/dhan/trades` | Completed trade book execution logs and fill timestamps. |
| `GET` | `/api/dhan/market/quotes` | Live Dhan marketfeed OHLCV quotes across NSE/BSE segments. |
| `POST` | `/api/dhan/credentials/update` | Encrypts and persists updated Dhan client ID and tokens to Firestore Vault. |

---

<div align="center">
  <sub>InfinityAI.Pro Engine C — Broker Gateway & Cryptographic Execution Engine.</sub>
</div>
