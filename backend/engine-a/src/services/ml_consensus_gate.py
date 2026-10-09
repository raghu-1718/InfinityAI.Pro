"""
InfinityAI.Pro — Multi-Model Consensus & Discordance Gate
==========================================================
Engine A | Production Grade | Version: 5.0.0
Specifications:
  1. Consensus Rule: Require min(catboost_prob, lgbm_prob, xgboost_prob) >= 0.45 for standard market execution.
  2. Divergence Filter: If any single model output falls below < 0.40 (e.g. XGBoost at 33%), flag market state as REGIME_CHOP_CONSOLIDATION.
  3. In REGIME_CHOP_CONSOLIDATION: Bypass aggressive market orders and route orders strictly through the Pullback Limit Engine.
"""

import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("InfinityAI.MultiModelConsensusGate")


class MultiModelConsensusGate:
    """
    Multi-Model Consensus & Discordance Gate.
    Eliminates model discordance blind spots by validating intra-ensemble alignment.
    """
    CONSENSUS_THRESHOLD = 0.45   # min(cb, lgb, xgb) >= 0.45 for standard market execution
    DIVERGENCE_THRESHOLD = 0.40  # if any model < 0.40 -> REGIME_CHOP_CONSOLIDATION

    @classmethod
    def evaluate_consensus(
        cls,
        catboost_prob: float,
        lightgbm_prob: float,
        xgboost_prob: float,
        decision: str = "BUY_CALL"
    ) -> Dict[str, Any]:
        """
        Evaluates intra-model agreement across CatBoost, LightGBM, and XGBoost.

        Returns structured payload with:
          - consensus_passed: bool
          - is_discordant: bool
          - market_state: "REGIME_TRENDING_CONSENSUS" | "REGIME_CHOP_CONSOLIDATION"
          - execution_route: "STANDARD_MARKET_ALLOWED" | "PULLBACK_LIMIT_ONLY"
          - ml_consensus_min: float
          - ml_consensus_max: float
          - spread: float
          - reason: str
        """
        # Directional mapping
        is_bullish = ("CALL" in decision.upper() or 
                      ("BUY" in decision.upper() and "PUT" not in decision.upper()) or
                      ("LONG" in decision.upper() and "PUT" not in decision.upper()))

        # Normalize directional conviction
        if is_bullish:
            p_cb = float(catboost_prob)
            p_lgb = float(lightgbm_prob)
            p_xgb = float(xgboost_prob)
        else:
            p_cb = float(catboost_prob) if ("PUT" in decision.upper() and catboost_prob >= 0.50) else (1.0 - catboost_prob)
            p_lgb = float(lightgbm_prob) if ("PUT" in decision.upper() and lightgbm_prob >= 0.50) else (1.0 - lightgbm_prob)
            p_xgb = float(xgboost_prob) if ("PUT" in decision.upper() and xgboost_prob >= 0.50) else (1.0 - xgboost_prob)

        min_prob = round(float(min(p_cb, p_lgb, p_xgb)), 4)
        max_prob = round(float(max(p_cb, p_lgb, p_xgb)), 4)
        spread = round(max_prob - min_prob, 4)

        # Condition 1: Divergence Filter (< 0.40)
        if min_prob < cls.DIVERGENCE_THRESHOLD:
            market_state = "REGIME_CHOP_CONSOLIDATION"
            is_discordant = True
            consensus_passed = False
            execution_route = "PULLBACK_LIMIT_ONLY"
            reason = (
                f"DISCORDANCE_DETECTED: Model output min({min_prob:.3f}) < {cls.DIVERGENCE_THRESHOLD:.2f} "
                f"(CB={p_cb:.2f}, LGB={p_lgb:.2f}, XGB={p_xgb:.2f}). Flagged REGIME_CHOP_CONSOLIDATION. "
                f"Routing strictly via Pullback Limit Engine."
            )
            logger.warning(f"⚠️ {reason}")

        # Condition 2: Sub-Consensus (0.40 <= min < 0.45)
        elif min_prob < cls.CONSENSUS_THRESHOLD:
            market_state = "REGIME_SUB_CONSENSUS"
            is_discordant = False
            consensus_passed = False
            execution_route = "PULLBACK_LIMIT_ONLY"
            reason = (
                f"SUB_CONSENSUS: Min probability {min_prob:.3f} < {cls.CONSENSUS_THRESHOLD:.2f} "
                f"(Spread={spread:.2f}). Bypassing aggressive market order. Pullback confirmation required."
            )
            logger.info(f"ℹ️ {reason}")

        # Condition 3: Full Consensus (min >= 0.45)
        else:
            market_state = "REGIME_TRENDING_CONSENSUS"
            is_discordant = False
            consensus_passed = True
            execution_route = "STANDARD_MARKET_ALLOWED"
            reason = (
                f"STRONG_CONSENSUS: All models agree (min {min_prob:.3f} >= {cls.CONSENSUS_THRESHOLD:.2f}, "
                f"Spread={spread:.2f}). Market execution permitted."
            )
            logger.info(f"✅ {reason}")

        return {
            "consensus_passed": consensus_passed,
            "is_discordant": is_discordant,
            "market_state": market_state,
            "execution_route": execution_route,
            "ml_consensus_min": min_prob,
            "ml_consensus_max": max_prob,
            "spread": spread,
            "reason": reason,
            "model_probs": {"catboost": p_cb, "lightgbm": p_lgb, "xgboost": p_xgb}
        }


# Singleton export
MULTI_MODEL_CONSENSUS_GATE = MultiModelConsensusGate()
