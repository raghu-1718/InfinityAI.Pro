# InfinityAI.Pro - Quick Execution Reference

**Last Phase Summary**: Engine tuning complete, ready for testing → deployment → live trading
**Current Time Estimate**: 2-3 hours to go-live
**GCP Project**: galvanic-pulsar-482815-h0

---

## 🎯 Phase 5: Testing (90 minutes)

### Quick Command Reference

```bash
# 1. Unit Tests (15 min)
cd backend/engine-b
python -m pytest tests/test_macd_params.py -v
python -m pytest tests/test_rsi_thresholds.py -v
python -m pytest tests/test_bb_width.py -v

# 2. Integration Tests (30 min)
cd ../tests
python -m pytest test_full_pipeline.py -v
python -m pytest test_dhan_integration.py -v

# 3. Data Validation (20 min)
python -m pytest test_signal_quality.py -v
python -m pytest test_indicator_ranges.py -v

# 4. Stress Tests (15 min)
python -m pytest test_stress_conditions.py -v

# 5. Generate Test Report
python scripts/generate_test_report.py > TEST_RESULTS.txt
```

### Expected Test Outputs

✅ All tests should pass with output like:

```
test_macd_10_20_9_vs_12_26_9 PASSED
test_rsi_25_75_thresholds PASSED
test_bb_width_2_5_vs_2_0 PASSED
test_signal_generation_pipeline PASSED
test_dhan_order_placement PASSED
test_signal_quality PASSED

===== 40 passed in 45.23s =====
```

### Test Failure Quick Fixes

| Symptom                 | Cause                  | Fix                                           |
| ----------------------- | ---------------------- | --------------------------------------------- |
| MACD column not found   | Parameters not updated | Check engine-b/src/main.py lines 1025-1035    |
| RSI values out of range | Calculation error      | Verify RSI formula in lines 1751-1758         |
| BB width not wider      | Parameter mismatch     | Check window_dev=2.5 in Dockerfile or main.py |
| Dhan connection fails   | Credentials missing    | Verify DHAN_AUTH_TOKEN in environment         |
| Pipeline test hangs     | Data fetch timeout     | Check market hours or data provider status    |

---

## 🚀 Phase 6: Cloud Deployment (60 minutes)

### Environment Setup (5 min)

```bash
# Set variables (copy-paste ready)
export GCP_PROJECT_ID="galvanic-pulsar-482815-h0"
export IMAGE_TAG="v1.0.0"
export REGION="us-central1"
export SERVICE_ACCOUNT="trading-engine-sa@galvanic-pulsar-482815-h0.iam.gserviceaccount.com"

# Verify gcloud configured
gcloud auth list
gcloud config set project ${GCP_PROJECT_ID}
```

### Build & Push Images (10 min)

```bash
# Build all three images
for ENGINE in engine-a engine-b engine-c; do
  cd backend/${ENGINE}
  docker build -t "gcr.io/${GCP_PROJECT_ID}/${ENGINE}:${IMAGE_TAG}" .
  docker push "gcr.io/${GCP_PROJECT_ID}/${ENGINE}:${IMAGE_TAG}"
  cd ../..
done

# Verify all pushed
gcloud container images list --project=${GCP_PROJECT_ID}
```

### Deploy to Cloud Run (20 min)

```bash
# Deploy Engine A
gcloud run deploy engine-a \
  --image="gcr.io/${GCP_PROJECT_ID}/engine-a:${IMAGE_TAG}" \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION} \
  --memory="2Gi" \
  --cpu="2" \
  --no-allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID}" \
  --service-account="${SERVICE_ACCOUNT}"

# Deploy Engine B
gcloud run deploy engine-b \
  --image="gcr.io/${GCP_PROJECT_ID}/engine-b:${IMAGE_TAG}" \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION} \
  --memory="1Gi" \
  --cpu="2" \
  --no-allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID}" \
  --service-account="${SERVICE_ACCOUNT}"

# Deploy Engine C
gcloud run deploy engine-c \
  --image="gcr.io/${GCP_PROJECT_ID}/engine-c:${IMAGE_TAG}" \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION} \
  --memory="2Gi" \
  --cpu="2" \
  --no-allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID}" \
  --service-account="${SERVICE_ACCOUNT}"

# Verify deployments
gcloud run services list --project=${GCP_PROJECT_ID}
```

### Create Infrastructure (10 min)

