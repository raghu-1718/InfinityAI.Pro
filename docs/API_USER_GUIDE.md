# InfinityAI.Pro API - User Guide & Documentation

## Table of Contents
1. [Quick Start](#quick-start)
2. [API Reference](#api-reference)
3. [Authentication](#authentication)
4. [Rate Limiting](#rate-limiting)
5. [Examples](#examples)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Quick Start

### Prerequisites
- API Key (request from admin)
- HTTPS-capable client (curl, Python, JavaScript, etc.)
- Project ID: `galvanic-pulsar-482815-h0`

### Your First Request

```bash
curl -X POST "https://backtest-orchestrator-3acobgd3qa-uc.a.run.app" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": "GOLD",
    "interval": "1d",
    "period": "1y"
  }'
```

**Expected Response** (200 OK):
```json
{
  "status": "success",
  "results": {
    "GOLD": {
      "trades": 1,
      "wins": 1,
      "total_pnl": 1918.20,
      "return_pct": 0.75,
      "sharpe_ratio": 2.11
    }
  }
}
```

---

## API Reference

### Endpoint

```
POST https://backtest-orchestrator-3acobgd3qa-uc.a.run.app
```

### Headers

| Header | Required | Value |
|--------|----------|-------|
| `Authorization` | Yes | `Bearer <API_KEY>` |
| `Content-Type` | Yes | `application/json` |

### Request Body

```json
{
  "symbols": "GOLD",
  "interval": "1d",
  "period": "1y"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbols` | string | Yes | Single symbol or comma-separated: `GOLD`, `NIFTY,BANKNIFTY` |
| `interval` | string | No | `1d` (daily), `1h` (hourly), `15m` (15-min). Default: `1d` |
| `period` | string | No | `6m` (6-month), `1y` (1-year), `3y` (3-year). Default: `1y` |

#### Supported Symbols

```
NIFTY      - Nifty 50 Index
BANKNIFTY  - Bank Nifty Index
FINNIFTY   - Financial Nifty Index
SENSEX     - BSE Sensex
GOLD       - Gold commodity (1 unit = 1 gram)
CRUDEOIL   - Crude Oil commodity (1 unit = 1 barrel)
```

#### Data Availability

| Interval | Coverage | Candles/Year | Notes |
|----------|----------|--------------|-------|
| 1d | 3 years | 252 | Full historical coverage |
| 1h | 6 months | 877 | Past 6 months available |
| 15m | 60 days | Variable | Yahoo Finance limitation |

### Response Format

#### Success (200 OK)

```json
{
  "status": "success",
  "timestamp": "2026-01-10T15:22:04.395201",
  "execution_time_ms": 756,
  "symbols_processed": 1,
  "results": {
    "GOLD": {
      "symbol": "GOLD",
      "interval": "1d",
      "period": "1y",
      "data_points": 254,
      "date_range": {
        "start": "2025-01-09",
        "end": "2026-01-09"
      },
      "trades": 1,
      "wins": 1,
      "losses": 0,
      "total_pnl": 1918.20,
      "total_return_pct": 0.75,
      "win_rate": 100.0,
      "avg_trade_pnl": 1918.20,
      "max_drawdown": 0.0,
      "sharpe_ratio": 2.11,
      "final_capital": 1001918.20
    }
  }
}
```

#### Error (400/401/429/500)

```json
{
  "error": "Invalid symbol",
  "message": "Symbol 'XYZ' not found. Available: NIFTY, BANKNIFTY, ...",
  "status": 400,
  "request_id": "12345-67890-abcde"
}
```

### Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process results |
| 400 | Bad Request | Check parameters |
| 401 | Unauthorized | Verify API key |
| 429 | Rate Limited | Wait and retry (exponential backoff) |
| 500 | Server Error | Retry with backoff |

---

## Authentication

### Getting Your API Key

1. Request API key from admin
2. Store securely (never commit to git)
3. Rotate quarterly for security
4. Report compromised keys immediately

### Using the API Key

#### Option 1: Bearer Token (Recommended)

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" ...
```

#### Option 2: Environment Variable

```bash
export BACKTEST_API_KEY="your-api-key-here"
curl -H "Authorization: Bearer $BACKTEST_API_KEY" ...
```

#### Option 3: Config File

Create `.env.local` (git-ignored):
```
BACKTEST_API_KEY=your-api-key-here
BACKTEST_FUNCTION_URL=https://backtest-orchestrator-3acobgd3qa-uc.a.run.app
```

---

## Rate Limiting

### Limits

- **100 requests per minute** per API key
- **Ban duration:** 5 minutes after exceeding limit
- **Concurrency:** Up to 3 simultaneous requests

### HTTP Response Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1578612000
Retry-After: 45
```

### Handling Rate Limits

#### Client-Side Strategy

```python
import time
from datetime import datetime

class RateLimitedClient:
    def __init__(self):
        self.requests_made = 0
        self.window_start = datetime.now()

    def make_request(self, data):
        # Enforce 100 req/min locally
        if self.requests_made >= 100:
            elapsed = (datetime.now() - self.window_start).total_seconds()
            if elapsed < 60:
                wait_time = 60 - elapsed
                print(f"Waiting {wait_time:.1f}s to avoid rate limit...")
                time.sleep(wait_time)
            self.window_start = datetime.now()
            self.requests_made = 0

        # Make request
        response = self.api_call(data)
        self.requests_made += 1
        return response
```

#### Exponential Backoff

```python
import requests
import time

def backtest_with_backoff(api_key, payload, max_retries=3):
    base_wait = 1  # Start with 1 second

    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=300
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited - exponential backoff
                wait_time = base_wait * (2 ** attempt)
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                raise Exception(f"Error {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            print("Request timeout, retrying...")
            continue

    raise Exception("Max retries exceeded")
```

### Optimization Tips

1. **Batch Requests:** Use comma-separated symbols
   ```json
   {"symbols": "GOLD,CRUDEOIL", "interval": "1d"}
   ```

2. **Cache Results:** Store results locally for repeated requests
   ```python
   cache = {}
   key = f"{symbol}_{interval}_{period}"
   if key in cache:
       return cache[key]
   ```

3. **Adjust Intervals:** Longer intervals (1d vs 1h) process faster
4. **Reduce Periods:** 1y backtest faster than 3y
5. **Monitor Quota:** Track requests in real-time

---

## Examples

### Python Client

```python
import requests
import json

class BacktestClient:
    def __init__(self, api_key, base_url="https://backtest-orchestrator-3acobgd3qa-uc.a.run.app"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def backtest(self, symbols, interval="1d", period="1y"):
        """Execute a backtest"""
        payload = {
            "symbols": symbols,
            "interval": interval,
            "period": period
        }

        response = requests.post(
            self.base_url,
            json=payload,
            headers=self.headers,
            timeout=300
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Error {response.status_code}: {response.text}")

    def backtest_multiple(self, symbols_list):
        """Backtest multiple symbols with batching"""
        results = {}
        for symbols in symbols_list:
            result = self.backtest(symbols)
            results.update(result.get("results", {}))
        return results

# Usage
client = BacktestClient(api_key="YOUR_API_KEY")
result = client.backtest("GOLD", "1d", "1y")
print(json.dumps(result, indent=2))
```

### JavaScript/Node.js

```javascript
class BacktestAPI {
  constructor(apiKey, baseUrl = "https://backtest-orchestrator-3acobgd3qa-uc.a.run.app") {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async backtest(symbols, interval = "1d", period = "1y") {
    const response = await fetch(this.baseUrl, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${this.apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ symbols, interval, period })
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  // Batch multiple requests
  async backtestBatch(symbolsList) {
    const results = {};
    for (const symbols of symbolsList) {
      try {
        const data = await this.backtest(symbols);
        Object.assign(results, data.results);
      } catch (error) {
        console.error(`Error for ${symbols}:`, error);
      }
    }
    return results;
  }
}

// Usage
const client = new BacktestAPI("YOUR_API_KEY");
client.backtest("GOLD", "1d", "1y")
  .then(result => console.log(JSON.stringify(result, null, 2)))
  .catch(error => console.error(error));
```

### cURL

```bash
# Single symbol
curl -X POST "https://backtest-orchestrator-3acobgd3qa-uc.a.run.app" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": "GOLD",
    "interval": "1d",
    "period": "1y"
  }' | jq .

# Multiple symbols
curl -X POST "https://backtest-orchestrator-3acobgd3qa-uc.a.run.app" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": "NIFTY,BANKNIFTY,GOLD,CRUDEOIL",
    "interval": "1d",
    "period": "1y"
  }' | jq '.results | to_entries[] | {symbol: .key, trades: .value.trades, pnl: .value.total_pnl}'
```

---

## Troubleshooting

### 401 Unauthorized

**Cause:** Invalid or missing API key

**Solution:**
```bash
# Verify API key is set
echo $BACKTEST_API_KEY

# Test with curl
curl -H "Authorization: Bearer $BACKTEST_API_KEY" \
  "https://backtest-orchestrator-3acobgd3qa-uc.a.run.app"
```

### 400 Bad Request

**Cause:** Invalid parameters

**Solution:**
```python
# Check parameters
valid_symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "GOLD", "CRUDEOIL"]
valid_intervals = ["1d", "1h", "15m"]
valid_periods = ["6m", "1y", "3y"]

assert symbol in valid_symbols, f"Invalid symbol: {symbol}"
assert interval in valid_intervals, f"Invalid interval: {interval}"
assert period in valid_periods, f"Invalid period: {period}"
```

### 429 Too Many Requests

**Cause:** Rate limit exceeded

**Solution:**
- Wait 300 seconds (5 minutes) before retrying
- Implement exponential backoff
- Batch symbols in single request
- Cache results

### 500 Server Error

**Cause:** Internal server error

**Solution:**
1. Check Cloud Console for error logs
2. Retry with exponential backoff
3. Contact support with request ID
4. Check status page: TBD

### Timeout (30+ seconds)

**Cause:** Large datasets or slow processing

**Solution:**
- Use shorter periods (1y instead of 3y)
- Use longer intervals (1d instead of 1h)
- Backtest single symbol instead of batch
- Increase client timeout to 300 seconds

---

## FAQ

### Q: Can I use the API for live trading?
**A:** No. The API is for **backtesting only**. Never use backtest results directly for live trading decisions.

### Q: What historical data is available?
**A:** Up to 3 years for daily data, 6 months for hourly, 60 days for 15-minute.

### Q: How often is data updated?
**A:** Daily after market close (~4 PM IST).

### Q: Can I export results to CSV?
**A:** The API returns JSON. Parse and convert using Python/JavaScript.

```python
import json
import csv

result = backtest_client.backtest("GOLD")
trades = result["results"]["GOLD"]["trades"]

with open("trades.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=["symbol", "entry_date", "entry_price", "exit_date", "exit_price", "pnl"])
    writer.writeheader()
    for trade in trades:
        writer.writerow(trade)
```

### Q: What's the maximum number of symbols per request?
**A:** Recommended maximum is 10 symbols. Larger batches may timeout.

### Q: Can I get daily updates programmatically?
**A:** Yes, use a scheduled job:

```python
import schedule
import time

def daily_backtest():
    symbols = "NIFTY,BANKNIFTY,GOLD,CRUDEOIL"
    result = client.backtest(symbols)
    save_to_database(result)
    send_email_report(result)

schedule.every().day.at("16:30").do(daily_backtest)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Q: How do I calculate compound annual growth rate (CAGR)?
**A:**
```python
def calculate_cagr(initial_capital, final_capital, years):
    return (pow(final_capital / initial_capital, 1/years) - 1) * 100

initial = 1000000
final = 1001918  # From GOLD backtest
years = 1
cagr = calculate_cagr(initial, final, years)
print(f"CAGR: {cagr:.2f}%")  # 0.19%
```

### Q: Is there a web UI instead of API?
**A:** A dashboard is coming soon. For now, use the API directly.

---

## Support & Resources

- **Documentation:** [GitHub Wiki](https://github.com/raghu-1718/InfinityAI.Pro/wiki)
- **Status:** [Status Page](https://status.infinityai.pro)
- **Issues:** [GitHub Issues](https://github.com/raghu-1718/InfinityAI.Pro/issues)
- **Email:** support@infinityai.pro

---

**Last Updated:** January 10, 2026
**API Version:** 1.0
**Project:** InfinityAI.Pro
**GCP Project:** galvanic-pulsar-482815-h0
