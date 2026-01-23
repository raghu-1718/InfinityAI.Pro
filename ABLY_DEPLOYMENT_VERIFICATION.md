# Ably Real-Time Integration - Deployment Verification Guide

**Status:** Deployments in progress
**Project:** galvanic-pulsar-482815-h0
**Deployment Date:** 2026-01-19

---

## 1. Deployment Architecture

### Security Model (Principle of Least Privilege)

```
┌─────────────────────────────────────────────────────────────┐
│                    GCP Secret Manager                       │
├─────────────────────┬───────────────────────────────────────┤
│ ably-api-key-root   │ Root key (Full capabilities)          │
│ (Backend publish)   │ qxp1Dw.Bhby1A:*** (stored securely)   │
├─────────────────────┼───────────────────────────────────────┤
│ ably-api-key-       │ Subscribe-only key (Read-only)        │
│ subscribe           │ qxp1Dw.ozz6rQ:*** (stored securely)   │
│ (Frontend read)     │                                       │
└─────────────────────┴───────────────────────────────────────┘
          ↓                              ↓
    Cloud Build                   Cloud Build
    (Root Key)                (Subscribe Key)
          ↓                              ↓
    Engine-C                       web-app
    (Publisher)                (Subscriber)
```

### Data Flow

```
Market Data             Engine-C                    Frontend
Source              (publisher)                   (subscriber)
  ↓                     ↓                             ↓
Cloud                Ably REST API              Ably WebSocket
Function         (ABLY_API_KEY=root)           (NEXT_PUBLIC_ABLY_API_KEY=subscribe)
                        ↓
                   Channel: infinityai:live-quotes
                        ↓
                  Published: <100ms
                        ↓
                    RealtimeDashboard
                    LiveMarketQuotes
                    PortfolioUpdates
                    TradingSignals
```

---

## 2. Deployed Components

### Frontend (web-app)

- **Service:** Cloud Run
- **Port:** 3000
- **Environment Variable:** `NEXT_PUBLIC_ABLY_API_KEY` (injected from Secret Manager)
- **Capability:** Subscribe-only (read real-time data)
- **Key Source:** `ably-api-key-subscribe:latest`
- **Components Using Ably:**
  - RealtimeDashboard (connection state indicator)
  - LiveMarketQuotes (market data display)
  - PortfolioUpdates (user portfolio changes)
  - TradingSignals (AI signals with confidence)

### Backend (Engine-C)

- **Service:** Cloud Run
- **Function:** Market data publisher
- **Environment Variable:** `ABLY_API_KEY` (injected from Secret Manager)
- **Capability:** Full publish/subscribe
- **Key Source:** `ably-api-key-root:latest`
- **Publisher Function:** `publishToAblyChannel()` in `/backend/shared/ably-publisher.ts`

---

## 3. Pre-Deployment Verification Checklist

### Cloud Build Configuration

- ✅ Frontend Cloud Build updated with `--set-secrets` for subscribe key
- ✅ Backend Cloud Build updated with `--set-secrets` for root key
- ✅ Project ID hardcoded: `galvanic-pulsar-482815-h0`
- ✅ Both use `gcloud` builder for secret injection support

### Secret Manager Setup

```bash
# Verify secrets exist and are accessible
gcloud secrets list --filter="name:(ably-api-key)" --project=galvanic-pulsar-482815-h0

# Verify Cloud Build service account has access
gcloud secrets get-iam-policy ably-api-key-root --project=galvanic-pulsar-482815-h0
gcloud secrets get-iam-policy ably-api-key-subscribe --project=galvanic-pulsar-482815-h0
```

### Frontend Readiness

- ✅ `src/lib/ably.ts` - Client singleton with auto-reconnect
- ✅ `src/contexts/AblyContext.tsx` - Global connection provider
- ✅ `src/hooks/useAbly.ts` - 8 specialized subscription hooks
- ✅ `src/components/providers.tsx` - AblyProvider wrapper integrated
- ✅ `next.config.ts` - Exposes `NEXT_PUBLIC_ABLY_API_KEY`
- ✅ Components ready: RealtimeDashboard, LiveMarketQuotes, PortfolioUpdates, TradingSignals

### Backend Readiness

- ✅ `backend/shared/ably-publisher.ts` - Publisher utility (192 lines)
- ✅ Functions: publishToAblyChannel(), publishMarketQuote(), etc.
- ✅ Channel definitions in `src/lib/ably.ts`:
  - infinityai:live-quotes
  - infinityai:trading-signals
  - infinityai:portfolio-update
  - infinityai:user-notifications
  - infinityai:portfolio:{userId}
  - infinityai:engine:{engineId}
  - infinityai:system-status

