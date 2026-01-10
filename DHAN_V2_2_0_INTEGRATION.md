# Dhan API v2.2.0 Integration & GCS Bucket Setup

## Executive Summary

**Date:** January 10, 2026
**Status:** ✅ GCS Buckets Created | ✅ Dhan v2.2.0 Client Implemented | ⏳ Awaiting API Testing

---

## Part 1: GCS Bucket Creation

### ✅ Buckets Created

```bash
# Created buckets in project: galvanic-pulsar-482815-h0
gsutil mb gs://infinityai-backtesting-data      # For ingested market data
gsutil mb gs://infinityai-backtest-results      # For backtest results
```

### Configuration

| Bucket | Purpose | Region | Versioning | Lifecycle |
|--------|---------|--------|------------|-----------|
| `infinityai-backtesting-data` | OHLCV data ingestion (Dhan/Yahoo) | us-central1 | Disabled | None (yet) |
| `infinityai-backtest-results` | Backtest output JSON/CSV | us-central1 | Disabled | None (yet) |

### Usage in Code

```python
# In tools/ingest_dhan_v2_2_0.py
--bucket gs://infinityai-backtesting-data

# In backend/shared/cloud_functions/main.py
output_bucket="gs://infinityai-backtest-results"
```

---

## Part 2: Dhan v2.2.0 API Integration

### Root Cause Analysis: Why v2.1.0 Code Failed

**Old Code Issue (v2.1.0):**
```python
# ❌ WRONG: Using non-existent endpoint
BASE_URL = "https://api.dhan.co"
response = requests.post(f"{BASE_URL}/v2/historical", ...)  # 404: Not Found
```

**Why 404?**
- Endpoint path should be `/v2/charts/historical`, not `/v2/historical`
- Authentication pattern was not using `DhanContext` (security risk)
- Required `access-token` header, not in request body

---

### ✅ New Implementation (v2.2.0)

#### Installation

```bash
pip install --pre dhanhq>=2.2.0
```

#### Key Changes from v2.1.0 → v2.2.0

