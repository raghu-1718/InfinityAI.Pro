# Live Market End-to-End Testing Plan

**Project:** InfinityAI.Pro (galvanic-pulsar-482815-h0)
**Date:** January 20, 2026
**Status:** Market is LIVE - NSE/BSE Trading Hours

---

## 🎯 Testing Objective

Validate the entire trading platform stack from frontend → backend → broker → market data in real-time production conditions.

---

## 📋 Pre-Test Checklist

### ✅ Infrastructure Status

```powershell
# Check all deployed services
gcloud run services list --project=galvanic-pulsar-482815-h0 --region=us-central1 --format="table(SERVICE_NAME,URL,LAST_DEPLOYED)"

# Check Cloud Functions
gcloud functions list --project=galvanic-pulsar-482815-h0 --gen2 --region=us-central1 --format="table(NAME,STATE,UPDATE_TIME)"

# Check Cloud Scheduler jobs
gcloud scheduler jobs list --project=galvanic-pulsar-482815-h0 --location=us-central1 --format="table(ID,STATE,SCHEDULE)"

# Check Firestore indexes
gcloud firestore indexes list --project=galvanic-pulsar-482815-h0

# Check Secret Manager
gcloud secrets list --project=galvanic-pulsar-482815-h0 --format="table(NAME,CREATED,LABELS)"
```

### ✅ Build Status

```powershell
# Check current Cloud Build
gcloud builds list --project=galvanic-pulsar-482815-h0 --limit=3 --format="table(ID,STATUS,CREATE_TIME,SOURCE,IMAGES)"

# Get specific build logs
gcloud builds log 77f95b67-05b7-4bff-be14-f752ef45ef58 --project=galvanic-pulsar-482815-h0 2>&1 | Select-Object -Last 200
```

---

## 🧪 Test Scenarios

### 1️⃣ Frontend Accessibility Test

**Objective:** Verify the web app loads and authenticates.

```powershell
# Get frontend URL
$FRONTEND_URL = gcloud run services describe web-app --region=us-central1 --project=galvanic-pulsar-482815-h0 --format="value(status.url)" 2>&1
Write-Host "Frontend URL: $FRONTEND_URL" -ForegroundColor Green

# Test health endpoint (if exists)
curl "$FRONTEND_URL/api/health" -Method GET 2>&1 | ConvertFrom-Json
```

**Manual Steps:**

1. Open browser: Navigate to `$FRONTEND_URL`
2. Firebase Auth: Sign in with test user
3. Dashboard: Verify UI loads without errors
4. Browser Console: Check for JavaScript errors
5. Network Tab: Verify API calls succeed

**Expected:**

- ✅ Login successful
- ✅ Dashboard displays
- ✅ No console errors
- ✅ Ably connection established

---

### 2️⃣ Backend API Health Test

**Objective:** Validate Engine-C is running and responsive.

```powershell
# Get Engine-C URL
$ENGINE_C_URL = gcloud run services describe engine-c --region=us-central1 --project=galvanic-pulsar-482815-h0 --format="value(status.url)" 2>&1
Write-Host "Engine-C URL: $ENGINE_C_URL" -ForegroundColor Green

# Test health endpoint
curl "$ENGINE_C_URL/health" -Method GET 2>&1 | ConvertFrom-Json

# Test root endpoint
curl "$ENGINE_C_URL/" -Method GET 2>&1
```

**Expected:**

```json
{
  "status": "healthy",
  "service": "engine-c",
  "timestamp": "2026-01-20T07:10:00Z"
}
```

---

### 3️⃣ User Credential Resolution Test

**Objective:** Verify user credential lookup (recently fixed).

```powershell
# Test with a known user UID
$USER_ID = "raghuyuvi10"  # Replace with actual Firebase UID
$TOKEN = "ya29...."  # Get from Firebase Auth

curl "$ENGINE_C_URL/api/v1/user/$USER_ID/funds" `
  -Method GET `
  -Headers @{"Authorization"="Bearer $TOKEN"} 2>&1 | ConvertFrom-Json
```

**Expected:**

- ✅ Returns fund data (not 500 error)
- ✅ Dhan credentials resolved correctly
- ✅ Response within 2 seconds

---

### 4️⃣ Live Market Data Test

**Objective:** Confirm real-time market data ingestion.

```powershell
# Manually trigger market data publisher
gcloud scheduler jobs run market-data-publisher --location=us-central1 --project=galvanic-pulsar-482815-h0

# Check Firestore for latest quotes
# (Need to query Firestore via gcloud or Firebase console)
gcloud firestore documents list market_data --project=galvanic-pulsar-482815-h0 --limit=5
```

**Manual Firestore Check:**

1. Open Firebase Console → Firestore
2. Navigate to `market_data` collection
3. Verify recent documents (timestamp within last 5 minutes)
4. Check `quotes` subcollection for NSE symbols like NIFTY, BANKNIFTY

