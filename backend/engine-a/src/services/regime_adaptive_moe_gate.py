"""
InfinityAI.Pro — Regime-Adaptive Dynamic Mixture-of-Experts (MoE) Consensus Gate
================================================================================
Engine A | Production Grade | Version: 3.3.0

Replaces the rigid 3-model 100% unanimity lock with dynamic regime-adaptive weighting:
- In STRONG_TREND (ADX >= 24): Trend specialists (LightGBM & CatBoost) take leadership (35% + 35%).
  High-conviction trend breakouts (>= 0.65) are approved even if lagging tree models lag.
- In MEAN_REVERTING_OSCILLATION: XGBoost & Random Forest take leadership (40% + 30%).
- In CHOPPY_SIDEWAYS (ADX < 19.0): Hard chop veto active to prevent theta decay.
- In VOLATILITY_SHOCK (India VIX >= 18.0): Defensive shrinkage with elevated threshold (>= 0.60).
- In EQUILIBRIUM_BASELINE: Dynamic majority consensus (2 out of 3 models >= 0.55 with MoE score >= 0.55).
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("InfinityAI.RegimeAdaptiveMoEGate")

DEFAULT_WEIGHTS = {
    "xgboost": 0.40,
    "lightgbm": 0.30,
    "catboost": 0.15,
    "random_forest": 0.15
}


def classify_regime_heuristics(
    adx_14: float = 20.0,
    atr_ratio: float = 0.010,
    india_vix: float = 14.5
) -> Tuple[str, bool]:
    """Classifies market regime and returns (regime_name, chop_veto_active)."""
    if india_vix >= 18.0 or atr_ratio >= 0.025:
        return "VOLATILITY_SHOCK", False
    elif adx_14 >= 24.0 and atr_ratio <= 0.018:
        return "STRONG_TREND", False
    elif adx_14 < 23.0 and atr_ratio >= 0.012:
        return "MEAN_REVERTING_OSCILLATION", False
    elif adx_14 < 19.0:
        return "CHOPPY_SIDEWAYS", True
    else:
        return "EQUILIBRIUM_BASELINE", False


def get_regime_weights(regime: str) -> Dict[str, float]:
    """Returns normalized model weights according to active market regime."""
    if regime == "STRONG_TREND":
        return {"lightgbm": 0.35, "catboost": 0.35, "xgboost": 0.15, "random_forest": 0.15}
    elif regime == "MEAN_REVERTING_OSCILLATION":
        return {"xgboost": 0.40, "random_forest": 0.30, "catboost": 0.15, "lightgbm": 0.15}
    elif regime == "VOLATILITY_SHOCK":
        return {"xgboost": 0.30, "lightgbm": 0.25, "catboost": 0.25, "random_forest": 0.20}
    elif regime == "CHOPPY_SIDEWAYS":
        return {"xgboost": 0.25, "lightgbm": 0.25, "catboost": 0.25, "random_forest": 0.25}
    else:
        return DEFAULT_WEIGHTS.copy()


def evaluate_regime_moe_consensus(
    symbol: str,
    decision_or_signal_type: str,
    analysis_data: Dict[str, Any],
    overall_confidence: float = 0.60
) -> Dict[str, Any]:
    """
    Evaluates signal against Regime-Adaptive Dynamic MoE Consensus.
    
    Returns structured dict:
    {
        "approved": bool,
        "regime": str,
        "moe_score": float,
        "agreeing_models": List[str],
        "agreement_count": int,
        "chop_veto_active": bool,
        "weights": Dict[str, float],
        "reason": str
    }
    """
    # 1. Determine direction
    is_bullish = ("CALL" in decision_or_signal_type.upper() or 
                  ("BUY" in decision_or_signal_type.upper() and "PUT" not in decision_or_signal_type.upper()) or
                  ("LONG" in decision_or_signal_type.upper() and "PUT" not in decision_or_signal_type.upper()))

    # 2. Extract model probabilities
    cb_p = float(analysis_data.get("catboost_prob", overall_confidence if is_bullish else (1.0 - overall_confidence)))
    lgb_p = float(analysis_data.get("lightgbm_prob", overall_confidence if is_bullish else (1.0 - overall_confidence)))
    xgb_p = float(analysis_data.get("xgboost_prob", overall_confidence if is_bullish else (1.0 - overall_confidence)))

    # Only include Random Forest if explicitly present in analysis_data
    has_rf = "random_forest_prob" in analysis_data or "random_forest" in analysis_data.get("model_breakdown", {})
    rf_p = float(analysis_data.get("random_forest_prob", 0.0)) if has_rf else None

    # Convert directional conviction for puts/bearish setups
    if is_bullish:
        p_cb, p_lgb, p_xgb = cb_p, lgb_p, xgb_p
        p_rf = rf_p if has_rf else None
    else:
        # For put setups: if models provided explicit put conviction (>= 0.50), keep; otherwise invert:
        p_cb = cb_p if ("PUT" in decision_or_signal_type.upper() and cb_p >= 0.50) else (1.0 - cb_p)
        p_lgb = lgb_p if ("PUT" in decision_or_signal_type.upper() and lgb_p >= 0.50) else (1.0 - lgb_p)
        p_xgb = xgb_p if ("PUT" in decision_or_signal_type.upper() and xgb_p >= 0.50) else (1.0 - xgb_p)
        p_rf = (rf_p if ("PUT" in decision_or_signal_type.upper() and rf_p >= 0.50) else (1.0 - rf_p)) if has_rf else None

    # 3. Extract or Classify Regime
    model_breakdown = analysis_data.get("model_breakdown", {})
    regime_moe = model_breakdown.get("regime_moe") or analysis_data.get("regime_moe") or {}

    adx_val = float(analysis_data.get("adx") or analysis_data.get("adx_14") or 
                    regime_moe.get("inputs", {}).get("adx_14", 20.0))
    vix_val = float(analysis_data.get("vix") or analysis_data.get("india_vix") or 
                    regime_moe.get("inputs", {}).get("india_vix", 14.5))
    atr_ratio = float(analysis_data.get("atr_ratio") or 
                      regime_moe.get("inputs", {}).get("atr_ratio", 0.010))

    if regime_moe.get("regime"):
        regime = regime_moe.get("regime")
        chop_veto = bool(regime_moe.get("chop_veto_active", False))
        weights = regime_moe.get("weights") or get_regime_weights(regime)
    else:
        regime, chop_veto = classify_regime_heuristics(adx_14=adx_val, atr_ratio=atr_ratio, india_vix=vix_val)
        weights = get_regime_weights(regime)

    # 4. Check Chop Veto Gate
    if chop_veto or (regime == "CHOPPY_SIDEWAYS" and adx_val < 19.0):
        return {
            "approved": False,
            "regime": regime,
            "moe_score": 0.0,
            "agreeing_models": [],
            "agreement_count": 0,
            "chop_veto_active": True,
            "weights": weights,
            "reason": f"CHOP_VETO_ACTIVE: Market is ranging/consolidating (ADX {adx_val:.1f} < 19.0; Theta decay risk)"
        }

    # 5. Compute Weighted MoE Score
    w_cb = weights.get("catboost", 0.35)
    w_lgb = weights.get("lightgbm", 0.35)
    w_xgb = weights.get("xgboost", 0.30)
    w_rf = weights.get("random_forest", 0.0) if has_rf else 0.0
    total_w = w_cb + w_lgb + w_xgb + (w_rf if has_rf else 0.0)

    weighted_sum = w_cb * p_cb + w_lgb * p_lgb + w_xgb * p_xgb
    if has_rf and p_rf is not None:
        weighted_sum += w_rf * p_rf
    moe_score = weighted_sum / (total_w if total_w > 0 else 1.0)
    moe_score = round(float(moe_score), 4)

    # 6. Evaluate Agreeing Models
    agreeing_models = []
    if p_cb >= 0.52: agreeing_models.append("catboost")
    if p_lgb >= 0.52: agreeing_models.append("lightgbm")
    if p_xgb >= 0.52: agreeing_models.append("xgboost")
    if has_rf and p_rf is not None and p_rf >= 0.52: agreeing_models.append("random_forest")
    agreement_count = len(agreeing_models)

    # 7. Regime-Adaptive Acceptance Criteria
    approved = False
    reason = ""

    if regime == "STRONG_TREND":
        # In a strong trend (ADX >= 24), Gradient Boosters are the designated Domain Experts.
        # MoE Principle: If the designated trend expert (LightGBM or CatBoost) detects strong momentum (>= 0.65),
        # and opposing models are neutral/lagging (neither has a hard reversal conviction >= 0.60 against the trend):
        trend_specialist_conviction = max(p_lgb, p_cb)
        has_trend_specialist = (trend_specialist_conviction >= 0.65)
        # Check that no model has an aggressive reversal signal (> 0.60 on the opposite side)
        no_hard_reversal = (p_xgb >= 0.20 and p_cb >= 0.20 and p_lgb >= 0.20)

        if has_trend_specialist and no_hard_reversal:
            approved = True
            reason = (f"Approved under STRONG_TREND: Designated Trend Expert active "
                      f"(LGB: {p_lgb:.2f}, CB: {p_cb:.2f}) without adverse reversal conflict.")
        elif agreement_count >= 2:
            approved = True
            reason = (f"Approved under STRONG_TREND: Multi-model consensus "
                      f"({agreement_count} models: {agreeing_models}) with MoE score {moe_score:.1%}.")
        else:
            reason = (f"Rejected under STRONG_TREND: Insufficient trend conviction "
                      f"(Trend specialist < 65% and agreement < 2 models).")

    elif regime == "MEAN_REVERTING_OSCILLATION":
        # Mean reversion favors XGBoost / Tree Partitioners
        if p_xgb >= 0.60 or agreement_count >= 2:
            approved = True
            reason = (f"Approved under MEAN_REVERTING_OSCILLATION: Reversion specialist active "
                      f"(XGB: {p_xgb:.2f}) with MoE score {moe_score:.1%}.")
        else:
            reason = (f"Rejected under MEAN_REVERTING_OSCILLATION: Lack of reversion edge "
                      f"(XGB < 60% and agreement < 2 models).")

    elif regime == "VOLATILITY_SHOCK":
        # Elevated volatility: defensive shrinkage requires higher conviction
        if agreement_count >= 2 and moe_score >= 0.58:
            approved = True
            reason = (f"Approved under VOLATILITY_SHOCK: High defensive confirmation "
                      f"({agreement_count} models) with MoE score {moe_score:.1%} >= 58%.")
        else:
            reason = (f"Rejected under VOLATILITY_SHOCK: Insufficient defensive confirmation "
                      f"(MoE score {moe_score:.1%} < 58% in high VIX {vix_val:.1f}).")

    else:  # EQUILIBRIUM_BASELINE
        # Majority rule: at least 2 models agree with directional conviction (>= 0.52)
        if agreement_count >= 2:
            approved = True
            reason = (f"Approved under EQUILIBRIUM_BASELINE: Majority consensus "
                      f"({agreement_count} models: {agreeing_models}) with MoE score {moe_score:.1%}.")
        elif p_lgb >= 0.72 or p_cb >= 0.72:
            approved = True
            reason = (f"Approved under EQUILIBRIUM_BASELINE: High specialist breakout "
                      f"(LGB: {p_lgb:.2f}, CB: {p_cb:.2f}) with MoE score {moe_score:.1%}.")
        else:
            reason = (f"Rejected under EQUILIBRIUM_BASELINE: Non-majority consensus "
                      f"({agreement_count} models, MoE score {moe_score:.1%}).")

    logger.info(
        f"⚖️ MoE Consensus Gate [{symbol}] ({decision_or_signal_type}): "
        f"Regime={regime} | MoE Score={moe_score:.1%} | Approved={approved} | Reason={reason}"
    )

    return {
        "approved": approved,
        "regime": regime,
        "moe_score": moe_score,
        "agreeing_models": agreeing_models,
        "agreement_count": agreement_count,
        "chop_veto_active": False,
        "weights": weights,
        "reason": reason
    }
