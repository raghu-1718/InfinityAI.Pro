# Antigravity — Master Infrastructure Disclosure Report

**Project:** `galvanic-pulsar-482815-h0`  
**Region:** `asia-south1`  
**Date:** 2026-01-05  
**Analyst:** Antigravity (AI Agent)

---

## 1. Executive Summary

The infrastructure for **InfinityAI.Pro** is in a **Critical / Partially Broken** state. While the Core Orchestration (`engine-a`) and Execution (`engine-c`) services are deployed, the AI Signal service (`engine-b`) is failing to start. Furthermore, **severe configuration drift** exists: services are hardcoded to communicate with a _different_ GCP project (`...-429140669077`), meaning the orchestrator is likely calling dead or incorrect endpoints. Critical dependencies like **Secret Manager** appear empty, which will cause authentication failures for external broker APIs (DhanHQ).

**Immediate Action Required:** Fix `engine-b` startup, update service-to-service URLs (Environment Variables), and populate Secret Manager.

---

## 2. Master Resource Ledger

### 2.1 Cloud Run Services (Compute)

| Service      | Region      | Status     | URL Hash        | Accessibility   | Notes                                               |
| :----------- | :---------- | :--------- | :-------------- | :-------------- | :-------------------------------------------------- |
| **engine-a** | asia-south1 | **ACTIVE** | `...-228557...` | Public          | Orchestrator. Running.                              |
| **engine-b** | asia-south1 | **FAILED** | `...-228557...` | **Unreachable** | "Container failed to start". Critical AI Component. |
| **engine-c** | asia-south1 | **ACTIVE** | `...-228557...` | Public          | Execution. Healthy.                                 |

### 2.2 Firebase & Frontend

| Component     | Status      | Details                                                       |
| :------------ | :---------- | :------------------------------------------------------------ |
| **Hosting**   | **UNKNOWN** | CLI failed to list sites. Potential permission/linking issue. |
| **Functions** | **Unknown** | Deployed status unclear from CLI errors.                      |
| **Web App**   | Code Ready  | Next.js 16.0.7 / React 19. Modern stack (Radix UI, Tailwind). |

### 2.3 Data & State

| Resource              | Status    | Criticality  | findings                                                                   |
| :-------------------- | :-------- | :----------- | :------------------------------------------------------------------------- |
| **Firestore**         | **ERROR** | **Critical** | CLI Permission Denied. Code uses it for User Credentials.                  |
| **Secret Manager**    | **EMPTY** | **Critical** | List returned 0 items. Code expects `dhan-client-id`, `dhan-access-token`. |
| **Artifact Registry** | Active    | High         | `cloud-run-source-deploy` repository exists.                               |
| **Cloud Storage**     | **ERROR** | Medium       | `gsutil` failed (path/permission). ML Models likely missing.               |

### 2.4 AI & Logging

| Resource          | Enabled | Status                                                          |
| :---------------- | :------ | :-------------------------------------------------------------- |
| **Vertex AI**     | YES     | No custom Access Points/Models found. Uses Gemini API directly. |
| **Cloud Logging** | YES     | Standard `_Required` sink active.                               |

---

## 3. Component-Wise Architecture Breakdown

### 3.1 Frontend Layer (`frontend/web-app`)

- **Framework:** Next.js 16 (React 19, App Router).
- **Styling:** TailwindCSS v4, Radix UI.
- **State:** Zustand, TanStack Query.
- **Authentication:** Firebase Auth (inferred).

### 3.2 Backend Layer (Microservices)

Built on **Python 3.11 / FastAPI**.

- **`engine-a` (Orchestration):**
  - **Role:** Traffic cop. Validates risk, checks sessions, calls B for signal, C for execution.
  - **Logic:** Hardcoded "Safe" VIX cache. Risk scoring logic (VaR, CVaR) implemented.
  - **Flaw:** Hardcoded `ENGINE_B_URL` defaults to old project.
