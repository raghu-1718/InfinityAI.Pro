# 📋 Deployment Execution Checklist

**Date**: January 19, 2026  
**Status**: 🟢 READY TO EXECUTE  
**Timeline**: This week through next Sunday  

---

## ✅ PHASE 1: DOCUMENTATION REVIEW (Today - 2 hours)

### Critical Documentation Files Review

- [ ] **PHASE3_EXECUTIVE_SUMMARY.md**
  - [ ] All URLs verified (3 engines, frontend)
  - [ ] Feature list complete
  - [ ] Security status accurate
  - [ ] Status: Production Ready confirmed
  
- [ ] **PHASE3_VERIFICATION_REPORT.md**
  - [ ] Deployment procedures correct
  - [ ] Environment variables documented
  - [ ] Cloud Run commands tested
  - [ ] Health check endpoints documented
  
- [ ] **USER_ONBOARDING_GUIDE.md**
  - [ ] All steps tested (account setup, DhanHQ, paper trading)
  - [ ] Screenshots placeholders noted
  - [ ] DhanHQ webhook URLs correct
  - [ ] Links updated to production URLs
  
- [ ] **PRODUCTION_DEPLOYMENT_COMPLETE.md**
  - [ ] Current service URLs verified
  - [ ] CORS security confirmed
  - [ ] Encryption status verified
  - [ ] Monitoring procedures current
  
- [ ] **QUICK_REFERENCE_CARD.md**
  - [ ] All CLI commands tested
  - [ ] Health check URLs updated
  - [ ] Emergency procedures clear
  - [ ] Support contacts current
  
- [ ] **KMS_AND_ENCRYPTION_STATUS.md**
  - [ ] AES-256-GCM confirmed active
  - [ ] KMS infrastructure ready
  - [ ] IAM permissions verified
  - [ ] Backup procedures documented

### Sign-Off: QA Lead
- [ ] All documentation reviewed
- [ ] No critical gaps identified
- [ ] Ready to proceed to testing

---

## 🧪 PHASE 2: FULL TEST SUITE EXECUTION (Today - 2 hours)

### Unit Tests (30 minutes)

- [ ] **backend/shared/tests/test_validators.py**
  - Expected: ✅ PASS
  - Command: `pytest backend/shared/tests/test_validators.py -v`
  
- [ ] **backend/engine-a/tests/test_risk.py**
  - Expected: ✅ PASS
  - Command: `pytest backend/engine-a/tests/test_risk.py -v`
  
- [ ] **backend/engine-c/tests/test_dhan_integration.py**
  - Expected: ✅ PASS
  - Command: `pytest backend/engine-c/tests/test_dhan_integration.py -v`

### Integration Tests (45 minutes)

- [ ] **tools/verification/test_complete_e2e.py**
  - Expected: ✅ PASS
  - Command: `pytest tools/verification/test_complete_e2e.py -v`
  
- [ ] **Paper Trading Tests**
  - Expected: ✅ PASS (order fill simulation, slippage modeling, P&L calculation)
  
- [ ] **Webhook Verification Tests**
  - Expected: ✅ PASS (HMAC-SHA256, timing attack protection, payload validation)

### Verification Tests (30 minutes)

- [ ] **All tools/verification/test_*.py files**
  - Expected: ✅ PASS (50+ tests)
  - Command: `pytest tools/verification/ -v --tb=short`

### Test Results Summary

| Test Category | Count | Status | Pass Rate |
|---------------|-------|--------|-----------|
| Unit Tests | 10+ | ✅ | >95% |
| Integration Tests | 20+ | ✅ | >90% |
| E2E Tests | 20+ | ✅ | >85% |
| **TOTAL** | **50+** | ✅ | **>90%** |

### Sign-Off: QA Lead
- [ ] All tests executed
- [ ] Pass rate >90%
- [ ] No critical failures
- [ ] Performance acceptable (p95 <2s)
- [ ] Ready for staging deployment

---

## 🌐 PHASE 3: STAGING DEPLOYMENT (Today → Tomorrow - 2 hours)

### Pre-Deployment Checks

- [ ] All commits pushed to main
  - Command: `git log --oneline -1`
  - Expected: Latest commit = Phase 3
  
- [ ] No uncommitted changes
  - Command: `git status`
  - Expected: "working tree clean"
  
- [ ] Docker images available in Artifact Registry
  - Command: `gcloud container images list --project=galvanic-pulsar-482815-h0`
  - Expected: engine-a, engine-b, engine-c images present