```bash
# Create Pub/Sub topics
for TOPIC in market-data engine-a-signals engine-b-features engine-c-predictions trade-execution audit-logs; do
  gcloud pubsub topics create ${TOPIC} --project=${GCP_PROJECT_ID} 2>/dev/null || true
done

# Create subscriptions for monitoring
gcloud pubsub subscriptions create engine-a-signals-sub \
  --topic=engine-a-signals \
  --project=${GCP_PROJECT_ID} 2>/dev/null || true

# Verify Firestore accessible
gcloud firestore collections list --project=${GCP_PROJECT_ID}
```

### Health Checks (10 min)

```bash
# Get service URLs
for SERVICE in engine-a engine-b engine-c; do
  URL=$(gcloud run services describe ${SERVICE} \
    --project=${GCP_PROJECT_ID} \
    --region=${REGION} \
    --format='value(status.url)')

  echo "Testing ${SERVICE}..."
  curl -s "${URL}/health" | jq . || echo "FAILED"
done

# Check logs for errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit=10 \
  --project=${GCP_PROJECT_ID}
```

### Enable Live Trading (5 min)

```bash
# Update config to enable trading (CAREFUL - enables real trades!)
gcloud firestore documents update config/deployment \
  --update="trading_enabled=true" \
  --project=${GCP_PROJECT_ID}

# Verify enabled
gcloud firestore documents get config/deployment \
  --project=${GCP_PROJECT_ID}
```

---

## 🔍 Monitoring Commands

### View Real-Time Logs

```bash
# Stream logs from all engines
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name:(engine-a OR engine-b OR engine-c)" \
  --limit=50 \
  --project=${GCP_PROJECT_ID} \
  --follow

# View error logs only
gcloud logging read \
  "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit=20 \
  --project=${GCP_PROJECT_ID}
```

### Check Service Status

```bash
# Detailed service status
for SERVICE in engine-a engine-b engine-c; do
  echo "=== ${SERVICE} ==="
  gcloud run services describe ${SERVICE} \
    --project=${GCP_PROJECT_ID} \
    --region=${REGION} \
    --format="table(status.conditions[].type,status.conditions[].status)"
done
```

### Monitor Pub/Sub

```bash
# Pull messages from trade-execution topic
gcloud pubsub subscriptions pull trade-execution-sub \
  --project=${GCP_PROJECT_ID} \
  --auto-ack \
  --limit=5

# Check topic metrics
gcloud pubsub topics describe market-data \
  --project=${GCP_PROJECT_ID}
```

### Query Firestore

```bash
# Latest signals
gcloud firestore documents list \
  --collection-ids=signals \
  --limit=5 \
  --project=${GCP_PROJECT_ID}

# Latest trades
gcloud firestore documents list \
  --collection-ids=trades \
  --limit=5 \
  --project=${GCP_PROJECT_ID}

# Performance metrics
gcloud firestore documents list \
  --collection-ids=metrics \
  --limit=5 \
  --project=${GCP_PROJECT_ID}
```

---

## 🛑 Rollback Procedures

### If Something Goes Wrong

```bash
# Stop all services
for SERVICE in engine-a engine-b engine-c; do
  gcloud run services delete ${SERVICE} \
    --project=${GCP_PROJECT_ID} \
    --quiet
done

# Disable live trading
gcloud firestore documents update config/deployment \
  --update="trading_enabled=false" \
  --project=${GCP_PROJECT_ID}

# Redeploy previous version
gcloud run deploy engine-a \
  --image="gcr.io/${GCP_PROJECT_ID}/engine-a:v0.9.9" \
  --project=${GCP_PROJECT_ID} \
  --region=${REGION}
```

---

## 📊 Go-Live Verification Checklist

```
PRE-DEPLOYMENT
[ ] Phase 5 tests: All PASSED ✅
[ ] Test report: Generated & reviewed ✅
[ ] Dhan credentials: In Secret Manager ✅
[ ] GCP permissions: Configured ✅
[ ] Docker images: Built locally ✅

DEPLOYMENT
[ ] Images: Pushed to GCR ✅
[ ] Engine A: Deployed & healthy ✅
[ ] Engine B: Deployed & healthy ✅
[ ] Engine C: Deployed & healthy ✅
[ ] Pub/Sub: Topics created ✅
[ ] Firestore: Accessible ✅

VERIFICATION
[ ] Health endpoints: 200 OK ✅
[ ] Logs: No critical errors ✅
[ ] Pub/Sub: Messaging working ✅
[ ] Firestore: Writing data ✅
[ ] Dhan: Order placement testable ✅

GO-LIVE
[ ] First test signal: Generated ✅
[ ] First test trade: Executed (optional) ✅
[ ] Monitoring: Active ✅
[ ] Alerts: Configured ✅
[ ] Rollback plan: Tested ✅

SIGN-OFF
[ ] All checks passed ✅
[ ] Authorization received ✅
[ ] Trading enabled ✅
[ ] LIVE ✅
```

