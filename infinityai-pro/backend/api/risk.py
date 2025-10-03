"""
Risk Management API Endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from services.risk_engine import risk_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/risk", tags=["Risk Management"])

class RiskAssessmentRequest(BaseModel):
    symbol: str
    strategy: str
    capital: float
    position_size: Optional[float] = None

@router.post("/assess")
async def assess_risk(request: RiskAssessmentRequest):
    """Assess risk for a trading position"""
    
    try:
        assessment = await risk_engine.assess_position_risk(
            symbol=request.symbol,
            strategy=request.strategy,
            capital=request.capital,
            position_size=request.position_size
        )
        
        return {
            "success": True,
            "risk_assessment": assessment,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio")
async def get_portfolio_risk():
    """Get portfolio risk metrics"""
    
    try:
        risk_metrics = await risk_engine.get_portfolio_risk()
        
        return {
            "success": True,
            "portfolio_risk": risk_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Portfolio risk calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/limits")
async def get_risk_limits():
    """Get current risk limits"""
    
    return {
        "success": True,
        "risk_limits": {
            "max_position_size": "10% of capital",
            "max_daily_loss": "5% of capital",
            "max_drawdown": "15% of capital",
            "var_95": "2% daily VaR",
            "concentration_limit": "25% per sector"
        },
        "timestamp": datetime.now().isoformat()
    }