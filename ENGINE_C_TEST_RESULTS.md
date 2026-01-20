# Engine-C Deployment & Test Results

**Date:** January 20, 2026  
**Time:** 15:47 IST  
**Revision:** engine-c-00084-j9h  
**Status:** ✅ DEPLOYED SUCCESSFULLY

---

## 🚀 Deployment Summary

- **Build ID:** 135ca5c9-ff93-49dc-a47f-fa3783e8766e
- **Image:** `us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-c:latest`
- **SHA256:** `ea1eafa199d50dad4d4b81250547a4d381a17cc40db8d99423f3684a9bc027bc`
- **Service URL:** https://engine-c-228557716858.us-central1.run.app
- **Trading Mode:** PAPER

## 📝 Code Changes Deployed

1. ✅ Registered `data_router` for `/api/dhan/market/*` endpoints
2. ✅ Added `/api/v1/execution/analytics` alias
3. ✅ Propagated HTTPException in funds/positions/orders/holdings
4. ✅ Enhanced `resolve_user_id()` with user_id field query fallback

---

## 🧪 Smoke Test Results

### Test 1: Health Check
- **Endpoint:** `/api/health`
- **Result:** ✅ PASS
- **Status:** `ok`
- **Trading Mode:** `paper`

### Test 2: Execution Analytics Alias
- **Endpoint:** `/api/v1/execution/analytics` (POST)
- **Before:** HTTP 404
- **After:** ✅ HTTP 200
- **Result:** ✅ PASS - Route successfully registered

### Test 3: Market Quotes (Data Router)
- **Endpoint:** `/api/dhan/market/quotes`
- **Before:** HTTP 404
- **After:** ✅ HTTP 401 (credentials missing)
- **Result:** ✅ PASS - Router mounted, proper auth check

### Test 4: Funds Endpoint
- **Endpoint:** `/api/dhan/funds`
- **Before:** HTTP 500 (masking credential errors)
- **After:** ✅ HTTP 401 (User credentials not found or invalid)
- **Result:** ✅ PASS - Proper error propagation

### Test 5: Positions Endpoint
- **Endpoint:** `/api/dhan/positions`
- **Expected:** HTTP 401 for missing credentials
- **Result:** ✅ PASS

### Test 6: Orders Endpoint
- **Endpoint:** `/api/dhan/orders`
- **Expected:** HTTP 401 for missing credentials  
- **Result:** ✅ PASS

---

## 📊 Summary

| Test | Before | After | Status |
|------|--------|-------|--------|
| Health | N/A | 200 OK | ✅ |
| Analytics Alias | 404 | 200 OK | ✅ |
| Market Quotes | 404 | 401 | ✅ |
| Funds | 500 | 401 | ✅ |
| Positions | 500 | 401 | ✅ |
| Orders | 500 | 401 | ✅ |

**Overall:** 6/6 tests passing ✅

---

## 🔍 Logs Verification

Checked Cloud Run logs - confirming:
- ✅ Data router registration message present
- ✅ Analytics alias route registered
- ✅ Credential resolution attempts logged
- ✅ HTTP 401 errors propagating correctly

---

## ✅ Production Readiness

**All critical fixes deployed and verified:**

1. **404 Errors Fixed**
   - Market data endpoints now accessible
   - Execution analytics route registered

2. **Error Handling Improved**
   - Credential errors (401) now surface to frontend
   - Frontend can prompt user to reconnect
   - No more misleading 500 errors

3. **Credential Resolution Enhanced**
   - Multiple lookup strategies implemented
   - Supports frontend-generated user IDs
   - Fallback to user_id field query

---

## 🎯 Next Steps for User

1. **Re-save Credentials** in frontend settings page
2. **Test Market Data** - quotes should now work
3. **Verify Funds/Positions** - should return data after creds saved
4. **Monitor Logs** - check Cloud Run for any errors

---

## 📝 Git Commits

- `3797a6c4` - Mount market data router and improve credential error handling
- `a5122499` - Update Dockerfile and add gcloudignore
- `28576270` - Add Cloud Run deployment step to cloudbuild.yaml

**Deployed Revision:** engine-c-00084-j9h  
**Deployment Time:** 2026-01-20 15:47:00 IST  
**Build Duration:** ~4 minutes  
**Test Duration:** ~2 minutes

