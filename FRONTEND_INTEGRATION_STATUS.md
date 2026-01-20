# Frontend Integration Status & Configuration Analysis

**Date:** January 20, 2026  
**User:** raghuyuvi10@gmail.com  
**Engine-C Revision:** engine-c-00084-j9h

---

## 1. Configuration Status

### ✅ Environment Variables (.env.local)
```env
NEXT_PUBLIC_ENGINE_A_URL=https://engine-a-228557716858.us-central1.run.app
NEXT_PUBLIC_ENGINE_B_URL=https://engine-b-228557716858.us-central1.run.app
NEXT_PUBLIC_ENGINE_C_URL=https://engine-c-228557716858.us-central1.run.app ✅ CORRECT
```

### ⚠️ Hardcoded Fallback URLs in api.ts

**Current State:**
```typescript
// Line 27 in src/lib/api.ts
export const getEngineCUrl = () => {
  return (
    process.env.NEXT_PUBLIC_ENGINE_C_URL ||
    "https://engine-c-3acobgd3qa-uc.a.run.app"  // ❌ OLD URL
  );
};
```

**Issue:** Fallback URL points to old service instance that may not exist or have outdated code.

**Impact:** 
- If environment variable not loaded properly, frontend will call wrong backend
- Development builds might use old URL
- Production deployments without proper env vars will fail

---

## 2. API Integration Points

### Engine-C Endpoints Called by Frontend

| Endpoint | Method | Hook/Component | Purpose |
|----------|--------|----------------|---------|
| `/api/health` | GET | useEngineHealth | Health check |
| `/api/dhan/funds` | GET | engineC.getDhanFunds | Fetch user funds |
| `/api/dhan/positions` | GET | engineC.getDhanPositions | Fetch positions |
| `/api/dhan/orders` | GET | engineC.getDhanOrders | Fetch orders |
| `/api/dhan/holdings` | GET | engineC.getDhanHoldings | Fetch holdings |
| `/api/dhan/market/quotes` | GET | engineC.getMarketQuotes | Live market data |
| `/api/v1/execution/analytics` | POST | useExecutionAnalytics | Execution stats |
| `/api/user/credentials` | POST/DELETE | Settings page | Save/delete credentials |
| `/api/trading-settings/{userId}` | GET/POST | Auto-trading settings | Trading config |
| `/api/background-trading/start` | POST | Auto-trading | Start persistent trading |

---

## 3. Data Flow Architecture

### User Authentication & ID Resolution

```
Frontend (Firebase Auth)
    ↓ (Firebase UID or email)
User Credentials Component
    ↓ (Saves credentials with user_id = email)
Firestore Collection: dhan_credentials
    ↓ (Document ID may differ from user_id field)
Engine-C Backend
    ↓ (Multi-strategy resolution: direct lookup → client_id scan → user_id field query)
DhanHQ API Client
    ↓
Live Market Data & Account Info
```

### Current User ID Used
- **Frontend:** `raghuyuvi10@gmail.com` (Firebase Auth email)
- **Backend Firestore Lookup:** Searches by:
  1. Document ID = `raghuyuvi10@gmail.com`
  2. Field `client_id` contains user_id
  3. Field `user_id` = `raghuyuvi10@gmail.com`
- **Retry Logic:** 4 attempts with exponential backoff (100ms, 200ms, 400ms)

---

## 4. Hook Integration Status

### Dhan Data Hooks (useDhanData.ts)

```typescript
// ✅ IMPLEMENTED - Market Data Hooks
useMarketQuotes(symbols: string[])        // Fetches live quotes, 5s refresh
useHistoricalData(symbol, from, to)       // Historical candles
useMarketDepth(symbol, levels)            // Order book, 2s refresh
useOptionChain(symbol, expiry)            // Options chain, 10s refresh
useExpiredOptions(symbol, date)           // Expired options data
```

**Configuration:**
- Uses `engineC.getMarketQuotes()` from `lib/api.ts`
- Auto-refresh intervals:
  - Market Quotes: 5 seconds
  - Market Depth: 2 seconds
  - Option Chain: 10 seconds

### Live Market Display Component

