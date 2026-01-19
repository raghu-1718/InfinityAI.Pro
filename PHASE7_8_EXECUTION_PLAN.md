# Phase 7 & 8 - Production Deployment & Monitoring

**Date**: 2026-01-19  
**Status**: INITIATING  
**Target Completion**: 2026-01-21 (Phase 7) + 48h monitoring (Phase 8 → 2026-01-23)

---

## PHASE 7: PRODUCTION DEPLOYMENT (2 hours)

### Overview
Deploy all services (engine-a, engine-b, engine-c, frontend) to production with zero-downtime strategy and rollback procedures ready.

### Pre-Deployment Checklist

✅ **Code Status**:
- engine-c: ✅ Revision 00074-vsq (healthy, latest fixes deployed)
- engine-a: Status check needed
- engine-b: Status check needed
- frontend: Status check needed

✅ **Infrastructure**:
- KMS: 90-day rotation enabled
- Secret Manager: Secrets replicated
- Firestore: Rules configured
- Cloud Run: Service accounts ready

✅ **Critical Issues Resolved**:
- Dockerfile paths fixed (engine-c)
- Import resilience implemented (engine-c)
- CORS hardening complete
- Coupon cleanup verified (10 INFAI-FAM-*)

### Deployment Sequence

#### Step 1: Engine-A Deployment (15 min)
```bash
# Check current status
gcloud run services describe engine-a --region us-central1 \
  --project galvanic-pulsar-482815-h0

# Deploy latest
gcloud run deploy engine-a --source backend \
  --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --allow-unauthenticated \
  --timeout 60 \
  --memory 512Mi \
  --quiet

# Verify
curl https://engine-a-URL/health
```

#### Step 2: Engine-B Deployment (15 min)
```bash
gcloud run deploy engine-b --source backend \
  --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --allow-unauthenticated \
  --timeout 60 \
  --memory 512Mi \
  --quiet

curl https://engine-b-URL/health
```

#### Step 3: Engine-C Re-verification (5 min)
```bash
# Confirm 00074-vsq still healthy
gcloud run services describe engine-c --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --format="value(status.latestReadyRevisionName)"

curl https://engine-c-228557716858.us-central1.run.app/health
```

#### Step 4: Backtest-Orchestrator Fix & Redeploy (20 min)
- Build from source (currently stale from 2026-01-10)
- Deploy with extended startup timeout if needed
- Verify health check responds

#### Step 5: Frontend Deployment (10 min)
```bash
# Deploy from frontend source
cd frontend/web-app
gcloud app deploy app.yaml \
  --project galvanic-pulsar-482815-h0 \
  --quiet

# Verify
curl https://infinityai.pro/health
```

### Rollback Procedures

**If Engine-A fails**:
```bash
gcloud run services update engine-a \
  --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --no-traffic  # Route 100% to previous stable revision
```

**If Engine-C fails** (revert to 00073-pq5):
```bash
gcloud run services update-traffic engine-c \
  --to-revisions engine-c-00073-pq5=100 \
  --region us-central1 \
  --project galvanic-pulsar-482815-h0
```

**Full rollback** (revert all services):
```bash
# Disable all services
for svc in engine-a engine-b engine-c; do
  gcloud run services update "$svc" \
    --region us-central1 \
    --project galvanic-pulsar-482815-h0 \
    --no-traffic
done
```

### Post-Deployment Verification

**Health Checks** (run all 5):
```bash
curl https://engine-a-URL/health
curl https://engine-b-URL/health
curl https://engine-c-URL/health
curl https://infinityai.pro/health
gcloud run services describe backtest-orchestrator
```

**Integration Tests**:
```bash
# Test coupon verification
curl -X POST https://engine-c-URL/api/auth/coupon/verify \
  -H "Content-Type: application/json" \
  -d '{"coupon_code":"INFAI-FAM-DAD","email":"test@test.com"}'

# Test AI signal generation (engine-b)
curl https://engine-b-URL/api/signals/analyze

# Test backtest endpoint (if recovered)
curl https://backtest-orchestrator-URL/health
```

**CORS Validation**:
```bash
curl -i -X OPTIONS https://infinityai.pro/api/auth/coupon/verify \
  -H "Origin: https://infinityai.pro"
```

