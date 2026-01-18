# 🔧 COMPLETE FIX PLAN - InfinityAI.Pro System Recovery

## Issues Identified & Fixes

### 1. **CRITICAL: Firebase Auth Misconfiguration** ✅ FIXED
**Problem**: `.env.local` pointed to wrong Firebase project (`gen-lang-client-0779271931`)
**Status**: FIXED - Updated to correct project `galvanic-pulsar-482815-h0`
**Action**: Restart dev server and clear browser cache

### 2. **HTTP 500 on getFunds (Backend)**
**Problem**: Engine C returns 500 when user has no Dhan credentials
**Root Cause**: `get_dhan_client_async` throws 401, but exception handler re-throws as 500
**Fix Required**: Engine C should return 401 when credentials missing (already implemented)

### 3. **HTTP 500 on getFunds (Frontend)**
**Problem**: Frontend calls `/api/dhan/funds?user_id={userId}` without checking credentials first
**Fix Required**: Add graceful degradation for missing credentials

### 4. **Session State Permissions Still Failing**
**Problem**: Firestore rule changes deployed but may not have propagated
**Status**: Waiting for index to build (uid/timestamp index is CREATING)

---

## Implementation Steps

### Step 1: Clear Browser Cache & Restart Dev Server

```bash
# Kill running dev server (Ctrl+C)
npm run dev
```

Browser: **Ctrl+Shift+Delete** → Select "All time" → Clear cookies/cache

### Step 2: Verify Firebase Config Updated

```bash
# Check .env.local was updated
cat frontend/web-app/.env.local | grep FIREBASE
```

Expected output:
```
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyD_y3lIPm7bTEXy3Uy4deGTnZPpjr2A8B8
NEXT_PUBLIC_FIREBASE_PROJECT_ID=galvanic-pulsar-482815-h0
```

### Step 3: Fix Engine C Error Handling (Optional - only if 500 persists)

If `/api/dhan/funds` still returns 500, update Engine C's getFunds endpoint:

**File**: `backend/engine-c/src/main.py` (line 1594)

```python
@app.get("/api/dhan/funds")
async def get_funds(user_id: Optional[str] = None):
    """
    Fetch available funds and margin details from DhanHQ.
    Returns 401 if user has no credentials (client should prompt connect)
    """
    try:
        if user_id:
            dhan_client = await get_dhan_client_async(user_id)
        else:
            dhan_client = get_dhan_client()
        response = dhan_client.get_fund_limits()

        if isinstance(response, dict) and response.get("status") == "success":
            fund_data = response.get("data", {})
            return {
                "status": "success",
                "data": fund_data,
                "summary": {
                    "available_balance": fund_data.get("availabelBalance", 0),
                    "utilized_margin": fund_data.get("utilizedMargin", 0),
                    "payin_amount": fund_data.get("payinAmount", 0),
                    "withdrawal_available": fund_data.get("withdrawableBalance", 0)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        return {"status": "success", "data": response}

    except HTTPException as he:
        # Pass through 401 credential errors as-is
        raise he
    except Exception as e:
        logger.error(f"Failed to fetch funds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch funds: {str(e)}")
```

### Step 4: Check Firestore Index Build Status

```bash
gcloud firestore indexes composite list --project=galvanic-pulsar-482815-h0 | grep -i "uid"
```

Expected: `STATE: READY` (wait max 5 minutes)

### Step 5: Test Login Flow

1. Go to `http://localhost:3000`
2. Click "Sign In with Google"
3. Should NOT see "auth/requests-from-referer-http://localhost:3000-are-blocked"
4. Complete two-factor verification

### Step 6: Connect Dhan Account

1. Navigate to Settings → Dhan Connection
2. Enter valid Dhan access token
3. Click "Verify Connection"
4. `getFunds` should work (if not, check Engine C error handling)

---

## Expected Timeline

| Phase | Time | Status |
|-------|------|--------|
| Firebase config fix applied | ✅ Now | COMPLETE |
| Browser cache cleared | ⏳ User action | PENDING |
| Dev server restarted | ⏳ User action | PENDING |
| Login works | ⏳ After restart | PENDING |
| Firestore index builds | ⏳ 2-5 min | IN PROGRESS |
| Session state works | ⏳ After index | PENDING |
| getFunds works | ⏳ After credentials | PENDING |

---

## Verification Checklist

- [ ] Firebase login works without COOP/referer errors
- [ ] Session state stream shows no "missing permissions" errors
- [ ] Dhan connection page shows account is connected (after credentials saved)
- [ ] getFunds returns 200 OK (instead of 500)
- [ ] Order history loads
- [ ] Dashboard shows available balance

---

## Support Escalation

If any step fails:
1. Check browser console for exact error messages
2. Check Engine C logs: `gcloud run services logs read engine-c`
3. Check Cloud Functions logs: `firebase functions:log`
4. Verify Firestore indexes are READY: `gcloud firestore indexes composite list`