### Staging Service Deployment

- [ ] **Deploy Engine A Staging**
  ```bash
  gcloud run deploy engine-a-staging \
    --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-a:latest \
    --set-env-vars="ENVIRONMENT=staging,DEBUG=true" \
    --region=us-central1 \
    --max-instances=2 \
    --project=galvanic-pulsar-482815-h0
  ```
  - [ ] Deployment successful
  - [ ] Status: Running
  - [ ] URL: `https://engine-a-staging-XXXX.a.run.app`

- [ ] **Deploy Engine B Staging**
  ```bash
  gcloud run deploy engine-b-staging \
    --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-b:latest \
    --set-env-vars="ENVIRONMENT=staging,DEBUG=true" \
    --region=us-central1 \
    --max-instances=2 \
    --project=galvanic-pulsar-482815-h0
  ```
  - [ ] Deployment successful
  - [ ] Status: Running
  - [ ] URL: `https://engine-b-staging-XXXX.a.run.app`

- [ ] **Deploy Engine C Staging**
  ```bash
  gcloud run deploy engine-c-staging \
    --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-c:latest \
    --set-env-vars="ENVIRONMENT=staging,DEBUG=true,TRADING_MODE=paper" \
    --region=us-central1 \
    --max-instances=2 \
    --project=galvanic-pulsar-482815-h0
  ```
  - [ ] Deployment successful
  - [ ] Status: Running
  - [ ] URL: `https://engine-c-staging-XXXX.a.run.app`

### Staging Verification

- [ ] **Health Checks Passing**
  - [ ] `curl https://engine-a-staging-XXXX.a.run.app/health` → 200 OK
  - [ ] `curl https://engine-b-staging-XXXX.a.run.app/health` → 200 OK
  - [ ] `curl https://engine-c-staging-XXXX.a.run.app/health` → 200 OK

- [ ] **CORS Configured**
  - [ ] Localhost requests blocked ✅
  - [ ] Production origins allowed ✅
  - [ ] Headers returned correctly ✅

- [ ] **Paper Trading Enabled**
  - [ ] TRADING_MODE=paper ✅
  - [ ] Orders fill with slippage ✅
  - [ ] No real money transferred ✅

- [ ] **Logging Enabled**
  - [ ] DEBUG=true ✅
  - [ ] Logs visible in Cloud Logging ✅
  - [ ] No sensitive data in logs ✅

### Sign-Off: Engineering Lead
- [ ] All staging services deployed
- [ ] Health checks passing
- [ ] CORS working correctly
- [ ] Paper trading active
- [ ] Logging functional
- [ ] Ready for UAT

---

## ✅ PHASE 4: UAT (User Acceptance Testing) - Tomorrow - 4 hours

### Test Case 1: Account Setup (30 minutes)

- [ ] User can create account via Google auth
- [ ] Profile setup completed successfully
- [ ] Email verified
- [ ] Status: ✅ PASS

### Test Case 2: DhanHQ Connection (30 minutes)

- [ ] User can connect DhanHQ credentials
- [ ] API key validated
- [ ] Connection test successful
- [ ] Account balance retrieved
- [ ] Status: ✅ PASS

### Test Case 3: Paper Trading (45 minutes)

- [ ] User can place BUY order (MARKET type)
- [ ] Order fills with realistic slippage
- [ ] Portfolio state updates correctly
- [ ] Can place SELL order to close
- [ ] P&L calculation accurate
- [ ] Status: ✅ PASS

### Test Case 4: Dashboard (30 minutes)

- [ ] Portfolio summary displays
- [ ] Account balance shows
- [ ] Order history visible
- [ ] Trading signals visible
- [ ] Risk metrics displayed
- [ ] Status: ✅ PASS

### Test Case 5: Mobile Access (30 minutes)

- [ ] Platform accessible on mobile
- [ ] Responsive layout works
- [ ] Can place orders on mobile
- [ ] All features functional
- [ ] Status: ✅ PASS

### UAT Sign-Off: Product Manager
- [ ] All test cases passed
- [ ] User experience acceptable
- [ ] No critical usability issues
- [ ] Features meet requirements
- [ ] Ready for performance testing

---

## 📈 PHASE 5: PERFORMANCE TESTING (Wed-Thu - 4 hours)

### Load Test Execution

- [ ] **1000 Concurrent Users**
  - [ ] Test duration: 30 minutes
  - [ ] Ramp-up time: 5 minutes
  - [ ] Constant load: 25 minutes
  
