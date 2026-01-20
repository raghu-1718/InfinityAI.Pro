# End-to-End Credential Flow Analysis
## InfinityAI.Pro - Complete Verification Report

**Date:** January 20, 2026  
**Project:** galvanic-pulsar-482815-h0  
**Status:** ⚠️ CRITICAL ARCHITECTURE ISSUES IDENTIFIED

---

## 🔴 CRITICAL FINDINGS

### 1. **DUAL CREDENTIAL SYSTEMS - UNINTEGRATED**

There are **TWO SEPARATE** credential management systems operating independently:

#### System A: User-Specific Credentials (Firestore)
- **Purpose:** Per-user DhanHQ credentials for multi-tenant trading
- **Storage:** Firestore collection `dhan_credentials`
- **Encryption:** AES-256-GCM
- **Used By:** Frontend → Cloud Functions → Firestore → Backend API

#### System B: Global Credentials (Secret Manager)  
- **Purpose:** Platform-wide DhanHQ credentials
- **Storage:** Google Secret Manager
- **Used By:** `dhan_credentials_manager.py` → Backend services
- **Files:** `dhan_credentials_manager.py`, `config.py`

### ⚠️ **PROBLEM:** These systems DO NOT communicate!

---

## 📊 End-to-End Flow Analysis

### **Flow 1: User Saves Credentials (Settings Page)**

```
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND: settings/page.tsx                                          │
│ User inputs:                                                         │
│  - Client ID                                                         │
│  - Access Token                                                      │
│  - API Key (optional)                                                │
│  - API Secret (optional)                                             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    POST /api/user/credentials
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND: engine-c/src/main.py                                        │
│ Endpoint: @app.post("/api/v1/user/credentials")                      │
│ Line 973                                                             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                   Calls UserCredentialsManager
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND: user_credentials.py                                         │
│ Method: save_user_credentials(user_id, client_id, ...)               │
│ Lines 135-204                                                        │
│                                                                      │
│ ACTIONS:                                                             │
│ 1. Strips whitespace from tokens                                    │
│ 2. Encrypts credentials with AES-256-GCM                             │
│ 3. Saves to Firestore: dhan_credentials/{user_id}                   │
│    Format: {                                                         │
│      "credentials": {                                                │
│        "client_id": "plaintext",                                     │
│        "access_token": "iv:tag:ciphertext",                          │
│        "api_key": "iv:tag:ciphertext",                               │
│        "api_secret": "iv:tag:ciphertext"                             │
│      },                                                              │
│      "clientId": "iv:tag:ciphertext",  // Frontend compat            │
│      "accessToken": "iv:tag:ciphertext",                             │
│      ...                                                             │
│    }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    ✅ Saved to Firestore
```

### **Flow 2: Backend Retrieves User Credentials for Trading**

```
┌─────────────────────────────────────────────────────────────────────┐
│ USER REQUESTS: GET /api/dhan/funds?user_id={id}                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND: main.py                                                     │
│ Endpoint: @app.get("/api/dhan/funds")                                │
│ Calls: get_dhan_client_async(user_id)                                │
│ Line 995 (approx)                                                    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND: user_credentials.py                                         │
│ Method: get_dhan_client_async(user_id)                               │
│ Lines 440-506                                                        │
│                                                                      │
│ ACTIONS:                                                             │
│ 1. Resolves user_id (handles generated IDs)                          │
│ 2. Retrieves from Firestore: dhan_credentials/{resolved_user_id}    │
│ 3. Decrypts credentials (handles both backend/frontend formats)      │
│ 4. Creates DhanClient with decrypted credentials                     │
│ 5. Returns authenticated client                                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
               Uses decrypted credentials for DhanHQ API
                              ↓
                  ✅ Returns funds/positions/orders
```

### **Flow 3: Secret Manager Credentials (NEW - UNUSED)**

```
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND STARTUP: config.py                                           │
│ Lines 23-41                                                          │
│                                                                      │
│ try:                                                                 │
│   _creds_mgr = get_credentials_manager()                             │
│   Config.DHAN_ACCESS_TOKEN = _creds_mgr.get_access_token()          │
│   Config.CLIENT_ID = _creds_mgr.get_client_id()                      │
│   Config.DHAN_API_KEY = _creds_mgr.get_api_key()                     │
│   Config.DHAN_API_SECRET = _creds_mgr.get_api_secret()               │
│ except:                                                              │
│   # Fallback to environment variables                                │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ dhan_credentials_manager.py                                          │
│ Class: DhanCredentialsManager                                        │
│                                                                      │
│ RETRIEVAL LOGIC:                                                     │
│ 1. Try Secret Manager: projects/{PROJECT}/secrets/dhan-api-key      │
│ 2. Fallback: os.getenv("DHAN_API_KEY")                               │
│ 3. Raise error if not found                                          │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
            ⚠️ Config values set but NEVER USED
                              ↓
         All trading uses Firestore user credentials
```

