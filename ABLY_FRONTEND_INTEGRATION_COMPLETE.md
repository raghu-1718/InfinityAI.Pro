# Ably Real-Time Frontend Integration - Complete Guide

**Status:** ✅ Frontend Integration Complete
**Date:** 2026-01-19
**Platform:** InfinityAI.Pro (galvanic-pulsar-482815-h0)
**Target Services:** Web Dashboard, Real-Time Updates

---

## 📋 Executive Summary

Ably integration has been **completed** at the frontend level. The application now has full support for real-time bidirectional communication through:

1. ✅ **AblyProvider Context** - Global real-time connection management
2. ✅ **React Hooks** - Easy subscription patterns (`useMarketData`, `usePortfolioUpdates`, `useTradingSignals`, etc.)
3. ✅ **Real-Time Dashboard** - Live update components ready to receive Ably messages
4. ✅ **Type-Safe Channels** - Pre-configured channel names for market data, trading, and system status
5. ✅ **Error Handling** - Connection state monitoring and failure recovery

---

## 🏗️ What Was Implemented

### 1. Environment Configuration

**File:** [next.config.ts](frontend/web-app/next.config.ts)

Added Ably API key as a public environment variable:

```typescript
env: {
  // ... Firebase config ...
  NEXT_PUBLIC_ABLY_API_KEY: process.env.NEXT_PUBLIC_ABLY_API_KEY || "",
}
```

**Security Model:**

- In development: Use local `.env.local` file
- In production: Injected via Secret Manager at Cloud Build time
- Public key only (safe to expose in browser)

### 2. Ably Client Library

**File:** [src/lib/ably.ts](frontend/web-app/src/lib/ably.ts)

Provides low-level Ably operations:

```typescript
// Singleton client initialization
export function initializeAblyClient(): Ably.Realtime {}

// Channel subscription with message handling
export function subscribeToChannel(
  channelName: string,
  messageHandler: (message: Message) => void,
): () => void {}

// Publishing (for bi-directional communication)
export function publishToChannel(
  channelName: string,
  data: any,
): Promise<void> {}

// Pre-configured channel names
export const ABLY_CHANNELS = {
  LIVE_QUOTES: "infinityai:live-quotes",
  TRADING_SIGNALS: "infinityai:trading-signals",
  PORTFOLIO_UPDATE: "infinityai:portfolio-update",
  USER_NOTIFICATIONS: "infinityai:user-notifications",
  USER_PORTFOLIO: (userId) => `infinityai:portfolio:${userId}`,
  ENGINE_STATUS: (engineId) => `infinityai:engine:${engineId}`,
  // ... more channels
};
```

**Key Features:**

- Auto-reconnection with backoff strategy
- Client ID generation for session tracking
- Development-mode connection state logging

### 3. Ably Context Provider

**File:** [src/contexts/AblyContext.tsx](frontend/web-app/src/contexts/AblyContext.tsx)

Wraps the entire application with Ably connection state:

```typescript
export function AblyProvider({ children }) {
  // Monitors connection state and errors
  // Makes available via useAblyContext() hook
  // Auto-cleanup on unmount
}

export function useAblyContext() {
  return { connectionState, isConnected, error };
}
```

**Integration:** Already integrated into [src/components/providers.tsx](frontend/web-app/src/components/providers.tsx)

### 4. React Hooks for Real-Time Data

**File:** [src/hooks/useAbly.ts](frontend/web-app/src/hooks/useAbly.ts)

Pre-built hooks for common patterns:

#### Market Data

```typescript
const { connectionState, error } = useMarketData((data) => {
  console.log(`${data.symbol}: ₹${data.price}`);
  updateUI(data);
});
```

#### Trading Signals

```typescript
const {} = useTradingSignals(engineId, (signal) => {
  console.log(
    `Signal: ${signal.action} ${signal.symbol} (${signal.confidence}% confidence)`,
  );
});
```

#### Portfolio Updates

```typescript
const {} = usePortfolioUpdates(userId, (portfolio) => {
  updatePortfolioUI(portfolio);
});
```

#### Notifications

```typescript
const {} = useNotifications(userId, (notification) => {
  toast.show(notification.message);
});
```

#### Connection Monitoring

```typescript
const { connectionState, error, isConnected } = useAblyConnection();
// Use to show connection status badge
```

### 5. Real-Time Dashboard Component

**File:** [src/components/RealtimeDashboard.tsx](frontend/web-app/src/components/RealtimeDashboard.tsx)

Already implemented with:

- Live connection status indicator (Radio icon animated when connected)
- Real-time order/trade event feed
- Last heartbeat timestamp
- Error display with reconnect button
- Event history with timestamps and status badges

