"""
InfinityAI.Pro — Dynamic Regime-Adaptive Mixture-of-Experts (MoE) Router
========================================================================
Engine B | Production Grade | Version: 3.2.0

Dynamically routes ensemble voting weights across the Tri-Model ML fleet
(CatBoost, LightGBM, XGBoost, Random Forest) conditioned on real-time market regimes:

  1. STRONG_TREND (ADX >= 25.0, ATR Ratio <= 0.015):
     - Prioritizes Gradient Boosters (CatBoost 35% + LightGBM 35%) for continuous trend pursuit.
  2. MEAN_REVERTING_OSCILLATION (ADX < 20.0, ATR Ratio >= 0.012):
     - Prioritizes Non-linear Tree Partitioners (XGBoost 40% + Random Forest 30%) to fade false breakouts.
  3. VOLATILITY_SHOCK (India VIX >= 18.0 or ATR Ratio >= 0.025):
     - Balanced defensive shrinkage.
  4. CHOPPY_SIDEWAYS (ADX < 19.0):
     - Equalized baseline with institutional Chop Veto flag active.
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger("InfinityAI.RegimeMoERouter")

# Baseline Prior Weights
DEFAULT_WEIGHTS = {
    "xgboost": 0.40,
    "lightgbm": 0.30,
    "catboost": 0.15,
    "random_forest": 0.15
}

class RegimeAdaptiveMoERouter:
    """Dynamic Mixture-of-Experts Router for Multi-Model Ensemble"""

    def __init__(self):
        self.regimes = [
            "STRONG_TREND",
            "MEAN_REVERTING_OSCILLATION",
            "VOLATILITY_SHOCK",
            "CHOPPY_SIDEWAYS",
            "EQUILIBRIUM_BASELINE"
        ]

    def classify_regime(
        self,
        adx_14: float = 20.0,
        atr_ratio: float = 0.010,
        india_vix: float = 14.5
    ) -> str:
        """Determines active market regime based on trend strength and volatility"""
        if india_vix >= 18.0 or atr_ratio >= 0.025:
            return "VOLATILITY_SHOCK"
        elif adx_14 >= 25.0 and atr_ratio <= 0.015:
            return "STRONG_TREND"
        elif adx_14 < 23.0 and atr_ratio >= 0.012:
            return "MEAN_REVERTING_OSCILLATION"
        elif adx_14 < 19.0:
            return "CHOPPY_SIDEWAYS"
        else:
            return "EQUILIBRIUM_BASELINE"

    def compute_regime_weights(
        self,
        regime: str,
        available_models: List[str]
    ) -> Dict[str, float]:
        """
        Calculates optimal model weight distribution for the given regime.
        Strictly guarantees weights sum to 1.000 across available models.
        """
        if regime == "STRONG_TREND":
            raw_weights = {
                "catboost": 0.35,
                "lightgbm": 0.35,
                "xgboost": 0.15,
                "random_forest": 0.15
            }
        elif regime == "MEAN_REVERTING_OSCILLATION":
            raw_weights = {
                "xgboost": 0.40,
                "random_forest": 0.30,
                "catboost": 0.15,
                "lightgbm": 0.15
            }
        elif regime == "VOLATILITY_SHOCK":
            raw_weights = {
                "xgboost": 0.30,
                "lightgbm": 0.25,
                "catboost": 0.25,
                "random_forest": 0.20
            }
        elif regime == "CHOPPY_SIDEWAYS":
            raw_weights = {
                "xgboost": 0.25,
                "lightgbm": 0.25,
                "catboost": 0.25,
                "random_forest": 0.25
            }
        else:  # EQUILIBRIUM_BASELINE
            raw_weights = DEFAULT_WEIGHTS.copy()

        # Filter by available models and normalize
        filtered = {m: raw_weights.get(m, 0.25) for m in available_models if m in raw_weights}
        if not filtered:
            filtered = {m: 1.0 / len(available_models) for m in available_models}

        total_weight = sum(filtered.values())
        if total_weight > 0:
            normalized = {m: round(float(w / total_weight), 4) for m, w in filtered.items()}
        else:
            normalized = {m: round(1.0 / len(filtered), 4) for m in filtered}

        # Fix minor rounding discrepancies to guarantee sum == 1.0
        diff = 1.0 - sum(normalized.values())
        if abs(diff) > 0.00001:
            first_m = list(normalized.keys())[0]
            normalized[first_m] = round(normalized[first_m] + diff, 4)

        return normalized

    def route(
        self,
        features: Optional[Dict[str, Any]] = None,
        available_models: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main routing function: Ingests features, classifies regime,
        and outputs regime-adapted weights.
        """
        feats = features or {}
        models = available_models or ["xgboost", "lightgbm", "catboost", "random_forest"]

        adx_14 = float(feats.get("adx_14", 20.0))
        atr_ratio = float(feats.get("atr_ratio", 0.010))
        india_vix = float(feats.get("india_vix", 14.5))

        regime = self.classify_regime(adx_14=adx_14, atr_ratio=atr_ratio, india_vix=india_vix)
        weights = self.compute_regime_weights(regime=regime, available_models=models)
        chop_veto = (regime == "CHOPPY_SIDEWAYS")

        return {
            "regime": regime,
            "weights": weights,
            "chop_veto_active": chop_veto,
            "inputs": {
                "adx_14": adx_14,
                "atr_ratio": atr_ratio,
                "india_vix": india_vix
            }
        }

REGIME_MOE_ROUTER = RegimeAdaptiveMoERouter()
