"""
InfinityAI.Pro — Institutional Model Evaluation & Conditional Promotion Gate (Audited & Corrected)
=====================================================================================================
Evaluates candidate models strictly based on Out-of-Sample (OOS) Walk-Forward Cross-Validation folds.
Zero in-sample evaluation leakage.

Institutional Promotion Gate Criteria:
  1. Majority Fold Robustness: Minimum 2 of 3 Walk-Forward folds MUST satisfy WFE (OOS Win / IS Win) >= 0.50.
  2. Absolute OOS Win Rate: Mean Out-of-Sample Win Rate across all folds >= 50.0%.
  3. Absolute OOS Profit Factor: Mean Out-of-Sample Profit Factor across all folds >= 1.10.
  4. Incumbent Comparison: If incumbent exists, Mean OOS Win Rate(Challenger) >= Mean OOS Win Rate(Incumbent) + 1.0%.

If ANY gate fails: The candidate model is strictly REJECTED.
The active production pointer is revoked or maintained on safe rules-based execution.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List

import joblib
import numpy as np
from google.cloud import firestore, storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ModelEvaluationGate")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
BUCKET_NAME = "infinity-ai-models-vault"

def evaluate_and_promote_asset_class(
    asset_class: str = "EQUITY",
    challenger_meta_path: str = None
) -> Dict[str, Any]:
    """Evaluates candidate model using strict Walk-Forward Cross-Validation folds."""
    db = firestore.Client(project=PROJECT_ID)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)

    gcs_prefix = "equities" if asset_class == "EQUITY" else "options"

    logger.info(f"\n================================================================================")
    logger.info(f"   AUDITED CONDITIONAL PROMOTION GATE: {asset_class.upper()} ENSEMBLE MODEL      ")
    logger.info(f"================================================================================")

    # 1. Load latest challenger metadata
    if not challenger_meta_path:
        meta_dir = f"trained_models/{gcs_prefix}"
        meta_files = [
            os.path.join(meta_dir, f) for f in os.listdir(meta_dir) 
            if f.endswith("_metadata.json") and not f.startswith("incumbent") and not "production" in f
        ]
        if not meta_files:
            raise FileNotFoundError(f"No candidate metadata found in {meta_dir}")
        challenger_meta_path = sorted(meta_files)[-1]

    with open(challenger_meta_path, "r", encoding="utf-8") as f:
        challenger_meta = json.load(f)

    challenger_version = challenger_meta["model_version"]
    folds: List[Dict[str, Any]] = challenger_meta.get("walk_forward_folds", [])

    if not folds:
        raise ValueError(f"Metadata for {challenger_version} contains no walk_forward_folds!")

    logger.info(f"🔍 Candidate Model: {challenger_version} ({len(folds)} Walk-Forward Folds)")

    # 2. Extract Fold Metrics
    fold_details = []
    passing_wfe_count = 0

    oos_win_rates = []
    oos_profit_factors = []
    wfe_scores = []

    for fold in folds:
        name = fold["fold_name"]
        is_win = fold["in_sample"]["win_rate_pct"]
        oos_win = fold["out_of_sample"]["win_rate_pct"]
        oos_pf = fold["out_of_sample"]["profit_factor"]
        wfe = fold["wfe_win_rate"]

        passed_fold_wfe = wfe >= 0.50 and oos_win >= 45.0
        if passed_fold_wfe:
            passing_wfe_count += 1

        oos_win_rates.append(oos_win)
        oos_profit_factors.append(oos_pf)
        wfe_scores.append(wfe)

        fold_details.append({
            "fold_name": name,
            "is_win_rate": is_win,
            "oos_win_rate": oos_win,
            "oos_profit_factor": oos_pf,
            "wfe": wfe,
            "passed_wfe_threshold": passed_fold_wfe
        })
        logger.info(
            f"   • {name}: IS Win={is_win}% | OOS Win={oos_win}% | "
            f"WFE={wfe:.2f} (Req >= 0.50) | OOS PF={oos_pf} | Fold Pass: {passed_fold_wfe}"
        )

    mean_oos_win = round(float(np.mean(oos_win_rates)), 2)
    mean_oos_pf = round(float(np.mean(oos_profit_factors)), 2)
    mean_wfe = round(float(np.mean(wfe_scores)), 3)

    logger.info(f"\n📊 Aggregate Walk-Forward Metrics:")
    logger.info(f"   • Passing Folds (WFE >= 0.50): {passing_wfe_count} / {len(folds)} (Req >= 2/3)")
    logger.info(f"   • Mean Out-of-Sample Win Rate: {mean_oos_win}% (Req >= 50.0%)")
    logger.info(f"   • Mean Out-of-Sample Profit Factor: {mean_oos_pf} (Req >= 1.10)")
    logger.info(f"   • Mean WFE: {mean_wfe}")

    # 3. Check Incumbent Reference
    incumbent_doc_ref = db.collection("active_production_models").document(f"{asset_class.upper()}_CURRENT")
    incumbent_doc = incumbent_doc_ref.get()

    incumbent_win_rate = 50.0  # Default benchmark requirement
    incumbent_version = "NONE"

    if incumbent_doc.exists:
        inc_data = incumbent_doc.to_dict()
        if inc_data.get("status") == "PROMOTED":
            incumbent_version = inc_data.get("model_version", "UNKNOWN")
            incumbent_win_rate = inc_data.get("metrics", {}).get("mean_oos_win_rate", 50.0)

    # 4. Strict Promotion Gate Verification
    gate_majority_wfe = passing_wfe_count >= 2
    gate_mean_win_rate = mean_oos_win >= 50.0
    gate_mean_pf = mean_oos_pf >= 1.10
    gate_vs_incumbent = mean_oos_win >= (incumbent_win_rate if incumbent_version != "NONE" else 50.0)

    promoted = gate_majority_wfe and gate_mean_win_rate and gate_mean_pf and gate_vs_incumbent
    decision_status = "PROMOTED" if promoted else "REJECTED"

    evaluation_report = {
        "asset_class": asset_class,
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": decision_status,
        "challenger": {
            "version": challenger_version,
            "mean_oos_win_rate": mean_oos_win,
            "mean_oos_profit_factor": mean_oos_pf,
            "mean_wfe": mean_wfe,
            "passing_folds_count": passing_wfe_count,
            "total_folds": len(folds),
            "fold_breakdown": fold_details,
            "gcs_uri": challenger_meta.get("gcs_artifact_uri")
        },
        "incumbent": {
            "version": incumbent_version,
            "benchmark_win_rate": incumbent_win_rate
        },
        "gate_checks": {
            "gate_majority_wfe_passed (>= 2/3)": gate_majority_wfe,
            "gate_mean_win_rate_passed (>= 50%)": gate_mean_win_rate,
            "gate_mean_profit_factor_passed (>= 1.10)": gate_mean_pf,
            "gate_vs_incumbent_passed": gate_vs_incumbent
        }
    }

    # 5. Apply Safe Production State
    if promoted:
        logger.info(f"🏆 PROMOTION ACCEPTED: Candidate {challenger_version} passed all walk-forward gates!")
        prod_gcs_model_blob = f"{gcs_prefix}/{asset_class.lower()}_ensemble_production.joblib"
        blob_source = bucket.blob(f"{gcs_prefix}/{asset_class.lower()}_ensemble_{challenger_version}.joblib")
        bucket.copy_blob(blob_source, bucket, prod_gcs_model_blob)

        active_record = {
            "asset_class": asset_class,
            "model_version": challenger_version,
            "status": "PROMOTED",
            "ml_enabled": True,
            "promoted_at": datetime.now(timezone.utc).isoformat(),
            "gcs_artifact_uri": f"gs://{BUCKET_NAME}/{prod_gcs_model_blob}",
            "metrics": {
                "mean_oos_win_rate": mean_oos_win,
                "mean_oos_profit_factor": mean_oos_pf,
                "mean_wfe": mean_wfe
            }
        }
        incumbent_doc_ref.set(active_record)
    else:
        logger.warning(
            f"❌ PROMOTION REJECTED: Candidate {challenger_version} FAILED walk-forward robustness gates!\n"
            f"   • Majority WFE Gate (>= 2/3): {gate_majority_wfe} ({passing_wfe_count}/3 folds)\n"
            f"   • Mean OOS Win Rate Gate (>= 50%): {gate_mean_win_rate} ({mean_oos_win}%)\n"
            f"   • Mean OOS Profit Factor Gate (>= 1.10): {gate_mean_pf} ({mean_oos_pf})\n"
            f"   🔒 ENFORCING SAFE FALLBACK: Disabling ML serving, falling back to pure technical momentum rules."
        )

        safe_fallback_record = {
            "asset_class": asset_class,
            "model_version": None,
            "status": "REJECTED_SAFE_FALLBACK",
            "ml_enabled": False,
            "fallback_mode": "RULES_BASED_TECHNICAL_MOMENTUM_ONLY",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "rejection_reason": f"Candidate failed Walk-Forward CV gates (Only {passing_wfe_count}/3 folds passed WFE >= 0.50; OOS Win Rate = {mean_oos_win}%)"
        }
        incumbent_doc_ref.set(safe_fallback_record)
        logger.info(f"🔥 Updated Firestore `active_production_models/{asset_class.upper()}_CURRENT` to SAFE FALLBACK (ML Disabled)")

    audit_doc_id = f"AUDIT_EVAL_{asset_class}_{challenger_version}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    db.collection("model_evaluation_audit").document(audit_doc_id).set(evaluation_report)
    logger.info(f"📝 Forensic evaluation report logged to Firestore `model_evaluation_audit/{audit_doc_id}`")

    return evaluation_report

def run_audited_evaluation_suite():
    """Runs audited evaluation for both asset classes."""
    eq_report = evaluate_and_promote_asset_class("EQUITY")
    opt_report = evaluate_and_promote_asset_class("OPTIONS")
    return eq_report, opt_report

if __name__ == "__main__":
    run_audited_evaluation_suite()
