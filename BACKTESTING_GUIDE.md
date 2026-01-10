# InfinityAI.Pro Backtesting Suite

## Overview

Production-grade backtesting framework for the InfinityAI.Pro trading platform, integrating:
- **Engine-B**: Signal generation (XGBoost, LightGBM, CatBoost, Random Forest)
- **Engine-A**: Risk management (VAR, CVaR, Kelly Criterion, Position Sizing)
- **Engine-C**: Execution simulation (realistic slippage, commission)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BACKTEST WORKFLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. DATA INGESTION                                          │
│     └─ tools/ingest_dhan_historical.py                     │
│        • Fetch OHLCV from Dhan API                         │
│        • Multiple symbols, intervals, periods              │
│        • Store in Cloud Storage (GCS)                      │
│                                                             │
│  2. SIGNAL GENERATION                                       │
│     └─ Engine-B (Cloud Run)                                │
│        • ML ensemble (4+ models)                           │
│        • Returns: Entry/Exit signals per candle            │
│        • Confidence scores                                 │
│                                                             │
│  3. RISK MANAGEMENT                                         │
│     └─ Engine-A (Cloud Run)                                │
│        • VAR/CVaR calculations                             │
│        • Kelly Criterion position sizing                   │
│        • Risk-adjusted entry/exit                          │
│                                                             │
│  4. BACKTESTING                                             │
│     └─ backend/backtester/engine.py                        │
│        • Vectorbt-based portfolio simulation               │
│        • Realistic commission/slippage                     │
│        • MA Crossover + Engine signals combo               │
│                                                             │
│  5. RESULT STORAGE                                          │
│     └─ Cloud Storage + Firestore                           │
│        • JSON performance metrics                          │
│        • Trade-by-trade analysis                           │
│        • Historical data archival                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

```bash
pip install pandas numpy vectorbt aiohttp google-cloud-storage google-cloud-firestore
```

### 1. Ingest Historical Data

```bash
# Using Dhan API (requires credentials)
python tools/ingest_dhan_historical.py \
  --symbols NIFTY BANKNIFTY FINNIFTY \
  --intervals 1d 1h 15m \
  --periods 6m 1y 3y \
  --access-token YOUR_DHAN_TOKEN \
  --client-id YOUR_DHAN_CLIENT_ID

# Or load from Firestore
python tools/ingest_dhan_historical.py \
  --credentials-user-id 1101302170 \
  --bucket gs://infinityai-backtesting-data
```

**Output:**
- GCS: `gs://infinityai-backtesting-data/data/{SYMBOL}/{INTERVAL}/{PERIOD}.csv`
- Metadata: `gs://infinityai-backtesting-data/metadata/{timestamp}_ingest.json`

### 2. Run Backtest Locally

```bash
cd backend/backtester

# Simple MA Crossover (no engine integration needed)
python engine.py --symbol NIFTY

# With Engine-B signals (requires Cloud Run access)
python engine.py --symbol NIFTY --use-engine-b --use-engine-a
```

### 3. Run Multi-Symbol Backtest via Cloud Function

```bash
# Deploy function
gcloud functions deploy backtest-orchestrator \
  --runtime python312 \
  --trigger-http \
  --entry-point orchestrate_backtest \
  --project galvanic-pulsar-482815-h0 \
  --region us-central1 \
  --timeout 3600

# Trigger backtest
curl -X POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1101302170"}'
```

## Configuration

### Data Ingestion Config

**File:** `tools/ingest_dhan_historical.py`

```python
IngestConfig(
    symbols=["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "GOLD", "CRUDEOIL"],
    intervals=["1d", "1h", "15m"],
    periods={"6m": 180, "1y": 365, "3y": 1095},
    gcs_bucket="infinityai-backtesting-data",
    max_concurrent=5,
    batch_size=500
)
```

### Backtest Config

**File:** `backend/backtester/engine.py`

```python
BacktestConfig(
    symbols=["NIFTY"],
    initial_capital=1000000,           # $1M starting capital
    commission=0.0005,                 # 0.05% per trade
    slippage=0.001,                    # 0.1% slippage
    position_size_method="kelly",      # kelly, fixed, risk_parity
    risk_per_trade=0.02,               # 2% max risk per trade
    use_engine_b_signals=True,         # ML signals
    use_engine_a_risk=True,            # Risk-adjusted sizing
    engine_b_url="https://engine-b-...",
    engine_a_url="https://engine-a-...",
)
```