---

## 🔍 Code Evidence

### 1. Frontend Saves to Firestore (via Engine-C API)

**File:** `frontend/web-app/src/app/(dashboard)/settings/page.tsx`
**Lines:** 116-126
```tsx
const response = await fetch(`${ENGINE_C_URL}/api/user/credentials`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: session.userId,
    client_id: dhanCredentials.client_id,
    api_key: dhanCredentials.api_key || "",
    api_secret: dhanCredentials.api_secret || "",
    access_token: dhanCredentials.access_token,
  }),
});
```

### 2. Backend Saves to Firestore

**File:** `backend/engine-c/src/user_credentials.py`  
**Lines:** 135-204 (save_user_credentials method)
```python
# Encrypt sensitive credentials
encrypted_credentials = {
    "client_id": client_id,  # Client ID is not secret
    "access_token": self._encrypt(access_token),
    "api_key": self._encrypt(api_key) if api_key else None,
    "api_secret": self._encrypt(api_secret) if api_secret else None,
}

# Save to Firestore
doc_ref = self.db.collection(self.collection).document(user_id)
doc_ref.set(doc_data, merge=True)
```
**Collection:** `dhan_credentials`  
**Document ID:** `user_id` (Firebase UID)

### 3. Backend Retrieves from Firestore for Trading

**File:** `backend/engine-c/src/user_credentials.py`  
**Lines:** 206-297 (get_user_credentials method)
```python
async def get_user_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
    doc_ref = self.db.collection(self.collection).document(user_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    # Decrypt and return credentials
```

**File:** `backend/engine-c/src/user_credentials.py`  
**Lines:** 440-506 (get_dhan_client_async method)
```python
async def get_dhan_client_async(user_id: str):
    """Get DhanHQ client for specific user from Firestore credentials"""
    manager = UserCredentialsManager()
    
    # Resolve user ID (handles generated IDs)
    resolved_user_id = await manager.resolve_user_id(user_id)
    
    # Get credentials from Firestore
    creds = await manager.get_user_credentials(resolved_user_id)
    
    # Create authenticated client
    client = create_dhan_client(
        client_id=creds["credentials"]["client_id"],
        access_token=creds["credentials"]["access_token"]
    )
    return client
```

### 4. Secret Manager System (Created but Unused)

**File:** `backend/engine-c/src/dhan_credentials_manager.py`  
**Lines:** 1-161 (entire file)
```python
class DhanCredentialsManager:
    def get_api_key(self) -> str:
        if self.use_secret_manager:
            value = self._get_secret_value("dhan-api-key")
            if value:
                return value
        return os.getenv("DHAN_API_KEY")
```

**File:** `backend/engine-c/src/core/config.py`  
**Lines:** 23-41
```python
try:
    from ..dhan_credentials_manager import get_credentials_manager
    _creds_mgr = get_credentials_manager()
    
    Config.DHAN_ACCESS_TOKEN = _creds_mgr.get_access_token()
    Config.CLIENT_ID = _creds_mgr.get_client_id()
    Config.DHAN_API_KEY = _creds_mgr.get_api_key()
    Config.DHAN_API_SECRET = _creds_mgr.get_api_secret()
except Exception as e:
    logging.warning(f"Failed to load credentials from Secret Manager: {e}")
```

**⚠️ PROBLEM:** Config values are set, but ALL trading endpoints use `get_dhan_client_async()` which retrieves from **Firestore**, not Config!

---

## 🔐 Encryption & Security Analysis

### Firestore User Credentials
- **Algorithm:** AES-256-GCM
- **Key Source:** 
  1. Environment variable `USER_CREDENTIALS_KEY` (64-char hex = 32 bytes)
  2. Secret Manager `user-credentials-key`
  3. Fallback: Insecure derived key
- **Format:** `iv:tag:ciphertext` (hex-encoded)
- **Storage:** Firestore `dhan_credentials` collection
- **Access:** Backend has Firestore admin access

