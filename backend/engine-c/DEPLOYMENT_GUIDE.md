# Deployment Guide: Real-Time Trading Engine

## Pre-Deployment Checklist

✅ **Code Changes Completed**

- ✅ realtime_enhancements.py created (250+ lines)
- ✅ main.py updated with imports
- ✅ Startup event initialization added
- ✅ Postback handler enhanced with Firestore storage
- ✅ SSE endpoint added: `/api/realtime/stream/{user_id}`
- ✅ NDJSON endpoint added: `/api/realtime/updates/{user_id}`

## Deployment Plan

### Step 1: Package and Verify Code Structure

```bash
# Verify all required files are in place
ls -la ./backend/engine-c/src/main.py
ls -la ./backend/engine-c/src/realtime_enhancements.py
ls -la ./backend/engine-c/src/activity_logger.py
```

### Step 2: Build and Deploy to Cloud Run

```bash
# Set project
gcloud config set project galvanic-pulsar-482815-h0

# Build the Docker image
cd ./backend/engine-c
gcloud builds submit --tag gcr.io/galvanic-pulsar-482815-h0/engine-c:latest .

# Deploy to Cloud Run (us-central1)
gcloud run deploy engine-c \
  --image gcr.io/galvanic-pulsar-482815-h0/engine-c:latest \
  --region us-central1 \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars=ENGINE_C_MODE=live,TRADING_MODE=live \
  --no-allow-unauthenticated \
  --service-account=engine-c@galvanic-pulsar-482815-h0.iam.gserviceaccount.com
```

### Step 3: Verify Deployment

```bash
# Check deployment status
gcloud run services describe engine-c --region us-central1

# Get service URL
SERVICE_URL=$(gcloud run services describe engine-c \
  --region us-central1 \
  --format='value(status.url)')

echo "Service URL: $SERVICE_URL"
# Expected: https://engine-c-XXXXXXXXXX-uc.a.run.app

# Check service health
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "$SERVICE_URL/health"

# Expected response: 200 OK with {"status": "healthy"}
```

### Step 4: Test Real-Time Endpoints

```bash
# Test 1: Check endpoint availability
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "$SERVICE_URL/api/realtime/stream/test-user"
# Expected: SSE stream with heartbeat every 30s

# Test 2: Test postback webhook
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "orderId": "ORD-123",
    "orderStatus": "FILLED",
    "transactionType": "BUY",
    "tradingSymbol": "INFY-EQ",
    "clientId": "1101302170",
    "price": 100.5,
    "quantity": 10,
    "filledQuantity": 10
  }' \
  "$SERVICE_URL/api/dhan/postback"
# Expected: 200 OK with {"status": "received", "stored": true}

# Test 3: Verify Firestore storage
gcloud firestore documents get --collection-id=trade_events --limit=1
# Expected: Recent trade_events document with order_id, symbol, status fields
```

### Step 5: Configure Dhan OAuth Callback URLs

Update Dhan developer dashboard:

- **Postback Webhook URL**: `{SERVICE_URL}/api/dhan/postback`
- **Redirect URL**: `{SERVICE_URL}/auth/dhan/success`

Where `{SERVICE_URL}` is from Step 3 (e.g., `https://engine-c-3acobgd3qa-uc.a.run.app`)

### Step 6: Verify Cloud Logging

```bash
# Check deployment logs
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="engine-c"' \
  --limit=50 \
  --format=json \
  --project=galvanic-pulsar-482815-h0

# Look for success messages:
# ✅ Real-time enhancements enabled
# ✅ Postback stored in Firestore
# 📢 Broadcast: order_update
# 🔌 SSE stream started
```

## Verification Checklist

### Post-Deployment Tests

#### Test 1: Endpoint Health

```bash
curl -I "$SERVICE_URL/health"
# Expected: 200 OK
```

#### Test 2: Account Data Endpoint (Recommended)

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "$SERVICE_URL/api/v1/user/1101302170/account"
# Expected: 200 OK with complete account data (funds, positions, orders, holdings, trades)
```

#### Test 3: Real-Time SSE Connection

```bash
# Start SSE listener in one terminal
curl -N -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "$SERVICE_URL/api/realtime/stream/1101302170"

# Send postback in another terminal
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "orderId": "ORD-SSE-TEST",
    "orderStatus": "PENDING",
    "transactionType": "BUY",
    "tradingSymbol": "NIFTY-50",
    "clientId": "1101302170"
  }' \
  "$SERVICE_URL/api/dhan/postback"

