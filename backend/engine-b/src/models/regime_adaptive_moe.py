"""
InfinityAI.Pro — Regime-Adaptive Mixture of Experts (MoE) Weighting Engine
===========================================================================
Dynamically calculates expert model weights (CatBoost, LightGBM, XGBoost, Random Forest)
conditioned on live volatility (India VIX) and directional trend strength (ADX).
Applies softmax temperature smoothing to prevent discontinuous weight churn.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple

def softmax(x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """Computes softmax probabilities with temperature scaling."""
    e_x = np.exp((x - np.max(x)) / max(temperature, 1e-4))
    return e_x / e_x.sum(axis=0)

class RegimeAdaptiveMoE:
    """Institutional Dynamic Mixture-of-Experts Router"""

    REGIMES = {
        "TRENDING_BREAKOUT": {
            "catboost": 0.50,
            "xgboost": 0.30,
            "lightgbm": 0.20,
            "random_forest": 0.00
        },
        "MEAN_REVERTING_CHOP": {
            "lightgbm": 0.50,
            "random_forest": 0.30,
            "xgboost": 0.20,
            "catboost": 0.00
        },
        "VOLATILITY_DISLOCATION": {
            "xgboost": 0.50,
            "catboost": 0.30,
            "lightgbm": 0.20,
            "random_forest": 0.00
        },
        "EQUILIBRIUM_BASELINE": {
            "xgboost": 0.35,
            "lightgbm": 0.35,
            "catboost": 0.20,
            "random_forest": 0.10
        }
    }

    @classmethod
    def determine_regime_weights(
        cls,
        adx: float,
        india_vix: float,
        temperature: float = 1.2
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculates continuous, smooth regime-adaptive weights across the Tri-Model ensemble.
        
        Parameters:
        - adx: Average Directional Index (trend strength)
        - india_vix: Live India VIX implied volatility level
        - temperature: Softmax temperature for smooth transition (prevents discrete step-churn)
        
        Returns:
        - weights: Dict of model name to normalized probability weight
        - primary_regime: Dominant market regime classification
        """
        # Distance scores to canonical regime centroids:
        # 1. Trending Breakout: High ADX (>=25), Elevated VIX (>15)
        # 2. Mean-Reverting Chop: Low ADX (<20), Low VIX (<14)
        # 3. Volatility Dislocation: High VIX (>=18)
        
        score_trend = (max(0.0, adx - 20.0) / 15.0) + (max(0.0, india_vix - 14.0) / 6.0)
        score_chop = (max(0.0, 25.0 - adx) / 15.0) + (max(0.0, 16.0 - india_vix) / 6.0)
        score_dislocation = (max(0.0, india_vix - 16.0) / 4.0) * 1.5
        score_baseline = 1.0  # Steady equilibrium prior

        raw_scores = np.array([score_trend, score_chop, score_dislocation, score_baseline], dtype=float)
        regime_probs = softmax(raw_scores, temperature=temperature)

        regime_names = ["TRENDING_BREAKOUT", "MEAN_REVERTING_CHOP", "VOLATILITY_DISLOCATION", "EQUILIBRIUM_BASELINE"]
        primary_regime = regime_names[int(np.argmax(regime_probs))]

        # Blend weights via convex combination of regime weight vectors
        model_names = ["catboost", "lightgbm", "xgboost", "random_forest"]
        blended_weights = {m: 0.0 for m in model_names}

        for i, r_name in enumerate(regime_names):
            p = float(regime_probs[i])
            r_weights = cls.REGIMES[r_name]
            for m in model_names:
                blended_weights[m] += p * r_weights.get(m, 0.0)

        # Re-normalize to guarantee exact sum = 1.000
        total_w = sum(blended_weights.values())
        final_weights = {m: round(blended_weights[m] / total_w, 4) for m in model_names}

        return final_weights, primary_regime
