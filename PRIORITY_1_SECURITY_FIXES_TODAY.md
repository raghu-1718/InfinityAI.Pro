# 🚀 IMMEDIATE ACTIONS - PRIORITY 1 SECURITY FIXES

**Status**: ACTION REQUIRED TODAY
**Project**: galvanic-pulsar-482815-h0
**Estimated Time**: 4-6 hours

---

## FIX #1: Unify Firebase Configuration (1 hour)

### Current State: TWO DIFFERENT API KEYS

**File 1**: `frontend/web-app/next.config.ts`

```typescript
NEXT_PUBLIC_FIREBASE_API_KEY: "AIzaSyAnEUI1GqUnAL8h3GFQMmnpBXv7nh6tu3k",
```

**File 2**: `frontend/web-app/src/lib/firebase/config.ts`

```typescript
apiKey: "AIzaSyD_y3lIPm7bTEXy3Uy4deGTnZPpjr2A8B8",
```

### ✅ ACTION: Choose One Source of Truth

The correct API key is in `firebase/config.ts` (this file is used by actual Firebase SDK init).

**Step 1**: Update `next.config.ts` to match

```bash
cd c:\workspace\InfinityAI.Pro
```

**Step 2**: Replace in next.config.ts (lines 29-46)
OLD:

```typescript
env: {
  NEXT_PUBLIC_ENGINE_A_URL: "https://engine-a-228557716858.us-central1.run.app",
  NEXT_PUBLIC_ENGINE_B_URL: "https://engine-b-228557716858.us-central1.run.app",
  NEXT_PUBLIC_ENGINE_C_URL: "https://engine-c-228557716858.us-central1.run.app",
  NEXT_PUBLIC_FIREBASE_API_KEY: "AIzaSyAnEUI1GqUnAL8h3GFQMmnpBXv7nh6tu3k",  // ❌ WRONG
  NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: "galvanic-pulsar-482815-h0.firebaseapp.com",
  NEXT_PUBLIC_FIREBASE_PROJECT_ID: "galvanic-pulsar-482815-h0",
  NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET: "galvanic-pulsar-482815-h0.firebasestorage.app",
  NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: "429140669077",
  NEXT_PUBLIC_FIREBASE_APP_ID: "1:429140669077:web:e071ad7a136c74a3ea219c",
  NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID: "G-NY37ZKLPBX",
},
```

NEW:

```typescript
env: {
  // Use Firebase Hosting rewrites instead of hardcoded URLs
  NEXT_PUBLIC_FIREBASE_API_KEY: "AIzaSyD_y3lIPm7bTEXy3Uy4deGTnZPpjr2A8B8",  // ✅ CORRECT
  NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: "galvanic-pulsar-482815-h0.firebaseapp.com",
  NEXT_PUBLIC_FIREBASE_PROJECT_ID: "galvanic-pulsar-482815-h0",
  NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET: "galvanic-pulsar-482815-h0.firebasestorage.app",
  NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: "228557716858",  // ✅ CORRECTED
  NEXT_PUBLIC_FIREBASE_APP_ID: "1:228557716858:web:d3ae59af1254d4b893aac3",  // ✅ CORRECTED
  NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID: "G-17NHEMLXDV",  // ✅ CORRECTED
},
```

**Step 3**: Verify

```bash
# Build frontend to catch any issues early
cd frontend/web-app
npm run build

# Should complete without errors
```

**Verification**:

- [ ] next.config.ts has matching API key from firebase/config.ts
- [ ] Firebase auth login works
- [ ] No console errors about mismatched configs

---

## FIX #2: Remove Localhost from CORS (2 hours)

### Current Issue: DEV ORIGINS IN PRODUCTION

**Files with issue**:

- `backend/engine-a/src/main.py` (lines 136-138)
- `backend/engine-b/src/main.py` (lines 323-325)
- `backend/engine-c/src/main.py` (lines 377-378)

### ✅ ACTION: Environment-Gate CORS Origins

Create new file: `backend/shared/cors_config.py`

```python
"""CORS configuration with environment-gating for production safety."""

import os
from typing import List

def get_allowed_origins() -> List[str]:
    """
    Get allowed CORS origins based on environment.

    DEVELOPMENT: Allows localhost for local testing
    PRODUCTION: Only allows whitelisted domains
    """

    environment = os.getenv("ENVIRONMENT", "production").lower()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "galvanic-pulsar-482815-h0")

    # Base production origins
    production_origins = [
        "https://infinityai.pro",
        "https://www.infinityai.pro",
        "https://app.infinityai.pro",
        f"https://{project_id}.web.app",
        f"https://{project_id}.firebaseapp.com",
    ]

    # Development-only origins (never in production)
    development_only = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ]

    if environment == "development":
        return production_origins + development_only
    else:
        # NEVER include dev origins in production
        return production_origins

# Export for use in engines
ALLOWED_ORIGINS = get_allowed_origins()
```

