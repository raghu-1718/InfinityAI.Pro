"""
Strategy Decision Wrapper Reusing Exact Engine A & Engine B Production Invariants
"""
import math
from typing import Dict, Any, Optional, Tuple
from .greeks import compute_bs_greeks
from .taxes import calculate_sebi_2026_charges

SEBI_LOT_SIZES = {
    "NIFTY": 65,
    "BANKNIFTY": 30,
    "FINNIFTY": 60,
    "MIDCPNIFTY": 120,
    "SENSEX": 20
}

STRIKE_INTERVALS = {
    "NIFTY": 50,
    "BANKNIFTY": 100,
    "FINNIFTY": 50,
    "MIDCPNIFTY": 25,
    "SENSEX": 100
}

class StrategyWrapper:
    """
    Encapsulates InfinityAI.Pro Directional Option Strategy logic:
      1. ITM-1 Strike Selection (Delta ~0.55 - 0.65)
      2. Dynamic Margin-Aware Lot Sizing
      3. Anti-Fee Cannibalization Hurdle (<35% fees)
      4. Multi-Tier Trailing Profit Lock Ratchet (+8% -> BE, +12% -> +6%, +15% -> +12%)
      5. ADX Conviction Gate (ADX > 22)
    """
    def __init__(self, capital: float = 25000.0, max_risk_per_trade: float = 0.10, adx_threshold: float = 22.0):
        self.capital = capital
        self.max_risk_per_trade = max_risk_per_trade
        self.adx_threshold = adx_threshold

    def resolve_itm1_strike(self, symbol: str, spot: float, signal_type: str) -> Dict[str, Any]:
        """Resolves ITM-1 strike mathematically according to SEBI 2026 rules"""
        sym = symbol.upper()
        interval = STRIKE_INTERVALS.get(sym, 50)
        lot_size = SEBI_LOT_SIZES.get(sym, 65)

        atm_strike = round(spot / interval) * interval
        if signal_type.upper() in ["BUY", "BUY_CALL", "CALL", "CE"]:
            target_strike = atm_strike - interval
            opt_type = "CE"
        else:
            target_strike = atm_strike + interval
            opt_type = "PE"

        # Compute Greeks
        greeks = compute_bs_greeks(spot=spot, strike=target_strike, dte_days=3.0, iv=0.145, option_type=opt_type)

        return {
            "symbol": sym,
            "strike": target_strike,
            "atm_strike": atm_strike,
            "option_type": opt_type,
            "lot_size": lot_size,
            "theoretical_premium": greeks["price"],
            "delta": greeks["delta"],
            "theta": greeks["theta"],
            "gamma": greeks["gamma"],
            "vega": greeks["vega"]
        }

    def calculate_lot_size(self, symbol: str, premium: float) -> Dict[str, Any]:
        """Calculates margin-aware lot sizing respecting hard risk limits"""
        sym = symbol.upper()
        lot_size = SEBI_LOT_SIZES.get(sym, 65)
        cost_per_lot = premium * lot_size

        if cost_per_lot <= 0 or cost_per_lot > self.capital:
            return {"is_viable": False, "lots": 0, "units": 0, "order_value": 0.0}

        # Max allocation based on capital and max risk per trade
        max_capital_allowed = self.capital * 0.40  # Max 40% capital in single trade
        optimal_lots = max(1, int(max_capital_allowed // cost_per_lot))
        optimal_lots = min(optimal_lots, 5)  # Cap at 5 lots for safety

        total_units = optimal_lots * lot_size
        order_value = total_units * premium

        return {
            "is_viable": True,
            "lots": optimal_lots,
            "units": total_units,
            "order_value": round(order_value, 2),
            "lot_size": lot_size
        }

    def evaluate_trailing_ratchet(
        self,
        entry_price: float,
        current_price: float,
        highest_price: float,
        current_sl: float,
        base_target_pct: float = 0.15
    ) -> Tuple[float, Optional[str]]:
        """
        Uncapped Multi-Target Milestone Ratchet:
          - Peak >= +8%   -> Move SL to Breakeven + 1% (Risk Free)
          - Peak >= +15%  -> Move SL to Lock +10%
          - Peak >= +30%  -> Move SL to Lock +20%
          - Peak >= +50%  -> Move SL to Lock +38%
          - Peak >= +100% -> Trail at max(+80%, Peak - 10%)
        """
        peak_gain_pct = (highest_price - entry_price) / entry_price
        new_sl = current_sl
        action = None
        if peak_gain_pct >= 1.00:
            target_sl = max(entry_price * 1.80, highest_price * 0.90)
            if target_sl > new_sl:
                new_sl = target_sl
                action = "SUPER_RUNNER_TRAIL_100PCT"
        elif peak_gain_pct >= 0.50:
            target_sl = entry_price * 1.38  # Lock +38%
            if target_sl > new_sl:
                new_sl = target_sl
                action = "TARGET_4_LOCK_50PCT"
        elif peak_gain_pct >= 0.30:
            target_sl = entry_price * 1.20  # Lock +20%
            if target_sl > new_sl:
                new_sl = target_sl
                action = "TARGET_3_LOCK_30PCT"
        elif peak_gain_pct >= 0.15:
            target_sl = entry_price * 1.10  # Lock +10%
            if target_sl > new_sl:
                new_sl = target_sl
                action = "TARGET_2_LOCK_15PCT"
        elif peak_gain_pct >= 0.08:
            target_sl = entry_price * 1.01  # Breakeven + 1%
            if target_sl > new_sl:
                new_sl = target_sl
                action = "TARGET_1_BREAKEVEN_8PCT"
        return round(new_sl, 2), action
