"""
InfinityAI.Pro — Pullback Entry Confirmation Engine
===================================================
Engine A | Production Grade | Version: 5.0.0
Specifications:
  1. Stops firing immediate breakout FOMO market orders at 1-minute candle peaks.
  2. Holds signals in an observation queue (up to 180 seconds / 3 minutes).
  3. Condition A: Underlying Spot distance to dynamic VWAP: abs(spot_price - live_vwap) <= 5.0 points.
  4. Condition B: 1-minute fast RSI (5-period): rsi_1m_period_5 < 45.0 (for CALL) / > 55.0 (for PUT).
  5. Condition C (Fallback): If spot is trending above VWAP without touching, place limit order at 5-period EMA of underlying spot converted to option limit price, or await a red 1-minute candle retest.
  6. Timeout: If conditions not met within 180s, invalidate with status PULLBACK_TIMEOUT_DISCARD.
  7. Telemetry: Tracks pullback_wait_duration_ms.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger("InfinityAI.PullbackExecutionManager")


class PullbackExecutionManager:
    """
    Manages pullback validation before executing market or limit option entries.
    Prevents buying at local 1-minute tops.
    """
    MAX_OBSERVATION_TIMEOUT_SECONDS = 180  # 3 minutes maximum observation window
    VWAP_PROXIMITY_THRESHOLD = 5.0         # Spot within 5.0 points of VWAP
    FAST_RSI_BULL_PULLBACK = 45.0          # RSI(5) dip below 45 for Call buying
    FAST_RSI_BEAR_PULLBACK = 55.0          # RSI(5) bounce above 55 for Put buying

    def __init__(self):
        # In-memory queue of pending signals awaiting pullback confirmation
        # keyed by symbol: {created_at, signal_payload, ...}
        self.pending_queue: Dict[str, Dict[str, Any]] = {}

    def register_candidate_signal(
        self,
        symbol: str,
        signal_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Registers a raw ML signal into the observation queue awaiting pullback.
        """
        now = datetime.now(timezone.utc)
        record = {
            "symbol": symbol.upper(),
            "signal_payload": signal_payload,
            "created_at": now,
            "created_timestamp": now.timestamp(),
            "status": "AWAITING_PULLBACK",
            "decision": signal_payload.get("decision", "BUY_CALL"),
            "initial_spot": float(signal_payload.get("spot_price", 0.0)),
        }
        self.pending_queue[symbol.upper()] = record
        logger.info(
            f"⏳ Pullback Engine: Registered candidate {symbol} {record['decision']} "
            f"at spot {record['initial_spot']:.2f}. Initializing 180s observation window."
        )
        return record

    def evaluate_pullback_conditions(
        self,
        symbol: str,
        current_spot: float,
        live_vwap: float,
        rsi_1m_period_5: float = 50.0,
        ema_5_spot: Optional[float] = None,
        is_red_candle: bool = False,
        is_green_candle: bool = False,
        decision: str = "BUY_CALL",
        elapsed_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates whether current market tick fulfills pullback criteria.
        Can be called directly per tick or on queued candidates.
        """
        sym_u = symbol.upper()
        is_bullish = ("CALL" in decision.upper() or 
                      ("BUY" in decision.upper() and "PUT" not in decision.upper()))

        # 1. Condition A: Underlying Spot distance to dynamic VWAP <= 5.0 pts
        vwap_diff = abs(current_spot - live_vwap) if live_vwap > 0 else 999.0
        cond_a_vwap_touch = vwap_diff <= self.VWAP_PROXIMITY_THRESHOLD

        # 2. Condition B: 1-minute fast RSI (period 5)
        if is_bullish:
            cond_b_rsi = rsi_1m_period_5 < self.FAST_RSI_BULL_PULLBACK
        else:
            cond_b_rsi = rsi_1m_period_5 > self.FAST_RSI_BEAR_PULLBACK

        # 3. Condition C: Trending Retest Fallback
        # If spot is trending above VWAP without touching, 5-period EMA proximity or candle retest
        cond_c_retest = False
        if is_bullish:
            # Trending above VWAP: check if spot touched 5-EMA or candle was red
            if ema_5_spot and abs(current_spot - ema_5_spot) <= 4.0:
                cond_c_retest = True
            elif is_red_candle:
                cond_c_retest = True
        else:
            if ema_5_spot and abs(current_spot - ema_5_spot) <= 4.0:
                cond_c_retest = True
            elif is_green_candle:
                cond_c_retest = True

        confirmed = cond_a_vwap_touch or cond_b_rsi or cond_c_retest
        confirmation_reason = []
        if cond_a_vwap_touch:
            confirmation_reason.append(f"VWAP_PROXIMITY ({vwap_diff:.1f}pts <= {self.VWAP_PROXIMITY_THRESHOLD}pts)")
        if cond_b_rsi:
            confirmation_reason.append(f"FAST_RSI_PULLBACK ({rsi_1m_period_5:.1f})")
        if cond_c_retest:
            confirmation_reason.append("TRENDING_EMA_OR_CANDLE_RETEST")

        return {
            "confirmed": confirmed,
            "condition_a_vwap": cond_a_vwap_touch,
            "condition_b_rsi": cond_b_rsi,
            "condition_c_retest": cond_c_retest,
            "vwap_distance": round(vwap_diff, 2),
            "fast_rsi": rsi_1m_period_5,
            "reason": " + ".join(confirmation_reason) if confirmed else "PULLBACK_NOT_MET"
        }

    def check_pending_signal(
        self,
        symbol: str,
        current_spot: float,
        live_vwap: float,
        rsi_1m_period_5: float = 50.0,
        ema_5_spot: Optional[float] = None,
        is_red_candle: bool = False,
        is_green_candle: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates a pending queued signal for the symbol against current live market tick.
        If confirmed -> returns execution payload with pullback_wait_duration_ms.
        If timed out (>180s) -> invalidates and returns PULLBACK_TIMEOUT_DISCARD.
        """
        sym_u = symbol.upper()
        record = self.pending_queue.get(sym_u)
        if not record:
            return None

        now = datetime.now(timezone.utc)
        elapsed = (now - record["created_at"]).total_seconds()
        wait_duration_ms = int(elapsed * 1000)

        # Check Timeout
        if elapsed > self.MAX_OBSERVATION_TIMEOUT_SECONDS:
            logger.warning(
                f"🛑 Pullback Engine: Signal for {sym_u} timed out ({elapsed:.1f}s > 180s). "
                f"Status: PULLBACK_TIMEOUT_DISCARD. Discarded safely without chasing."
            )
            del self.pending_queue[sym_u]
            return {
                "status": "PULLBACK_TIMEOUT_DISCARD",
                "symbol": sym_u,
                "pullback_wait_duration_ms": wait_duration_ms,
                "signal_payload": record["signal_payload"]
            }

        # Evaluate conditions
        decision = record["decision"]
        eval_res = self.evaluate_pullback_conditions(
            symbol=sym_u,
            current_spot=current_spot,
            live_vwap=live_vwap,
            rsi_1m_period_5=rsi_1m_period_5,
            ema_5_spot=ema_5_spot,
            is_red_candle=is_red_candle,
            is_green_candle=is_green_candle,
            decision=decision
        )

        if eval_res["confirmed"]:
            logger.info(
                f"🎯 Pullback Engine: Confirmed entry for {sym_u} after {elapsed:.1f}s "
                f"({wait_duration_ms}ms)! Triggers: {eval_res['reason']}"
            )
            del self.pending_queue[sym_u]
            return {
                "status": "PULLBACK_CONFIRMED",
                "symbol": sym_u,
                "pullback_wait_duration_ms": wait_duration_ms,
                "signal_payload": record["signal_payload"],
                "confirmation_triggers": eval_res["reason"],
                "confirmed_spot": current_spot
            }

        logger.debug(
            f"⏳ Pullback Engine: {sym_u} awaiting dip (Elapsed: {elapsed:.1f}s/180s | "
            f"VWAP Diff: {eval_res['vwap_distance']:.1f}pts | RSI: {rsi_1m_period_5:.1f})"
        )
        return None


# Singleton export
PULLBACK_EXECUTION_MANAGER = PullbackExecutionManager()
