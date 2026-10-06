import os
import sys
import unittest
from pathlib import Path

# Add backend/engine-a to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "engine-a"))

from src.services.regime_adaptive_moe_gate import (
    evaluate_regime_moe_consensus,
    classify_regime_heuristics,
    get_regime_weights
)


class TestRegimeAdaptiveMoEGate(unittest.TestCase):

    def test_today_scenario_strong_trend_breakout(self):
        """
        Tests 06-10 market condition: LightGBM = 0.7724, CatBoost = 0.297, XGBoost = 0.3312.
        Under the old rigid unanimity gate, this was vetoed.
        Under Regime-Adaptive MoE with STRONG_TREND or high breakout, this should be APPROVED.
        """
        analysis_data = {
            "catboost_prob": 0.297,
            "lightgbm_prob": 0.7724,
            "xgboost_prob": 0.3312,
            "adx": 26.5,
            "vix": 14.5,
            "atr_ratio": 0.011,
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
        res = evaluate_regime_moe_consensus(
            symbol="NIFTY",
            decision_or_signal_type="BUY",
            analysis_data=analysis_data,
            overall_confidence=0.75
        )
        self.assertTrue(res["approved"], f"Expected approved under STRONG_TREND: {res['reason']}")
        self.assertEqual(res["regime"], "STRONG_TREND")
        self.assertIn("lightgbm", res["agreeing_models"])

    def test_chop_veto_active(self):
        """
        Tests BankNIFTY/FinNIFTY condition today: ADX = 12.9 < 19.0.
        Must trigger chop veto to prevent theta decay.
        """
        analysis_data = {
            "catboost_prob": 0.70,
            "lightgbm_prob": 0.75,
            "xgboost_prob": 0.65,
            "adx": 12.9,
            "vix": 14.5,
            "atr_ratio": 0.008,
            "model_breakdown": {
                "regime_moe": {
                    "regime": "CHOPPY_SIDEWAYS",
                    "chop_veto_active": True
                }
            }
        }
        res = evaluate_regime_moe_consensus(
            symbol="BANKNIFTY",
            decision_or_signal_type="BUY",
            analysis_data=analysis_data,
            overall_confidence=0.70
        )
        self.assertFalse(res["approved"])
        self.assertTrue(res["chop_veto_active"])
        self.assertIn("CHOP_VETO_ACTIVE", res["reason"])

    def test_majority_equilibrium_consensus(self):
        """
        Tests 2 out of 3 models agreeing in equilibrium.
        CatBoost = 0.65, LightGBM = 0.68, XGBoost = 0.45.
        """
        analysis_data = {
            "catboost_prob": 0.65,
            "lightgbm_prob": 0.68,
            "xgboost_prob": 0.45,
            "adx": 21.0,
            "vix": 14.0
        }
        res = evaluate_regime_moe_consensus(
            symbol="NIFTY",
            decision_or_signal_type="BUY",
            analysis_data=analysis_data,
            overall_confidence=0.65
        )
        self.assertTrue(res["approved"])
        self.assertEqual(res["agreement_count"], 2)

    def test_conflicting_bearish_rejection(self):
        """
        All models low or conflicting in equilibrium.
        """
        analysis_data = {
            "catboost_prob": 0.40,
            "lightgbm_prob": 0.45,
            "xgboost_prob": 0.35,
            "adx": 21.0,
            "vix": 14.0
        }
        res = evaluate_regime_moe_consensus(
            symbol="NIFTY",
            decision_or_signal_type="BUY",
            analysis_data=analysis_data,
            overall_confidence=0.40
        )
        self.assertFalse(res["approved"])


if __name__ == "__main__":
    unittest.main()
