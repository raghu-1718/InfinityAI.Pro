# Critical System Audit & Fix Plan
**Project:** InfinityAI.Pro / galvanic-pulsar-482815-h0
**Date:** January 9, 2026
**Status:** Issues Identified, Fix Strategy Ready

---

## Executive Summary

The application has multiple interconnected issues affecting user experience and trading functionality:

1. ✅ **Engine-B is actually ONLINE** (cloud logs show 200 OK health checks)
   - Issue: Frontend health check logic incorrectly marks it as offline
   - Root cause: Response parsing or status comparison logic
   - Impact: Dashboard shows "System Degraded" instead of "All Engines Online"

2. ❌ **Dhan Credentials:** Uncertain if persisted in backend
   - Settings shows "Connected + Verified" but unclear if credentials stored
   - Real-time feeds not working (WebSocket or Dhan webhook issue)

3. ❌ **Trading Page Shows "STOP TRADING"** without user starting
   - Indicates session state initialization issue
   - Possible: Session persists from previous interaction or wrong initial state

4. ❌ **Currency Display:** Shows `$` (USD) instead of `₹` (INR)
   - Affects all balance displays, P&L, orders
   - Multiple components need currency symbol update

5. ❌ **Asset Classes:** Hardcoded placeholders
   - Currently using mock/placeholder config
   - Need to validate integration with Dhan API and market data

6. ⚠️ **Real-Time Feeds:** Not receiving events
   - WebSocket connection shows "Live" but "0 events received"
   - Need to verify: Dhan webhook, event broadcasting, subscription

7. ⚠️ **Trading Mode:** Application mentions "paper trading" in docs
   - Unclear if currently in paper or live mode
   - Risk: Live orders could be placed unintentionally

---

## Issues Breakdown & Fixes

### Issue 1: Engine-B Shows Offline (Dashboard)

**Current State:**
```
Cloud Logs: ✅ GET /api/health → 200 OK  (Engine-B is healthy)
Frontend:   ❌ enginesState.engineB.status = 'offline'  (shown as degraded)
```

**Root Cause Analysis:**
- `useEngineHealth()` calls `api.checkAllEngines()`
- `Promise.allSettled()` returns health responses
- Status updated in store: `status: engineB ? 'online' : 'offline'`
- Condition `if (engineB)` evaluates truthy object as online ✓
- **Possible Issue:** Response structure changed, or fetch error caught silently

**Fix:**
- Add detailed logging to health check response
- Validate response structure matches expected schema
- Add fallback to treat non-null health response as online

**Files to Update:**
- `frontend/web-app/src/hooks/useApi.ts` - Add logging and robust checks
- `frontend/web-app/src/lib/api.ts` - Validate response schema

---

### Issue 2: Dhan Credentials Not Persisting

**Current State:**
```
Settings: Shows "Status: CONNECTED ✓ Verified"
Backend: Unclear if stored in Firestore or Secret Manager
```

**Verification Steps:**
1. Check Firestore `user_credentials` collection
2. Check Cloud Secret Manager for stored tokens
3. Verify `storeUserCredentials` Cloud Function executes
4. Verify `getUserCredentials` retrieves from backend

**Fix:**
- Ensure `Settings` page calls backend to persist credentials
- Verify `storeUserCredentials` Cloud Function saves to both Firestore AND Secret Manager
- Add validation that credentials are accessible after save

**Files to Check:**
- `frontend/functions/src/userCredentials.ts` - Credential storage
- `backend/engine-c/...` - Dhan credential management endpoints
- Firestore rules - Read/write permissions on `user_credentials` collection

---

### Issue 3: Trading Page Shows "STOP TRADING" on Load

**Current State:**
```
User Action: Did NOT click "Start Trading"
Page Load: Shows "STOP TRADING" button (indicates session.isActive = true)
```

**Root Cause:**
- Trading session state persists from previous interaction
- OR session initialization defaults to `isActive: true`
- OR localStorage persists session state

**Fix:**
- Clear trading session state on component mount
- Verify initial state is `isActive: false`
- Check localStorage for stale session data

**Files to Update:**
- `frontend/web-app/src/app/(dashboard)/trading/page.tsx` - Trading session logic

---

### Issue 4: Currency Display ($ instead of ₹)

**Current State:**
```
Components show: "$0.00" (USD)
Should show: "₹0.00" (Indian Rupee)
```

**Scope:**
- Account Overview cards (Available Balance, Holdings Value, P&L)
- Account Details (Funds breakdown)
- Trading interface (Capital, Profits/Losses)
- Order displays
- Historical P&L

**Fix:**
- Create `CurrencySymbol` constant: `₹`
- Replace all `$` with `₹` in display components
- Update number formatting for Indian locale (space as thousand separator)

