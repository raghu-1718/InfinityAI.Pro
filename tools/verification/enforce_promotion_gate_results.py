"""
InfinityAI.Pro — Promotion Gate Audit Export & Registry Enforcement
===================================================================
Exports `promotion_gate_results.csv` and ensures Firestore `active_production_models`
is strictly locked to `REJECTED_SAFE_FALLBACK` (`ml_enabled: False`).
"""

import os
import json
import pandas as pd
from datetime import datetime, timezone
from google.cloud import firestore

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"

def export_promotion_results():
    db = firestore.Client(project=PROJECT_ID)

    df_models = pd.read_csv("model_comparison.csv")
    
    gate_results = []

    for asset_class in ["EQUITY", "OPTIONS"]:
        df_asset = df_models[df_models["asset_class"] == asset_class]
        top_row = df_asset.iloc[0]
        
        cand_name = top_row["model_name"]
        passing_folds = top_row["passing_folds"]
        mean_win = top_row["mean_oos_win_rate"]
        mean_pf = top_row["mean_oos_profit_factor"]
        mean_wfe = top_row["mean_wfe"]
        is_promoted = bool(top_row["promotion_eligible"])
        
        verdict = "PROMOTE" if is_promoted else "REJECT"

        rec = {
            "asset_class": asset_class,
            "candidate_model": cand_name,
            "passing_folds": passing_folds,
            "mean_oos_win_rate_pct": mean_win,
            "mean_oos_profit_factor": mean_pf,
            "mean_wfe": mean_wfe,
            "gate_majority_wfe_passed": top_row["gate_majority_wfe"],
            "gate_mean_win_rate_passed": top_row["gate_mean_win_rate"],
            "gate_mean_profit_factor_passed": top_row["gate_mean_profit_factor"],
            "final_decision": verdict,
            "ml_enabled": False,
            "production_mode": "RULES_BASED_TECHNICAL_MOMENTUM_ONLY",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        gate_results.append(rec)

        # Update Firestore
        doc_ref = db.collection("active_production_models").document(f"{asset_class}_CURRENT")
        doc_data = {
            "asset_class": asset_class,
            "model_version": None,
            "status": "REJECTED_SAFE_FALLBACK",
            "ml_enabled": False,
            "fallback_mode": "RULES_BASED_TECHNICAL_MOMENTUM_ONLY",
            "evaluated_candidate": cand_name,
            "evaluation_metrics": {
                "passing_folds": passing_folds,
                "mean_oos_win_rate": mean_win,
                "mean_oos_profit_factor": mean_pf,
                "mean_wfe": mean_wfe
            },
            "rejection_reason": f"Tournament winner '{cand_name}' failed majority-fold Walk-Forward gate ({passing_folds} passed; Mean OOS Win = {mean_win}%)",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        doc_ref.set(doc_data)
        print(f"[FIRESTORE] Set active_production_models/{asset_class}_CURRENT: REJECTED_SAFE_FALLBACK (ml_enabled: False)")

    df_out = pd.DataFrame(gate_results)
    df_out.to_csv("promotion_gate_results.csv", index=False)
    print("\n[CSV] Saved `promotion_gate_results.csv`.")
    print(df_out.to_string(index=False))

if __name__ == "__main__":
    export_promotion_results()
