# InfinityAI.Pro - Final Release Verification Guide

**Status:** 🚀 DEPLOYMENT IN PROGRESS
**Project ID:** `galvanic-pulsar-482815-h0`
**Region:** `asia-south1`

## 1. System Access Points

| Component    | URL                                                                                    |
| :----------- | :------------------------------------------------------------------------------------- |
| **Frontend** | [https://galvanic-pulsar-482815-h0.web.app](https://galvanic-pulsar-482815-h0.web.app) |
| **Engine A** | Use Cloud Console / Logs                                                               |
| **Engine B** | Internal Service                                                                       |
| **Engine C** | Internal Service                                                                       |

## 2. Infrastructure & Security Status

- **Secrets**: ✅ Hardened. `dhan-client-id`, `dhan-access-token`, `encryption-key` injected.
- **Backend**: ✅ Configured with correct Project ID and Secret Mapping.
- **Frontend**: ✅ Wired to new Firebase Project.

## 3. Final Deployment (Run Locally)

Because I cannot authenticate as 'you' for Firebase Hosting, please run this final command in your terminal:

```powershell
# 1. Login to Firebase (if not already)
firebase login

# 2. Deploy Frontend & Rules
cd frontend/web-app
firebase use galvanic-pulsar-482815-h0
firebase deploy --only hosting,firestore,functions
```

## 4. Step-by-Step Verification

### Step 1: Frontend Login

1.  Open the [Frontend URL](https://galvanic-pulsar-482815-h0.web.app).
2.  Log in (or Sign up).
3.  Go to **Settings**.

### Step 2: Connection Verification

1.  Check if "Dhan Connection" shows **Verified** (if using system creds).
2.  If not, enter your credentials:
    - **Client ID**: `1101302170`
    - **Access Token**: _(Your supplied long token)_
    - Click **Save Credentials**.
3.  **Expected Result**: A green "Credentials Verified" toast / status.

### Step 3: Trading Loop Test

1.  Navigate to **Trade / Dashboard**.
2.  Click **Start Session**.
3.  **Monitor Logs**:

    ```powershell
    # Check Engine A (Orchestrator)
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=engine-a" --limit=20

    # Check Engine C (Execution)
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=engine-c" --limit=20
    ```

4.  **Success Criteria**:
    - Engine A: "Session Started", "Risk Check Passed".
    - Engine C: "Order Placed" (or "Simulated Order" if in sandbox).

### Step 4: AI Signal Test (Engine B)

1.  Check logs for Engine B:
    ```powershell
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=engine-b" --limit=20
    ```
2.  **Success Criteria**: "Model loaded", "Signal generated".

## 4. Troubleshooting

- **"HTTP 500" on Save**: Check Firebase Function logs.
  `firebase functions:log`
- **"Engine B Crashed"**: Check if `dhan-client-id` secret matches what is expected.

---

**Deployment Verification Command:**
Run this to see if all services are green:

```powershell
gcloud run services list
```
