# 🔐 DHAN CREDENTIAL VERIFICATION GUIDE

**Purpose**: Verify that Dhan credentials updated via dashboard are properly stored and accessible by the backend
**Project**: InfinityAI.Pro (galvanic-pulsar-482815-h0)
**Last Updated**: January 11, 2026
**Status**: ✅ READY FOR VERIFICATION

---

## 📋 CREDENTIAL FLOW ARCHITECTURE

### Storage Layers (Dual-Storage Pattern)

```
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND DASHBOARD (Settings → Dhan Account Tab)            │
│  - User inputs Dhan API credentials                          │
│  - Submits via POST /api/user/credentials                    │
└───────────────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────┴────────────────┐
        │                                │
        ▼                                ▼
    ┌─────────────────┐         ┌──────────────────────┐
    │   FIRESTORE     │         │  GOOGLE SECRET MGR   │
    │   Collection:   │         │  Secret Name:        │
    │user_credentials │         │user-creds-{user_id}  │
    │                 │         │                      │
    │Fields:          │         │Contains:             │
    │- user_id        │         │- client_id           │
    │- dhan_client_id │         │- access_token        │
    │- access_token   │         │- api_key (optional)  │
    │- updated_at     │         │- api_secret (opt.)   │
    │- has_credentials│         │- version (versioned) │
    └─────────────────┘         └──────────────────────┘
        PRIMARY VAULT                BACKUP VAULT
        (Firestore)          (Cloud Secret Manager)

        ▼ (Frontend CloudFn)  ▼ (Engine-C Backend)

    Both systems:
    - Triggered on dashboard update
    - Automatically encrypted
    - Version-controlled
    - Audit-logged
```

---

## 🔍 VERIFICATION STEPS

### STEP 1: Check Firestore Storage

**Purpose**: Verify credentials are stored in Firebase Firestore
**Collection**: `user_credentials`
**Document ID**: Your Google User ID (same as authenticated user)

#### Option A: Firebase Console (Web UI)

1. Go to: https://console.firebase.google.com
2. Select Project: `galvanic-pulsar-482815-h0`
3. Navigate to: **Firestore Database** → Collections
4. Find collection: `user_credentials`
5. Look for document with your **User ID**
6. Verify these fields exist:
   - ✅ `user_id` (string): Your authenticated user ID
   - ✅ `dhan_client_id` (string): 10-digit numeric Dhan client ID
   - ✅ `dhan_access_token` (string): Long token string
   - ✅ `updated_at` (timestamp): Should be recent (your dashboard update time)

#### Option B: CLI Verification

```bash
# List all documents in user_credentials collection
gcloud firestore documents list --collection-path=user_credentials \
  --project=galvanic-pulsar-482815-h0

# Get your specific document
gcloud firestore documents get user_credentials/{YOUR_USER_ID} \
  --project=galvanic-pulsar-482815-h0
```

**Expected Output**:
```
fields:
  dhan_access_token:
    stringValue: "eyJ0eXAi..."
  dhan_client_id:
    stringValue: "1234567890"
  updated_at:
    timestampValue: "2026-01-11T15:30:45Z"
  user_id:
    stringValue: "rBwWLLL6XiS6KBeXkiacx6c848q1"
```

---

### STEP 2: Check Cloud Secret Manager Storage

**Purpose**: Verify credentials are also backed up in Google Secret Manager
**Secret Name Pattern**: `user-creds-{user_id}` (with special characters escaped)

#### Option A: Cloud Console

1. Go to: https://console.cloud.google.com
2. Select Project: `galvanic-pulsar-482815-h0`
3. Navigate to: **Secret Manager** → Secrets
4. Search for secret starting with: `user-creds-`
5. Click the secret matching your user ID
6. Click **Versions** tab
7. Latest version should show:
   - ✅ **Created**: Recent (matching dashboard update)
   - ✅ **State**: Enabled
   - ✅ **Access count**: May show recent accesses

#### Option B: CLI Verification

```bash
# List all user credential secrets
gcloud secrets list --filter="name:user-creds-*" \
  --project=galvanic-pulsar-482815-h0

# Get your specific secret (LATEST VERSION)
gcloud secrets versions list user-creds-YOUR_ESCAPED_ID \
  --project=galvanic-pulsar-482815-h0

# View secret metadata (NOT the actual secret value for security)
gcloud secrets describe user-creds-YOUR_ESCAPED_ID \
  --project=galvanic-pulsar-482815-h0
```

