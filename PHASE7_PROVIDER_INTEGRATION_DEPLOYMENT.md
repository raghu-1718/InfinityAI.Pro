# Phase 7 Provider Integration - Deployment & Implementation Guide

## Overview
Phase 7 integrates **7 real-time data and news providers** to replace yfinance as the primary data source. All credentials are managed via GCP Secret Manager; no keys stored in code.

## Providers Integrated

### Market Data Providers (3)
| Provider | Type | Coverage | Rate Limit | Cost | WebSocket |
|----------|------|----------|-----------|------|-----------|
| **Alpha Vantage** | REST API | Stocks, Forex, Crypto, Commodities, Options | 5/min free, 600/min premium | Free tier available | No |
| **MarketStack** | REST API | 170k+ tickers, 50+ countries, EOD + Intraday | 5 req/sec | $9.99/mo | No |
| **Massive** | REST + WebSocket | Stocks, Options, Futures, Indices, Forex | Variable | Freemium | Yes |

### News Providers (3)
| Provider | Type | Coverage | Rate Limit | Cost | Features |
|----------|------|----------|-----------|------|----------|
| **NewsAPI** | REST API | 40k+ sources | 100/day free | Free tier | Trending, Headlines, Search |
| **NewsData.io** | REST API | Global, multi-language | 2k/day free | Free tier | Sentiment, Language detection |
| **NewsAPI.ai** | REST API | Semantic search, Events | 2k tokens/day free | Free tier | Concepts, Events, AI analysis |

### Real-time Platform (Optional)
- **Ably**: Pub/Sub alternative for bridging external feeds into GCP Pub/Sub

---

## Step 1: Set Up Secret Manager

```bash
# Clone the setup script
cd /workspace/InfinityAI.Pro

# Run setup interactively
bash scripts/setup_provider_secrets.sh

# Or create secrets manually:
gcloud secrets create provider-alphavantage-api-key \
  --replication-policy="automatic" \
  --project=galvanic-pulsar-482815-h0

# Verify secrets created
gcloud secrets list --project=galvanic-pulsar-482815-h0 \
  --filter="name:provider-*"
```

---

## Step 2: Create Pub/Sub Topics

```bash
PROJECT_ID="galvanic-pulsar-482815-h0"

# Market data topics
gcloud pubsub topics create market-data.raw --project=$PROJECT_ID
gcloud pubsub topics create market-data.processed --project=$PROJECT_ID
gcloud pubsub topics create market-data.alerts --project=$PROJECT_ID

# News topics
gcloud pubsub topics create news.raw --project=$PROJECT_ID
gcloud pubsub topics create news.processed --project=$PROJECT_ID
gcloud pubsub topics create news.alerts --project=$PROJECT_ID

# Verify
gcloud pubsub topics list --project=$PROJECT_ID --format="table(name)"
```

---

## Step 3: Deploy Ingestion Services

### 3a. Deploy Market Data Ingestion

```bash
# Load env vars from Secret Manager
export PROVIDER_ALPHAVANTAGE_API_KEY=$(gcloud secrets versions access latest \
  --secret=provider-alphavantage-api-key --project=galvanic-pulsar-482815-h0)

export PROVIDER_MARKETSTACK_API_KEY=$(gcloud secrets versions access latest \
  --secret=provider-marketstack-access-key --project=galvanic-pulsar-482815-h0)

# Deploy
gcloud run deploy market-data-ingestion \
  --source backend/market-data-ingestion \
  --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --allow-unauthenticated \
  --timeout 60 \
  --memory 512Mi \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0,\
PUBSUB_TOPIC_MARKET_DATA_RAW=market-data.raw,\
PROVIDER_ALPHAVANTAGE_API_KEY=$PROVIDER_ALPHAVANTAGE_API_KEY,\
PROVIDER_MARKETSTACK_API_KEY=$PROVIDER_MARKETSTACK_API_KEY" \
  --quiet
```

### 3b. Deploy News Ingestion

```bash
export PROVIDER_NEWSAPI_API_KEY=$(gcloud secrets versions access latest \
  --secret=provider-newsapi-api-key --project=galvanic-pulsar-482815-h0)

export PROVIDER_NEWSDATAIO_API_KEY=$(gcloud secrets versions access latest \
  --secret=provider-newsdataio-api-key --project=galvanic-pulsar-482815-h0)

gcloud run deploy news-ingestion \
  --source backend/news-ingestion \
  --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --allow-unauthenticated \
  --timeout 60 \
  --memory 512Mi \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0,\
PUBSUB_TOPIC_NEWS_RAW=news.raw,\
PROVIDER_NEWSAPI_API_KEY=$PROVIDER_NEWSAPI_API_KEY,\
PROVIDER_NEWSDATAIO_API_KEY=$PROVIDER_NEWSDATAIO_API_KEY" \
  --quiet
```

---

## Step 4: Verify Service Health

```bash
# Check Cloud Run services
gcloud run services list --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --format="table(name,status,lastModifiedTime)"

# Test health endpoints
MARKET_URL=$(gcloud run services describe market-data-ingestion \
  --region us-central1 --project galvanic-pulsar-482815-h0 \
  --format='value(status.url)')

NEWS_URL=$(gcloud run services describe news-ingestion \
  --region us-central1 --project galvanic-pulsar-482815-h0 \
  --format='value(status.url)')

curl -s ${MARKET_URL}/health | jq .
curl -s ${NEWS_URL}/health | jq .
```

---

## Step 5: Configure Cloud Scheduler Jobs

### 5a. Market Data Fetch Job (every 5 minutes)

