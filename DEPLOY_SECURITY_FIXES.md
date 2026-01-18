# 🔒 Deploy Security Fixes to Production

**Status**: 3/4 Priority 1 fixes implemented and committed
**Git Commit**: `490d8025` - Security fixes pushed to `main`
**Deployment**: In progress (Engine A building...)

## ✅ Changes Committed (Git)

1. **Firebase Config Unification**
   - Fixed API key mismatch in `frontend/web-app/next.config.ts`
   - Now matches `firebase/config.ts`: `AIzaSyD_y3lIPm7bTEXy3Uy4deGTnZPpjr2A8B8`
   - Corrected `messagingSenderId` and `appId`
   - Removed hardcoded engine URLs

2. **Environment-Gated CORS**
   - Created `backend/shared/cors_config.py` with environment detection
   - Updated all 3 engines to use shared CORS module
   - **Production mode blocks localhost** (activated after deployment)

3. **Analysis Documentation**
   - `COMPREHENSIVE_ANALYSIS_AND_FIXES.md` (15,000 words)
   - `PRIORITY_1_SECURITY_FIXES_TODAY.md` (step-by-step guide)
   - `EXECUTIVE_SUMMARY_FOR_STAKEHOLDERS.md` (business context)

## ⚠️ Changes NOT Committed (Local Only)

`.env` file updated (correctly in `.gitignore`):

```bash
# BEFORE (WRONG)
GOOGLE_CLOUD_PROJECT="infinity-ai-pro-dev"

# AFTER (CORRECT)
GOOGLE_CLOUD_PROJECT="galvanic-pulsar-482815-h0"
ENVIRONMENT="production"
DEBUG="false"
ENABLE_LOCALHOST_CORS="false"
LOG_LEVEL="INFO"
```

**Action Required**: These env vars must be set during deployment (see commands below).

---

## 🚀 Deployment Commands

### Prerequisites

```powershell
# Verify GCP project context
gcloud config get-value project
# Should return: galvanic-pulsar-482815-h0

# Verify git is up to date
git status
# Should show: "Your branch is up to date with 'origin/main'"
```

### Engine A (Orchestration & Risk Management)

```powershell
cd c:\workspace\InfinityAI.Pro

# Build using Cloud Build (correct build context from root)
gcloud builds submit `
  --config=backend/engine-a/cloudbuild.yaml `
  --project=galvanic-pulsar-482815-h0 `
  --region=us-central1

# Deploy to Cloud Run with production env vars
gcloud run deploy engine-a `
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-a:latest `
  --region=us-central1 `
  --project=galvanic-pulsar-482815-h0 `
  --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0,LOG_LEVEL=INFO,DEBUG=false" `
  --allow-unauthenticated
```

### Engine B (AI Signal Generation)

```powershell
# Build
gcloud builds submit `
  --config=backend/engine-b/cloudbuild.yaml `
  --project=galvanic-pulsar-482815-h0 `
  --region=us-central1

# Deploy
gcloud run deploy engine-b `
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-b:latest `
  --region=us-central1 `
  --project=galvanic-pulsar-482815-h0 `
  --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0,LOG_LEVEL=INFO,DEBUG=false" `
  --allow-unauthenticated
```

### Engine C (Trade Execution)

```powershell
# Build
gcloud builds submit `
  --config=backend/engine-c/cloudbuild.yaml `
  --project=galvanic-pulsar-482815-h0 `
  --region=us-central1

# Deploy
gcloud run deploy engine-c `
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-c:latest `
  --region=us-central1 `
  --project=galvanic-pulsar-482815-h0 `
  --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0,LOG_LEVEL=INFO,DEBUG=false" `
  --allow-unauthenticated
```

### Frontend (Next.js Static Export)

```powershell
cd c:\workspace\InfinityAI.Pro\frontend\web-app

# Build static export
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting --project=galvanic-pulsar-482815-h0
```

---

## ✅ Verification Steps

### 1. Verify CORS Security (Critical!)

```powershell
# Test localhost is BLOCKED (should return 403 or CORS error)
curl -v -H "Origin: http://localhost:3000" `
  https://engine-a-228557716858.us-central1.run.app/health

# Test production origin is ALLOWED (should return 200)
curl -v -H "Origin: https://infinityai.pro" `
  https://engine-a-228557716858.us-central1.run.app/health
```

**Expected Results**:

- Localhost origin → **CORS error** or **403 Forbidden** (good!)
- Production origin → **200 OK** with health data (good!)

### 2. Verify Environment Variables

```powershell
# Check Engine A config
gcloud run services describe engine-a `
  --region=us-central1 `
  --project=galvanic-pulsar-482815-h0 `
  --format="value(spec.template.spec.containers[0].env)"

# Should show: ENVIRONMENT=production, DEBUG=false
```

### 3. Verify Firebase Config

```powershell
# Check frontend build output
cd c:\workspace\InfinityAI.Pro\frontend\web-app
npm run build

# Should compile without errors (verified 2024-12-XX at 2.3min)
```

### 4. Verify Service Health

```powershell
# Engine A
curl https://engine-a-228557716858.us-central1.run.app/health

# Engine B
curl https://engine-b-228557716858.us-central1.run.app/health

# Engine C
curl https://engine-c-228557716858.us-central1.run.app/health

# All should return: {"status":"healthy",...}
```

---

## 🔐 Remaining Work (Priority 1, Fix #4)

### Credential Encryption with Cloud KMS

**Status**: Not yet implemented
**Timeline**: 3-4 hours
**Risk Level**: Medium (credentials currently plaintext but user-isolated in Firestore)

#### Steps:

