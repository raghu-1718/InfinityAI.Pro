# Trading Signals Cloud Functions

This directory contains the Cloud Functions for trading signal generation and retrieval.

## Functions

### `detect_momentum_signals`

- **Purpose:** Generates trading signals using RSI and MACD indicators
- **Trigger:** HTTP
- **Symbols:** NIFTY, BANKNIFTY, FINNIFTY, SENSEX, GOLD, CRUDEOIL
- **Output:** Stores signals in Firestore `trading_signals` collection and publishes to Pub/Sub

### `get_latest_signals`

- **Purpose:** Retrieves recent trading signals from Firestore
- **Trigger:** HTTP
- **Parameters:**
  - `hours`: Lookback period (default: 24)
  - `limit`: Max signals to return (default: 20)

## Deployment

Deploy using GitHub Actions workflow or manually:

```bash
# Deploy detect-momentum-signals
gcloud functions deploy detect-momentum-signals \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=detect_momentum_signals \
  --trigger-http \
  --allow-unauthenticated

# Deploy get-latest-signals
gcloud functions deploy get-latest-signals \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=get_latest_signals \
  --trigger-http \
  --allow-unauthenticated
```

## Environment Variables

None required - uses default GCP project credentials.