---

## 4. Post-Deployment Verification Steps

### Step 1: Check Deployments Status

```powershell
# Frontend deployment
gcloud run services describe web-app --region us-central1 --project galvanic-pulsar-482815-h0

# Backend deployment
gcloud run services describe engine-c --region us-central1 --project galvanic-pulsar-482815-h0
```

### Step 2: Verify Environment Variables Injected

```powershell
# Frontend - should show NEXT_PUBLIC_ABLY_API_KEY (will be masked)
gcloud run services describe web-app --region us-central1 --project galvanic-pulsar-482815-h0 | grep -A 5 "environment"

# Backend - should show ABLY_API_KEY (will be masked)
gcloud run services describe engine-c --region us-central1 --project galvanic-pulsar-482815-h0 | grep -A 5 "environment"
```

### Step 3: Test Frontend Ably Connection

1. Open web-app in browser: `https://web-app-[hash].us-central1.run.app`
2. Open DevTools Console (F12)
3. Look for: **"✅ Ably connected successfully"**
4. Check RealtimeDashboard component:
   - Should show: "Live" indicator (green)
   - Should show: Connection state transitions
   - Should show: Message event feed

### Step 4: Test Message Publishing

```bash
# Publish test market data to Ably channel
curl -X POST https://rest.ably.io/channels/infinityai:live-quotes/publish \
  -H "Authorization: Basic $(echo -n 'qxp1Dw.Bhby1A:hVwzJAMcoYo63kpymX6EIs8g7plmBGYG8Wk5r3qBXYU' | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "market-data",
    "data": {
      "symbol": "BTC",
      "price": 95000,
      "bid": 94950,
      "ask": 95050,
      "timestamp": "2026-01-19T17:00:00Z"
    }
  }'
```

### Step 5: Monitor Real-Time Message Flow

1. Frontend receives test message on `infinityai:live-quotes` channel
2. RealtimeDashboard updates in real-time
3. LiveMarketQuotes component displays: BTC 95000
4. Latency should be <100ms

### Step 6: Verify Error Handling

1. Stop backend service: Observe frontend "Reconnecting..." state
2. Resume backend: Observe "Connected" transition
3. Verify reconnection logic works (auto-reconnect after 15 seconds)

### Step 7: Check Cloud Logs

```bash
# Frontend logs (look for Ably connection messages)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=web-app" \
  --limit 50 --project galvanic-pulsar-482815-h0

# Backend logs (look for published messages)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=engine-c" \
  --limit 50 --project galvanic-pulsar-482815-h0
```

---

## 5. Integration Test Scenarios

### Scenario A: Live Market Data

**Expected Flow:**

```
Market Data → Engine-C (publishes to infinityai:live-quotes)
            → Ably Channel → Frontend subscribed
            → RealtimeDashboard & LiveMarketQuotes update
```

**Verification:**

- [ ] RealtimeDashboard shows live connection
- [ ] LiveMarketQuotes displays real-time prices
- [ ] Message latency < 100ms
- [ ] Price updates appear instantly on UI

### Scenario B: Trading Signals

**Expected Flow:**

```
Engine-C (AI analysis) → publishes to infinityai:trading-signals
                       → Ably Channel → Frontend subscribed
                       → TradingSignals component updates
```

**Verification:**

- [ ] TradingSignals component displays signals with confidence
- [ ] Engine filter works (Engine-A, B, C specific)
- [ ] Signals appear with <1 second latency

### Scenario C: Portfolio Updates

**Expected Flow:**

```
Trade Execution → publishes to infinityai:portfolio:{userId}
                → Ably Channel (user-specific)
                → Frontend subscribed (userId match)
                → PortfolioUpdates component reflects changes
```

**Verification:**

- [ ] Portfolio value updates in real-time
- [ ] P&L calculations reflect new positions
- [ ] Only user's own portfolio updates visible
- [ ] New trades appear instantly in portfolio

### Scenario D: Connection Resilience

**Test:** Simulate network interruption

```
1. Open DevTools → Network → Offline
2. Observe: "Reconnecting..." indicator
3. Wait 15 seconds
4. Online: Network → Online
5. Observe: "Connected" indicator restored
```

**Verification:**

- [ ] Automatic reconnection after 15 seconds
- [ ] Messages during offline are queued (if applicable)
- [ ] UI state recovers gracefully

---

## 6. Troubleshooting Guide

### Issue: "Ably connection failed"

**Root Causes:**

