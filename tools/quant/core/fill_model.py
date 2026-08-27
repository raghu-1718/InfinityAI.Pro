"""
Realistic Execution & Fill Simulation Models
"""
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class FillConfig:
    name: str
    entry_slippage_pct: float     # e.g., 0.002 (0.2%)
    exit_slippage_pct: float      # e.g., 0.002 (0.2%)
    spread_penalty_pct: float     # e.g., 0.005 (0.5%)
    latency_bars: int             # 0 for instant, 1 for 1-bar delay
    max_allowed_spread_pct: float # 0.015 (1.5%)

OPTIMISTIC_MODEL = FillConfig(
    name="OPTIMISTIC",
    entry_slippage_pct=0.0,
    exit_slippage_pct=0.0,
    spread_penalty_pct=0.0,
    latency_bars=0,
    max_allowed_spread_pct=0.03
)

REALISTIC_MODEL = FillConfig(
    name="REALISTIC",
    entry_slippage_pct=0.003,      # 0.3% entry slippage
    exit_slippage_pct=0.003,       # 0.3% exit slippage
    spread_penalty_pct=0.005,      # 0.5% half-spread cost
    latency_bars=0,
    max_allowed_spread_pct=0.015   # 1.5% spread gate
)

CONSERVATIVE_MODEL = FillConfig(
    name="CONSERVATIVE",
    entry_slippage_pct=0.008,      # 0.8% entry slippage
    exit_slippage_pct=0.008,       # 0.8% exit slippage
    spread_penalty_pct=0.010,      # 1.0% spread penalty
    latency_bars=1,                # 1 bar latency delay
    max_allowed_spread_pct=0.015
)

class ExecutionSimulator:
    """Simulates option fill prices under various slippage and spread regimes"""
    def __init__(self, config: FillConfig = REALISTIC_MODEL):
        self.config = config

    def simulate_entry_fill(self, theoretical_premium: float, spread_pct: float = 0.008) -> Dict[str, Any]:
        """Calculates actual entry fill price applying slippage and spread penalty"""
        if spread_pct > self.config.max_allowed_spread_pct:
            return {
                "filled": False,
                "rejection_reason": f"EXCESSIVE_SPREAD ({spread_pct:.2%} > {self.config.max_allowed_spread_pct:.2%})"
            }

        # Entry penalty: Buy at Ask (mid + half-spread + slippage)
        half_spread = theoretical_premium * (spread_pct / 2.0)
        slippage = theoretical_premium * self.config.entry_slippage_pct
        effective_price = round(theoretical_premium + half_spread + slippage, 2)

        return {
            "filled": True,
            "theoretical_price": round(theoretical_premium, 2),
            "effective_price": effective_price,
            "slippage_amount": round(slippage, 2),
            "spread_cost": round(half_spread, 2)
        }

    def simulate_exit_fill(self, theoretical_premium: float, spread_pct: float = 0.008) -> float:
        """Calculates actual exit fill price applying sell-side slippage and bid-spread discount"""
        half_spread = theoretical_premium * (spread_pct / 2.0)
        slippage = theoretical_premium * self.config.exit_slippage_pct
        effective_price = round(max(0.05, theoretical_premium - half_spread - slippage), 2)
        return effective_price