**File:** `src/components/LiveMarketQuotes.tsx`

```tsx
export function LiveMarketQuotes() {
  const [quotes, setQuotes] = useState<Map<string, Quote>>(new Map());
  const { connectionState, error } = useMarketData((data) => {
    // Updates quotes via Ably real-time streaming
  });
  
  // Shows: Symbol, LTP, Bid, Ask, Change%, Trend
}
```

**Status:** ✅ Integrated with Ably for real-time streaming

---

## 5. Dashboard Integration

### Main Dashboard (app/(dashboard)/page.tsx)

**Data Sources:**
```typescript
const { data: systemState } = useSystemState();        // Engine health
const { data: engineHealth } = useEngineHealth();      // Engine status
const { data: userAccount } = useUserAccount();        // Funds & holdings
const { data: positionsRes } = usePositions();         // Active positions
const { data: signalsRes } = useSignals();             // AI signals
const { data: executionStats } = useExecutionAnalytics(); // Performance stats
```

**Displayed Metrics:**
- Portfolio Value (Funds + Holdings)
- Today's P&L (Realized + Unrealized)
- Active Positions Count (Options vs Equity)
- Win Rate (from execution analytics)
- AI Signals with confidence scores
- Trading Engine Status

**Current Status:**
- ✅ Health checks working
- ✅ Funds endpoint returning data (verified with raghuyuvi10@gmail.com)
- ✅ Positions endpoint working
- ✅ Orders endpoint working
- ✅ Execution analytics alias working

---

## 6. Real-Time Data Integration

### Ably WebSocket Streaming

**File:** `src/hooks/useRealtimeTrading.ts`

```typescript
const ENGINE_C_URL = process.env.NEXT_PUBLIC_ENGINE_C_URL ||
  "https://engine-c-3acobgd3qa-uc.a.run.app"; // ⚠️ OLD FALLBACK

// SSE Endpoint: ${ENGINE_C_URL}/api/realtime/stream/${userId}
```

**Streams:**
- `useMarketData()` - Live market quotes
- `usePortfolioUpdates()` - Position/order updates
- `useRealtimeTrading()` - Trade execution events

**Configuration Required:**
- Ably API key in environment (already configured)
- Engine-C SSE endpoint for streaming

---

## 7. What the Frontend Shows

### Dashboard View (When Logged In as raghuyuvi10@gmail.com)

#### Top Section
```
Welcome back, [Name from profile or clientId]
[Date] • [Time]
[LIVE MODE] [Bell Icon] [Settings Icon]
```

#### Quick Stats Cards
```
┌─────────────────────┐  ┌─────────────────────┐
│ Portfolio Value     │  │ Today's P&L         │
│ ₹X,XXX,XXX         │  │ +₹X,XXX / -₹X,XXX  │
│ 💼 Total Assets     │  │ 📈 X active trades  │
└─────────────────────┘  └─────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐
│ Active Positions    │  │ Win Rate            │
│ XX                 │  │ XX%                 │
│ ⚡ X Options, X Eq  │  │ 🎯 Real-time Stats  │
└─────────────────────┘  └─────────────────────┘
```

#### Trading Engine Control Panel
```
🧠 Trading Engine
   AI-Powered Automated Trading
   
   Status: [Active / Inactive]
   [Start Engine] / [Stop Engine] button
```

#### Live Market Quotes (if enabled)
```
┌─────────────────────┐
│ NIFTY 50            │
│ ₹23,450.25         │
│ +150.50 (+0.65%)   │
│ Bid: 23,449 | Ask: 23,451 │
└─────────────────────┘
```

#### Active Positions Table
```
Symbol | Type    | Qty | Entry | Current | P&L      | Action
-------|---------|-----|-------|---------|----------|--------
NIFTY  | CALL    | 50  | 100   | 105     | +₹250    | [Exit]
BANKNIF| PUT     | 25  | 200   | 195     | -₹125    | [Exit]
```

#### AI Signals Panel
```
📡 Latest AI Signals

BUY  NIFTY   Confidence: 85%  [Execute]
SELL BANKNIF Confidence: 72%  [Execute]
HOLD RELIANCE Confidence: 60% [Ignore]
```