### Secret Manager Credentials
- **Storage:** Google Secret Manager
- **Secrets:**
  - `dhan-api-key`
  - `dhan-api-secret`
  - `dhan-client-id`
  - `dhan-access-token`
- **Access:** IAM role `roles/secretmanager.secretAccessor` required
- **Usage:** NONE (code exists but not used in trading flow)

---

## 🚨 Architecture Problems

### Problem 1: Credentials You Provided Are Not Being Used

**You provided:**
- API Key: b76a41e2
- API Secret: 3b27c08e-797c-40e4-8e80-0498ea853236
- Client ID: 1101302170
- Access Token: eyJ0eXAi...

**Current System Behavior:**
1. If stored in Secret Manager → Config loads them → **UNUSED** (no endpoint reads Config for trading)
2. If NOT stored in Firestore per-user → **Error 808** when user tries to trade
3. System expects **each user** to input their own credentials in Settings page

**Root Cause:** Multi-tenant architecture expects individual user credentials, but you're trying to use platform-wide credentials.

### Problem 2: dhan_credentials_manager.py Is Dead Code

- Created for Secret Manager integration
- Config.py loads values successfully
- **BUT:** No trading endpoint uses Config values
- All trading uses `get_dhan_client_async(user_id)` → Firestore lookup
- Secret Manager values sit unused in memory

### Problem 3: Dual Storage Without Bridge

- User credentials → Firestore (encrypted with `USER_CREDENTIALS_KEY`)
- Platform credentials → Secret Manager (encrypted by Google)
- **NO MIGRATION PATH** between systems
- **NO FALLBACK** from Secret Manager to Firestore

### Problem 4: Error 808 Will Persist

**Current Flow:**
```
User logs in → Settings page loads
User tries to trade → Backend calls get_dhan_client_async(user_id)
Firestore lookup: dhan_credentials/{user_id}
Document doesn't exist → Returns None
Trading endpoints fail → Error 808 "Client ID or Token invalid"
```

**Even if you store credentials in Secret Manager:**
```
Secrets created → Config.py loads them
User tries to trade → get_dhan_client_async(user_id)
Firestore lookup: dhan_credentials/{user_id}
Document doesn't exist → Returns None
Config values ignored → Error 808
```

---

## ✅ Solutions

### Solution 1: Use Firestore User Credentials (Current Architecture)

**For Your Account:**
1. Log into frontend with your Firebase UID
2. Go to Settings page
3. Input your DhanHQ credentials:
   - Client ID: 1101302170
   - Access Token: eyJ0eXAi...
   - API Key: b76a41e2
   - API Secret: 3b27c08e-797c-40e4-8e80-0498ea853236
4. Click "Save Credentials"
5. Frontend calls `POST /api/user/credentials`
6. Backend saves to Firestore: `dhan_credentials/{your_firebase_uid}`

**Result:** Your credentials encrypted and stored; trading works for YOUR account.

**Limitation:** Each user must input their own credentials.

---

### Solution 2: Platform-Wide Credentials (Requires Code Changes)

**Modify:** `user_credentials.py::get_dhan_client_async()`

**Current Code (Lines 440-506):**
```python
async def get_dhan_client_async(user_id: str):
    manager = UserCredentialsManager()
    resolved_user_id = await manager.resolve_user_id(user_id)
    creds = await manager.get_user_credentials(resolved_user_id)
    # Uses Firestore credentials
```

**New Code (with Secret Manager fallback):**
```python
async def get_dhan_client_async(user_id: str):
    manager = UserCredentialsManager()
    resolved_user_id = await manager.resolve_user_id(user_id)
    creds = await manager.get_user_credentials(resolved_user_id)
    
    # NEW: Fallback to platform credentials if user credentials missing
    if not creds or not creds.get("credentials"):
        from .dhan_credentials_manager import get_credentials_manager
        platform_creds = get_credentials_manager()
        
        creds = {
            "credentials": {
                "client_id": platform_creds.get_client_id(),
                "access_token": platform_creds.get_access_token(),
                "api_key": platform_creds.get_api_key(),
                "api_secret": platform_creds.get_api_secret(),
            }
        }
        logger.info(f"Using platform credentials for user {user_id}")
    
    # Create client
    client = create_dhan_client(
        client_id=creds["credentials"]["client_id"],
        access_token=creds["credentials"]["access_token"]
    )
    return client
```

