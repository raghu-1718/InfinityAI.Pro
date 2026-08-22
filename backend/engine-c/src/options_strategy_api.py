"""
InfinityAI.Pro — Multi-Leg Options Strategy Execution API
=========================================================
Engine C | Engine-Grade: Production Institutional | Version: 2.0.0

Exposes endpoints for constructing, analyzing, and executing multi-leg options strategies:
  - Short / Long Straddles
  - Short / Long Strangles
  - Bull Call Spreads / Bear Put Spreads
  - Iron Condors / Iron Butterflies
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import numpy as np
import logging

try:
    from src.multi_leg_options_engine import (
        multi_leg_engine,
        MultiLegStrategyBuilder,
        StrategyType,
        StrategyPlan,
        OptionLeg,
        LegAction,
        OptionType,
        MultiLegExecutionResponse,
        BlackScholesEngine
    )
except ImportError:
    from multi_leg_options_engine import (
        multi_leg_engine,
        MultiLegStrategyBuilder,
        StrategyType,
        StrategyPlan,
        OptionLeg,
        LegAction,
        OptionType,
        MultiLegExecutionResponse,
        BlackScholesEngine
    )

logger = logging.getLogger("InfinityAI.OptionsStrategyAPI")

router = APIRouter(prefix="/api/dhan/options/strategies", tags=["Multi-Leg Option Strategies"])


# ==============================================================================
# Request / Response Schemas
# ==============================================================================

class ConstructStrategyRequest(BaseModel):
    strategy_type: StrategyType = Field(..., description="Options Strategy Type")
    underlying: str = Field("NIFTY", description="Index / Asset (NIFTY, BANKNIFTY, FINNIFTY, SENSEX)")
    spot_price: float = Field(..., description="Current Underlying Spot Price")
    expiry_date: str = Field(..., description="Target Expiry Date (YYYY-MM-DD)")
    num_lots: int = Field(1, ge=1, le=50, description="Number of lots to execute")
    implied_volatility: float = Field(0.16, ge=0.01, le=1.50, description="Implied Volatility (e.g. 0.16 = 16%)")
    wing_distance_pts: Optional[int] = Field(None, description="Strike width for wings/spreads (e.g. 100 for NIFTY)")
    strangle_otm_pts: Optional[int] = Field(None, description="OTM strike distance for strangles/condors")
    custom_target_pct: float = Field(0.25, description="Target Profit % (default 25%)")
    custom_sl_pct: float = Field(0.30, description="Stop Loss % (default 30%)")


class PayoffCurveRequest(BaseModel):
    spot_price: float
    legs: List[OptionLeg]
    range_pct: float = Field(10.0, description="Percentage range above and below spot to calculate (e.g. 10.0 = ±10%)")
    points: int = Field(40, description="Number of curve resolution points")


class ExecuteStrategyRequest(BaseModel):
    plan: StrategyPlan
    user_id: str = Field("raghu_primary", description="Vault User ID")
    dry_run: bool = Field(False, description="True for simulated sandbox validation, False for Live Broker Execution")


class SquareOffRequest(BaseModel):
    strategy_id: str
    user_id: str = Field("raghu_primary", description="Vault User ID")


# ==============================================================================
# API Endpoints
# ==============================================================================

@router.post("/construct", response_model=StrategyPlan)
async def construct_strategy(req: ConstructStrategyRequest):
    """
    Construct an institutional multi-leg option strategy with strikes, theoretical premiums,
    portfolio Greeks (Delta, Gamma, Theta, Vega), and breakeven points.
    """
    try:
        plan = MultiLegStrategyBuilder.construct_strategy(
            strategy_type=req.strategy_type,
            underlying=req.underlying,
            spot_price=req.spot_price,
            expiry_date=req.expiry_date,
            num_lots=req.num_lots,
            implied_volatility=req.implied_volatility,
            wing_distance_pts=req.wing_distance_pts,
            strangle_otm_pts=req.strangle_otm_pts,
            custom_target_pct=req.custom_target_pct,
            custom_sl_pct=req.custom_sl_pct
        )
        return plan
    except Exception as e:
        logger.error(f"Failed to construct strategy: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payoff")
async def calculate_payoff(req: PayoffCurveRequest):
    """
    Calculates the 40-50 point interactive PnL Payoff curve across spot price movements.
    """
    try:
        lower_spot = req.spot_price * (1.0 - req.range_pct / 100.0)
        upper_spot = req.spot_price * (1.0 + req.range_pct / 100.0)
        spots = np.linspace(lower_spot, upper_spot, req.points).tolist()

        payoff_data = []
        for s in spots:
            pnl = 0.0
            for leg in req.legs:
                intr = max(0.0, s - leg.strike) if leg.option_type == OptionType.CE else max(0.0, leg.strike - s)
                if leg.action == LegAction.BUY:
                    pnl += (intr - leg.estimated_premium) * leg.quantity
                else:
                    pnl += (leg.estimated_premium - intr) * leg.quantity
            payoff_data.append({
                "spot_price": round(s, 2),
                "pnl_inr": round(pnl, 2),
                "pnl_pct": round((pnl / (req.spot_price + 1e-6)) * 100.0, 2)
            })

        return {
            "spot_price": req.spot_price,
            "range_pct": req.range_pct,
            "payoff_curve": payoff_data
        }
    except Exception as e:
        logger.error(f"Payoff calculation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute", response_model=MultiLegExecutionResponse)
async def execute_strategy(req: ExecuteStrategyRequest):
    """
    Executes all legs of a strategy plan on DhanHQ API v2 with rate limit protection (9 req/s),
    correlation IDs, and market hours enforcement.
    """
    try:
        res = await multi_leg_engine.execute_plan(
            plan=req.plan,
            user_id=req.user_id,
            dry_run=req.dry_run
        )
        return res
    except ValueError as ve:
        logger.error(f"Validation error during strategy execution: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Strategy execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_strategies():
    """
    Lists all active multi-leg strategy positions and execution orders.
    """
    return {
        "active_strategies_count": len(multi_leg_engine.active_strategies),
        "strategies": multi_leg_engine.active_strategies
    }


@router.post("/square-off")
async def square_off_strategy(req: SquareOffRequest):
    """
    Squares off all open legs of an active strategy atomically on DhanHQ.
    """
    try:
        res = await multi_leg_engine.square_off_strategy(
            strategy_id=req.strategy_id,
            user_id=req.user_id
        )
        return res
    except Exception as e:
        logger.error(f"Failed to square off strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Backward Compatibility Endpoint ──────────────────────────────────────────
@router.post("/analyze")
async def analyze_strategy_legacy(req: Dict[str, Any] = Body(...)):
    """
    Legacy backwards-compatible endpoint for existing UI components.
    """
    try:
        strat_name = req.get("strategy_name", "Short Straddle")
        spot = float(req.get("spot_price", 24500.0))
        p = req.get("params", {})
        qty = int(p.get("quantity", 1))

        # Map name to StrategyType
        strat_map = {
            "Short Straddle": StrategyType.SHORT_STRADDLE,
            "Long Straddle": StrategyType.LONG_STRADDLE,
            "Short Strangle": StrategyType.SHORT_STRANGLE,
            "Long Strangle": StrategyType.LONG_STRANGLE,
            "Bull Call Spread": StrategyType.BULL_CALL_SPREAD,
            "Bear Put Spread": StrategyType.BEAR_PUT_SPREAD,
            "Iron Condor": StrategyType.IRON_CONDOR,
            "Butterfly": StrategyType.IRON_BUTTERFLY
        }
        st = strat_map.get(strat_name, StrategyType.SHORT_STRADDLE)
        plan = MultiLegStrategyBuilder.construct_strategy(
            strategy_type=st,
            underlying="NIFTY",
            spot_price=spot,
            expiry_date=datetime.now().strftime("%Y-%m-%d"),
            num_lots=qty
        )
        return {
            "status": "success",
            "strategy": strat_name,
            "summary": plan.dict(),
            "payoff_chart": [
                {"spot": s, "pnl": round(plan.net_cashflow_total, 2)}
                for s in [spot * 0.95, spot, spot * 1.05]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

