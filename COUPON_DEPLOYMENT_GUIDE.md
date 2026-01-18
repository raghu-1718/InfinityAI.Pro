# Coupon System Update - Deployment & Testing Guide

**Date**: January 11, 2026
**Project**: galvanic-pulsar-482815-h0
**Update**: Migration to 8 new personalized coupons with dynamic email binding

---

## 📋 Summary of Changes

### Cloud Function: `verifyCoupon`
**File**: `frontend/functions/src/verifyCoupon.ts`
**Changes Made**:

1. **Removed 4 old coupons**:
   - ❌ INFINITY1718
   - ❌ INFINITY0506
   - ❌ INFINITYRAJ
   - ❌ TESTCOUPON

2. **Added 8 new personalized coupons**:
   - ✅ INFINITY_DAD
   - ✅ INFINITY_MOM
   - ✅ INFINITY_RAJ
   - ✅ INFINITY_SAI
   - ✅ INFINITY_PRIYA
   - ✅ INFINITY_RAGHU
   - ✅ INFINITY_KAVI
   - ✅ INFINITY_HARSHA

3. **Updated configuration**:
   - **All expiry**: Changed to 2027-01-11 (1 year)
   - **All max_uses**: Changed to 1 (single-user per coupon)
   - **All features**: Unified to full access (5 features each)

4. **Implemented dynamic email binding**:
   - **New validation**: Check `coupon_email_bindings` collection before redemption
   - **New logic**: Reject if coupon already bound to different email
   - **New collection**: Create email binding on first redemption
   - **Atomic**: All changes committed in single Firestore batch

---

## 🚀 Deployment Steps

### Step 1: Navigate to Functions Directory

```powershell
cd c:\workspace\InfinityAI.Pro\frontend\functions
```

### Step 2: Install/Update Dependencies

```powershell
npm install
```

### Step 3: Deploy Cloud Function

```powershell
firebase deploy --only functions:verifyCoupon --project=galvanic-pulsar-482815-h0
```

**Expected Output**:
```
i  deploying functions
i  functions: ensuring required API client-functions.googleapis.com is enabled...
i  functions: ensuring required API artifactregistry.googleapis.com is enabled...
...
✔  Deploy complete!

Function URL (verifyCoupon): https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/verifyCoupon
```

**Success Indicators**:
- ✅ No TypeScript compilation errors
- ✅ Deployment completes without errors
- ✅ Function URL is accessible
- ✅ Cloud Function shows in Firebase Console

### Step 4: Verify Firestore Collections

The following collections must exist (auto-created on first use):
- ✅ `coupon_usage` - Global coupon counters
- ✅ `user_coupons` - User redemption records
- ✅ `coupon_email_bindings` - Email-to-coupon bindings (NEW)
- ✅ `user_sessions` - Active user sessions
- ✅ `user_profiles` - User profile metadata

**Manual Verification**:
```powershell
# Check Firestore console
firebase firestore:get --project=galvanic-pulsar-482815-h0
```

---

## 🧪 Testing Strategy

### Test Case 1: Valid Coupon Redemption (First Use)

**Scenario**: User `dad@example.com` redeems `INFINITY_DAD`

**Request**:
```json
{
  "coupon_code": "INFINITY_DAD",
  "google_user_id": "user_dad_123",
  "google_email": "dad@example.com"
}
```

**Expected Response**:
```json
{
  "success": true,
  "session_id": "session_user_dad_123_1736553000000",
  "features": [
    "live_trading",
    "portfolio_analysis",
    "ai_signals",
    "vertex_ai",
    "engine_c_access"
  ],
  "expires_at": "2026-04-11T14:30:00.000Z"
}
```

**Firestore Verification**:
1. ✅ `coupon_usage/INFINITY_DAD` created with `total_uses: 1`
2. ✅ `user_coupons/user_dad_123_INFINITY_DAD` created
3. ✅ `coupon_email_bindings/INFINITY_DAD` created with `bound_email: dad@example.com`
4. ✅ `user_sessions/user_dad_123` created with all 5 features
5. ✅ `user_profiles/user_dad_123` updated with coupon info

---

### Test Case 2: Re-verification (Same User)

**Scenario**: User `dad@example.com` redeems `INFINITY_DAD` again (within 90 days)

**Request**:
```json
{
  "coupon_code": "INFINITY_DAD",
  "google_user_id": "user_dad_123",
  "google_email": "dad@example.com"
}
```