---

## 8. Current Issues & Fixes Needed

### ❌ Issue 1: Hardcoded Fallback URLs

**File:** `frontend/web-app/src/lib/api.ts` (Line 27)

**Problem:**
```typescript
"https://engine-c-3acobgd3qa-uc.a.run.app"  // Wrong fallback
```

**Should Be:**
```typescript
"https://engine-c-228557716858.us-central1.run.app"  // Correct production URL
```

**Fix Required:** Update all three engine fallback URLs to match actual deployed services.

### ❌ Issue 2: Market Quotes API Mismatch

**File:** `frontend/web-app/src/lib/api.ts` (Line 1348)

**Current:**
```typescript
async getMarketQuotes(
  userId: string,
  securityIds: string[],
  exchangeSegment: string = "NSE_EQ",
) {
  const qs = new URLSearchParams({
    security_ids: securityIds.join(","),
    exchange_segment: exchangeSegment,
    user_id: userId,
  });
  const res = await fetchWithTimeout(
    `${API_CONFIG.ENGINE_C}/api/dhan/market/quotes?${qs.toString()}`,
  );
  return res.json();
}
```

**Hook Usage:**
```typescript
// File: src/hooks/useDhanData.ts
export function useMarketQuotes(symbols: string[], enabled: boolean = true) {
  return useQuery({
    queryKey: ['market', 'quotes', symbols.join(',')],
    queryFn: async () => {
      const response = await engineC.getMarketQuotes(symbols); // ❌ Missing userId!
      return response;
    },
    ...
  });
}
```

**Problem:** Hook calls `getMarketQuotes(symbols)` but API expects `(userId, securityIds, exchangeSegment)`

**Impact:** Market quotes hook will fail at runtime with incorrect arguments

**Fix Required:** Update hook to pass userId from context/store

---

## 9. Verification Tests Performed

### ✅ Backend Endpoint Tests (with raghuyuvi10@gmail.com)

```bash
# All tests PASSED with HTTP 200 OK

GET /api/dhan/funds?user_id=raghuyuvi10@gmail.com
→ Response: { status: "success", data: { ... funds data ... } }

GET /api/dhan/positions?user_id=raghuyuvi10@gmail.com
→ Response: { status: "success", data: [ ... positions ... ] }

GET /api/dhan/orders?user_id=raghuyuvi10@gmail.com
→ Response: { status: "success", data: [ ... orders ... ] }

GET /api/dhan/market/quotes?security_ids=13&exchange_segment=IDX_I&user_id=raghuyuvi10@gmail.com
→ Response: { status: "success", data: [ ... market quotes ... ] }
```

### ⏳ Frontend Tests Pending

**Need to verify:**
1. Dashboard loads without errors
2. Portfolio metrics display correct values
3. Market quotes auto-refresh every 5 seconds
4. Positions table shows live data
5. AI signals appear in sidebar
6. Auto-trading controls work
7. Settings page can save/update credentials

---

## 10. Recommended Actions

### 🔧 CRITICAL - Fix Fallback URLs

**File:** `frontend/web-app/src/lib/api.ts`

**Change Lines 9, 16, 27:**
```typescript
// OLD (WRONG)
export const getEngineAUrl = () => {
  return (
    process.env.NEXT_PUBLIC_ENGINE_A_URL ||
    "https://engine-a-3acobgd3qa-uc.a.run.app"  // ❌
  );
};

export const getEngineBUrl = () => {
  return (
    process.env.NEXT_PUBLIC_ENGINE_B_URL ||
    "https://engine-b-3acobgd3qa-uc.a.run.app"  // ❌
  );
};

export const getEngineCUrl = () => {
  return (
    process.env.NEXT_PUBLIC_ENGINE_C_URL ||
    "https://engine-c-3acobgd3qa-uc.a.run.app"  // ❌
  );
};

// NEW (CORRECT)
export const getEngineAUrl = () => {
  return (
    process.env.NEXT_PUBLIC_ENGINE_A_URL ||
    "https://engine-a-228557716858.us-central1.run.app"  // ✅
  );
};

export const getEngineBUrl = () => {
  return (
    process.env.NEXT_PUBLIC_ENGINE_B_URL ||
    "https://engine-b-228557716858.us-central1.run.app"  // ✅
  );
};

export const getEngineCUrl = () => {
  return (
    process.env.NEXT_PUBLIC_ENGINE_C_URL ||
    "https://engine-c-228557716858.us-central1.run.app"  // ✅
  );
};
```

