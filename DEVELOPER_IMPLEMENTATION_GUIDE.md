# 👨‍💻 DEVELOPER IMPLEMENTATION GUIDE

**Target**: Engineering team implementing credential sync fixes
**Difficulty**: Easy (straightforward code additions)
**Time Estimate**: 30 minutes
**Risk Level**: Low

---

## Pre-Implementation Checklist

- [ ] Read `INCIDENT_ANALYSIS_CREDENTIAL_SYNC_TIMING.md`
- [ ] Review `REMEDIATION_ACTION_PLAN.md`
- [ ] Understand root cause: Firestore eventual consistency race condition
- [ ] Have write access to backend/engine-c and frontend/web-app
- [ ] Node.js 18+ and Python 3.9+ installed locally
- [ ] Firebase CLI and gcloud CLI configured

---

## Implementation Steps

### STEP 1: Backend Retry Logic (10 mins)

**File**: `backend/engine-c/src/main.py`

**Location**: Around line 715, function `get_dhan_client_async`

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
        # ... rest of code ...
```

**New Code**:
```python
async def get_dhan_client_async(user_id: str, retry_count: int = 0, start_time: float = None) -> dhanhq:
    """
    Async version: Create authenticated DhanHQ client for a specific user.
    Uses GCP Secret Manager for credentials.

    **WITH RETRY LOGIC**: Retries up to 3 times with exponential backoff
    to handle Firestore eventual consistency delays.
    """
    import time
    import asyncio

    if start_time is None:
        start_time = time.time()

    MAX_RETRIES = 3
    RETRY_DELAYS = [0.1, 0.2, 0.4]  # 100ms, 200ms, 400ms

    try:
        creds_manager = get_credentials_manager()
        creds = await creds_manager.get_user_credentials(user_id)
        resolved_user_id = user_id

        # If no direct match, try locating by Dhan client_id (numeric user_id from frontend)
        if not creds and user_id and user_id.isdigit():
            creds = await creds_manager.find_credentials_by_client_id(user_id)
            if creds:
                resolved_user_id = creds.get("user_id", user_id)

        if creds:
            credentials = creds.get("credentials", {})
            client_id = credentials.get("client_id")
            access_token = credentials.get("access_token")

            if client_id and access_token:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(f"✅ DhanHQ client created for user {resolved_user_id} in {elapsed_ms:.0f}ms on attempt {retry_count + 1}")
                return dhanhq(client_id, access_token)

        # RETRY LOGIC: If credentials not found and haven't exhausted retries
        if retry_count < MAX_RETRIES:
            wait_time = RETRY_DELAYS[retry_count]
            logger.warning(f"⚠️ Credentials not found for {user_id}. "
                          f"Retrying in {wait_time*1000:.0f}ms (attempt {retry_count + 2}/{MAX_RETRIES + 1})")
            await asyncio.sleep(wait_time)
            return await get_dhan_client_async(user_id, retry_count + 1, start_time)

        # Failed after all retries
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"❌ User credentials not found for {user_id} after {elapsed_ms:.0f}ms and {MAX_RETRIES} retries")
        raise HTTPException(status_code=401, detail="User credentials not found or invalid")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user credentials for {user_id}: {e}")
        raise HTTPException(status_code=401, detail="User credentials not found or invalid")
```

**Changes Made**:
1. Added `retry_count` and `start_time` parameters to track retries
2. Added `MAX_RETRIES = 3` and `RETRY_DELAYS` array
3. When credentials not found, sleep for increasing duration then retry
4. Added detailed logging showing which retry attempt succeeded
5. Maintains backward compatibility (can still call without retry parameters)

**Testing**:
```bash
# Test 1: Normal path (should not retry)
curl "http://localhost:8000/api/v1/user/raghuyuvi10@gmail.com/account"

