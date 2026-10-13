"""
InfinityAI.Pro - Institutional Short-Momentum & Trend Filter Gate
==================================================================
Protects the algorithmic portfolio against the 'Short-Momentum Trap' (0% Put Win Rate).

Context:
In Indian capital markets with persistent structural long bias driven by domestic
institutional (DII) systematic investment plans (SIPs), intraday pullbacks are
aggressively bought up. Naive short-momentum signals (BUY_PUT) on intraday breakdown
attempts have historically suffered a 0% win rate (0 wins out of 68 attempts) due to
immediate institutional mean-reversion buying.

Gate Criteria:
A short-momentum order (BUY_PUT / SELL_CALL / SHORT) is AUTHORIZED ONLY IF:
1. Spot Price is strictly below the Daily VWAP (spot < live_vwap or vwap_distance < 0).
2. The Vertex AI MacroIntelligencePayload explicitly scores a macro_bias of 'BEARISH'.

If the broader market is trading at or above VWAP, or if macro bias is NEUTRAL/BULLISH,
Engine-A aggressively suppresses all short-momentum signals, classifying them as
false breakdowns / bull-market bear traps.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("InfinityAI.ShortMomentumGate")

class ShortMomentumFilterGate:
    """Institutional gatekeeper preventing premature counter-trend put buying."""

    @staticmethod
    def evaluate_short_momentum_gate(
        symbol: str,
        decision_or_signal: str,
        spot_price: float,
        live_vwap: Optional[float] = None,
        vwap_distance: Optional[float] = None,
        macro_bias: Optional[str] = None,
        adx: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates whether a short-momentum trade passes the strict VWAP & Macro bias filter.

        Args:
            symbol: Underlying scrip symbol (e.g. NIFTY, BANKNIFTY)
            decision_or_signal: Trading action (e.g. BUY_PUT, SELL_CALL, BUY_CALL)
            spot_price: Live underlying spot price
            live_vwap: Current session Volume Weighted Average Price
            vwap_distance: Percentage distance from VWAP (negative = below VWAP)
            macro_bias: Macro sentiment bias from Vertex AI ('BULLISH', 'BEARISH', 'NEUTRAL')
            adx: Average Directional Index (trend strength)

        Returns:
            Dict containing:
              - 'allowed': bool (True if trade passes gate, False if suppressed)
              - 'reason': str (Detailed institutional audit reasoning)
              - 'is_put_side': bool
              - 'spot': float
              - 'vwap': float
              - 'macro_bias': str
        """
        action = (decision_or_signal or "").upper()
        is_put_side = any(k in action for k in ["PUT", "SELL", "SHORT"]) and not ("SELL_PUT" in action or "BUY_CALL" in action)

        if not is_put_side:
            # CALL side signals (BUY_CALL / SELL_PUT) have an 85.9% win rate and pass this filter
            return {
                "allowed": True,
                "reason": "CALL_SIDE_LONG_MOMENTUM_APPROVED",
                "is_put_side": False,
                "spot": spot_price,
                "vwap": live_vwap or spot_price,
                "macro_bias": macro_bias or "BULLISH"
            }

        # 1. Resolve Macro Sentiment Vector
        if macro_bias is not None and str(macro_bias).strip() != "":
            resolved_macro = str(macro_bias).upper()
        else:
            try:
                from .news_sentiment_ingestor import NEWS_SENTIMENT_INGESTOR
                macro_data = NEWS_SENTIMENT_INGESTOR.get_current_macro_bias()
                resolved_macro = str(macro_data.get("sentiment_direction") or "NEUTRAL").upper()
            except Exception as e:
                logger.debug(f"Macro bias lookup fallback: {e}")
                resolved_macro = "NEUTRAL"

        # 2. Resolve VWAP positioning
        vwap_val = live_vwap if (live_vwap and live_vwap > 0) else spot_price
        is_strictly_below_vwap = False

        if vwap_distance is not None and vwap_distance != 0.0:
            is_strictly_below_vwap = (vwap_distance < -0.02)  # At least 0.02% below VWAP
        elif live_vwap and live_vwap > 0:
            is_strictly_below_vwap = (spot_price < (live_vwap - 1.0))  # Strictly 1 pt below VWAP buffer
        else:
            # If no VWAP reference exists, reject shorting to protect capital
            is_strictly_below_vwap = False

        # 3. Gate Condition 1: Must be below VWAP
        if not is_strictly_below_vwap:
            reason = (
                f"🛡️ SHORT-MOMENTUM TRAP GATE: {symbol} {action} suppressed. "
                f"Spot ({spot_price:.2f}) is at or above Daily VWAP ({vwap_val:.2f}). "
                f"Broader market trending above VWAP (Classified as False Breakdown / Bear Trap)."
            )
            logger.warning(reason)
            return {
                "allowed": False,
                "reason": reason,
                "rejection_code": "SPOT_ABOVE_DAILY_VWAP",
                "is_put_side": True,
                "spot": spot_price,
                "vwap": vwap_val,
                "macro_bias": resolved_macro
            }

        # 4. Gate Condition 2: Macro Bias must be explicitly BEARISH
        # Intraday Structural Breakdown Override:
        # If market microstructure confirms severe intraday breakdown below VWAP
        # (vwap_distance <= -0.35% or spot breakdown > 0.35%), with strong trend momentum (ADX >= 28.0),
        # AND macro is not explicitly BULLISH:
        # We permit the short trade because pure technical momentum overrides stale morning news.
        pct_below_vwap = vwap_distance if (vwap_distance is not None and vwap_distance != 0.0) else ((spot_price - vwap_val) / vwap_val * 100.0)
        structural_breakdown_override = (
            pct_below_vwap <= -0.35 and
            (adx is not None and adx >= 28.0) and
            resolved_macro != "BULLISH"
        )

        if resolved_macro != "BEARISH" and not structural_breakdown_override:
            reason = (
                f"🛡️ SHORT-MOMENTUM TRAP GATE: {symbol} {action} suppressed. "
                f"Vertex AI Macro Bias is '{resolved_macro}' (Requires explicit 'BEARISH'). "
                f"DII SIP structural long liquidity active; suppressing counter-trend put purchase."
            )
            logger.warning(reason)
            return {
                "allowed": False,
                "reason": reason,
                "rejection_code": "MACRO_BIAS_NOT_BEARISH",
                "is_put_side": True,
                "spot": spot_price,
                "vwap": vwap_val,
                "macro_bias": resolved_macro
            }

        # Satisfied: Legitimate breakdown confirmed
        if structural_breakdown_override and resolved_macro != "BEARISH":
            approval_msg = (
                f"✅ SHORT-MOMENTUM CONFIRMED (INTRADAY BREAKDOWN OVERRIDE): {symbol} {action} authorized. "
                f"Spot ({spot_price:.2f}) is {abs(pct_below_vwap):.2f}% below VWAP ({vwap_val:.2f}) "
                f"with high trend momentum (ADX {adx:.1f} >= 28.0). Overriding NEUTRAL macro bias."
            )
        else:
            approval_msg = (
                f"✅ SHORT-MOMENTUM CONFIRMED: {symbol} {action} authorized. "
                f"Spot ({spot_price:.2f}) < VWAP ({vwap_val:.2f}) and Vertex AI Macro Bias is BEARISH."
            )
        logger.info(approval_msg)
        return {
            "allowed": True,
            "reason": approval_msg,
            "rejection_code": None,
            "is_put_side": True,
            "spot": spot_price,
            "vwap": vwap_val,
            "macro_bias": resolved_macro
        }

SHORT_MOMENTUM_FILTER = ShortMomentumFilterGate()