Expected headers:
- `Access-Control-Allow-Origin: https://infinityai.pro` ✅
- `Access-Control-Allow-Methods: POST, GET, OPTIONS` ✅
- `Access-Control-Allow-Credentials: true` ✅

### Sign-Off

**Deployment Owner**: [CTO/Engineering Lead]  
**Verified By**: Live integration tests  
**Time**: [Record deployment time]  
**Status**: ⏳ PENDING EXECUTION

---

## PHASE 8: 48-HOUR MONITORING & STABILIZATION

### Monitoring Schedule

#### First 24 Hours - CRITICAL (Hourly)
Every hour from deployment:
- Health checks for all 5 services
- Error rate <0.1%
- Latency p95 <1000ms
- Uptime validation

#### Second 24 Hours - STANDARD (Every 4 hours)
- Health checks (all services)
- Error rate trend <0.1%
- Latency trend <1000ms
- Resource utilization check

### Key Metrics to Monitor

```
┌─────────────────────────────────────────────────────────────┐
│ Metric                │ Threshold    │ Alert If          │
├─────────────────────────────────────────────────────────────┤
│ Uptime                │ >99.9%       │ <99.5%            │
│ Error Rate (5xx)      │ <0.1%        │ >0.5%             │
│ p95 Latency           │ <1000ms      │ >2000ms           │
│ Memory Usage          │ <80%         │ >90%              │
│ CPU Usage             │ <70%         │ >85%              │
│ Request/sec           │ Baseline+10% │ Baseline+50%      │
│ Cold Start Time       │ <10s         │ >15s              │
│ Firestore Ops         │ <1000 ops/s  │ >5000 ops/s       │
│ KMS Latency           │ <100ms       │ >500ms            │
│ Secret Manager Latency│ <50ms        │ >200ms            │
└─────────────────────────────────────────────────────────────┘
```

### Monitoring Commands

**Hourly Health Check Script**:
```bash
#!/bin/bash
# Run every hour for first 24 hours

SERVICES=("engine-a" "engine-b" "engine-c" "backtest-orchestrator")
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "=== HEALTH CHECK: $TIMESTAMP ===" >> monitoring.log

for svc in "${SERVICES[@]}"; do
  STATUS=$(gcloud run services describe "$svc" \
    --region us-central1 \
    --project galvanic-pulsar-482815-h0 \
    --format="value(status.conditions[0].status)")
  
  if [ "$STATUS" = "True" ]; then
    echo "✅ $svc: HEALTHY" >> monitoring.log
  else
    echo "❌ $svc: UNHEALTHY" >> monitoring.log
    # ALERT: Send to PagerDuty/Slack
  fi
done

# Check error rates
gcloud logging read \
  'severity="ERROR" OR severity="CRITICAL"' \
  --limit 100 \
  --project galvanic-pulsar-482815-h0 >> monitoring.log
```

**Error Rate Check**:
```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity="ERROR"' \
  --format="table(timestamp, resource.labels.service_name, jsonPayload.message)" \
  --project galvanic-pulsar-482815-h0
```

**Latency Analysis**:
```bash
gcloud monitoring time-series list \
  --filter 'metric.type="run.googleapis.com/request_latencies"' \
  --format="table(metric.labels.service_name, points[0].value.double_value)" \
  --project galvanic-pulsar-482815-h0
```

**Uptime Report**:
```bash
gcloud run services describe engine-c \
  --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --format="value(status.observedGeneration, metadata.generation)"
```

### Escalation Procedures

**TIER 1: Yellow Alert** (Minor issue)
- Service still responding but error rate 0.1-0.5%
- **Action**: Monitor closely, check logs, may not require immediate action
- **Notification**: Log to monitoring dashboard

**TIER 2: Orange Alert** (Major issue)
- Service degraded: error rate 0.5-2%
- **Action**: Check logs, identify root cause, may need manual intervention
- **Notification**: Alert engineering team on Slack

**TIER 3: Red Alert** (Critical)
- Service down or error rate >5%
- **Action**: IMMEDIATE - Execute rollback procedures
- **Notification**: Page on-call engineer

**Rollback Decision Tree**:
```
Service Down?
  ├─→ YES: Immediate rollback (5 min SLA)
  └─→ NO: Error rate >2%?
       ├─→ YES: Rollback (30 min window)
       └─→ NO: Continue monitoring, investigate logs
```

### Firestore & Database Monitoring

