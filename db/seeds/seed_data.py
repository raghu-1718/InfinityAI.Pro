"""
Seed Script for BigQuery & Storage Layer
Populates realistic Indian market data across ticks, trades, model metadata, and backtests.
"""
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from db.dal.bigquery_dal import bigquery_dal
from backend.shared.tax_calculator import calculate_options_roundtrip_charges


def generate_seed_ticks(count: int = 50) -> List[Dict[str, Any]]:
    """Generate realistic NIFTY/BANKNIFTY options ticks."""
    ticks = []
    base_time = datetime.utcnow() - timedelta(minutes=count)
    for i in range(count):
        sym = "NIFTY" if i % 2 == 0 else "BANKNIFTY"
        strike = 24500.0 if sym == "NIFTY" else 51500.0
        opt_type = "CE" if (i // 2) % 2 == 0 else "PE"
        premium = round(135.0 + (i * 0.45), 2)
        ticks.append({
            "tick_id": f"seed-tick-{i:04d}",
            "symbol": sym,
            "price": premium,
            "volume": 1000 + (i * 50),
            "strike_price": strike,
            "option_type": opt_type,
            "open_interest": 450000 + (i * 1200),
            "implied_volatility": round(14.2 + ((i % 10) * 0.1), 2),
            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "correlation_id": f"seed-corr-{i:04d}"
        })
    return ticks


def generate_seed_trades(count: int = 10) -> List[Dict[str, Any]]:
    """Generate executed trades with calculated statutory taxes."""
    trades = []
    base_time = datetime.utcnow() - timedelta(hours=count)
    for i in range(count):
        sym = "NIFTY26AUG24500CE"
        action = "BUY" if i % 2 == 0 else "SELL"
        qty = 65
        price = 145.0 + (i * 2.5)
        gross = round(price * qty, 2)
        taxes = calculate_options_roundtrip_charges(premium=price, lot_size=65, lots=1)
        tax_amount = taxes.get("total_charges", 55.40)
        net_pnl = round(1850.0 - tax_amount if action == "SELL" else 0.0, 2)

        trades.append({
            "trade_id": f"seed-trd-{i:04d}",
            "correlation_id": f"seed-order-corr-{i:04d}",
            "symbol": sym,
            "action": action,
            "quantity": qty,
            "price": price,
            "order_type": "LIMIT",
            "gross_value": gross,
            "statutory_taxes": tax_amount,
            "net_pnl": net_pnl,
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "strategy": "tri_model_ensemble"
        })
    return trades


def generate_seed_models() -> List[Dict[str, Any]]:
    """Generate Tri-Model ensemble metadata records."""
    now = datetime.utcnow().isoformat()
    return [
        {
            "model_id": "mdl-catboost-001",
            "model_name": "catboost",
            "version": "v2.4-cbm",
            "algorithm": "CatBoostClassifier",
            "weights_json": '{"weight": 0.40, "features": 18}',
            "val_loss": 0.312,
            "sharpe_ratio": 1.95,
            "gcs_artifact_uri": "gs://infinity-ai-models-vault/catboost_v2.4.cbm",
            "registered_at": now
        },
        {
            "model_id": "mdl-lightgbm-001",
            "model_name": "lightgbm",
            "version": "v2.4-lgb",
            "algorithm": "LGBMClassifier",
            "weights_json": '{"weight": 0.35, "features": 18}',
            "val_loss": 0.328,
            "sharpe_ratio": 1.88,
            "gcs_artifact_uri": "gs://infinity-ai-models-vault/lightgbm_v2.4.txt",
            "registered_at": now
        },
        {
            "model_id": "mdl-xgboost-001",
            "model_name": "xgboost",
            "version": "v2.4-xgb",
            "algorithm": "XGBClassifier",
            "weights_json": '{"weight": 0.25, "features": 18}',
            "val_loss": 0.341,
            "sharpe_ratio": 1.76,
            "gcs_artifact_uri": "gs://infinity-ai-models-vault/xgboost_v2.4.json",
            "registered_at": now
        }
    ]


def generate_seed_backtests() -> List[Dict[str, Any]]:
    """Generate historical backtest runs."""
    now = datetime.utcnow().isoformat()
    return [
        {
            "run_id": "bt-seed-wfo-001",
            "strategy": "tri_model_ensemble_wfo",
            "symbol": "NIFTY",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 500000.0,
            "total_pnl": 184500.0,
            "total_return_pct": 36.9,
            "sharpe_ratio": 1.84,
            "deflated_sharpe_ratio": 1.62,
            "probabilistic_sharpe_ratio": 0.965,
            "max_drawdown": 10.4,
            "win_rate": 54.2,
            "total_trades": 184,
            "metrics_json": '{"slippage": 0.0005, "sebi_taxes_included": true}',
            "created_at": now
        },
        {
            "run_id": "bt-seed-bnh-002",
            "strategy": "buy_and_hold_benchmark",
            "symbol": "NIFTY",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 500000.0,
            "total_pnl": 95000.0,
            "total_return_pct": 19.0,
            "sharpe_ratio": 1.15,
            "deflated_sharpe_ratio": 0.98,
            "probabilistic_sharpe_ratio": 0.880,
            "max_drawdown": 14.8,
            "win_rate": 51.0,
            "total_trades": 1,
            "metrics_json": '{"benchmark": true}',
            "created_at": now
        }
    ]


def run_seed_all() -> Dict[str, Any]:
    """Execute complete seeding process and benchmark query latency."""
    t0 = time.monotonic()
    
    ticks = generate_seed_ticks(50)
    ticks_inserted = bigquery_dal.insert_ticks(ticks)

    trades = generate_seed_trades(10)
    trades_inserted = bigquery_dal.insert_trades(trades)

    models = generate_seed_models()
    for m in models:
        bigquery_dal.insert_model_metadata(m)

    backtests = generate_seed_backtests()
    for b in backtests:
        bigquery_dal.insert_backtest_run(b)

    counts = bigquery_dal.get_row_counts()
    
    # Measure query latency
    query_t0 = time.monotonic()
    query_res = bigquery_dal.query_ticks("NIFTY", limit=25)
    query_latency_ms = round((time.monotonic() - query_t0) * 1000.0, 2)
    total_time_ms = round((time.monotonic() - t0) * 1000.0, 2)

    summary = {
        "status": "seeded",
        "row_counts": counts,
        "ticks_queried": len(query_res),
        "query_latency_ms": query_latency_ms,
        "total_seed_duration_ms": total_time_ms
    }
    return summary


if __name__ == "__main__":
    result = run_seed_all()
    print("Seeding Complete:", result)
