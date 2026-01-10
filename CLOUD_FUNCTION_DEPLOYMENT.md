# Cloud Function Deployment Guide

## Quick Deploy Command

```bash
# Deploy to GCP
gcloud functions deploy backtest-orchestrator \
  --project=galvanic-pulsar-482815-h0 \
  --source=./backend/shared/cloud_functions \
  --runtime=python312 \
  --trigger-http \
  --entry-point=orchestrate_backtest \
  --timeout=3600 \
  --memory=2GB \
  --env-vars-file=./config/env/cloud-function.env
```

## Test Deploy

```bash
# Dry-run to check for errors
gcloud functions deploy backtest-orchestrator \
  --project=galvanic-pulsar-482815-h0 \
  --dry-run \
  --source=./backend/shared/cloud_functions \
  --runtime=python312 \
  --trigger-http
```

## Function Status Check

```bash
# Check if deployed
gcloud functions describe backtest-orchestrator \
  --project=galvanic-pulsar-482815-h0 \
  --region=us-central1

# View logs
gcloud functions logs read backtest-orchestrator \
  --project=galvanic-pulsar-482815-h0 \
  --limit=50
```

## Manual Trigger (Testing)

```bash
# Test HTTP trigger
curl -X POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["NIFTY", "BANKNIFTY", "FINNIFTY"],
    "periods": ["6m", "1y"],
    "intervals": ["1d", "1h"]
  }'
```

## Scheduler Setup

```bash
# Create daily backtest job (6 PM IST = 12:30 PM UTC)
gcloud scheduler jobs create http daily-backtest \
  --project=galvanic-pulsar-482815-h0 \
  --schedule="30 12 * * *" \
  --location=us-central1 \
  --http-method=POST \
  --uri=https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  --message-body='{"symbols": ["NIFTY", "BANKNIFTY", "FINNIFTY"]}' \
  --oidc-service-account-email=cloud-scheduler@galvanic-pulsar-482815-h0.iam.gserviceaccount.com

# Test scheduler job
gcloud scheduler jobs run daily-backtest --location=us-central1

# View job execution history
gcloud scheduler jobs describe daily-backtest --location=us-central1
```

## IAM Permissions Required

```bash
# Grant Cloud Function service account permissions
gcloud projects add-iam-policy-binding galvanic-pulsar-482815-h0 \
  --member=serviceAccount:cloud-functions@galvanic-pulsar-482815-h0.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin

gcloud projects add-iam-policy-binding galvanic-pulsar-482815-h0 \
  --member=serviceAccount:cloud-functions@galvanic-pulsar-482815-h0.iam.gserviceaccount.com \
  --role=roles/firestore.user

# Grant Scheduler permission to invoke Cloud Function
gcloud functions add-iam-policy-binding backtest-orchestrator \
  --region=us-central1 \
  --member=serviceAccount:cloud-scheduler@galvanic-pulsar-482815-h0.iam.gserviceaccount.com \
  --role=roles/cloudfunctions.invoker
```

## Environment Variables

**File:** `config/env/cloud-function.env`

```env
GCP_PROJECT_ID=galvanic-pulsar-482815-h0
FIRESTORE_DATABASE=galvanic-pulsar-482815-h0
GCS_BUCKET=gs://infinityai-backtesting-data
DHAN_API_TIMEOUT=30
BACKTEST_TIMEOUT=3600
LOG_LEVEL=INFO
```

## Monitoring

### View Metrics

```bash
# CPU usage
gcloud monitoring timeseries list \
  --filter 'metric.type = "cloudfunctions.googleapis.com/function/execution_times"' \
  --interval-start-time 2024-01-10T00:00:00Z

# Errors
gcloud logging read \
  "resource.type=cloud_function AND resource.labels.function_name=backtest-orchestrator AND severity=ERROR" \
  --limit=100
```

### Create Alert

```bash
# Alert if function fails
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Backtest Function Errors" \
  --condition-display-name="High error rate" \
  --condition-expression='resource.type="cloud_function" AND metric.type="cloudfunctions.googleapis.com/function/execution_count" AND metadata.user_labels.function_name="backtest-orchestrator"'
```

## Cleanup

```bash
# Delete function
gcloud functions delete backtest-orchestrator --region=us-central1

# Delete scheduler job
gcloud scheduler jobs delete daily-backtest --location=us-central1

# Delete results bucket
gsutil -m rm -r gs://infinityai-backtesting-data
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Function timeout** | Increase `--timeout` to 3600s, optimize data loading |
| **Memory exceeded** | Increase `--memory` to 4GB, batch process data |
| **Firestore quota** | Reduce backtest frequency or batch writes |
| **Dhan API rate limit** | Add delay between symbol fetches (500ms) |
| **Permissions denied** | Run `gcloud auth application-default login` |

## Status Dashboard URL

After deployment, view metrics:
```
https://console.cloud.google.com/functions/details/us-central1/backtest-orchestrator?project=galvanic-pulsar-482815-h0
```

---

**Last Updated:** 2026-01-10
**Version:** 1.0.0