---

## 🎯 Key Parameters (India Tuning)

### Engine B - Technical Indicators

```
MACD:
  Fast: 10
  Slow: 20
  Signal: 9

RSI:
  Period: 14
  Oversold: < 25
  Overbought: > 75

Bollinger Bands:
  Period: 20
  Multiplier: 2.5
  Formula: mean ± (2.5 × stddev)
```

### Engine A - Risk Rules

```
Max Position: 2% of portfolio
Max Daily Loss: 2%
Max Monthly Loss: 5%
Stop Loss: Risk-adjusted
Take Profit: 1:1.5 R/R minimum
```

---

## 📞 Support Contacts & Resources

**GCP Console**: https://console.cloud.google.com/
**Firestore**: https://console.firebase.google.com/
**Dhan API Docs**: https://dhanhq.co/docs/
**Cloud Run Docs**: https://cloud.google.com/run/docs

**Quick Help**:

```bash
# View all GCP commands
gcloud --help

# View Cloud Run commands
gcloud run --help

# View Pub/Sub commands
gcloud pubsub --help

# View Firestore commands
gcloud firestore --help
```

---

## ⏱️ Time Budget

| Task                    | Time   | Total            |
| ----------------------- | ------ | ---------------- |
| Phase 5 Testing         | 90 min | 90 min           |
| Phase 6 Deployment      | 60 min | 150 min          |
| Verification & sign-off | 20 min | 170 min          |
| **TOTAL**               |        | **2 hrs 50 min** |

**ETA to Go-Live**: ~3 hours from start

---

## 🚀 Final Command Sequence (Copy-Paste Ready)

```bash
# Complete deployment in sequence
export GCP_PROJECT_ID="galvanic-pulsar-482815-h0"
export IMAGE_TAG="v1.0.0"
export REGION="us-central1"

# 1. Build images
for ENGINE in engine-a engine-b engine-c; do
  cd backend/${ENGINE}
  docker build -t "gcr.io/${GCP_PROJECT_ID}/${ENGINE}:${IMAGE_TAG}" .
  docker push "gcr.io/${GCP_PROJECT_ID}/${ENGINE}:${IMAGE_TAG}"
  cd ../..
done

# 2. Deploy services
for ENGINE in engine-a engine-b engine-c; do
  gcloud run deploy ${ENGINE} \
    --image="gcr.io/${GCP_PROJECT_ID}/${ENGINE}:${IMAGE_TAG}" \
    --project=${GCP_PROJECT_ID} \
    --region=${REGION} \
    --no-allow-unauthenticated
done

# 3. Create infrastructure
for TOPIC in market-data engine-a-signals engine-b-features engine-c-predictions trade-execution audit-logs; do
  gcloud pubsub topics create ${TOPIC} --project=${GCP_PROJECT_ID} 2>/dev/null || true
done

# 4. Verify health
for SERVICE in engine-a engine-b engine-c; do
  URL=$(gcloud run services describe ${SERVICE} \
    --project=${GCP_PROJECT_ID} \
    --region=${REGION} \
    --format='value(status.url)')
  curl -s "${URL}/health" | jq .
done

# 5. Enable trading
gcloud firestore documents update config/deployment \
  --update="trading_enabled=true" \
  --project=${GCP_PROJECT_ID}

echo "✅ LIVE TRADING ENABLED"
```

---

## 📋 Document Index

- [PROJECT_COMPLETION_SUMMARY.md](PROJECT_COMPLETION_SUMMARY.md) - Overview of all phases
- [PHASE4_ENGINE_TUNING_COMPLETE.md](PHASE4_ENGINE_TUNING_COMPLETE.md) - Detailed engine changes
- [PHASE5_TESTING_GUIDE.md](PHASE5_TESTING_GUIDE.md) - Testing procedures
- [PHASE6_CLOUD_DEPLOYMENT.md](PHASE6_CLOUD_DEPLOYMENT.md) - Deployment procedures
- [EXECUTION_REFERENCE.md](EXECUTION_REFERENCE.md) - This file

---

**Status**: ✅ Ready to Execute
**Next Action**: Start Phase 5 tests now
**Estimated Completion**: Today (2025-01-19) evening

---

**Document Version**: 1.0
**Last Updated**: 2025-01-19
**Purpose**: Quick reference for Phase 5 & 6 execution
