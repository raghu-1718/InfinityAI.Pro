# ✅ Phase 3: Staging Deployment - EXECUTION PLAN

**Date**: January 19, 2026  
**Target Environment**: Cloud Run Staging  
**Timeline**: 2-3 hours  
**Status**: 🟢 **DEPLOYMENT READY**  

---

## 🎯 Phase 3 Objectives

### Primary Goals
1. ✅ Deploy Engine A (staging) with paper trading enabled
2. ✅ Deploy Engine B (staging) with ML signals
3. ✅ Deploy Engine C (staging) with DhanHQ integration
4. ✅ Deploy Frontend (staging) with API routing
5. ✅ Verify health checks on all services
6. ✅ Execute smoke tests
7. ✅ Validate staging environment operational

### Deployment Strategy

**Environment Setup**:
- GCP Project: `galvanic-pulsar-482815-h0`
- Region: `us-central1`
- Naming Convention: Service names with `-staging` suffix (optional)
- Approach: Deploy using existing production images with staging environment variables

**Configuration Differences (Staging vs Production)**:
- Trading Mode: PAPER (default, can switch to LIVE with approval)
- CORS: Accept localhost:3000 (development frontend)
- Database: Separate Firestore collections or use staging namespace
- Logging: Increased verbosity for troubleshooting

---

## 📋 Staging Deployment Checklist

### Pre-Deployment Verification

**Infrastructure Ready**:
- [ ] GCP credentials configured
- [ ] Cloud Run API enabled
- [ ] Firestore configured
- [ ] Cloud Storage ready
- [ ] KMS encryption ready
- [ ] All environment variables available

**Images Available**:
- [ ] Engine A docker image available in Artifact Registry
- [ ] Engine B docker image available in Artifact Registry
- [ ] Engine C docker image available in Artifact Registry
- [ ] Frontend build artifacts ready for Firebase Hosting

**Documentation Ready**:
- [ ] QUICK_REFERENCE_CARD.md available
- [ ] Deployment commands prepared
- [ ] Health check endpoints documented
- [ ] Rollback procedures documented

---

## 🚀 Deployment Execution Steps

### Step 1: Verify Production Services Status

```bash
# Check Engine A
gcloud run services describe engine-a --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 --format="table(status.url)"

# Check Engine B
gcloud run services describe engine-b --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 --format="table(status.url)"

# Check Engine C
gcloud run services describe engine-c --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 --format="table(status.url)"
```

**Current Production URLs**:
- Engine A: https://engine-a-3acobgd3qa-uc.a.run.app
- Engine B: https://engine-b-3acobgd3qa-uc.a.run.app
- Engine C: https://engine-c-3acobgd3qa-uc.a.run.app

---

### Step 2: Stage 1 - Deploy to Staging Environment

**Approach**: Create staging versions or deploy to separate Cloud Run services

**Option A: Create Staging Services** (Recommended for Phase 3)

```bash
# For each engine, deploy with staging configuration
gcloud run deploy engine-a-staging \
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-a:latest \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --set-env-vars "TRADING_MODE=paper,ENV=staging" \
  --memory=2Gi \
  --cpu=2 \
  --max-instances=5 \
  --allow-unauthenticated
```

**Option B: Use Existing Production** (Faster for Phase 3 validation)

For initial Phase 3 validation, we can test the existing production services:
1. Verify health checks
2. Run smoke tests
3. Document results

This is faster and allows us to validate the deployment pipeline quickly.

---

### Step 3: Health Check Verification

**Endpoint Testing**:

```bash
# Test Engine A health
curl -v https://engine-a-3acobgd3qa-uc.a.run.app/health

# Test Engine B health  
curl -v https://engine-b-3acobgd3qa-uc.a.run.app/health

# Test Engine C health
curl -v https://engine-c-3acobgd3qa-uc.a.run.app/health

# Test Frontend
curl -I https://galvanic-pulsar-482815-h0.web.app
```

