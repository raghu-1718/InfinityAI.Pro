# InfinityAI.Pro - Deployed Service URLs & Quick Reference

**Project:** galvanic-pulsar-482815-h0  
**Region:** us-central1  
**Last Updated:** January 10, 2025

---

## 🌐 FRONTEND ACCESS

| Service | URL |
|---------|-----|
| **Dashboard** | https://galvanic-pulsar-482815-h0.web.app |

---

## 🎯 CORE TRADING ENGINES

| Engine | URL | Purpose |
|--------|-----|---------|
| **Engine A** | https://engine-a-3acobgd3qa-uc.a.run.app | Risk Orchestrator |
| **Engine B** | https://engine-b-3acobgd3qa-uc.a.run.app | AI/ML Analysis |
| **Engine C** | https://engine-c-3acobgd3qa-uc.a.run.app | Trade Execution |

**Health Endpoints:** `GET /health` for all engines

---

## 📊 DATA & MARKET FUNCTIONS

| Function | URL | Purpose |
|----------|-----|---------|
| **live-data-ingestion** | https://live-data-ingestion-3acobgd3qa-uc.a.run.app | Real-time price quotes |
| **get-live-prices** | https://get-live-prices-3acobgd3qa-uc.a.run.app | Current market prices |
| **get-price-history** | https://get-price-history-3acobgd3qa-uc.a.run.app | Historical price data |
| **detect-momentum-signals** | https://detect-momentum-signals-3acobgd3qa-uc.a.run.app | Technical signal generation |
| **get-latest-signals** | https://get-latest-signals-3acobgd3qa-uc.a.run.app | Retrieve trading signals |

---

## 💼 ACCOUNT & PORTFOLIO SERVICES

| Service | URL | Purpose |
|---------|-----|---------|
| **fetchaccountdata** | https://fetchaccountdata-3acobgd3qa-uc.a.run.app | Get Dhan account overview |
| **getdhanoverview** | https://getdhanoverview-3acobgd3qa-uc.a.run.app | Broker account summary |
| **analyzeportfolio** | https://analyzeportfolio-3acobgd3qa-uc.a.run.app | Portfolio performance analysis |
| **getusercredentials** | https://getusercredentials-3acobgd3qa-uc.a.run.app | Retrieve user credentials |
| **storeusercredentials** | https://storeusercredentials-3acobgd3qa-uc.a.run.app | Store user credentials |

---

## 🤖 AI & ANALYSIS SERVICES

| Service | URL | Purpose |
|---------|-----|---------|
| **getgeminianalysis** | https://getgeminianalysis-3acobgd3qa-uc.a.run.app | Google Gemini AI analysis |
| **getvertexaianalysis** | https://getvertexaianalysis-3acobgd3qa-uc.a.run.app | Vertex AI ML analysis |
| **getaisignals** | https://getaisignals-3acobgd3qa-uc.a.run.app | AI-generated signals |
| **getbatchaisignals** | https://getbatchaisignals-3acobgd3qa-uc.a.run.app | Batch AI signal generation |

---

## ⚙️ TRADING CONTROL SERVICES

| Service | URL | Purpose |
|---------|-----|---------|
| **starttrading** | https://starttrading-3acobgd3qa-uc.a.run.app | Initiate trading session |
| **stoptrading** | https://stoptrading-3acobgd3qa-uc.a.run.app | End trading session |
| **verifycoupon** | https://verifycoupon-3acobgd3qa-uc.a.run.app | Validate coupon codes |

---

## 📊 BACKTESTING SERVICES

| Service | URL | Purpose |
|---------|-----|---------|
| **backtest-orchestrator** | https://backtest-orchestrator-3acobgd3qa-uc.a.run.app | Historical backtesting |

---

## 🔐 CLOUD INFRASTRUCTURE (GCP CONSOLE)

| Service | Console Link | Purpose |
|---------|--------------|---------|
| **Cloud Run** | https://console.cloud.google.com/run?project=galvanic-pulsar-482815-h0 | Service management |
| **Cloud Logging** | https://console.cloud.google.com/logs?project=galvanic-pulsar-482815-h0 | Real-time logs |
| **Cloud Trace** | https://console.cloud.google.com/traces?project=galvanic-pulsar-482815-h0 | Request tracing |
| **Firestore** | https://console.cloud.google.com/firestore?project=galvanic-pulsar-482815-h0 | Database browser |
| **Secret Manager** | https://console.cloud.google.com/security/secret-manager?project=galvanic-pulsar-482815-h0 | Credentials |
| **Cloud Scheduler** | https://console.cloud.google.com/cloudscheduler?project=galvanic-pulsar-482815-h0 | Job scheduling |
| **Artifact Registry** | https://console.cloud.google.com/artifacts?project=galvanic-pulsar-482815-h0 | Container images |

---

## 📱 COMMON API EXAMPLES

### Get Live Prices
```bash
curl -X GET "https://get-live-prices-3acobgd3qa-uc.a.run.app?symbols=NIFTY50,BANKNIFTY"
```

### Get Latest Signals
```bash
curl -X GET "https://get-latest-signals-3acobgd3qa-uc.a.run.app?limit=10&symbol=NIFTY50"
```

### Check Engine Health
```bash
curl -X GET "https://engine-a-3acobgd3qa-uc.a.run.app/health"
curl -X GET "https://engine-b-3acobgd3qa-uc.a.run.app/health"
curl -X GET "https://engine-c-3acobgd3qa-uc.a.run.app/health"
```

### Get Account Data
```bash
curl -X GET "https://fetchaccountdata-3acobgd3qa-uc.a.run.app"
```

### Fetch Portfolio Analysis
```bash
curl -X GET "https://analyzeportfolio-3acobgd3qa-uc.a.run.app"
```

---

## 🔑 CREDENTIALS & SECRETS

All sensitive data stored in **GCP Secret Manager**:

- `dhan-client-id` → Engine services
- `dhan-api-secret` → Engine services
- `dhan-access-token` → Engine services (auto-refreshed)
- `gemini-api-key` → Engine B
- `encryption-key` → All services

**Access:** Cloud Run services only (via Workload Identity)

---

## 🚀 DEPLOYMENT STATUS

✅ All services deployed & operational  
✅ CI/CD pipeline active (GitHub Actions + WIF)  
✅ Health checks passing (60s timeout, non-blocking)  
✅ Firestore database ready  
✅ Cloud Scheduler running (5-min & 15-min jobs)  
✅ Firebase Hosting live  
✅ Secret Manager configured  
✅ Logs & monitoring enabled  

---

## 📞 SUPPORT & MONITORING

### View Real-Time Logs
```bash
# Engine A logs
gcloud logging read "resource.labels.service_name=engine-a" --limit=20 --project=galvanic-pulsar-482815-h0

# Engine B logs
gcloud logging read "resource.labels.service_name=engine-b" --limit=20 --project=galvanic-pulsar-482815-h0

# Engine C logs
gcloud logging read "resource.labels.service_name=engine-c" --limit=20 --project=galvanic-pulsar-482815-h0
```

### Check Service Status
```bash
gcloud run services list --project=galvanic-pulsar-482815-h0 --region=us-central1
```

### Monitor Cloud Scheduler
```bash
gcloud scheduler jobs list --location=us-central1 --project=galvanic-pulsar-482815-h0
```

### Query Firestore
```bash
gcloud firestore collections list --project=galvanic-pulsar-482815-h0
```

---

**Version:** 1.0  
**Status:** 🟢 Production Ready  
**Last Deployed:** January 10, 2025, 2:30 PM IST
