"""
InfinityAI.Pro - Time-of-Day Adaptive Market Regime Thresholds (Domain 1)
=========================================================================
Institutional regime state-machine based on Indian Standard Time (IST / Asia/Kolkata).
Replaces static thresholds with dynamic parameters that adapt to daily market liquidity:
  - REGIME 1: Morning Opening Expansion (09:15 - 10:30 IST) -> ADX: 18.0, ML: 0.65, Theta Damper: False
  - REGIME 2: Mid-Day Lunch Chop Trap    (11:30 - 13:30 IST) -> ADX: 24.0, ML: 0.65, Theta Damper: True
  - REGIME 3: Afternoon Institutional Sweep (13:45 - 15:15 IST) -> ADX: 19.0, ML: 0.65, Theta Damper: False
  - DEFAULT REGIME: All other times (10:30-11:30, 13:30-13:45, 15:15-15:30, off-market)
                   -> ADX: 20.0, ML: 0.70, Theta Damper: False
"""

import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

IST_TIMEZONE = ZoneInfo("Asia/Kolkata")


@dataclass(frozen=True)
class MarketRegimeConfig:
    regime_id: str
    name: str
    adx_threshold: float
    ml_threshold: float
    theta_decay_damper: bool
    ist_time: str
    description: str


def get_current_market_regime(dt: Optional[datetime] = None) -> MarketRegimeConfig:
    """
    Evaluates the institutional market regime based on Indian Standard Time (IST).
    
    Args:
        dt: Optional datetime. If None, current UTC time is converted to Asia/Kolkata.
            Can be an aware or naive datetime; if naive, assumes UTC.
    
    Returns:
        MarketRegimeConfig containing regime parameters.
    """
    if dt is None:
        ist_now = datetime.now(IST_TIMEZONE)
    else:
        if dt.tzinfo is None:
            # Assume UTC if tzinfo is missing
            dt = dt.replace(tzinfo=timezone.utc)
        ist_now = dt.astimezone(IST_TIMEZONE)

    current_t = ist_now.time()
    time_str = ist_now.strftime("%H:%M:%S")

    # Time boundaries (IST)
    r1_start = time(9, 15, 0)
    r1_end   = time(10, 30, 0)

    r2_start = time(11, 30, 0)
    r2_end   = time(13, 30, 0)

    r3_start = time(13, 45, 0)
    r3_end   = time(15, 15, 0)

    # REGIME 1: Morning Opening Expansion (09:15 – 10:30 IST)
    if r1_start <= current_t < r1_end:
        return MarketRegimeConfig(
            regime_id="REGIME_1",
            name="Morning Opening Expansion",
            adx_threshold=18.0,
            ml_threshold=0.65,
            theta_decay_damper=False,
            ist_time=time_str,
            description="High opening momentum & volatility expansion. ADX threshold reduced to capture early institutional breakout trends."
        )

    # REGIME 2: Mid-Day Lunch Chop Trap (11:30 – 13:30 IST)
    elif r2_start <= current_t < r2_end:
        return MarketRegimeConfig(
            regime_id="REGIME_2",
            name="Mid-Day Lunch Chop Trap",
            adx_threshold=24.0,
            ml_threshold=0.65,
            theta_decay_damper=True,
            ist_time=time_str,
            description="Institutional lunch consolidation & premium erosion. Forcefully heightened ADX with active theta decay damper."
        )

    # REGIME 3: Afternoon Institutional Sweep (13:45 – 15:15 IST)
    elif r3_start <= current_t < r3_end:
        return MarketRegimeConfig(
            regime_id="REGIME_3",
            name="Afternoon Institutional Sweep",
            adx_threshold=19.0,
            ml_threshold=0.65,
            theta_decay_damper=False,
            ist_time=time_str,
            description="European market overlap & afternoon directional gamma unwinding. Standard ADX threshold re-armed."
        )

    # DEFAULT REGIME (All other market hours & off-market safety)
    else:
        return MarketRegimeConfig(
            regime_id="REGIME_DEFAULT",
            name="Default Regime / Transition Hours",
            adx_threshold=20.0,
            ml_threshold=0.70,
            theta_decay_damper=False,
            ist_time=time_str,
            description="Transition periods or off-market hours. Safe conservative fallback thresholds enforced."
        )
