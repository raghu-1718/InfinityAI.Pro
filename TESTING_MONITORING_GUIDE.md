# Live Testing & Monitoring Guide

**Date**: January 11, 2026
**Project**: InfinityAI.Pro - Coupon System
**Status**: Deployed & Ready for Testing

---

## 🧪 Manual Testing Instructions

### Option 1: Using Firebase Console UI

**Steps**:
1. Go to: https://console.firebase.google.com/project/galvanic-pulsar-482815-h0
2. Click "Cloud Functions" in left menu
3. Find and click "verifyCoupon" function
4. Click the "Testing" tab
5. Input your request JSON (see below)
6. Click "Call Function"
7. View response and check Firestore

**Request JSON Template**:
```json
{
  "coupon_code": "INFINITY_DAD",
  "google_user_id": "test_user_dad_123",
  "google_email": "dad@example.com"
}
```

**Expected Response**:
```json
{
  "success": true,
  "session_id": "session_test_user_dad_123_1736600000000",
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

---

### Option 2: Using PowerShell & cURL

**Get Authentication Token**:
```powershell
# Login to Firebase
firebase login

# Get ID token (requires authenticated user)
gcloud auth application-default print-access-token
```

**Make Request**:
```powershell
$url = "https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/verifyCoupon"
$token = "YOUR_ACCESS_TOKEN_HERE"

$body = @{
  coupon_code = "INFINITY_DAD"
  google_user_id = "test_user_dad_123"
  google_email = "dad@example.com"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri $url `
  -Method POST `
  -Headers @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $token"
  } `
  -Body $body

$response.Content | ConvertFrom-Json | Format-List
```

---

### Option 3: Using JavaScript/Frontend Code

```javascript
import { getFunctions, httpsCallable } from "firebase/functions";
import { initializeApp } from "firebase/app";

// Initialize Firebase (use your config)
const app = initializeApp(firebaseConfig);
const functions = getFunctions(app, "us-central1");

// Call Cloud Function
const verifyCoupon = httpsCallable(functions, "verifyCoupon");

async function testCoupon() {
  try {
    const result = await verifyCoupon({
      coupon_code: "INFINITY_DAD",
      google_user_id: "test_user_dad_123",
      google_email: "dad@example.com"
    });

    console.log("✅ Coupon verified:", result.data);
    // Response:
    // {
    //   success: true,
    //   session_id: "session_...",
    //   features: [...],
    //   expires_at: "2026-04-11T..."
    // }
  } catch (error) {
    console.error("❌ Error:", error.message);
    // Error response:
    // {
    //   code: "permission-denied",
    //   message: "This coupon is already bound to..."
    // }
  }
}

testCoupon();
```

---

## 📊 Firestore Verification Steps

### 1. Check Coupon Usage Counter

**What to Look For**: `coupon_usage` collection

**Command**:
```powershell
firebase firestore:get coupon_usage --project=galvanic-pulsar-482815-h0
```

**Expected Output** (after first redemption):
```json
{
  "INFINITY_DAD": {
    "total_uses": 1,
    "last_used_by": "dad@example.com",
    "last_used_at": "2026-01-11T16:12:40Z"
  }
}
```

---

### 2. Check Email Bindings (NEW COLLECTION)

**What to Look For**: `coupon_email_bindings` collection

**Command**:
```powershell
firebase firestore:get coupon_email_bindings --project=galvanic-pulsar-482815-h0
```

**Expected Output** (after first redemption):
```json
{
  "INFINITY_DAD": {
    "coupon_code": "INFINITY_DAD",
    "bound_email": "dad@example.com",
    "bound_user_id": "test_user_dad_123",
    "bound_at": "2026-01-11T16:12:40Z"
  }
}
```

---

### 3. Check User Session

**What to Look For**: `user_sessions` collection

**Command**:
```powershell
firebase firestore:get user_sessions/test_user_dad_123 --project=galvanic-pulsar-482815-h0
```

**Expected Output**:
```json
{
  "session_id": "session_test_user_dad_123_1736600000000",
  "features": [
    "live_trading",
    "portfolio_analysis",
    "ai_signals",
    "vertex_ai",
    "engine_c_access"
  ],
  "created_at": "2026-01-11T16:12:40Z",
  "expires_at": "2026-04-11T16:12:40Z",
  "coupon_code": "INFINITY_DAD"
}
```

---

### 4. Check User Profile

**What to Look For**: `user_profiles` collection

**Command**:
```powershell
firebase firestore:get user_profiles/test_user_dad_123 --project=galvanic-pulsar-482815-h0
```

**Expected Output**:
```json
{
  "google_user_id": "test_user_dad_123",
  "email": "dad@example.com",
  "features": [
    "live_trading",
    "portfolio_analysis",
    "ai_signals",
    "vertex_ai",
    "engine_c_access"
  ],
  "coupon_code": "INFINITY_DAD",
  "coupon_redeemed_at": "2026-01-11T16:12:40Z",
  "coupon_expires_at": "2026-04-11T16:12:40Z",
  "last_login": "2026-01-11T16:12:40Z"
}
```

---

### 5. Check User Coupon Record

**What to Look For**: `user_coupons` collection

**Command**:
```powershell
firebase firestore:get user_coupons/test_user_dad_123_INFINITY_DAD --project=galvanic-pulsar-482815-h0
```

**Expected Output**:
```json
{
  "user_id": "test_user_dad_123",
  "coupon_code": "INFINITY_DAD",
  "email": "dad@example.com",
  "redeemed_at": "2026-01-11T16:12:40Z"
}
```

---

## 🔍 Monitoring Cloud Function Logs

### Check Recent Logs

```powershell
firebase functions:log --project=galvanic-pulsar-482815-h0
```

