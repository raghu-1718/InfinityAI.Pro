# 📊 Real-Time Trading Engine - Configuration & URLs

## Current Deployment Information

**Project**: `galvanic-pulsar-482815-h0`
**Service**: `engine-c`
**Region**: `us-central1`
**Cloud Run Endpoint**: `https://engine-c-3acobgd3qa-uc.a.run.app`

---

## 🔗 API Endpoints

### Primary Account Data Endpoint (✅ RECOMMENDED)

**GET** `/api/v1/user/{user_id}/account`

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "https://engine-c-3acobgd3qa-uc.a.run.app/api/v1/user/1101302170/account"
```

**Response**: Complete account data including:

- Available funds
- Utilized margin
- Current positions
- Open orders
- Trade history
- Holdings summary

**Status**: ✅ **Verified Working**

---

### Real-Time SSE Stream

**GET** `/api/realtime/stream/{user_id}`

**URL**: `https://engine-c-3acobgd3qa-uc.a.run.app/api/realtime/stream/{user_id}`

**Format**: Server-Sent Events (SSE)

**Connection**: Persistent HTTP streaming with:

- 30-second heartbeat
- Auto-reconnect support
- 20-minute timeout

**Frontend Example** (JavaScript):

```javascript
const userId = "1101302170";
const eventSource = new EventSource(
  `https://engine-c-3acobgd3qa-uc.a.run.app/api/realtime/stream/${userId}`
);

// Listen for order updates
eventSource.addEventListener("order_update", (event) => {
  const update = JSON.parse(event.data);
  console.log("Order Update:", {
    order_id: update.order_id,
    symbol: update.symbol,
    status: update.status,
    timestamp: update.timestamp,
  });
});

// Listen for position updates
eventSource.addEventListener("position_update", (event) => {
  const position = JSON.parse(event.data);
  console.log("Position Update:", position);
});

// Handle connection loss
eventSource.onerror = () => {
  console.log("Connection lost, will auto-reconnect...");
};
```

**Status**: ✅ **Deployed & Ready**

---

### Alternative: JSON Lines Stream (NDJSON)

**GET** `/api/realtime/updates/{user_id}`

**URL**: `https://engine-c-3acobgd3qa-uc.a.run.app/api/realtime/updates/{user_id}`

**Format**: NDJSON (one JSON object per line)

**Frontend Example** (Node.js/Browser):

```javascript
const userId = "1101302170";
const response = await fetch(
  `https://engine-c-3acobgd3qa-uc.a.run.app/api/realtime/updates/${userId}`
);

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value);
  const lines = buffer.split("\n");
  buffer = lines.pop(); // Keep incomplete line

  for (const line of lines) {
    if (line.trim()) {
      const event = JSON.parse(line);
      console.log("Real-time update:", event);
    }
  }
}
```

**Status**: ✅ **Deployed & Ready**

---

## 🔐 Dhan OAuth Configuration

### Postback Webhook URL

**Configure in Dhan Developer Dashboard**

```
https://engine-c-3acobgd3qa-uc.a.run.app/api/dhan/postback
```

**Purpose**: Receive real-time order updates and trade confirmations

**Data Stored**:

- Order ID
- Symbol
- Status (PENDING, FILLED, REJECTED)
- Side (BUY, SELL)
- Price & Quantity
- Filled Quantity
- Complete payload

**Firestore Collection**: `trade_events`

### OAuth Redirect URL

**Configure in Dhan Developer Dashboard**

```
https://engine-c-3acobgd3qa-uc.a.run.app/auth/dhan/success
```

**Purpose**: Receive authorization code after OAuth login

**Flow**:

1. User clicks "Login with Dhan"
2. Redirected to `https://login.dhan.co`
3. User authenticates
4. Redirected back to `/auth/dhan/success` with auth code
5. Engine-C exchanges code for access token
6. Token stored in Firestore

---

## 📱 Frontend Integration Guide

### Setup Real-Time Dashboard

**TypeScript/React Hook**:

```typescript
// hooks/useRealtime.ts
import { useEffect, useState, useCallback } from 'react';

interface TradeEvent {
  type: 'order_update' | 'position_update' | 'trade_update';
  data: {
    order_id?: string;
    symbol?: string;
    status?: string;
    side?: string;
    price?: number;
    timestamp: string;
  };
}

export function useRealtimeTrading(userId: string) {
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState<TradeEvent[]>([]);
  const [latestUpdate, setLatestUpdate] = useState<TradeEvent | null>(null);

  useEffect(() => {
    const SERVICE_URL = 'https://engine-c-3acobgd3qa-uc.a.run.app';
    const eventSource = new EventSource(
      `${SERVICE_URL}/api/realtime/stream/${userId}`
    );

    // Connection opened
    eventSource.addEventListener('open', () => {
      setConnected(true);
      console.log('✅ Real-time connection established');
    });

    // Handle all trade events
    ['order_update', 'position_update', 'trade_update'].forEach((eventType) => {
      eventSource.addEventListener(eventType, (event) => {
        try {
          const data = JSON.parse(event.data);
          const tradeEvent: TradeEvent = { type: eventType as any, data };

          setEvents((prev) => [tradeEvent, ...prev.slice(0, 99)]);
          setLatestUpdate(tradeEvent);

          // Log to analytics if needed
          console.log(`📊 ${eventType}:`, data);
        } catch (err) {
          console.error(`Failed to parse ${eventType}:`, err);
        }
      });
    });

    // Connection error
    eventSource.onerror = () => {
      setConnected(false);
      console.log('❌ Real-time connection lost');
      // Browser will auto-reconnect
    };

    return () => eventSource.close();
  }, [userId]);

  return {
    connected,
    events,
    latestUpdate,
    eventCount: events.length,
  };
}

// In your Dashboard component:
function TradingDashboard() {
  const userId = '1101302170'; // Your user ID
  const { connected, latestUpdate, eventCount } = useRealtimeTrading(userId);

  return (
    <div className="dashboard">
      {/* Connection Status */}
      <div className={`connection-status ${connected ? 'live' : 'offline'}`}>
        {connected ? '🟢 Live' : '🔴 Offline'}
      </div>

      {/* Latest Update */}
      {latestUpdate && (
        <div className="latest-update">
          <h3>{latestUpdate.type}</h3>
          <p>Order: {latestUpdate.data.order_id}</p>
          <p>Status: {latestUpdate.data.status}</p>
          <p>Symbol: {latestUpdate.data.symbol}</p>
          <time>{new Date(latestUpdate.data.timestamp).toLocaleTimeString()}</time>
        </div>
      )}

      {/* Event Counter */}
      <div className="event-counter">
        Received {eventCount} events
      </div>
    </div>
  );
}
```

### Performance Monitoring

Track real-time metrics:

```typescript
// Monitor connection health
const connectionMetrics = {
  connectedAt: Date.now(),
  messageCount: 0,
  errorCount: 0,
  averageLatency: 0,
  lastMessageAt: Date.now(),
};

eventSource.addEventListener("order_update", (event) => {
  const receivedAt = Date.now();
  const eventData = JSON.parse(event.data);
  const sentAt = new Date(eventData.timestamp).getTime();

  const latency = receivedAt - sentAt;
  connectionMetrics.messageCount++;
  connectionMetrics.lastMessageAt = receivedAt;
  connectionMetrics.averageLatency =
    (connectionMetrics.averageLatency * (connectionMetrics.messageCount - 1) +
      latency) /
    connectionMetrics.messageCount;

  console.log(
    `Message latency: ${latency}ms (avg: ${connectionMetrics.averageLatency.toFixed(0)}ms)`
  );
});
```

---

## 📊 Firestore Schema

### Collection: `trade_events`

**Document ID Pattern**: `{order_id}_{timestamp}`

**Fields**:

```json
{
  "order_id": "ORD-123456",
  "client_id": "1101302170",
  "symbol": "INFY-EQ",
  "status": "FILLED",
  "side": "BUY",
  "price": 1500.5,
  "quantity": 10,
  "filled_qty": 10,
  "full_payload": {
    /* complete Dhan postback data */
  },
  "received_at": "2026-01-07T10:30:00.123Z",
  "timestamp": 1641558600123,
  "processor_version": "1.0"
}
```

### Collection: `user_positions`

**Document ID**: `{client_id}`

**Fields**:

```json
{
  "position_INFY-EQ": {
    "symbol": "INFY-EQ",
    "qty": 10,
    "avg_price": 1500.5,
    "status": "open",
    "last_updated": "2026-01-07T10:30:00.123Z"
  },
  "position_SBIN-EQ": {
    "symbol": "SBIN-EQ",
    "qty": -5,
    "avg_price": 500.0,
    "status": "open",
    "last_updated": "2026-01-07T10:31:00.456Z"
  },
  "last_modified": "2026-01-07T10:31:00.456Z"
}
```

---

## 🧪 Testing

### Quick Test Script

```bash
#!/bin/bash

SERVICE_URL="https://engine-c-3acobgd3qa-uc.a.run.app"
USER_ID="1101302170"
TOKEN=$(gcloud auth print-identity-token)

echo "🧪 Testing Real-Time Trading Engine"
echo "================================="

# Test 1: Account Data
echo -e "\n1. Testing account data endpoint..."
curl -s -H "Authorization: Bearer $TOKEN" \
  "$SERVICE_URL/api/v1/user/$USER_ID/account" | jq '.data.summary'

# Test 2: SSE Connection (5 seconds)
echo -e "\n2. Testing SSE connection (5 seconds)..."
timeout 5 curl -N -H "Authorization: Bearer $TOKEN" \
  "$SERVICE_URL/api/realtime/stream/$USER_ID" || true

# Test 3: Postback
echo -e "\n\n3. Testing postback webhook..."
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "orderId": "TEST-'$(date +%s)'",
    "orderStatus": "FILLED",
    "transactionType": "BUY",
    "tradingSymbol": "NIFTY-50",
    "clientId": "'$USER_ID'",
    "price": 23000,
    "quantity": 1,
    "filledQuantity": 1
  }' \
  "$SERVICE_URL/api/dhan/postback" | jq '.'

# Test 4: Firestore Verification
echo -e "\n\n4. Checking Firestore storage..."
gcloud firestore documents list --collection-id=trade_events --limit=1

echo -e "\n✅ Testing complete!"
```

---

## 🔒 Security Notes

### Authentication

All endpoints require `Authorization: Bearer <token>` header

Tokens can be obtained via:

```bash
# Using gcloud CLI
gcloud auth print-identity-token

# Or in application
from google.auth import default
from google.auth.transport.requests import Request

credentials, project = default()
credentials.refresh(Request())
token = credentials.token
```

### CORS Configuration

Frontend domain must be whitelisted in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://infinityai.pro",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Rate Limiting

Recommended per-user limits:

- Postback webhooks: 100/min
- SSE connections: 5 concurrent per user
- Account queries: 60/min

---

## 📈 Performance Targets

| Metric               | Target  | Threshold             |
| -------------------- | ------- | --------------------- |
| Postback Latency     | < 100ms | > 500ms ⚠️            |
| SSE Connection Time  | < 500ms | > 2000ms ⚠️           |
| Firestore Write      | < 50ms  | > 200ms ⚠️            |
| SSE Event Delivery   | < 200ms | > 1000ms ⚠️           |
| Concurrent SSE Users | 1000+   | Scale at 80% capacity |

---

## 🆘 Support & Troubleshooting

### Check Service Status

```bash
gcloud run services describe engine-c --region=us-central1
```

### View Recent Logs

```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="engine-c"' \
  --limit=50 \
  --format=json
```

### Debug SSE Issues

```bash
# Check connection in Chrome DevTools:
# 1. Open Network tab
# 2. Look for EventSource request to /api/realtime/stream/...
# 3. Check Status (should be 200)
# 4. Check Response tab (should show event stream)
```

### Firestore Verification

```bash
# Check documents were stored
gcloud firestore documents list --collection-id=trade_events

# Get specific trade event
gcloud firestore documents get trade_events/ORD-123_1641558600
```

---

## 📋 Checklist: Complete Setup

- [ ] Deploy engine-c to Cloud Run
- [ ] Configure Dhan postback URL: `{SERVICE_URL}/api/dhan/postback`
- [ ] Configure Dhan redirect URL: `{SERVICE_URL}/auth/dhan/success`
- [ ] Test account data endpoint
- [ ] Test SSE stream connection
- [ ] Send test postback and verify Firestore storage
- [ ] Integrate frontend SSE hook
- [ ] Configure CORS for frontend domain
- [ ] Set up Cloud Logging alerts
- [ ] Monitor performance metrics

---

**Last Updated**: 2026-01-07
**Version**: 1.0.0
**Status**: ✅ Production Ready