**Files to Update:**
- `frontend/web-app/src/components/AccountSummary.tsx`
- `frontend/web-app/src/app/(dashboard)/trading/page.tsx`
- `frontend/web-app/src/app/(dashboard)/page.tsx`
- All other financial display components

---

### Issue 5: Real-Time Feeds Not Working

**Current State:**
```
Dashboard: "Real-Time Connection: Live"
Event Count: "0 events received"
Expected: Live trade notifications from Dhan
```

**Root Cause Options:**
1. WebSocket connection not authenticated properly
2. Dhan webhook not configured correctly
3. Event broadcasting not implemented
4. Subscription not receiving events

**Verification:**
- Check WebSocket connection to Engine-C
- Verify Dhan webhook URL in Engine-C configuration
- Check Engine-C logs for webhook events
- Verify event broadcast mechanism

**Fix:**
- Implement proper WebSocket authentication
- Verify Dhan postback URL and webhook signature
- Add event logging for debugging
- Implement fallback polling if WebSocket fails

**Files to Check:**
- `backend/engine-c/...` - Dhan webhook handlers
- `frontend/web-app/src/components/RealtimeDashboard.tsx` - WebSocket subscription

---

### Issue 6: Asset Classes Configuration

**Current State:**
```
NIFTY 50 selected (hardcoded)
"Trading instruments" config appears as placeholder
```

**Verification:**
- Check if asset class selection from Settings is persisted
- Verify Engine-C respects asset class preference
- Verify signals are generated only for selected instruments

**Fix:**
- Validate asset class storage in Firestore/localStorage
- Verify Engine-C reads asset class configuration
- Test signal generation for different asset classes

**Files to Check:**
- `frontend/web-app/src/lib/store.ts` - Asset class state
- `backend/engine-b/src/main.py` - Asset class configuration
- `backend/engine-c/...` - Asset class handling

---

### Issue 7: Paper vs Live Trading Mode

**Current State:**
```
Unclear if application is in paper or live mode
Dhan credentials could execute live trades
```

**Critical Check:**
- Are orders being submitted to Dhan or mocked?
- Are real capital being risked?
- What's the trading mode configuration?

**Fix:**
- Implement explicit trading mode flag
- Add "PAPER MODE" badge if in paper mode
- Verify mode is set to PAPER by default
- Require explicit user confirmation to enable LIVE mode

**Files to Update:**
- `frontend/web-app/src/lib/store.ts` - Add trading mode state
- `backend/engine-c/...` - Add mode check before order execution
- `frontend/web-app/src/app/(dashboard)/trading/page.tsx` - Display mode badge

---

## Fix Priority & Sequencing

### Phase 1 (Immediate - High Impact)
1. **Fix Engine-B health check** (5 min)
   - Add logging and validation
   - Should immediately show all engines online

2. **Fix trading session state** (10 min)
   - Clear session on page load
   - Set default to `isActive: false`

3. **Fix currency display** (20 min)
   - Replace all `$` with `₹`
   - Update number formatting

### Phase 2 (Important - User Experience)
4. **Verify Dhan credential persistence** (15 min)
   - Check Firestore and Secret Manager
   - Validate retrieval in backend

5. **Fix real-time feeds** (30 min)
   - Debug WebSocket/webhook
   - Add event logging

6. **Verify asset class configuration** (20 min)
   - Test different instruments
   - Validate signal generation

### Phase 3 (Critical Safety)
7. **Implement trading mode toggle** (30 min)
   - Add PAPER/LIVE badge
   - Require confirmation for live
   - Default to PAPER mode

### Phase 4 (Testing & Deployment)
8. **End-to-end testing** (45 min)
   - Test all flows
   - Verify logs
   - Deploy

---

## Testing Checklist

After fixes applied:

- [ ] Dashboard shows "3 Engines Online" (not "System Degraded")
- [ ] Settings shows "Dhan: Connected + Verified"
- [ ] Account Overview displays balances in `₹` format
- [ ] Trading page shows "START TRADING" button on load
- [ ] Real-Time Connection receives events (or shows 0 with "waiting...")
- [ ] Asset class selection persists across page loads
- [ ] Trading mode shows "PAPER MODE" badge
- [ ] No actual orders placed without user action
- [ ] Cloud logs show no errors

---

## Estimated Time

- **Phase 1:** 35 minutes
- **Phase 2:** 65 minutes
- **Phase 3:** 30 minutes
- **Phase 4:** 45 minutes
- **Total:** ~3 hours for complete audit + fixes + deployment

---

## Implementation Status

- [x] Issue identification complete
- [x] Root cause analysis complete
- [x] Fix plan created
- [ ] Fixes applied
- [ ] Testing completed
- [ ] Deployment ready

---

Next: Begin Phase 1 fixes with Engine-B health check validation.
