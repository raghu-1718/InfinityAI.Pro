"""
InfinityAI.Pro — Verification Test Suite for Institutional AI/ML Optimizations
=============================================================================
Covers:
1. test_triple_barrier_labeling_bounds: Confirms ATR upper/lower/vertical resolution and sample weights.
2. test_gex_and_obi_feature_calculation: Verifies edge cases (zero OI, empty order book, NaN handling).
3. test_cpcv_purging_and_embargo_overlap: Asserts zero index overlap between training labels and test frames.
4. test_onnx_int8_latency_and_correlation: Asserts inference runtime < 2.0ms and r >= 0.990.
5. test_gemini_pydantic_schema_validation: Validates mock Gemini payload complies strictly with MacroIntelligencePayload.
6. test_psi_drift_triggers_alert: Tests PSI calculation and alert boundary conditions.
"""

import sys
import os
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import pytest
import numpy as np
import pandas as pd
from pydantic import ValidationError

# Ensure engine-b root is in python path
ENGINE_B_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ENGINE_B_ROOT not in sys.path:
    sys.path.insert(0, ENGINE_B_ROOT)

from src.training.labeling_utils import (
    calculate_atr,
    apply_triple_barrier_labeling
)
from src.training.microstructure_features import (
    calculate_gamma_exposure,
    calculate_pcr_momentum,
    calculate_iv_skew,
    calculate_order_book_imbalance,
    enrich_dataset_with_microstructure
)
from src.models.cpcv_evaluator import CombinatorialPurgedCV
from src.models.regime_adaptive_moe import RegimeAdaptiveMoE
from src.inference.onnx_inference_accelerator import ONNXInferenceAccelerator
from src.services.macro_intelligence import (
    MacroIntelligencePayload,
    MacroIntelligenceEngine
)
from src.mlops.psi_drift_watchdog import DualMetricDriftWatchdog
from src.mlops.hot_reload import CanaryModelVaultManager


# ============================================================================
# 1. TRIPLE BARRIER LABELING & SAMPLE WEIGHTING TEST
# ============================================================================
def test_triple_barrier_labeling_bounds():
    """
    Confirms ATR upper/lower/vertical resolution, target values {0, 1, 2},
    and returns-scaled sample weights bounded in [0.2, 5.0].
    """
    n_bars = 60
    prices = [22500.0]
    # Create synthetic price trajectory: upward surge, followed by drop, followed by flat
    for i in range(1, n_bars):
        if i < 20:
            prices.append(prices[-1] + 15.0)  # Strong upward trend
        elif i < 40:
            prices.append(prices[-1] - 15.0)  # Strong downward trend
        else:
            prices.append(prices[-1] + 0.5 * (1 if i % 2 == 0 else -1))  # Flat chop

    df = pd.DataFrame({
        "close": prices,
        "high": [p + 5.0 for p in prices],
        "low": [p - 5.0 for p in prices],
        "volume": [1000] * n_bars
    })

    labeled_df, sample_weights = apply_triple_barrier_labeling(
        df,
        pt_multiplier=1.5,
        sl_multiplier=1.0,
        max_holding_bars=10
    )

    # Assertions
    assert "target" in labeled_df.columns
    assert "sample_weight" in labeled_df.columns
    assert "barrier_hit" in labeled_df.columns

    # Target values must be subset of {0 (SELL), 1 (HOLD), 2 (BUY)}
    targets = labeled_df["target"].unique()
    for t in targets:
        assert t in {0, 1, 2}

    # Barrier hits must be subset of {'UPPER', 'LOWER', 'VERTICAL'}
    barrier_hits = labeled_df["barrier_hit"].unique()
    for b in barrier_hits:
        assert b in {"UPPER", "LOWER", "VERTICAL"}

    # Early upward bars should hit UPPER barrier -> target = 2
    assert labeled_df.loc[0, "target"] == 2
    assert labeled_df.loc[0, "barrier_hit"] == "UPPER"

    # Middle downward bars should hit LOWER barrier -> target = 0
    assert labeled_df.loc[22, "target"] == 0
    assert labeled_df.loc[22, "barrier_hit"] == "LOWER"

    # Later bars in chop with small moves should hit VERTICAL barrier -> target = 1
    assert labeled_df.loc[45, "barrier_hit"] == "VERTICAL"
    assert labeled_df.loc[45, "target"] == 1

    # Weights must be bounded within institutional clamps [0.20, 5.0]
    weights_arr = sample_weights.values
    assert np.all(weights_arr >= 0.20)
    assert np.all(weights_arr <= 5.0)
    assert np.all(~np.isnan(weights_arr))
    # Mean weight is approximately 1.0
    assert 0.8 <= np.mean(weights_arr) <= 1.2


