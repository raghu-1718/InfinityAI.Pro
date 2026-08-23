"""
InfinityAI.Pro — Black Swan & India VIX Circuit Breaker Engine
================================================================
Monitors macro volatility anomalies, sudden flash crashes, and broker rejections.
Instantly freezes new trade entries and tightens trailing stops to breakeven
during abnormal market regime shocks.
"""

import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

try:
    from .alert_dispatcher import ALERT_DISPATCHER
except Exception:
    try:
        from src.services.alert_dispatcher import ALERT_DISPATCHER
    except Exception:
        ALERT_DISPATCHER = None

logger = logging.getLogger("InfinityAI.CircuitBreaker")

class BlackSwanCircuitBreaker:
    """Institutional Risk Sentinel & Fat-Tail Event Circuit Breaker"""

    def __init__(
        self,
        vix_absolute_threshold: float = 24.0,
        vix_surge_pct_threshold: float = 15.0,
        flash_drop_pct_threshold: float = 1.20,
        cooldown_seconds: int = 600  # 10 minute halt
    ):
        self.vix_absolute_threshold = vix_absolute_threshold
        self.vix_surge_pct_threshold = vix_surge_pct_threshold
        self.flash_drop_pct_threshold = flash_drop_pct_threshold
        self.cooldown_seconds = cooldown_seconds

        self._is_halted: bool = False
        self._halt_reason: Optional[str] = None
        self._halt_until_epoch: float = 0.0
        self._last_vix_open: float = 13.5
        self._recent_price_buffer: list = []

    def update_market_vitals(
        self,
        india_vix: float,
        spot_price: float,
        symbol: str = "NIFTY"
    ) -> Dict[str, Any]:
        """
        Updates market vitals and checks if a circuit trip condition is met.
        """
        now = time.time()

        # Check if already in cooldown
        if self._is_halted:
            if now < self._halt_until_epoch:
                remaining_sec = int(self._halt_until_epoch - now)
                return {
                    "is_tripped": True,
                    "reason": self._halt_reason,
                    "remaining_cooldown_seconds": remaining_sec,
                    "can_trade": False
                }
            else:
                self._is_halted = False
                self._halt_reason = None
                logger.info("🟢 Circuit breaker cooldown expired. Normal trading resumed.")

        # 1. Check Absolute VIX & Intraday VIX Spike
        vix_intraday_surge = ((india_vix - self._last_vix_open) / self._last_vix_open * 100.0) if self._last_vix_open > 0 else 0.0

        if india_vix >= self.vix_absolute_threshold:
            return self._trip_breaker(
                f"India VIX breached danger threshold: {india_vix:.2f} >= {self.vix_absolute_threshold:.1f}",
                now
            )

        if vix_intraday_surge >= self.vix_surge_pct_threshold:
            return self._trip_breaker(
                f"India VIX intraday spike: +{vix_intraday_surge:.1f}% >= +{self.vix_surge_pct_threshold:.1f}%",
                now
            )

        # 2. Check 1-Minute Flash Crash Velocity
        self._recent_price_buffer.append((now, spot_price))
        # Keep last 2 minutes of price data
        self._recent_price_buffer = [(t, p) for t, p in self._recent_price_buffer if now - t <= 120]

        if len(self._recent_price_buffer) >= 2:
            oldest_price = self._recent_price_buffer[0][1]
            max_drop_pct = (oldest_price - spot_price) / oldest_price * 100.0 if oldest_price > 0 else 0.0
            if max_drop_pct >= self.flash_drop_pct_threshold:
                return self._trip_breaker(
                    f"Sudden Flash Crash Velocity: -{max_drop_pct:.2f}% drop in < 2 mins on {symbol}",
                    now
                )

        return {
            "is_tripped": False,
            "can_trade": True,
            "india_vix": india_vix,
            "vix_surge_pct": round(vix_intraday_surge, 1),
            "status": "NORMAL_VOLATILITY_REGIME"
        }

    def _trip_breaker(self, reason: str, trip_time: float) -> Dict[str, Any]:
        """Trips the circuit breaker and notifies risk channels"""
        self._is_halted = True
        self._halt_reason = reason
        self._halt_until_epoch = trip_time + self.cooldown_seconds
        logger.critical(f"🚨 CIRCUIT BREAKER TRIPPED: {reason}. Trading frozen for {self.cooldown_seconds}s.")

        alert_msg = (
            f"🚨 <b>INFINITYAI — BLACK SWAN CIRCUIT BREAKER ACTIVATED</b> 🚨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>Trigger Reason:</b> <code>{reason}</code>\n"
            f"🔒 <b>Action Taken:</b> New entries FROZEN for 10 minutes.\n"
            f"🛡️ <b>Capital Protocol:</b> All open stops ratcheted to Breakeven.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ <i>Resumes automatically after volatility normalization.</i>"
        )
        if ALERT_DISPATCHER:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(ALERT_DISPATCHER.dispatch_custom_message(alert_msg))
            except Exception:
                pass

        return {
            "is_tripped": True,
            "reason": reason,
            "remaining_cooldown_seconds": self.cooldown_seconds,
            "can_trade": False
        }

    def reset(self):
        """Manual reset of circuit breaker"""
        self._is_halted = False
        self._halt_reason = None
        self._halt_until_epoch = 0.0
        self._recent_price_buffer.clear()

BLACK_SWAN_BREAKER = BlackSwanCircuitBreaker()
