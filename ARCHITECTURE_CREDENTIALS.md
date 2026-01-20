# Credential Architecture - InfinityAI.Pro
## Multi-Tenant Per-User DhanHQ Credentials

**Last Updated:** January 20, 2026  
**Project:** galvanic-pulsar-482815-h0  
**Architecture:** Multi-tenant with per-user broker accounts

---

## 🎯 Architecture Decision

**Chosen Model:** Each user has their own DhanHQ broker account

**Rationale:**
- Supports multiple users trading independently
- Each user's funds/positions isolated to their broker account
- Regulatory compliance (trading in user's name, not platform)
- Clear audit trail per user
- No shared credential security risks

---

## 🔐 Credential Storage & Flow

### Storage: Firestore

**Collection:** `dhan_credentials`  
**Document Structure:**
```
dhan_credentials/{user_firebase_uid}
  ├─ user_id: string (Firebase UID)
  ├─ credentials: {
  │   ├─ client_id: string (plaintext)
  │   ├─ access_token: string (AES-256-GCM encrypted)
  │   ├─ api_key: string (AES-256-GCM encrypted)
  │   └─ api_secret: string (AES-256-GCM encrypted)
  │  }
  ├─ created_at: timestamp
  ├─ updated_at: timestamp
  ├─ is_active: boolean
  └─ connection_status: string
```

**Encryption:**
- **Algorithm:** AES-256-GCM
- **Format:** `iv:tag:ciphertext` (hex-encoded, colon-separated)
- **Key Source:** Environment variable `USER_CREDENTIALS_KEY` (32 bytes / 64 hex chars)
- **Key Fallback:** Secret Manager `user-credentials-key` → Project-derived key (insecure)

---

## 📊 Complete Flow

### 1. User Onboarding (Save Credentials)

```
┌─────────────────────────────────────────────────────────────────┐
│ USER ACTION                                                      │
│ 1. Log in to InfinityAI.Pro with Firebase Auth                  │
│ 2. Navigate to Settings → DhanHQ Integration                    │
│ 3. Input credentials from DhanHQ dashboard:                     │
│    - Client ID                                                  │
│    - Access Token                                               │
│    - API Key (optional - for market data APIs)                  │
│    - API Secret (optional)                                      │
│ 4. Click "Save Credentials"                                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: web-app/src/app/(dashboard)/settings/page.tsx         │
│ Line 116: POST /api/user/credentials                            │
│ Payload: {                                                      │
│   user_id: firebase_uid,                                        │
│   client_id: "...",                                             │
│   access_token: "...",                                          │
│   api_key: "...",                                               │
│   api_secret: "..."                                             │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: engine-c/src/main.py                                   │
│ Line 973: @app.post("/api/v1/user/credentials")                 │
│ Calls: UserCredentialsManager().save_user_credentials(...)      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: engine-c/src/user_credentials.py                       │
│ Line 135: save_user_credentials(...)                            │
│                                                                 │
│ ACTIONS:                                                        │
│ 1. Strip whitespace from all tokens (prevent JWT parse errors)  │
│ 2. Encrypt sensitive fields with AES-256-GCM:                   │
│    - access_token → iv:tag:ciphertext                           │
│    - api_key → iv:tag:ciphertext                                │
│    - api_secret → iv:tag:ciphertext                             │
│ 3. Save to Firestore: dhan_credentials/{firebase_uid}           │
│ 4. Return success response                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                 ✅ Credentials stored securely
```

### 2. Trading Operations (Use Credentials)

```
┌─────────────────────────────────────────────────────────────────┐
│ USER REQUEST                                                     │
│ GET /api/dhan/funds?user_id={firebase_uid}                      │
│ GET /api/dhan/positions?user_id={firebase_uid}                  │
│ POST /api/dhan/orders?user_id={firebase_uid}                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: engine-c/src/main.py                                   │
│ Trading endpoint handler                                        │
│ Calls: get_dhan_client_async(user_id)                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: engine-c/src/user_credentials.py                       │
│ Line 440: get_dhan_client_async(user_id)                        │
│                                                                 │
│ ACTIONS:                                                        │
│ 1. Resolve user_id (handles generated IDs like                  │
│    "user_1768802144009_1jvf3b" → Firebase UID)                  │
│ 2. Retrieve from Firestore: dhan_credentials/{resolved_uid}     │
│ 3. Decrypt credentials (AES-256-GCM)                             │
│ 4. Create authenticated DhanHQ client                            │
│ 5. Return client object                                          │
│                                                                 │
│ ERROR HANDLING:                                                 │
│ - Document not found → HTTP 401 "Credentials not found"         │
│ - Decryption fails → HTTP 500 "Credential decryption error"     │
│ - DhanHQ auth fails → HTTP 401 "DhanHQ authentication failed"   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ DHAN API CALL                                                    │
│ Uses decrypted user credentials                                 │
│ Returns: Funds, Positions, Orders, etc.                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                  ✅ User-specific data returned
```

---

## 🔧 Key Components

### UserCredentialsManager
**File:** `backend/engine-c/src/user_credentials.py`  
**Purpose:** Manages encrypted per-user credentials in Firestore

**Key Methods:**
- `save_user_credentials(user_id, client_id, access_token, ...)` - Encrypts and stores
- `get_user_credentials(user_id)` - Retrieves and decrypts
- `resolve_user_id(user_id)` - Handles generated user IDs → Firebase UID
- `get_dhan_client_async(user_id)` - Returns authenticated DhanHQ client
- `verify_user_credentials(user_id)` - Tests credentials with DhanHQ API
- `delete_user_credentials(user_id)` - Removes credentials from Firestore

**Encryption Details:**
```python
def _encrypt(self, data: str) -> str:
    nonce = os.urandom(12)  # 12-byte IV for GCM
    encryptor = Cipher(
        algorithms.AES(self.encryption_key),  # 32-byte key
        modes.GCM(nonce),
    ).encryptor()
    ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
    tag = encryptor.tag
    return f"{nonce.hex()}:{tag.hex()}:{ciphertext.hex()}"
```

### Config (Platform Defaults)
**File:** `backend/engine-c/src/core/config.py`  
**Purpose:** Optional platform-wide defaults (NOT used for trading)

**Values (all optional):**
- `DHAN_API_BASE` - DhanHQ API base URL
- `WEBSOCKET_URL` - DhanHQ WebSocket URL
- `DHAN_ACCESS_TOKEN` - Platform default (unused in trading)
- `CLIENT_ID` - Platform default (unused in trading)

**Note:** These are NOT used for user trading operations. All trading uses per-user Firestore credentials.

---

## 🚫 Removed Components

### dhan_credentials_manager.py
**Status:** DEPRECATED (marked as unused)  
**Previous Purpose:** Secret Manager integration for platform-wide credentials  
**Removal Reason:** Architecture chose per-user credentials; platform-wide credentials not needed  
**Action:** File kept for reference with deprecation notice

---

## ✅ Security Best Practices

### 1. Encryption Key Management
**Environment Variable:** `USER_CREDENTIALS_KEY`
```bash
# Generate 32-byte key (64 hex characters)
openssl rand -hex 32
# Example: a3f2c8e9d4b7f1a6c5e8d2f9b3a7c1e4d8f2b6a9c3e7d1f5b8a2c6e9d3f7b1a5
```

**Cloud Run Setup:**
```bash
gcloud run services update engine-c \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --set-env-vars="USER_CREDENTIALS_KEY=<your-64-char-hex-key>"
```

**Alternative (Secret Manager):**
```bash
# Store key in Secret Manager
echo "<your-64-char-hex-key>" | gcloud secrets create user-credentials-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=galvanic-pulsar-482815-h0

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding user-credentials-key \
  --member="serviceAccount:engine-c@galvanic-pulsar-482815-h0.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=galvanic-pulsar-482815-h0

# Update Cloud Run to use secret
gcloud run services update engine-c \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --set-secrets="USER_CREDENTIALS_KEY=user-credentials-key:latest"
```

### 2. Firestore Security Rules
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // DhanHQ credentials - user can only access their own
    match /dhan_credentials/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      allow read: if request.auth.token.admin == true; // Backend service account
    }
  }
}
```

### 3. API Endpoint Security
- All endpoints require valid `user_id` parameter
- Credentials retrieved only for authenticated user
- No cross-user credential access
- Encrypted at rest in Firestore
- Decrypted only in memory (never logged)

### 4. Credential Validation
```python
# All credentials stripped of whitespace to prevent JWT parsing errors
access_token = access_token.strip()
client_id = client_id.strip()
api_key = api_key.strip() if api_key else None
api_secret = api_secret.strip() if api_secret else None
```

---

## 📝 User Onboarding Guide

### For End Users

**Step 1: Get DhanHQ Credentials**
1. Log in to [DhanHQ Dashboard](https://dhan.co)
2. Navigate to API Settings
3. Copy:
   - Client ID
   - Access Token
   - API Key (for market data)
   - API Secret

**Step 2: Save in InfinityAI.Pro**
1. Log in to InfinityAI.Pro
2. Go to Settings → DhanHQ Integration
3. Paste credentials
4. Click "Save Credentials"
5. Wait for verification ✅

**Step 3: Start Trading**
- Credentials are now active
- All trading operations use your DhanHQ account
- Funds/positions reflect your broker account

---

## 🧪 Testing & Verification

### Test Credential Save
```bash
curl -X POST https://engine-c-<hash>.run.app/api/v1/user/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "firebase_uid_here",
    "client_id": "1101302170",
    "access_token": "eyJ0eXAi...",
    "api_key": "b76a41e2",
    "api_secret": "3b27c08e-..."
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Credentials saved successfully",
  "user_id": "firebase_uid_here",
  "client_id": "1101302170"
}
```

### Test Credential Retrieval
```bash
curl https://engine-c-<hash>.run.app/api/v1/user/credentials/firebase_uid_here
```

**Expected Response:**
```json
{
  "status": "success",
  "configured": true,
  "client_id": "1101302170",
  "is_verified": true,
  "connection_status": "connected"
}
```

### Test Trading Endpoint
```bash
curl https://engine-c-<hash>.run.app/api/dhan/funds?user_id=firebase_uid_here
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "availableFunds": 25000.50,
    "usedMargin": 5000.00,
    ...
  }
}
```

---

## 🔍 Debugging

### Common Issues

**Issue 1: "Credentials not found" (HTTP 401)**
- **Cause:** User hasn't saved credentials in Settings page
- **Fix:** User must input credentials via frontend Settings

**Issue 2: "Credential decryption error" (HTTP 500)**
- **Cause:** `USER_CREDENTIALS_KEY` mismatch or missing
- **Fix:** Ensure same encryption key used for encrypt/decrypt

**Issue 3: "DhanHQ authentication failed" (HTTP 401)**
- **Cause:** Invalid/expired DhanHQ access token
- **Fix:** User must regenerate token from DhanHQ dashboard

**Issue 4: Generated user IDs not resolving**
- **Cause:** Frontend sends `user_1768802144009_1jvf3b` instead of Firebase UID
- **Fix:** `resolve_user_id()` method handles this automatically
- **Verify:** Check Firestore document exists with Firebase UID

### Check Firestore Documents
```bash
# List all credential documents
gcloud firestore documents list dhan_credentials --project=galvanic-pulsar-482815-h0