# ============================================================================
# 2. OPTIONS MICROSTRUCTURE & EDGE CASE TEST
# ============================================================================
def test_gex_and_obi_feature_calculation():
    """
    Verifies microstructure metrics (GEX, OBI, PCR momentum, IV Skew)
    under normal conditions and extreme edge cases (zero OI, empty book, NaNs).
    """
    spot = 22500.0

    # 1. Edge Case: Empty options dataframe
    df_empty = pd.DataFrame(columns=["strike_price", "open_interest", "implied_volatility", "option_type"])
    gex_empty = calculate_gamma_exposure(df_empty, spot_price=spot)
    assert gex_empty == 0.0

    skew_empty = calculate_iv_skew(df_empty, spot_price=spot)
    assert skew_empty == 0.0

    # 2. Edge Case: Zero OI options dataframe
    df_zero_oi = pd.DataFrame([
        {"strike_price": 22400.0, "open_interest": 0, "implied_volatility": 0.16, "option_type": "PE"},
        {"strike_price": 22600.0, "open_interest": 0, "implied_volatility": 0.14, "option_type": "CE"},
    ])
    gex_zero = calculate_gamma_exposure(df_zero_oi, spot_price=spot)
    assert gex_zero == 0.0

    # 3. Normal Option Chain GEX & Skew
    df_valid = pd.DataFrame([
        {"strike_price": 22400.0, "open_interest": 50000, "implied_volatility": 0.18, "option_type": "PE"},
        {"strike_price": 22600.0, "open_interest": 45000, "implied_volatility": 0.14, "option_type": "CE"},
    ])
    gex_valid = calculate_gamma_exposure(df_valid, spot_price=spot)
    assert isinstance(gex_valid, float)
    assert not np.isnan(gex_valid)

    skew_valid = calculate_iv_skew(df_valid, spot_price=spot)
    assert skew_valid == pytest.approx(0.04, abs=0.001)  # 0.18 - 0.14 = 0.04

    # 4. Order Book Imbalance (OBI) Bounds & Edge Cases
    # Empty book: 0 bids, 0 asks -> 0.0
    obi_zero = calculate_order_book_imbalance(0.0, 0.0)
    assert obi_zero == 0.0

    # Equal liquidity -> 0.0
    obi_equal = calculate_order_book_imbalance(10000.0, 10000.0)
    assert obi_equal == 0.0

    # Extreme buy pressure -> +1.0
    obi_buy = calculate_order_book_imbalance(50000.0, 0.0)
    assert obi_buy == 1.0

    # Heavy sell pressure -> bounded in [-1.0, 0.0)
    obi_sell = calculate_order_book_imbalance(1000.0, 4000.0)
    assert obi_sell == -0.6
    assert -1.0 <= obi_sell <= 1.0

    # 5. Full Enrichment with NaN handling
    raw_df = pd.DataFrame({
        "close": [22500.0 + i for i in range(30)],
        "volume": [1000 + i * 50 for i in range(30)],
    })
    enriched_df, added_cols = enrich_dataset_with_microstructure(raw_df, df_options=df_valid)
    assert "gex" in enriched_df.columns
    assert "obi" in enriched_df.columns
    assert "pcr_momentum" in enriched_df.columns
    assert "iv_skew" in enriched_df.columns
    # Ensure zero remaining NaNs in added microstructure columns
    for col in added_cols:
        assert not enriched_df[col].isna().any()
        assert not np.isinf(enriched_df[col]).any()


