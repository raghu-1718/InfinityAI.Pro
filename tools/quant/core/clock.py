"""
Deterministic Event Clock & Session-Aware Market Hours Model
"""
from datetime import datetime, time
from typing import Dict, Any

class MarketClock:
    """
    Simulates real-time market session timeline in IST:
      - 08:55 IST: Container Warmup / Pre-Market
      - 09:15 - 09:20 IST: Opening Volatility Cooldown (No entries if enabled)
      - 09:20 - 15:30 IST: Active Signal Entry & Trade Management
      - 15:35 IST: Mandatory EOD Intraday Squareoff
    """
    def __init__(self, opening_cooldown_enabled: bool = True):
        self.opening_cooldown_enabled = opening_cooldown_enabled

    def is_market_open(self, dt: datetime) -> bool:
        t = dt.time()
        return time(9, 15) <= t <= time(15, 30)

    def is_entry_allowed(self, dt: datetime) -> bool:
        t = dt.time()
        if not (time(9, 15) <= t <= time(15, 30)):
            return False
        if self.opening_cooldown_enabled and time(9, 15) <= t < time(9, 20):
            return False
        return True

    def is_eod_squareoff_due(self, dt: datetime) -> bool:
        t = dt.time()
        return t >= time(15, 35)
