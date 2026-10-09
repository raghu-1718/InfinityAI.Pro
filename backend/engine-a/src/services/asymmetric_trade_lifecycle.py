"""
InfinityAI.Pro — Asymmetric Multi-Tier Profit Trailing Engine
=============================================================
Engine A | Production Grade | Version: 5.0.0
Specifications:
  1. Enforces lot sizing in even multiples (minimum 2 lots).
  2. Dynamic Breakeven Ratchet: Immediately when option premium gains >= +6.0%,
     shifts Stop Loss to entry_premium + 1.00 (covers slippage, STT, and exchange fees).
  3. Tier 1 (Partial Booking - 50% Qty):
     Trigger: Option premium reaches +12% to +15% (entry_premium * 1.12 - 1.15).
     Action: Executes 50% partial exit, logs tier1_hit_timestamp, locks in realized gains.
  4. Tier 2 (Runner - 50% Qty):
     No static target ceiling. Trails runner using Spot Supertrend (7, 3.0) or 5-minute close below 20-EMA.
     Exits runner position strictly when spot trend structure reverses.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("InfinityAI.AsymmetricTradeLifecycle")


class AsymmetricTradeLifecycle:
    """
    Asymmetric multi-tier profit trailing and partial-booking state machine.
    Transforms inverted risk-reward into positive expectancy with early breakeven protection
    and uncapped structural trend runners.
    """
    BREAKEVEN_TRIGGER_PCT = 0.06   # +6.0% gain triggers Breakeven Ratchet
    BREAKEVEN_OFFSET_RS = 1.00     # entry_premium + 1.00 covers friction & STT
    TIER1_TRIGGER_PCT = 0.12       # +12.0% triggers 50% partial booking
    TIER1_TARGET_HIGH_PCT = 0.15   # +15.0% upper bound for Tier 1

    @classmethod
    def enforce_even_lots(cls, standard_lot_size: int, requested_lots: int = 2) -> Tuple[int, int]:
        """
        Enforces execution in even multiples of lots (minimum 2 lots).
        Returns (total_quantity, lot_count).
        """
        lots = max(2, requested_lots)
        if lots % 2 != 0:
            lots += 1  # Round up to even lot count for clean 50/50 partial booking
        total_qty = standard_lot_size * lots
        return total_qty, lots

    @classmethod
    def evaluate_lifecycle_state(
        cls,
        entry_premium: float,
        current_premium: float,
        highest_observed_premium: float,
        current_sl_premium: float,
        tier1_booked: bool = False,
        tier1_hit_timestamp: Optional[str] = None,
        is_spot_trend_reversed: bool = False,
        lot_size: int = 65,
        total_lots: int = 2,
        remaining_lots: int = 2,
        is_sell: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates active trade state against the Asymmetric Multi-Tier Lifecycle:
          1. Dynamic Breakeven Ratchet (+6% gain -> SL = entry + 1.00)
          2. Tier 1 Partial Booking (+12% to +15% -> Exit 50% position)
          3. Tier 2 Runner Trailing (Spot structure exit)

        Returns actionable instructions for trade monitoring and execution.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        gain_pct = (current_premium - entry_premium) / entry_premium if entry_premium > 0 else 0.0
        peak_gain_pct = (highest_observed_premium - entry_premium) / entry_premium if entry_premium > 0 else 0.0

        updated_sl = current_sl_premium
        actions_to_execute = []
        new_tier1_booked = tier1_booked
        new_tier1_timestamp = tier1_hit_timestamp
        new_remaining_lots = remaining_lots
        lifecycle_status = "POSITION_ACTIVE"
        active_tier_label = "BASE_STRUCTURAL_RISK"

        # ── 1. Dynamic Breakeven Ratchet (+6.0% Gain) ──────────────────────────
        be_target_sl = round(entry_premium + cls.BREAKEVEN_OFFSET_RS, 2)
        if gain_pct >= cls.BREAKEVEN_TRIGGER_PCT or peak_gain_pct >= cls.BREAKEVEN_TRIGGER_PCT:
            # Ratchet Invariant: SL moves UP, never backward
            if updated_sl < be_target_sl:
                updated_sl = be_target_sl
                active_tier_label = "BREAKEVEN_RATCHET_ACTIVE"
                logger.info(
                    f"🛡️ Breakeven Ratchet: Premium gain +{gain_pct*100:.1f}% >= +6.0%. "
                    f"Ratcheting SL to ₹{updated_sl:.2f} (Entry + ₹1.00)."
                )

        # ── 2. Tier 1 Partial Booking (+12.0% to +15.0% Gain on 50% Qty) ───────
        if not tier1_booked and (gain_pct >= cls.TIER1_TRIGGER_PCT or peak_gain_pct >= cls.TIER1_TRIGGER_PCT):
            new_tier1_booked = True
            new_tier1_timestamp = now_iso
            booked_lots = total_lots // 2
            new_remaining_lots = total_lots - booked_lots
            actions_to_execute.append({
                "action": "PARTIAL_MARKET_EXIT",
                "lots_to_exit": booked_lots,
                "qty_to_exit": booked_lots * lot_size,
                "exit_premium": current_premium,
                "reason": f"TIER1_PARTIAL_PROFIT_BOOKED (+{gain_pct*100:.1f}% >= +12.0%)"
            })
            active_tier_label = "TIER1_PARTIAL_PROFIT_BOOKED"
            # Ensure SL is at least Breakeven + 1.00 after Tier 1 booking
            updated_sl = max(updated_sl, be_target_sl)
            logger.info(
                f"🎉 Tier 1 Target Reached: Booking 50% position ({booked_lots} lots / {booked_lots * lot_size} qty) "
                f"at ₹{current_premium:.2f}. Runner position remaining: {new_remaining_lots} lots."
            )

        # ── 3. Tier 2 Runner Evaluation (Trailing on Spot Trend Structure) ─────
        if new_tier1_booked:
            if tier1_booked:
                active_tier_label = "TIER2_RUNNER_ACTIVE"
            else:
                active_tier_label = "TIER1_PARTIAL_PROFIT_BOOKED"

            # Check if Spot Trend reversed (e.g., 5m candle close below 20-EMA or Supertrend flip)
            if is_spot_trend_reversed:
                actions_to_execute.append({
                    "action": "FULL_MARKET_EXIT",
                    "lots_to_exit": new_remaining_lots,
                    "qty_to_exit": new_remaining_lots * lot_size,
                    "exit_premium": current_premium,
                    "reason": "RUNNER_SPOT_TREND_REVERSAL"
                })
                lifecycle_status = "RUNNER_EXITED_ON_TREND_REVERSAL"
                active_tier_label = "RUNNER_COMPLETED"
                logger.info(
                    f"🏁 Runner Exit: Spot trend structure confirmed reversal. "
                    f"Closing remaining {new_remaining_lots} lots at ₹{current_premium:.2f}."
                )

        # ── 4. Stop Loss Breach Check (Against Ratcheted Option SL) ─────────────
        # If premium drops below ratcheted SL (e.g. Breakeven + 1.00), exit remaining
        is_sl_breached = (current_premium <= updated_sl) and (updated_sl >= be_target_sl)
        if is_sl_breached and lifecycle_status == "POSITION_ACTIVE":
            actions_to_execute.append({
                "action": "FULL_MARKET_EXIT",
                "lots_to_exit": new_remaining_lots,
                "qty_to_exit": new_remaining_lots * lot_size,
                "exit_premium": current_premium,
                "reason": "RATCHETED_BREAKEVEN_STOP_HIT"
            })
            lifecycle_status = "STOP_LOSS_HIT" if not new_tier1_booked else "RUNNER_STOPPED_AT_BREAKEVEN"

        return {
            "current_sl_premium": updated_sl,
            "tier1_booked": new_tier1_booked,
            "tier1_hit_timestamp": new_tier1_timestamp,
            "remaining_lots": new_remaining_lots,
            "total_lots": total_lots,
            "actions_to_execute": actions_to_execute,
            "lifecycle_status": lifecycle_status,
            "active_tier_label": active_tier_label,
            "gain_pct": round(gain_pct * 100, 2),
            "peak_gain_pct": round(peak_gain_pct * 100, 2)
        }


# Singleton export
ASYMMETRIC_TRADE_LIFECYCLE = AsymmetricTradeLifecycle()