# ============================================================================
# 3. CPCV PURGING & EMBARGO OVERLAP TEST
# ============================================================================
def test_cpcv_purging_and_embargo_overlap():
    """
    Asserts zero index overlap between training labels and test frames,
    confirming that both the left-purge holding window and post-test embargo
    strictly prevent serial correlation leakage.
    """
    n_samples = 250
    holding_bars = 15
    embargo_pct = 0.04  # 4% of 250 = 10 bars embargo
    n_splits = 5

    X = np.arange(n_samples).reshape(-1, 1)
    cpcv = CombinatorialPurgedCV(n_splits=n_splits, embargo_pct=embargo_pct, holding_bars=holding_bars)

    embargo_bars = max(1, int(n_samples * embargo_pct))
    fold_count = 0

    for train_idx, test_idx in cpcv.split(X):
        fold_count += 1
        train_set = set(train_idx)
        test_set = set(test_idx)

        # 1. Assert zero direct overlap between train and test
        assert len(train_set.intersection(test_set)) == 0

        test_start = min(test_idx)
        test_end = max(test_idx) + 1

        # 2. Assert Purge Window: No train index in [test_start - holding_bars, test_start)
        purge_left = max(0, test_start - holding_bars)
        purged_indices = set(range(purge_left, test_start))
        assert len(train_set.intersection(purged_indices)) == 0

        # 3. Assert Embargo Window: No train index in [test_end, test_end + embargo_bars)
        embargo_right = min(n_samples, test_end + embargo_bars)
        embargoed_indices = set(range(test_end, embargo_right))
        assert len(train_set.intersection(embargoed_indices)) == 0

    assert fold_count == n_splits

    # 4. Assert CPCV metric evaluation
    y_true = np.array([2, 0, 1, 2, 0, 1, 2, 2, 0, 1])
    y_pred = np.array([2, 0, 1, 2, 0, 1, 2, 1, 0, 1])
    y_proba = np.array([
        [0.05, 0.15, 0.80],
        [0.75, 0.20, 0.05],
        [0.10, 0.80, 0.10],
        [0.05, 0.15, 0.80],
        [0.70, 0.20, 0.10],
        [0.10, 0.70, 0.20],
        [0.05, 0.15, 0.80],
        [0.15, 0.50, 0.35],
        [0.80, 0.15, 0.05],
        [0.10, 0.75, 0.15]
    ])
    metrics = CombinatorialPurgedCV.evaluate_cpcv_metrics(y_true, y_pred, y_proba)
    assert "brier_score" in metrics
    assert "sharpe_ratio" in metrics
    assert "sortino_ratio" in metrics
    assert metrics["brier_score"] >= 0.0
    assert metrics["brier_score"] <= 1.0