### 6. Live Market Quotes Component

**File:** [src/components/LiveMarketQuotes.tsx](frontend/web-app/src/components/LiveMarketQuotes.tsx)

Shows real-time market data with:

- Live price updates with trend indicators (🟢 up / 🔴 down)
- Bid/Ask spread display
- Change percentage calculation
- Connection status indicator

---

## 🚀 Deployment Setup

### For Local Development

1. **Get Ably API Key:**

   ```bash
   # Go to https://ably.com/dashboard → API Keys
   # Copy Root API Key
   ```

2. **Create `.env.local`:**

   ```bash
   cd frontend/web-app
   cat > .env.local << EOF
   NEXT_PUBLIC_ABLY_API_KEY=your-ably-api-key-here
   EOF
   ```

3. **Start development server:**

   ```bash
   npm run dev
   # Open http://localhost:3000
   ```

4. **Verify in browser:**
   - Check browser console for "Ably connected successfully"
   - RealtimeDashboard should show "Live" indicator

### For Production Deployment

#### Step 1: Store API Key in Secret Manager

```bash
# Create secret
echo "your-ably-api-key" | gcloud secrets create ably-api-key \
  --data-file=- \
  --project=galvanic-pulsar-482815-h0

# Grant Cloud Build access
gcloud secrets add-iam-policy-binding ably-api-key \
  --member=serviceAccount:228557716858@cloudbuild.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor \
  --project=galvanic-pulsar-482815-h0
```

#### Step 2: Update Cloud Build Configuration

In your `cloudbuild.yaml` (frontend build step):

```yaml
steps:
  - name: "gcr.io/cloud-builders/npm"
    args:
      - "install"
      - "--prefix=frontend/web-app"

  - name: "gcr.io/cloud-builders/npm"
    args:
      - "run"
      - "build"
      - "--prefix=frontend/web-app"
    env:
      - "NEXT_PUBLIC_ABLY_API_KEY=${ABLY_API_KEY}"
    secretEnv: ["ABLY_API_KEY"]

availableSecrets:
  secretManager:
    - versionName: projects/$PROJECT_ID/secrets/ably-api-key/versions/latest
      env: "ABLY_API_KEY"
```

#### Step 3: Deploy with Firebase Hosting

```bash
firebase deploy --only hosting:web-app \
  --project=galvanic-pulsar-482815-h0
```

---

## 📊 Channel Architecture

### Pre-Configured Channels

| Channel                         | Purpose                 | Publish From        | Subscribe From      |
| ------------------------------- | ----------------------- | ------------------- | ------------------- |
| `infinityai:live-quotes`        | Market price updates    | Market Data Service | Dashboard           |
| `infinityai:trading-signals`    | AI trading signals      | Engine C            | Strategy Analyzer   |
| `infinityai:portfolio-update`   | Portfolio changes       | Trade Execution     | Portfolio View      |
| `infinityai:user-notifications` | User alerts             | Backend Services    | Notification Center |
| `infinityai:portfolio:{userId}` | User-specific portfolio | Trade Execution     | User Dashboard      |
| `infinityai:trades:{userId}`    | User trade history      | Trade Execution     | Trade List          |
| `infinityai:signals:{userId}`   | User signal feed        | Engine C            | Signal Feed         |
| `infinityai:system-status`      | Platform health         | Monitoring          | Status Dashboard    |
| `infinityai:engine:{engineId}`  | Engine-specific status  | Engine C            | Engine Monitor      |

---

## 🔌 Backend Integration Checklist

To enable real-time updates from your backend:

### [ ] Market Data Service

- [ ] Subscribe to market data updates (WebSocket, polling, or API)
- [ ] Publish to Ably channel: `infinityai:live-quotes`
- [ ] Data format: `{ symbol, price, bid, ask, timestamp }`

### [ ] Engine C (Trading Signals)

- [ ] Publish signals to: `infinityai:trading-signals`
- [ ] Publish user signals to: `infinityai:signals:{userId}`
- [ ] Data format: `{ engineId, symbol, action, confidence, reason, timestamp }`

### [ ] Trade Execution Service

- [ ] Publish fills to: `infinityai:trade-execution`
- [ ] Publish portfolio updates to: `infinityai:portfolio-update` and `infinityai:portfolio:{userId}`
- [ ] Data format: `{ tradeId, symbol, quantity, price, type, status, timestamp }`

### [ ] Notification Service

- [ ] Publish to: `infinityai:user-notifications`
- [ ] Publish to: `infinityai:user-notifications` for broadcasts
- [ ] Data format: `{ id, type, title, message, timestamp }`

---

## 🔐 Security & Best Practices

### Frontend Side (Already Implemented)

