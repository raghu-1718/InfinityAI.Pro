# 🚀 Real-Time Data Quick Reference

## ✅ What Was Deployed

| Component              | Status      | URL/Command                                                 |
| ---------------------- | ----------- | ----------------------------------------------------------- |
| **WebSocket Streamer** | ✅ LIVE     | https://websocket-streamer-228557716858.us-central1.run.app |
| **Cloud Schedulers**   | ✅ 5 ACTIVE | Every 5-10 sec during 9 AM - 11 PM                          |
| **Timezone Fix**       | ✅ FIXED    | Engine-B shows correct IST                                  |
| **Commodity Hours**    | ✅ EXTENDED | Trading until 11:15 PM (not 3:30 PM)                        |

---

## 🔍 Quick Health Checks

### 1. WebSocket Status

```bash
curl "https://websocket-streamer-228557716858.us-central1.run.app/health"
```

**Expected**: `{"status": "healthy", "websocket_connected": true}`

### 2. Market Status

```bash
curl "https://engine-b-3acobgd3qa-uc.a.run.app/api/v1/market/status"
```

**Expected**: Correct IST time (e.g., "19-01-2026 03:33:24 PM")

### 3. Cloud Schedulers

```bash
gcloud scheduler jobs list --location=us-central1 --format="table(name,state,lastAttemptTime)"
```

**Expected**: All 5 schedulers showing `ENABLED` state

### 4. Pub/Sub Messages

```bash
gcloud pubsub subscriptions pull market-data-test-sub --limit=5
```

**Expected**: New messages after tomorrow 9:15 AM

---

## 📊 Data Flow (Simplified)

```
DhanHQ API ──┬──► Cloud Schedulers (every 5-10 sec) ──► Engine-C ──► Pub/Sub
             │
             └──► WebSocket (tick-level) ──────────────────────────► Pub/Sub
                                                                          │
                                                                          ▼
                                                          Engine-A & Engine-B consume
```

---

## 🕐 When Will Data Flow?

**Tomorrow Morning** (Monday, Jan 20, 2026):

- **9:15 AM**: Cloud Schedulers start triggering
- **9:15 AM**: WebSocket streaming live ticks
- **9:20 AM**: Pub/Sub should have fresh data
- **3:30 PM**: Equity market closes (schedulers keep running)
- **11:15 PM**: Commodity market closes (schedulers stop)

**Right Now** (3:40 PM Sunday):

- WebSocket: ✅ Connected, waiting for market open
- Schedulers: ⏳ Paused (next trigger: tomorrow 9:15 AM)
- Pub/Sub: Old messages (will refresh tomorrow)

---

## 🎯 What to Verify Tomorrow

### At 9:15 AM (Market Open)

1. Check Cloud Scheduler logs:

   ```bash
   gcloud logging read "resource.type=cloud_scheduler_job" --limit=10
   ```

2. Pull fresh Pub/Sub messages:

   ```bash
   gcloud pubsub subscriptions pull market-data-test-sub --limit=10
   ```

   **Look for**: JSON with `"source": "engine-c-dhan"` or `"source": "dhan-websocket"`

3. Check WebSocket logs:
   ```bash
   gcloud logging read "resource.labels.service_name=websocket-streamer AND severity>=INFO" --limit=20
   ```
   **Look for**: `✅ Published tick: NIFTY` or similar

---

## ⚙️ Key Services

| Service                     | Purpose                | Schedule                   |
| --------------------------- | ---------------------- | -------------------------- |
| `realtime-data-poller`      | Fetch account funds    | Every 5 min (9 AM - 11 PM) |
| `realtime-positions-poller` | Fetch open positions   | Every 10 min               |
| `realtime-orders-poller`    | Fetch order status     | Every 10 min               |
| `market-data-publisher`     | Trigger Cloud Function | Every 5 min                |
| `websocket-streamer`        | Live tick streaming    | Always-on (min 1 instance) |

---

## 🚨 Emergency Commands

### Pause All Schedulers

```bash
gcloud scheduler jobs pause realtime-data-poller --location=us-central1
gcloud scheduler jobs pause realtime-positions-poller --location=us-central1
gcloud scheduler jobs pause realtime-orders-poller --location=us-central1
gcloud scheduler jobs pause market-data-publisher --location=us-central1
gcloud scheduler jobs pause live-data-ingestion-scheduler --location=us-central1
```

### Resume All Schedulers

```bash
gcloud scheduler jobs resume realtime-data-poller --location=us-central1
# (repeat for all 5 schedulers)
```

### Stop WebSocket Streamer

```bash
gcloud run services update websocket-streamer --min-instances=0 --region=us-central1
```

### Restart WebSocket Streamer

```bash
gcloud run services update websocket-streamer --min-instances=1 --region=us-central1
```

---

## 📋 System Status Right Now

**Trading Mode**: 💰 LIVE (Real Money)
**Account Balance**: ₹100.25
**Client ID**: 1101302170
**Broker**: DhanHQ

**Data Providers**:

- ✅ DhanHQ REST API (via Cloud Schedulers)
- ✅ DhanHQ WebSocket (via Cloud Run streamer)
- ✅ Pub/Sub (7 topics, 4 subscriptions)
- ✅ Cloud Functions (market-data-ingestion)

**Market Status**:

- Equity: CLOSED (opens tomorrow 9:15 AM)
- Commodities: CLOSED (opens tomorrow 9:15 AM)

**Next Action**: Wait for tomorrow morning, then verify data flow ✅

---

## 📞 Support

**Logs Location**: Google Cloud Logging
**Project**: galvanic-pulsar-482815-h0
**Region**: us-central1
**Deployment Docs**: [REALTIME_DATA_DEPLOYMENT_COMPLETE.md](./REALTIME_DATA_DEPLOYMENT_COMPLETE.md)

**Created**: January 19, 2026, 3:40 PM IST
