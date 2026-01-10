# ⚡ Quick Start Guide: Execute Backtesting Pipeline Now

**Status:** ✅ All infrastructure ready. Choose your next step below.

---

## 🎯 Option 1: Ingest Real Dhan Data (Recommended First Step)

### Command:
```bash
cd c:\workspace\InfinityAI.Pro
python tools/ingest_dhan_historical.py \
  --credentials-user-id 1101302170 \
  --symbols NIFTY BANKNIFTY FINNIFTY SENSEX GOLD CRUDEOIL \
  --intervals 1d 1h 15m \
  --periods 6m 1y 3y \
  --bucket gs://infinityai-backtesting-data
```

### What It Does:
- ✅ Loads Dhan credentials from Firestore (user 1101302170)
- ✅ Fetches 54 dataset combinations from Dhan API
- ✅ Uploads OHLCV data to Cloud Storage
- ✅ Generates metadata tracking

### Timeline:
- **Duration:** 3-5 minutes
- **Output:** gs://infinityai-backtesting-data/data/{SYMBOL}/{INTERVAL}/{PERIOD}.csv
- **Logs:** Cloud Storage metadata in /metadata/ folder

### Success Indicators:
- ✅ No authentication errors
- ✅ All 54 files uploaded to GCS
- ✅ Metadata JSON created
- ✅ No rate-limit errors

---

## 🎯 Option 2: Run Backtests on Real Data

### Prerequisites:
- ✅ Complete Option 1 first (data ingestion)
- ✅ Real data in gs://infinityai-backtesting-data/

### Command:
```bash
cd c:\workspace\InfinityAI.Pro
python backend/backtester/engine.py \
  --symbols NIFTY BANKNIFTY FINNIFTY \
  --data-source gs://infinityai-backtesting-data \
  --strategies ma_crossover engine_b combined
```

### What It Does:
- ✅ Loads real data from Cloud Storage
- ✅ Runs 3 strategy modes per symbol
- ✅ Calculates all performance metrics
- ✅ Saves results to local JSON + uploads to GCS

### Timeline:
- **Duration:** 10-15 seconds per symbol
- **Output:** data/results/{SYMBOL}_backtest_{timestamp}.json
- **Metrics:** Sharpe, Sortino, drawdown, win rate, profit factor

### Strategy Modes:
1. **MA Crossover** - Baseline 20/50 moving average crossover
2. **Engine-B Signals** - Pure ML ensemble signals
3. **Combined** - MA + Signals + Engine-A risk sizing

---

## 🎯 Option 3: Deploy Cloud Function

### Prerequisites:
- ✅ Have gcloud CLI installed
- ✅ Authenticated with `gcloud auth application-default login`
- ✅ Project: galvanic-pulsar-482815-h0

### Command:
```bash
gcloud functions deploy backtest-orchestrator \
  --project=galvanic-pulsar-482815-h0 \
  --source=./backend/shared/cloud_functions \
  --runtime=python312 \
  --trigger-http \
  --entry-point=orchestrate_backtest \
  --timeout=3600 \
  --memory=2GB \
  --region=us-central1
```

### What It Does:
- ✅ Deploys backtest orchestrator as Cloud Function
- ✅ Makes it callable via HTTP endpoint
- ✅ Sets up 5-stage automated pipeline
- ✅ Enables Cloud Scheduler integration

### Timeline:
- **Duration:** 2-3 minutes
- **Endpoint:** https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator

### Verify Deployment:
```bash
gcloud functions describe backtest-orchestrator \
  --project=galvanic-pulsar-482815-h0 \
  --region=us-central1
```

---

## 🎯 Option 4: Configure Daily Automation (Cloud Scheduler)

### Prerequisites:
- ✅ Cloud Function deployed (Option 3)
- ✅ Cloud Scheduler API enabled

### Command:
```bash
gcloud scheduler jobs create http daily-backtest \
  --project=galvanic-pulsar-482815-h0 \
  --schedule="30 12 * * *" \
  --location=us-central1 \
  --http-method=POST \
  --uri=https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  --message-body='{"symbols": ["NIFTY", "BANKNIFTY", "FINNIFTY"]}' \
  --oidc-service-account-email=cloud-scheduler@galvanic-pulsar-482815-h0.iam.gserviceaccount.com
```