# Expected in SSE listener: Event data with order_update
```

#### Test 4: Firestore Persistence

```bash
# Check Firestore collections
gcloud firestore documents list --collection-id=trade_events
gcloud firestore documents list --collection-id=user_positions

# Verify recent data
gcloud firestore documents get trade_events/ORD-SSE-TEST_<timestamp>
```

#### Test 5: NDJSON Stream (Alternative Format)

```bash
curl -N -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "$SERVICE_URL/api/realtime/updates/1101302170" | head -20
# Expected: One JSON object per line, each valid JSON
```

## Rollback Plan

If issues occur:

```bash
# 1. Check previous revisions
gcloud run revisions list --service=engine-c --region=us-central1

# 2. Rollback to previous revision
PREV_REVISION=$(gcloud run revisions list --service=engine-c \
  --region=us-central1 \
  --format='value(name)' \
  --limit=2 | tail -1)

gcloud run services update-traffic engine-c \
  --to-revisions $PREV_REVISION=100 \
  --region=us-central1

# 3. Full redeploy from source
gcloud run deploy engine-c \
  --source . \
  --region us-central1 \
  --project=galvanic-pulsar-482815-h0
```

## Performance Monitoring

### Cloud Logging Queries

```bash
# Monitor SSE connections
gcloud logging read 'logName="projects/galvanic-pulsar-482815-h0/logs/engine-c" AND "SSE stream started"' \
  --limit=10

# Monitor postback events
gcloud logging read 'logName="projects/galvanic-pulsar-482815-h0/logs/engine-c" AND "Postback received"' \
  --limit=20

# Monitor errors
gcloud logging read 'logName="projects/galvanic-pulsar-482815-h0/logs/engine-c" AND severity="ERROR"' \
  --limit=10
```

### Metrics to Watch

1. **Postback Latency**: Time from webhook received to Firestore stored
   - Target: < 100ms
   - Alert threshold: > 500ms

2. **SSE Connection Count**: Active SSE listeners
   - Target: Scale with concurrent users
   - Limit: 1000 concurrent per Cloud Run service

3. **Firestore Write Cost**: Trade events storage
   - Monitor: `/api/dhan/postback` call frequency
   - Optimize: Batch writes if > 10 postbacks/second

4. **Error Rate**: Failed postbacks or SSE disconnects
   - Target: < 0.1%
   - Alert threshold: > 1%

## Troubleshooting

### Issue: SSE Connection Timeout

**Symptoms**: Browser closes connection after ~60 seconds
**Cause**: Reverse proxy buffering
**Solution**: Headers already set in code (`X-Accel-Buffering: no`)

### Issue: Postback Not Stored

**Symptoms**: Postback returns 200 but no Firestore document
**Cause**: Firestore write permissions or module not initialized
**Solution**:

```bash
# Check service account permissions
gcloud projects get-iam-policy galvanic-pulsar-482815-h0 \
  --flatten="bindings[].members" \
  --filter="members:engine-c@"

# Check Firestore rules
gcloud firestore databases list
```

### Issue: High Latency on Postback

**Symptoms**: Postback takes > 1 second
**Cause**: Firestore initialization or network latency
**Solution**:

```bash
# Check Cloud Run CPU/Memory usage
gcloud run services describe engine-c --region=us-central1

# Scale up if needed
gcloud run deploy engine-c \
  --region us-central1 \
  --memory 4Gi \
  --cpu 4
```

## Success Criteria

✅ Deployment successful when:

1. ✅ Service deployed and healthy (curl health endpoint)
2. ✅ Account data endpoint returns complete account info
3. ✅ Postback webhook stores to Firestore (verify trade_events collection)
4. ✅ SSE stream connects and receives events
5. ✅ NDJSON stream returns valid JSON Lines format
6. ✅ End-to-end: postback → Firestore → SSE notification < 500ms
7. ✅ No errors in Cloud Logging related to real-time module
8. ✅ Dhan callback URLs configured and tested

## Next Steps

1. **Frontend Integration**: Connect SSE stream to dashboard
2. **Mobile Support**: Implement fallback for mobile clients (polling)
3. **Performance Optimization**: Monitor and optimize Firestore queries
4. **Alerting**: Set up Cloud Monitoring alerts for errors and latency
5. **Scaling**: Monitor concurrent SSE connections and scale as needed

---

**Deployment Date**: [Current Date]
**Service URL**: https://engine-c-XXXXXXXXXX-uc.a.run.app
**Status**: Ready for deployment
