# Ably Integration Guide - Phase 7 Real-Time Data Platform

## Overview

**Ably** is an enterprise-grade real-time messaging platform that serves as an optional **bridge layer** for the InfinityAI.Pro trading platform. While not required for basic Phase 7 functionality (which uses GCP Pub/Sub), Ably provides enhanced capabilities for:

1. **Real-Time WebSocket Streaming** - Direct push updates to frontend without polling
2. **Multi-Region Distribution** - Globally replicated message delivery
3. **Fallback Redundancy** - Automatic failover if GCP Pub/Sub unavailable
4. **Client-Side Subscriptions** - Browser/mobile clients connect directly to Ably channels
5. **Message History** - Automatic persistence for late subscribers (optional)

---

## How Ably Is Used in Phase 7

### Architecture Pattern

```
Data Providers (APIs)
    ↓
Cloud Run Ingestion Services
    ├─→ GCP Pub/Sub (primary, internal)
    └─→ Ably Channels (secondary, real-time frontend bridge)
    ↓
Dual-Channel Distribution:
├─ Backend Consumers (Engines) ← Pub/Sub
└─ Frontend Clients (WebSocket) ← Ably Channels
```

### Ably Use Cases

#### 1. **Real-Time Quote Updates to Dashboard**

```
Frontend subscribes to Ably channel: "market-data:AAPL"
Backend publishes quote updates to channel:
  {symbol: "AAPL", price: 182.50, bid: 182.48, ask: 182.52, timestamp: "2026-01-19T..."}
Frontend receives update <100ms after publish
No polling required; reduced frontend complexity
```

#### 2. **News Feed Streaming**

```
Frontend subscribes: "news:trending"
Backend publishes article arrivals:
  {title: "Apple Q4 Results Exceed...", source: "Reuters", sentiment: "positive"}
Real-time news ticker updates without refresh
```

#### 3. **Trade Signal Notifications**

```
Frontend subscribes: "signals:{userId}"
Backend publishes trading signals:
  {strategy: "momentum", symbol: "AAPL", action: "BUY", strength: 0.92}
User sees alerts in real-time
```

#### 4. **System Health Monitoring**

```
Frontend subscribes: "system:health"
Backend publishes:
  {service: "market-data-ingestion", status: "healthy", uptime: "23h45m"}
Operations dashboard shows live provider status
```

---

## Ably Integration Steps

### Step 1: Create Ably Account & Get API Key

1. Navigate to https://ably.com/signup
2. Create free account (25M messages/month included)
3. Go to **Settings → API Keys** → Copy **Root API Key**
4. Store in Secret Manager:
   ```powershell
   # Already in setup_provider_secrets.ps1, but manual example:
   "your-ably-api-key" | gcloud secrets versions add provider-ably-api-key --data-file=-
   ```

### Step 2: Configure Ably Channels

Create a backend service to bridge Pub/Sub → Ably:

**backend/ably-bridge/src/main.py** (pseudocode):

```python
import ably
from google.cloud import pubsub_v1

# Initialize Ably client
ably_client = ably.Realtime(key=os.getenv("PROVIDER_ABLY_API_KEY"))

# Subscribe to Pub/Sub
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, "market-data-processed")

def forward_to_ably(message):
    """Forward Pub/Sub message to Ably channel"""
    data = json.loads(message.data.decode())

    # Determine channel from data
    symbol = data.get("symbol")
    channel = ably_client.channels.get(f"market-data:{symbol}")

    # Publish to Ably
    channel.publish(name="quote", data=data)
    message.ack()

# Subscribe with callback
subscriber.subscribe(subscription_path, callback=forward_to_ably)
```

### Step 3: Frontend Client Implementation

**frontend/src/hooks/useAblySubscription.ts** (React example):

```typescript
import { useEffect, useState } from 'react';
import * as Ably from 'ably';

export function useAblySubscription(channelName: string) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Initialize Ably client with token (secure, from backend)
    const client = new Ably.Realtime({
      authUrl: '/api/ably-token',
      authMethod: 'GET'
    });

    const channel = client.channels.get(channelName);

    // Subscribe to messages
    channel.subscribe(message => {
      setData(message.data);
    });

    // Handle connection state
    client.on('connected', () => setConnected(true));
    client.on('disconnected', () => setConnected(false));

    return () => {
      channel.unsubscribe();
      client.close();
    };
  }, [channelName]);

  return { data, connected };
}

// Usage in component:
function QuoteTicket({ symbol }) {
  const { data: quote, connected } = useAblySubscription(`market-data:${symbol}`);

  return (
    <div>
      <span style={{ color: connected ? 'green' : 'red' }}>
        {connected ? 'LIVE' : 'OFFLINE'}
      </span>
      {quote && <span>${quote.price}</span>}
    </div>
  );
}
```

### Step 4: Backend Token Generation

Secure clients get ephemeral tokens (not full API key):

**backend/src/api/ably.py**:

