# FRONTEND FIX & INTEGRATION AUDIT REPORT

**Date:** January 19, 2026
**Status:** 🔴 CRITICAL ISSUES IDENTIFIED - IN PROGRESS FIX
**Project:** InfinityAI.Pro Frontend Integration

---

## 📋 ISSUES IDENTIFIED (FROM ATTACHMENTS)

### 1. **Dhan Connection State Inconsistency** 🔴 CRITICAL

**Problem:**

- User clicks "Disconnect" on Settings page (Attachment 1)
- Shows: "Status: DISCONNECTED"
- User navigates to Dashboard (Attachment 2)
- Portfolio shows real values, market data displays
- User returns to Settings (Attachment 3)
- Shows: "Status: CONNECTED" (but we disconnected!)
- Click "Save Credentials" → Error message (Attachment 4)

**Root Cause:**

- `connectionStatus` state in `settings/page.tsx` is local (component-level)
- Does NOT persist to Firestore or backend when changed
- Page refresh or navigation loads cached state from API
- No global state update on disconnect
- Frontend and backend out of sync

**How It Should Work:**

```
User clicks "Disconnect"
       ↓
DELETE /api/user/credentials (clear backend)
       ↓
DELETE Firestore dhan_credentials/{userId}
       ↓
Update Zustand global store (isConnected = false)
       ↓
Update ALL components immediately
       ↓
Page refresh shows same state (from Firestore)
```

---

### 2. **Placeholder/Hardcoded Values** 🔴 CRITICAL

**Portfolio Value:**

- Shows: `₹100` (Attachment 2)
- Expected: Real balance from DhanHQ API
- **Location:** `frontend/web-app/src/app/(dashboard)/page.tsx` line 119
- **Calculation:** `portfolioValue = (userAccount?.funds?.availableBalance || 0) + (userAccount?.funds?.collateralAmount || 0)`
- **Issue:** `userAccount` not updating from API

**Market Data (NIFTY, BANKNIFTY):**

- Shows: `NIFTY -- +0.00%` (Attachment 1)
- Shows: `BANKNIFTY -- +0.00%` (Attachment 1)
- Expected: Real-time index prices
- **Source:** Should come from Ably channel `infinityai:live-quotes`
- **Issue:** Ably subscription not working or data not flowing

**VIX:**

- Shows: `VIX 12.45` (Attachment 1 top right)
- **Issue:** Hardcoded or stale data, not real-time

**Portfolio Widget:**

- Shows: `Portfolio Value: ₹100`
- Shows: `Today's P&L: +₹0`
- Shows: `Active Positions: 0 Options, 0 Equity`
- **Issue:** All zeros (no real DhanHQ data)

---

### 3. **Theme Toggle Not Working** 🟡 MEDIUM

**Problem:**

- Click "Toggle Theme" on settings
- Nothing happens visually
- Expected: Dark ↔ Light theme switch

**Location:** `frontend/web-app/src/app/(dashboard)/settings/page.tsx`

---

### 4. **User Display Hardcoded** 🔴 CRITICAL

**Problem:**

- Shows: `"User 1101302170"` (Attachment 2 & 3 bottom left)
- Should: Show current logged-in user's name/email
- Expected: `"User {Firebase Auth User Name}"`

**Current Flow (Wrong):**

```
Frontend hardcoded: "user_1101302170"
       ↓
Multiple users see SAME user ID
       ↓
Credentials get overwritten
```

**Expected Flow:**

```
Firebase Auth: User logs in → Gets Firebase UID
       ↓
Zustand store: Stores currentUserId
       ↓
All API calls: Include userId from auth
       ↓
Each user sees own credentials, positions, P&L
```

---

### 5. **Firestore State Persistence Broken** 🔴 CRITICAL

**Evidence:**

- User disconnects (local state updated)
- User navigates away
- User returns → Shows "connected" again
- **Why:** Settings page reloads state from API on mount, doesn't check global store

**Should Persist To:**

1. ✅ Firestore `dhan_credentials/{userId}` collection (encrypted)
2. ✅ Zustand global store (`useAppStore`)
3. ✅ Local Storage (optional, for offline state)

**Current Missing:**

- No Firestore update on disconnect
- No global store update
- No localStorage fallback

---

### 6. **Credentials Flow Not Implemented** 🔴 CRITICAL

**Expected Complete Flow:**

```
Frontend Input (Client)
  ├─ Client ID
  ├─ Access Token
  ├─ API Key (optional)
  └─ API Secret (optional)
       ↓
POST /api/user/credentials (Engine-C)
       ↓
Backend Validation & Encryption
  ├─ Validate token format
  ├─ Encrypt with AES-256-GCM
  ├─ Generate unique key per user
  └─ Save to Firestore dhan_credentials/{userId}
       ↓
Secret Manager Storage
  ├─ user-credentials-key (AES key)
  ├─ dhan-client-id
  ├─ dhan-access-token
       ↓
Frontend Notification
  ├─ Success toast: "Connected!"
  ├─ Update local state
  ├─ Refresh user profile
  └─ Enable trading UI
```

