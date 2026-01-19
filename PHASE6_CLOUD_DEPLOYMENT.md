# Phase 6: Cloud Deployment & Go-Live

**Status**: Ready (blocked on Phase 5 test completion)
**Duration**: 60 minutes
**Estimated Go-Live**: 2025-01-19 Evening
**Project ID**: galvanic-pulsar-482815-h0

---

## Executive Summary

Phase 6 deploys the tuned trading engines to Google Cloud Platform (GCP) for live trading. All three engines will be deployed as containerized microservices on Cloud Run, with orchestration via Pub/Sub and persistence in Firestore.

**Key Deliverables**:

1. ✅ Build & containerize all engines (Docker)
2. ✅ Deploy to Cloud Run (compute)
3. ✅ Configure Pub/Sub messaging (orchestration)
4. ✅ Verify Firestore persistence (data)
5. ✅ Monitor with Cloud Logging (observability)
6. ✅ Execute health checks & sign-off (validation)

---

## Pre-Deployment Checklist

Before Phase 6 begins, verify:

- [ ] Phase 5 tests PASSED ✅
- [ ] All critical bugs FIXED
- [ ] Engine code finalized (no pending changes)
- [ ] GCP project accessible (gcloud auth)
- [ ] Docker installed locally
- [ ] All Dhan credentials in Secret Manager
- [ ] Firestore indexes created
- [ ] Cloud Run permissions configured
- [ ] Monitoring alerts configured

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Google Cloud Platform                        │
│                    Project: galvanic-pulsar...                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Pub/Sub Topics (Orchestration)              │  │
│  │  • market-data      (price feeds)                        │  │
│  │  • engine-a-signals (Engine A outputs)                  │  │
│  │  • engine-b-features (Engine B technical data)          │  │
│  │  • trade-execution (approved orders)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ↕                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Engine A   │  │  Engine B    │  │  Engine C   │             │
│  │   Risk      │  │   Technical  │  │     ML      │             │
│  │   Mgmt      │  │ Indicators   │  │   Model     │             │
│  │             │  │              │  │             │             │
│  │ Cloud Run   │  │  Cloud Run   │  │  Cloud Run  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│           ↓              ↓              ↓                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Firestore Database (Persistence)               │  │
│  │  Collections:                                            │  │
│  │  • trades (executed orders)                             │  │
│  │  • signals (generated signals)                          │  │
│  │  • metrics (performance data)                           │  │
│  │  • logs (audit trail)                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      Cloud Logging & Monitoring (Observability)          │  │
│  │  • Structured logs (JSON)                               │  │
│  │  • Performance metrics                                  │  │
│  │  • Error tracking                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
         ↓
    External APIs
    • Dhan Broker (order execution)
    • Market data provider
```

---

## Deployment Steps

### Step 1: Prepare Docker Images (10 min)

#### 1.1 Build Engine A Image

```bash
# Set project and image details
export GCP_PROJECT_ID="galvanic-pulsar-482815-h0"
export IMAGE_NAME="engine-a"
export IMAGE_TAG="v1.0.0"

# Navigate to backend directory
cd backend/engine-a

# Build Docker image
docker build \
  --tag "gcr.io/${GCP_PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}" \
  --file Dockerfile .

# Verify image built
docker images | grep ${IMAGE_NAME}
```

**Expected Output**:

```
gcr.io/galvanic-pulsar-482815-h0/engine-a   v1.0.0   <image-id>
```

---

#### 1.2 Build Engine B Image

```bash
export IMAGE_NAME="engine-b"

cd ../engine-b

docker build \
  --tag "gcr.io/${GCP_PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}" \
  --file Dockerfile .

# Verify
docker images | grep ${IMAGE_NAME}
```

---

#### 1.3 Build Engine C Image

```bash
export IMAGE_NAME="engine-c"

cd ../engine-c

docker build \
  --tag "gcr.io/${GCP_PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}" \
  --file Dockerfile .

# Verify
docker images | grep ${IMAGE_NAME}
```

**Verification**:

```bash
# List all three images
docker images | grep gcr.io
```

Expected:

```
gcr.io/galvanic-pulsar-482815-h0/engine-a        v1.0.0    <id1>
gcr.io/galvanic-pulsar-482815-h0/engine-b        v1.0.0    <id2>
gcr.io/galvanic-pulsar-482815-h0/engine-c        v1.0.0    <id3>
```

---

### Step 2: Push Images to Container Registry (5 min)

#### 2.1 Authenticate Docker with GCR

```bash
# Configure Docker authentication
gcloud auth configure-docker gcr.io