# Test 2: Simulate missing creds (will retry and fail after 3 attempts)
# Manually delete Firestore doc before running
```

---

### STEP 2: Frontend Error Handling (10 mins)

**File**: `frontend/web-app/src/hooks/useApi.ts`

**Location**: Around line 181, function `useUserAccount`

**Current Code**:
```typescript
export function useUserAccount() {
  const { userProfile, setFunds, setUserProfile, setDematData } = useAppStore();
  const userId = userProfile?.userId || getStoredUserId();

  return useQuery({
    queryKey: ['userAccount', userId],
    queryFn: async () => {
      // ... implementation ...
    },
    refetchInterval: 15000,
    staleTime: 10000,
    enabled: !!userId,
    retry: 2,
  });
}
```

**New Code**:
```typescript
export function useUserAccount() {
  const { userProfile, setFunds, setUserProfile, setDematData } = useAppStore();
  const userId = userProfile?.userId || getStoredUserId();

  return useQuery({
    queryKey: ['userAccount', userId],
    queryFn: async () => {
      if (!userId) {
        throw new Error('No user ID available');
      }

      const res = await engineC.getUserAccount(userId);

      if (res.status === 'success') {
        // Update funds in store
        if (res.funds) {
          setFunds({
            availableBalance: res.funds.availabelBalance || res.funds.availableBalance || 0,
            sodLimit: res.funds.sodLimit || 0,
            collateralAmount: res.funds.collateralAmount || res.funds.utilizedAmount || 0,
            dhanClientId: res.funds.dhanClientId || userId,
          });
        }

        // Update user profile if needed
        if (!userProfile?.isConnected) {
          setUserProfile({
            userId: userId,
            clientId: res.user_id || userId,
            name: res.name || res.user_name || `User ${res.user_id || userId}`,
            email: '',
            isConnected: true,
            isVerified: true,
          });
        }

        // Update demat data
        setDematData({
          holdings: {
            totalValue: res.holdings?.total_value || 0,
            count: res.holdings?.count || 0,
            items: Array.isArray(res.holdings?.data) ? res.holdings.data : [],
          },
          positions: {
            totalPnl: res.positions?.total_pnl || res.account_summary?.total_positions_pnl || 0,
            count: res.positions?.count || 0,
            items: Array.isArray(res.positions?.data) ? res.positions.data : [],
          },
          funds: {
            availableBalance: res.funds?.availabelBalance || res.funds?.availableBalance || 0,
            utilisedMargin: res.funds?.utilizedAmount || 0,
            totalBalance: (res.funds?.availabelBalance || 0) + (res.funds?.collateralAmount || 0),
          },
        });

        return res;
      }

      throw new Error(res.detail || 'Failed to fetch user account');
    },
    refetchInterval: 15000, // 15 seconds for real-time updates
    staleTime: 10000,
    enabled: !!userId,

    // **IMPROVED RETRY LOGIC**: Exponential backoff with smart error handling
    retry: (failureCount, error: any) => {
      console.log(`useUserAccount retry attempt ${failureCount + 1}`, error);

      // Don't retry 401 (authentication error) - user needs to fix credentials
      if (error?.status === 401) {
        logger.warn('Auth error (401) - not retrying. User needs to verify credentials.');
        return false;
      }

      // Retry 404 and 500 errors (transient) up to 2 times
      if (error?.status === 404 || error?.status === 500) {
        if (failureCount < 2) {
          logger.warn(`Transient error (${error?.status}). Retry attempt ${failureCount + 2}/3`);
          return true;
        }
      }

      // For network errors, retry up to 2 times
      if (!error?.status) {
        if (failureCount < 2) {
          logger.warn(`Network error. Retry attempt ${failureCount + 2}/3`);
          return true;
        }
      }

      return false;
    },

    // **IMPROVED ERROR HANDLING**: Don't immediately disconnect on transient errors
    onError: (error: any) => {
      console.error('useUserAccount error:', error);

      // Transient errors (404/500) - don't change connection state
      if (error?.status === 404 || error?.status === 500) {
        logger.warn(`Transient error ${error?.status}. Keeping existing state, will retry on next interval.`);
        return; // Don't update profile
      }

      // Network errors - keep existing state
      if (!error?.status) {
        logger.warn('Network error. Keeping existing state, will retry automatically.');
        return; // Don't update profile
      }

      // Only disconnect on genuine auth failure (401)
      if (error?.status === 401 && userProfile?.isConnected) {
        logger.error('Auth error (401). Credentials may be invalid.');
        setUserProfile({
          ...userProfile,
          isConnected: false,
          isVerified: false
        });
      }
    }
  });
}
```

**Changes Made**:
1. Added `retry` function that intelligently handles different error types
2. Returns `false` for 401 (don't retry auth errors)
3. Returns `true` for 404/500 (retry transient errors)
4. Added `onError` handler to preserve state on transient errors
5. Added detailed console logging for debugging
6. Only sets `isConnected: false` on genuine 401 errors

**Testing**:
```bash
# Build and test
npm run build

# Test 1: Fresh credential load
# 1. Dashboard should show data within 2 seconds
# 2. Check browser console - should see "retry attempt" messages
# 3. Final data should load successfully

# Test 2: Simulate 404 error
# 1. Manually return 404 from backend temporarily
# 2. Verify frontend auto-retries (check console)
# 3. After 2 retries, shows error but doesn't disconnect
```

---

### STEP 3: Add Logging (5 mins)

**File**: `backend/engine-c/src/main.py`

**Add near top of file** (after other imports):
```python
import time
import logging