**Expected Response**:
```json
{
  "success": true,
  "session_id": "session_user_dad_123_1736553000000",  // Same session ID
  "features": [
    "live_trading",
    "portfolio_analysis",
    "ai_signals",
    "vertex_ai",
    "engine_c_access"
  ],
  "expires_at": "2026-04-11T14:30:00.000Z"  // Same expiry
}
```

**Behavior**:
- ✅ Returns existing session (no new binding created)
- ✅ Firestore unchanged (same batch not re-executed)
- ✅ Usage counter NOT incremented again

---

### Test Case 3: Different User Same Coupon (Rejection)

**Scenario**: User `mom@example.com` tries to redeem `INFINITY_DAD` (already bound to `dad@example.com`)

**Request**:
```json
{
  "coupon_code": "INFINITY_DAD",
  "google_user_id": "user_mom_456",
  "google_email": "mom@example.com"
}
```

**Expected Response**:
```json
{
  "code": "permission-denied",
  "message": "This coupon is already bound to dad@example.com. Each coupon can only be used by one email address."
}
```

**Behavior**:
- ✅ Function rejects with permission-denied error
- ✅ No Firestore modifications
- ✅ No new session created
- ✅ Usage counter NOT incremented

---

### Test Case 4: Invalid Coupon Code

**Scenario**: User tries to redeem non-existent coupon `INVALID_CODE`

**Request**:
```json
{
  "coupon_code": "INVALID_CODE",
  "google_user_id": "user_test_123",
  "google_email": "test@example.com"
}
```

**Expected Response**:
```json
{
  "code": "not-found",
  "message": "Invalid coupon code"
}
```

---

### Test Case 5: Expired Coupon

**Scenario**: User tries to redeem coupon after Jan 11, 2027

**Request**:
```json
{
  "coupon_code": "INFINITY_DAD",
  "google_user_id": "user_test_123",
  "google_email": "test@example.com"
}
```

**Expected Response** (on/after 2027-01-12):
```json
{
  "code": "failed-precondition",
  "message": "Coupon has expired"
}
```

---

### Test Case 6: Missing Required Fields

**Scenario**: Request missing `google_email`

**Request**:
```json
{
  "coupon_code": "INFINITY_DAD",
  "google_user_id": "user_test_123"
}
```

**Expected Response**:
```json
{
  "code": "invalid-argument",
  "message": "Missing required fields: coupon_code, google_user_id, google_email"
}
```

---

## 🧬 Manual Testing via Firebase Console

### Option 1: Using Cloud Functions UI

1. **Open Firebase Console**: https://console.firebase.google.com/project/galvanic-pulsar-482815-h0
2. **Navigate**: Cloud Functions → verifyCoupon
3. **Click "Testing" tab**
4. **Input JSON**:
   ```json
   {
     "coupon_code": "INFINITY_DAD",
     "google_user_id": "test_user_001",
     "google_email": "test@example.com"
   }
   ```
5. **Click "Call Function"**
6. **Verify Response**: Should return success with session

### Option 2: Using cURL

```powershell
$token = "YOUR_AUTH_TOKEN_HERE"
$url = "https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/verifyCoupon"

$body = @{
  coupon_code = "INFINITY_DAD"
  google_user_id = "test_user_001"
  google_email = "test@example.com"
} | ConvertTo-Json

Invoke-WebRequest -Uri $url `
  -Method POST `
  -Headers @{"Content-Type" = "application/json"; "Authorization" = "Bearer $token"} `
  -Body $body
```

### Option 3: Using Firebase Client SDK

```javascript
// From frontend application
import { getFunctions, httpsCallable } from "firebase/functions";

const functions = getFunctions();
const verifyCoupon = httpsCallable(functions, 'verifyCoupon');

