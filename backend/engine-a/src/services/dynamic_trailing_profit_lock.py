"""
InfinityAI.Pro — Mode 2 Uncapped Dynamic Trailing Profit Lock & Milestone Engine
===============================================================================
Engine A | Production Grade | Version: 4.0.0-runner
Features:
  1. Uncapped Multi-Target Milestone Ladder (+8%, +15%, +30%, +50%, +100% Super Runner)
  2. Ratchet Invariant: Stop Loss strictly moves UP and CAN NEVER MOVE DOWN
  3. Dynamic Pullback Trailing for Super Runners (>100% gain trailed at Peak - 10%)
  4. Real-time Firestore milestone logging and settlement formatting
"""
import math
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("InfinityAI.MilestoneRunnerEngine")

class DynamicTrailingProfitLock:
    """
    Uncapped Multi-Target Milestone Ratchet Engine.
    Protects downside while allowing multi-bagger runners (+50%, +100%, +200%) to compound.
    """
    # Multi-Target Milestone Ladder Definition
    MILESTONE_LADDER = [
        {
            "level": 1,
            "threshold_pct": 0.08,  # +8% Gain
            "lock_profit_pct": 0.01, # Lock Breakeven + 1%
            "tag": "TARGET_1_HIT",
            "label": "Target 1 (+8% Breakeven Lock)"
        },
        {
            "level": 2,
            "threshold_pct": 0.15,  # +15% Gain
            "lock_profit_pct": 0.10, # Lock +10% Profit
            "tag": "TARGET_2_HIT",
            "label": "Target 2 (+15% Gain / +10% Lock)"
        },
        {
            "level": 3,
            "threshold_pct": 0.30,  # +30% Gain
            "lock_profit_pct": 0.20, # Lock +20% Profit
            "tag": "TARGET_3_HIT",
            "label": "Target 3 (+30% Gain / +20% Lock)"
        },
        {
            "level": 4,
            "threshold_pct": 0.50,  # +50% Gain
            "lock_profit_pct": 0.38, # Lock +38% Profit
            "tag": "TARGET_4_HIT",
            "label": "Target 4 (+50% Gain / +38% Lock)"
        },
        {
            "level": 5,
            "threshold_pct": 1.00,  # +100% Gain (Super Runner)
            "lock_profit_pct": 0.80, # Lock +80% Profit
            "tag": "SUPER_RUNNER_HIT",
            "label": "Super Runner (+100% Gain / Trailing Peak -10%)"
        }
    ]

    @classmethod
    def evaluate_trailing_lock(
        cls,
        entry_price: float = 0.0,
        current_price: float = 0.0,
        highest_observed_price: float = 0.0,
        current_sl: float = 0.0,
        initial_sl: Optional[float] = None,
        entry_premium: Optional[float] = None,
        highest_observed_premium: Optional[float] = None,
        current_premium: Optional[float] = None,
        lot_size: int = 65,
        estimated_taxes: float = 55.0,
        base_stop_loss_pct: Optional[float] = None,
        live_greeks: Optional[Dict[str, float]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluates current price against the Milestone Ladder and updates the Trailing Stop Loss.
        
        Returns:
            - new_sl: The ratcheted Stop Loss (strictly >= current_sl)
            - highest_observed: Updated peak price
            - peak_gain_pct: Maximum observed gain percentage
            - current_gain_pct: Current unrealized gain percentage
            - highest_milestone: Highest milestone tag reached
            - milestones_achieved: List of all unlocked milestones
            - is_sl_hit: Boolean indicating whether current price breached the active trailing SL
        """
        # Support both naming schemes
        entry_p = entry_price if entry_price > 0 else (entry_premium if entry_premium is not None else 0.0)
        curr_p = current_price if current_price > 0 else (current_premium if current_premium is not None else 0.0)
        high_p_input = highest_observed_price if highest_observed_price > 0 else (highest_observed_premium if highest_observed_premium is not None else 0.0)
        curr_sl = current_sl if current_sl > 0 else (initial_sl if initial_sl is not None else (entry_p * 0.92 if entry_p > 0 else 0.0))

        if entry_p <= 0:
            return {
                "new_sl": curr_sl,
                "effective_stop_loss": curr_sl,
                "highest_observed": curr_p,
                "highest_observed_premium": curr_p,
                "peak_gain_pct": 0.0,
                "current_gain_pct": 0.0,
                "highest_milestone": "ENTRY_LEVEL",
                "active_tier": "ENTRY_LEVEL",
                "milestones_achieved": [],
                "is_sl_hit": False,
                "outcome_status": "OPEN"
            }

        # 1. Update peak observed price
        highest_p = max(high_p_input, curr_p, entry_p)
        peak_gain_pct = (highest_p - entry_p) / entry_p
        current_gain_pct = (curr_p - entry_p) / entry_p
        new_sl = curr_sl
        milestones_achieved = []
        highest_milestone = "ENTRY_LEVEL"

        # 2. Evaluate Milestone Ladder
        for milestone in cls.MILESTONE_LADDER:
            if peak_gain_pct >= milestone["threshold_pct"]:
                milestones_achieved.append({
                    "level": milestone["level"],
                    "tag": milestone["tag"],
                    "label": milestone["label"],
                    "threshold_price": round(entry_p * (1.0 + milestone["threshold_pct"]), 2),
                    "locked_sl_price": round(entry_p * (1.0 + milestone["lock_profit_pct"]), 2)
                })
                highest_milestone = milestone["tag"]
                # Ratchet Stop Loss up
                target_sl = entry_p * (1.0 + milestone["lock_profit_pct"])
                if target_sl > new_sl:
                    new_sl = target_sl

        # 3. Dynamic Peak Trailing for Super Runners (Peak Gain >= 50%)
        if peak_gain_pct >= 0.50:
            # Trail 10% below highest observed peak
            runner_sl = highest_p * 0.90
            if runner_sl > new_sl:
                new_sl = runner_sl

        new_sl = round(new_sl, 2)

        # 4. Check if Current Price breached Trailing Stop Loss
        is_sl_hit = curr_p <= new_sl

        return {
            "new_sl": new_sl,
            "effective_stop_loss": new_sl,
            "highest_observed": round(highest_p, 2),
            "highest_observed_premium": round(highest_p, 2),
            "peak_gain_pct": round(peak_gain_pct, 4),
            "current_gain_pct": round(current_gain_pct, 4),
            "highest_milestone": highest_milestone,
            "active_tier": highest_milestone,
            "milestones_achieved": milestones_achieved,
            "is_sl_hit": is_sl_hit,
            "outcome_status": "TRAILING_PROFIT_LOCKED_EXIT" if (is_sl_hit and highest_milestone != "ENTRY_LEVEL") else ("STOP_LOSS_HIT" if is_sl_hit else "OPEN")
        }

DYNAMIC_PROFIT_LOCK = DynamicTrailingProfitLock()