### Update Each Engine

#### Engine A: `backend/engine-a/src/main.py`

OLD (lines 130-147):

```python
# CORS allowed origins for production
ALLOWED_ORIGINS = [
    "https://infinityai.pro",
    "https://www.infinityai.pro",
    "https://app.infinityai.pro",
    "https://engine-a.infinityai.pro",
    "https://engine-b.infinityai.pro",
    "https://engine-c.infinityai.pro",
    f"https://{PROJECT_ID}.web.app",
    f"https://{PROJECT_ID}.firebaseapp.com",
    "http://localhost:3000",  # ❌ REMOVE
    "http://localhost:8000",  # ❌ REMOVE
    "http://127.0.0.1:3000",  # ❌ REMOVE
]
```

NEW:

```python
# Import from shared config
from src.shared.cors_config import ALLOWED_ORIGINS
# or:
# from backend.shared.cors_config import ALLOWED_ORIGINS
```

#### Engine B & C: Similar change

### Deploy with Environment Flag

```bash
# Verify current deployment
gcloud run services list --region=us-central1 --project=galvanic-pulsar-482815-h0

# Deploy all three engines with production environment
gcloud run deploy engine-a \
  --set-env-vars="ENVIRONMENT=production" \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --image=gcr.io/galvanic-pulsar-482815-h0/engine-a:latest

gcloud run deploy engine-b \
  --set-env-vars="ENVIRONMENT=production" \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --image=gcr.io/galvanic-pulsar-482815-h0/engine-b:latest

gcloud run deploy engine-c \
  --set-env-vars="ENVIRONMENT=production" \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --image=gcr.io/galvanic-pulsar-482815-h0/engine-c:latest

# Verify deployment
for service in engine-a engine-b engine-c; do
  echo "=== $service ==="
  gcloud run services describe $service --region=us-central1 --project=galvanic-pulsar-482815-h0 \
    | grep -A5 "Environment variables"
done
```

**Verification**:

- [ ] CORS request from localhost rejected in production (`curl -H "Origin: http://localhost:3000" ...` returns 403)
- [ ] CORS request from infinityai.pro accepted (returns 200)
- [ ] All three engines report `ENVIRONMENT=production` in env vars

---

## FIX #3: Encrypt Dhan Credentials in Firestore (3 hours)

### Current Issue: PLAINTEXT TOKENS STORED

**Problem**:

```firestore
dhan_credentials/{userId} {
  "access_token": "eyJ0eXAi...",  // Plaintext - SECURITY RISK
  "client_id": "1234567890"
}
```

### ✅ ACTION: Use Cloud KMS for Encryption

#### Step 1: Create Cloud KMS Key (if not exists)

```bash
# Create key ring
gcloud kms keyrings create infinityai \
  --location=us-central1 \
  --project=galvanic-pulsar-482815-h0

# Create crypto key
gcloud kms keys create credentials \
  --location=us-central1 \
  --keyring=infinityai \
  --purpose=encryption \
  --project=galvanic-pulsar-482815-h0

# Grant Cloud Run service account permission to decrypt
SERVICE_ACCOUNT="$(gcloud iam service-accounts list \
  --filter="email:*-compute@developer.gserviceaccount.com" \
  --format="value(email)" \
  --project=galvanic-pulsar-482815-h0)"

gcloud kms keys add-iam-policy-binding credentials \
  --location=us-central1 \
  --keyring=infinityai \
  --member=serviceAccount:$SERVICE_ACCOUNT \
  --role=roles/cloudkms.cryptoKeyEncrypterDecrypter \
  --project=galvanic-pulsar-482815-h0
```

#### Step 2: Update Cloud Function - Store Credentials

**File**: `frontend/functions/src/storeCredentials.ts`

