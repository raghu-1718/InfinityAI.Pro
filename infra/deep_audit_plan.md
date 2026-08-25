# Antigravity — Deep Infrastructure & Code Audit

**Project:** `galvanic-pulsar-482815-h0`  
**Region:** `asia-south1`  
**Date:** 2026-01-05

---

## 1. Executive Summary

**Status:** **Critical / Partially Broken**  
The platform is in a "split-brain" state. The code is hardwired for an old GCP project (`...-429140669077`), while deployments are targeting the new one (`galvanic-pulsar-482815-h0`).

**Top 3 Blockers:**

1.  **AI Signal Engine (Engine-B) Down:** The container fails to start, likely due to a crash when failing to load ML models from a missing/empty Cloud Storage bucket (`galvanic-pulsar-482815-h0-ml-models`).
2.  **Configuration Drift:** `engine-a` is calling incorrect URLs for peer services, guaranteed to cause timeout/networking errors.
3.  **Missing Secrets:** Critical DhanHQ API credentials are missing from Secret Manager, blocking all real-world execution.

---

## 2. System Capabilities & Architecture Map

### 2.1 Backend Microservices (Cloud Run)

| Service      | Role             | Tech Stack                    | Dependencies                                   | Communication                        |
| :----------- | :--------------- | :---------------------------- | :--------------------------------------------- | :----------------------------------- |
| **Engine A** | **Orchestrator** | Python 3.11, FastAPI          | RiskManager, SecretManager, Firestore          | Calls B (Signal) & C (Execution).    |
| **Engine B** | **AI Logic**     | XGBoost, LightGBM, Gemini 2.5 | **GCS (Models)**, **Vertex AI**, SecretManager | Receives calls from A.               |
| **Engine C** | **Ordering**     | Python 3.11, DhanHQ SDK       | **Firestore (Creds)**, SecretManager           | Receives calls from A. Calls Broker. |

### 2.2 Data Layer

| Resource           | Role           | Usage in Code                                         | Status                         |
| :----------------- | :------------- | :---------------------------------------------------- | :----------------------------- |
| **Firestore**      | User State     | `user_credentials` collection (Dhan tokens).          | **Inaccessible (Permissions)** |
| **Secret Manager** | System Secrets | `dhan-client-id`, `dhan-access-token` (System/Admin). | **Empty / Missing**            |
| **Cloud Storage**  | ML Artifacts   | Bucket: `[PROJECT_ID]-ml-models`.                     | **Missing / Empty**            |

### 2.3 CI/CD & Infrastructure

| Component       | Findings                                                                                                                                        |
| :-------------- | :---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Cloud Build** | `cloudbuild-deploy.yaml` pushes images to `asia-south1-docker.pkg.dev/project-841b7f97-5ee3-4fbe-920/...`. **this is the WRONG artifact registry.** |
| **IAM**         | Default Compute Service Account used. Likely missing `Secret Manager Accessor` and `Storage Object Viewer`.                                     |

---

## 3. Detailed Gaps & Fixes

### 3.1 ❌ Configuration Drift (URLs & Project IDs)

**Symptom:** Code defaults `ENGINE_B_URL` to `https://engine-b-429140669077...`.
**Root Cause:** Files `backend/engine-a/src/main.py` and `backend/engine-c/src/main.py` have hardcoded fallback URLs for the old project.
**Fix:**

1.  **Deploy Time:** Set `ENGINE_B_URL` and `ENGINE_C_URL` as specific **env vars** in Cloud Run override during deployment.
2.  **Code:** Update default fallbacks to `os.getenv("ENGINE_B_URL", "http://localhost:8080")` (fail safe) or the new project URL.

### 3.2 ❌ Engine B Startup Crash

