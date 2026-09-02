"""
Backtesting Runner & BigQuery Run Persistence
Executes strategies and persists performance records to BigQuery dataset market_data.
"""
import sys
import uuid
import json
import argparse
from typing import Dict, Any
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backtesting.vectorized_engine import VectorizedBacktester
from db.dal.bigquery_dal import bigquery_dal


def generate_synthetic_nifty_bars(n_bars: int = 252) -> pd.DataFrame:
    """Generate realistic 1-year daily bars for NIFTY 50."""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.utcnow(), periods=n_bars, freq="B")
    
    # Starting at ~21,500 and trending upwards to ~24,500 with 12% vol
    returns = np.random.normal(0.0006, 0.0085, size=n_bars)
    price_curve = 21500.0 * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        "timestamp": dates,
        "close": price_curve,
        "volume": np.random.randint(100000, 500000, size=n_bars)
    })

    # Add technical indicators for strategy signals
    df["sma_20"] = df["close"].rolling(20, min_periods=1).mean()
    df["sma_50"] = df["close"].rolling(50, min_periods=1).mean()
    # Strategy signal: 1 when 20 SMA > 50 SMA, 0 otherwise
    df["signal"] = (df["sma_20"] > df["sma_50"]).astype(float)

    return df


def execute_backtest_and_persist(
    strategy_name: str = "tri_model_ensemble",
    initial_capital: float = 500000.0,
    slippage_pct: float = 0.0005,
    include_sebi_taxes: bool = True
) -> Dict[str, Any]:
    """Execute backtest and store run results in BigQuery."""
    df = generate_synthetic_nifty_bars()
    backtester = VectorizedBacktester(
        initial_capital=initial_capital,
        slippage_pct=slippage_pct,
        include_sebi_taxes=include_sebi_taxes
    )

    # 1. Run Strategy
    if strategy_name == "buy_and_hold":
        metrics = backtester.run_buy_and_hold_benchmark(df)
    else:
        metrics = backtester.run_strategy(df, signal_col="signal")

    run_id = f"bt-{uuid.uuid4().hex[:10]}"
    record = {
        "run_id": run_id,
        "strategy": strategy_name,
        "symbol": "NIFTY",
        "start_date": str(df["timestamp"].iloc[0].date()),
        "end_date": str(df["timestamp"].iloc[-1].date()),
        "initial_capital": initial_capital,
        "total_pnl": metrics["total_pnl"],
        "total_return_pct": metrics["total_return_pct"],
        "sharpe_ratio": metrics["sharpe_ratio"],
        "deflated_sharpe_ratio": metrics["deflated_sharpe_ratio"],
        "probabilistic_sharpe_ratio": metrics["probabilistic_sharpe_ratio"],
        "max_drawdown": metrics["max_drawdown_pct"],
        "win_rate": metrics["win_rate_pct"],
        "total_trades": metrics["total_trades"],
        "metrics_json": json.dumps(metrics),
        "created_at": datetime.utcnow().isoformat()
    }

    # 2. Persist to BigQuery DAL
    bigquery_dal.insert_backtest_run(record)
    return {"run_id": run_id, "metrics": metrics}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run institutional backtest")
    parser.add_argument("--benchmark", type=str, default="tri_model_ensemble", choices=["buy_and_hold", "tri_model_ensemble"])
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    result = execute_backtest_and_persist(strategy_name=args.benchmark)
    m = result["metrics"]
    print(f"\n==================== BACKTEST SUMMARY: {args.benchmark.upper()} ====================")
    print(f"Run ID:                 {result['run_id']}")
    print(f"Initial Capital:        INR {m['initial_capital']:,.2f}")
    print(f"Final Equity:           INR {m['final_equity']:,.2f}")
    print(f"Net P&L:                INR {m['total_pnl']:,.2f} ({m['total_return_pct']}%)")
    print(f"Sharpe Ratio:           {m['sharpe_ratio']}")
    print(f"Deflated Sharpe (DSR):  {m['deflated_sharpe_ratio']}")
    print(f"Probabilistic Sharpe:   {m['probabilistic_sharpe_ratio']}")
    print(f"Max Drawdown:           {m['max_drawdown_pct']}%")
    print(f"Win Rate:               {m['win_rate_pct']}%")
    print(f"Total Trades:           {m['total_trades']}")
    print("=========================================================================\n")