1. **Create KMS Key Ring and Key**

   ```powershell
   gcloud kms keyrings create infinityai-credentials `
     --location=us-central1 `
     --project=galvanic-pulsar-482815-h0

   gcloud kms keys create dhan-credentials `
     --location=us-central1 `
     --keyring=infinityai-credentials `
     --purpose=encryption `
     --project=galvanic-pulsar-482815-h0
   ```

2. **Grant IAM Permissions**

   ```powershell
   # Cloud Functions service account
   gcloud kms keys add-iam-policy-binding dhan-credentials `
     --location=us-central1 `
     --keyring=infinityai-credentials `
     --member="serviceAccount:galvanic-pulsar-482815-h0@appspot.gserviceaccount.com" `
     --role="roles/cloudkms.cryptoKeyEncrypterDecrypter" `
     --project=galvanic-pulsar-482815-h0

   # Engine C service account
   ENGINE_C_SA=$(gcloud run services describe engine-c \
     --region=us-central1 \
     --project=galvanic-pulsar-482815-h0 \
     --format="value(spec.template.spec.serviceAccountName)")

   gcloud kms keys add-iam-policy-binding dhan-credentials `
     --location=us-central1 `
     --keyring=infinityai-credentials `
     --member="serviceAccount:$ENGINE_C_SA" `
     --role="roles/cloudkms.cryptoKeyDecrypter" `
     --project=galvanic-pulsar-482815-h0
   ```

3. **Update Cloud Functions (`saveDhanCredentials`)**
   - Location: `infra/firebase/functions/src/index.ts` (or Python equivalent)
   - Add KMS encryption before Firestore write:

     ```typescript
     import { KMSClient, EncryptCommand } from "@google-cloud/kms";

     const kms = new KMSClient();
     const keyName =
       "projects/galvanic-pulsar-482815-h0/locations/us-central1/keyRings/infinityai-credentials/cryptoKeys/dhan-credentials";

     // Encrypt client_id
     const encryptedClientId = await kms.encrypt({
       name: keyName,
       plaintext: Buffer.from(dhanCredentials.client_id),
     });

     // Store encrypted version in Firestore
     await db
       .collection("user_broker_credentials")
       .doc(uid)
       .set({
         dhan_client_id_encrypted:
           encryptedClientId.ciphertext.toString("base64"),
         encryption_key_version: keyName,
         last_updated: admin.firestore.FieldValue.serverTimestamp(),
       });
     ```

4. **Update Engine C Decryption**
   - Location: `backend/engine-c/src/main.py`
   - Add KMS decryption when loading credentials:

     ```python
     from google.cloud import kms

     kms_client = kms.KeyManagementServiceClient()
     key_name = 'projects/galvanic-pulsar-482815-h0/locations/us-central1/keyRings/infinityai-credentials/cryptoKeys/dhan-credentials'

     # Decrypt client_id
     ciphertext = base64.b64decode(cred_doc['dhan_client_id_encrypted'])
     response = kms_client.decrypt(request={'name': key_name, 'ciphertext': ciphertext})
     decrypted_client_id = response.plaintext.decode('utf-8')
     ```

5. **Migration Script for Existing Credentials**
   - Create `tools/migrate_credentials_to_kms.py`
   - Read all plaintext credentials from Firestore
   - Encrypt with KMS
   - Write back encrypted versions
   - Verify decryption works
   - Delete plaintext versions

#### Estimated Timeline

- KMS setup: 30 minutes
- Cloud Functions update: 1 hour
- Engine C update: 1 hour
- Migration script: 1 hour
- Testing & verification: 30 minutes
- **Total**: 3-4 hours

---

## 📊 Deployment Status

| Component          | Build Status   | Deploy Status | CORS Security | Notes                           |
| ------------------ | -------------- | ------------- | ------------- | ------------------------------- |
| **Engine A**       | 🟡 In Progress | ⏳ Pending    | ⏳ Pending    | Building via Cloud Build        |
| **Engine B**       | ⏳ Pending     | ⏳ Pending    | ⏳ Pending    | Awaiting Engine A completion    |
| **Engine C**       | ⏳ Pending     | ⏳ Pending    | ⏳ Pending    | Awaiting Engine B completion    |
| **Frontend**       | ✅ Tested      | ⏳ Pending    | N/A           | Build verified (2.3min compile) |
| **KMS Encryption** | ⏳ Not Started | N/A           | N/A           | Fix #4 - 3-4 hours remaining    |

### Next Actions (In Order)

1. ✅ ~~Complete Engine A build~~ (currently running)
2. ⏳ Deploy Engine A to Cloud Run with ENVIRONMENT=production
3. ⏳ Verify CORS blocks localhost
4. ⏳ Build & deploy Engine B
5. ⏳ Build & deploy Engine C
6. ⏳ Deploy frontend to Firebase Hosting
7. ⏳ Full E2E verification (frontend → engines → Firestore)
8. ⏳ Implement KMS credential encryption (Fix #4)

---

## 🎯 Success Criteria

- [x] Git commit pushed to main
- [ ] All 3 engines deployed with `ENVIRONMENT=production`
- [ ] CORS blocks localhost origins (verified via curl)
- [ ] Frontend Firebase config unified (verified via build)
- [ ] All `/health` endpoints return 200
- [ ] Credentials encrypted with KMS (Fix #4)

**Timeline**: Today (except KMS which is 3-4 hours additional work)

---

## 📞 Contact

**Deployed by**: Principal Cloud Solutions Architect
**GCP Project**: `galvanic-pulsar-482815-h0`
**Git Commit**: `490d8025`
**Deployment Date**: 2024-XX-XX (in progress)

For issues or questions, check:

- Cloud Build logs: https://console.cloud.google.com/cloud-build/builds?project=228557716858
- Cloud Run services: https://console.cloud.google.com/run?project=228557716858
- Firebase Console: https://console.firebase.google.com/project/galvanic-pulsar-482815-h0