# Get specific user's document
gcloud firestore documents get dhan_credentials/firebase_uid_here --project=galvanic-pulsar-482815-h0
```

### Check Logs
```bash
# Engine-C logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name="engine-c"' \
  --limit=100 \
  --project=galvanic-pulsar-482815-h0 \
  --format=json
```

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                       USER (Browser)                                 │
│                                                                      │
│  1. Firebase Auth Login → Firebase UID                              │
│  2. Navigate to Settings → Input DhanHQ credentials                 │
│  3. Click "Save Credentials"                                        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  FRONTEND (Next.js / Cloud Run)                      │
│                                                                      │
│  POST /api/user/credentials                                         │
│  { user_id, client_id, access_token, api_key, api_secret }          │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│              BACKEND ENGINE-C (FastAPI / Cloud Run)                  │
│                                                                      │
│  UserCredentialsManager.save_user_credentials()                     │
│  ├─ Strip whitespace                                                │
│  ├─ Encrypt with AES-256-GCM                                        │
│  └─ Save to Firestore                                               │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    FIRESTORE (GCP)                                   │
│                                                                      │
│  Collection: dhan_credentials                                        │
│  Document: {firebase_uid}                                           │
│  Fields: encrypted credentials, metadata                            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
          ✅ Credentials stored securely and ready for trading
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    TRADING FLOW (Later)                              │
│                                                                      │
│  User clicks "Buy" or "Sell" → Trading endpoint                     │
│  ├─ get_dhan_client_async(user_id)                                  │
│  ├─ Retrieve from Firestore                                         │
│  ├─ Decrypt credentials                                             │
│  ├─ Create DhanHQ client                                            │
│  └─ Execute trade on DhanHQ API                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎓 Summary

**Architecture:** Multi-tenant per-user credentials  
**Storage:** Firestore with AES-256-GCM encryption  
**Flow:** Frontend Settings → Engine-C API → Firestore → Trading Endpoints  
**Security:** User-isolated, encrypted at rest, decrypted in memory only  
**Onboarding:** Users save their own DhanHQ credentials via Settings page  
**Removed:** Secret Manager platform-wide credential system (deprecated)  

**Result:** Clean, secure, multi-tenant trading platform with per-user broker accounts. ✅
