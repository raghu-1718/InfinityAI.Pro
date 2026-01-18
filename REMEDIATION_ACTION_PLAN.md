# 🚀 REMEDIATION ACTION PLAN

## Quick Reference

**Problem**: ❌ 404 errors when fetching account data after credential update
**Root Cause**: Firestore eventual consistency + missing retry logic
**Solution**: Add automatic retry with exponential backoff
**Time to Fix**: 30 minutes
**Risk Level**: LOW

---

## Phase 1: Immediate Fix (Backend - 15 mins)

### Step 1: Update `get_dhan_client_async` with Retry Logic

**File**: `backend/engine-c/src/main.py` (around line 715)

**Current Code**:
```python
async def get_dhan_client_async(user_id: str) -> dhanhq:
    """
    Async version: Create authenticated DhanHQ client for a specific user.
    Uses GCP Secret Manager for credentials.
    """
    try:
        creds_manager = get_credentials_manager()
        creds = await creds_manager.get_user_credentials(user_id)
        # ... rest of function ...
```

**Action**: Replace with retry-enabled version from INCIDENT_ANALYSIS document (Fix 1 section)

**Testing**:
```bash
# Test 1: Normal credential retrieval
curl "http://localhost:8000/api/v1/user/raghuyuvi10@gmail.com/account" \
  -H "Authorization: Bearer $TOKEN"

# Test 2: Simulate credential not found (should retry and succeed)
# (Internal test - manually delete Firestore doc and re-add during function execution)
```

---

## Phase 2: Frontend Enhancement (15 mins)

### Step 2: Improve Error Handling in useUserAccount Hook

**File**: `frontend/web-app/src/hooks/useApi.ts` (around line 181)

**Add retry configuration** per Fix 2 in INCIDENT_ANALYSIS document

**Testing**:
```bash
# Build and test
npm run build

# Test 1: Fresh credential load
# 1. Go to Settings → Dhan Account
# 2. Enter credentials and Save
# 3. Go to Dashboard
# 4. Observe: Should fetch account data within 2 seconds (with retry)

# Test 2: Stale data refresh
# 1. Have credentials already saved
# 2. Go to Dashboard and verify balance updates
# 3. Check browser console for no 404 errors
```

---

## Phase 3: Monitoring & Observability (10 mins)

### Step 3: Add Logging to Track Issue

**File**: `backend/engine-c/src/main.py`

Add before `get_dhan_client_async`:
```python
import time
import asyncio

async def get_dhan_client_async_with_retry(user_id: str, retry_count: int = 0, start_time: float = None) -> dhanhq:
    """
    Async version with automatic retry for Firestore eventual consistency.
    """
    if start_time is None:
        start_time = time.time()

    MAX_RETRIES = 3
    RETRY_DELAYS = [0.1, 0.2, 0.4]

    try:
        creds_manager = get_credentials_manager()
        creds = await creds_manager.get_user_credentials(user_id)

        if creds:
            credentials = creds.get("credentials", {})
            client_id = credentials.get("client_id")
            access_token = credentials.get("access_token")

            if client_id and access_token:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(f"✅ DhanHQ client created for {user_id} in {elapsed_ms:.0f}ms on attempt {retry_count + 1}")
                return dhanhq(client_id, access_token)

        # Retry logic
        if retry_count < MAX_RETRIES:
            wait_time = RETRY_DELAYS[retry_count]
            logger.warning(f"⚠️ Credentials not found for {user_id}. "
                          f"Retrying in {wait_time*1000:.0f}ms (attempt {retry_count + 2}/{MAX_RETRIES + 1})")
            await asyncio.sleep(wait_time)
            return await get_dhan_client_async_with_retry(user_id, retry_count + 1, start_time)

        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"❌ Credentials not found for {user_id} after {elapsed_ms:.0f}ms and {MAX_RETRIES} retries")
        raise HTTPException(status_code=401, detail="User credentials not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user credentials for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail=str(e))

# Then update existing get_dhan_client_async to call this version
async def get_dhan_client_async(user_id: str) -> dhanhq:
    return await get_dhan_client_async_with_retry(user_id)
```

**Monitoring Dashboard**:
Create a simple endpoint to track metrics:
```python
@app.get("/api/v1/health/credentials-metrics")
async def get_credential_metrics():
    """Return metrics about credential retrieval performance"""
    return {
        "total_retrieval_attempts": logger.stats.get("credential_retrieval_attempts", 0),
        "successful_first_attempt": logger.stats.get("successful_first_attempt", 0),
        "retries_needed": logger.stats.get("retries_needed", 0),
        "avg_retrieval_time_ms": logger.stats.get("avg_retrieval_time_ms", 0),
        "last_error": logger.stats.get("last_credential_error", None)
    }
```

---

## Phase 4: Deployment & Validation

### Step 4: Deploy Changes

