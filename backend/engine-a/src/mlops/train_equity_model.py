"""
InfinityAI.Pro — Institutional Equity Tri-Model Walk-Forward Training Engine
=============================================================================
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

import joblib
import numpy as np
import pandas as pd
from google.cloud import bigquery, storage, firestore
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, brier_score_loss

# Add paths
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from ensemble_definition import EquityEnsembleModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EquityModelTrainer")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
BUCKET_NAME = "infinity-ai-models-vault"
TABLE_ID = f"{PROJECT_ID}.market_data.equity_training_features"

FEATURE_COLS = [
    "rsi_14", "adx_14", "atr_14", "range_pct", "intraday_return_pct",
    "sma_20_dist_pct", "sma_50_dist_pct", "volatility_20", "volume_ratio_20"
]

def evaluate_fold(model: EquityEnsembleModel, X: np.ndarray, y: np.ndarray, returns: np.ndarray) -> Dict[str, float]:
    """Computes quantitative performance metrics for a split."""
    y_clean = np.asarray(y, dtype=np.int32)
    probs = model.predict_proba(X)
    preds = (probs >= 0.50).astype(int)

    acc = accuracy_score(y_clean, preds)
    prec = precision_score(y_clean, preds, zero_division=0)
    rec = recall_score(y_clean, preds, zero_division=0)
    auc = roc_auc_score(y_clean, probs) if len(np.unique(y_clean)) > 1 else 0.5
    brier = brier_score_loss(y_clean, probs)

    trade_mask = preds == 1
    if trade_mask.sum() > 0:
        traded_returns = np.asarray(returns)[trade_mask]
        win_rate = (traded_returns > 0).mean() * 100.0
        mean_return = traded_returns.mean()
        pos_rets = traded_returns[traded_returns > 0].sum()
        neg_rets = abs(traded_returns[traded_returns < 0].sum())
        profit_factor = round(pos_rets / (neg_rets + 1e-9), 2)
    else:
        win_rate = 0.0
        mean_return = 0.0
        profit_factor = 0.0

    return {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "roc_auc": round(float(auc), 4),
        "brier_score": round(float(brier), 4),
        "win_rate_pct": round(float(win_rate), 2),
        "mean_return_pct": round(float(mean_return), 2),
        "profit_factor": float(profit_factor),
        "trade_count": int(trade_mask.sum())
    }

def run_walk_forward_training() -> Dict[str, Any]:
    """Runs Walk-Forward Validation and trains production ensemble."""
    bq_client = bigquery.Client(project=PROJECT_ID)
    db = firestore.Client(project=PROJECT_ID)
    storage_client = storage.Client(project=PROJECT_ID)

    logger.info("📥 Pulling Equity features from BigQuery...")
    query = f"SELECT * FROM `{TABLE_ID}` ORDER BY bar_date ASC"
    df = bq_client.query(query).to_dataframe()
    df["bar_date"] = pd.to_datetime(df["bar_date"])
    logger.info(f"   • Loaded {len(df):,} total equity training records ({df['bar_date'].min().date()} -> {df['bar_date'].max().date()}).")

    folds = [
        {"name": "Fold 1 (2024 -> Q1 2025)", "train_end": "2024-12-31", "test_start": "2025-01-01", "test_end": "2025-03-31"},
        {"name": "Fold 2 (2024–H1 2025 -> Q3 2025)", "train_end": "2025-06-30", "test_start": "2025-07-01", "test_end": "2025-09-30"},
        {"name": "Fold 3 (2024–2025 -> 2026 Live)", "train_end": "2025-12-31", "test_start": "2026-01-01", "test_end": "2026-08-31"}
    ]

    fold_results = []
    logger.info("\n🧪 Starting 3-Fold Walk-Forward Cross-Validation (Equities)...")

    for fold in folds:
        df_train = df[df["bar_date"] <= fold["train_end"]]
        df_test = df[(df["bar_date"] >= fold["test_start"]) & (df["bar_date"] <= fold["test_end"])]

        X_train = df_train[FEATURE_COLS].to_numpy(dtype=np.float32)
        y_train = np.asarray(df_train["label_win"].values, dtype=np.int32)
        ret_train = np.asarray(df_train["realized_return_pct"].values, dtype=np.float32)

        X_test = df_test[FEATURE_COLS].to_numpy(dtype=np.float32)
        y_test = np.asarray(df_test["label_win"].values, dtype=np.int32)
        ret_test = np.asarray(df_test["realized_return_pct"].values, dtype=np.float32)

        model = EquityEnsembleModel()
        model.fit(X_train, y_train)

        is_metrics = evaluate_fold(model, X_train, y_train, ret_train)
        oos_metrics = evaluate_fold(model, X_test, y_test, ret_test)

        wfe_win_rate = round(oos_metrics["win_rate_pct"] / (is_metrics["win_rate_pct"] + 1e-9), 3)
        wfe_return = round(oos_metrics["mean_return_pct"] / (is_metrics["mean_return_pct"] + 1e-9), 3)

        passed_wfe = wfe_win_rate >= 0.65 and oos_metrics["win_rate_pct"] >= 45.0

        res = {
            "fold_name": fold["name"],
            "train_samples": len(df_train),
            "test_samples": len(df_test),
            "in_sample": is_metrics,
            "out_of_sample": oos_metrics,
            "wfe_win_rate": wfe_win_rate,
            "wfe_return": wfe_return,
            "wfe_passed": passed_wfe
        }
        fold_results.append(res)
        logger.info(
            f"   • {fold['name']}: IS Win={is_metrics['win_rate_pct']}% | "
            f"OOS Win={oos_metrics['win_rate_pct']}% | WFE={wfe_win_rate:.2f} | "
            f"OOS ProfitFactor={oos_metrics['profit_factor']} | Pass={passed_wfe}"
        )

    logger.info("\n🏆 Training Final Production Equity Ensemble on Full Dataset...")
    X_full = df[FEATURE_COLS].to_numpy(dtype=np.float32)
    y_full = np.asarray(df["label_win"].values, dtype=np.int32)
    prod_model = EquityEnsembleModel()
    prod_model.fit(X_full, y_full)

    version = f"v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    os.makedirs("trained_models/equities", exist_ok=True)
    local_artifact_path = f"trained_models/equities/equity_ensemble_{version}.joblib"
    local_meta_path = f"trained_models/equities/equity_ensemble_{version}_metadata.json"

    feature_importances = {}
    for name, m in prod_model.models.items():
        if hasattr(m, "feature_importances_"):
            feature_importances[name] = dict(zip(FEATURE_COLS, [round(float(x), 4) for x in m.feature_importances_]))

    metadata = {
        "model_version": version,
        "asset_class": "EQUITY",
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_training_samples": len(df),
        "unique_symbols": int(df["symbol"].nunique()),
        "feature_cols": FEATURE_COLS,
        "ensemble_weights": prod_model.weights,
        "feature_importances": feature_importances,
        "walk_forward_folds": fold_results,
        "mean_oos_win_rate": round(float(np.mean([f["out_of_sample"]["win_rate_pct"] for f in fold_results])), 2),
        "mean_oos_profit_factor": round(float(np.mean([f["out_of_sample"]["profit_factor"] for f in fold_results])), 2),
        "mean_wfe": round(float(np.mean([f["wfe_win_rate"] for f in fold_results])), 3),
        "gcs_artifact_uri": f"gs://{BUCKET_NAME}/equities/equity_ensemble_{version}.joblib"
    }

    joblib.dump(prod_model, local_artifact_path)
    with open(local_meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_model = bucket.blob(f"equities/equity_ensemble_{version}.joblib")
        blob_model.upload_from_filename(local_artifact_path)
        blob_meta = bucket.blob(f"equities/equity_ensemble_{version}_metadata.json")
        blob_meta.upload_from_filename(local_meta_path)
        logger.info(f"☁️ Uploaded Equity Ensemble to GCS: {metadata['gcs_artifact_uri']}")
    except Exception as e:
        logger.error(f"Failed uploading to GCS: {e}")

    try:
        db.collection("model_training_runs").document(f"EQUITY_{version}").set(metadata)
        logger.info(f"🔥 Registered training run in Firestore `model_training_runs/EQUITY_{version}`")
    except Exception as e:
        logger.error(f"Failed logging to Firestore: {e}")

    logger.info("🎉 Equity Model Training & Walk-Forward Cross-Validation Completed!")
    return metadata

if __name__ == "__main__":
    run_walk_forward_training()
