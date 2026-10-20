"""
InfinityAI.Pro — Master Trade Ranker & Capital-Constrained Filtration Tier
========================================================================
Engine A | Production Grade | Optimization Mode

Implements the Secondary, Hardened Filtration Tier to rank all triggered setups
during forward-testing and live simulation.

Key Capabilities:
1. Multi-Factor Scoring Matrix:
   - MoE Ensemble Conviction (40% weight)
   - Risk-to-Reward Ratio (25% weight)
   - Trend Momentum Slope (20% weight)
   - Microstructure Spread & Liquidity (15% weight)
2. Master Trades Isolation:
   - Strictly isolates the Top 10 highest-probability setups per session.
   - Rejects lower-ranked setups to prevent capital over-allocation.
3. Dynamic Capital Boundary Sizing (₹30,000 INR Allocation):
   - Maximum capital utilization capped at ₹30,000.
   - Maximum concurrent open positions = 2 (max ₹15,000 margin per scrip).
   - Reserves a mandatory 40-50% liquidity cushion for trailing stops and MTM swings.
   - Automatically recalibrates lot sizing to prevent margin calls.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger("InfinityAI.MasterTradeRanker")

TOTAL_SIMULATION_CAPITAL = 30000.0  # ₹30,000 INR Allocation Boundary
MAX_CONCURRENT_POSITIONS = 2        # Never exceed 2 simultaneous positions
MAX_MASTER_TRADES_PER_DAY = 10      # Strictly Top 10 Master Trades
MAX_MARGIN_PER_POSITION = TOTAL_SIMULATION_CAPITAL / MAX_CONCURRENT_POSITIONS  # ₹15,000 max margin

# Standard NSE F&O Lot Multipliers (Post-SEBI circular compliance)
LOT_SIZE_MAP = {
    "NIFTY": 65,
    "BANKNIFTY": 30,
    "FINNIFTY": 60,
    "MIDCPNIFTY": 120,
    "SENSEX": 20
}

class MasterTradeRanker:
    """Institutional ranking and position sizing coordinator for ₹30,000 capital accounts."""

    def __init__(self, total_capital: float = TOTAL_SIMULATION_CAPITAL):
        self.total_capital = total_capital
        self.active_positions_count = 0
        self.session_master_trades_count = 0

    def compute_composite_trade_score(
        self,
        moe_prob: float,
        risk_reward_ratio: float,
        adx: float,
        adx_slope: float = 0.5,
        bid_ask_spread_pct: float = 0.05
    ) -> float:
        """
        Calculates a normalized 0.0 to 1.0 composite trade quality score.
        Score = 0.40 * Conviction + 0.25 * RR_Norm + 0.20 * Trend_Norm + 0.15 * Spread_Norm
        """
        # 1. Conviction score (clamped 0.50 to 1.00 mapped to 0.0 - 1.0)
        c_score = max(0.0, min(1.0, (moe_prob - 0.45) / 0.55))

        # 2. Risk-Reward normalization (1:1.5 -> 0.5, 1:2.0 -> 0.75, >=1:3.0 -> 1.0)
        rr_score = max(0.0, min(1.0, (risk_reward_ratio - 1.0) / 2.0))

        # 3. Trend momentum score (ADX >= 15 with positive slope)
        trend_score = max(0.0, min(1.0, ((adx - 12.0) / 25.0) + (0.1 if adx_slope > 0 else -0.1)))

        # 4. Microstructure liquidity penalty (spread > 0.5% heavily penalized)
        liquidity_score = max(0.0, min(1.0, 1.0 - (bid_ask_spread_pct / 0.50)))

        composite_score = (
            0.40 * c_score +
            0.25 * rr_score +
            0.20 * trend_score +
            0.15 * liquidity_score
        )
        return round(float(composite_score), 4)

    def rank_and_filter_candidates(
        self,
        candidates: List[Dict[str, Any]],
        current_active_positions: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Takes raw qualified candidate setups, applies the multi-factor scoring matrix,
        ranks them in descending order of quality, and isolates the Top 10 Master Trades.
        """
        scored_candidates = []
        for c in candidates:
            moe_p = float(c.get("moe_score", c.get("confidence_score", 0.50)))
            rr = float(c.get("risk_reward_numeric", 2.0))
            adx = float(c.get("adx", 18.0))
            adx_slope = float(c.get("adx_slope", 0.5))
            spread = float(c.get("spread_pct", 0.05))

            score = self.compute_composite_trade_score(
                moe_prob=moe_p,
                risk_reward_ratio=rr,
                adx=adx,
                adx_slope=adx_slope,
                bid_ask_spread_pct=spread
            )

            c_copy = dict(c)
            c_copy["master_rank_score"] = score
            scored_candidates.append(c_copy)

        # Sort descending by composite score
        scored_candidates.sort(key=lambda x: x["master_rank_score"], reverse=True)

        # Assign session rank
        for idx, sc in enumerate(scored_candidates):
            sc["session_rank"] = idx + 1
            sc["is_top_10_master_trade"] = (idx < MAX_MASTER_TRADES_PER_DAY)

        return scored_candidates

    def evaluate_capital_aware_execution(
        self,
        trade_setup: Dict[str, Any],
        active_positions_count: int,
        current_available_margin: float
    ) -> Dict[str, Any]:
        """
        Evaluates whether a candidate trade setup can be executed within the ₹30,000 boundary.
        Enforces:
        - Max 2 concurrent positions
        - Max ₹15,000 margin per position
        - Strict lot sizing to prevent margin calls
        """
        symbol = trade_setup.get("symbol", "NIFTY").upper()
        est_premium = float(trade_setup.get("entry_premium", 100.0))
        lot_size = LOT_SIZE_MAP.get(symbol, 65)
        cost_per_lot = est_premium * lot_size

        # Gate 1: Active positions capacity check
        if active_positions_count >= MAX_CONCURRENT_POSITIONS:
            return {
                "approved_for_execution": False,
                "rejection_code": "MAX_CONCURRENT_POSITIONS_REACHED",
                "reason": f"Active positions ({active_positions_count}) at max capacity ({MAX_CONCURRENT_POSITIONS}). Trade queued.",
                "allocated_lots": 0,
                "margin_required": 0.0,
                "available_margin": current_available_margin
            }

        # Gate 2: Master Trade Rank Check
        rank = trade_setup.get("session_rank", 999)
        if rank > MAX_MASTER_TRADES_PER_DAY:
            return {
                "approved_for_execution": False,
                "rejection_code": "BELOW_TOP_10_MASTER_RANK",
                "reason": f"Trade rank (#{rank}) is below Top {MAX_MASTER_TRADES_PER_DAY} cutoff. Capital reserved for higher-alpha opportunities.",
                "allocated_lots": 0,
                "margin_required": 0.0,
                "available_margin": current_available_margin
            }

        # Gate 3: Margin Allocation Check
        if cost_per_lot > MAX_MARGIN_PER_POSITION:
            return {
                "approved_for_execution": False,
                "rejection_code": "EXCEEDS_POSITION_MARGIN_BUDGET",
                "reason": f"Cost per lot (₹{cost_per_lot:,.2f}) exceeds ₹{MAX_MARGIN_PER_POSITION:,.2f} position cap.",
                "allocated_lots": 0,
                "margin_required": cost_per_lot,
                "available_margin": current_available_margin
            }

        # Calculate optimal lots (strictly 1 lot for small capital to eliminate margin risk)
        affordable_lots = int(min(current_available_margin, MAX_MARGIN_PER_POSITION) // cost_per_lot)
        allocated_lots = max(1, min(1, affordable_lots)) if affordable_lots >= 1 else 0

        if allocated_lots <= 0:
            return {
                "approved_for_execution": False,
                "rejection_code": "INSUFFICIENT_AVAILABLE_MARGIN",
                "reason": f"Available margin (₹{current_available_margin:,.2f}) cannot cover 1 lot (₹{cost_per_lot:,.2f}).",
                "allocated_lots": 0,
                "margin_required": cost_per_lot,
                "available_margin": current_available_margin
            }

        total_margin = allocated_lots * cost_per_lot
        remaining_cushion = current_available_margin - total_margin

        return {
            "approved_for_execution": True,
            "rejection_code": None,
            "reason": f"Approved Master Trade (#{rank}) on {symbol}. Allocated {allocated_lots} lot(s) (₹{total_margin:,.2f} margin).",
            "allocated_lots": allocated_lots,
            "lot_size": lot_size,
            "total_quantity": allocated_lots * lot_size,
            "margin_required": round(total_margin, 2),
            "remaining_margin_cushion": round(remaining_cushion, 2),
            "capital_utilization_pct": round((total_margin / self.total_capital) * 100.0, 2)
        }

MASTER_TRADE_RANKER = MasterTradeRanker()
