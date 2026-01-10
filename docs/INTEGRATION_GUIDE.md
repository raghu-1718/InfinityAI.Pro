# InfinityAI.Pro API - Integration Guide

## Quick Links
- [User Guide](./API_USER_GUIDE.md)
- [Monitoring Guide](../infra/MONITORING_GUIDE.md)
- [Rate Limiting Guide](../infra/RATE_LIMITING_GUIDE.md)

---

## Integration Patterns

### Pattern 1: Batch Processing System

Perfect for processing multiple symbols overnight.

```python
#!/usr/bin/env python3
"""
Batch backtest processor for daily runs
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict
import requests
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BatchBacktestProcessor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = os.getenv(
            "BACKTEST_FUNCTION_URL",
            "https://backtest-orchestrator-3acobgd3qa-uc.a.run.app"
        )
        self.results = {}
        self.errors = {}

    def process_symbols(self, symbols: List[str], interval: str = "1d", period: str = "1y"):
        """Process multiple symbols"""
        logger.info(f"Starting batch processing: {len(symbols)} symbols")

        # Batch symbols (max 10 per request for performance)
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            symbols_str = ",".join(batch)

            try:
                logger.info(f"Processing batch {i//batch_size + 1}: {symbols_str}")
                result = self._backtest(symbols_str, interval, period)
                self.results.update(result.get("results", {}))
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Batch failed: {str(e)}")
                for sym in batch:
                    self.errors[sym] = str(e)

        return self.results

    def _backtest(self, symbols: str, interval: str, period: str):
        """Execute single backtest request"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "symbols": symbols,
            "interval": interval,
            "period": period
        }

        response = requests.post(
            self.base_url,
            json=payload,
            headers=headers,
            timeout=300
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Error {response.status_code}: {response.text}")

    def generate_report(self) -> Dict:
        """Generate summary report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_symbols": len(self.results) + len(self.errors),
            "successful": len(self.results),
            "failed": len(self.errors),
            "results": self.results,
            "errors": self.errors
        }

        # Calculate aggregate metrics
        if self.results:
            total_pnl = sum(r.get("total_pnl", 0) for r in self.results.values())
            winning_symbols = sum(1 for r in self.results.values() if r.get("total_pnl", 0) > 0)

            report["aggregate"] = {
                "total_pnl": total_pnl,
                "winning_symbols": winning_symbols,
                "losing_symbols": len(self.results) - winning_symbols,
                "win_rate": f"{(winning_symbols/len(self.results)*100):.1f}%"
            }

        return report

# Usage
if __name__ == "__main__":
    api_key = os.getenv("BACKTEST_API_KEY")
    processor = BatchBacktestProcessor(api_key)

    symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "GOLD", "CRUDEOIL"]
    results = processor.process_symbols(symbols)

    report = processor.generate_report()

    # Save report
    with open("backtest_report.json", "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"✅ Batch processing complete: {report['successful']} successful, {report['failed']} failed")
```

### Pattern 2: Real-time Dashboard

Continuously monitor strategy performance.

```javascript
// Node.js + Express dashboard
const express = require('express');
const BacktestAPI = require('./backtest-api');

const app = express();
const api = new BacktestAPI(process.env.BACKTEST_API_KEY);

// Cache for dashboard
const dashboardCache = {
  lastUpdate: null,
  results: {}
};

// Fetch latest results
app.get('/api/dashboard/latest', async (req, res) => {
  try {
    const symbols = ["NIFTY", "BANKNIFTY", "GOLD", "CRUDEOIL"];
    const results = await api.backtestBatch(symbols, "1d", "1y");

    dashboardCache.lastUpdate = new Date();
    dashboardCache.results = results;

    // Calculate metrics
    const metrics = {
      timestamp: dashboardCache.lastUpdate,
      totalPnL: Object.values(results).reduce((sum, r) => sum + r.total_pnl, 0),
      winRate: calculateWinRate(results),
      averageLatency: calculateAvgLatency(results),
      symbols: results
    };

    res.json(metrics);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// WebSocket for real-time updates
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
  const interval = setInterval(async () => {
    try {
      const metrics = await api.backtest("NIFTY");
      ws.send(JSON.stringify(metrics));
    } catch (error) {
      ws.send(JSON.stringify({ error: error.message }));
    }
  }, 60000); // Update every minute

  ws.on('close', () => clearInterval(interval));
});

app.listen(3000, () => console.log('Dashboard running on port 3000'));
```

### Pattern 3: Scheduled Reports

Generate reports on a schedule.

