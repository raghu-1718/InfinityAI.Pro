from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Import Strategies
# In Cloud Run: /app/backend/options... -> backend.options...
# Local: c:\workspace\InfinityAI.Pro\backend\options
try:
    from backend.options.strategies.advanced_strategies import (
        BearPutSpreadStrategy, 
        LongStraddleStrategy, 
        LongStrangleStrategy, 
        ButterflySpreadStrategy
    )
    # Import others if needed from other files
    from backend.options.strategies.iron_condor import IronCondorStrategy
    from backend.options.strategies.bull_call_spread import BullCallSpreadStrategy
    from backend.options.strategies.covered_call import CoveredCallStrategy
except ImportError as e:
    logger.warning(f"Strategy Import Error (safely handled for local dev): {e}")
    # Defines dummies or trys sys path hack if strictly necessary, 
    # but we assume Dockerfile fixed the path.
    pass

router = APIRouter(prefix="/api/dhan/options/strategies", tags=["Option Strategies"])

class StrategyRequest(BaseModel):
    strategy_name: str
    spot_price: float
    params: Dict[str, float]  # keys: strikes, premiums, quantity

@router.post("/analyze")
async def analyze_strategy(req: StrategyRequest):
    """
    Analyze an option strategy PnL and Payoff.
    """
    try:
        strat = None
        p = req.params
        qty = int(p.get("quantity", 1))

        # 1. Instantiate Strategy
        if req.strategy_name == "Bear Put Spread":
            strat = BearPutSpreadStrategy(
                buy_strike=p["buy_strike"],
                sell_strike=p["sell_strike"],
                buy_premium=p["buy_premium"],
                sell_premium=p["sell_premium"],
                quantity=qty
            )
        elif req.strategy_name == "Long Straddle":
            strat = LongStraddleStrategy(
                strike=p["strike"],
                call_premium=p["call_premium"],
                put_premium=p["put_premium"],
                quantity=qty
            )
        elif req.strategy_name == "Long Strangle":
            strat = LongStrangleStrategy(
                call_strike=p["call_strike"],
                put_strike=p["put_strike"],
                call_premium=p["call_premium"],
                put_premium=p["put_premium"],
                quantity=qty
            )
        elif req.strategy_name == "Butterfly":
            strat = ButterflySpreadStrategy(
                lower_strike=p["lower_strike"],
                middle_strike=p["middle_strike"],
                upper_strike=p["upper_strike"],
                lower_premium=p["lower_premium"],
                middle_premium=p["middle_premium"],
                upper_premium=p["upper_premium"],
                quantity=qty
            )
        elif "Iron Condor" in req.strategy_name:
            # Assuming IronCondorStrategy exists in iron_condor.py
            from backend.options.strategies.iron_condor import IronCondorStrategy
            strat = IronCondorStrategy(
                 spot_price=req.spot_price,
                 buy_put_strike=p["put_long_strike"],
                 sell_put_strike=p["put_short_strike"],
                 sell_call_strike=p["call_short_strike"],
                 buy_call_strike=p["call_long_strike"],
                 buy_put_premium=p.get("put_long_premium", 0),
                 sell_put_premium=p.get("put_short_premium", 0), 
                 sell_call_premium=p.get("call_short_premium", 0),
                 buy_call_premium=p.get("call_long_premium", 0),
                 quantity=qty
            )
        elif "Bull Call" in req.strategy_name:
             from backend.options.strategies.bull_call_spread import BullCallSpreadStrategy
             strat = BullCallSpreadStrategy(
                 buy_strike=p["buy_strike"],
                 sell_strike=p["sell_strike"],
                 buy_premium=p["buy_premium"],
                 sell_premium=p["sell_premium"],
                 quantity=qty
             )
        
        if not strat:
             raise HTTPException(status_code=400, detail=f"Strategy '{req.strategy_name}' not supported or implemented.")

        # 2. Get Summary
        summary = strat.get_strategy_summary()

        # 3. Calculate Payoff Chart (Spot +/- 10%)
        # generate 20 points
        lower_bound = req.spot_price * 0.90
        upper_bound = req.spot_price * 1.10
        spots = np.linspace(lower_bound, upper_bound, 20).tolist()
        
        # calculate_payoff returns DataFrame, we convert to dict
        payoff_df = strat.calculate_payoff(spots)
        
        # Convert DataFrame to list of dicts: [{'spot': x, 'pnl': y}, ...]
        payoff_data = payoff_df.to_dict(orient="records")

        return {
            "status": "success",
            "strategy": req.strategy_name,
            "summary": summary,
            "payoff_chart": payoff_data
        }

    except KeyError as k:
        logger.error(f"Missing parameter for strategy: {k}")
        raise HTTPException(status_code=400, detail=f"Missing parameter: {k}")
    except Exception as e:
        logger.error(f"Strategy analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