```typescript
import { CloudKMS } from "@google-cloud/kms";

const kms = new CloudKMS();

interface EncryptedCredentials {
  access_token: string; // Encrypted (base64)
  client_id: string; // Plaintext (OK - not secret)
  encrypted: true;
  encrypted_at: FirebaseFirestore.Timestamp;
  encryption_key: string; // Reference to KMS key used
}

async function encryptCredential(plaintext: string): Promise<string> {
  const keyName = `projects/galvanic-pulsar-482815-h0/locations/us-central1/keyRings/infinityai/cryptoKeys/credentials`;

  const response = await kms.encrypt({
    name: keyName,
    plaintext: Buffer.from(plaintext).toString("base64"),
  });

  return response.ciphertext || "";
}

export const submitDhanCredentialsV2 = onCall(
  {
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 60,
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in");
    }

    const uid = request.auth.uid;
    const { clientId, apiKey, apiSecret, accessToken } = request.data;

    // Validate
    if (!clientId || !accessToken) {
      throw new HttpsError(
        "invalid-argument",
        "Missing clientId or accessToken",
      );
    }

    try {
      // Encrypt the access token
      const encryptedToken = await encryptCredential(accessToken);

      const db = getFirestore();
      const timestamp = admin.firestore.Timestamp.now();

      // Store encrypted credentials
      await db
        .collection("dhan_credentials")
        .doc(uid)
        .set(
          {
            client_id: clientId, // Plaintext OK
            access_token: encryptedToken, // Encrypted ✅
            api_key: apiKey, // Plaintext OK (though should also encrypt)
            api_secret: apiSecret, // Encrypted recommended
            encrypted: true, // Marker for decryption
            encrypted_at: timestamp,
            encryption_key:
              "projects/galvanic-pulsar-482815-h0/locations/us-central1/keyRings/infinityai/cryptoKeys/credentials",
          } as EncryptedCredentials,
          { merge: true },
        );

      // Also store plaintext client_id in user_credentials for quick lookup
      await db.collection("user_credentials").doc(uid).set(
        {
          dhan_client_id: clientId,
          has_credentials: true,
          updated_at: timestamp,
        },
        { merge: true },
      );

      return {
        success: true,
        message: "Credentials encrypted and stored successfully",
      };
    } catch (error) {
      console.error("Error storing encrypted credentials:", error);
      throw new HttpsError("internal", "Failed to store credentials");
    }
  },
);
```

#### Step 3: Update Engine C - Retrieve & Decrypt

**File**: `backend/engine-c/src/user_credentials.py`

```python
from google.cloud import kms
import base64

class UserCredentialsManager:
    def __init__(self):
        self.kms_client = kms.KeyManagementServiceClient()
        self.key_name = "projects/galvanic-pulsar-482815-h0/locations/us-central1/keyRings/infinityai/cryptoKeys/credentials"

    async def decrypt_credential(self, encrypted_data: str) -> str:
        """Decrypt a credential using Cloud KMS."""
        try:
            response = self.kms_client.decrypt(
                request={
                    "name": self.key_name,
                    "ciphertext": encrypted_data.encode(),
                }
            )
            plaintext = base64.b64decode(response.plaintext).decode('utf-8')
            return plaintext
        except Exception as e:
            logger.error(f"Failed to decrypt credential: {e}")
            raise ValueError("Could not decrypt credentials")

    async def get_dhan_credentials(self, user_id: str):
        """Retrieve and decrypt user's Dhan credentials."""
        try:
            cred_doc = await self.db.collection('dhan_credentials').document(user_id).get()

            if not cred_doc.exists:
                return None

            data = cred_doc.to_dict()

            # If encrypted, decrypt the access token
            if data.get('encrypted'):
                data['access_token'] = await self.decrypt_credential(data['access_token'])
                if data.get('api_secret'):
                    data['api_secret'] = await self.decrypt_credential(data['api_secret'])

            return {
                'client_id': data['client_id'],
                'access_token': data['access_token'],
                'api_key': data.get('api_key', ''),
                'api_secret': data.get('api_secret', ''),
            }
        except Exception as e:
            logger.error(f"Error retrieving credentials for {user_id}: {e}")
            return None
```

#### Step 4: Update Engine A & Engine B (if they read credentials)

Same decrypt logic should be used.

#### Step 5: Deploy

```bash
# Redeploy Cloud Functions with encryption support
firebase deploy --only functions:submitDhanCredentialsV2 \
  --project=galvanic-pulsar-482815-h0

# Redeploy Engine C with decryption support
gcloud run deploy engine-c \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0
```

**Verification**:

- [ ] New credentials stored with `encrypted: true` flag
- [ ] Firestore doc shows encrypted token (not readable)
- [ ] Engine C can decrypt and place orders successfully
- [ ] Try to read encrypted token directly → get garbage (not plaintext)