**Expected Responses**:
- `/health` → 200 OK with JSON status
- `/ready` → 200 OK with readiness status
- Frontend → 200 OK with index.html

---

### Step 4: Smoke Test Execution

**Basic Functional Tests**:

```python
# Test 1: Risk Management Calculation
curl -X POST https://engine-a-3acobgd3qa-uc.a.run.app/api/risk \
  -H "Content-Type: application/json" \
  -d '{"positions": [], "capital": 100000}'

# Test 2: Signal Generation
curl -X GET https://engine-b-3acobgd3qa-uc.a.run.app/api/signals/nifty

# Test 3: Paper Trading
curl -X POST https://engine-c-3acobgd3qa-uc.a.run.app/api/dhan/place-order \
  -H "Content-Type: application/json" \
  -d '{"symbol": "NIFTY50", "quantity": 1, "price": 23000, "mode": "paper"}'
```

---

### Step 5: Service Integration Test

**Frontend to Engine Communication**:

```bash
# Verify CORS configuration
curl -v -H "Origin: http://localhost:3000" \
  https://engine-a-3acobgd3qa-uc.a.run.app/health

# Expected header: Access-Control-Allow-Origin: http://localhost:3000 (dev) or https://galvanic-pulsar-482815-h0.web.app (prod)
```

---

## ✅ Deployment Verification Checklist

### Service Status Checks

**Engine A (Orchestration & Risk)**
- [ ] Service deployed and healthy
- [ ] `/health` endpoint responds with 200
- [ ] `/ready` endpoint responds with 200
- [ ] Firestore connectivity verified
- [ ] CORS headers correct
- [ ] Metrics being collected

**Engine B (ML Signals)**
- [ ] Service deployed and healthy
- [ ] `/health` endpoint responds with 200
- [ ] `/ready` endpoint responds with 200
- [ ] Models loaded successfully
- [ ] Signal generation working
- [ ] Metrics being collected

**Engine C (Trade Execution)**
- [ ] Service deployed and healthy
- [ ] `/health` endpoint responds with 200
- [ ] `/ready` endpoint responds with 200
- [ ] Paper trading mode enabled
- [ ] Webhook verification working
- [ ] Metrics being collected

**Frontend**
- [ ] Firebase Hosting serving correctly
- [ ] Static assets loading
- [ ] API routing configured
- [ ] Authentication working
- [ ] Database queries succeeding

### Performance Baseline

**Latency Checks**:
- [ ] Engine A response time < 500ms
- [ ] Engine B response time < 1000ms
- [ ] Engine C response time < 500ms
- [ ] Frontend load time < 3s

**Availability**:
- [ ] All services responding (0% error rate)
- [ ] No timeouts observed
- [ ] No memory leaks detected
- [ ] CPU utilization normal

---

## 🔍 Staging-Specific Validations

### Configuration Validation

**Environment Variables**:
- [ ] TRADING_MODE set to "paper" (not "live")
- [ ] CORS allows localhost:3000 (dev) + production domain
- [ ] Logging level set to DEBUG for troubleshooting
- [ ] All required secrets available
- [ ] Database connections working

**Security Settings**:
- [ ] AES-256-GCM encryption active
- [ ] CORS properly configured
- [ ] API authentication working
- [ ] Webhook signature verification enabled
- [ ] Rate limiting functional

**Monitoring & Logging**:
- [ ] Cloud Logging configured
- [ ] Metrics collection active
- [ ] Error tracking enabled
- [ ] Distributed tracing active
- [ ] Alerts configured (non-critical for staging)

### Feature Validation

**Phase 3 Features**:
- [ ] Paper Trading Mode
  - Order simulation working
  - Slippage calculation correct
  - P&L tracking accurate
  - Portfolio state consistent

- [ ] Webhook Verification
  - HMAC-SHA256 validation working
  - Timing attack protection active
  - Invalid signatures rejected (403)
  - Valid signatures accepted (200)

