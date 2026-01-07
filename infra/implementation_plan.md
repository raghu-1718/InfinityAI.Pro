# implementation_plan.md

# End-to-End Infrastructure Repair & Deployment Plan

## Goal

Fully repair, secure, and deploy the InfinityAI.Pro trading platform on the `galvanic-pulsar-482815-h0` project. This includes fixing "split-brain" drift, hardening secret management, and ensuring a successful end-to-end flow from User UI -> Firebase -> Cloud Run -> DhanHQ.

## User Review Required

> [!IMPORTANT]
> **Secret Values**: You must manually populate the secrets in Google Secret Manager after running the setup script. I will only create the _names_.
> **Dhan Credentials**:
>
> - **System/House Account**: Stored in Secret Manager (`dhan-client-id`, etc.) and used by Engine B/C.
> - **User Accounts**: Stored in Firestore (Encrypted) via Firebase Functions.

## Proposed Changes

### 1. Infrastructure (Scripted)

- **Secrets**: Create `dhan-client-id`, `dhan-access-token`, `dhan-api-secret`, `dhan-api-key`, `openai-api-key`, `encryption-key` (for Firebase Functions).
- **IAM**: extensive role grants for Cloud Run (Secret Accessor, Storage Object Admin, Datastore User) and Firebase Functions.
- **Storage**: Ensure `ml-models` and `trading-history` buckets exist and have `init.txt`.

### 2. Backend Code (Cloud Run)

#### `backend/cloudbuild-deploy.yaml`

- [MODIFY](file:///c:/workspace/InfinityAI.Pro/backend/cloudbuild-deploy.yaml)
  - **Hardening**: Use explicit `us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai` registry.
  - **Secret Injection**: Inject `DHAN_CLIENT_ID`, `DHAN_ACCESS_TOKEN` from Secret Manager as Environment Variables for Engine B/C startup compliance.
  - **Project ID**: Inject `GOOGLE_CLOUD_PROJECT` env var.

#### `backend/engine-b/src/main.py`

- [MODIFY](file:///c:/workspace/InfinityAI.Pro/backend/engine-b/src/main.py)
  - **Resilience**: Wrap `require_env` in a try-catch or soft-fail for local dev compatibility (optional, but good practice).
  - **Model Loading**: Ensure `ModelStorage` doesn't crash if bucket is empty (already checked, effectively fixed by `init.txt` existence, but will double check).

### 3. Frontend & Firebase

#### `frontend/functions/src/storeCredentials.ts`

- [MODIFY](file:///c:/workspace/InfinityAI.Pro/frontend/functions/src/storeCredentials.ts)
  - Ensure `ENCRYPTION_KEY` parameter is correctly defined and used.
  - Update GCP Project ID logic to be robust.

#### `firestore.rules`

- [NEW](file:///c:/workspace/InfinityAI.Pro/firestore.rules)
  - strict `allow read, write: if request.auth.uid == userId` for credential documents.

#### `firebase.json`

- [NEW](file:///c:/workspace/InfinityAI.Pro/firebase.json)
  - Ensure `rewrites` point to the correct function/Cloud Run service if needed.

## Verification Plan

### Automated Tests

- **Cloud Build**: Must pass green for all 3 engines.
- **Firebase Deploy**: Must succeed for Functions and Rules.

### Manual Verification

1.  **Secrets**: Run `gcloud secrets versions list` to confirm existence.
2.  **Engine Startup**: Check Cloud Run logs for "Startup complete" messages.
3.  **Frontend**:
    - Login to Web App.
    - Navigate to Settings.
    - Enter Dummy Credentials -> Save.
    - Check Firestore: Document should exist in `dhan_credentials/{uid}` and be encrypted.
    - Check Function Logs: Confirm successful execution.
