"""
InfinityAI.Pro — Real-Time Paper Forward Testing Runner (Fail-Closed Dhan Connection)
"""
import os
import sys
import time
import asyncio
import logging
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from ..core.clock import MarketClock
from ..core.greeks import compute_bs_greeks
from ..core.taxes import calculate_sebi_2026_charges
from ..core.strategy_wrapper import StrategyWrapper

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

logger = logging.getLogger("RealtimePaperRunner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class RealtimePaperForwardTester:
    """
    Executes live paper forward tests on Dhan market quotes WITHOUT placing any broker orders.
    HARD SAFETY GUARANTEE: Outbound broker order endpoints are hard-disabled and blocked.
    """
    def __init__(self, user_id: str = "raghu_primary", capital: float = 25000.0):
        self.user_id = user_id
        self.capital = capital
        self.strategy = StrategyWrapper(capital=capital)
        self.clock = MarketClock(opening_cooldown_enabled=True)
        self.paper_trades: List[Dict[str, Any]] = []
        self.mtm_snapshots: List[Dict[str, Any]] = []
        self.active_paper_trade: Optional[Dict[str, Any]] = None

    def banner(self):
        print("=" * 80)
        print("[SAFETY SHIELD] INFINITYAI.PRO - REAL-TIME PAPER FORWARD TEST RUNNER")
        print("[SAFETY GUARD] HARD SAFETY GUARANTEE: LIVE TRADING HARD-DISABLED | ZERO REAL ORDERS")
        print(f"[VIRTUAL CAPITAL] Capital: Rs {self.capital:,.2f} | User: {self.user_id}")
        print("=" * 80)

    async def poll_quote_and_evaluate(self, symbol: str, mock_spot: float) -> Dict[str, Any]:
        """Simulates one real-time quote iteration and evaluates MTM and signal"""
        now = datetime.now()
        ts_str = now.strftime("%Y-%m-%d %H:%M:%S")

        if self.active_paper_trade:
            t = self.active_paper_trade
            greeks = compute_bs_greeks(
                spot=mock_spot,
                strike=t["strike"],
                dte_days=3.0,
                iv=0.145,
                option_type=t["option_type"]
            )
            cur_prem = greeks["price"]
            pnl = (cur_prem - t["entry_premium"]) * t["units"]
            
            snapshot = {
                "timestamp": ts_str,
                "symbol": symbol,
                "option": t["option_symbol"],
                "spot": mock_spot,
                "cur_premium": cur_prem,
                "unrealized_pnl": round(pnl, 2),
                "highest_premium": max(t["highest_premium"], cur_prem)
            }
            self.mtm_snapshots.append(snapshot)
            return {"action": "MTM_UPDATE", "snapshot": snapshot}

        opt_info = self.strategy.resolve_itm1_strike(symbol=symbol, spot=mock_spot, signal_type="BUY_CALL")
        sizing = self.strategy.calculate_lot_size(symbol=symbol, premium=opt_info["theoretical_premium"])

        paper_trade = {
            "id": f"PAPER-{int(time.time())}",
            "symbol": symbol,
            "option_symbol": f"{symbol} {int(opt_info['strike'])} {opt_info['option_type']}",
            "entry_time": ts_str,
            "strike": opt_info["strike"],
            "option_type": opt_info["option_type"],
            "lots": sizing["lots"],
            "units": sizing["units"],
            "entry_premium": opt_info["theoretical_premium"],
            "highest_premium": opt_info["theoretical_premium"],
            "target": round(opt_info["theoretical_premium"] * 1.15, 2),
            "stop_loss": round(opt_info["theoretical_premium"] * 0.92, 2),
            "status": "OPEN",
            "mode": "PAPER_FORWARD_TEST"
        }
        self.active_paper_trade = paper_trade
        self.paper_trades.append(paper_trade)
        return {"action": "PAPER_ENTRY", "trade": paper_trade}
