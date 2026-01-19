# Phase 7: Provider Integration Scaffolding

This document outlines the initial scaffolding for integrating Market Data Providers and News Providers. No credentials are stored in the repo; use GCP Secret Manager and environment variables.

## Components

- Market Data Ingestion (Cloud Run): backend/market-data-ingestion
- News Ingestion (Cloud Run): backend/news-ingestion
- Shared Provider Interfaces: backend/shared/providers

## Environment Variables (add to .env or Secret Manager)

- GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0
- PUBSUB_TOPIC_MARKET_DATA_RAW=market-data.raw
- PUBSUB_TOPIC_NEWS_RAW=news.raw
- PROVIDER_DEFAULT=none
- PROVIDER_X_API_KEY=from-secret-manager
- PROVIDER_X_ENDPOINT=https://api.example.com

## Pub/Sub Topics

Create topics for raw ingestion:

- market-data.raw
- news.raw

## Deployment (CLI-first)

```
# Market Data Ingestion
gcloud run deploy market-data-ingestion \
  --source backend/market-data-ingestion \
  --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0,PUBSUB_TOPIC_MARKET_DATA_RAW=market-data.raw

# News Ingestion
gcloud run deploy news-ingestion \
  --source backend/news-ingestion \
  --region us-central1 \
  --project galvanic-pulsar-482815-h0 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0,PUBSUB_TOPIC_NEWS_RAW=news.raw
```

## Verification Checklist

- Health endpoints return status
- Pub/Sub topics exist and receive messages
- Cloud Run logs show published message IDs
- No secrets hardcoded; values sourced from Secret Manager

## Next Steps

- Plug concrete providers once details are available
- Add provider adapters under backend/shared/providers/<provider_name>.py
- Wire fetch jobs (scheduled) to call ingestion services