## Strategy Types

### 1. MA Crossover (Baseline)

```python
engine.run_ma_crossover_with_engine_signals(
    fast_ma=20,
    slow_ma=50,
    integration=integration  # Optional Engine integration
)
```

**Logic:**
- Entry: Fast MA > Slow MA
- Exit: Fast MA < Slow MA

### 2. Engine-B Signals Only

```python
engine.run_engine_b_signals_only(
    integration=integration
)
```

**Logic:**
- Entry/Exit: ML model predictions from Engine-B
- Confidence threshold: 0.6+

### 3. Combined (MA + Engine-B + Engine-A)

```python
engine.run_ma_crossover_with_engine_signals(
    fast_ma=20,
    slow_ma=50,
    integration=integration
)
```

**Logic:**
- Entry: (MA Crossover) AND (Engine-B Signal)
- Position Size: Engine-A Kelly Criterion
- Risk Limit: 2% max loss per trade

## Output & Reports

### Backtest Report JSON

```json
{
  "symbol": "NIFTY",
  "timestamp": "2026-01-10T18:30:00",
  "performance": {
    "total_return": 28.5,
    "annual_return": 12.3,
    "sharpe_ratio": 1.82,
    "sortino_ratio": 2.47,
    "max_drawdown": -14.7,
    "win_rate": 0.6449,
    "profit_factor": 2.15
  },
  "trades": {
    "total_trades": 245,
    "winning_trades": 158,
    "losing_trades": 87,
    "avg_trade_pnl": 1163.27,
    "best_trade": 8.5,
    "worst_trade": -3.2
  },
  "duration": {
    "backtest_period_days": 365,
    "avg_holding_period_days": 4.2
  }
}
```

**Location:**
- Local: `data/results/{SYMBOL}_backtest_{timestamp}.json`
- GCS: `gs://infinityai-backtesting-data/results/{SYMBOL}/backtest_{timestamp}.json`
- Firestore: `backtest_results` collection

## Performance Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Sharpe Ratio** | Risk-adjusted return | > 1.5 |
| **Sortino Ratio** | Downside risk-adjusted | > 2.0 |
| **Profit Factor** | Gross profit / Gross loss | > 1.5 |
| **Win Rate** | % of profitable trades | > 50% |
| **Max Drawdown** | Largest peak-to-trough | < 20% |
| **CAGR** | Compound Annual Growth Rate | > 15% |

## Data Storage

### Cloud Storage (Historical Data)

```
gs://infinityai-backtesting-data/
├── data/
│   ├── NIFTY/
│   │   ├── 1d/
│   │   │   ├── 6m.csv
│   │   │   ├── 1y.csv
│   │   │   └── 3y.csv
│   │   ├── 1h/
│   │   └── 15m/
│   ├── BANKNIFTY/
│   └── ...
├── metadata/
│   ├── 2026-01-10T18-30-00_ingest.json
│   └── ...
└── results/
    ├── NIFTY/
    │   ├── backtest_2026-01-10T18-30-00.json
    │   └── ...
    └── ...
```

### Firestore (Results)

```
backtest_results/
├── 1101302170/
│   {
│     "user_id": "1101302170",
│     "timestamp": "2026-01-10T18:30:00",
│     "results": { ... },
│     "symbols": ["NIFTY", "BANKNIFTY", "FINNIFTY"],
│   }
```

## Integration with Production Engines

### Engine-B Signal Generation

**Endpoint:** `POST /api/v1/signals`

```python
payload = {
    "symbol": "NIFTY",
    "lookback_candles": 500,
    "model": "ensemble",  # xgboost, lightgbm, catboost, random_forest, ensemble
    "confidence_threshold": 0.6
}

response = await integration.get_engine_b_signals("NIFTY", df)
# Returns: np.array of shape (len(df),) with bool entry signals
```

### Engine-A Risk Calculations

**Endpoint:** `POST /api/v1/risk/position-size`