# Verify authentication
docker run --rm gcr.io/google.com/cloudsdktool/cloud-sdk:slim echo "Auth OK"
```

---

#### 2.2 Push Each Image

```bash
# Push Engine A
docker push "gcr.io/${GCP_PROJECT_ID}/engine-a:${IMAGE_TAG}"

# Push Engine B
docker push "gcr.io/${GCP_PROJECT_ID}/engine-b:${IMAGE_TAG}"

# Push Engine C
docker push "gcr.io/${GCP_PROJECT_ID}/engine-c:${IMAGE_TAG}"

# Verify all pushed
gcloud container images list --project=${GCP_PROJECT_ID}
```

**Expected Output**:

```
gcr.io/galvanic-pulsar-482815-h0/engine-a
gcr.io/galvanic-pulsar-482815-h0/engine-b
gcr.io/galvanic-pulsar-482815-h0/engine-c
```

---

### Step 3: Deploy to Cloud Run (20 min)

#### 3.1 Deploy Engine A (Risk Management)

```bash
# Set environment variables
export SERVICE_NAME="engine-a"
export REGION="us-central1"  # or preferred region
export MEMORY="2Gi"
export CPU="2"
export TIMEOUT="3600"  # 60 minutes for long-running processes

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image="gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION} \
  --memory=${MEMORY} \
  --cpu=${CPU} \
  --timeout=${TIMEOUT} \
  --no-allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID}" \
  --set-env-vars="PUBSUB_TOPIC_SIGNALS=engine-a-signals" \
  --set-env-vars="PUBSUB_TOPIC_TRADES=trade-execution" \
  --service-account="trading-engine-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Verify deployment
gcloud run services describe ${SERVICE_NAME} \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION}
```

**Expected Output**:

```
Service: engine-a
Status: ✓
URL: https://engine-a-<hash>-uc.a.run.app
Last deployed by: <user>
Last deployed at: <timestamp>
Traffic: 100% LATEST
```

---

#### 3.2 Deploy Engine B (Technical Indicators)

```bash
export SERVICE_NAME="engine-b"

gcloud run deploy ${SERVICE_NAME} \
  --image="gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION} \
  --memory="1Gi" \
  --cpu="2" \
  --timeout=${TIMEOUT} \
  --no-allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID}" \
  --set-env-vars="PUBSUB_TOPIC_INPUT=market-data" \
  --set-env-vars="PUBSUB_TOPIC_OUTPUT=engine-b-features" \
  --service-account="trading-engine-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Verify
gcloud run services describe ${SERVICE_NAME} \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION}
```

---

#### 3.3 Deploy Engine C (ML Model)

```bash
export SERVICE_NAME="engine-c"

gcloud run deploy ${SERVICE_NAME} \
  --image="gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION} \
  --memory="2Gi" \
  --cpu="2" \
  --timeout=${TIMEOUT} \
  --no-allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID}" \
  --set-env-vars="PUBSUB_TOPIC_INPUT=engine-b-features" \
  --set-env-vars="PUBSUB_TOPIC_OUTPUT=engine-c-predictions" \
  --service-account="trading-engine-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Verify all three services deployed
gcloud run services list \
  --project=${GCP_PROJECT_ID} \
  --filter="metadata.name:(engine-a OR engine-b OR engine-c)"
```

**Expected Output**:

```
Service       Status  Latest URL
engine-a      ✓       https://engine-a-...
engine-b      ✓       https://engine-b-...
engine-c      ✓       https://engine-c-...
```

---

### Step 4: Configure Pub/Sub Topics (5 min)

#### 4.1 Create Topics

```bash
# Topics
TOPICS=(
  "market-data"
  "engine-a-signals"
  "engine-b-features"
  "engine-c-predictions"
  "trade-execution"
  "audit-logs"
)

# Create each topic
for TOPIC in "${TOPICS[@]}"; do
  gcloud pubsub topics create ${TOPIC} \
    --project=${GCP_PROJECT_ID} || echo "Topic ${TOPIC} already exists"
done

# Verify topics created
gcloud pubsub topics list --project=${GCP_PROJECT_ID}
```

---

#### 4.2 Create Subscriptions

```bash
# Subscriptions (for testing/monitoring)
# Each topic gets a subscription for debugging