# Set up structured logging for debugging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
```

**Add detailed logs in get_dhan_client_async** (already included in Step 1):
```python
# Existing logger calls will now provide detailed timing info
logger.info(f"✅ DhanHQ client created for {user_id} in {elapsed_ms:.0f}ms on attempt {retry_count + 1}")
logger.warning(f"⚠️ Credentials not found. Retrying in {wait_time*1000:.0f}ms...")
logger.error(f"❌ Credentials not found after {elapsed_ms:.0f}ms and {MAX_RETRIES} retries")
```

**Test Logging**:
```bash
# View logs locally
gcloud functions logs read getDhanOverview --limit=50

# Search for our new messages
gcloud functions logs read getDhanOverview --limit=100 | grep "DhanHQ client\|Retrying\|elapsed"
```

---

## Verification Steps

### Local Testing

```bash
# Test 1: Start local backend
cd backend/engine-c
python main.py

# Test 2: Start local frontend
cd ../../frontend/web-app
npm run dev

# Test 3: Manual credential workflow
# 1. Open http://localhost:3000
# 2. Go to Settings → Dhan Account
# 3. Enter test credentials
# 4. Go to Dashboard
# 5. Should see account data load quickly
# 6. Check browser console for no 404 errors
```

### Integration Testing

```bash
# Test in staging environment
# 1. Deploy to Cloud Run staging
# 2. Run credential update test
# 3. Monitor logs for retry messages
# 4. Verify success rate >99%
```

### Production Testing

```bash
# Monitor after production deployment
gcloud functions logs read getDhanOverview --project=galvanic-pulsar-482815-h0 | grep "attempt\|Retry"

# Check error rate
gcloud monitoring time-series list --filter='metric.type=cloudfunctions.googleapis.com/execution_count'
```

---

## Common Issues During Implementation

### Issue 1: Import Error - `asyncio` not available
**Solution**: Add `import asyncio` at top of file

### Issue 2: Logger not defined
**Solution**: Ensure logger is initialized: `logger = logging.getLogger(__name__)`

### Issue 3: Frontend retry not working
**Solution**: Check that react-query version supports retry function (v4.0+)

### Issue 4: Typescript compilation errors
**Solution**: Run `npm run typecheck` to validate types

---

## Performance Expectations

### Before Fixes
- **Cold start** (fresh credentials): 404 error, then retry manually
- **Latency**: 15+ seconds (includes manual retry)
- **User experience**: Error shown, manual intervention needed

### After Fixes
- **Cold start**: Auto-retries, succeeds within 2 seconds
- **Latency**: <2 seconds (including automatic retries)
- **User experience**: Transparent, no error shown

---

## Rollback Procedure

If issues arise post-deployment:

```bash
# Quick revert (keeps git history)
git revert <commit-hash>

# Deploy reverted code
gcloud functions deploy getDhanOverview \
  --source=backend/engine-c \
  --project=galvanic-pulsar-482815-h0

# Deploy reverted frontend
firebase deploy --only hosting
```

---

## Code Review Checklist

When submitting PR, verify:
- [ ] All imports added (`asyncio`, `time`)
- [ ] Logger calls use correct format strings
- [ ] Retry counts and delays match spec (3 retries, 100/200/400ms)
- [ ] Error handling preserves backward compatibility
- [ ] No hardcoded values (use constants)
- [ ] TypeScript/Python syntax correct
- [ ] No console.log() left in production code
- [ ] Comments explain retry logic
- [ ] Tests pass locally
- [ ] No breaking changes to API

---

## Deployment Commands

```bash
# 1. Backend deployment
cd backend/engine-c
gcloud functions deploy getDhanOverview \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --project=galvanic-pulsar-482815-h0 \
  --region=us-central1 \
  --source=. \
  --entry-point=app

# 2. Frontend deployment
cd ../../frontend/web-app
firebase deploy --only hosting --project=galvanic-pulsar-482815-h0

# 3. Verify deployment
gcloud functions describe getDhanOverview --project=galvanic-pulsar-482815-h0
```

---

## Monitoring After Deployment

### Key Metrics to Watch

```bash
# 1. Error rate (should drop from 5% to <0.1%)
gcloud monitoring time-series list \
  --filter='resource.type=cloud_function AND metric.type=cloudfunctions.googleapis.com/execution_count'

# 2. Response latency (should be <2 seconds)
gcloud monitoring time-series list \
  --filter='resource.type=cloud_function AND metric.type=cloudfunctions.googleapis.com/execution_times'

# 3. Check for "attempt X" in logs (indicates retries)
gcloud functions logs read getDhanOverview --limit=100 | grep "attempt"
```

---

**Status**: Ready to implement
**Estimated Time**: 30 minutes
**Difficulty**: Easy
**Risk**: Low

Begin with Step 1 (Backend), then Step 2 (Frontend), then Step 3 (Logging).