try {
  const result = await verifyCoupon({
    coupon_code: 'INFINITY_DAD',
    google_user_id: 'user_dad_123',
    google_email: 'dad@example.com'
  });
  console.log('Coupon verified:', result.data);
} catch (error) {
  console.error('Coupon verification failed:', error);
}
```

---

## 📊 Verification Checklist

### Pre-Deployment

- [ ] `frontend/functions/src/verifyCoupon.ts` has 8 new coupons
- [ ] All coupons expire on "2027-01-11"
- [ ] All coupons have `max_uses: 1`
- [ ] All coupons have all 5 features
- [ ] Email binding logic is added (lines 165-177)
- [ ] Email binding creation is in batch (lines 240-250)
- [ ] TypeScript compiles without errors
- [ ] No console errors in Firebase Function logs

### Deployment

- [ ] `firebase deploy --only functions:verifyCoupon` completes successfully
- [ ] No errors in Cloud Function deployment logs
- [ ] Function URL is accessible and returns 200 OK
- [ ] Firebase Console shows verifyCoupon as deployed

### Post-Deployment Testing

- [ ] **Test 1**: First user redemption creates email binding ✅
- [ ] **Test 2**: Same user re-verification returns existing session ✅
- [ ] **Test 3**: Different user is rejected with permission-denied ✅
- [ ] **Test 4**: Invalid coupon code returns not-found ✅
- [ ] **Test 5**: Missing fields returns invalid-argument ✅

### Firestore Data Validation

- [ ] `coupon_usage/{COUPON_CODE}` documents exist
- [ ] `coupon_usage` shows correct `total_uses` (should be 0 or 1)
- [ ] `coupon_email_bindings/{COUPON_CODE}` created for used coupons
- [ ] `coupon_email_bindings` has correct `bound_email`
- [ ] `user_coupons/{USER_ID}_{COUPON_CODE}` created for redemptions
- [ ] `user_sessions/{USER_ID}` has all 5 features granted
- [ ] `user_profiles/{USER_ID}` has correct coupon metadata

### Error Handling

- [ ] Email binding check prevents different emails ✅
- [ ] Usage limit enforced (max 1 user per coupon) ✅
- [ ] Expiry dates checked correctly ✅
- [ ] Atomic batch prevents partial updates ✅

---

## 🔄 Rollback Plan

If issues occur, rollback to previous version:

```powershell
# Revert to backup
git checkout HEAD -- frontend/functions/src/verifyCoupon.ts

# Redeploy
firebase deploy --only functions:verifyCoupon --project=galvanic-pulsar-482815-h0
```

**Rollback Triggers**:
- ❌ Email binding logic prevents legitimate users from accessing
- ❌ Firestore batch operations fail silently
- ❌ Function timeout on batch writes
- ❌ Unexpected errors in logs

---

## 📝 Code Changes Summary

### Modified Function: `verifyCoupon.ts`

**Lines Changed**:
- **Lines 27-127**: Updated VALID_COUPONS configuration
  - Removed: INFINITY1718, INFINITY0506, INFINITYRAJ, TESTCOUPON
  - Added: INFINITY_DAD, INFINITY_MOM, INFINITY_RAJ, INFINITY_SAI, INFINITY_PRIYA, INFINITY_RAGHU, INFINITY_KAVI, INFINITY_HARSHA
  - Changed all expiry to "2027-01-11"
  - Changed all max_uses to 1
  - All features now unified (5 features each)

- **Lines 165-177**: Added email binding verification
  - Query coupon_email_bindings collection
  - Check if bound email matches current email
  - Reject with permission-denied if mismatch

- **Lines 240-250**: Added email binding creation
  - Create coupon_email_bindings document on first use
  - Store coupon_code, bound_email, bound_user_id, bound_at
  - Only create if not already bound

**Total Changes**:
- ~100 lines modified/added
- ~50 lines removed (old coupons)
- 0 lines removing critical logic
- All changes backward compatible with existing collections

---

## 📞 Support

### Issue: Email binding prevents legitimate users

**Solution**: Check `coupon_email_bindings` Firestore collection
```powershell
firebase firestore:delete coupon_email_bindings/{COUPON_CODE} --project=galvanic-pulsar-482815-h0
```

### Issue: Function timeout

**Solution**: Check Cloud Function logs
```powershell
firebase functions:log --only verifyCoupon --project=galvanic-pulsar-482815-h0
```

### Issue: Partial Firestore writes

**Solution**: Batch operations ensure atomicity. If issues occur:
1. Check logs for batch commit errors
2. Manually clean up orphaned documents
3. Redeploy function

---

## 🎯 Success Criteria

✅ **Deployment Successful When**:
1. All 8 new coupons are in `VALID_COUPONS`
2. Email binding logic is active
3. First redemption creates binding
4. Different emails are rejected
5. Same email is allowed to re-verify
6. All 5 features granted for each coupon
7. Expiry is 2027-01-11 for all coupons
8. Firestore shows correct documents

✅ **System Ready For Production When**:
1. All test cases pass
2. No errors in Cloud Function logs
3. Email binding enforced correctly
4. Firestore data matches expectations
5. Frontend integration verified
6. Documentation updated

---

**Status**: ✅ Ready for Deployment
**Timeline**: 15-30 minutes (deploy + test)
**Risk Level**: Low (backward compatible, no breaking changes)