```bash
# 1. Create feature branch
git checkout -b fix/credential-sync-retry

# 2. Apply changes to main.py
# 3. Apply changes to useApi.ts

# 4. Test locally
cd backend/engine-c
python -m pytest tests/test_credentials.py -v

cd ../../frontend/web-app
npm test -- hooks/useApi.test.ts

# 5. Commit
git add -A
git commit -m "fix: Add automatic retry logic for credential retrieval

- Add exponential backoff retry to get_dhan_client_async()
- Improves resilience to Firestore eventual consistency delays
- Frontend now automatically retries on transient 404/500 errors
- Adds detailed logging for troubleshooting

Fixes: #ISSUE_NUMBER
"

# 6. Push and create PR
git push origin fix/credential-sync-retry
```

### Step 5: Verify in Production

**Immediate Tests** (first 30 minutes after deploy):
```bash
# 1. Monitor error logs
gcloud functions logs read getDhanOverview \
  --limit=100 --project=galvanic-pulsar-482815-h0 \
  | grep -E "Credentials|retry|ERROR"

# 2. Check success rate
# Look for: "DhanHQ client created" messages
# Expected: 100% success after first attempt

# 3. Test user credential workflow
# - Update credentials via dashboard
# - Check that account data loads within 2 seconds
# - Verify no 404 errors in browser console
```

**Extended Tests** (first 24 hours):
```bash
# 1. Monitor total 401 error rate
# Should be <0.1% (only genuine auth failures)

gcloud monitoring time-series list \
  --filter='resource.type=cloud_function AND metric.type=cloudfunctions.googleapis.com/execution_count AND resource.labels.function_name=getDhanOverview' \
  --format='table(metric.labels.status)'

# 2. Check average credential retrieval latency
# Should be <500ms including retry overhead

# 3. User satisfaction: Monitor for support tickets
# Should see 0 new reports about "404 errors after credential update"
```

---

## Phase 5: Long-term Improvements

### Step 6: Implement Advanced Monitoring (Next Sprint)

Add metrics to Cloud Monitoring:
```python
from google.cloud import monitoring_v3

def record_credential_retrieval_metric(user_id, success, elapsed_ms, retry_count):
    """Record credential retrieval metric"""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/credential_retrieval_latency"
    series.resource.type = "cloud_function"
    series.resource.labels['function_name'] = 'getUserAccount'

    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10 ** 9)
    interval = monitoring_v3.TimeInterval({"end_time": {"seconds": seconds, "nanos": nanos}})
    point = monitoring_v3.Point({"interval": interval, "value": {"double_value": elapsed_ms}})

    series.points = [point]
    series.metric.labels['success'] = str(success)
    series.metric.labels['retry_count'] = str(retry_count)

    client.create_time_series(request={'name': project_name, 'time_series': [series]})
```

---

## Rollback Plan

If issues arise after deployment:

```bash
# 1. Identify the issue
# - Check logs for any exception patterns
# - Review error rate spike

# 2. Quick rollback
git revert <commit-hash>
gcloud functions deploy getDhanOverview \
  --source=backend/engine-c/src \
  --project=galvanic-pulsar-482815-h0

# 3. Root cause analysis
# - Compare new code vs old code
# - Check if retry logic is causing issues
# - Review Secret Manager access patterns
```

**Rollback Success Criteria**:
- Error rate returns to baseline <5%
- No new error patterns appear
- Customer reports stop

---

## Success Criteria

✅ **Deployment Successful When**:
1. **No 404 errors** on account data fetch after credential update (within 2 seconds)
2. **Automatic retry** succeeds on first retry for fresh credentials
3. **Logging shows**: "DhanHQ client created... on attempt 1" for normal case
4. **Zero regressions** in other endpoints
5. **Support tickets** drop to zero for "404 after credential update"

✅ **Performance Criteria**:
- Credential retrieval latency: <500ms (including retry overhead)
- P99 latency: <1000ms
- Success rate: >99.9%
- Retry rate: <5% (only needed for fresh credentials)

---

## Timeline

| Phase | Task | Est. Time | Status |
|-------|------|-----------|--------|
| 1 | Backend retry logic | 15 min | ⏳ Ready |
| 2 | Frontend error handling | 15 min | ⏳ Ready |
| 3 | Logging & observability | 10 min | ⏳ Ready |
| 4 | Deploy to production | 10 min | ⏳ Ready |
| 5 | Validation & monitoring | Ongoing | ⏳ Ready |
| **Total** | **All phases** | **~1.5 hours** | **Ready** |

---

## Questions & Notes

**Q: Will this affect existing users?**
A: No. Retry logic is transparent. Existing users with stable credentials won't notice any change.

**Q: What about encryption key retrieval delays?**
A: The retry logic covers this. If encryption key lookup is slow, the retry will succeed once cached.

**Q: Can we reduce the retry delay further?**
A: Possibly to [50ms, 100ms, 200ms] but depends on Firestore SLA. Current delays are conservative.

**Q: What if a credential is genuinely invalid?**
A: Still returns 401 immediately after retries. Won't waste time on bad creds.

---

## Sign-Off

- **Identified by**: GitHub Copilot Agent
- **Reviewed by**: [Awaiting review]
- **Approved by**: [Awaiting approval]
- **Deployed by**: [To be completed]
- **Validated by**: [To be completed]

**Next Step**: Implement Phase 1 & 2 fixes, then deploy to production with monitoring enabled.
