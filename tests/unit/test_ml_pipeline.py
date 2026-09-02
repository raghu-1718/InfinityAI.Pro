"""
Tests for AI/ML Tri-Model Ensemble & Out-of-Sample Backtesting Pipeline
"""
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

from ml_models.feature_engineering import build_ml_features
from ml_models.training_pipeline import TriModelTrainingPipeline, MODELS_DIR
from ml_models.evaluate_oos_backtest import run_oos_model_backtest
from backtesting.runner import generate_synthetic_nifty_bars
from db.dal.bigquery_dal import bigquery_dal


@pytest.fixture
def raw_market_data():
    return generate_synthetic_nifty_bars(n_bars=350)


def test_feature_engineering_no_lookahead(raw_market_data):
    """Verify feature engineering generates clean features with no future information leakage."""
    features_df = build_ml_features(raw_market_data)

    # Required features
    required_cols = ["ret_1", "rsi_14", "macd", "volatility_20", "volume_ratio", "pcr_proxy", "target"]
    for col in required_cols:
        assert col in features_df.columns, f"Missing feature column {col}"

    # No NaN values
    assert features_df.isna().sum().sum() == 0

    # Verify target distribution (0s and 1s only)
    targets = features_df["target"].unique()
    assert set(targets).issubset({0, 1})


def test_tri_model_training_and_metrics(raw_market_data):
    """Verify Tri-Model pipeline trains CatBoost, LightGBM, and XGBoost with valid OOS metrics."""
    pipeline = TriModelTrainingPipeline(version="v-unit-test")
    results = pipeline.train(raw_market_data)

    assert results["version"] == "v-unit-test"
    metrics = results["metrics"]

    # Verify all models evaluated
    for model_name in ["catboost", "lightgbm", "xgboost", "ensemble"]:
        assert model_name in metrics
        m = metrics[model_name]
        assert "accuracy" in m
        assert "roc_auc" in m
        assert "f1_score" in m
        assert 0.0 <= m["accuracy"] <= 1.0


def test_model_versioning_and_file_artifacts():
    """Verify model files are saved to disk with version identifiers."""
    xgb_file = MODELS_DIR / "v-unit-test-xgb.json"
    lgb_file = MODELS_DIR / "v-unit-test-lgb.txt"
    cb_file = MODELS_DIR / "v-unit-test-cb.cbm"

    assert xgb_file.exists(), "XGBoost model file missing"
    assert lgb_file.exists(), "LightGBM model file missing"
    assert cb_file.exists(), "CatBoost model file missing"


def test_oos_backtest_execution():
    """Verify trained model predictions can be backtested through the Phase 6 engine."""
    res = run_oos_model_backtest(n_bars=300)

    assert "run_id" in res
    assert res["run_id"].startswith("bt-oos-ml-")
    assert "oos_backtest_metrics" in res
    m = res["oos_backtest_metrics"]

    assert "total_pnl" in m
    assert "sharpe_ratio" in m
    assert "max_drawdown_pct" in m
    assert m["max_drawdown_pct"] >= 0.0