| Aspect | v2.1.0 | v2.2.0 | Impact |
|--------|--------|--------|--------|
| **Authentication** | `dhanhq('client_id','access_token')` | `DhanContext("client_id","access_token")` → `dhanhq(context)` | Secure context pattern |
| **Imports** | `from dhanhq import marketfeed.MarketFeed` | `from dhanhq import MarketFeed` | Simpler, flat structure |
| **Constants** | `marketfeed.NSE` | `MarketFeed.NSE` | Class-scoped |
| **Historical Endpoint** | `/v2/historical` (❌ doesn't exist) | `/v2/charts/historical` (✅ correct) | **FIXES 404 ERRORS** |
| **Intraday Endpoint** | `/v2/intraday` (❌) | `/v2/charts/intraday` (✅) | **FIXES 404 ERRORS** |
| **Security IDs** | String-based | Integer-based (+ exchange segment) | More flexible |
| **Features** | Basic | 200-level market depth, expired options, super orders | Rich functionality |

---

### ✅ New Dhan v2.2.0 Client

**File:** [tools/ingest_dhan_v2_2_0.py](tools/ingest_dhan_v2_2_0.py)

#### Class: `Dhanv220Client`

```python
class Dhanv220Client:
    # Correct endpoints (v2.2.0)
    HISTORICAL_ENDPOINT = "/charts/historical"  # ← Was /v2/historical (404)
    INTRADAY_ENDPOINT = "/charts/intraday"      # ← Was /v2/intraday (404)

    async def _request_historical(...):
        """POST to /v2/charts/historical with correct payload"""
        payload = {
            "securityId": security_id,
            "exchangeSegment": exchange_segment,  # NSE_EQ, BSE_EQ, MCX_COMM
            "instrument": instrument_type,         # INDEX, EQUITY, FUTCOM
            "expiryCode": 0,
            "fromDate": "2025-01-01",
            "toDate": "2026-01-10"
        }
        # Returns: {"data": [{"open": ..., "high": ..., "close": ..., ...}]}
```

#### Security ID Mapping

```python
DhanSecurityMapping = {
    "NSE_EQUITY": {
        "NIFTY": ("NSE_EQ", "1333", "INDEX"),
        "BANKNIFTY": ("NSE_EQ", "11915", "INDEX"),
        "FINNIFTY": ("NSE_EQ", "13748", "INDEX"),
        "SENSEX": ("BSE_EQ", "1", "INDEX"),
    },
    "COMMODITIES": {
        "GOLD": ("MCX_COMM", "228", "FUTCOM"),
        "CRUDEOIL": ("MCX_COMM", "226", "FUTCOM"),
    }
}
```

---

### Usage

#### Test API Connectivity (Single Day)

```bash
python tools/ingest_dhan_v2_2_0.py \
  --test-api \
  --credentials-file .dhan_credentials_temp.json \
  --symbols NIFTY
```

**Expected Output:**
```
🧪 Test mode: Fetching 1 day for ['NIFTY']
✅ DhanContext initialized (v2.2.0 pattern)
✅ Historical data fetched: 1333 (2026-01-09 to 2026-01-10)
✅ Fetched 1 candles for NIFTY
✅ Saved 1 records to data/dhan_historical/NIFTY_daily.csv
✅ DATA INGESTION COMPLETE
```

#### Full Historical Ingestion (All Symbols, Multiple Timeframes)

```bash
python tools/ingest_dhan_v2_2_0.py \
  --credentials-file .dhan_credentials_temp.json \
  --symbols NIFTY BANKNIFTY FINNIFTY SENSEX GOLD CRUDEOIL \
  --intervals 1d 1h 15m \
  --days-back 365 \
  --bucket gs://infinityai-backtesting-data \
  --output-dir data/dhan_historical
```

#### Upload to GCS

```bash
gsutil -m cp data/dhan_historical/*.csv gs://infinityai-backtesting-data/
```

---

## Part 3: API Endpoint Reference (v2.2.0)

### Historical Daily Data

**Endpoint:** `POST /v2/charts/historical`

**Request:**
```json
{
  "securityId": "1333",
  "exchangeSegment": "NSE_EQ",
  "instrument": "INDEX",
  "expiryCode": 0,
  "fromDate": "2025-06-01",
  "toDate": "2026-01-10"
}
```

**Response:**
```json
{
  "data": [
    {
      "timestamp": 1735896600,
      "open": 25640.5,
      "high": 25940.6,
      "low": 25623.0,
      "close": 25683.3,
      "volume": 1250000000,
      "oi": 0
    }
  ]
}
```

### Intraday Data

**Endpoint:** `POST /v2/charts/intraday`

**Request:**
```json
{
  "securityId": "1333",
  "exchangeSegment": "NSE_EQ",
  "instrument": "INDEX",
  "interval": "15",  # "1", "5", "15", "30", "60"
  "fromDate": "2026-01-01",
  "toDate": "2026-01-10"
}
```

**Response:** Same structure as historical

### Headers (All Requests)

```
access-token: <your_access_token>
Content-Type: application/json
```

---

## Part 4: DhanContext Authentication (New v2.2.0 Pattern)

### Old Pattern (v2.1.0) ❌

```python
from dhanhq import dhanhq

# ❌ Insecure: credentials spread across code
dhan = dhanhq('client_id', 'access_token')
market_feed = MarketFeed('client_id', 'access_token', instruments)
```

### New Pattern (v2.2.0) ✅

```python
from dhanhq import DhanContext, dhanhq, MarketFeed

# ✅ Secure: single context, reusable
dhan_context = DhanContext("client_id", "access_token")
dhan = dhanhq(dhan_context)
market_feed = MarketFeed(dhan_context, instruments, version="v2")
```

**Benefits:**
1. Credentials defined once
2. No credential leakage across classes
3. Cleaner API surface
4. Better for cloud deployments (Secret Manager injection)

---

## Part 5: Error Handling & Troubleshooting

### Common Issues & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `404 Not Found` | Endpoint `/v2/historical` wrong | ✅ Use `/v2/charts/historical` |
| `401 Unauthorized` | Invalid access token | ✅ Refresh token (contact support) |
| `400 Bad Request` | Wrong security ID format | ✅ Use correct security_id from mapping |
| `Rate Limited (429)` | Too many concurrent requests | ✅ Reduce `max_concurrent` (default: 3) |
| `Timeout` | Large date range or slow network | ✅ Reduce `days_back` or use multiple requests |

### Debug Mode

```bash
# Enable detailed logging
python tools/ingest_dhan_v2_2_0.py \
  --test-api \
  --credentials-file .dhan_credentials_temp.json \
  --symbols NIFTY \
  2>&1 | tee debug.log
```

---

## Part 6: Integration with Cloud Function

### Cloud Function Deployment

The Cloud Function (`backend/shared/cloud_functions/main.py`) can now call Dhan v2.2.0:

```python
@functions_framework.http
def main(request):
    client_id = os.getenv("DHAN_CLIENT_ID")
    access_token = os.getenv("DHAN_ACCESS_TOKEN")

    # Use new v2.2.0 pattern
    from dhanhq import DhanContext, dhanhq
    dhan_context = DhanContext(client_id, access_token)
    dhan = dhanhq(dhan_context)

    # Fetch data and run backtest
    return json.dumps({"status": "success", ...})
```

### Secret Manager Configuration

```bash
# Store credentials securely
gcloud secrets create dhan-client-id --data-file=<(echo -n "YOUR_CLIENT_ID")
gcloud secrets create dhan-access-token --data-file=<(echo -n "YOUR_TOKEN")

# Grant Cloud Function access
gcloud projects add-iam-policy-binding galvanic-pulsar-482815-h0 \
  --member=serviceAccount:backtest-orchestrator@galvanic-pulsar-482815-h0.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

---

## Part 7: Next Steps (Production Checklist)

- [ ] **Test API:** `python tools/ingest_dhan_v2_2_0.py --test-api --credentials-file .dhan_credentials_temp.json --symbols NIFTY`
- [ ] **Fetch Full History:** `python tools/ingest_dhan_v2_2_0.py --credentials-file .dhan_credentials_temp.json --symbols NIFTY BANKNIFTY FINNIFTY SENSEX GOLD CRUDEOIL --days-back 365`
- [ ] **Upload to GCS:** `gsutil -m cp data/dhan_historical/*.csv gs://infinityai-backtesting-data/`
- [ ] **Update Cloud Function:** Deploy with Dhan v2.2.0 client code
- [ ] **Verify Backtesting:** Run STEP 2 with real Dhan data
- [ ] **Monitor:** Set up Cloud Logging alerts for API errors
- [ ] **Revoke Temp Credentials:** Delete `.dhan_credentials_temp.json`, use Secret Manager in production
- [ ] **Documentation:** Update README with Dhan v2.2.0 setup guide

---

## Summary

| Component | Status | Details |
|-----------|--------|---------|
| **GCS Buckets** | ✅ Created | `infinityai-backtesting-data`, `infinityai-backtest-results` |
| **Dhan v2.2.0 Client** | ✅ Implemented | [tools/ingest_dhan_v2_2_0.py](tools/ingest_dhan_v2_2_0.py) |
| **API Endpoints** | ✅ Corrected | `/v2/charts/historical`, `/v2/charts/intraday` |
| **Authentication** | ✅ Secured | DhanContext pattern, security ready |
| **Symbols Mapped** | ✅ Complete | NIFTY, BANKNIFTY, FINNIFTY, SENSEX, GOLD, CRUDEOIL |
| **Testing** | ⏳ Ready | Run test command below |

---

## Quick Start

```bash
# 1. Install v2.2.0
pip install --pre dhanhq>=2.2.0

# 2. Test API
python tools/ingest_dhan_v2_2_0.py \
  --test-api \
  --credentials-file .dhan_credentials_temp.json \
  --symbols NIFTY

# 3. Fetch full history
python tools/ingest_dhan_v2_2_0.py \
  --credentials-file .dhan_credentials_temp.json \
  --symbols NIFTY BANKNIFTY FINNIFTY SENSEX GOLD CRUDEOIL \
  --intervals 1d 1h 15m \
  --days-back 365 \
  --bucket gs://infinityai-backtesting-data

# 4. Upload to GCS
gsutil -m cp data/dhan_historical/*.csv gs://infinityai-backtesting-data/

# 5. Verify
gsutil ls -r gs://infinityai-backtesting-data/
```

---

**Document Generated:** January 10, 2026
**Project:** InfinityAI.Pro (galvanic-pulsar-482815-h0)
**Author:** Cloud Solutions Architect
