"""
Out-of-Sample (OOS) Model Backtest Evaluation
Connects Tri-Model ML predictions with the Phase 6 institutional backtesting engine.
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_models.training_pipeline import TriModelTrainingPipeline
from backtesting.vectorized_engine import VectorizedBacktester
from backtesting.runner import generate_synthetic_nifty_bars
from db.dal.bigquery_dal import bigquery_dal


def run_oos_model_backtest(n_bars: int = 500) -> dict:
    """
    Train Tri-Model on historical data, generate Out-of-Sample predictions,
    and backtest predictions using the Phase 6 Vectorized Backtester.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # 1. Generate historical market data
    df = generate_synthetic_nifty_bars(n_bars=n_bars)

    # 2. Train Tri-Model pipeline
    pipeline = TriModelTrainingPipeline(version="v2.5.0-oos")
    training_results = pipeline.train(df)

    test_df = training_results["test_df"].copy()
    oos_probs = pipeline.predict_ensemble(test_df)

    # 3. Formulate trading signals from probabilities
    # Signal: 1 (Long) if prob >= 0.52, 0 (Cash) if between 0.48-0.52, -1 (Short) if <= 0.48
    test_df["signal"] = np.where(oos_probs >= 0.52, 1.0, np.where(oos_probs <= 0.48, -1.0, 0.0))

    # 4. Backtest through Phase 6 Engine
    backtester = VectorizedBacktester(
        initial_capital=500000.0,
        slippage_pct=0.0005,
        include_sebi_taxes=True
    )
    oos_metrics = backtester.run_strategy(test_df, signal_col="signal")

    # 5. Persist OOS Backtest to BigQuery
    run_id = f"bt-oos-ml-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    record = {
        "run_id": run_id,
        "strategy": "tri_model_ml_oos_predictions",
        "symbol": "NIFTY",
        "start_date": str(test_df["timestamp"].iloc[0].date()),
        "end_date": str(test_df["timestamp"].iloc[-1].date()),
        "initial_capital": 500000.0,
        "total_pnl": oos_metrics["total_pnl"],
        "total_return_pct": oos_metrics["total_return_pct"],
        "sharpe_ratio": oos_metrics["sharpe_ratio"],
        "deflated_sharpe_ratio": oos_metrics["deflated_sharpe_ratio"],
        "probabilistic_sharpe_ratio": oos_metrics["probabilistic_sharpe_ratio"],
        "max_drawdown": oos_metrics["max_drawdown_pct"],
        "win_rate": oos_metrics["win_rate_pct"],
        "total_trades": oos_metrics["total_trades"],
        "metrics_json": json.dumps(oos_metrics),
        "created_at": datetime.utcnow().isoformat()
    }
    bigquery_dal.insert_backtest_run(record)

    return {
        "run_id": run_id,
        "classification_metrics": training_results["metrics"],
        "oos_backtest_metrics": oos_metrics,
        "test_bars": len(test_df)
    }


if __name__ == "__main__":
    res = run_oos_model_backtest(n_bars=500)
    m = res["oos_backtest_metrics"]
    clf = res["classification_metrics"]["ensemble"]

    print("\n==================== TRI-MODEL OOS BACKTEST REPORT ====================")
    print(f"Run ID:                 {res['run_id']}")
    print(f"OOS Test Samples:       {res['test_bars']} bars")
    print(f"Ensemble OOS Accuracy:  {clf['accuracy'] * 100:.1f}%")
    print(f"Ensemble OOS ROC-AUC:   {clf['roc_auc']:.3f}")
    print(f"Ensemble OOS F1 Score:  {clf['f1_score']:.3f}")
    print("-----------------------------------------------------------------------")
    print(f"Initial Capital:        INR {m['initial_capital']:,.2f}")
    print(f"Final Equity:           INR {m['final_equity']:,.2f}")
    print(f"Net OOS P&L:            INR {m['total_pnl']:,.2f} ({m['total_return_pct']}%)")
    print(f"Sharpe Ratio:           {m['sharpe_ratio']}")
    print(f"Deflated Sharpe (DSR):  {m['deflated_sharpe_ratio']}")
    print(f"Probabilistic Sharpe:   {m['probabilistic_sharpe_ratio']}")
    print(f"Max Drawdown:           {m['max_drawdown_pct']}%")
    print(f"Win Rate:               {m['win_rate_pct']}%")
    print(f"Total Trades:           {m['total_trades']}")
    print("=======================================================================\n")
