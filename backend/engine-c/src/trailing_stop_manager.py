"""
InfinityAI.Pro — Dynamic Profit-Locking & Trailing Stop-Loss Daemon
===================================================================
Engine C | Category: Execution Management | Version: 2.0.0

Manages intraday profit-locking & dynamic trailing for active positions:
  - Tier 1: At +8% Profit  -> Shift SL to Breakeven (+0.5% buffer for brokerage/taxes)
  - Tier 2: At +12% Profit -> Shift SL to +6.0% (Lock in 50% of peak gains)
  - Tier 3: At +15% Profit -> Trail SL at (Peak Profit - 4.0%) or trigger Target Exit
"""

import sys
import os
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger("InfinityAI.TrailingStopManager")

# ==============================================================================
# Position State Model
# ==============================================================================

@dataclass
class MonitoredPosition:
    position_id: str
    symbol: str
    security_id: str
    entry_price: float
    quantity: int
    direction: str             # "LONG" or "SHORT"
    initial_sl_price: float    # -11% default
    current_sl_price: float
    target_price: float        # +15% default
    peak_price: float
    peak_pnl_pct: float
    current_ltp: float
    current_pnl_pct: float
    trailing_tier: str         # "INITIAL", "BREAKEVEN_LOCKED", "PROFIT_LOCKED", "DYNAMIC_TRAILING"
    is_active: bool = True
    broker_order_id: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ==============================================================================
# Trailing Stop-Loss Manager Engine
# ==============================================================================