**Example Output**:
```
name: projects/galvanic-pulsar-482815-h0/secrets/user-creds-rBwWLLL6XiS6KBeXkiacx6c848q1
versions:
  - name: 1
    createTime: 2026-01-11T15:30:45Z
    state: ENABLED
    updateTime: 2026-01-11T15:30:45Z
```

---

### STEP 3: Test Credential Retrieval via Cloud Function

**Purpose**: Verify credentials can be retrieved and used by backend services
**Cloud Function**: `getUserCredentials` (Frontend Function in Firebase)

#### Via Cloud Console

1. Navigate to: **Cloud Functions** → `getUserCredentials`
2. Click **TESTING** tab
3. In the request JSON, enter:
```json
{
  "user_id": "YOUR_USER_ID"
}
```
4. Click **EXECUTE**
5. Expected response:
```json
{
  "success": true,
  "dhan_client_id": "1234567890",
  "dhan_access_token": "eyJ0eXAi...",
  "updated_at": "2026-01-11T15:30:45.000Z"
}
```

#### Via CLI

```bash
gcloud functions call getUserCredentials \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --data='{"user_id":"YOUR_USER_ID"}'
```

---

### STEP 4: Test Dhan API Connectivity

**Purpose**: Verify the stored credentials actually work with Dhan API
**Endpoint**: Engine-C `/api/dhan/verify`

#### Via curl

```bash
curl -X POST https://engine-c-738553258162.us-central1.run.app/api/dhan/verify \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "client_id": "1234567890",
    "access_token": "YOUR_ACCESS_TOKEN"
  }'
```

**Expected Success Response**:
```json
{
  "success": true,
  "verified": true,
  "message": "Connection verified successfully"
}
```

**Expected Error Response** (credentials invalid):
```json
{
  "success": false,
  "verified": false,
  "message": "Verification failed: Invalid access token or client ID"
}
```

#### Via Engine-C Dashboard API (Recommended)

If your Dashboard has an API testing interface:

1. Navigate to Engine-C: https://engine-c.infinityai.pro/docs (if available)
2. Find endpoint: **POST** `/api/dhan/verify`
3. Expand the endpoint
4. Click "Try it out"
5. Enter request body:
```json
{
  "user_id": "YOUR_USER_ID",
  "client_id": "1234567890",
  "access_token": "YOUR_ACCESS_TOKEN"
}
```
6. Click **Execute**
7. Check response code (200 = success, 401/403 = credential invalid)

---

### STEP 5: Test Account Data Retrieval

**Purpose**: Verify credentials work end-to-end for fetching Dhan account data
**Endpoint**: Engine-C `/api/v1/user/{userId}/account`

#### Via curl

```bash
curl -X GET "https://engine-c-738553258162.us-central1.run.app/api/v1/user/YOUR_USER_ID/account" \
  -H "Authorization: Bearer YOUR_DHAN_ACCESS_TOKEN"
```

**Expected Success Response**:
```json
{
  "success": true,
  "user_id": "YOUR_USER_ID",
  "account": {
    "funds": {
      "available": 100000,
      "used": 25000,
      "total": 125000
    },
    "holdings": [...],
    "positions": [...]
  }
}
```

---

## 🧪 AUTOMATED VERIFICATION SCRIPT

Run the provided verification tool to check everything at once:

```bash
# From workspace root
cd c:\workspace\InfinityAI.Pro

# Verify credentials for a specific user
python tools/verify_engine_c_dhan.py YOUR_USER_ID

# Example output:
# ==================================================
#    DHAN INTEGRATION VERIFICATION TOOL
# ==================================================
#
# 🔍 Checking Firestore for User: rBwWLLL6XiS6KBeXkiacx6c848q1
#    📄 User Document Found:
#       - Dhan Connected: True
#       - Dhan Client ID: 1234567890
#
# 🔐 Checking Stored Credentials for User: rBwWLLL6XiS6KBeXkiacx6c848q1
#    ✅ Credentials found in Secret Manager!
#       - Client ID: 1234567890
#       - Verified Status: True
#       - Last Updated: 2026-01-11T15:30:45Z
#
# 📊 DIAGNOSIS SUMMARY
# ────────────────────
# Firestore 'dhanConnected': True
# Secret Manager Credentials: FOUND
# ✅ VERIFICATION PASSED
```

---

## 🚨 COMMON ISSUES & DIAGNOSTICS

### Issue 1: Credentials Found in Firestore BUT Not in Secret Manager

**Possible Cause**: Backend storage failed silently
**Verification Step**:
```bash
# Check Cloud Function logs for errors
gcloud functions logs read storeUserCredentials \
  --limit=50 \
  --project=galvanic-pulsar-482815-h0
```
**Fix**: Clear Firestore document and re-submit credentials from dashboard