gcloud pubsub subscriptions create engine-a-signals-sub \
  --topic=engine-a-signals \
  --project=${GCP_PROJECT_ID}

gcloud pubsub subscriptions create trade-execution-sub \
  --topic=trade-execution \
  --project=${GCP_PROJECT_ID}

# Verify subscriptions
gcloud pubsub subscriptions list --project=${GCP_PROJECT_ID}
```

---

### Step 5: Verify Firestore Collections (5 min)

#### 5.1 Check Firestore Structure

```bash
# Verify Firestore accessible
gcloud firestore collections list --project=${GCP_PROJECT_ID}

# Expected collections:
# - trades
# - signals
# - metrics
# - logs
# - config
```

---

#### 5.2 Create Initial Config Document

```bash
# Create config collection with deployment metadata
cat > /tmp/config.json << 'EOF'
{
  "deployment_version": "v1.0.0",
  "deployed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "deployed_by": "phase-6-automation",
  "engine_a_version": "1.0.0",
  "engine_b_parameters": {
    "macd_fast": 10,
    "macd_slow": 20,
    "macd_signal": 9,
    "rsi_oversold": 25,
    "rsi_overbought": 75,
    "bb_width_multiplier": 2.5
  },
  "status": "live",
  "trading_enabled": false
}
EOF

# Note: Replace with actual deployment time
# This config will be used by engines to validate settings
```

---

### Step 6: Health Checks (5 min)

#### 6.1 Test Cloud Run Services

```bash
# Get service URLs
ENGINE_A_URL=$(gcloud run services describe engine-a \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION} \
  --format='value(status.url)')

ENGINE_B_URL=$(gcloud run services describe engine-b \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION} \
  --format='value(status.url)')

ENGINE_C_URL=$(gcloud run services describe engine-c \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION} \
  --format='value(status.url)')

# Test health endpoints
curl -s "${ENGINE_A_URL}/health" | jq .
curl -s "${ENGINE_B_URL}/health" | jq .
curl -s "${ENGINE_C_URL}/health" | jq .
```

**Expected Responses**:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-19T18:00:00Z",
  "version": "1.0.0",
  "checks": {
    "firestore": "connected",
    "pubsub": "connected",
    "broker_credentials": "verified"
  }
}
```

---

#### 6.2 Test Pub/Sub Integration

```bash
# Publish test message to market-data topic
gcloud pubsub topics publish market-data \
  --project=${GCP_PROJECT_ID} \
  --message='{"symbol":"TCS","price":4250.50,"timestamp":"2025-01-19T15:30:00Z"}'

# Subscribe and verify message
gcloud pubsub subscriptions pull market-data-test-sub \
  --project=${GCP_PROJECT_ID} \
  --auto-ack \
  --limit=1

# Verify logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name:(engine-a OR engine-b OR engine-c)" \
  --limit 10 \
  --project=${GCP_PROJECT_ID}
```

---

#### 6.3 Verify Firestore Connectivity

```bash
# Check if engines can write to Firestore
# This test will be automatic from service logs

# Query for recent writes
gcloud firestore documents list \
  --collection-ids=signals \
  --limit=5 \
  --project=${GCP_PROJECT_ID}
```

---

### Step 7: Configuration & Secrets (5 min)

#### 7.1 Verify Secrets in Secret Manager

```bash
# Verify all required secrets exist
SECRETS=(
  "dhan-client-id"
  "dhan-auth-token"
  "dhan-api-key"
  "dhan-api-secret"
  "polygon-api-key"
  "firebase-service-account"
)

for SECRET in "${SECRETS[@]}"; do
  gcloud secrets versions access latest \
    --secret=${SECRET} \
    --project=${GCP_PROJECT_ID} > /dev/null && \
    echo "✓ ${SECRET}" || \
    echo "✗ ${SECRET} NOT FOUND"
done
```

---

#### 7.2 Update Secret Manager with Deployment Version

```bash
# Add deployment info to Secret Manager
echo "Deployment version: v1.0.0" | \
  gcloud secrets versions add deployment-metadata \
    --data-file=- \
    --project=${GCP_PROJECT_ID}
```

---

### Step 8: Monitoring & Alerts (5 min)

#### 8.1 Create Monitoring Dashboard

