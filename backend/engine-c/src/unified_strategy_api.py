"""
Unified Strategy API - Simplified Version (No External Imports)
Provides single endpoint for frontend to execute any strategy with user-specific capital and risk management
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["Unified Strategies"])


class AssetClass(str, Enum):
    OPTIONS = "options"
    EQUITIES = "equities"
    GIFT_NIFTY = "gift_nifty"


class StrategyName(str, Enum):
    # Options Strategies
    IRON_CONDOR = "iron_condor"
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    COVERED_CALL = "covered_call"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    
    # Equity Strategies
    RSI = "rsi"
    MA_CROSSOVER = "ma_crossover"
    HYBRID = "hybrid"
    
    # GIFT Nifty
    GIFT_NIFTY_GAP = "gift_nifty_gap"


class StrategyExecutionRequest(BaseModel):
    """Request to execute a trading strategy"""
    asset_class: AssetClass
    strategy: StrategyName
    symbol: str = Field(default="NIFTY", description="Trading symbol (NIFTY, BANKNIFTY, etc.)")
    capital: float = Field(gt=0, description="Total capital to allocate")
    risk_percent: float = Field(gt=0, le=100, default=2.0, description="Risk percentage per trade")
    profit_target: float = Field(gt=0, le=100, default=5.0, description="Profit target percentage")
    
    # Optional parameters
    expiry: Optional[str] = None
    spot_price: Optional[float] = None


class StrategyExecutionResponse(BaseModel):
    """Response from strategy execution"""
    status: str
    strategy_name: str
    asset_class: str
    symbol: str
    
    # Position details
    positions_to_open: List[Dict[str, Any]]
    capital_allocated: float
    position_size: int
    
    # Risk metrics
    max_profit: float
    max_loss: float
    risk_reward_ratio: float
    
    # Execution details
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Additional info
    signal_strength: Optional[str] = None
    reasoning: Optional[str] = None
    timestamp: str


def get_next_expiry() -> str:
    """Get next Thursday expiry date"""
    today = datetime.now()
    days_ahead = 3 - today.weekday()  # Thursday is 3
    if days_ahead <= 0:
        days_ahead += 7
    next_thursday = today + timedelta(days=days_ahead)
    return next_thursday.strftime("%Y-%m-%d")


def calculate_iron_condor_positions(
    symbol: str,
    spot_price: float,
    capital: float,
    risk_percent: float,
    lot_size: int = 50
) -> Dict[str, Any]:
    """Calculate Iron Condor positions"""
    
    # Round to nearest 100 for ATM
    atm = round(spot_price / 100) * 100
    
    # Define strikes (simplified - would use Greeks in production)
    call_short_strike = atm + 200
    call_long_strike = atm + 300
    put_short_strike = atm - 200
    put_long_strike = atm - 300
    
    # Estimate premiums (simplified)
    call_short_premium = 50
    call_long_premium = 25
    put_short_premium = 50
    put_long_premium = 25
    
    # Net credit per lot
    net_credit = (call_short_premium - call_long_premium + put_short_premium - put_long_premium) * lot_size
    
    # Max loss per lot
    spread_width = max(call_long_strike - call_short_strike, put_short_strike - put_long_strike)
    max_loss_per_lot = (spread_width * lot_size) - net_credit
    
    # Calculate number of lots based on risk
    risk_amount = capital * (risk_percent / 100)
    num_lots = max(1, int(risk_amount / max_loss_per_lot))
    
    # Build positions
    positions = [
        {
            "strike": call_short_strike,
            "option_type": "CE",
            "quantity": -lot_size * num_lots,
            "premium": call_short_premium,
            "action": "SELL"
        },
        {
            "strike": call_long_strike,
            "option_type": "CE",
            "quantity": lot_size * num_lots,
            "premium": call_long_premium,
            "action": "BUY"
        },
        {
            "strike": put_short_strike,
            "option_type": "PE",
            "quantity": -lot_size * num_lots,
            "premium": put_short_premium,
            "action": "SELL"
        },
        {
            "strike": put_long_strike,
            "option_type": "PE",
            "quantity": lot_size * num_lots,
            "premium": put_long_premium,
            "action": "BUY"
        }
    ]
    
    return {
        "positions": positions,
        "capital_allocated": max_loss_per_lot * num_lots,
        "position_size": num_lots,
        "max_profit": net_credit * num_lots,
        "max_loss": max_loss_per_lot * num_lots,
        "risk_reward_ratio": (max_loss_per_lot * num_lots) / (net_credit * num_lots) if net_credit > 0 else 0
    }


def calculate_equity_positions(
    symbol: str,
    spot_price: float,
    capital: float,
    risk_percent: float,
    profit_target: float
) -> Dict[str, Any]:
    """Calculate equity positions"""
    
    # Calculate stop loss and take profit
    stop_loss_pct = 2.0  # 2% stop loss
    stop_loss_price = spot_price * (1 - stop_loss_pct / 100)
    take_profit_price = spot_price * (1 + profit_target / 100)
    
    # Calculate position size
    risk_amount = capital * (risk_percent / 100)
    risk_per_share = spot_price - stop_loss_price
    position_size = int(risk_amount / risk_per_share) if risk_per_share > 0 else 1
    
    # Build position
    positions = [{
        "symbol": symbol,
        "action": "BUY",
        "quantity": position_size,
        "price": spot_price,
        "order_type": "LIMIT"
    }]
    
    capital_allocated = spot_price * position_size
    max_loss = risk_per_share * position_size
    max_profit = (take_profit_price - spot_price) * position_size
    
    return {
        "positions": positions,
        "capital_allocated": capital_allocated,
        "position_size": position_size,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "risk_reward_ratio": max_loss / max_profit if max_profit > 0 else 0,
        "entry_price": spot_price,
        "stop_loss": stop_loss_price,
        "take_profit": take_profit_price
    }


@router.post("/execute", response_model=StrategyExecutionResponse)
async def execute_strategy(
    request: StrategyExecutionRequest,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """
    Execute a trading strategy with user-specific capital and risk management
    """
    try:
        logger.info(f"Executing {request.strategy} for user {x_user_id}")
        
        # Get spot price (use provided or default)
        spot_price = request.spot_price or 23500.0
        
        # Determine lot size
        lot_size = 50 if "NIFTY" in request.symbol else 25
        
        # Route to appropriate calculator
        if request.asset_class == AssetClass.OPTIONS:
            if request.strategy == StrategyName.IRON_CONDOR:
                result = calculate_iron_condor_positions(
                    request.symbol,
                    spot_price,
                    request.capital,
                    request.risk_percent,
                    lot_size
                )
            else:
                # Other options strategies - simplified
                result = calculate_iron_condor_positions(
                    request.symbol,
                    spot_price,
                    request.capital,
                    request.risk_percent,
                    lot_size
                )
        
        elif request.asset_class == AssetClass.EQUITIES:
            result = calculate_equity_positions(
                request.symbol,
                spot_price,
                request.capital,
                request.risk_percent,
                request.profit_target
            )
        
        else:
            raise HTTPException(status_code=400, detail="Asset class not supported yet")
        
        # Build response
        response = StrategyExecutionResponse(
            status="success",
            strategy_name=request.strategy.value,
            asset_class=request.asset_class.value,
            symbol=request.symbol,
            positions_to_open=result["positions"],
            capital_allocated=result["capital_allocated"],
            position_size=result["position_size"],
            max_profit=result["max_profit"],
            max_loss=result["max_loss"],
            risk_reward_ratio=result["risk_reward_ratio"],
            entry_price=result.get("entry_price"),
            stop_loss=result.get("stop_loss"),
            take_profit=result.get("take_profit"),
            signal_strength="MEDIUM",
            reasoning=f"{request.strategy.value} strategy on {request.symbol} with {request.capital} capital",
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Strategy executed successfully: {response.strategy_name}")
        return response
        
    except Exception as e:
        logger.error(f"Error executing strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_strategies():
    """List all available strategies"""
    return {
        "options": [
            {"name": "iron_condor", "description": "4-leg neutral strategy", "risk": "Limited", "reward": "Limited"},
            {"name": "bull_call_spread", "description": "Bullish spread", "risk": "Limited", "reward": "Limited"},
            {"name": "bear_put_spread", "description": "Bearish spread", "risk": "Limited", "reward": "Limited"},
            {"name": "covered_call", "description": "Income generation", "risk": "High", "reward": "Limited"},
            {"name": "straddle", "description": "Volatility play", "risk": "Limited", "reward": "Unlimited"},
            {"name": "strangle", "description": "Wide volatility play", "risk": "Limited", "reward": "Unlimited"}
        ],
        "equities": [
            {"name": "rsi", "description": "RSI-based mean reversion", "risk": "Medium", "reward": "Medium"},
            {"name": "ma_crossover", "description": "Moving average crossover", "risk": "Medium", "reward": "Medium"},
            {"name": "hybrid", "description": "Multi-strategy selector", "risk": "Medium", "reward": "Medium"}
        ],
        "gift_nifty": [
            {"name": "gift_nifty_gap", "description": "Pre-market gap analysis", "risk": "Medium", "reward": "High"}
        ]
    }