---

## FIX #4: Update .env File (30 minutes)

### Current Issue: POINTS TO WRONG PROJECT

OLD `.env`:

```dotenv
GOOGLE_CLOUD_PROJECT=infinity-ai-pro-dev
NODE_ENV=development
LOG_LEVEL=DEBUG
```

### ✅ ACTION: Update to correct project

```bash
cd c:\workspace\InfinityAI.Pro

# Backup old
copy .env .env.backup

# Create correct .env
cat > .env <<'EOF'
# ================================================================
# InfinityAI.Pro - PRODUCTION Environment Variables
# ================================================================
# Project: I Am Infinity (galvanic-pulsar-482815-h0)
# Environment: PRODUCTION
# Last Updated: 2026-01-19
#
# CRITICAL: Never commit actual secrets to git
# Use GCP Secret Manager for sensitive values
# ================================================================

# GCP & Firebase (REQUIRED)
GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0
FIREBASE_PROJECT_ID=galvanic-pulsar-482815-h0
GCP_REGION=us-central1
ENVIRONMENT=production

# Node Environment
NODE_ENV=production
LOG_LEVEL=INFO

# Firestore
FIRESTORE_DATABASE=default

# Cloud KMS (for credential encryption)
KMS_KEY_NAME=projects/galvanic-pulsar-482815-h0/locations/us-central1/keyRings/infinityai/cryptoKeys/credentials

# Trading Settings
TRADING_MODE=paper
SESSION_TIMEOUT_MINUTES=60
MIN_CONFIDENCE_THRESHOLD=0.75
MAX_RISK_PER_TRADE=0.02
ENABLE_AUTO_TRADING=false

# Debug (PRODUCTION: false)
DEBUG=false
ENABLE_LOCALHOST_CORS=false
EOF

# Verify
cat .env
```

**Verification**:

- [ ] `gcloud config get-value project` returns `galvanic-pulsar-482815-h0`
- [ ] `.env` contains correct project ID
- [ ] `ENVIRONMENT=production`

---

## TESTING AFTER ALL FIXES

```bash
# 1. Verify Firebase config
cd frontend/web-app
npm run build 2>&1 | head -20

# 2. Test CORS from localhost (should fail in production)
curl -v \
  -H "Origin: http://localhost:3000" \
  https://engine-a-228557716858.us-central1.run.app/health

# 3. Test CORS from production domain (should succeed)
curl -v \
  -H "Origin: https://galvanic-pulsar-482815-h0.web.app" \
  https://engine-a-228557716858.us-central1.run.app/health

# 4. Test credential encryption
firebase functions:config:set secrets.encryption_key="$(gcloud secrets versions access latest --secret=encryption-key --project=galvanic-pulsar-482815-h0)"

# 5. End-to-end: Store credentials and place order
# (requires manual testing in UI)

# 6. Check logs for any errors
gcloud logging read "severity=ERROR" \
  --limit=10 \
  --project=galvanic-pulsar-482815-h0 \
  --format=json | jq '.[] | {textPayload, timestamp}'
```

---

## ROLLBACK PLAN (if issues occur)

```bash
# Revert Firebase config
git checkout frontend/web-app/next.config.ts

# Revert CORS changes
git checkout backend/engine-a/src/main.py
git checkout backend/engine-b/src/main.py
git checkout backend/engine-c/src/main.py

# Revert .env
cp .env.backup .env

# Redeploy old versions
gcloud run deploy engine-a --region=us-central1 --project=galvanic-pulsar-482815-h0 --image=gcr.io/galvanic-pulsar-482815-h0/engine-a:previous

# Verify health
curl https://engine-a-228557716858.us-central1.run.app/health
```

---

## CHECKLIST

- [ ] Fix #1: Firebase config unified (1h)
- [ ] Fix #2: CORS environment-gated (2h)
- [ ] Fix #3: Credentials encrypted (3h)
- [ ] Fix #4: .env updated (30m)
- [ ] All fixes tested
- [ ] CORS test: localhost rejected
- [ ] CORS test: production allowed
- [ ] Credential encryption verified
- [ ] End-to-end trading test passes
- [ ] Commit to git with message: "🔒 [URGENT] Security Fixes: CORS, Credentials, Config"

**Estimated Total Time**: 6-7 hours
**Target Completion**: Today EOD

---

**Status**: Ready to implement
**Risk Level**: Low (only config/security, no logic changes)
**Rollback**: 10 minutes (git revert)
