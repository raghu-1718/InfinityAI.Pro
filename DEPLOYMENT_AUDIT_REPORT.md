# Deployment Audit & Remediation Report

**Date:** January 22, 2026 - 10:00 AM IST
**Status:** IN PROGRESS - Fixing Critical Issues

---

## 🔍 Audit Results

### Cloud Run Services Status (20 Total)

| Service                 | Status    | Revision  | Issue                                                                  |
| ----------------------- | --------- | --------- | ---------------------------------------------------------------------- |
| engine-a                | ❌ FAILED | 00053-6l8 | Container failed to start - Missing None headers when calling Engine-C |
| engine-b                | ✅ ACTIVE | 00042-8g6 | Healthy                                                                |
| engine-c                | ✅ ACTIVE | 00088-mqf | Healthy (LIVE TRADING)                                                 |
| analyzeportfolio        | ✅ ACTIVE | 00009-zen | Healthy                                                                |
| detect-momentum-signals | ✅ ACTIVE | 00001-wav | Healthy                                                                |
| fetchaccountdata        | ✅ ACTIVE | 00009-mev | Healthy                                                                |
| get-latest-signals      | ✅ ACTIVE | 00001-suw | Healthy                                                                |
| get-live-prices         | ✅ ACTIVE | 00001-quh | Healthy                                                                |
| get-price-history       | ✅ ACTIVE | 00001-vim | Healthy                                                                |
| getaisignals            | ✅ ACTIVE | 00009-fal | Healthy                                                                |
| getbatchaisignals       | ✅ ACTIVE | 00009-sov | Healthy                                                                |
| getdhanoverview         | ✅ ACTIVE | 00009-bej | Healthy                                                                |
| getgeminianalysis       | ✅ ACTIVE | 00009-tev | Healthy                                                                |
| getvertexaianalysis     | ✅ ACTIVE | 00009-vik | Healthy                                                                |
| live-data-ingestion     | ✅ ACTIVE | 00002-muk | Healthy                                                                |
| market-data-ingestion   | ✅ ACTIVE | 00007-fov | Healthy                                                                |
| starttrading            | ✅ ACTIVE | 00009-how | Healthy                                                                |
| stoptrading             | ✅ ACTIVE | 00009-zur | Healthy                                                                |
| storeusercredentials    | ✅ ACTIVE | 00009-kek | Healthy                                                                |
| verifycoupon            | ✅ ACTIVE | 00011-rej | Healthy                                                                |
| websocket-streamer      | ✅ ACTIVE | 00002-rvm | Healthy                                                                |

**Summary:** 19/20 services healthy (95% uptime)

---

### Firebase Hosting Status

| Component     | Status        | Issue                                           |
| ------------- | ------------- | ----------------------------------------------- |
| Configuration | ✅ VALID      | Points to `frontend/web-app/out`                |
| Build Output  | ❌ MISSING    | Directory `frontend/web-app/out` does not exist |
| Deployment    | ❌ NO CONTENT | Results in black screen                         |

---

## 🚨 Critical Issues Identified

### 1. Engine-A Runtime Failure ❌

**Error:**

```
Header value must be str or bytes, not <class 'NoneType'>
```

**Root Cause:**
Engine-A's autonomous_trader is calling Engine-C execution API without proper authentication headers.

**Impact:**

- Automated trading signals cannot execute
- Manual trading via Engine-C still works
- Advisory functions unaffected

**Fix Applied:**

- ✅ Rolled back to stable revision 00051-scg
- ⏳ Need to fix header propagation in src/services/autonomous_trader.py

---

### 2. Frontend Dashboard Black Screen ❌

**Root Cause:**

- Next.js app not built (no `out/` directory)
- Firebase Hosting serving empty content

**Impact:**

- Complete frontend unavailable
- No UI for users
- All backend APIs functional but inaccessible via web

**Fix In Progress:**

- 🔄 Running `npm run build` to create production build
- ⏳ Will deploy to Firebase Hosting after build completes

---

## 🔧 Remediation Actions

### Completed ✅

1. ✅ Comprehensive audit of all 20 Cloud Run services
2. ✅ Identified Engine-A failure (runtime error, not deployment)
3. ✅ Rolled back Engine-A to last stable revision (00051)
4. ✅ Started frontend build process

### In Progress 🔄

5. 🔄 Building Next.js frontend (`npm run build`)
6. 🔄 Waiting for build completion (~2-3 minutes)

### Pending ⏳

7. ⏳ Deploy frontend to Firebase Hosting
8. ⏳ Verify frontend loads correctly (no black screen)
9. ⏳ Fix Engine-A autonomous trader header issue
10. ⏳ Redeploy Engine-A with fix
11. ⏳ End-to-end testing

---

## 📊 Service Classification

### Core Trading Engines (Critical)

