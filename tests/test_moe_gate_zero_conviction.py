"""
Unit and Regression Tests for MoE Gate Conviction Safeguards.
InfinityAI.Pro - Phase 2 MoE Gate Hard Veto Suite
Verifies that unanimous low-conviction model outputs:
(p_xgb=0.0049, p_cb=0.0001, p_lgb=0.0000)
are permanently blocked (BLOCKED_LOW_PROBABILITY) and never routed into pullback queues.
"""

import sys
from pathlib import Path
import pytest

# Ensure engine-a is on path
_engine_a_dir = Path(__file__).resolve().parent.parent / "backend" / "engine-a"
if str(_engine_a_dir) not in sys.path:
    sys.path.insert(0, str(_engine_a_dir))

from src.services.regime_adaptive_moe_gate import evaluate_regime_moe_consensus
from src.services.ml_consensus_gate import MultiModelConsensusGate


def test_moe_gate_zero_conviction_hard_veto():
    """
    Test the exact 2026-10-19 10:27 IST flaw:
    CatBoost = 0.0001, LightGBM = 0.0000, XGBoost = 0.0049.
    Assert:
    - approved is False
    - execution_route is "BLOCKED_LOW_PROBABILITY"
    - does NOT route to "PULLBACK_LIMIT_ONLY" or "MARKET_DIRECT"
    """
    analysis_data = {
        "catboost_prob": 0.0001,
        "lightgbm_prob": 0.0,
        "xgboost_prob": 0.0049,
        "adx": 28.5,
        "vix": 14.2,
        "atr_ratio": 0.012,
        "model_breakdown": {
            "regime_moe": {
                "regime": "STRONG_TREND",
                "weights": {
                    "catboost": 0.35,
                    "lightgbm": 0.35,
                    "xgboost": 0.15,
                    "random_forest": 0.15
                },
                "chop_veto_active": False
            }
        }
    }

    result = evaluate_regime_moe_consensus(
        symbol="MIDCPNIFTY",
        decision_or_signal_type="BUY",
        analysis_data=analysis_data,
        overall_confidence=0.005
    )

    assert result["approved"] is False
    assert result["execution_route"] == "BLOCKED_LOW_PROBABILITY"
    assert result["execution_route"] != "PULLBACK_LIMIT_ONLY"
    assert "UNANIMOUS_LOW_CONVICTION" in result["reason"] or "BLOCKED_LOW_PROBABILITY" in result["reason"]


def test_ml_consensus_gate_condition_zero():
    """
    Verify MultiModelConsensusGate Condition 0:
    When max_prob < 0.35, returns BLOCKED_LOW_PROBABILITY.
    """
    gate = MultiModelConsensusGate()
    eval_res = gate.evaluate_consensus(
        catboost_prob=0.0001,
        lightgbm_prob=0.0000,
        xgboost_prob=0.0049,
        decision="BUY_CALL",
        adx=30.0
    )

    assert eval_res["consensus_passed"] is False
    assert eval_res["execution_route"] == "BLOCKED_LOW_PROBABILITY"
    assert eval_res["market_state"] == "UNANIMOUS_ENSEMBLE_REJECTION"


def test_moe_gate_valid_high_conviction_passes():
    """Verify that legitimate high conviction breakout signals are approved."""
    analysis_data = {
        "catboost_prob": 0.72,
        "lightgbm_prob": 0.78,
        "xgboost_prob": 0.69,
        "adx": 26.0,
        "vix": 14.0,
        "atr_ratio": 0.011,
        "model_breakdown": {
            "regime_moe": {
                "regime": "STRONG_TREND",
                "weights": {"catboost": 0.35, "lightgbm": 0.35, "xgboost": 0.15, "random_forest": 0.15},
                "chop_veto_active": False
            }
        }
    }

    result = evaluate_regime_moe_consensus(
        symbol="NIFTY",
        decision_or_signal_type="BUY",
        analysis_data=analysis_data,
        overall_confidence=0.75
    )

    assert result["approved"] is True
    assert result["execution_route"] in ["STANDARD_MARKET_ALLOWED", "MARKET_DIRECT"]