- **`engine-b` (AI Signals):**
  - **Role:** Signal generation using ML Ensemble (XGBoost, LightGBM, CatBoost).
  - **Logic:** "Weighted Voting" system. Uses Gemini 2.5 Flash/Pro.
  - **Status:** **CRASHING**. Likely due to missing model files or memory issues during ML init.
- **`engine-c` (Execution):**
  - **Role:** DhanHQ Broker Connector.
  - **Capabilities:** TWAP/VWAP Order splitting. ML-based slippage prediction.
  - **Logic:** "System Status" authority.

### 3.3 Shared Library (`backend/shared`)

- **Modules:** `google_integrations` (Glass, Agents), `performance`, `utils`.
- **Design:** Clean, modular wrapper around GCP services. Good pattern.

---

## 4. Detailed Gaps & Critical Risks

### ❌ 4.1 Configuration Drift (The "Split Brain" Problem)

**Severity: CRITICAL**

- **Issue:** `engine-a` code defaults `ENGINE_B_URL` and `ENGINE_C_URL` to:
  `https://engine-x-429140669077.asia-south1.run.app`
- **Reality:** Services are deployed at:
  `https://engine-x-228557716858.asia-south1.run.app`
- **Impact:** `engine-a` will try to call the old project. If that project is down or inaccessible, **all trades will fail** or hang.

### ❌ 4.2 Missing Secrets

**Severity: CRITICAL**

- **Issue:** `gcloud secrets list` returned 0 items.
- **Impact:** Code calling `get_secret("dhan-client-id")` will fail (returns empty string) -> Authentication fails -> **No Trading**.
- **Fix:** Must populate `dhan-client-id`, `dhan-access-token`, `dhan-api-secret` immediately.

### ❌ 4.3 Engine B Failure

**Severity: HIGH**

- **Issue:** `engine-b` is in a failed state.
- **Hypothesis:** It attempts to load ML models from GCS bucket `[PROJECT_ID]-ml-models` on startup. If the bucket/files are missing (likely, given storage error), the container crashes.
- **Impact:** No AI signals. `engine-a` will fallback to "HOLD" or error out.

### ❌ 4.4 Firestore Permissions

**Severity: HIGH**

- **Issue:** CLI cannot access Firestore. Agent/User credentials stored there.
- **Impact:** If the service account also lacks permissions, user login and trade verification will fail.

---

## 5. Improvement Recommendations & Roadmap

### Phase 1: Stabilization (Immediate)

1.  **Populate Secrets:** Create required secrets in Google Secret Manager.
2.  **Fix URLs:** Deploy `engine-a` with environment variables `ENGINE_B_URL` and `ENGINE_C_URL` set to the **current, correct** Cloud Run URLs.
3.  **Fix Engine B:** Check logs for `engine-b`. Likely need to create the ML Models bucket and upload initial model artifacts (or add graceful fallback for missing models).
4.  **Verify IAM:** Ensure `Default Compute Service Account` has `Secret Manager Secret Accessor` and `Datastore User` roles.

### Phase 2: Resilience (Short Term)

1.  **Remove Hardcoded Defaults:** Change code to **fail fast** if service URLs are not in ENV, rather than defaulting to a random project ID.
2.  **Health Check Interdependency:** `engine-c` checks `engine-b` health on startup. If B is down, C might become unhealthy. Decouple startup health checks or make them non-blocking (already attempted in code, verify execution).

### Phase 3: Scaling (Medium Term)

1.  **Async Events:** Move inter-service communication to **Cloud Pub/Sub** instead of direct HTTP calls to decouple A, B, and C.
2.  **Redis Cache:** Replace in-memory caching (seen in `engine-a` and `engine-c`) with a managed Redis instance for shared state across instances.

## 6. Conclusion

The codebase is sophisticated (Financial ML, Microservices, Modern Frontend), but the **infrastructure deployment is disjointed**. The focus must shift from "Coding" to "DevOps/SRE" to wire these components correctly in the new GCP project.