**Expected:**

- ✅ Documents with timestamp < 5 minutes old
- ✅ Live LTP (Last Traded Price) updates
- ✅ Volume and OI (Open Interest) data present

---

### 5️⃣ Dhan API Integration Test

**Objective:** Validate broker connectivity with live credentials.

```powershell
# Test positions endpoint (requires valid session)
curl "$ENGINE_C_URL/api/v1/user/$USER_ID/positions" `
  -Method GET `
  -Headers @{"Authorization"="Bearer $TOKEN"} 2>&1 | ConvertFrom-Json

# Test holdings endpoint
curl "$ENGINE_C_URL/api/v1/user/$USER_ID/holdings" `
  -Method GET `
  -Headers @{"Authorization"="Bearer $TOKEN"} 2>&1 | ConvertFrom-Json
```

**Expected:**

- ✅ Returns current positions/holdings
- ✅ No "credentials not found" errors
- ✅ Dhan client initialized successfully

---

### 6️⃣ Real-Time Quotes Test

**Objective:** Fetch live market quotes for NSE instruments.

```powershell
# Test quote endpoint
$SYMBOL = "NSE_EQ%7CINFY"  # URL-encoded NSE_EQ|INFY
curl "$ENGINE_C_URL/api/v1/quotes/$SYMBOL" `
  -Method GET `
  -Headers @{"Authorization"="Bearer $TOKEN"} 2>&1 | ConvertFrom-Json
```

**Expected:**

```json
{
  "symbol": "NSE_EQ|INFY",
  "ltp": 1523.45,
  "bid": 1523.4,
  "ask": 1523.5,
  "volume": 1234567,
  "timestamp": "2026-01-20T07:15:00Z"
}
```

---

### 7️⃣ Order Placement Test (PAPER TRADING ONLY)

**Objective:** Validate order placement WITHOUT executing real trades.

⚠️ **CRITICAL:** Only test in paper trading mode or with extreme caution.

```powershell
# Example: Place a TEST order (ensure Dhan is in paper/test mode)
$ORDER_PAYLOAD = @{
  symbol = "NSE_EQ|RELIANCE"
  quantity = 1
  transaction_type = "BUY"
  order_type = "LIMIT"
  price = 2500.00
  product_type = "INTRADAY"
} | ConvertTo-Json

curl "$ENGINE_C_URL/api/v1/user/$USER_ID/orders" `
  -Method POST `
  -Headers @{"Authorization"="Bearer $TOKEN"; "Content-Type"="application/json"} `
  -Body $ORDER_PAYLOAD 2>&1 | ConvertFrom-Json
```

**Expected:**

- ✅ Order accepted with order_id
- ✅ Order appears in Dhan dashboard (if paper trading)
- ✅ No real money moved

---

### 8️⃣ Ably Real-Time Streaming Test

**Objective:** Verify WebSocket data flow to frontend.

**Manual Steps:**

1. Open browser DevTools → Network → WS (WebSocket)
2. Filter for Ably connections
3. Observe incoming messages (market updates, order status)

**Expected:**

- ✅ Ably channel subscriptions active
- ✅ Market data updates every 1-5 seconds
- ✅ Order status updates on changes

---

### 9️⃣ End-to-End User Journey Test

**Objective:** Simulate a complete user workflow.

**Scenario:**

1. User logs in via Firebase Auth
2. Dashboard loads with live portfolio value
3. User navigates to "Trading" page
4. User views live quotes for NIFTY
5. User (optionally) places a paper trade
6. User receives real-time order confirmation via Ably
7. User checks "History" page for audit log

**Success Criteria:**

- ✅ No errors in browser console
- ✅ All API calls return < 2s
- ✅ Real-time data updates visible
- ✅ Audit trail logged in Firestore

---

### 🔟 Performance & Scaling Test

**Objective:** Validate system under concurrent load.

```powershell
# Check Cloud Run metrics
gcloud run services describe engine-c `
  --region=us-central1 `
  --project=galvanic-pulsar-482815-h0 `
  --format="value(status.traffic,status.conditions)"

# Monitor Cloud Run logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=engine-c" `
  --project=galvanic-pulsar-482815-h0 `
  --limit=50
```

**Load Test (Optional):**

```powershell
# Use Apache Bench or similar
ab -n 100 -c 10 "$ENGINE_C_URL/health"
```

**Expected:**

- ✅ Auto-scaling triggers if needed
- ✅ No 503/504 errors
- ✅ Cold start < 5 seconds

---

## 📊 Monitoring & Observability

### Cloud Logging

```powershell
# Real-time logs for engine-c
gcloud logging tail "resource.type=cloud_run_revision" `
  --project=galvanic-pulsar-482815-h0 `
  --filter="resource.labels.service_name=engine-c"

# Error logs only
gcloud logging tail "resource.type=cloud_run_revision AND severity>=ERROR" `
  --project=galvanic-pulsar-482815-h0