### What It Does:
- ✅ Creates daily scheduled job
- ✅ Runs at 18:00 IST (12:30 UTC)
- ✅ Automatically triggers backtest orchestrator
- ✅ Persists results to Firestore + Cloud Storage

### Timeline:
- **Duration:** 1-2 minutes to create
- **Frequency:** Daily at 18:00 IST

### Test the Job:
```bash
gcloud scheduler jobs run daily-backtest --location=us-central1
```

---

## 📊 Recommended Execution Sequence

### For Quick Validation:
```
1. ✅ Done: Verify infrastructure (all 15 Cloud Run services live)
2. ✅ Done: Validate backtest engine (sample data tests passed)
3. → NEXT: Execute Option 1 (Ingest Dhan data)
4. → THEN: Execute Option 2 (Run backtests)
5. → FINALLY: Execute Option 3 & 4 (Deploy cloud infrastructure)
```

### Estimated Total Time:
- Ingest data: 3-5 minutes
- Run backtests: 15 seconds
- Deploy function: 2-3 minutes
- **Total: ~10 minutes to fully operational**

---

## 🔍 Monitoring & Verification

### View Backtest Results:
```bash
# List results in local filesystem
Get-ChildItem -Path "data/results/" -Filter "*.json"

# View specific result
Get-Content "data/results/NIFTY_backtest_*.json" | ConvertFrom-Json
```

### Check Cloud Storage:
```bash
# List ingested data
gsutil ls gs://infinityai-backtesting-data/data/

# List backtest results
gsutil ls gs://infinityai-backtesting-data/results/
```

### Monitor Cloud Function:
```bash
# View function logs
gcloud functions logs read backtest-orchestrator \
  --project=galvanic-pulsar-482815-h0 \
  --limit=50

# Monitor metrics
gcloud monitoring time-series list \
  --filter='metric.type = "cloudfunctions.googleapis.com/function/execution_times"'
```

---

## ⚠️ Troubleshooting

### Issue: "Missing credentials"
```bash
# Verify Dhan credentials are stored in Firestore
# Collection: user_credentials
# Document: 1101302170
# Fields: access_token, client_id
```

### Issue: "Dhan API rate limit exceeded"
```bash
# Reduce number of symbols or use longer time periods
# Or wait 5-10 minutes for rate limit reset
```

### Issue: "Cloud Function timeout"
```bash
# Increase timeout from 3600 to 7200 seconds
# Or batch process symbols separately
```

### Issue: "Firestore quota exceeded"
```bash
# Use bulk write optimization
# Or adjust batch size in orchestrator code
```

---

## 📚 Reference Documents

| Document | Purpose |
|----------|---------|
| [BACKTEST_PRODUCTION_STATUS.md](BACKTEST_PRODUCTION_STATUS.md) | Complete project status |
| [BACKTEST_RESULTS_ANALYSIS.md](BACKTEST_RESULTS_ANALYSIS.md) | Performance analysis |
| [CLOUD_FUNCTION_DEPLOYMENT.md](CLOUD_FUNCTION_DEPLOYMENT.md) | Detailed deployment guide |
| [BACKTESTING_GUIDE.md](BACKTESTING_GUIDE.md) | Architecture & setup |

---

## ✅ Success Criteria

After executing all 4 options, you should have:

- ✅ 54 datasets in Cloud Storage (NIFTY, BANKNIFTY, FINNIFTY + others)
- ✅ Backtest results showing performance metrics
- ✅ Cloud Function deployed and callable
- ✅ Daily automated backtests scheduled
- ✅ Results persisting to Firestore + Cloud Storage

---

## 🚀 What's Next After Backtesting

1. **Monitor daily results** in Firestore backtest_results collection
2. **Compare strategy performance** (MA vs Engine-B vs Combined)
3. **Validate on extended data** (6 months to 3 years)
4. **Paper trade validation** (Dhan paper trading account)
5. **Live trading** with minimal position size

---

## 📞 Support

**Project:** InfinityAI.Pro
**Repository:** https://github.com/raghu-1718/InfinityAI.Pro
**GCP Project:** galvanic-pulsar-482815-h0
**Status:** ✅ Production Ready

---

**Last Updated:** 2026-01-10 14:20 UTC
**Version:** 1.0.0
**Status:** Ready to Execute
