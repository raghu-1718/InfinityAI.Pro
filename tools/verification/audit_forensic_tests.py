"""
InfinityAI.Pro — Forensic Model Validation Auditor
===================================================
Executes forensic tests A through F to diagnose metrics discrepancy.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from google.cloud import bigquery, firestore, storage
import joblib

# Paths
sys.path.insert(0, os.path.abspath("backend/engine-a/src/mlops"))
from ensemble_definition import EquityEnsembleModel, OptionsEnsembleModel

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
FEATURE_COLS = [
    "rsi_14", "adx_14", "atr_14", "range_pct", "intraday_return_pct",
    "sma_20_dist_pct", "sma_50_dist_pct", "volatility_20", "volume_ratio_20"
]

def run_forensic_audit():
    bq = bigquery.Client(project=PROJECT_ID)
    db = firestore.Client(project=PROJECT_ID)
    storage_client = storage.Client(project=PROJECT_ID)

    print("================================================================================")
    print("                 PHASE 2: FORENSIC AUDIT EVIDENCE COLLECTION                   ")
    print("================================================================================")

    # --- TEST A: Row-level date range and count of 'held-out 2026' ---
    print("\n--- TEST A: Row-level date range and count of 'held-out 2026' ---")
    query_a = f"""
    SELECT 
        MIN(bar_date) as min_date,
        MAX(bar_date) as max_date,
        COUNT(*) as total_rows,
        COUNT(DISTINCT symbol) as unique_symbols
    FROM `project-841b7f97-5ee3-4fbe-920.market_data.equity_training_features`
    WHERE bar_date >= '2026-01-01'
    """
    df_a = bq.query(query_a).to_dataframe()
    print(df_a.to_string(index=False))

    # --- TEST B: Training Set vs Evaluation Set Overlap (Data Leakage Intersect) ---
    print("\n--- TEST B: Training Set vs Evaluation Set Overlap Check ---")
    query_b_full = f"""
    SELECT symbol, bar_date
    FROM `project-841b7f97-5ee3-4fbe-920.market_data.equity_training_features`
    """
    df_full = bq.query(query_b_full).to_dataframe()
    
    query_b_eval = f"""
    SELECT symbol, bar_date
    FROM `project-841b7f97-5ee3-4fbe-920.market_data.equity_training_features`
    WHERE bar_date >= '2026-01-01'
    """
    df_eval = bq.query(query_b_eval).to_dataframe()

    # Find intersection
    df_overlap = pd.merge(df_full, df_eval, on=["symbol", "bar_date"], how="inner")
    print(f"Total rows in full training table (df used to fit prod_model): {len(df_full):,}")
    print(f"Total rows in 'held-out 2026' evaluation set: {len(df_eval):,}")
    print(f"INTERSECT COUNT between prod_model training data and eval set: {len(df_overlap):,} rows (100% OVERLAP!)")

    # --- TEST C: Recompute metrics manually with fresh independent script ---
    print("\n--- TEST C: Independent Recomputation of Metrics ---")
    meta_path = "trained_models/equities/equity_ensemble_v20260901_172338_metadata.json"
    with open(meta_path, "r") as f:
        meta = json.load(f)
    
    model_path = "trained_models/equities/equity_ensemble_v20260901_172338.joblib"
    model = joblib.load(model_path)

    # Pull 2026 data
    query_2026 = f"""
    SELECT *
    FROM `project-841b7f97-5ee3-4fbe-920.market_data.equity_training_features`
    WHERE bar_date >= '2026-01-01'
    ORDER BY bar_date ASC
    """
    df_2026 = bq.query(query_2026).to_dataframe()
    X_2026 = df_2026[FEATURE_COLS].to_numpy(dtype=np.float32)
    y_2026 = np.asarray(df_2026["label_win"].values, dtype=np.int32)
    ret_2026 = np.asarray(df_2026["realized_return_pct"].values, dtype=np.float32)

    probs = model.predict_proba(X_2026)
    preds = (probs >= 0.50).astype(int)
    trade_mask = preds == 1
    
    traded_rets = ret_2026[trade_mask]
    pos_rets = traded_rets[traded_rets > 0].sum()
    neg_rets = abs(traded_rets[traded_rets < 0].sum())
    calc_win_rate = (traded_rets > 0).mean() * 100.0
    calc_pf = pos_rets / (neg_rets + 1e-9)

    print(f"evaluate_and_promote.py reported on candidate: Win Rate = 86.84%, Profit Factor = 12.51")
    print(f"Independent Recomputation on prod_model (In-Sample): Win Rate = {calc_win_rate:.2f}%, Profit Factor = {calc_pf:.2f}")

    # Now test TRUE out-of-sample on Fold 3 (model trained ONLY up to 2025-12-31)
    df_train_pre2026 = bq.query(f"SELECT * FROM `project-841b7f97-5ee3-4fbe-920.market_data.equity_training_features` WHERE bar_date <= '2025-12-31'").to_dataframe()
    X_pre = df_train_pre2026[FEATURE_COLS].to_numpy(dtype=np.float32)
    y_pre = np.asarray(df_train_pre2026["label_win"].values, dtype=np.int32)
    
    true_oos_model = EquityEnsembleModel()
    true_oos_model.fit(X_pre, y_pre)

    true_oos_probs = true_oos_model.predict_proba(X_2026)
    true_oos_preds = (true_oos_probs >= 0.50).astype(int)
    true_oos_mask = true_oos_preds == 1
    true_traded_rets = ret_2026[true_oos_mask]
    true_pos = true_traded_rets[true_traded_rets > 0].sum()
    true_neg = abs(true_traded_rets[true_traded_rets < 0].sum())
    true_win_rate = (true_traded_rets > 0).mean() * 100.0
    true_pf = true_pos / (true_neg + 1e-9)

    print(f"TRUE OUT-OF-SAMPLE 2026 (Trained <= 2025-12-31): Win Rate = {true_win_rate:.2f}%, Profit Factor = {true_pf:.2f}")

    # --- TEST D: Feature calculation window in label_historical_signals.py ---
    print("\n--- TEST D: Feature calculation inspection in label_historical_signals.py ---")
    with open("backend/engine-a/src/mlops/label_historical_signals.py", "r", encoding="utf-8") as f:
        code = f.read()
    
    indicators = ["rsi_14", "adx_14", "atr_14", "sma_20_dist_pct", "volatility_20", "volume_ratio_20"]
    for ind in indicators:
        idx = code.find(ind)
        if idx != -1:
            snippet = code[max(0, idx-40):min(len(code), idx+180)]
            print(f"Feature '{ind}' snippet:\n{snippet}\n")

    # --- TEST E: evaluate_and_promote.py Gate Logic ---
    print("\n--- TEST E: evaluate_and_promote.py Gate Logic Inspection ---")
    with open("backend/engine-a/src/mlops/evaluate_and_promote.py", "r", encoding="utf-8") as f:
        eval_code = f.read()
    gate_start = eval_code.find("def evaluate_and_promote_asset_class")
    print(eval_code[gate_start+1500:gate_start+3000])

    # --- TEST F: Stored Baseline Model & Firestore Check ---
    print("\n--- TEST F: Stored Production Baseline in Firestore ---")
    eq_curr = db.collection("active_production_models").document("EQUITY_CURRENT").get()
    opt_curr = db.collection("active_production_models").document("OPTIONS_CURRENT").get()
    print("EQUITY_CURRENT doc exists:", eq_curr.exists)
    if eq_curr.exists:
        print("EQUITY_CURRENT:", json.dumps(eq_curr.to_dict(), indent=2))
    print("OPTIONS_CURRENT doc exists:", opt_curr.exists)
    if opt_curr.exists:
        print("OPTIONS_CURRENT:", json.dumps(opt_curr.to_dict(), indent=2))

if __name__ == "__main__":
    run_forensic_audit()
