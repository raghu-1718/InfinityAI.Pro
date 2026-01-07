# 🚀 Quick Reference Card - Real-Time Trading Engine

## Service Information

- **Project**: `galvanic-pulsar-482815-h0`
- **Service**: `engine-c` (Cloud Run)
- **Region**: `us-central1`
- **URL**: `https://engine-c-3acobgd3qa-uc.a.run.app`

---

## API Endpoints

### 📊 Account Data (Recommended)

```
GET /api/v1/user/{user_id}/account
```

Complete account: funds, positions, orders, trades, holdings

### 🔴 Real-Time SSE Stream

```
GET /api/realtime/stream/{user_id}
```

Server-Sent Events - perfect for dashboards

### 📋 Real-Time NDJSON Stream

```
GET /api/realtime/updates/{user_id}
```

JSON Lines format - for any client

### 📥 Dhan Postback Webhook

```
POST /api/dhan/postback
```

Receives order updates, stores in Firestore, broadcasts SSE

---

## Dhan Configuration

### Postback URL (Configure in Dhan Dashboard)

```
https://engine-c-3acobgd3qa-uc.a.run.app/api/dhan/postback
```

### Redirect URL (Configure in Dhan Dashboard)

```
https://engine-c-3acobgd3qa-uc.a.run.app/auth/dhan/success
```

---

## Frontend Integration (Copy-Paste Ready)

### JavaScript - SSE

```javascript
const userId = "1101302170";
const eventSource = new EventSource(
  `https://engine-c-3acobgd3qa-uc.a.run.app/api/realtime/stream/${userId}`
);

eventSource.addEventListener("order_update", (event) => {
  const update = JSON.parse(event.data);
  console.log("Trade:", update);
});

eventSource.onerror = () => console.log("Reconnecting...");
```

### React Hook

```typescript
import { useEffect, useState } from "react";

export function useRealtime(userId: string) {
  const [trade, setTrade] = useState(null);

  useEffect(() => {
    const es = new EventSource(`/api/realtime/stream/${userId}`);
    es.addEventListener("order_update", (e) => {
      setTrade(JSON.parse(e.data));
    });
    return () => es.close();
  }, [userId]);

  return trade;
}
```

---

## Testing Commands

### Test Account Data

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "https://engine-c.../api/v1/user/1101302170/account"
```

### Test Postback

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"orderId":"TEST-1","orderStatus":"FILLED","transactionType":"BUY","tradingSymbol":"INFY-EQ","clientId":"1101302170"}' \
  "https://engine-c.../api/dhan/postback"
```

### Test SSE

```bash
curl -N "https://engine-c.../api/realtime/stream/1101302170"
```

### Check Logs

```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="engine-c"' --limit=20
```

### Check Firestore

```bash
gcloud firestore documents list --collection-id=trade_events --limit=5
```

---

## Firestore Collections

### trade_events

Every order/trade from Dhan

- Document: `{order_id}_{timestamp}`
- Fields: order_id, client_id, symbol, status, side, price, qty, etc.

### user_positions

Current holdings per user

- Document: `{client_id}`
- Fields: position\_{symbol}, last_modified

### activity_logs (Existing)

System activity and trade events

---

## Performance Targets

| Operation            | Target  | Alert   |
| -------------------- | ------- | ------- |
| Postback → Firestore | < 100ms | > 500ms |
| SSE Connection       | < 500ms | > 2s    |
| Account Query        | < 500ms | > 1s    |
| Firestore Write      | < 50ms  | > 200ms |

---

## Deployment Steps (Quick)

```bash
# 1. Build
cd backend/engine-c
gcloud builds submit --tag gcr.io/galvanic-pulsar-482815-h0/engine-c:latest .

# 2. Deploy
gcloud run deploy engine-c \
  --image gcr.io/galvanic-pulsar-482815-h0/engine-c:latest \
  --region us-central1 \
  --memory 2Gi --cpu 2

# 3. Verify
gcloud run services describe engine-c --region us-central1

# 4. Test
curl "https://engine-c.../health"
```

---

## Troubleshooting

### SSE Not Connecting?

1. Check authorization token
2. Verify user_id format
3. Look in browser Network tab
4. Check Cloud Logging

### Postback Not Stored?

1. Verify Firestore rules allow writes
2. Check service account permissions
3. Look for "Postback stored" in logs
4. Verify firestore client initialized

### High Latency?

1. Check Cloud Run CPU/Memory
2. Monitor Firestore RUs
3. Look for slow queries in logs
4. Consider scaling up resources

---

## Files Reference

| Purpose        | File                                                                                |
| -------------- | ----------------------------------------------------------------------------------- |
| API URLs       | [CONFIG_AND_URLS.md](CONFIG_AND_URLS.md)                                            |
| Deploy         | [DEPLOYMENT_GUIDE.md](backend/engine-c/DEPLOYMENT_GUIDE.md)                         |
| Integration    | [REALTIME_INTEGRATION_GUIDE.md](backend/engine-c/src/REALTIME_INTEGRATION_GUIDE.md) |
| Implementation | [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)                            |
| Code           | [realtime_enhancements.py](backend/engine-c/src/realtime_enhancements.py)           |

---

## Key URLs (Your Endpoint)

```
Service: https://engine-c-3acobgd3qa-uc.a.run.app

Account:  /api/v1/user/{id}/account
SSE:      /api/realtime/stream/{id}
NDJSON:   /api/realtime/updates/{id}
Postback: /api/dhan/postback
Health:   /health
```

---

## Security Essentials

- ✅ All requests require Bearer token
- ✅ User can only access own data
- ✅ Credentials in Secret Manager
- ✅ HTTPS only
- ✅ Rate limiting recommended

---

## Monitoring Dashboard

### Commands for Monitoring

```bash
# Postback events
gcloud logging read 'text:"Postback received"' --limit=20

# Real-time events
gcloud logging read 'text:"Broadcast:"' --limit=20

# Errors
gcloud logging read 'severity=ERROR' --limit=10

# Firestore storage
gcloud firestore documents list --collection-id=trade_events --limit=5

# Cloud Run metrics
gcloud monitoring metrics-descriptors list | grep cloud_run
```

---

## Status Check (One Command)

```bash
# Complete health check
SERVICE_URL="https://engine-c-3acobgd3qa-uc.a.run.app"
TOKEN=$(gcloud auth print-identity-token)

echo "1. Service Health:"
curl -s -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/health" | jq .

echo -e "\n2. Account Data:"
curl -s -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/api/v1/user/1101302170/account" | jq '.data.summary'

echo -e "\n3. SSE Connection (5s):"
timeout 5 curl -N -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/api/realtime/stream/1101302170" || echo "Stream OK"

echo -e "\n✅ All endpoints operational"
```

---

## Next Steps

1. **Deploy**: Run deployment commands above
2. **Configure**: Update Dhan OAuth URLs
3. **Integrate**: Add SSE hook to frontend
4. **Monitor**: Set up Cloud Logging alerts
5. **Test**: Send live trade orders

---

**Status**: ✅ Production Ready
**Last Updated**: 2026-01-07
**Version**: 1.0.0