```python
#!/usr/bin/env python3
"""
Scheduled daily backtest report generator
"""

import os
import json
from datetime import datetime
import schedule
import time
from backtest_client import BacktestClient
from email.mime.text import MIMEText
import smtplib

class ScheduledReportGenerator:
    def __init__(self, api_key: str, recipient_email: str):
        self.client = BacktestClient(api_key)
        self.recipient_email = recipient_email

    def generate_daily_report(self):
        """Generate and send daily report"""
        logger.info("Generating daily report...")

        symbols = ["NIFTY", "BANKNIFTY", "GOLD", "CRUDEOIL"]
        results = self.client.backtest_multiple(symbols)

        # Generate HTML report
        html = self._generate_html(results)

        # Send email
        self._send_email(html)

        logger.info("Daily report sent successfully")

    def _generate_html(self, results: Dict) -> str:
        """Generate HTML email report"""
        rows = ""
        total_pnl = 0

        for symbol, data in results.items():
            total_pnl += data.get("total_pnl", 0)
            rows += f"""
            <tr>
                <td>{symbol}</td>
                <td>{data.get('trades', 0)}</td>
                <td>₹{data.get('total_pnl', 0):.2f}</td>
                <td>{data.get('return_pct', 0):.2f}%</td>
                <td>{data.get('sharpe_ratio', 0):.2f}</td>
            </tr>
            """

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .summary {{ font-size: 18px; font-weight: bold; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Daily Backtest Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <div class="summary">
                Total P&L: ₹{total_pnl:.2f}
            </div>

            <table>
                <tr>
                    <th>Symbol</th>
                    <th>Trades</th>
                    <th>P&L</th>
                    <th>Return %</th>
                    <th>Sharpe</th>
                </tr>
                {rows}
            </table>
        </body>
        </html>
        """

        return html

    def _send_email(self, html: str):
        """Send email report"""
        msg = MIMEText(html, 'html')
        msg['Subject'] = f"Daily Backtest Report - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = os.getenv('SMTP_FROM')
        msg['To'] = self.recipient_email

        # Send via SMTP
        with smtplib.SMTP(os.getenv('SMTP_HOST'), 587) as server:
            server.starttls()
            server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
            server.send_message(msg)

# Schedule daily report at 5 PM
schedule.every().day.at("17:00").do(
    ScheduledReportGenerator(
        api_key=os.getenv("BACKTEST_API_KEY"),
        recipient_email="team@infinityai.pro"
    ).generate_daily_report
)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Testing & Validation

### Unit Tests

```python
import unittest
from backtest_client import BacktestClient

class TestBacktestClient(unittest.TestCase):
    def setUp(self):
        self.client = BacktestClient(api_key="test-key")

    def test_single_symbol_backtest(self):
        """Test single symbol backtest"""
        result = self.client.backtest("GOLD", "1d", "1y")

        self.assertEqual(result["status"], "success")
        self.assertIn("results", result)
        self.assertIn("GOLD", result["results"])
        self.assertGreater(result["execution_time_ms"], 0)

    def test_multi_symbol_backtest(self):
        """Test multiple symbols"""
        result = self.client.backtest("NIFTY,GOLD", "1d", "1y")

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 2)

    def test_invalid_symbol(self):
        """Test invalid symbol handling"""
        with self.assertRaises(Exception):
            self.client.backtest("INVALID_SYMBOL")

    def test_rate_limiting(self):
        """Test rate limit handling"""
        # Make 101 requests (exceeds 100/min limit)
        for i in range(101):
            try:
                self.client.backtest("GOLD")
            except Exception as e:
                self.assertIn("429", str(e))
                break

if __name__ == '__main__':
    unittest.main()
```

### Load Testing

```bash
#!/bin/bash
# Load test with Apache Bench

API_KEY="your-api-key"
URL="https://backtest-orchestrator-3acobgd3qa-uc.a.run.app"

# Test 100 requests, 10 concurrent
ab -n 100 \
   -c 10 \
   -H "Authorization: Bearer $API_KEY" \
   -H "Content-Type: application/json" \
   -p payload.json \
   $URL

# Test sustained load (500 req over 5 min)
for i in {1..500}; do
  curl -s -X POST $URL \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"symbols":"GOLD","interval":"1d"}' &

  if [ $((i % 10)) -eq 0 ]; then
    sleep 1  # Rate limit
  fi
done
```

---

## Deployment Checklist

- [ ] API key generated and distributed securely
- [ ] Rate limiting configured (100 req/min)
- [ ] Monitoring dashboards set up
- [ ] Alert policies created
- [ ] Documentation reviewed
- [ ] Integration tests passed
- [ ] Load tests completed
- [ ] On-call rotation configured
- [ ] Runbooks created
- [ ] Team trained on API usage

---

## Support

For issues or questions:
1. Check [User Guide](./API_USER_GUIDE.md)
2. Review [Monitoring Guide](../infra/MONITORING_GUIDE.md)
3. Check [GitHub Issues](https://github.com/raghu-1718/InfinityAI.Pro/issues)
4. Email: support@infinityai.pro

**Last Updated:** January 10, 2026