**Symptom:** Container failed to start.
**Root Cause:** `MLModelStore` in `shared/google_integrations/cloud_storage.py` attempts to list blobs from `[PROJECT_ID]-ml-models` on init. If bucket is active but permissions missing, or SDK fails, it might not be catching the exception cleanly enough to stay alive, or `uvicorn` startup times out.
**Fix:**

1.  Create Bucket: `gs://galvanic-pulsar-482815-h0-ml-models`.
2.  Upload a placeholder "dummy" model or ensure the code handles an empty bucket gracefully without crashing.
3.  Ensure Service Account has `Storage Object Admin`.

### 3.3 ❌ Missing Secrets

**Symptom:** `get_secret` calls will return empty strings.
**Root Cause:** Secrets have not been created in the new project.
**Fix:** Run `gcloud secrets create` for:

- `dhan-client-id`
- `dhan-access-token`
- `dhan-api-secret`
- `openai-api-key` (if used by any fallback).

### 3.4 ❌ CI/CD Registry Mismatch

**Symptom:** Builds push to `project-841b7f97-5ee3-4fbe-920`.
**Fix:** Update `cloudbuild-deploy.yaml` to use project ID `galvanic-pulsar-482815-h0`.

---

## 4. Capability & Limitations Matrix

| Feature                   | Status         | Blocker                                                                                   |
| :------------------------ | :------------- | :---------------------------------------------------------------------------------------- |
| **User Login (Frontend)** | ⚠️ Risky       | Relies on Firebase Auth + Firestore. Firestore rules/permissions for new project unclear. |
| **Dhan Binding**          | ❌ **Broken**  | Firestore write for user creds likely fails (IAM).                                        |
| **AI Signal (Engine B)**  | ❌ **Offline** | Service crashing.                                                                         |
| **Trade Execution**       | ❌ **Blocked** | No Dhan secrets = Auth failure.                                                           |
| **Market Data**           | ❌ **Blocked** | No Secrets = No API access.                                                               |

---

## 5. Step-by-Step Runbook (Fix Plan)

### Phase 1: Stabilization (The "Plumbing" Fix)

1.  **Create Secrets:**
    ```powershell
    # Powershell / Terminal
    gcloud secrets create dhan-client-id --data-file=./dhan_id.txt
    gcloud secrets create dhan-access-token --data-file=./dhan_token.txt
    gcloud secrets create dhan-api-secret --data-file=./dhan_secret.txt
    ```
2.  **Create Storage Buckets:**
    ```powershell
    gsutil mb -l asia-south1 gs://galvanic-pulsar-482815-h0-ml-models
    gsutil mb -l asia-south1 gs://galvanic-pulsar-482815-h0-trading-history
    ```
3.  **Fix IAM:**
    Grant `roles/secretmanager.secretAccessor`, `roles/datastore.user`, and `roles/storage.objectAdmin` to the Cloud Run service account (`228557716858-compute@developer.gserviceaccount.com`).
4.  **Update Deployment Config:**
    Edit `backend/cloudbuild-deploy.yaml`: Replace `project-841b7f97-5ee3-4fbe-920` with `galvanic-pulsar-482815-h0`.

### Phase 2: Resilience (The "Code" Fix)

1.  **Redeploy Engine B:**
    Trigger a manual build/deploy of Engine B. Watch logs.
2.  **Redeploy Engine A with Env Vars:**
    ```powershell
    gcloud run deploy engine-a --image ... --set-env-vars ENGINE_B_URL=https://engine-b-...,ENGINE_C_URL=https://engine-c-...
    ```
3.  **Verify Inter-Service:**
    Call `https://engine-a-.../health` and check `google_integrations` status.

### Phase 3: Validation

1.  **Frontend Test:** Log in, go to Settings, enter "Dhan Client ID" (dummy if needed).
2.  **Check Firestore:** Verify document created in `dhan_credentials/{uid}`.
3.  **Check Engine Logs:** Ensure `engine-c` sees the new credentials.

**Recommendation:** Proceed immediately with Phase 1.