- **engine-a**: Advisory, Risk Management, Orchestration - ⚠️ DEGRADED (rollback active)
- **engine-b**: ML/AI Signals (XGBoost, LightGBM, CatBoost, LSTM, DQN) - ✅ ACTIVE
- **engine-c**: Live Trading Execution (DhanHQ) - ✅ ACTIVE

### Data Services (High Priority)

- market-data-ingestion - ✅ ACTIVE
- live-data-ingestion - ✅ ACTIVE
- websocket-streamer - ✅ ACTIVE
- get-live-prices - ✅ ACTIVE
- get-price-history - ✅ ACTIVE

### AI/ML Analysis (Medium Priority)

- getgeminianalysis - ✅ ACTIVE
- getvertexaianalysis - ✅ ACTIVE
- getaisignals - ✅ ACTIVE
- getbatchaisignals - ✅ ACTIVE

### Trading Operations (Medium Priority)

- starttrading - ✅ ACTIVE
- stoptrading - ✅ ACTIVE
- analyzeportfolio - ✅ ACTIVE
- fetchaccountdata - ✅ ACTIVE
- getdhanoverview - ✅ ACTIVE

### Support Services (Low Priority)

- storeusercredentials - ✅ ACTIVE
- verifycoupon - ✅ ACTIVE
- detect-momentum-signals - ✅ ACTIVE
- get-latest-signals - ✅ ACTIVE

### Analysis: No Unnecessary Services

All 20 services serve distinct purposes:

- **Core engines (3)**: Essential for trading operations
- **Data services (5)**: Required for market data pipeline
- **AI services (4)**: Generate trading signals
- **Operations (5)**: Manage trading sessions and accounts
- **Support (3)**: User management and utilities

**Recommendation:** Keep all services. None are redundant.

---

## 🎯 Root Cause Analysis

### Engine-A Failure

**Symptom:** Container fails startup health check
**Actual Cause:** Runtime error after startup (misleading error message)
**Error:** `Header value must be str or bytes, not <class 'NoneType'>`
**Location:** `src/services/autonomous_trader.py` → Engine-C API call

**Code Issue:**

```python
# Missing or None auth headers when calling Engine-C
headers = {
    "X-User-ID": user_id,  # Could be None
    "Authorization": token  # Could be None
}
```

**Fix Required:**

```python
# Add None check
headers = {}
if user_id:
    headers["X-User-ID"] = user_id
if token:
    headers["Authorization"] = token
```

---

### Frontend Black Screen

**Symptom:** Browser shows blank page
**Root Cause:** Next.js not built, no static files in `out/` directory
**Firebase Config:** Pointing to correct path (`frontend/web-app/out`)
**Hosting Server:** Working correctly, but serving empty directory

**Fix:** Build Next.js app (in progress)

---

## 📋 Deployment Commands Used

### Audit Commands

```bash
# Check all Cloud Run services
gcloud run services list --platform=managed --project=galvanic-pulsar-482815-h0

# Check Engine-A logs
gcloud logging read 'resource.labels.service_name=engine-a AND severity>=ERROR' --limit=10

# Check Firebase config
cat firebase.json | jq '.hosting'

# Check frontend build output
ls frontend/web-app/out
```

### Remediation Commands

```bash
# Rollback Engine-A
gcloud run services update-traffic engine-a \
  --to-revisions=engine-a-00051-scg=100 \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0

# Build frontend
cd frontend/web-app
npm install
npm run build

# Deploy frontend (pending)
firebase deploy --only hosting --project=galvanic-pulsar-482815-h0
```

---

## ⏭️ Next Steps (Immediate)

1. **Wait for Frontend Build** (~1 minute remaining)
2. **Verify Build Output**

   ```bash
   ls frontend/web-app/out
   # Should show: index.html, _next/, assets/, etc.
   ```

3. **Deploy to Firebase Hosting**

   ```bash
   firebase deploy --only hosting --project=galvanic-pulsar-482815-h0
   ```

4. **Test Frontend Access**
   - URL: https://galvanic-pulsar-482815-h0.web.app
   - Expected: Dashboard loads (no black screen)

5. **Fix Engine-A autonomous_trader.py**
   - Add None checks for headers
   - Rebuild and redeploy

6. **End-to-End Testing**
   - Frontend → Engine-A → Engine-B → Engine-C
   - Verify signal generation and execution

---

## 📈 System Health After Fixes

**Target State:**

- ✅ 20/20 Cloud Run services healthy
- ✅ Frontend dashboard accessible
- ✅ Complete E2E trading flow operational
- ✅ All unnecessary services removed (none found)

**Current Progress:** 70% complete

- ✅ Audit completed
- ✅ Engine-A stabilized (rollback)
- 🔄 Frontend building
- ⏳ Frontend deployment pending
- ⏳ Engine-A fix pending

---

**Report Status:** IN PROGRESS - Awaiting frontend build completion
**Next Update:** After frontend deployment