```python
@app.post("/api/ably-token")
async def get_ably_token(user_id: str):
    """Generate ephemeral Ably token for client"""
    ably_client = Ably.AblyRest(key=os.getenv("PROVIDER_ABLY_API_KEY"))

    # Token grants access to specific channels only
    token_request = ably_client.auth.create_token_request({
        'capability': {
            f'market-data:*': ['subscribe'],
            f'news:*': ['subscribe'],
            f'signals:{user_id}': ['subscribe']
        },
        'ttl': 3600  # 1 hour
    })

    return {'token': token_request.get('token')}
```

---

## Ably Rate Limits & Pricing

| Tier       | Message Limit | Cost               | Use Case                    |
| ---------- | ------------- | ------------------ | --------------------------- |
| Free       | 25M/month     | $0                 | Development, small volume   |
| Pro        | 100M+/month   | $0.001 per message | Production, high volume     |
| Enterprise | Unlimited     | Custom             | Financial, critical systems |

**For InfinityAI.Pro:**

- Market data: ~10 updates/min per symbol × 100 symbols = 1M/month (~free tier)
- News: ~100 articles/day = 3k/month (~free tier)
- **Total estimate: 1M+ messages/month → Free tier sufficient for MVP**

---

## Ably vs. GCP Pub/Sub

| Aspect                | GCP Pub/Sub           | Ably                    |
| --------------------- | --------------------- | ----------------------- |
| **Primary Use**       | Backend-to-backend    | Client-facing real-time |
| **Latency**           | <50ms (internal)      | <100ms (global)         |
| **WebSocket Support** | ❌ (requires bridge)  | ✅ (native)             |
| **Authentication**    | Service accounts      | Token/API key           |
| **Message History**   | Temporary             | Optional persistence    |
| **Cost (1M msg/mo)**  | ~$5                   | Free (first 25M)        |
| **Best For**          | Internal architecture | Client subscriptions    |

**Recommendation:** Use **Pub/Sub for backend orchestration** (engines, Firestore writes), **Ably for frontend real-time UI** (quote ticker, alerts, news feed).

---

## Implementation Plan (Optional)

### Phase 7a: (Current - Pub/Sub Foundation)

✅ Market data & news ingestion to Pub/Sub
✅ Backend consumers (engines) reading from Pub/Sub

### Phase 7b: (Optional - Ably Bridge)

- [ ] Create ably-bridge Cloud Run service
- [ ] Subscribe to Pub/Sub; forward to Ably channels
- [ ] Frontend Ably client library (React hook)
- [ ] Ably token endpoint for authentication
- [ ] Deploy to production with feature flag

### Phase 7c: (Optional - Dual-Channel Consumer)

- [ ] Update frontend dashboard to consume from Ably
- [ ] Real-time quote ticker widget
- [ ] Live news feed component
- [ ] Alert notification system

---

## Quick Start: Ably Bridge Service

**backend/ably-bridge/src/main.py**:

```python
import json
import os
import ably
from google.cloud import pubsub_v1
from flask import Flask
from concurrent.futures import TimeoutError

app = Flask(__name__)

# Initialize clients
ably_client = ably.Realtime(key=os.getenv("PROVIDER_ABLY_API_KEY"))
subscriber = pubsub_v1.SubscriberClient()

@app.post("/bridge/start")
def start_bridge():
    """Start Pub/Sub → Ably forwarding"""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    subscription_path = subscriber.subscription_path(project_id, "market-data-processed")

    def forward_message(message):
        try:
            data = json.loads(message.data.decode())
            symbol = data.get("symbol")

            # Forward to Ably
            channel = ably_client.channels.get(f"market-data:{symbol}")
            channel.publish(name="quote", data=data)

            message.ack()
        except Exception as e:
            print(f"Error: {e}")
            message.nack()

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=forward_message)

    # Block indefinitely
    try:
        streaming_pull_future.result(timeout=3600)
    except TimeoutError:
        streaming_pull_future.cancel()

@app.get("/health")
def health():
    return {"status": "ok", "service": "ably-bridge"}

if __name__ == "__main__":
    app.run(port=8080, debug=False)
```

---

## Monitoring Ably

### Dashboard Metrics

1. Navigate to https://ably.com/login → Dashboard
2. View **Message Throughput, Active Channels, Connected Clients**
3. Set up alerts for quota usage

### CLI Monitoring

```bash
# Via Ably REST API
curl -H "Authorization: Basic $(echo -n $ABLY_KEY | base64)" \
  https://rest.ably.io/channels \
  | jq '.channels[] | {name, occupancy}'
```

---

## Security Considerations

1. **Never expose API keys in frontend** → Use token endpoint
2. **Token-based auth** → Tokens have TTL and limited capabilities
3. **Channel permissions** → Users can only subscribe to their own channels
4. **Message encryption** → Enable optional end-to-end encryption
5. **Rate limits** → Prevent abuse with connection limits

---

## Conclusion

Ably is an **optional enhancement** to Phase 7:

- ✅ Use **Pub/Sub** for primary backend data flow (required)
- ✅ Add **Ably bridge** to enable WebSocket streaming to clients (optional, Phase 7b)
- ✅ Leverages existing Pub/Sub data → minimal code changes
- ✅ Scales with volume; free tier covers MVP

**Next Decision:** Deploy Phase 7 Pub/Sub-only (now), then add Ably bridge if frontend real-time requirements emerge.