```bash
# Create dashboard for engine monitoring
cat > /tmp/dashboard.json << 'EOF'
{
  "displayName": "Trading Engines Dashboard",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Engine A - Signal Generation Rate",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"engine-a\""
                }
              }
            }]
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Engine B - Feature Calculation Time",
          "xyChart": {}
        }
      }
    ]
  }
}
EOF

# Deploy dashboard (optional - can use Console)
# gcloud monitoring dashboards create --config-from-file=/tmp/dashboard.json
```

---

#### 8.2 Set Up Alerts

```bash
# Alert if service is down
gcloud alpha monitoring policies create \
  --notification-channels=<CHANNEL_ID> \
  --display-name="Engine Service Down" \
  --condition-display-name="Engine unavailable" \
  --condition-threshold-value=0 \
  --condition-threshold-duration=300s

# Alert if error rate high
gcloud alpha monitoring policies create \
  --notification-channels=<CHANNEL_ID> \
  --display-name="High Engine Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=60s
```

---

## Post-Deployment Verification

### Verification Checklist

- [ ] All three Cloud Run services deployed
- [ ] Health check endpoints responding (status: healthy)
- [ ] Pub/Sub topics created and subscriptions active
- [ ] Firestore collections accessible
- [ ] Secrets in Secret Manager verified
- [ ] Cloud Logging showing healthy messages
- [ ] No critical errors in logs
- [ ] Dhan broker connectivity verified
- [ ] Market data feed active
- [ ] Test signal generated successfully

### Log Verification Commands

```bash
# View recent logs from all engines
for SERVICE in engine-a engine-b engine-c; do
  echo "=== Logs for ${SERVICE} ==="
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE}" \
    --limit=5 \
    --format="table(timestamp,severity,textPayload)" \
    --project=${GCP_PROJECT_ID}
done

# Check for errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit=10 \
  --project=${GCP_PROJECT_ID}
```

---

## Rollback Procedure

If critical issues found:

```bash
# Stop/rollback a service
gcloud run services describe engine-a \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION}

# Redeploy previous version (if tag available)
gcloud run deploy engine-a \
  --image="gcr.io/${GCP_PROJECT_ID}/engine-a:v0.9.9" \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION}

# Or delete service entirely
gcloud run services delete engine-a \
  --project=${GCP_PROJECT_ID}
```

---

## Go-Live Checklist

### Before Enabling Live Trading

- [ ] **Phase 5 Tests**: All passed ✅
- [ ] **Deployment**: All services healthy ✅
- [ ] **Health Checks**: All returning 200 OK ✅
- [ ] **Dhan Connection**: Orders testable ✅
- [ ] **Firestore**: Writing data successfully ✅
- [ ] **Logs**: No errors in past 5 minutes ✅
- [ ] **Monitoring**: Dashboards active ✅
- [ ] **Documentation**: All updated ✅
- [ ] **Rollback Plan**: Documented & tested ✅

### Enable Live Trading

```bash
# Update Firestore config to enable trading
# WARNING: This enables real trades

gcloud firestore documents update config/deployment \
  --update="trading_enabled=true" \
  --project=${GCP_PROJECT_ID}

# Verify status
gcloud firestore documents get config/deployment \
  --project=${GCP_PROJECT_ID}
```

---

## Phase 6 Sign-Off

**Deployment Complete When**:
✅ All services deployed and healthy
✅ All tests passing
✅ Monitoring active
✅ Documentation complete
✅ Rollback procedures tested
✅ Go-live authorization received

---

**Current Status**: Ready for Phase 5 → Phase 6 transition
**Blocking Item**: Phase 5 tests must pass first
**Estimated Total Project Completion**: 75% → 100% (ETA: 2025-01-19 evening)

---

## Quick Reference

### Key Commands

```bash
# Deploy all services
for SERVICE in engine-a engine-b engine-c; do
  gcloud run deploy $SERVICE \
    --image="gcr.io/${GCP_PROJECT_ID}/${SERVICE}:v1.0.0" \
    --project=${GCP_PROJECT_ID} \
    --region=us-central1
done

# Check service status
gcloud run services list --project=${GCP_PROJECT_ID}

# View logs
gcloud logging read "resource.type=cloud_run_revision" \
  --project=${GCP_PROJECT_ID} --limit=50

# Test health
for URL in $(gcloud run services list --format='value(status.url)' --project=${GCP_PROJECT_ID}); do
  curl -s "${URL}/health"
done
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-19
**Author**: Phase 6 Deployment Guide