**Result:** 
- Users with their own credentials → Use their credentials
- Users without credentials → Use platform credentials from Secret Manager
- **YOUR** credentials work for all users (single DhanHQ account)

---

### Solution 3: Migrate Firestore to Secret Manager (Advanced)

**Steps:**
1. Retrieve all documents from `dhan_credentials` collection
2. For each user:
   - Decrypt Firestore credentials
   - Store in Secret Manager: `dhan-credentials-{user_id}`
3. Update `get_user_credentials()` to read from Secret Manager
4. Deprecate Firestore storage

**Pros:** Centralized secret management, better security  
**Cons:** Complexity, IAM management per user

---

## 📋 Verification Checklist

### Current State (As-Is)
- ✅ Frontend saves credentials to Firestore via Engine-C API
- ✅ Backend encrypts credentials with AES-256-GCM
- ✅ Firestore collection `dhan_credentials` stores encrypted data
- ✅ Backend retrieves from Firestore for trading operations
- ✅ `user_credentials.py` handles encryption/decryption
- ✅ `get_dhan_client_async()` creates authenticated DhanHQ client
- ❌ Secret Manager credentials NOT used in trading flow
- ❌ `dhan_credentials_manager.py` loaded but unused
- ❌ Config values set but never referenced in trading endpoints
- ❌ Error 808 persists if user credentials missing in Firestore

### What Works
- Users can save credentials via Settings page
- Backend stores in Firestore securely
- Backend retrieves for trading operations
- Encryption/decryption working (AES-256-GCM)

### What Doesn't Work
- Platform-wide credentials from Secret Manager (not integrated)
- Error 808 if user hasn't saved credentials in Settings
- `dhan_credentials_manager.py` is dead code

---

## 🎯 Recommended Action Plan

### Option A: Quick Fix (Use Firestore for Your Account)
**Time:** 2 minutes  
**Steps:**
1. Open frontend Settings page
2. Input your credentials
3. Click Save
4. Test trading endpoints

**Result:** Works for your account immediately.

---

### Option B: Integrate Secret Manager (Platform-Wide)
**Time:** 15 minutes  
**Steps:**
1. Store credentials in Secret Manager (your provided values)
2. Grant IAM access to Cloud Run service account
3. Modify `get_dhan_client_async()` to fallback to platform credentials
4. Deploy backend
5. Test with any user

**Result:** All users can trade using your DhanHQ account.

---

### Option C: Verify Current Flow (No Changes)
**Time:** 10 minutes  
**Steps:**
1. Check Firestore: `dhan_credentials/{your_firebase_uid}`
2. Verify encryption key: `USER_CREDENTIALS_KEY` env var
3. Test save credentials API endpoint
4. Test retrieve credentials API endpoint
5. Test trading endpoints with your UID

**Result:** Confirms current architecture working (per-user credentials).

---

## 📊 Summary Table

| Component | Purpose | Storage | Used By | Status |
|-----------|---------|---------|---------|--------|
| **UserCredentialsManager** | Per-user credentials | Firestore `dhan_credentials` | All trading endpoints | ✅ Active |
| **DhanCredentialsManager** | Platform credentials | Secret Manager | Config.py only | ❌ Unused |
| **Frontend Settings** | Credential input UI | → Engine-C API → Firestore | Users | ✅ Active |
| **Config.py values** | Startup config | Memory (from Secret Manager) | None | ❌ Orphaned |
| **Error 808 Issue** | Missing credentials | Firestore lookup failure | Users without saved creds | 🔴 Active Bug |

---

## 🔧 Next Steps

**YOU MUST CHOOSE:**

1. **Use Firestore (Current System):**
   - Save your credentials via Settings page
   - Error 808 fixed for your account
   - Other users need their own credentials

2. **Integrate Secret Manager (Platform-Wide):**
   - Store your credentials in Secret Manager
   - Modify `get_dhan_client_async()` for fallback
   - All users trade with your account

3. **Verify & Document (No Deploy):**
   - Test current Firestore flow end-to-end
   - Document credential paths
   - Plan migration strategy

---

## 📞 Urgent Questions

1. **Are all users trading with YOUR DhanHQ account?** (Single broker account)
2. **Or does each user have their own DhanHQ account?** (Multi-tenant)
3. **Should Secret Manager credentials be platform-wide defaults?**
4. **Is Firestore the permanent user credential storage?**

**Awaiting your decision to proceed with correct solution.**