# ============================================================================
# 4. ONNX INT8 LATENCY & NUMERICAL PRECISION GATE TEST
# ============================================================================
def test_onnx_int8_latency_and_correlation():
    """
    Asserts median inference runtime < 2.0ms and Pearson correlation r >= 0.990
    with max absolute probability divergence <= 0.015 across 10,000 synthetic test ticks.
    """
    accelerator = ONNXInferenceAccelerator()

    # 1. Numerical Precision Gate with 10,000 ticks
    np.random.seed(42)
    n_ticks = 10000
    fp32_probas = np.random.uniform(0.1, 0.9, size=(n_ticks, 3))
    # Normalize rows
    fp32_probas /= fp32_probas.sum(axis=1, keepdims=True)

    # Simulated INT8 dynamic quantization with minor precision variance (bounded <= 0.010)
    int8_probas = fp32_probas + np.random.normal(0.0, 0.002, size=(n_ticks, 3))
    int8_probas = np.clip(int8_probas, 0.01, 0.99)
    int8_probas /= int8_probas.sum(axis=1, keepdims=True)

    gate_result = accelerator.verify_precision_gate(
        fp32_probas,
        int8_probas,
        min_correlation=0.990,
        max_abs_divergence=0.015
    )

    assert gate_result["passed"] is True
    assert gate_result["pearson_correlation"] >= 0.990
    assert gate_result["max_absolute_divergence"] <= 0.015

    # 2. Gate Rejection verification (corrupted / drifted model)
    corrupted_probas = fp32_probas + np.random.normal(0.0, 0.05, size=(n_ticks, 3))
    fail_gate = accelerator.verify_precision_gate(
        fp32_probas,
        corrupted_probas,
        min_correlation=0.990,
        max_abs_divergence=0.015
    )
    assert fail_gate["passed"] is False

    # 3. Latency Benchmark: Sub-2ms per tick verification
    benchmark_res = accelerator.benchmark_latency(n_ticks=200)
    assert benchmark_res["median_latency_ms"] < 2.0
    assert benchmark_res["is_compliant_sub_2ms"] is True


# ============================================================================
# 5. GEMINI PYDANTIC SCHEMA VALIDATION TEST
# ============================================================================
def test_gemini_pydantic_schema_validation():
    """
    Validates mock Gemini payload complies strictly with MacroIntelligencePayload
    without regex parsing, and verifies dynamic thinking budget allocation.
    """
    # 1. Valid Payload
    valid_data = {
        "macro_sentiment_score": 0.45,
        "conviction_score": 0.85,
        "gift_nifty_implied_bias": "BULLISH",
        "fii_dii_flow_assessment": "ACCUMULATION",
        "primary_catalysts": [
            "GIFT Nifty indicating +65 pts gap up",
            "Brent Crude drops 1.8% easing fiscal pressure",
            "FII net cash buyers (+1,850 Cr)"
        ]
    }
    payload = MacroIntelligencePayload.model_validate(valid_data)
    assert payload.macro_sentiment_score == 0.45
    assert payload.conviction_score == 0.85
    assert payload.gift_nifty_implied_bias == "BULLISH"
    assert len(payload.primary_catalysts) == 3

    # 2. Range Violation Rejection: sentiment > 1.0
    with pytest.raises(ValidationError):
        MacroIntelligencePayload.model_validate({
            **valid_data,
            "macro_sentiment_score": 1.50  # Invalid (> 1.0)
        })

    # Range Violation Rejection: conviction < 0.0
    with pytest.raises(ValidationError):
        MacroIntelligencePayload.model_validate({
            **valid_data,
            "conviction_score": -0.20  # Invalid (< 0.0)
        })

    # 3. Dynamic Thinking Budget Verification
    macro_engine = MacroIntelligenceEngine()
    
    # Routine session -> thinking_budget = 0
    assert macro_engine.determine_thinking_budget(None) == 0
    assert macro_engine.determine_thinking_budget("Routine Intraday") == 0

    # Macro calendar days -> thinking_budget = 1024
    assert macro_engine.determine_thinking_budget("RBI_MPC") == 1024
    assert macro_engine.determine_thinking_budget("UNION_BUDGET") == 1024
    assert macro_engine.determine_thinking_budget("US_FOMC_MEETING") == 1024

    # 4. Fallback execution safety
    fallback = macro_engine.generate_macro_intelligence(
        news_headlines=["Indian markets steady ahead of trade balance data"],
        gift_nifty_pts=35.0,
        crude_oil_change_pct=-1.2
    )
    assert isinstance(fallback, MacroIntelligencePayload)
    assert fallback.gift_nifty_implied_bias == "BULLISH"
    assert fallback.macro_sentiment_score > 0.0