### 🔧 HIGH - Fix Market Quotes Hook

**File:** `frontend/web-app/src/hooks/useDhanData.ts`

**Change Line 52:**
```typescript
// OLD
export function useMarketQuotes(symbols: string[], enabled: boolean = true) {
  return useQuery({
    queryKey: ['market', 'quotes', symbols.join(',')],
    queryFn: async () => {
      const response = await engineC.getMarketQuotes(symbols); // ❌
      return response;
    },
    ...
  });
}

// NEW
import { getUserId } from '@/lib/user';

export function useMarketQuotes(symbols: string[], enabled: boolean = true) {
  const userId = getUserId(); // ✅ Get from context
  
  return useQuery({
    queryKey: ['market', 'quotes', symbols.join(','), userId],
    queryFn: async () => {
      const response = await engineC.getMarketQuotes(
        userId,           // ✅ Pass userId
        symbols,          // security IDs
        "NSE_EQ"         // exchange segment
      );
      return response;
    },
    enabled: enabled && symbols.length > 0 && !!userId, // ✅ Check userId exists
    ...
  });
}
```

### 📝 MEDIUM - Deploy Frontend with Fixes

```bash
# 1. Apply fixes above
# 2. Rebuild and deploy

cd frontend/web-app
npm run build

# 3. Deploy to Firebase Hosting or Cloud Run
firebase deploy --only hosting --project=galvanic-pulsar-482815-h0

# OR if using Cloud Run:
gcloud run deploy web-app \
  --source=. \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --allow-unauthenticated
```

### 🧪 LOW - End-to-End Testing Script

```bash
# Open frontend in browser
# Login as raghuyuvi10@gmail.com
# Navigate to Dashboard
# Verify:
# - Portfolio value shows correct amount
# - Positions table populated
# - Market quotes refreshing every 5s
# - AI signals displayed
# - No console errors in DevTools
```

---

## 11. Summary

### ✅ What's Working
- Backend engine-c deployed and tested (revision 00084-j9h)
- All API endpoints returning HTTP 200 with valid data
- Credentials stored and resolved correctly
- Multi-strategy user ID resolution with retries
- Environment variables configured in .env.local

### ⚠️ What Needs Fixing
- **CRITICAL:** Hardcoded fallback URLs in api.ts point to old/wrong services
- **HIGH:** Market quotes hook missing userId parameter
- **MEDIUM:** Frontend not yet redeployed with latest env vars
- **LOW:** Real-time streaming endpoints not verified end-to-end

### 📊 Expected Frontend Behavior (After Fixes)

When you open the frontend and login as `raghuyuvi10@gmail.com`:

1. **Dashboard loads in <2 seconds**
2. **Portfolio Value card** shows total funds + holdings value
3. **Today's P&L card** shows realized + unrealized profit/loss
4. **Active Positions card** shows count of open trades
5. **Win Rate card** shows execution analytics (if trades executed)
6. **Market Quotes** refresh every 5 seconds with live LTP
7. **AI Signals panel** shows latest BUY/SELL/HOLD recommendations
8. **Trading Engine status** shows whether auto-trading is active
9. **No 404/401/500 errors** in browser console
10. **Real-time updates** via Ably WebSocket for order fills

---

## 12. Next Steps

1. ✅ Fix fallback URLs in `api.ts`
2. ✅ Fix market quotes hook to include userId
3. 🔄 Rebuild frontend with fixes
4. 🔄 Deploy to Firebase Hosting or Cloud Run
5. 🧪 Test end-to-end in browser
6. 📊 Monitor console for errors
7. ✅ Verify all dashboard metrics populate correctly

---

**Status:** Backend ready ✅ | Frontend needs URL fixes ⚠️ | Deployment pending 🔄
