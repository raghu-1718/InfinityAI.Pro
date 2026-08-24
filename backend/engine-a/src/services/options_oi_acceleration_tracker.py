"""
InfinityAI.Pro — Restricted Open Interest (OI) Acceleration & Institutional Wall Tracker
========================================================================================
Engine A | Production Grade | Version: 3.1.0
Applies strict Strikes-From-ATM (SFATM) boundary filtering to eliminate far-OTM
percentage noise artifacts and isolate legitimate near-the-money institutional walls:
  • NIFTY (Step: 50)       -> Zone: ATM +- 150 pts (7 strikes max)
  • BANKNIFTY (Step: 100)  -> Zone: ATM +- 300 pts (7 strikes max)
  • FINNIFTY (Step: 50)    -> Zone: ATM +- 150 pts (7 strikes max)
  • SENSEX (Step: 100)     -> Zone: ATM +- 300 pts (7 strikes max)
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("InfinityAI.OIAccelerationTracker")

# SEBI 2026 Strike Interval Standards
INDEX_STRIKE_STEPS = {
    "NIFTY": 50.0,
    "BANKNIFTY": 100.0,
    "FINNIFTY": 50.0,
    "MIDCPNIFTY": 25.0,
    "SENSEX": 100.0,
    "BANKEX": 100.0
}

class RestrictedOIAccelerationTracker:
    """Tracks intraday Open Interest accumulation velocity strictly within ATM +- 3 strikes"""
    def __init__(self, max_strike_buffer: int = 3, oi_threshold_pct: float = 20.0):
        self.max_strike_buffer = max_strike_buffer  # Restricts scan to exactly 7 near-money strikes
        self.oi_threshold_pct = oi_threshold_pct    # Minimum 20.0% Delta OI to qualify as a wall
        self._historical_oi_cache: Dict[str, Dict[int, Dict[str, Any]]] = {}

    def resolve_atm_strike(self, symbol: str, spot_price: float) -> int:
        """Mathematically anchors the closest ATM strike based on symbol-specific intervals."""
        step = INDEX_STRIKE_STEPS.get(symbol.upper(), 50.0)
        return int(round(spot_price / step) * step)

    def evaluate_oi_velocity(
        self,
        symbol: str,
        spot_price: float,
        current_strikes_oi: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Filters incoming DhanHQ option ticks, rejecting noisy far-OTM structural artifacts.
        Only evaluates strikes inside the immediate resistance/support zone [ATM - 3, ATM + 3].
        """
        step = INDEX_STRIKE_STEPS.get(symbol.upper(), 50.0)
        atm_strike = self.resolve_atm_strike(symbol, spot_price)
        lower_bound = atm_strike - (self.max_strike_buffer * step)
        upper_bound = atm_strike + (self.max_strike_buffer * step)

        if not current_strikes_oi:
            return {
                "symbol": symbol,
                "atm_strike": atm_strike,
                "scan_window": [lower_bound, upper_bound],
                "call_wall_detected": False,
                "put_wall_detected": False,
                "conviction_multiplier": 1.00,
                "active_walls": [],
                "wall_summary": "No raw OI data available; neutral baseline"
            }

        call_wall_detected = False
        put_wall_detected = False
        active_walls = []
        now = datetime.now(timezone.utc)

        if symbol not in self._historical_oi_cache:
            self._historical_oi_cache[symbol] = {}
        sym_cache = self._historical_oi_cache[symbol]

        for row in current_strikes_oi:
            strike = row.get("strike", 0)
            
            # STRICT HARDENING: Reject any strike outside the immediate ATM +- 3 boundary layer
            if not (lower_bound <= strike <= upper_bound):
                continue

            call_oi_now = row.get("call_oi", 0)
            put_oi_now = row.get("put_oi", 0)

            prev_oi = sym_cache.get(strike, {})
            prev_call = prev_oi.get("call_oi", call_oi_now)
            prev_put = prev_oi.get("put_oi", put_oi_now)

            delta_call_pct = ((call_oi_now - prev_call) / prev_call * 100.0) if prev_call > 0 else 0.0
            delta_put_pct = ((put_oi_now - prev_put) / prev_put * 100.0) if prev_put > 0 else 0.0

            # Direct delta pass-through if pre-calculated in feed
            if "delta_oi_pct" in row:
                opt_type = row.get("type", row.get("option_type", "CE")).upper()
                if "CE" in opt_type or "CALL" in opt_type:
                    delta_call_pct = row["delta_oi_pct"]
                else:
                    delta_put_pct = row["delta_oi_pct"]

            # Evaluate Overhead Call Walls strictly inside the boundary zone
            if strike >= spot_price and delta_call_pct >= self.oi_threshold_pct:
                call_wall_detected = True
                active_walls.append({
                    "type": "CALL_WRITING_WALL",
                    "strike": strike,
                    "delta_oi_pct": round(delta_call_pct, 1),
                    "description": f"Overhead Call Wall at {strike} (+{delta_call_pct:.1f}% Delta OI)"
                })

            # Evaluate Underlying Put Support strictly inside the boundary zone
            if strike <= spot_price and delta_put_pct >= self.oi_threshold_pct:
                put_wall_detected = True
                active_walls.append({
                    "type": "PUT_WRITING_SUPPORT",
                    "strike": strike,
                    "delta_oi_pct": round(delta_put_pct, 1),
                    "description": f"Underlying Put Support at {strike} (+{delta_put_pct:.1f}% Delta OI)"
                })

            # Update cache
            sym_cache[strike] = {
                "call_oi": call_oi_now,
                "put_oi": put_oi_now,
                "timestamp": now
            }

        # Multi-Layer Execution Conviction Multipliers
        if call_wall_detected and not put_wall_detected:
            conviction_multiplier = 0.80  # Immediate Overhead Resistance
            summary = f"Overhead Call Wall hardening inside [{lower_bound} - {upper_bound}] -> Dialing back Long Call conviction"
        elif put_wall_detected and not call_wall_detected:
            conviction_multiplier = 1.15  # Immediate Structural Floor Support
            summary = f"Underlying Put Support hardening inside [{lower_bound} - {upper_bound}] -> Strong floor for Long Calls"
        elif call_wall_detected and put_wall_detected:
            conviction_multiplier = 0.90  # Volatility Squeeze State
            summary = f"Both Call & Put Walls detected inside [{lower_bound} - {upper_bound}] -> Rangebound squeeze regime"
        else:
            conviction_multiplier = 1.00
            summary = f"Normal Open Interest distribution in ATM zone [{lower_bound} - {upper_bound}]"

        return {
            "symbol": symbol,
            "atm_strike": atm_strike,
            "scan_window": [lower_bound, upper_bound],
            "call_wall_detected": call_wall_detected,
            "put_wall_detected": put_wall_detected,
            "conviction_multiplier": round(conviction_multiplier, 2),
            "active_walls": active_walls,
            "wall_summary": summary,
            "evaluated_strikes_count": len(active_walls)
        }

OI_ACCELERATION_TRACKER = RestrictedOIAccelerationTracker()