- Subscribe key not injected (check Cloud Build logs)
- Ably service down (check Ably status page)
- Network/CORS issue

**Resolution:**

```bash
# Check Cloud Build step logs
gcloud builds log [BUILD_ID] --project=galvanic-pulsar-482815-h0

# Verify secret is accessible
gcloud secrets versions access latest --secret="ably-api-key-subscribe" --project=galvanic-pulsar-482815-h0
```

### Issue: "NEXT_PUBLIC_ABLY_API_KEY is undefined"

**Root Causes:**

- `--set-secrets` flag not working in Cloud Run deployment
- Environment variable name mismatch

**Resolution:**

```bash
# Check deployed service environment variables
gcloud run services describe web-app --region us-central1 --project galvanic-pulsar-482815-h0

# Check for secret injection errors in build logs
gcloud builds log [BUILD_ID] --project=galvanic-pulsar-482815-h0 | grep -i secret
```

### Issue: "Messages not received on frontend"

**Root Causes:**

- Channel name mismatch (check `ABLY_CHANNELS` object)
- Subscription not started
- Backend not publishing

**Resolution:**

```bash
# Test manual subscription
# In browser console:
// Copy from useMarketData hook
const market = useMarketData();
console.log("Subscribed to market data:", market.data);

# Test manual publish from backend
curl -X POST https://rest.ably.io/channels/infinityai:live-quotes/publish \
  -H "Authorization: Basic [base64 root key]" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","data":{"msg":"hello"}}'
```

### Issue: "Latency >100ms"

**Root Causes:**

- Network latency
- Browser performance
- Component re-render overhead

**Resolution:**

```bash
# Check Ably metrics via dashboard
# Monitor Cloud Run service metrics in GCP Console
# Profile React components with React DevTools Profiler
```

---

## 7. Rollback Plan

### If deployment fails:

```bash
# Revert frontend
gcloud run deploy web-app \
  --source=[previous-working-image] \
  --region us-central1 \
  --project=galvanic-pulsar-482815-h0

# Revert backend (Engine-C)
gcloud run deploy engine-c \
  --source=[previous-working-image] \
  --region us-central1 \
  --project=galvanic-pulsar-482815-h0
```

### Secrets remain safe:

- Both keys stored in Secret Manager
- Can be reused in next deployment
- No credential rotation needed unless compromised

---

## 8. Success Criteria

✅ **Frontend Deployment:**

- Web-app Cloud Run service running
- NEXT_PUBLIC_ABLY_API_KEY injected from Secret Manager
- Ably connection established in browser console
- RealtimeDashboard shows "Live" indicator

✅ **Backend Deployment:**

- Engine-C Cloud Run service running
- ABLY_API_KEY injected from Secret Manager
- Can publish to Ably channels
- Messages appear in frontend components <100ms

✅ **End-to-End Flow:**

- Market data flows: Engine-C → Ably → Frontend
- Trading signals appear with confidence levels
- Portfolio updates reflect in real-time
- Connection recovers automatically after interruption

✅ **Production Readiness:**

- All components deployed to us-central1
- Secrets secured in Secret Manager
- No credentials in logs or console output
- Monitoring and alerting configured

---

## 9. Next Steps

1. **Monitor Build Progress:**

   ```bash
   gcloud builds log [BUILD_ID] --stream --project=galvanic-pulsar-482815-h0
   ```

2. **Verify Deployments:**
   - Execute verification steps from Section 4

3. **Run Integration Tests:**
   - Execute test scenarios from Section 5

4. **Monitor Production:**
   - Check Cloud Logging for errors
   - Monitor latency metrics
   - Set up alerts for connection failures

5. **Document Issues:**
   - Log any anomalies for future reference
   - Update troubleshooting guide as needed

---

## 10. Build Status Tracking

### Frontend Build

- **Status:** In Progress
- **Command:** `gcloud builds submit --project=galvanic-pulsar-482815-h0 --config=cloudbuild.yaml`
- **Expected Duration:** 5-10 minutes
- **Outputs:**
  - Docker image pushed to Artifact Registry
  - Cloud Run service updated with subscribe key

### Backend Build

- **Status:** In Progress
- **Command:** `gcloud builds submit --project=galvanic-pulsar-482815-h0 --config=cloudbuild-deploy.yaml`
- **Expected Duration:** 10-15 minutes
- **Outputs:**
  - Docker images for Engine-A, B, C
  - Cloud Run services updated with root key

---

**Document Version:** 1.0
**Last Updated:** 2026-01-19 17:40 UTC
**Created By:** GitHub Copilot (Cloud Solutions Architect)