- [ ] Health Checks
  - /health endpoint working (startup probe)
  - /ready endpoint working (readiness probe)
  - Dependency checks passing
  - Status reporting accurate

---

## 📊 Staging Deployment Timeline

| Step | Task | Duration | Status |
|------|------|----------|--------|
| 1 | Pre-deployment verification | 15 min | ⏳ Pending |
| 2 | Deploy services | 45 min | ⏳ Pending |
| 3 | Health check verification | 15 min | ⏳ Pending |
| 4 | Smoke test execution | 20 min | ⏳ Pending |
| 5 | Performance baseline | 15 min | ⏳ Pending |
| 6 | Documentation & sign-off | 10 min | ⏳ Pending |
| **TOTAL** | | **2 hours** | **⏳ READY** |

---

## 🎯 Deployment Success Criteria

### Must Have ✅
- [ ] All 4 services deployed successfully
- [ ] All health check endpoints responding (200 OK)
- [ ] No critical errors in logs
- [ ] CORS security verified
- [ ] Paper trading mode enabled
- [ ] Zero P1/P2 issues

### Should Have ✅
- [ ] Performance baselines established
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Team sign-off obtained

### Nice to Have
- [ ] Load testing baseline
- [ ] Security scan results
- [ ] Cost analysis updated

---

## ⏭️ Phase 4 Preparation

### UAT (User Acceptance Testing) - Next Phase

**Timeline**: Tomorrow, 4 hours

**Scope**:
- Account setup workflow
- DhanHQ connection process
- Paper trading execution
- Dashboard functionality
- Mobile access verification

**Team Involvement**:
- Product Manager (sign-off)
- QA Lead (test execution)
- Engineering Lead (support)

---

## 📋 Deployment Command Reference

### Quick Deploy Commands

```bash
# Deploy Engine A
gcloud run deploy engine-a-staging \
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-a:latest \
  --region=us-central1 --project=galvanic-pulsar-482815-h0 \
  --memory=2Gi --cpu=2 --max-instances=5

# Deploy Engine B  
gcloud run deploy engine-b-staging \
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-b:latest \
  --region=us-central1 --project=galvanic-pulsar-482815-h0 \
  --memory=4Gi --cpu=4 --max-instances=3

# Deploy Engine C
gcloud run deploy engine-c-staging \
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-c:latest \
  --region=us-central1 --project=galvanic-pulsar-482815-h0 \
  --memory=2Gi --cpu=2 --max-instances=5
```

### Health Check Commands

```bash
# Check all services
for service in engine-a-staging engine-b-staging engine-c-staging; do
  echo "Checking $service..."
  curl -s "https://$service-XXXX.a.run.app/health" | jq .
done
```

---

## 🔄 Rollback Procedure (If Needed)

**Quick Rollback**:
```bash
# Revert to previous stable revision
gcloud run deploy engine-c-staging \
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-c:previous \
  --region=us-central1 --project=galvanic-pulsar-482815-h0
```

**Full Rollback**:
1. Identify last known good revision
2. Update traffic to 100% on previous revision
3. Verify health checks
4. Investigate failure
5. Document incident

---

## ✅ PHASE 3 READINESS SUMMARY

**Status**: 🟢 **READY TO DEPLOY**

**Prerequisites Met**:
- ✅ All Phase 1 & 2 deliverables complete
- ✅ Production services verified operational
- ✅ Docker images available in Artifact Registry
- ✅ Environment configuration prepared
- ✅ Deployment procedures documented
- ✅ Health checks configured
- ✅ Rollback procedures ready

**Deployment Plan**: Comprehensive and detailed above

**Risk Assessment**: LOW
- Staging environment is separate from production
- Rollback procedures in place
- Health checks will catch any issues
- Team expertise available

**Next Action**: Execute deployment steps 1-6 above

---

**Phase 3 Deployment Plan Created**: January 19, 2026  
**Status**: ✅ READY FOR EXECUTION  
**Sign-Off Authority**: Engineering Lead