### Look for:
- ✅ **SUCCESS**: "Coupon verified successfully"
- ⚠️ **INFO**: "Email binding created for [email]"
- ❌ **ERROR**: Only if there's a problem (should be minimal)

### Log Entry Examples

**Successful Redemption**:
```
2026-01-11 16:12:40 verifyCoupon
Request: {coupon_code: "INFINITY_DAD", google_email: "dad@example.com"}
Response: {success: true, session_id: "session_...", features: [...]}
Duration: 234ms
```

**Email Binding Rejection**:
```
2026-01-11 16:12:45 verifyCoupon
Request: {coupon_code: "INFINITY_DAD", google_email: "mom@example.com"}
Error: permission-denied - "This coupon is already bound to dad@example.com"
Duration: 45ms
```

---

## 🎯 Test Scenarios

### Scenario 1: First Time User (Happy Path)

**Steps**:
1. User authenticates as `dad@example.com` (new user)
2. User enters coupon: `INFINITY_DAD`
3. Function processes and creates binding
4. User gets full access ✅

**Success Indicators**:
- Response: success = true
- Firestore: coupon_email_bindings created
- Firestore: user_sessions created with features
- Duration: <500ms

---

### Scenario 2: Same User Re-verification

**Steps**:
1. Same user (`dad@example.com`) enters `INFINITY_DAD` again
2. Function finds existing binding & session
3. Returns existing session without new writes

**Success Indicators**:
- Response: success = true
- Response: same session_id
- Firestore: No new documents created
- Duration: <200ms (faster, no batch write)

---

### Scenario 3: Different User Blocked

**Steps**:
1. Different user (`mom@example.com`) enters `INFINITY_DAD`
2. Function checks email binding
3. Binding exists for `dad@example.com`
4. Request rejected ❌

**Success Indicators**:
- Response: code = "permission-denied"
- Response: message includes "already bound to dad@example.com"
- Firestore: No changes
- Duration: <100ms (fast rejection)

---

### Scenario 4: Invalid Coupon Code

**Steps**:
1. User enters: `INVALID_CODE`
2. Function checks VALID_COUPONS
3. Code not found
4. Request rejected ❌

**Success Indicators**:
- Response: code = "not-found"
- Response: message = "Invalid coupon code"
- Duration: <50ms (instant rejection)

---

## 📈 Performance Metrics

### Expected Response Times

| Scenario | Duration | Status |
| :--- | :--- | :--- |
| First redemption (new binding) | 200-500ms | ✅ NORMAL |
| Re-verification (same user) | 100-200ms | ✅ FAST |
| Rejection (different email) | 50-150ms | ✅ FAST |
| Invalid code rejection | <50ms | ✅ INSTANT |
| Usage limit reached | <100ms | ✅ INSTANT |

### Resource Usage

| Metric | Expected | Target |
| :--- | :--- | :--- |
| Memory Usage | <50MB | <256MB |
| CPU Usage | Low | <25% |
| Firestore Reads | 2 per request | <5 |
| Firestore Writes | 1 batch (5 docs) | ✅ |
| Network Latency | 50-200ms | <500ms |

---

## ✅ Verification Checklist

After first test redemption, verify:

- [ ] Function returned success: true
- [ ] Session ID generated (not empty)
- [ ] Features array has all 5 features
- [ ] expires_at is ~90 days from now
- [ ] coupon_usage document created with total_uses = 1
- [ ] coupon_email_bindings created with correct email
- [ ] user_sessions document updated with features
- [ ] user_profiles document updated
- [ ] user_coupons redemption record created
- [ ] No errors in Cloud Function logs
- [ ] Second request by same email returns existing session
- [ ] Third request by different email returns permission-denied

---

## 🚨 Troubleshooting

### Problem: Function returns "not-found"

**Cause**: Coupon code not in VALID_COUPONS
**Solution**: Use one of these codes:
- INFINITY_DAD
- INFINITY_MOM
- INFINITY_RAJ
- INFINITY_SAI
- INFINITY_PRIYA
- INFINITY_RAGHU
- INFINITY_KAVI
- INFINITY_HARSHA

---

### Problem: Email binding prevents second user

**Cause**: First user already claimed coupon
**Behavior**: This is CORRECT (by design)
**Solution**: Use a different coupon code

---

### Problem: Function times out

**Cause**: Firestore slow or network issue
**Solution**:
1. Check Firestore dashboard for issues
2. Verify network connection
3. Try again (may be temporary)
4. Check Cloud Function logs

---

### Problem: Firestore documents not created

**Cause**: Batch commit failed silently
**Solution**:
1. Check Cloud Function logs for errors
2. Verify Firestore collections exist
3. Check IAM permissions
4. Try manual document creation

---

## 📞 Support Commands

```powershell
# View all functions
firebase functions:list --project=galvanic-pulsar-482815-h0

# Check function status
gcloud functions list --project=galvanic-pulsar-482815-h0

# Delete and re-deploy if needed
firebase deploy --only functions:verifyCoupon --project=galvanic-pulsar-482815-h0

# View Firestore database
firebase firestore:get --project=galvanic-pulsar-482815-h0

# Export data for backup
firebase firestore:export backup --project=galvanic-pulsar-482815-h0
```

---

## 🎯 Success Criteria

The deployment is **SUCCESSFUL** when:

✅ All 8 coupons respond correctly
✅ First redemption creates email binding
✅ Same email re-verification works
✅ Different email is rejected
✅ Firestore documents match expected schema
✅ No errors in logs
✅ Response times < 500ms
✅ All test scenarios pass

---

**Ready to Test**: ✅ YES
**Function Status**: 🟢 ACTIVE
**Date**: January 11, 2026

