# Ably Frontend Quick Reference - Developer Card

## 🚀 30-Second Setup

```bash
# 1. Get API key from https://ably.com/dashboard → API Keys
# 2. Create .env.local in frontend/web-app:
echo "NEXT_PUBLIC_ABLY_API_KEY=your-key" > frontend/web-app/.env.local

# 3. Start dev server
cd frontend/web-app && npm run dev
```

## 📡 Most Common Hooks

### Subscribe to Market Data

```typescript
import { useMarketData } from '@/hooks/useAbly';

export function MyComponent() {
  useMarketData((data) => {
    console.log(`${data.symbol}: ₹${data.price}`);
  });
  return <div>Check console</div>;
}
```

### Subscribe to Portfolio Updates

```typescript
import { usePortfolioUpdates } from "@/hooks/useAbly";

usePortfolioUpdates(userId, (portfolio) => {
  console.log(`Portfolio Value: ₹${portfolio.totalValue}`);
});
```

### Subscribe to Trading Signals

```typescript
import { useTradingSignals } from "@/hooks/useAbly";

useTradingSignals(engineId, (signal) => {
  console.log(`${signal.action} ${signal.symbol} @ ${signal.confidence}%`);
});
```

### Check Connection Status

```typescript
import { useAblyConnection } from '@/hooks/useAbly';

const { isConnected, error } = useAblyConnection();

if (!isConnected && error) {
  return <div>Offline: {error.message}</div>;
}
```

## 🎯 Channel Names (Pre-Configured)

```typescript
import { ABLY_CHANNELS } from "@/lib/ably";

// Public channels
ABLY_CHANNELS.LIVE_QUOTES; // "infinityai:live-quotes"
ABLY_CHANNELS.TRADING_SIGNALS; // "infinityai:trading-signals"
ABLY_CHANNELS.PORTFOLIO_UPDATE; // "infinityai:portfolio-update"

// User-specific channels
ABLY_CHANNELS.USER_PORTFOLIO(userId); // "infinityai:portfolio:{userId}"
ABLY_CHANNELS.USER_SIGNALS(userId); // "infinityai:signals:{userId}"
ABLY_CHANNELS.USER_TRADES(userId); // "infinityai:trades:{userId}"

// System channels
ABLY_CHANNELS.SYSTEM_STATUS; // "infinityai:system-status"
ABLY_CHANNELS.ENGINE_STATUS(engineId); // "infinityai:engine:{engineId}"
```

## 🔧 Low-Level Operations

```typescript
import {
  subscribeToChannel,
  publishToChannel,
  getAblyClient,
} from "@/lib/ably";

// Subscribe to any channel
const unsubscribe = subscribeToChannel("custom-channel", (message) => {
  console.log("Received:", message.data);
});

// Publish to a channel (from frontend)
await publishToChannel("custom-channel", {
  msg: "Hello from frontend",
  timestamp: Date.now(),
});

// Unsubscribe when done
unsubscribe();
```

## ⚡ Real-Time Dashboard Component

```typescript
import { RealtimeDashboard } from '@/components/RealtimeDashboard';

export default function Page() {
  return <RealtimeDashboard userId={currentUser.id} />;
}
```

**Shows:**

- ✅ Connection status (🟢 Live / 🔴 Offline)
- ✅ Real-time event feed
- ✅ Last heartbeat timestamp
- ✅ Error alerts with reconnect button

## 🛑 Error Handling

```typescript
import { useAblyChannel } from '@/hooks/useAbly';

const { connectionState, error } = useAblyChannel('channel-name', (data) => {
  try {
    processData(data);
  } catch (e) {
    console.error('Failed to process:', e);
  }
});

// Monitor state
useEffect(() => {
  if (connectionState === 'connected') console.log('Connected');
  if (connectionState === 'failed') console.log('Connection failed');
}, [connectionState]);

// Show error
{error && <AlertBanner message={error.message} />}
```

## 🔐 Environment Variables

| Variable                   | Required | Source                                      | Usage               |
| -------------------------- | -------- | ------------------------------------------- | ------------------- |
| `NEXT_PUBLIC_ABLY_API_KEY` | ✅ Yes   | `.env.local` (dev) or Secret Manager (prod) | Ably authentication |

**Development:** Create `.env.local`

```env
NEXT_PUBLIC_ABLY_API_KEY=your-ably-api-key-here
```

**Production:** Injected via Cloud Build from Secret Manager

```bash
gcloud secrets create ably-api-key --data-file=- <<< "your-key"
```

## 📦 Already Integrated

✅ Ably SDK: `ably` (^1.2.47)
✅ AblyProvider: Wraps entire app in `src/components/providers.tsx`
✅ Type definitions: Ably types imported from `ably` package
✅ Singleton pattern: Reuses single Ably client across app
✅ Auto-reconnection: 15s timeout, 10 max attempts
✅ Development logging: Connection state changes logged in dev mode

## 🐛 Quick Debug

```bash
# Check connection in browser console
cd frontend/web-app
npm run dev

# In browser DevTools Console:
window.localStorage.getItem('ably_client_id')  # Should show client ID
// Check for "Ably connected successfully" message
```

## 📚 Full Docs

- **Frontend Integration:** [ABLY_FRONTEND_INTEGRATION_COMPLETE.md](ABLY_FRONTEND_INTEGRATION_COMPLETE.md)
- **Platform Guide:** [ABLY_INTEGRATION_GUIDE.md](ABLY_INTEGRATION_GUIDE.md)
- **Official Docs:** https://ably.com/documentation
- **React Examples:** https://github.com/ably/ably-js

## ✅ Verification

```bash
# 1. Local dev works
cd frontend/web-app && npm run dev
# → See "Live" indicator in RealtimeDashboard

# 2. Check connection in console
# → Look for "Ably connection: *** → connected"

# 3. Test subscription
# → See market quote updates or trading signals flowing in
```

---

**TL;DR:** Add API key to `.env.local`, use hooks like `useMarketData()`, components auto-subscribe. Done! 🎉