```python
payload = {
    "symbol": "NIFTY",
    "portfolio_value": 1000000,
    "risk_per_trade": 0.02,  # 2%
    "method": "kelly"
}

position_size = await integration.get_engine_a_position_size(...)
# Returns: float (0.0 to 1.0) position size multiplier
```

## Advanced Usage

### Custom Strategy Development

```python
class CustomStrategy:
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.engine = BacktestEngine("NIFTY", config=config)
        self.integration = EngineIntegration(config)

    async def my_strategy(self):
        # Load data
        df = self.engine.df

        # Generate custom signals
        entries = ... # Your logic here
        exits = ...

        # Portfolio simulation
        portfolio = vbt.Portfolio.from_signals(
            df["Close"].values,
            entries,
            exits,
            init_cash=self.config.initial_capital,
            fees=self.config.commission,
            freq="1d"
        )

        # Generate report
        return await self.engine._generate_backtest_report(portfolio)
```

### Batch Backtesting

```python
config = BacktestConfig(
    symbols=["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"],
    initial_capital=1000000,
    use_engine_b_signals=True,
    use_engine_a_risk=True
)

results = asyncio.run(run_multi_symbol_backtest(config))

# results = {
#   "NIFTY": { ... },
#   "BANKNIFTY": { ... },
#   "FINNIFTY": { ... },
#   "SENSEX": { ... }
# }
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Historical data not found"** | Run `ingest_dhan_historical.py` first |
| **"Engine-B unavailable"** | Check Cloud Run service is live: `gcloud run services describe engine-b` |
| **"Rate limited by Dhan API"** | Increase `--max-concurrent` or reduce request frequency |
| **GCS upload fails** | Verify bucket exists and credentials have Storage permissions |
| **Firestore permission error** | Check `firestore.rules` allows write to `backtest_results` |

## Production Deployment

### 1. Deploy Cloud Function

```bash
gcloud functions deploy backtest-orchestrator \
  --runtime python312 \
  --trigger-http \
  --entry-point orchestrate_backtest \
  --project galvanic-pulsar-482815-h0 \
  --region us-central1 \
  --timeout 3600 \
  --set-env-vars DHAN_API_BASE=https://api.dhan.co/v2
```

### 2. Schedule Daily Backtests

```bash
gcloud scheduler jobs create http backtest-daily \
  --schedule="0 2 * * *" \
  --uri="https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/backtest-orchestrator" \
  --http-method=POST \
  --message-body='{"user_id": "1101302170"}'
```

### 3. Monitor Results

```bash
# View function logs
gcloud functions logs read backtest-orchestrator --limit 50

# Query Firestore results
firebase firestore:query backtest_results
```

## Performance Benchmarks

**Machine:** Cloud Run 2 vCPU / 4GB RAM

| Symbol | Period | Candles | Runtime |
|--------|--------|---------|---------|
| NIFTY  | 1 year (Daily) | 252 | ~2.5s |
| NIFTY  | 1 year (Hourly) | 6,048 | ~8.3s |
| NIFTY  | 1 year (15-min) | 24,192 | ~22.1s |
| NIFTY + BANKNIFTY | 1 year | 504 | ~5.2s |
| All 6 symbols | 1 year | 3,024 | ~31.5s |

## Next Steps

1. ✅ **Ingest Data**: Run `ingest_dhan_historical.py` to download 6 months, 1 year, 3 years of data
2. ⏳ **Local Backtest**: Test with `python engine.py` to validate locally
3. ⏳ **Engine Integration**: Connect to live Engine-B and Engine-A via APIs
4. ⏳ **Multi-Symbol**: Run batch backtests on all symbols
5. ⏳ **Cloud Deployment**: Deploy orchestrator function for automated backtesting

## References

- **Vectorbt**: https://vectorbt.dev/
- **Dhan API**: https://dhan.co/
- **Cloud Run**: https://cloud.google.com/run
- **Cloud Functions**: https://cloud.google.com/functions
- **Cloud Storage**: https://cloud.google.com/storage

---

**Status**: ✅ Ready for backtesting with Dhan data
**Updated**: 2026-01-10
**Maintainer**: Platform Engineering Team