---

### Issue 2: Credentials in Both Stores BUT Dhan API Returns 401 (Unauthorized)

**Possible Cause**: Credentials expired or invalid at Dhan's end
**Verification Step**:
1. Log in to Dhan directly: https://dhanhq.com
2. Go to **Settings → API → Access Tokens**
3. Check if your `access_token` is listed and **Enabled**
4. If expired, generate a new token
5. Re-submit via Settings → Dhan Account tab in Dashboard

---

### Issue 3: Credentials NOT Found in Either Store

**Possible Cause**: Dashboard update didn't trigger backend functions
**Verification Step**:
```bash
# Check if Cloud Functions are deployed
gcloud functions list --filter="name:storeUserCredentials OR name:submitDhanCredentialsV2" \
  --project=galvanic-pulsar-482815-h0

# Check function logs for errors
gcloud functions logs read submitDhanCredentialsV2 \
  --limit=100 \
  --project=galvanic-pulsar-482815-h0
```
**Fix**: Manually trigger credential submission:
```javascript
// In browser console (after logging in via Dashboard)
const { storeCredentialsAPI } = await import('/lib/cloudFunctions.ts');
const result = await storeCredentialsAPI(
  "YOUR_USER_ID",
  "YOUR_CLIENT_ID",
  "YOUR_ACCESS_TOKEN"
);
console.log(result);
```

---

### Issue 4: Timestamp Mismatch (Credentials Old vs. Dashboard Update Recent)

**Possible Cause**: Credentials were stored from previous session
**Verification Step**:
```bash
# Get the timestamp from Firestore
gcloud firestore documents get user_credentials/YOUR_USER_ID \
  --project=galvanic-pulsar-482815-h0 | grep updated_at

# Compare with your expected update time
# If old: re-submit credentials from Settings page
```

---

## ✅ VERIFICATION CHECKLIST

Use this checklist to verify complete credential flow:

- [ ] **Firestore**: Document exists in `user_credentials` collection
- [ ] **Firestore**: `dhan_client_id` field matches Dhan account
- [ ] **Firestore**: `updated_at` timestamp is recent (matches dashboard update)
- [ ] **Secret Manager**: Secret `user-creds-{user_id}` exists
- [ ] **Secret Manager**: Latest version is enabled and recent
- [ ] **Cloud Function**: `getUserCredentials` returns credentials successfully
- [ ] **Dhan API**: `/api/dhan/verify` returns `verified: true`
- [ ] **Account Data**: `/api/v1/user/{userId}/account` returns holdings/positions
- [ ] **Frontend Dashboard**: Settings page shows "Status: CONNECTED ✓ Verified"

---

## 📊 QUICK REFERENCE: Key Endpoints

| Action | Endpoint | Method | Auth Required |
|--------|----------|--------|---------------|
| **Store Credentials** | `/api/user/credentials` | POST | Firebase Auth |
| **Retrieve Credentials** | `/api/dhan/credentials/{user_id}` | GET | Service Auth |
| **Verify Connection** | `/api/dhan/verify` | POST | None (client provides) |
| **Get Account Data** | `/api/v1/user/{userId}/account` | GET | Dhan Token |
| **Delete Credentials** | `/api/dhan/credentials/{user_id}` | DELETE | Service Auth |

---

## 🔒 SECURITY NOTES

✅ **What's Secure**:
- Credentials stored encrypted in Firestore (at-rest)
- Credentials encrypted in Secret Manager (versioned, audit-logged)
- Frontend never stores raw credentials (uses Cloud Functions)
- Dhan API calls use service-to-service auth
- Credentials masked in API responses (last 4 chars only)

⚠️ **Best Practices**:
- Never share your access token (it's like a password)
- Regenerate token periodically in Dhan settings
- Delete old credentials when switching Dhan accounts
- Monitor Cloud Function logs for unauthorized access attempts
- Use separate tokens for testing vs. production

---

## 📞 SUPPORT

If verification fails:
1. Run automated script: `python tools/verify_engine_c_dhan.py YOUR_USER_ID`
2. Check Cloud Function logs: `gcloud functions logs read`
3. Verify Dhan token in Dhan console: https://dhanhq.com/settings
4. Clear browser cache and re-submit credentials from Settings
5. Contact support with the diagnostic output from step 1

---

**Next Step**: Run the verification checklist above. All ✅ items should be marked when credentials are properly stored and accessible.
