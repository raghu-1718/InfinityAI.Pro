"""
InfinityAI.Pro — Spot-Anchored Structural Risk Manager
======================================================
Engine A | Production Grade | Version: 5.0.0
Specifications:
  1. Deprecates noisy option premium stops (e.g. -15% / -20% option premium noise) as primary exit trigger.
  2. Anchors exit decisions strictly in the underlying index structure (NIFTY spot):
     - For BUY_CALL: Stop triggers ONLY if current_spot < structural_support_level.
       structural_support_level = min(prior_15m_candle_low, live_vwap - 8.0)
     - For BUY_PUT: Stop triggers ONLY if current_spot > structural_resistance_level.
       structural_resistance_level = max(prior_15m_candle_high, live_vwap + 8.0)
  3. Absolute Emergency Circuit Breaker: Hard terminal option stop at -25% of entry premium strictly
     to protect against black-swan exchange freezes or delta collapses.
  4. Telemetry: Exports spot_structural_sl in structured logs and records.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("InfinityAI.StructuralRiskManager")


class StructuralRiskManager:
    """
    Spot-anchored structural stop-loss engine.
    Ensures positions are NOT shaken out by temporary option premium volatility (-10% to -15%)
    as long as the underlying index structure remains intact.
    """
    VWAP_BUFFER_POINTS = 8.0       # 8.0 points buffer below/above VWAP
    EMERGENCY_PREMIUM_STOP_PCT = 0.25 # -25.0% maximum catastrophic option drawdown

    @classmethod
    def calculate_structural_levels(
        cls,
        decision: str,
        current_spot: float,
        live_vwap: float,
        prior_15m_low: Optional[float] = None,
        prior_15m_high: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculates exact structural support and resistance levels for the underlying index.
        """
        is_bullish = ("CALL" in decision.upper() or 
                      ("BUY" in decision.upper() and "PUT" not in decision.upper()))

        # Defensive fallback if 15m candle high/low not yet provided
        p_low = prior_15m_low if (prior_15m_low and prior_15m_low > 0) else (current_spot - 25.0)
        p_high = prior_15m_high if (prior_15m_high and prior_15m_high > 0) else (current_spot + 25.0)
        vwap = live_vwap if (live_vwap and live_vwap > 0) else current_spot

        if is_bullish:
            # For BUY_CALL: support is min(prior_15m_candle_low, live_vwap - 8.0)
            structural_level = min(p_low, vwap - cls.VWAP_BUFFER_POINTS)
        else:
            # For BUY_PUT: resistance is max(prior_15m_candle_high, live_vwap + 8.0)
            structural_level = max(p_high, vwap + cls.VWAP_BUFFER_POINTS)

        return {
            "structural_level": round(float(structural_level), 2),
            "is_bullish": is_bullish,
            "vwap_buffered": round(float(vwap - cls.VWAP_BUFFER_POINTS if is_bullish else vwap + cls.VWAP_BUFFER_POINTS), 2),
            "prior_15m_anchor": round(float(p_low if is_bullish else p_high), 2)
        }

    @classmethod
    def evaluate_structural_stop(
        cls,
        decision: str,
        current_spot: float,
        live_vwap: float,
        entry_premium: float,
        current_premium: float,
        prior_15m_low: Optional[float] = None,
        prior_15m_high: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates whether an exit is triggered based on underlying spot structure
        OR the -25% emergency option circuit breaker.

        Returns:
          - is_stop_triggered: bool
          - exit_reason: Optional[str]
          - spot_structural_sl: float
          - is_emergency_stop: bool
          - premium_drawdown_pct: float
        """
        is_bullish = ("CALL" in decision.upper() or 
                      ("BUY" in decision.upper() and "PUT" not in decision.upper()))

        struct_res = cls.calculate_structural_levels(
            decision=decision,
            current_spot=current_spot,
            live_vwap=live_vwap,
            prior_15m_low=prior_15m_low,
            prior_15m_high=prior_15m_high
        )
        spot_structural_sl = struct_res["structural_level"]

        # Option premium drawdown calculation
        prem_drawdown_pct = 0.0
        if entry_premium > 0:
            prem_drawdown_pct = (current_premium - entry_premium) / entry_premium

        # 1. Check Absolute Emergency Circuit Breaker (-25% premium drop)
        emergency_floor = entry_premium * (1.0 - cls.EMERGENCY_PREMIUM_STOP_PCT)
        if current_premium <= emergency_floor:
            logger.warning(
                f"🚨 Structural Risk: Emergency -25% circuit breaker triggered! "
                f"Premium ₹{current_premium:.2f} <= ₹{emergency_floor:.2f} (Entry: ₹{entry_premium:.2f})"
            )
            return {
                "is_stop_triggered": True,
                "exit_reason": "EMERGENCY_PREMIUM_STOP_HIT",
                "spot_structural_sl": spot_structural_sl,
                "is_emergency_stop": True,
                "premium_drawdown_pct": round(prem_drawdown_pct * 100, 2),
                "structural_support_intact": False
            }

        # 2. Check Underlying Spot Structural Breakdown
        if is_bullish:
            # Call Stop triggers ONLY if current_spot < structural_support_level
            spot_breached = current_spot < spot_structural_sl
            if spot_breached:
                logger.info(
                    f"🛑 Structural Risk: Call stop triggered on SPOT breakdown: "
                    f"Current Spot {current_spot:.2f} < Structural SL {spot_structural_sl:.2f}."
                )
                return {
                    "is_stop_triggered": True,
                    "exit_reason": "STRUCTURAL_SPOT_SUPPORT_BREACH",
                    "spot_structural_sl": spot_structural_sl,
                    "is_emergency_stop": False,
                    "premium_drawdown_pct": round(prem_drawdown_pct * 100, 2),
                    "structural_support_intact": False
                }
        else:
            # Put Stop triggers ONLY if current_spot > structural_resistance_level
            spot_breached = current_spot > spot_structural_sl
            if spot_breached:
                logger.info(
                    f"🛑 Structural Risk: Put stop triggered on SPOT breakdown: "
                    f"Current Spot {current_spot:.2f} > Structural Resistance {spot_structural_sl:.2f}."
                )
                return {
                    "is_stop_triggered": True,
                    "exit_reason": "STRUCTURAL_SPOT_RESISTANCE_BREACH",
                    "spot_structural_sl": spot_structural_sl,
                    "is_emergency_stop": False,
                    "premium_drawdown_pct": round(prem_drawdown_pct * 100, 2),
                    "structural_support_intact": False
                }

        # Structure is INTACT: Even if option premium is down -10% or -15%, hold!
        return {
            "is_stop_triggered": False,
            "exit_reason": None,
            "spot_structural_sl": spot_structural_sl,
            "is_emergency_stop": False,
            "premium_drawdown_pct": round(prem_drawdown_pct * 100, 2),
            "structural_support_intact": True
        }


# Singleton export
STRUCTURAL_RISK_MANAGER = StructuralRiskManager()