class TrailingStopManager:
    """
    Monitors live positions and executes tiered profit-locking and trailing stop adjustments.
    """

    BREAKEVEN_TRIGGER_PCT = 0.08   # +8.0% gain
    BREAKEVEN_LOCK_PCT = 0.005     # +0.5% (covers brokerage & STT)
    
    TIER2_TRIGGER_PCT = 0.12       # +12.0% gain
    TIER2_LOCK_PCT = 0.060         # +6.0% lock-in

    TIER3_TRIGGER_PCT = 0.15       # +15.0% gain
    TIER3_TRAIL_OFFSET_PCT = 0.040 # Trail 4.0% below peak

    def __init__(self):
        self.positions: Dict[str, MonitoredPosition] = {}
        logger.info("✅ TrailingStopManager initialized.")

    def register_position(
        self,
        position_id: str,
        symbol: str,
        security_id: str,
        entry_price: float,
        quantity: int,
        direction: str = "LONG",
        initial_sl_pct: Optional[float] = None,
        target_pct: float = 0.15,
        broker_order_id: Optional[str] = None,
        iv: float = 0.172,
        gamma: float = 0.001
    ) -> MonitoredPosition:
        """Registers a newly opened trade for real-time trailing SL surveillance with dynamic risk floor."""
        if initial_sl_pct is None:
            initial_sl_pct = round(max(0.04, (iv * 0.25) + (gamma * 15.0)), 4)

        sl_price = entry_price * (1.0 - initial_sl_pct) if direction == "LONG" else entry_price * (1.0 + initial_sl_pct)
        target_price = entry_price * (1.0 + target_pct) if direction == "LONG" else entry_price * (1.0 - target_pct)

        pos = MonitoredPosition(
            position_id=position_id,
            symbol=symbol,
            security_id=security_id,
            entry_price=entry_price,
            quantity=quantity,
            direction=direction,
            initial_sl_price=round(sl_price, 2),
            current_sl_price=round(sl_price, 2),
            target_price=round(target_price, 2),
            peak_price=entry_price,
            peak_pnl_pct=0.0,
            current_ltp=entry_price,
            current_pnl_pct=0.0,
            trailing_tier="INITIAL",
            broker_order_id=broker_order_id
        )

        self.positions[position_id] = pos
        logger.info(f"📍 Registered position {position_id} ({symbol} {direction} @ ₹{entry_price:.2f}) for trailing surveillance.")
        return pos

    def update_tick(self, position_id: str, current_ltp: float) -> Dict[str, Any]:
        """
        Evaluates incoming live tick quote against profit-locking rules.
        """
        if position_id not in self.positions:
            return {"status": "NOT_FOUND"}

        pos = self.positions[position_id]
        if not pos.is_active:
            return {"status": "INACTIVE", "position": pos}

        pos.current_ltp = current_ltp
        pos.last_updated = datetime.now(timezone.utc).isoformat()

        # Calculate PnL %
        if pos.direction == "LONG":
            pnl_pct = (current_ltp - pos.entry_price) / pos.entry_price
            if current_ltp > pos.peak_price:
                pos.peak_price = current_ltp
        else:
            pnl_pct = (pos.entry_price - current_ltp) / pos.entry_price
            if current_ltp < pos.peak_price or pos.peak_price == pos.entry_price:
                pos.peak_price = current_ltp

        pos.current_pnl_pct = round(pnl_pct, 4)
        pos.peak_pnl_pct = max(pos.peak_pnl_pct, pnl_pct)

        action_taken = "NONE"
        old_sl = pos.current_sl_price

        # ── 1. Stop-Loss Trigger Check ──
        if (pos.direction == "LONG" and current_ltp <= pos.current_sl_price) or \
           (pos.direction == "SHORT" and current_ltp >= pos.current_sl_price):
            pos.is_active = False
            action_taken = "STOP_LOSS_EXIT"
            logger.warning(f"🛑 [STOP LOSS HIT] Position {position_id} triggered SL at ₹{current_ltp:.2f} (SL: ₹{pos.current_sl_price:.2f}).")
            return {
                "action": action_taken,
                "position_id": position_id,
                "exit_price": current_ltp,
                "realized_pnl_pct": pos.current_pnl_pct,
                "trailing_tier": pos.trailing_tier
            }

        # ── 2. Tier 3: Dynamic Trailing (Gain >= +15%) ──
        if pos.peak_pnl_pct >= self.TIER3_TRIGGER_PCT:
            pos.trailing_tier = "DYNAMIC_TRAILING"
            if pos.direction == "LONG":
                new_sl = round(pos.peak_price * (1.0 - self.TIER3_TRAIL_OFFSET_PCT), 2)
                if new_sl > pos.current_sl_price:
                    pos.current_sl_price = new_sl
                    action_taken = "TRAILED_TIER_3"
            else:
                new_sl = round(pos.peak_price * (1.0 + self.TIER3_TRAIL_OFFSET_PCT), 2)
                if new_sl < pos.current_sl_price:
                    pos.current_sl_price = new_sl
                    action_taken = "TRAILED_TIER_3"

        # ── 3. Tier 2: Gain Locking (Gain >= +12%) ──
        elif pos.peak_pnl_pct >= self.TIER2_TRIGGER_PCT:
            pos.trailing_tier = "PROFIT_LOCKED"
            if pos.direction == "LONG":
                new_sl = round(pos.entry_price * (1.0 + self.TIER2_LOCK_PCT), 2)
                if new_sl > pos.current_sl_price:
                    pos.current_sl_price = new_sl
                    action_taken = "LOCKED_TIER_2_PROFIT"
            else:
                new_sl = round(pos.entry_price * (1.0 - self.TIER2_LOCK_PCT), 2)
                if new_sl < pos.current_sl_price:
                    pos.current_sl_price = new_sl
                    action_taken = "LOCKED_TIER_2_PROFIT"

        # ── 4. Tier 1: Breakeven Locking (Gain >= +8%) ──
        elif pos.peak_pnl_pct >= self.BREAKEVEN_TRIGGER_PCT:
            pos.trailing_tier = "BREAKEVEN_LOCKED"
            if pos.direction == "LONG":
                new_sl = round(pos.entry_price * (1.0 + self.BREAKEVEN_LOCK_PCT), 2)
                if new_sl > pos.current_sl_price:
                    pos.current_sl_price = new_sl
                    action_taken = "SHIFTED_TO_BREAKEVEN"
            else:
                new_sl = round(pos.entry_price * (1.0 - self.BREAKEVEN_LOCK_PCT), 2)
                if new_sl < pos.current_sl_price:
                    pos.current_sl_price = new_sl
                    action_taken = "SHIFTED_TO_BREAKEVEN"

        if action_taken != "NONE":
            logger.info(f"🔄 [{action_taken}] Position {position_id}: SL adjusted from ₹{old_sl:.2f} -> ₹{pos.current_sl_price:.2f} (Current Gain: {pos.current_pnl_pct*100:+.2f}%)")

        return {
            "action": action_taken,
            "position_id": position_id,
            "current_ltp": current_ltp,
            "current_pnl_pct": pos.current_pnl_pct,
            "peak_pnl_pct": pos.peak_pnl_pct,
            "current_sl_price": pos.current_sl_price,
            "trailing_tier": pos.trailing_tier
        }

# Global Instance
trailing_stop_manager = TrailingStopManager()