```bash
gcloud scheduler jobs create http market-data-fetch \
  --schedule="*/5 * * * *" \
  --uri="${MARKET_URL}/ingest/quotes" \
  --http-method=POST \
  --headers="Content-Type: application/json" \
  --message-body='{"records":[{"symbol":"AAPL"},{"symbol":"MSFT"}]}' \
  --time-zone="UTC" \
  --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --oidc-service-account-email=cloud-scheduler@galvanic-pulsar-482815-h0.iam.gserviceaccount.com
```

### 5b. News Fetch Job (every hour)

```bash
gcloud scheduler jobs create http news-fetch \
  --schedule="0 * * * *" \
  --uri="${NEWS_URL}/ingest/news" \
  --http-method=POST \
  --headers="Content-Type: application/json" \
  --message-body='{"records":[{"topic":"AAPL"},{"topic":"crypto"}]}' \
  --time-zone="UTC" \
  --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --oidc-service-account-email=cloud-scheduler@galvanic-pulsar-482815-h0.iam.gserviceaccount.com
```

---

## Step 6: Test End-to-End Data Flow

### 6a. Publish Test Market Data

```bash
curl -X POST ${MARKET_URL}/ingest/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "symbol": "AAPL",
        "price": 199.25,
        "timestamp": "2026-01-19T10:00:00Z",
        "source": "test"
      },
      {
        "symbol": "MSFT",
        "price": 425.50,
        "timestamp": "2026-01-19T10:00:00Z",
        "source": "test"
      }
    ]
  }'
```

### 6b. Publish Test News

```bash
curl -X POST ${NEWS_URL}/ingest/news \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "id": "news-1",
        "title": "Apple Earnings Beat",
        "body": "Apple reports strong Q1 earnings...",
        "published_at": "2026-01-19T10:00:00Z",
        "symbols": ["AAPL"],
        "source": "reuters"
      }
    ]
  }'
```

### 6c. Verify Pub/Sub Messages

```bash
# Create temporary subscription
gcloud pubsub subscriptions create market-test-sub \
  --topic=market-data.raw \
  --project galvanic-pulsar-482815-h0

# Pull 5 messages
gcloud pubsub subscriptions pull market-test-sub \
  --limit=5 \
  --auto-ack \
  --format="table(message.data.decode())" \
  --project galvanic-pulsar-482815-h0

# Cleanup
gcloud pubsub subscriptions delete market-test-sub \
  --project galvanic-pulsar-482815-h0
```

---

## Step 7: Monitor & Troubleshoot

### View Cloud Logging

```bash
# Market data service logs
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="market-data-ingestion"' \
  --limit=50 \
  --format=json \
  --project galvanic-pulsar-482815-h0 | jq .

# News ingestion logs
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="news-ingestion"' \
  --limit=50 \
  --format=json \
  --project galvanic-pulsar-482815-h0 | jq .

# Errors only
gcloud logging read 'resource.type="cloud_run_revision" AND severity="ERROR"' \
  --limit=20 \
  --format=json \
  --project galvanic-pulsar-482815-h0 | jq .
```

### Check Pub/Sub Metrics

```bash
gcloud pubsub topics describe market-data.raw \
  --project galvanic-pulsar-482815-h0

gcloud pubsub subscriptions list --project galvanic-pulsar-482815-h0 \
  --format="table(name,topic,ackDeadlineSeconds)"
```

---

## Step 8: Integrate with Engines

### Update Engine-C to consume provider data

Edit `backend/engine-c/src/main.py`:

```python
from backend.shared.providers import AlphaVantageProvider, MarketStackProvider

@app.on_event("startup")
async def startup():
    # Initialize market data providers
    global alpha_vantage_provider
    alpha_vantage_provider = AlphaVantageProvider()
    
    # Start periodic fetch of market data
    asyncio.create_task(periodic_market_data_fetch())

async def periodic_market_data_fetch():
    while True:
        symbols = ["AAPL", "MSFT", "TSLA"]
        quotes = await alpha_vantage_provider.fetch_quotes(symbols)
        # Publish to Pub/Sub for consumption
        await publish_to_pubsub("market-data.processed", quotes)
        await asyncio.sleep(300)  # Every 5 minutes

@app.get("/api/quotes/{symbol}")
async def get_quotes(symbol: str):
    # Query Firestore for latest quotes from providers
    doc = await db.collection("quotes").document(symbol).get()
    return doc.to_dict() if doc.exists else {"error": "Not found"}
```

---

## Deployment Verification Checklist

- [ ] All 7 provider API keys stored in Secret Manager
- [ ] Pub/Sub topics created and verified
- [ ] market-data-ingestion service READY
- [ ] news-ingestion service READY
- [ ] Health endpoints respond 200 OK
- [ ] Cloud Scheduler jobs created and running
- [ ] Test messages published and received via Pub/Sub
- [ ] Cloud Logging shows successful data ingestion
- [ ] Firestore rules allow Pub/Sub writes to data collections
- [ ] Monitoring alerts configured for failures
- [ ] Engines configured to consume from Pub/Sub topics

---

## Rates & Quotas Reference

| Provider | Free Tier | Cost to Scale |
|----------|-----------|--------------|
| Alpha Vantage | 5 req/min | $50-500/mo premium |
| MarketStack | 100/day | $9.99+/mo |
| Massive | Freemium | Variable |
| NewsAPI | 100/day | $49/mo |
| NewsData.io | 2000/day | Paid plans |
| NewsAPI.ai | 2000 tokens/day | Paid plans |

---

## Next Steps (Phase 8+)
1. Wire Pub/Sub consumers in each engine
2. Add provider failover logic (try primary → secondary → tertiary)
3. Implement data quality checks and schema validation
4. Create admin dashboard to monitor provider health
5. Add user preferences for data sources
6. Set up alerting for provider outages
