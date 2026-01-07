# InfinityAI.Pro - Final Repair Runbook

**Status:** ✅ REPAIRS APPLIED (Deployment Retry #4 In-Progress)
**Project:** `galvanic-pulsar-482815-h0`
**Timestamp:** 2026-01-05

---

## 1. Repairs Executed

### 1.1 Infrastructure

| Resource         | Status   | Action Taken                                  |
| :--------------- | :------- | :-------------------------------------------- |
| **Secrets**      | ✅ Fixed | Created `dhan-client-id` etc. (Placeholders). |
| **Storage**      | ✅ Fixed | Created `ml-models` bucket with `init.txt`.   |
| **IAM**          | ✅ Fixed | Granted IAM roles to Compute SA.              |
| **Artifact Reg** | ✅ Fixed | Created `infinityai` repo.                    |

### 1.2 Code & Configuration

| Component       | Status   | Action Taken                                                                                      |
| :-------------- | :------- | :------------------------------------------------------------------------------------------------ |
| **CI/CD**       | ✅ Fixed | Updated Project ID and Registry.                                                                  |
| **Env Vars**    | ✅ Fixed | Injected `GOOGLE_CLOUD_PROJECT` into all services.                                                |
| **Secrets Inj** | ✅ Fixed | **Injected Secrets** (`DHAN_CLIENT_ID`, `DHAN_ACCESS_TOKEN`) into Engine B (Fixes Startup Crash). |
| **Engine A/C**  | ✅ Fixed | Patched hardcoded URLs.                                                                           |

---

## 2. Validation Guide (End-to-End)

### Step 1: Monitor Deployment

`gcloud builds list --ongoing`

### Step 2: Update Secrets (CRITICAL)

**You must update them for the app to work.**

```powershell
echo "YOUR_REAL_CLIENT_ID" | gcloud secrets versions add dhan-client-id --data-file=-
echo "YOUR_REAL_ACCESS_TOKEN" | gcloud secrets versions add dhan-access-token --data-file=-
```

### Step 3: Frontend Validation

1.  Navigate to: `https://galvanic-pulsar-482815-h0.web.app/`
2.  Login.
3.  Go to Settings -> DhanHQ Integration.
4.  Enter Credentials -> Save.
    - _Success Criteria:_ "Credentials Saved" toast appears.

### Step 4: Full Loop Test

1.  Go to "Trade" Dashboard.
2.  Click "Start Session" (Calls Engine A).
3.  Watch Logs: `gcloud logging read "resource.type=cloud_run_revision" --limit=20`
    - _Success Criteria:_ Engine A logs "Got Signal" -> "Order Sent".