# ============================================================================
# 6. PSI & FEATURE IMPORTANCE DRIFT WATCHDOG TEST
# ============================================================================
def test_psi_drift_triggers_alert():
    """
    Tests Population Stability Index (PSI) calculation and alert boundary conditions
    (PSI > 0.25 on core features and >40% feature importance collapse).
    """
    watchdog = DualMetricDriftWatchdog(num_bins=10, drift_threshold=0.25)
    np.random.seed(101)

    # 1. Stable Distribution: Baseline vs similar live data
    baseline_gex = np.random.normal(loc=1.5, scale=0.3, size=2000)
    live_stable_gex = np.random.normal(loc=1.51, scale=0.31, size=1500)
    psi_stable = watchdog.calculate_psi(baseline_gex, live_stable_gex)
    assert psi_stable < 0.10  # Stable regime

    # 2. Critical Regime Shift: Distribution mean dislocation
    live_drifted_gex = np.random.normal(loc=3.2, scale=0.8, size=1500)
    psi_drifted = watchdog.calculate_psi(baseline_gex, live_drifted_gex)
    assert psi_drifted > 0.25  # Critical drift triggered

    # 3. Multi-Feature Dataset Drift Evaluation
    baseline_dict = {
        "gex": baseline_gex,
        "obi": np.random.normal(0.0, 0.2, size=2000),
        "vwap_distance": np.random.normal(0.0, 0.005, size=2000)
    }
    # Create drift on 2 core features
    live_dict = {
        "gex": live_drifted_gex,
        "obi": np.random.normal(0.6, 0.4, size=1500),  # Heavy skew to buy
        "vwap_distance": np.random.normal(0.0002, 0.0051, size=1500)
    }

    eval_result = watchdog.evaluate_dataset_drift(
        baseline_df_dict=baseline_dict,
        live_df_dict=live_dict,
        core_features=["gex", "obi", "vwap_distance"]
    )

    assert eval_result["trigger_retraining"] is True
    assert eval_result["status"] == "CRITICAL_DRIFT"
    assert eval_result["action"] == "TRIGGER_CLOUD_BUILD_RETRAINING"
    assert "gex" in eval_result["critical_features"]
    assert "obi" in eval_result["critical_features"]

    # 4. Feature Importance Drift Collapse (>40%)
    base_importance = {"gex": 0.35, "obi": 0.25, "rsi": 0.20, "vwap": 0.20}
    live_collapsed_importance = {"gex": 0.12, "obi": 0.24, "rsi": 0.22, "vwap": 0.19}  # GEX collapsed by ~65%

    importance_drift = watchdog.calculate_feature_importance_drift(
        base_importance,
        live_collapsed_importance,
        max_allowed_collapse_pct=0.40
    )
    assert importance_drift["is_importance_drifted"] is True
    assert importance_drift["alert"] is True
    assert "gex" in importance_drift["drifted_features"]


# ============================================================================
# 7. CANARY MODEL PROMOTION EVALUATOR TEST
# ============================================================================
def test_canary_model_promotion_evaluation():
    """
    Verifies that challenger model is only promoted if Brier score is <= champion
    and Sharpe ratio is >= champion.
    """
    vault = CanaryModelVaultManager()

    # Case A: Challenger has lower Brier (better) and higher Sharpe (better) -> PROMOTE
    res_promote = vault.evaluate_challenger_promotion(
        champion_brier=0.185,
        champion_sharpe=1.65,
        candidate_brier=0.172,
        candidate_sharpe=1.82
    )
    assert res_promote["should_promote"] is True
    assert res_promote["status"] == "PROMOTED_TO_CHAMPION"

    # Case B: Challenger has higher Sharpe but worse Brier (poorer calibration) -> REJECT
    res_reject = vault.evaluate_challenger_promotion(
        champion_brier=0.185,
        champion_sharpe=1.65,
        candidate_brier=0.210,
        candidate_sharpe=1.90
    )
    assert res_reject["should_promote"] is False
    assert res_reject["status"] == "REJECTED_RETAIN_CHAMPION"
