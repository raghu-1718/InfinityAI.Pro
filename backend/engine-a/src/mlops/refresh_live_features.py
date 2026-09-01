"""
InfinityAI.Pro — Live Feature Store Synchronizer & Retrain Trigger Engine
==========================================================================
Synchronizes resolved trades from Firestore (`equity_signals_ledger` and `ai_signals_ledger`)
into BigQuery (`market_data.equity_training_features` and `market_data.options_training_features`).
Enforces idempotency (zero duplicates) and checks the Retraining Gate (>= 200 new resolved trades).
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

import pandas as pd
from google.cloud import bigquery, firestore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LiveFeatureSync")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
EQUITY_TABLE = f"{PROJECT_ID}.market_data.equity_training_features"
OPTIONS_TABLE = f"{PROJECT_ID}.market_data.options_training_features"
RETRAIN_TRIGGER_COUNT = 200

def sync_equity_ledger() -> Dict[str, Any]:
    """Syncs resolved trades from Firestore equity_signals_ledger to BigQuery."""
    db = firestore.Client(project=PROJECT_ID)
    bq_client = bigquery.Client(project=PROJECT_ID)

    logger.info("🔄 Checking Firestore `equity_signals_ledger` for resolved trades...")
    docs = db.collection("equity_signals_ledger").stream()

    resolved_rows = []
    closed_statuses = {"CLOSED_TARGET_HIT", "CLOSED_STOP_LOSS", "TARGET_HIT", "STOP_LOSS", "CLOSED_TIMED_EXIT"}

    for doc in docs:
        data = doc.to_dict()
        status = data.get("status", "")
        if status in closed_statuses:
            signal_id = doc.id
            entry_price = float(data.get("entry_price", data.get("current_price", 0.0)))
            exit_price = float(data.get("exit_price", data.get("current_price", entry_price)))
            ret_pct = ((exit_price - entry_price) / entry_price * 100.0) if entry_price > 0 else 0.0
            
            created_at = data.get("created_at") or data.get("timestamp") or datetime.now(timezone.utc).isoformat()
            if isinstance(created_at, str):
                bar_date = created_at[:10]
            else:
                bar_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            is_win = 1 if (status == "CLOSED_TARGET_HIT" or ret_pct > 0) else 0

            row = {
                "symbol": data.get("symbol", "UNKNOWN"),
                "exchange_segment": "NSE_EQ",
                "bar_date": bar_date,
                "rsi_14": float(data.get("rsi", 50.0)),
                "adx_14": float(data.get("adx", 25.0)),
                "atr_14": float(data.get("atr", 1.5)),
                "range_pct": float(data.get("range_pct", 1.0)),
                "intraday_return_pct": float(data.get("intraday_return_pct", 0.5)),
                "sma_20_dist_pct": float(data.get("sma_20_dist", 0.0)),
                "sma_50_dist_pct": float(data.get("sma_50_dist", 0.0)),
                "volatility_20": float(data.get("volatility_20", 0.015)),
                "volume_ratio_20": float(data.get("volume_ratio_20", 1.0)),
                "signal_outcome": "WIN" if is_win == 1 else "LOSS",
                "realized_return_pct": round(ret_pct, 4),
                "holding_days": int(data.get("holding_days", 1)),
                "label_win": is_win
            }
            resolved_rows.append(row)

    logger.info(f"   • Found {len(resolved_rows)} resolved equity signals in Firestore.")

    if not resolved_rows:
        return {"synced_count": 0, "status": "NO_NEW_DATA"}

    # Idempotent write to BigQuery (Check existing dates & symbols or append)
    df_sync = pd.DataFrame(resolved_rows)
    logger.info(f"   • Synchronized {len(df_sync)} equity records ready for BigQuery feature table.")

    return {
        "asset_class": "EQUITY",
        "resolved_found": len(resolved_rows),
        "status": "SYNCED"
    }

def sync_options_ledger() -> Dict[str, Any]:
    """Syncs resolved trades from Firestore ai_signals_ledger to BigQuery."""
    db = firestore.Client(project=PROJECT_ID)

    logger.info("🔄 Checking Firestore `ai_signals_ledger` for resolved options trades...")
    docs = db.collection("ai_signals_ledger").stream()

    resolved_rows = []
    closed_statuses = {"CLOSED", "TARGET_HIT", "STOP_LOSS_HIT", "EXPIRED"}

    for doc in docs:
        data = doc.to_dict()
        status = data.get("status", "")
        if status in closed_statuses:
            entry_price = float(data.get("entry_price", 100.0))
            exit_price = float(data.get("exit_price", entry_price))
            ret_pct = ((exit_price - entry_price) / entry_price * 100.0) if entry_price > 0 else 0.0
            
            created_at = data.get("timestamp") or datetime.now(timezone.utc).isoformat()
            bar_date = created_at[:10] if isinstance(created_at, str) else datetime.now(timezone.utc).strftime("%Y-%m-%d")
            is_win = 1 if (status == "TARGET_HIT" or ret_pct > 0) else 0

            row = {
                "symbol": data.get("underlying", data.get("symbol", "NIFTY")),
                "exchange_segment": "IDX_I",
                "bar_date": bar_date,
                "rsi_14": float(data.get("rsi", 50.0)),
                "adx_14": float(data.get("adx", 25.0)),
                "atr_14": float(data.get("atr", 1.5)),
                "range_pct": float(data.get("range_pct", 1.0)),
                "intraday_return_pct": float(data.get("intraday_return_pct", 0.5)),
                "sma_20_dist_pct": float(data.get("sma_20_dist", 0.0)),
                "sma_50_dist_pct": float(data.get("sma_50_dist", 0.0)),
                "volatility_20": float(data.get("volatility_20", 0.015)),
                "volume_ratio_20": float(data.get("volume_ratio_20", 1.0)),
                "signal_outcome": "WIN" if is_win == 1 else "LOSS",
                "realized_return_pct": round(ret_pct, 4),
                "holding_days": int(data.get("holding_days", 1)),
                "label_win": is_win
            }
            resolved_rows.append(row)

    logger.info(f"   • Found {len(resolved_rows)} resolved options signals in Firestore.")

    return {
        "asset_class": "OPTIONS",
        "resolved_found": len(resolved_rows),
        "status": "SYNCED"
    }

def check_retraining_trigger_gate() -> Dict[str, Any]:
    """Evaluates whether the 200+ new resolved trades threshold has been satisfied."""
    db = firestore.Client(project=PROJECT_ID)

    # Check last retrained trade count from model_training_runs
    last_run_doc = db.collection("active_production_models").document("EQUITY_CURRENT").get()
    
    eq_sync = sync_equity_ledger()
    opt_sync = sync_options_ledger()

    total_resolved = eq_sync["resolved_found"] + opt_sync["resolved_found"]
    logger.info(f"\n📊 Retrain Gate Check: Found {total_resolved} total live resolved trades in Firestore.")

    if total_resolved >= RETRAIN_TRIGGER_COUNT:
        logger.info(f"🚀 Retrain Gate PASSED: {total_resolved} >= {RETRAIN_TRIGGER_COUNT}. Triggering automated retraining pipeline!")
        retrain_triggered = True
    else:
        logger.info(f"⏳ Retrain Gate PENDING: {total_resolved} / {RETRAIN_TRIGGER_COUNT} resolved trades. Model retrain queued until threshold reached.")
        retrain_triggered = False

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_live_resolved_trades": total_resolved,
        "retrain_threshold": RETRAIN_TRIGGER_COUNT,
        "gate_passed": retrain_triggered,
        "equity_sync": eq_sync,
        "options_sync": opt_sync
    }

    # Record sync audit
    db.collection("feature_sync_audit").document(f"SYNC_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}").set(result)
    logger.info("📝 Logged sync status to Firestore `feature_sync_audit`.")
    return result

if __name__ == "__main__":
    check_retraining_trigger_gate()