✅ API key stored in environment variables (not in source code)
✅ Public key only (safe for browser)
✅ Client ID generation for session identification
✅ Connection state monitoring with error handling
✅ Automatic reconnection with backoff

### Backend Side (To Implement)

- [ ] Rate limit publishes to Ably channels
- [ ] Validate channel names and data formats
- [ ] Use Ably token authentication for user-specific channels
- [ ] Implement channel-level permissions via Ably rules
- [ ] Log all publishes to audit trail for compliance

### Ably Account Security

- [ ] Rotate API keys every 90 days
- [ ] Use separate keys for dev/staging/production
- [ ] Enable 2FA on Ably dashboard
- [ ] Monitor quota usage and set alerts

---

## ✅ Verification Checklist

### Local Development

- [ ] Frontend starts without Ably API key errors
- [ ] Browser console shows "Ably connected successfully"
- [ ] RealtimeDashboard displays "Live" indicator
- [ ] Open DevTools → Console, verify no errors
- [ ] Try manual publish: `publishToChannel('test', {msg: 'hello'})`

### Production Verification

```bash
# Check that API key is securely injected
gcloud secrets versions list ably-api-key --project=galvanic-pulsar-482815-h0

# Verify build includes Ably
firebase hosting:channel:deploy test \
  --project=galvanic-pulsar-482815-h0

# Open deployed URL and check browser console
# Should show connection state changes
```

---

## 🐛 Troubleshooting

### Connection Fails: "NEXT_PUBLIC_ABLY_API_KEY is not set"

**Solution:**

1. Check `.env.local` (or env vars) include the key
2. Verify key format: should be `keyId:keySecret` (from Ably dashboard)
3. Restart dev server: `npm run dev`

### Connection State Stuck on "Connecting"

**Solution:**

1. Check Ably API key is valid: https://ably.com/dashboard/apps
2. Check browser network tab for XHR/WebSocket errors
3. Verify no CORS issues (Ably handles this, but check console)
4. Restart browser and dev server

### High Latency / Missing Updates

**Solution:**

1. Check `clientId` format in sessionStorage
2. Verify Ably account quota not exceeded: https://ably.com/dashboard
3. Check backend is actually publishing to channels
4. Look at `lastHeartbeat` in RealtimeDashboard

### Pub/Sub vs Ably Conflict

**Note:** Ably is **optional** and **complementary** to Pub/Sub

- Pub/Sub handles backend-to-backend messaging (Engines, Functions)
- Ably handles backend-to-frontend messaging (Web Dashboard)
- Both can run simultaneously without conflict

---

## 📚 Component Usage Examples

### Example 1: Display Live Quotes

```typescript
// pages/dashboard.tsx
import { LiveMarketQuotes } from '@/components/LiveMarketQuotes';

export default function Dashboard() {
  return (
    <div>
      <LiveMarketQuotes />
    </div>
  );
}
```

### Example 2: Custom Real-Time Component

```typescript
'use client';

import { useMarketData } from '@/hooks/useAbly';
import { useState } from 'react';

export function MyPriceDisplay() {
  const [price, setPrice] = useState(null);

  useMarketData((data) => {
    if (data.symbol === 'AAPL') {
      setPrice(data.price);
    }
  });

  return <div>AAPL: ₹{price}</div>;
}
```

### Example 3: Monitor Connection State

```typescript
import { useAblyConnection } from '@/hooks/useAbly';

export function ConnectionStatus() {
  const { isConnected, error } = useAblyConnection();

  return (
    <div>
      {isConnected ? '🟢 Live' : '🔴 Offline'}
      {error && <p>Error: {error.message}</p>}
    </div>
  );
}
```

---

## 🔗 Related Documentation

- [ABLY_INTEGRATION_GUIDE.md](ABLY_INTEGRATION_GUIDE.md) - Full platform integration
- [00_START_HERE.md](00_START_HERE.md) - Project overview
- [frontend/web-app/.env.example](frontend/web-app/.env.example) - Environment template
- [Ably Official Docs](https://ably.com/documentation) - Ably reference
- [Phase 7 Real-Time Data](PHASE7_REAL_TIME_DATA_AND_MARKET_ANALYSIS.md) - Real-time architecture

---

## 📞 Support

**Issue Template:**

```
Issue: [Brief description]
Frontend Component: [e.g., LiveMarketQuotes]
Error Message: [From browser console]
Steps to Reproduce:
1.
2.
3.
Environment:
  - Node: [version]
  - Browser: [name + version]
  - OS: [Windows/macOS/Linux]
```

---

**Last Updated:** 2026-01-19
**Next Review:** 2026-02-19 (Q1 Performance Check)
