"""
Enhanced Option Analytics Endpoints for Engine C
PCR, Max Pain, ATM Strike, IV Surface, and Greeks
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Create enhanced analytics router
analytics_router = APIRouter(prefix="/api/dhan/options", tags=["Options Analytics"])


class GreeksRequest(BaseModel):
    spot_price: float
    strike_price: float
    time_to_expiry_days: float
    implied_volatility: float  # e.g., 0.15 for 15%
    risk_free_rate: float = 0.05  # Default 5%
    option_type: str = 'call'  # 'call' or 'put'


class PortfolioGreeksRequest(BaseModel):
    positions: List[Dict[str, Any]]  # List of positions with qty, spot, strike, etc.


class MaxPainRequest(BaseModel):
    option_chain: List[Dict[str, Any]]  # Option chain data with strikes, OI


@analytics_router.post("/greeks/calculate")
async def calculate_greeks(req: GreeksRequest):
    """
    Calculate all Greeks for a single option
    
    Request Body:
    {
        "spot_price": 18100,
        "strike_price": 18000,
        "time_to_expiry_days": 15,
        "implied_volatility": 0.15,
        "risk_free_rate": 0.05,
        "option_type": "call"
    }
    """
    try:
        from .options_analytics import get_greeks_calculator
        
        calc = get_greeks_calculator()
        
        # Convert days to years
        T = req.time_to_expiry_days / 365
        
        greeks = calc.calculate_all_greeks(
            S=req.spot_price,
            K=req.strike_price,
            T=T,
            r=req.risk_free_rate,
            sigma=req.implied_volatility,
            option_type=req.option_type
        )
        
        return {
            "status": "success",
            "greeks": greeks,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error calculating Greeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/greeks/portfolio")
async def calculate_portfolio_greeks(req: PortfolioGreeksRequest):
    """
    Calculate aggregated portfolio Greeks
    
    Request Body:
    {
        "positions": [
            {
                "qty": 50,
                "spot_price": 18000,
                "strike_price": 17900,
                "time_to_expiry": 0.041,
                "implied_volatility": 0.15,
                "option_type": "put"
            },
            ...
        ]
    }
    """
    try:
        from .options_analytics import get_greeks_calculator
        
        calc = get_greeks_calculator()
        portfolio_greeks = calc.calculate_portfolio_greeks(req.positions)
        
        return {
            "status": "success",
            "portfolio_greeks": portfolio_greeks,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error calculating portfolio Greeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/analytics/pcr")
async def calculate_pcr(option_chain: List[Dict[str, Any]]):
    """
    Calculate Put-Call Ratio from option chain
    
    PCR = Total Put OI / Total Call OI
    PCR > 1 = Bearish, PCR < 1 = Bullish
    """
    try:
        total_call_oi = sum([opt['call_oi'] for opt in option_chain if 'call_oi' in opt])
        total_put_oi = sum([opt['put_oi'] for opt in option_chain if 'put_oi' in opt])
        
        if total_call_oi == 0:
            raise HTTPException(status_code=400, detail="No call open interest data")
        
        pcr = total_put_oi / total_call_oi
        
        # Interpret PCR
        if pcr > 1.2:
            sentiment = "Strong Bearish"
        elif pcr > 1.0:
            sentiment = "Bearish"
        elif pcr > 0.8:
            sentiment = "Neutral"
        else:
            sentiment = "Bullish"
        
        return {
            "status": "success",
            "pcr": round(pcr, 2),
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "sentiment": sentiment,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error calculating PCR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/analytics/max-pain")
async def calculate_max_pain(option_chain: List[Dict[str, Any]]):
    """
    Calculate Max Pain strike
    
    Max Pain = Strike where option sellers (writers) lose minimum money
    """
    try:
        strikes = sorted(set([opt['strike'] for opt in option_chain if 'strike' in opt]))
        
        max_pain_data = []
        
        for strike in strikes:
            # Calculate total value of options at this strike
            call_value = 0
            put_value = 0
            
            for opt in option_chain:
                opt_strike = opt.get('strike', 0)
                call_oi = opt.get('call_oi', 0)
                put_oi = opt.get('put_oi', 0)
                
                # Intrinsic value if expired at this strike
                if opt_strike < strike:
                    call_value += call_oi * (strike - opt_strike)
                if opt_strike > strike:
                    put_value += put_oi * (opt_strike - strike)
            
            total_value = call_value + put_value
            max_pain_data.append({
                'strike': strike,
                'total_value': total_value
            })
        
        # Max pain is where total value is MINIMUM
        max_pain_strike = min(max_pain_data, key=lambda x: x['total_value'])
        
        return {
            "status": "success",
            "max_pain_strike": max_pain_strike['strike'],
            "total_value_at_max_pain": max_pain_strike['total_value'],
            "all_strikes": max_pain_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error calculating Max Pain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/analytics/atm-strike")
async def identify_atm_strike(spot_price: float, option_chain: List[Dict[str, Any]]):
    """
    Identify ATM (At-The-Money) strike
    """
    try:
        strikes = [opt['strike'] for opt in option_chain if 'strike' in opt]
        
        if not strikes:
            raise HTTPException(status_code=400, detail="No strikes found in option chain")
        
        # Find closest strike to spot price
        atm_strike = min(strikes, key=lambda x: abs(x - spot_price))
        
        # Classify surrounding strikes
        itm_call_strikes = [s for s in strikes if s < spot_price]
        otm_call_strikes = [s for s in strikes if s > spot_price]
        itm_put_strikes = [s for s in strikes if s > spot_price]
        otm_put_strikes = [s for s in strikes if s < spot_price]
        
        return {
            "status": "success",
            "spot_price": spot_price,
            "atm_strike": atm_strike,
            "distance_from_spot": abs(atm_strike - spot_price),
            "itm_call_strikes": sorted(itm_call_strikes, reverse=True)[:5],
            "otm_call_strikes": sorted(otm_call_strikes)[:5],
            "itm_put_strikes": sorted(itm_put_strikes)[:5],
            "otm_put_strikes": sorted(otm_put_strikes, reverse=True)[:5],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error identifying ATM strike: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/analytics/summary")
async def get_option_analytics_summary(
    security_id: int = Query(..., description="Underlying security ID"),
    spot_price: float = Query(..., description="Current spot price")
):
    """
    Get comprehensive option analytics summary:
    - PCR
    - Max Pain
    - ATM Strike
    - OI analysis
    """
    try:
        # This would fetch option chain from DhanHQ
        # For now, return structure
        return {
            "status": "success",
            "security_id": security_id,
            "spot_price": spot_price,
            "analytics": {
                "pcr": "Call separate endpoint",
                "max_pain": "Call separate endpoint",
                "atm_strike": "Call separate endpoint"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error generating analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
