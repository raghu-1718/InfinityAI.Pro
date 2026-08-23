"""
InfinityAI.Pro — Expiry Afternoon Theta Damper & IV Crush Protection Engine
=============================================================================
Protects Option Buyers against non-linear late-afternoon Theta decay on weekly
and monthly expiry days by dynamically adapting take-profit targets and trailing stops.

Authentic 2026 SEBI-Compliant Expiry Schedule:
  - NSE (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY): ALL derivatives expire on TUESDAY (1)
  - BSE (SENSEX, BANKEX): ALL derivatives expire on THURSDAY (3)
  - MCX (CRUDEOIL): Monthly Commodity Expiry on FRIDAY (4)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

logger = logging.getLogger("InfinityAI.ExpiryThetaDamper")

SEBI_EXPIRY_SCHEDULE = {
    "NIFTY": 1,       # Tuesday (NSE Weekly & Monthly Benchmark)
    "BANKNIFTY": 1,   # Tuesday (NSE Monthly Only)
    "FINNIFTY": 1,    # Tuesday (NSE Monthly Only)
    "MIDCPNIFTY": 1,  # Tuesday (NSE Monthly Only)
    "SENSEX": 3,      # Thursday (BSE Weekly & Monthly Benchmark)
    "BANKEX": 3,      # Thursday (BSE Monthly Only)
    "CRUDEOIL": 4     # Friday (MCX Monthly Commodity)
}

class ExpiryThetaDamper:
    """Dynamic bracket adjuster for expiry afternoon volatility and theta decay"""

    @staticmethod
    def is_expiry_day(symbol: str) -> bool:
        """Returns True if today is the active expiry day for this instrument"""
        now_utc = datetime.now(timezone.utc)
        ist = now_utc + timedelta(hours=5, minutes=30)
        today_weekday = ist.weekday()
        sym_u = symbol.upper()
        target_weekday = SEBI_EXPIRY_SCHEDULE.get(sym_u, 3)
        return today_weekday == target_weekday

    @staticmethod
    def is_afternoon_decay_window() -> bool:
        """Returns True between 13:00 and 15:15 IST"""
        now_utc = datetime.now(timezone.utc)
        ist = now_utc + timedelta(hours=5, minutes=30)
        hour = ist.hour
        minute = ist.minute
        # Afternoon window starts at 13:00 IST
        return (hour == 13) or (hour == 14) or (hour == 15 and minute <= 15)

    @classmethod
    def get_adapted_bracket(
        cls,
        symbol: str,
        entry_premium: float,
        base_target_pct: float = 0.15,
        base_stop_loss_pct: float = 0.11
    ) -> Dict[str, Any]:
        """
        Dynamically adapts target and stop-loss on expiry afternoons:
          • Normal: Target +15%, Stop Loss -11%
          • Expiry Afternoon (13:00–15:15 IST): Target tightened to +10%, Stop Loss -9%
            to capture quick bursts before rapid extrinsic decay occurs.
        """
        on_expiry = cls.is_expiry_day(symbol)
        in_afternoon = cls.is_afternoon_decay_window()
        is_damper_active = on_expiry and in_afternoon

        if is_damper_active:
            adapted_target_pct = 0.10      # Tighten to +10% target
            adapted_stop_loss_pct = 0.09   # Tighten to -9% stop loss
            regime = "EXPIRY_AFTERNOON_THETA_DAMPER"
        else:
            adapted_target_pct = base_target_pct
            adapted_stop_loss_pct = base_stop_loss_pct
            regime = "STANDARD_INSTITUTIONAL"

        target_prem = round(entry_premium * (1.0 + adapted_target_pct), 2)
        stop_loss_prem = round(entry_premium * (1.0 - adapted_stop_loss_pct), 2)

        return {
            "regime": regime,
            "is_damper_active": is_damper_active,
            "target_pct": adapted_target_pct,
            "target_percent_str": f"+{adapted_target_pct * 100:.1f}%",
            "stop_loss_pct": adapted_stop_loss_pct,
            "stop_loss_percent_str": f"-{adapted_stop_loss_pct * 100:.1f}%",
            "entry_premium": entry_premium,
            "target_premium": target_prem,
            "stop_loss_premium": stop_loss_prem
        }

EXPIRY_THETA_DAMPER = ExpiryThetaDamper()