- [ ] **Order Placement at Scale**
  - [ ] Create order rate: 100+ orders/second
  - [ ] Expected p50 latency: <500ms
  - [ ] Expected p95 latency: <1000ms
  - [ ] Expected p99 latency: <2000ms

### Performance Results

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| p50 Latency | <500ms | ___ | ✅/❌ |
| p95 Latency | <1000ms | ___ | ✅/❌ |
| p99 Latency | <2000ms | ___ | ✅/❌ |
| Error Rate | <0.1% | ___ | ✅/❌ |
| Throughput | >100 req/s | ___ | ✅/❌ |

### Auto-scaling Verification

- [ ] Services scaled up under load
- [ ] Max instances reached appropriately
- [ ] Services scaled back after load
- [ ] No OOM errors
- [ ] Databases handled concurrency

### Sign-Off: Engineering Lead
- [ ] Performance targets met
- [ ] No bottlenecks identified
- [ ] Auto-scaling works correctly
- [ ] Database handles load
- [ ] Ready for security audit

---

## 🔒 PHASE 6: SECURITY AUDIT (Thursday - 2 hours)

### CORS Security Verification

- [ ] ✅ Localhost blocked: `curl -H "Origin: http://localhost:3000" ...` → no CORS header
- [ ] ✅ Production allowed: `curl -H "Origin: https://infinityai.pro" ...` → CORS header present
- [ ] ✅ Wildcard origins: Not used
- [ ] ✅ Credentials mode: Configured

### API Security

- [ ] ✅ HTTPS enforced (no HTTP redirects)
- [ ] ✅ TLS 1.3 configured
- [ ] ✅ Rate limiting active
- [ ] ✅ Input validation enabled

### Data Protection

- [ ] ✅ Encryption at rest: AES-256-GCM
- [ ] ✅ Encryption in transit: TLS 1.3
- [ ] ✅ KMS infrastructure: Ready
- [ ] ✅ Secrets in Secret Manager (not env vars)

### Authentication & Authorization

- [ ] ✅ Google OAuth working
- [ ] ✅ Session tokens valid
- [ ] ✅ IAM roles minimal
- [ ] ✅ No public admin endpoints

### Broker Integration Security

- [ ] ✅ Webhook signature verification: HMAC-SHA256
- [ ] ✅ Timing attack protection: Yes
- [ ] ✅ Paper trading mode: Default
- [ ] ✅ Credentials encrypted: Yes

### Audit Results

- [ ] No CRITICAL findings
- [ ] No HIGH findings
- [ ] MEDIUM findings: ___ (acceptable if <3)
- [ ] LOW findings: ___ (acceptable if <10)

### Sign-Off: Security Lead
- [ ] All security checks passed
- [ ] No critical vulnerabilities
- [ ] Medium/Low issues documented
- [ ] Mitigation plans in place
- [ ] Ready for production deployment

---

## 🎯 PHASE 7: PRODUCTION DEPLOYMENT (Friday - 2 hours)

### Pre-Production Final Checks

- [ ] UAT complete ✅
- [ ] Performance targets met ✅
- [ ] Security audit passed ✅
- [ ] All documentation reviewed ✅
- [ ] Staging stable for 24h+ ✅

### Production Backup

- [ ] Firestore data exported to GCS
  ```bash
  gcloud firestore export gs://infinityai-backups/$(date +%Y%m%d-%H%M%S)/
  ```
- [ ] Backup verified
- [ ] Backup location documented: `gs://infinityai-backups/[DATE]/`

### Production Deployment

- [ ] **Update Engine A**
  ```bash
  gcloud run deploy engine-a \
    --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-a:latest \
    --set-env-vars="ENVIRONMENT=production,DEBUG=false" \
    --region=us-central1 \
    --project=galvanic-pulsar-482815-h0
  ```
  - [ ] Deployment successful
  - [ ] No traffic loss
  - [ ] Revision: ___________

- [ ] **Update Engine B**
  ```bash
  gcloud run deploy engine-b \
    --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-b:latest \
    --set-env-vars="ENVIRONMENT=production,DEBUG=false" \
    --region=us-central1 \
    --project=galvanic-pulsar-482815-h0
  ```
  - [ ] Deployment successful
  - [ ] Models loaded
  - [ ] Revision: ___________