```

### Cloud Monitoring

1. Open [Google Cloud Console → Monitoring](https://console.cloud.google.com/monitoring?project=galvanic-pulsar-482815-h0)
2. Check dashboards for:
   - Cloud Run request latency
   - Cloud Run error rate
   - Firestore read/write operations
   - Cloud Functions invocations

### Ably Monitoring

1. Open [Ably Dashboard](https://ably.com/dashboard)
2. Check:
   - Active connections
   - Message throughput
   - Channel occupancy

---

## 🚨 Troubleshooting Guide

### Issue: Frontend 404/500 Errors

**Diagnosis:**

```powershell
# Check Cloud Build status
gcloud builds describe 77f95b67-05b7-4bff-be14-f752ef45ef58 --project=galvanic-pulsar-482815-h0 --format="value(STATUS)"

# Check Cloud Run deployment
gcloud run revisions list --service=web-app --region=us-central1 --project=galvanic-pulsar-482815-h0 --format="table(REVISION,STATUS,DEPLOYED)"
```

**Fix:**

- If build failed: Check logs, fix code, redeploy
- If deployment incomplete: Wait or trigger manual deploy

---

### Issue: "Credentials Not Found" Errors

**Diagnosis:**

```powershell
# Check Firestore user_credentials collection
gcloud firestore documents list user_credentials --project=galvanic-pulsar-482815-h0 --limit=5

# Check Secret Manager
gcloud secrets versions access latest --secret=dhan-client-id --project=galvanic-pulsar-482815-h0
```

**Fix:**

- Verify `user_credentials/{uid}/brokers/dhan` document exists
- Ensure `client_id` and `access_token` are valid
- Re-run credential verification script

---

### Issue: No Market Data Updates

**Diagnosis:**

```powershell
# Check scheduler job status
gcloud scheduler jobs describe market-data-publisher --location=us-central1 --project=galvanic-pulsar-482815-h0

# Check Cloud Function logs
gcloud functions logs read publishMarketData --region=us-central1 --project=galvanic-pulsar-482815-h0 --limit=50
```

**Fix:**

- Manually trigger: `gcloud scheduler jobs run market-data-publisher --location=us-central1 --project=galvanic-pulsar-482815-h0`
- Verify Dhan API keys in Secret Manager
- Check Firestore write permissions

---

## ✅ Test Results Template

### Test Execution Summary

| Test                    | Status     | Timestamp | Notes             |
| ----------------------- | ---------- | --------- | ----------------- |
| Frontend Load           | ⏳ Pending | -         | Waiting for build |
| Backend Health          | ⏳ Pending | -         | -                 |
| Credential Resolution   | ⏳ Pending | -         | -                 |
| Market Data Ingestion   | ⏳ Pending | -         | -                 |
| Dhan API Integration    | ⏳ Pending | -         | -                 |
| Real-Time Quotes        | ⏳ Pending | -         | -                 |
| Order Placement (Paper) | ⏳ Pending | -         | -                 |
| Ably Streaming          | ⏳ Pending | -         | -                 |
| E2E User Journey        | ⏳ Pending | -         | -                 |
| Performance Test        | ⏳ Pending | -         | -                 |

### Critical Metrics

- **Frontend Latency:** TBD
- **Backend Latency:** TBD
- **Market Data Lag:** TBD
- **Order Execution Time:** TBD
- **Error Rate:** TBD
- **Active Users:** TBD

---

## 🔒 Safety Reminders

### NEVER:

- ❌ Execute real trades without explicit confirmation
- ❌ Use production credentials in test environments
- ❌ Expose API keys in logs or screenshots
- ❌ Test with large order quantities in live market

### ALWAYS:

- ✅ Use paper trading mode for order tests
- ✅ Start with small position sizes
- ✅ Monitor error logs in real-time
- ✅ Have a rollback plan ready
- ✅ Verify market hours before testing live data

---

## 📞 Escalation Contacts

**Technical Issues:**

- Cloud Build Failures → Check build logs, review recent commits
- Firestore Errors → Verify indexes, check quotas
- Dhan API Errors → Check broker dashboard, verify credentials

**Regulatory/Compliance:**

- Trading Errors → Immediately halt, review audit logs
- Data Breaches → Rotate secrets, notify stakeholders

---

## 📝 Next Steps After Testing

1. **Document Results:** Update this file with actual test outcomes
2. **Fix Critical Bugs:** Address any failures immediately
3. **Performance Tuning:** Optimize based on metrics
4. **User Acceptance Testing:** Invite beta users if all tests pass
5. **Production Readiness Review:** Final checklist before go-live

---

**Prepared by:** GitHub Copilot (Principal Cloud Solutions Architect AI)
**Last Updated:** 2026-01-20 07:10 UTC
**Project Binding:** galvanic-pulsar-482815-h0