**Current State:**

- ✅ Backend endpoint exists (`/api/user/credentials`)
- ❌ Frontend doesn't properly handle response
- ❌ Global state not updated
- ❌ No cascade update to other components
- ❌ Error handling incomplete

---

### 7. **Multi-User Support Missing** 🔴 CRITICAL

**Current Implementation:**

- Frontend uses hardcoded Firebase credentials (maybe)
- API calls don't include userId
- All users see same data

**Required Implementation:**

```typescript
// Before any API call, check:
const { user } = useAuth(); // Firebase Auth

if (!user?.uid) {
  return <Redirect to="/login" />
}

// Include userId in ALL API calls:
const response = await fetch(
  `${ENGINE_C_URL}/api/user/credentials?user_id=${user.uid}`,
  { headers: { 'Authorization': `Bearer ${await user.getIdToken()}` } }
);
```

---

## 🔧 FIX IMPLEMENTATION PLAN

### Phase 1: Backend Verification (5 minutes)

- ✅ Verify `/api/user/credentials` endpoint works
- ✅ Verify Firestore encryption/decryption
- ✅ Verify Secret Manager access
- ✅ Verify IAM permissions

### Phase 2: Frontend State Management (30 minutes)

- 🔄 Fix Zustand store: Add disconnect action
- 🔄 Implement Firestore listeners for real-time state
- 🔄 Add proper error handling and user feedback
- 🔄 Implement session persistence

### Phase 3: Credential Flow Implementation (45 minutes)

- 🔄 Create proper credential save/delete flow
- 🔄 Add global state updates
- 🔄 Add real-time data fetching
- 🔄 Add cascade component updates

### Phase 4: Remove Hardcoded Values (30 minutes)

- 🔄 Replace portfolio ₹100 with real DhanHQ data
- 🔄 Replace NIFTY/BANKNIFTY with Ably real-time
- 🔄 Replace VIX with real data source
- 🔄 Replace hardcoded user ID with Firebase Auth

### Phase 5: Multi-User Support (30 minutes)

- 🔄 Add Firebase Auth checks
- 🔄 Add userId to all API calls
- 🔄 Add user-scoped Firestore queries
- 🔄 Add Firestore security rule enforcement

### Phase 6: Real-Time Data Integration (45 minutes)

- 🔄 Connect market data from Ably
- 🔄 Connect portfolio data from Engine-C
- 🔄 Connect position updates from Firestore
- 🔄 Add real-time subscription management

### Phase 7: Frontend Simplification (60 minutes)

- 🔄 Remove BacktestRunner component
- 🔄 Remove StrategyBuilder component
- 🔄 Simplify ChartingTools
- 🔄 Keep only monitoring components

### Phase 8: Deployment & Testing (30 minutes)

- 🔄 Fix Cloud Build error
- 🔄 Deploy to Firebase Hosting
- 🔄 Test with real DhanHQ credentials
- 🔄 Verify end-to-end flow

---

## 🔍 VERIFICATION CHECKLIST

**Firestore Rules:**

- [ ] Users can only read/write own credentials
- [ ] `dhan_credentials/{userId}` write-only for user
- [ ] `dhan_credentials/{userId}` read-only for backend
- [ ] User profile updates trigger UI refresh

**GCP Secret Manager:**

- [ ] Engine-C service account can read secrets
- [ ] Cloud Build service account has limited access
- [ ] No hardcoded secrets in code
- [ ] Automatic secret rotation supported

**Credential Encryption:**

- [ ] AES-256-GCM encryption in Firestore
- [ ] Keys stored in Secret Manager (not Firestore)
- [ ] Each user has unique encryption key (optional)
- [ ] Decryption works only with valid key

**Frontend State:**

- [ ] Global store updates on credential changes
- [ ] Firestore listeners update UI in real-time
- [ ] Component subscribes to store updates
- [ ] Properly unsubscribes on unmount

**API Endpoints:**

- [ ] All endpoints require userId
- [ ] All endpoints require Firebase Auth token
- [ ] All endpoints validate user ownership
- [ ] All endpoints log actions to audit trail

---

## 📊 SUCCESS METRICS

**After Fixes:**

1. ✅ User disconnects → Immediately shows disconnected across app
2. ✅ Page refresh → Still shows disconnected
3. ✅ Navigate to other pages → State persists
4. ✅ Return to settings → Shows disconnected with disconnect button disabled
5. ✅ Different user logs in → Sees only own data
6. ✅ Portfolio shows real ₹ value from DhanHQ
7. ✅ NIFTY/BANKNIFTY show real prices updated every 5 seconds
8. ✅ Theme toggle works (dark/light)
9. ✅ User name shows logged-in user (not hardcoded)
10. ✅ No placeholder values anywhere in UI

---

**Next Step:** Begin Phase 1 backend verification