- [ ] **Update Engine C**
  ```bash
  gcloud run deploy engine-c \
    --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-c:latest \
    --set-env-vars="ENVIRONMENT=production,TRADING_MODE=paper,DEBUG=false" \
    --region=us-central1 \
    --project=galvanic-pulsar-482815-h0
  ```
  - [ ] Deployment successful
  - [ ] Paper trading active
  - [ ] Webhook verification enabled
  - [ ] Revision: ___________

- [ ] **Update Frontend**
  ```bash
  firebase deploy --only hosting --project=galvanic-pulsar-482815-h0
  ```
  - [ ] Build successful
  - [ ] Deployment successful
  - [ ] Version: ___________

### Post-Deployment Verification

- [ ] All health checks passing
  - [ ] `curl https://engine-a-3acobgd3qa-uc.a.run.app/health` → 200 OK
  - [ ] `curl https://engine-b-3acobgd3qa-uc.a.run.app/health` → 200 OK
  - [ ] `curl https://engine-c-3acobgd3qa-uc.a.run.app/health` → 200 OK

- [ ] Frontend accessible
  - [ ] `https://galvanic-pulsar-482815-h0.web.app/` → loading
  
- [ ] CORS working
  - [ ] Localhost blocked ✅
  - [ ] Production allowed ✅
  
- [ ] Logging functional
  - [ ] No errors in Cloud Logging
  - [ ] Metrics visible

### Sign-Off: CTO
- [ ] All deployments successful
- [ ] No errors observed
- [ ] Services responding
- [ ] Ready for monitoring

---

## 📊 PHASE 8: MONITORING (24-48 hours - Fri → Sun)

### Hour-by-Hour Monitoring (First 24 hours)

- [ ] **Hour 1-4**: Check health every 30 minutes
  - [ ] CPU usage < 60%
  - [ ] Memory usage < 70%
  - [ ] Error rate < 0.1%
  - [ ] p95 latency < 1s

- [ ] **Hour 5-12**: Check health every 1 hour
  - [ ] All metrics normal
  - [ ] No service restarts
  - [ ] CORS headers correct
  - [ ] Webhook signatures validating

- [ ] **Hour 13-24**: Check health every 2 hours
  - [ ] Sustained performance
  - [ ] No anomalies
  - [ ] Database queries normal
  - [ ] Backups running

### 24-Hour Post-Deployment Report

```
PRODUCTION DEPLOYMENT - 24 HOUR REPORT

Date: ___________
Status: [HEALTHY/WARNING/CRITICAL]

Metrics Summary:
- Uptime: ___% (target: >99.9%)
- Error Rate: ___% (target: <0.1%)
- p95 Latency: ___ms (target: <1000ms)
- Unique Users: ____
- Transactions: ____

Issues: [None/List any issues and resolutions]

Sign-off:
- On-Call Engineer: ___________
- Engineering Lead: ___________
```

### 48-Hour Post-Deployment Report

```
PRODUCTION DEPLOYMENT - 48 HOUR REPORT

Date: ___________
Status: [HEALTHY/WARNING/CRITICAL]

Key Metrics:
- Uptime: ___% 
- Error Rate: ___%
- Average Latency: ___ms
- Peak Users: ____
- Total Transactions: ____

Observations:
- [Observation 1]
- [Observation 2]

Action Items:
- [Action 1]: [Owner]
- [Action 2]: [Owner]

Sign-off:
- On-Call Engineer: ___________
- Engineering Lead: ___________
- CTO: ___________
```

### Sign-Off: On-Call Engineer + Engineering Lead
- [ ] 24-hour period completed successfully
- [ ] All metrics within targets
- [ ] No critical issues
- [ ] System stable
- [ ] Ready for regular operations

---

## 🎉 DEPLOYMENT COMPLETE

**Date Completed**: ___________  
**Total Duration**: 8-10 days  
**Status**: 🟢 **PRODUCTION LIVE**

### Final Sign-Offs

- [ ] **QA Lead**: _____________________ Date: _____
- [ ] **Engineering Lead**: _____________________ Date: _____
- [ ] **Product Manager**: _____________________ Date: _____
- [ ] **Security Lead**: _____________________ Date: _____
- [ ] **CTO**: _____________________ Date: _____

### Post-Deployment Actions

- [ ] Announce deployment to stakeholders
- [ ] Update documentation with final URLs
- [ ] Schedule retrospective meeting
- [ ] Plan Phase 4 features
- [ ] Setup ongoing monitoring

---

**Next Steps**: Begin Phase 8 monitoring and transition to regular operations.
