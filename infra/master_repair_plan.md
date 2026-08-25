# InfinityAI.Pro - Master Repair Plan & Deployment Guide

## 1. System & Security Overview

**Architecture:**

- **Frontend**: Next.js (Firebase Hosting + Auth). Calls Cloud Run services via direct URL or Rewrites.
- **Backend**:
  - `engine-a` (Orchestrator)
  - `engine-b` (AI Signals - Requires ML Models & Secrets)
  - `engine-c` (Execution - Requires Dhan Secrets)
- **Secrets Management**:
  - **User Credentials**: Stored in Firestore (`dhan_credentials/{uid}`), encrypted via Firebase Function/App Logic.
  - **System Credentials** (House Account / Startup Checks): Stored in Google Secret Manager and injected as Environment Variables to Engine B/C.

## 2. Infrastructure Setup (Command Pack)

**Step 1: Run the Setup Script (PowerShell)**
This script creates the secrets (placeholders), buckets, and IAM roles.

```powershell
./infra/setup_secrets_iam.ps1
```

**Step 2: Update Real Secret Values (REQUIRED)**
You must manually update these values in Google Cloud Console or via CLI:

```powershell
# Example: Updating Dhan Client ID
echo "YOUR_REAL_CLIENT_ID" | gcloud secrets versions add dhan-client-id --data-file=-

# Secrets to Update:
# - dhan-client-id
# - dhan-access-token
# - dhan-api-secret (Optional but recommended)
# - encryption-key (For Firebase Functions)
# - openai-api-key (If used)
```

## 3. Code & Config Patches

**Status: ** ✅ Patches Applied in Previous Steps.

**Key Changes:**

1.  **`cloudbuild-deploy.yaml`**:
    - Updated to use new Artifact Registry `asia-south1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai`.
    - **Hardened**: Injected `DHAN_CLIENT_ID`, `DHAN_ACCESS_TOKEN` secrets as Env Vars for Engine B startup.
    - **Fixed**: Injected `GOOGLE_CLOUD_PROJECT` env var.
2.  **`engine-b/src/main.py`**:
    - Startup logic reinforced by Secret Injection.
3.  **`engine-a` / `engine-c`**:
    - Hardcoded URLs pointing to old projects removed.

## 4. Firebase & Frontend Wiring

**Firestore Rules (`firestore.rules`)**
_Secure user data access:_

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth.uid == userId;
    }
    match /dhan_credentials/{userId} {
      allow read, write: if request.auth.uid == userId;
    }
    match /dhan_orders/{orderId} {
      allow read, write: if request.auth.uid == resource.data.userId;
    }
  }
}
```

**Firebase Config (`firebase.json`)**
_Ensure rewrites point to Cloud Run:_

```json
{
  "hosting": {
    "public": "out",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "/api/dhan/**",
        "run": {
          "serviceId": "engine-c",
          "region": "asia-south1"
        }
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

## 5. Deployment Commands

**Phase 1: Deploy Backend (Cloud Run)**

```bash
cd backend
gcloud builds submit --config=cloudbuild-deploy.yaml .
```

**Phase 2: Deploy Frontend & Firebase**

```bash
# Build Next.js app first
cd frontend/web-app
npm install && npm run build
# Deploy to Firebase
firebase deploy --only hosting,firestore,functions
```

## 6. End-to-End Verification Checklist

| Area         | Check                                             | Pass Criteria                                            |
| :----------- | :------------------------------------------------ | :------------------------------------------------------- |
| **Secrets**  | `gcloud secrets versions list dhan-client-id`     | Returns at least `v1` (enabled)                          |
| **Backend**  | `gcloud run services list`                        | All 3 engines have Green Checkmarks                      |
| **Frontend** | Visit `https://galvanic-pulsar-482815-h0.web.app` | Loads Login Page                                         |
| **Flow**     | Login -> Settings -> Save Dhan Creds              | Toast "Credentials Saved", Firestore doc created         |
| **Trading**  | Dashboard -> Start Session                        | Engine A log: "Got Signal", Engine C log: "Order Placed" |

---

**Troubleshooting:**

- **Engine B Crash**: Check `gcloud logging read "resource.type=cloud_run_revision"` for "Missing Env Var". Fix: Update Secret.
- **Frontend Error**: Check Browser Console + Network Tab. If 404, check `firebase.json` rewrites.
