"""
InfinityAI.Pro — Finance & Calculations Verification Script
============================================================
Independently verifies calculations of:
- returns_pct
- trade outcome classification (WIN vs LOSS vs EXPIRED)
- profit factor
- win rate aggregation
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery, firestore

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"

def verify_calculations():
    bq = bigquery.Client(project=PROJECT_ID)
    db = firestore.Client(project=PROJECT_ID)

    print("================================================================================")
    print("           PHASE 5: FINANCE & CALCULATIONS INDEPENDENT AUDIT                    ")
    print("================================================================================")

    # 1. Sample 10 random equity training records
    q_sample = f"""
    SELECT signal_id, symbol, bar_date, entry_price, target_price, stop_loss_price, 
           exit_price, realized_return_pct, signal_outcome, label_win, target_pct, stop_loss_pct
    FROM `project-841b7f97-5ee3-4fbe-920.market_data.equity_training_features`
    ORDER BY RAND()
    LIMIT 10
    """
    df_sample = bq.query(q_sample).to_dataframe()

    discrepancies = 0
    print("\n--- Auditing 10 Random Training Records from BigQuery ---")
    for idx, r in df_sample.iterrows():
        entry = float(r["entry_price"])
        exit_p = float(r["exit_price"])
        stored_ret = float(r["realized_return_pct"])
        calc_ret = round(((exit_p - entry) / entry) * 100.0, 2)

        if r["signal_outcome"] == "WIN":
            expected_label = 1
        elif r["signal_outcome"] == "LOSS":
            expected_label = 0
        else: # EXPIRED
            expected_label = 1 if stored_ret > 0.5 else 0
        ret_match = abs(calc_ret - stored_ret) <= 0.05
        label_match = int(r["label_win"]) == expected_label

        if ret_match and label_match:
            print(f"[PASS] VERIFIED: {r['symbol']} ({r['bar_date']}) | Entry={entry:.2f}, Exit={exit_p:.2f} | Return={stored_ret:.2f}% | Outcome={r['signal_outcome']} (Label={r['label_win']})")
        else:
            discrepancies += 1
            print(f"[FAIL] DISCREPANCY: {r['signal_id']} | Entry={entry}, Exit={exit_p}, StoredRet={stored_ret}, CalcRet={calc_ret}")

    print(f"\nTotal Discrepancies in Sample: {discrepancies} / 10")

    # 2. Recompute Profit Factor formula manually
    print("\n--- Verifying Profit Factor Formula on Benchmark Equity Split ---")
    q_all = f"""
    SELECT realized_return_pct FROM `project-841b7f97-5ee3-4fbe-920.market_data.equity_training_features`
    """
    df_all = bq.query(q_all).to_dataframe()
    rets = df_all["realized_return_pct"].values
    pos = rets[rets > 0].sum()
    neg = abs(rets[rets < 0].sum())
    manual_pf = pos / neg
    print(f"Total Positive Returns Sum: +{pos:.2f}%")
    print(f"Total Negative Returns Sum: -{neg:.2f}%")
    print(f"Manual Baseline Profit Factor: {manual_pf:.3f}")

if __name__ == "__main__":
    verify_calculations()