Monitor these collections for anomalies:
- `coupons`: Should have exactly 10 INFAI-FAM-* docs
- `coupon_sessions`: Sessions created during trades
- `dhan_credentials`: No direct reads (backend-only)
- `user_profiles`: User signup/login events

### Sign-Off Checklist

After 48 hours, verify all pass:

- [ ] **Uptime**: >99.9% across all services
- [ ] **Error Rate**: <0.1% for all services
- [ ] **Latency**: p95 <1000ms for all endpoints
- [ ] **Resource Usage**: <80% memory, <70% CPU
- [ ] **No Anomalies**: No unexpected spikes in request volume or latency
- [ ] **Firestore Data**: All collections intact, coupon cleanup verified
- [ ] **KMS/Secrets**: All credential access successful, no errors
- [ ] **User Transactions**: Paper trading flows completed successfully
- [ ] **Backups**: Firestore backup completed and verified
- [ ] **Documentation**: Monitoring logs and incident reports archived

### Success Criteria

**Phase 7 & 8 Complete When**:
- ✅ All 5 services (engine-a/b/c, backtest, frontend) READY
- ✅ Zero critical errors in first 24 hours
- ✅ 48 hours of continuous monitoring with <0.1% error rate
- ✅ All integration tests passing
- ✅ Rollback procedures ready but not needed
- ✅ Team confidence in production state: HIGH

### Documentation Requirements

**Create After Phase 7**:
- `PHASE7_DEPLOYMENT_COMPLETE.md` - Record exact times, service URLs, revision IDs
- `PHASE7_DEPLOYMENT_VERIFICATION.md` - All health checks passed

**Create During Phase 8**:
- `PHASE8_MONITORING_LOG_[DAY1].md` - Hourly logs
- `PHASE8_MONITORING_LOG_[DAY2].md` - Hourly logs
- `PHASE8_INCIDENT_REPORT.md` - Any issues and resolutions

**Create After Phase 8**:
- `PHASE7_8_SIGN_OFF.md` - Final sign-off document with metrics
- `PRODUCTION_OPERATIONS_PLAYBOOK.md` - Ongoing monitoring procedures

---

## Timeline & Owners

| Phase | Task | Duration | Owner | Status |
|-------|------|----------|-------|--------|
| 7 | Pre-deploy verification | 15 min | DevOps | ⏳ TODO |
| 7 | Deploy engine-a | 15 min | DevOps | ⏳ TODO |
| 7 | Deploy engine-b | 15 min | DevOps | ⏳ TODO |
| 7 | Verify engine-c | 5 min | QA | ⏳ TODO |
| 7 | Fix backtest-orchestrator | 20 min | DevOps | ⏳ TODO |
| 7 | Deploy frontend | 10 min | DevOps | ⏳ TODO |
| 7 | Post-deploy integration tests | 10 min | QA | ⏳ TODO |
| 7 | Sign-off | 5 min | CTO | ⏳ TODO |
| 8 | 24-hour continuous monitoring | 24h | On-Call | ⏳ TODO |
| 8 | 24-hour post-monitoring | 24h | On-Call | ⏳ TODO |
| 8 | Final sign-off | 30 min | Engineering Lead | ⏳ TODO |

**Total**: ~5.5 hours (Phase 7) + 48 hours (Phase 8)

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| Engine startup fails | P0 - Service down | Low | Rollback procedure, extended timeout |
| High error rate spike | P1 - Degraded service | Low | Monitoring alerts, immediate investigation |
| Firestore outage | P1 - Data unavailable | Very Low | GCP SLA 99.95%, backup ready |
| KMS key rotation fails | P2 - Credential access | Very Low | Manual key rotation ready, fallback keys |
| CORS misconfiguration | P2 - Frontend blocked | Low | CORS preflight tested before deploy |
| Backtest recovery slow | P3 - Non-critical | Medium | Monitored separately, not blocking other services |

---

## Success Definition

🟢 **Phase 7 & 8 SUCCESS** when:
- All 5 services deployed and READY (Status: True)
- 48 hours of continuous operation with >99.9% uptime
- Error rate <0.1% throughout monitoring period
- No critical incidents requiring rollback
- Team confidence in production readiness: **CONFIRMED**
- All documentation complete and archived

---

**Prepared by**: Architecture Team  
**Date**: 2026-01-19  
**Next Review**: Upon Phase 7 completion (expected 2026-01-19 23:30)
