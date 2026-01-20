# Engine-C Deployment Status & Next Steps

**Date:** January 20, 2026  
**Status:** DEPLOYMENT IN PROGRESS  
**Build:** Cloud Build running (monorepo Dockerfile)

---

## ✅ Code Fixes Completed

### 1. Market Data Router (404 Fix)
- **File:** `backend/engine-c/src/main.py`
- **Change:** Registered `data_router` to mount `/api/dhan/market/*` endpoints
- **Impact:** Eliminates 404 errors on market quotes endpoint

### 2. Execution Analytics Alias (404 Fix)
- **File:** `backend/engine-c/src/main.py`
- **Change:** Added `/api/v1/execution/analytics` alias pointing to optimizer
- **Impact:** Frontend can now call analytics endpoint without 404

### 3. Credential Error Propagation (500→401 Fix)
- **Files:** `backend/engine-c/src/main.py` (orders, positions, holdings, funds endpoints)
- **Change:** Added `except HTTPException: raise` before generic exception handler
- **Impact:** 401 errors from credential lookup now surface to frontend instead of becoming 500s

### 4. Enhanced User ID Resolution
- **File:** `backend/engine-c/src/user_credentials.py`
- **Change:** Added Strategy 3 in `resolve_user_id()` to query by `user_id` field
- **Impact:** Better credential lookup for frontend-generated IDs like `user_1768893783541_3n0uc`

---

## 🔄 Current Deployment

**Method:** Cloud Build with `backend/engine-c/cloudbuild.yaml`  
**Dockerfile:** `backend/engine-c/Dockerfile.monorepo`  
**Command:**
```bash
gcloud builds submit . \
  --project=galvanic-pulsar-482815-h0 \
  --config=backend/engine-c/cloudbuild.yaml
```

**Build Status:** Running (Step #0 installing dependencies)

---

## 📋 Post-Deployment Tests

Once deployment completes, run these smoke tests:

```powershell
$ENGINE_C = "https://engine-c-228557716858.us-central1.run.app"
$USER_ID = "user_1768893783541_3n0uc"

# 1. Health Check
Invoke-RestMethod -Uri "$ENGINE_C/api/health"

# 2. Execution Analytics (should be 200, not 404)
$body = @{ orders = @() } | ConvertTo-Json
Invoke-RestMethod -Uri "$ENGINE_C/api/v1/execution/analytics" `
  -Method POST -Body $body -ContentType "application/json"

# 3. Market Quotes (should be 200, not 404)
Invoke-RestMethod -Uri "$ENGINE_C/api/dhan/market/quotes?security_ids=13,25&exchange_segment=IDX_I&user_id=$USER_ID"

# 4. Funds (should be 401 if creds not found, not 500)
Invoke-RestMethod -Uri "$ENGINE_C/api/dhan/funds?user_id=$USER_ID"

# 5. Positions
Invoke-RestMethod -Uri "$ENGINE_C/api/dhan/positions?user_id=$USER_ID"

# 6. Orders
Invoke-RestMethod -Uri "$ENGINE_C/api/dhan/orders?user_id=$USER_ID"
```

---

## ✅ Expected Results

| Endpoint | Before | After |
|----------|--------|-------|
| `/api/v1/execution/analytics` | 404 | 200 |
| `/api/dhan/market/quotes` | 404 | 200 or 401 |
| `/api/dhan/funds` (no creds) | 500 | 401 |
| `/api/dhan/positions` (no creds) | 500 | 401 |
| `/api/dhan/orders` (no creds) | 500 | 401 |

---

## 🔍 Credential Resolution Flow

1. Frontend submits credentials via settings page
2. Credentials saved to Firestore `dhan_credentials/{user_id}`
3. Backend `get_dhan_client_async()` attempts:
   - Direct lookup by `user_id` as document ID
   - If not found, call `resolve_user_id()`:
     - Try client_id scan (if numeric)
     - Try user_id field query (NEW)
4. If resolved, decrypt and return Dhan client
5. If not found, raise HTTP 401

---

## 🐛 If Tests Still Fail

### Market Quotes or Analytics still 404:
- Check Cloud Run logs for router registration messages:
  ```
  ✅ Dhan Market Data API endpoints enabled
  ✅ Execution Analytics compatible alias registered
  ```

### Funds/Positions/Orders still return 500:
- Check logs for credential resolution errors
- Verify Firestore `dhan_credentials` collection has document for user
- Check document structure (flat CamelCase vs nested snake_case)

### Credentials still not found (401):
1. Re-save credentials in frontend settings
2. Check Firestore directly:
   ```bash
   # Check if document exists
   gcloud firestore documents list dhan_credentials \
     --project=galvanic-pulsar-482815-h0
   ```
3. Check Cloud Run logs for resolution attempts:
   ```
   📍 Resolved user_id user_XXX via user_id field on document YYY
   ```

---

## 📊 Git Commits

1. `3797a6c4` - Mount market data router and improve credential error handling
2. `a5122499` - Update Dockerfile and add gcloudignore for Cloud Run builds

---

## ⏭️ Next Actions

1. **Wait** for Cloud Build to complete (~4 minutes)
2. **Run** smoke tests above
3. **Verify** logs in Cloud Run console
4. **Re-test** frontend with real user credentials
5. **Document** final results

---

**Last Updated:** During Cloud Build execution  
**Cloud Build ID:** TBD (check with `gcloud builds list`)
