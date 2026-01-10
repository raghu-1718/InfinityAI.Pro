# Cloud API Quick Reference

## Backtest Orchestrator Endpoint

**URL:** `https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator`

---

## API Examples

### 1. Single Symbol Backtest (GOLD)
```bash
curl -X POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": "GOLD",
    "interval": "1d",
    "period": "1y"
  }'
```

**Expected Response Time:** 0.76 seconds

**Sample Output:**
```json
{
  "status": "success",
  "timestamp": "2026-01-10T10:02:23.690843",
  "results": {
    "GOLD": {
      "trades": 1,
      "wins": 1,
      "total_pnl": 1918.20,
      "return_pct": 0.75
    }
  }
}
```

---

### 2. Multi-Symbol Batch
```bash
curl -X POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": "NIFTY,BANKNIFTY,FINNIFTY,SENSEX,GOLD,CRUDEOIL",
    "interval": "1d",
    "period": "1y"
  }'
```

**Expected Response Time:** 0.68 seconds
**Expected Trades:** 2 (GOLD: +₹1,918, CRUDEOIL: -₹357)

---

### 3. Hourly Data Analysis
```bash
curl -X POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": "NIFTY",
    "interval": "1h",
    "period": "6m"
  }'
```

**Expected Response Time:** 0.50 seconds
**Note:** 877 hourly candles, fewer trading signals

---

### 4. Different Time Period
```bash
curl -X POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": "GOLD",
    "interval": "1d",
    "period": "3y"
  }'
```

**Expected Response Time:** 1.2-1.5 seconds (larger dataset)

---

## Parameters Reference

### symbols
- **Type:** String (comma-separated list)
- **Options:** NIFTY, BANKNIFTY, FINNIFTY, SENSEX, GOLD, CRUDEOIL
- **Example:** `"GOLD"` or `"NIFTY,GOLD,CRUDEOIL"`

### interval
- **Type:** String
- **Options:**
  - `"1d"` → Daily data (252 candles/year)
  - `"1h"` → Hourly data (877 candles/6m)
  - `"15m"` → 15-minute data (limited to 60-day window)

### period
- **Type:** String
- **Options:**
  - `"6m"` → 6 months
  - `"1y"` → 1 year (most common)
  - `"3y"` → 3 years

---

## Response Schema

```json
{
  "status": "success|error",
  "timestamp": "ISO-8601 datetime",
  "config": {
    "interval": "1d|1h|15m",
    "period": "6m|1y|3y"
  },
  "results": {
    "SYMBOL": {
      "trades": integer,
      "wins": integer,
      "losses": integer,
      "total_pnl": float,
      "final_equity": float,
      "return_pct": float,
      "sharpe_ratio": float
    }
  }
}
```

---

## Performance Metrics

| Request Type | Latency | Status |
|--------------|---------|--------|
| Single Symbol | 0.76s | ✅ |
| 4 Symbols | 0.68s | ✅ |
| Hourly Data | 0.50s | ✅ |
| 3 Concurrent | 8.2s | ✅ |

---

## Supported Symbols

| Symbol | Type | Status |
|--------|------|--------|
| NIFTY | Index | ✅ Available |
| BANKNIFTY | Index | ✅ Available |
| FINNIFTY | Index | ✅ Available |
| SENSEX | Index | ✅ Available |
| GOLD | Commodity | ✅ Available |
| CRUDEOIL | Commodity | ✅ Available |

---

## Common Use Cases

### Daily Analysis (1 year)
```bash
curl -X POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  -H "Content-Type: application/json" \
  -d '{"symbols":"NIFTY,BANKNIFTY","interval":"1d","period":"1y"}'
```

### Intraday Analysis (6 months hourly)
```bash
curl -X POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  -H "Content-Type: application/json" \
  -d '{"symbols":"NIFTY","interval":"1h","period":"6m"}'
```

### Commodity Trading (3 years)
```bash
curl -X POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  -H "Content-Type: application/json" \
  -d '{"symbols":"GOLD,CRUDEOIL","interval":"1d","period":"3y"}'
```

### Multi-Asset Allocation
```bash
curl -X POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  -H "Content-Type: application/json" \
  -d '{"symbols":"NIFTY,BANKNIFTY,FINNIFTY,SENSEX,GOLD,CRUDEOIL","interval":"1d","period":"1y"}'
```

---

## Error Handling

### Invalid Symbol
```json
{
  "status": "error",
  "message": "Symbol not found or data unavailable"
}
```

### Timeout
**Response Time:** 300+ seconds
**Action:** Request will return 503 Service Unavailable

### Malformed JSON
**HTTP Status:** 400 Bad Request
**Action:** Verify JSON syntax and parameters

---

## System Status

**Last Verified:** January 10, 2026
**Status:** ✅ OPERATIONAL
**Uptime:** 100%
**Available:** 24/7

---

## Support & Monitoring

- **Cloud Function:** backtest-orchestrator (Gen2)
- **Region:** us-central1
- **Data Source:** Yahoo Finance via GCS
- **Max Timeout:** 300 seconds
- **Max Concurrent:** 3 requests

---

## Integration Examples

### Python
```python
import requests
import json

url = "https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator"
payload = {
    "symbols": "GOLD",
    "interval": "1d",
    "period": "1y"
}

response = requests.post(url, json=payload, timeout=60)
result = response.json()
print(f"Trades: {result['results']['GOLD']['trades']}")
print(f"P&L: ₹{result['results']['GOLD']['total_pnl']}")
```

### JavaScript
```javascript
const url = "https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator";
const payload = {
  symbols: "GOLD",
  interval: "1d",
  period: "1y"
};

fetch(url, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload)
})
.then(r => r.json())
.then(data => console.log(`Trades: ${data.results.GOLD.trades}`));
```

---

**API Version:** 1.0
**Last Updated:** January 10, 2026
