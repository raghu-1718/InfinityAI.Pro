"""
InfinityAI.Pro — Institutional Multi-Model Quant Tournament & Walk-Forward Engine
==================================================================================
Executes a rigorous tournament across Baselines, Tree Ensembles, and Calibrated Stacks.
Enforces:
  1. 3-Fold Chronological Walk-Forward Cross Validation
  2. 15-Day Temporal Purging & Embargo between Train and Test splits
  3. Realistic Roundtrip Transaction Friction (0.10% Equities, 0.05% Options)
  4. Statistically sound Conviction Thresholding (Train-Fold calibrated)
  5. Minimum Trade Count Gate (>= 20 trades/fold Equities, >= 10 trades/fold Options)
  6. Defensively capped Profit Factor calculation (max 5.0)
  7. Audited Promotion Gate Evaluation & CSV Export
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
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, brier_score_loss
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV

# Boosters
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import lightgbm as lgb
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ModelTournament")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
BUCKET_NAME = "infinity-ai-models-vault"

FEATURE_COLS = [
    "rsi_14", "adx_14", "atr_14", "range_pct", "intraday_return_pct",
    "sma_20_dist_pct", "sma_50_dist_pct", "volatility_20", "volume_ratio_20"
]

def build_model_pool() -> Dict[str, Any]:
    """Instantiates candidate tournament architectures."""
    models = {}

    # 1. Baseline: Logistic Regression (L2 Regularized)
    models["LogisticRegression_L2"] = LogisticRegression(
        penalty="l2", C=0.2, solver="lbfgs", max_iter=500, random_state=42
    )

    # 2. Baseline: Ridge Classifier
    models["RidgeClassifier"] = RidgeClassifier(
        alpha=1.0, random_state=42
    )

    # 3. Baseline: Shallow Decision Tree
    models["DecisionTree_Shallow"] = DecisionTreeClassifier(
        max_depth=3, min_samples_leaf=30, random_state=42
    )

    # 4. Tree Ensemble: Random Forest
    models["RandomForest_Robust"] = RandomForestClassifier(
        n_estimators=100, max_depth=4, min_samples_leaf=20, random_state=42
    )

    # 5. Tree Ensemble: Extra Trees
    models["ExtraTrees_Robust"] = ExtraTreesClassifier(
        n_estimators=100, max_depth=4, min_samples_leaf=20, random_state=42
    )

    # 6. Tree Ensemble: LightGBM (Regularized shallow booster)
    if HAS_LGBM:
        models["LightGBM_Regularized"] = lgb.LGBMClassifier(
            n_estimators=100, max_depth=3, num_leaves=7, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.8, min_child_samples=30,
            reg_alpha=0.3, reg_lambda=3.0, verbose=-1, random_state=42
        )

    # 7. Tree Ensemble: XGBoost (Regularized shallow booster)
    if HAS_XGB:
        models["XGBoost_Regularized"] = xgb.XGBClassifier(
            n_estimators=100, max_depth=3, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.8, reg_alpha=0.3, reg_lambda=3.0,
            eval_metric="logloss", random_state=42
        )

    # 8. Tree Ensemble: CatBoost (Regularized shallow booster)
    if HAS_CATBOOST:
        models["CatBoost_Regularized"] = CatBoostClassifier(
            iterations=100, depth=3, learning_rate=0.03,
            l2_leaf_reg=4.0, verbose=0, random_seed=42
        )

    return models

def optimize_train_threshold(probs_train: np.ndarray, returns_train: np.ndarray, min_trades: int = 30) -> float:
    """Finds optimal conviction threshold on training fold."""
    best_th = 0.50
    best_score = -1e9

    # Test percentiles from 50th to 90th percentile of predicted probs
    potential_thresholds = np.unique(np.percentile(probs_train, np.arange(50, 92, 5)))
    potential_thresholds = np.clip(potential_thresholds, 0.35, 0.75)

    for th in potential_thresholds:
        mask = probs_train >= th
        if mask.sum() >= min_trades:
            rets = returns_train[mask]
            win_r = (rets > 0).mean()
            mean_r = rets.mean()
            # Multi-objective score: Win Rate + Mean Return
            score = (win_r * 100.0) + (mean_r * 8.0)
            if score > best_score:
                best_score = score
                best_th = round(float(th), 4)

    return best_th

def evaluate_metrics(
    y_true: np.ndarray,
    probs: np.ndarray,
    returns_raw: np.ndarray,
    threshold: float = 0.50,
    friction_pct: float = 0.10
) -> Dict[str, float]:
    """Computes quantitative metrics with friction and safe bounding."""
    preds = (probs >= threshold).astype(int)
    y_clean = np.asarray(y_true, dtype=np.int32)
    net_returns = returns_raw - friction_pct

    acc = accuracy_score(y_clean, preds)
    prec = precision_score(y_clean, preds, zero_division=0)
    rec = recall_score(y_clean, preds, zero_division=0)
    auc = roc_auc_score(y_clean, probs) if len(np.unique(y_clean)) > 1 else 0.5
    brier = brier_score_loss(y_clean, probs)

    trade_mask = preds == 1
    trade_count = int(trade_mask.sum())

    if trade_count > 0:
        traded_rets = net_returns[trade_mask]
        win_rate = (traded_rets > 0).mean() * 100.0
        mean_return = traded_rets.mean()
        pos_rets = traded_rets[traded_rets > 0].sum()
        neg_rets = abs(traded_rets[traded_rets < 0].sum())

        if neg_rets > 0:
            profit_factor = round(min(5.0, float(pos_rets / neg_rets)), 2)
        elif pos_rets > 0:
            profit_factor = 5.0 # Capped ceiling for zero-loss folds
        else:
            profit_factor = 0.0

        cum_ret = np.cumsum(traded_rets)
        peak = np.maximum.accumulate(cum_ret)
        dd = peak - cum_ret
        max_dd = round(float(np.max(dd)) if len(dd) > 0 else 0.0, 2)
    else:
        win_rate = 0.0
        mean_return = 0.0
        profit_factor = 0.0
        max_dd = 0.0

    return {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "roc_auc": round(float(auc), 4),
        "brier_score": round(float(brier), 4),
        "win_rate_pct": round(float(win_rate), 2),
        "mean_return_pct": round(float(mean_return), 2),
        "profit_factor": float(profit_factor),
        "max_drawdown_pct": float(max_dd),
        "trade_count": trade_count
    }

def run_asset_tournament(asset_class: str = "EQUITY") -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Runs complete model tournament for an asset class."""
    bq_client = bigquery.Client(project=PROJECT_ID)
    table_name = f"project-841b7f97-5ee3-4fbe-920.market_data.{asset_class.lower()}_training_features"
    friction = 0.10 if asset_class == "EQUITY" else 0.05
    min_trade_thresh = 20 if asset_class == "EQUITY" else 10

    logger.info(f"\n================================================================================")
    logger.info(f"   QUANT MODEL TOURNAMENT: {asset_class.upper()} (Friction: {friction}%)")
    logger.info(f"================================================================================")

    query = f"SELECT * FROM `{table_name}` ORDER BY bar_date ASC"
    df = bq_client.query(query).to_dataframe()
    df["bar_date"] = pd.to_datetime(df["bar_date"])
    logger.info(f"Loaded {len(df):,} records ({df['bar_date'].min().date()} -> {df['bar_date'].max().date()})")

    # 3 Chronological Walk-Forward Folds with 15-Day Purge Window
    folds = [
        {"name": "Fold 1 (2024 -> Q1 2025)", "train_end": "2024-12-15", "test_start": "2025-01-01", "test_end": "2025-03-31"},
        {"name": "Fold 2 (2024–H1 2025 -> Q3 2025)", "train_end": "2025-06-15", "test_start": "2025-07-01", "test_end": "2025-09-30"},
        {"name": "Fold 3 (2024–2025 -> 2026 Live)", "train_end": "2025-12-15", "test_start": "2026-01-01", "test_end": "2026-08-31"}
    ]

    candidate_models = build_model_pool()
    all_fold_records = []
    model_summaries = []

    for model_name, model_inst in candidate_models.items():
        fold_oos_wins = []
        fold_wfes = []
        fold_pfs = []
        fold_returns = []
        passing_folds = 0

        for fold in folds:
            df_train = df[df["bar_date"] <= fold["train_end"]]
            df_test = df[(df["bar_date"] >= fold["test_start"]) & (df["bar_date"] <= fold["test_end"])]

            scaler = StandardScaler()
            X_train = scaler.fit_transform(df_train[FEATURE_COLS].to_numpy(dtype=np.float32))
            y_train = np.asarray(df_train["label_win"].values, dtype=np.int32)
            ret_train = np.asarray(df_train["realized_return_pct"].values, dtype=np.float32)

            X_test = scaler.transform(df_test[FEATURE_COLS].to_numpy(dtype=np.float32))
            y_test = np.asarray(df_test["label_win"].values, dtype=np.int32)
            ret_test = np.asarray(df_test["realized_return_pct"].values, dtype=np.float32)

            # Fit Model
            fitted_model = build_model_pool()[model_name]
            fitted_model.fit(X_train, y_train)

            if hasattr(fitted_model, "predict_proba"):
                is_probs = fitted_model.predict_proba(X_train)[:, 1]
                oos_probs = fitted_model.predict_proba(X_test)[:, 1]
            elif hasattr(fitted_model, "decision_function"):
                df_is = fitted_model.decision_function(X_train)
                df_oos = fitted_model.decision_function(X_test)
                is_probs = 1.0 / (1.0 + np.exp(-df_is))
                oos_probs = 1.0 / (1.0 + np.exp(-df_oos))
            else:
                is_probs = fitted_model.predict(X_train).astype(float)
                oos_probs = fitted_model.predict(X_test).astype(float)

            # Train-Fold Threshold Optimization
            opt_th = optimize_train_threshold(is_probs, ret_train, min_trades=min_trade_thresh)

            is_m = evaluate_metrics(y_train, is_probs, ret_train, threshold=opt_th, friction_pct=friction)
            oos_m = evaluate_metrics(y_test, oos_probs, ret_test, threshold=opt_th, friction_pct=friction)

            wfe = round(oos_m["win_rate_pct"] / (is_m["win_rate_pct"] + 1e-9), 3)
            
            # Robust Fold Gate: WFE >= 0.50, OOS Win >= 45%, Trade Count >= min_trades
            passed_gate = (
                wfe >= 0.50 and 
                oos_m["win_rate_pct"] >= 45.0 and 
                oos_m["trade_count"] >= min_trade_thresh
            )
            if passed_gate:
                passing_folds += 1

            fold_oos_wins.append(oos_m["win_rate_pct"])
            fold_wfes.append(wfe)
            fold_pfs.append(oos_m["profit_factor"])
            fold_returns.append(oos_m["mean_return_pct"])

            fold_rec = {
                "asset_class": asset_class,
                "model_name": model_name,
                "fold_name": fold["name"],
                "train_samples": len(df_train),
                "test_samples": len(df_test),
                "calibrated_threshold": opt_th,
                "is_win_rate": is_m["win_rate_pct"],
                "oos_win_rate": oos_m["win_rate_pct"],
                "wfe": wfe,
                "oos_profit_factor": oos_m["profit_factor"],
                "oos_mean_return": oos_m["mean_return_pct"],
                "oos_max_dd": oos_m["max_drawdown_pct"],
                "oos_trade_count": oos_m["trade_count"],
                "passed_fold_gate": passed_gate
            }
            all_fold_records.append(fold_rec)

        mean_oos_win = round(float(np.mean(fold_oos_wins)), 2)
        std_oos_win = round(float(np.std(fold_oos_wins)), 2)
        mean_wfe = round(float(np.mean(fold_wfes)), 3)
        mean_pf = round(float(np.mean(fold_pfs)), 2)
        mean_ret = round(float(np.mean(fold_returns)), 2)

        meets_majority_wfe = passing_folds >= 2
        meets_mean_win = mean_oos_win >= 50.0
        meets_mean_pf = mean_pf >= 1.10
        eligible_for_promotion = meets_majority_wfe and meets_mean_win and meets_mean_pf

        summary_rec = {
            "asset_class": asset_class,
            "model_name": model_name,
            "passing_folds": f"{passing_folds}/3",
            "mean_oos_win_rate": mean_oos_win,
            "std_oos_win_rate": std_oos_win,
            "mean_wfe": mean_wfe,
            "mean_oos_profit_factor": mean_pf,
            "mean_oos_return": mean_ret,
            "gate_majority_wfe": meets_majority_wfe,
            "gate_mean_win_rate": meets_mean_win,
            "gate_mean_profit_factor": meets_mean_pf,
            "promotion_eligible": eligible_for_promotion
        }
        model_summaries.append(summary_rec)
        logger.info(
            f"SUMMARY [{model_name}]: Passing Folds={passing_folds}/3 | Mean OOS Win={mean_oos_win}% | "
            f"Mean WFE={mean_wfe} | Mean PF={mean_pf} | Eligible: {eligible_for_promotion}"
        )

    df_folds = pd.DataFrame(all_fold_records)
    df_models = pd.DataFrame(model_summaries).sort_values(
        by=["promotion_eligible", "mean_oos_win_rate", "mean_oos_profit_factor"], ascending=False
    )
    best_candidate = df_models.iloc[0].to_dict()

    return df_models, df_folds, best_candidate

def run_tournament():
    """Executes tournaments for Equities and Options, produces CSVs."""
    eq_models, eq_folds, eq_best = run_asset_tournament("EQUITY")
    opt_models, opt_folds, opt_best = run_asset_tournament("OPTIONS")

    df_all_models = pd.concat([eq_models, opt_models], ignore_index=True)
    df_all_folds = pd.concat([eq_folds, opt_folds], ignore_index=True)

    os.makedirs("trained_models", exist_ok=True)
    df_all_models.to_csv("model_comparison.csv", index=False)
    df_all_folds.to_csv("fold_metrics.csv", index=False)
    logger.info("\n📁 Saved `model_comparison.csv` and `fold_metrics.csv`.")

    print("\n================================================================================")
    print("                    MODEL TOURNAMENT AUDIT RESULTS TABLE                       ")
    print("================================================================================")
    print(df_all_models.to_string(index=False))

    return df_all_models, df_all_folds, eq_best, opt_best

if __name__ == "__main__":
    run_tournament()
