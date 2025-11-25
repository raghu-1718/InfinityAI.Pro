#!/usr/bin/env python3
"""
InfinityAI.Pro - Real-Time Signal Predictor API
FastAPI service for exposing live trading signals using dynamic strategy loader
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
import asyncio

# Add strategies directory to path
# Assuming this file is at backend/engine-core/src/signal_api.py
# The strategies dir is at backend/strategies/
STRATEGIES_DIR = Path(__file__).parent.parent.parent / "strategies"
sys.path.insert(0, str(STRATEGIES_DIR))

from strategy_loader import StrategyLoader, list_strategies

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="🎯 InfinityAI.Pro - Signal Predictor API",
    description="Real-time trading signal generation using dynamic strategy execution",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize strategy loader
# The STRATEGIES_DIR is now correctly pointing to backend/strategies
strategy_loader = StrategyLoader(STRATEGIES_DIR)

# Pydantic models
class SignalRequest(BaseModel):
    """Request model for signal generation"""
    symbol: str = Field(..., description="Trading symbol (e.g., NIFTY, BANKNIFTY)")
    strategy_name: str = Field(..., description="Strategy to use (momentum, mean_reversion, etc.)")
    close: Optional[float] = Field(None, description="Current close price")
    prices: Optional[List[float]] = Field(None, description="Historical prices for analysis")
    highs: Optional[List[float]] = Field(None, description="Historical high prices")
    lows: Optional[List[float]] = Field(None, description="Historical low prices")
    volume: Optional[int] = Field(None, description="Current volume")
    timeframe: Optional[str] = Field("1D", description="Timeframe (1m, 5m, 1h, 1D)")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "NIFTY",
                "strategy_name": "momentum",
                "close": 22650.50,
                "prices": [22600, 22620, 22640, 22650.50],
                "highs": [22610, 22630, 22650, 22660],
                "lows": [22590, 22610, 22630, 22640],
                "volume": 1000000,
                "timeframe": "1D"
            }
        }


class SignalResponse(BaseModel):
    """Response model for signals"""
    success: bool
    symbol: str
    strategy: str
    signal: str
    confidence: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    target: Optional[float]
    risk_reward: Optional[float]
    indicators: Optional[Dict[str, Any]]
    reasons: Optional[List[str]]
    timestamp: str


class MultiSignalRequest(BaseModel):
    """Request for multiple symbols"""
    symbols: List[str] = Field(..., description="List of symbols to analyze")
    strategy_name: str = Field(..., description="Strategy to use")
    market_data: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Market data by symbol")


# Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "InfinityAI.Pro Signal Predictor API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "strategies": "/api/strategies",
            "signal": "/api/signal",
            "batch_signals": "/api/batch-signals",
            "live_signal": "/api/live-signal/{symbol}",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        strategies = strategy_loader.list_strategies()
        return {
            "status": "healthy",
            "service": "signal-predictor-api",
            "strategies_loaded": len(strategies),
            "strategies": strategies,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/api/strategies")
async def get_strategies():
    """List all available strategies with details"""
    try:
        strategies = strategy_loader.list_strategies()
        strategy_details = []
        
        for strategy_name in strategies:
            # We need a get_strategy_info method in our loader
            # For now, let's assume it exists or just return names
            try:
                info = strategy_loader.get_strategy_info(strategy_name)
                strategy_details.append({
                    "name": strategy_name,
                    "info": info
                })
            except AttributeError: # In case get_strategy_info doesn't exist
                 strategy_details.append({"name": strategy_name, "info": "Not available"})

        
        return {
            "success": True,
            "count": len(strategies),
            "strategies": strategy_details,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signal")
async def get_signal(
    strategy_name: str = Query(..., description="Strategy to use"),
    symbol: str = Query(..., description="Trading symbol"),
    close: Optional[float] = Query(None, description="Current close price")
):
    """
    Get trading signal for a symbol using specified strategy
    Simple GET endpoint for quick queries
    """
    try:
        if close is None:
            raise HTTPException(
                status_code=400,
                detail="Price data required. Use POST /api/signal for complete data submission."
            )
        
        data = { "symbol": symbol, "close": close, "prices": [close] }
        
        result = strategy_loader.execute_strategy(strategy_name, data)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found or failed")
        
        return SignalResponse(
            success=True,
            symbol=result.get("symbol", symbol),
            strategy=strategy_name,
            signal=result.get("signal", "HOLD"),
            confidence=result.get("confidence", 0.0),
            entry_price=result.get("entry_price"),
            stop_loss=result.get("stop_loss"),
            target=result.get("target"),
            risk_reward=result.get("risk_reward"),
            indicators=result.get("indicators"),
            reasons=result.get("reasons"),
            timestamp=result.get("timestamp", datetime.now().isoformat())
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/signal")
async def post_signal(request: SignalRequest):
    """
    Generate trading signal with complete market data
    """
    try:
        data = {
            "symbol": request.symbol,
            "close": request.close,
            "prices": request.prices or ([request.close] if request.close else []),
            "highs": request.highs or request.prices or [],
            "lows": request.lows or request.prices or [],
            "volume": request.volume or 0
        }
        
        if request.strategy_name not in strategy_loader.list_strategies():
            raise HTTPException(
                status_code=404,
                detail=f"Strategy '{request.strategy_name}' not found. Available: {strategy_loader.list_strategies()}"
            )
        
        logger.info(f"Executing strategy '{request.strategy_name}' for {request.symbol}")
        result = strategy_loader.execute_strategy(request.strategy_name, data)
        
        if result is None:
            raise HTTPException(
                status_code=500,
                detail=f"Strategy execution failed for '{request.strategy_name}'"
            )
        
        return SignalResponse(
            success=True,
            symbol=result.get("symbol", request.symbol),
            strategy=request.strategy_name,
            signal=result.get("signal", "HOLD"),
            confidence=result.get("confidence", 0.0),
            entry_price=result.get("entry_price"),
            stop_loss=result.get("stop_loss"),
            target=result.get("target"),
            risk_reward=result.get("risk_reward"),
            indicators=result.get("indicators"),
            reasons=result.get("reasons"),
            timestamp=result.get("timestamp", datetime.now().isoformat())
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in post_signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/batch-signals")
async def get_batch_signals(request: MultiSignalRequest):
    """
    Get signals for multiple symbols in batch
    """
    try:
        results = []
        
        for symbol in request.symbols:
            if request.market_data and symbol in request.market_data:
                data = request.market_data[symbol]
                data["symbol"] = symbol
            else:
                logger.warning(f"No market data for {symbol}, skipping")
                continue
            
            result = strategy_loader.execute_strategy(request.strategy_name, data)
            
            if result:
                results.append({
                    "symbol": symbol,
                    "signal": result.get("signal", "HOLD"),
                    "confidence": result.get("confidence", 0.0),
                    "entry_price": result.get("entry_price"),
                    "indicators": result.get("indicators"),
                    "reasons": result.get("reasons")
                })
        
        return {
            "success": True,
            "strategy": request.strategy_name,
            "count": len(results),
            "signals": results,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in batch signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live-signal/{symbol}")
async def get_live_signal(
    symbol: str,
    strategy: str = Query("momentum", description="Strategy to use")
):
    """
    Placeholder for live signal generation.
    """
    try:
        logger.info(f"Live signal requested for {symbol} using {strategy}")
        
        # In a real scenario, you would fetch live market data here.
        # Using demo data for now.
        demo_data = {
            "symbol": symbol, "close": 22650.50,
            "prices": [22500 + i*10 for i in range(50)],
            "highs": [22510 + i*10 for i in range(50)],
            "lows": [22490 + i*10 for i in range(50)]
        }
        
        result = strategy_loader.execute_strategy(strategy, demo_data)
        
        if result is None:
            raise HTTPException(status_code=500, detail="Signal generation failed")
        
        return {
            "success": True, "live": False, "demo_mode": True,
            "symbol": symbol, "strategy": strategy,
            "signal": result.get("signal", "HOLD"),
            "confidence": result.get("confidence", 0.0),
            "timestamp": datetime.now().isoformat(),
            "note": "This is a demo response. Integrate a real market data feed."
        }
    
    except Exception as e:
        logger.error(f"Error in live signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Adding a dummy get_strategy_info to the loader if it doesn't exist
# to prevent the app from crashing.
if not hasattr(StrategyLoader, 'get_strategy_info'):
    def get_strategy_info(self, name: str):
        strategy = self.load_strategy(name)
        if hasattr(strategy, 'STRATEGY_INFO'):
            return getattr(strategy, 'STRATEGY_INFO')
        return {"error": f"Strategy '{name}' has no STRATEGY_INFO attribute."}
    StrategyLoader.get_strategy_info = get_strategy_info
    
# Hot-reload endpoint
@app.post("/api/strategy/reload/{strategy_name}")
async def reload_strategy(strategy_name: str):
    """
    Reload a strategy module for development.
    """
    try:
        # Assuming a reload_strategy method exists on the loader
        if not hasattr(strategy_loader, 'reload_strategy'):
            return {"success": False, "message": "Hot-reloading not supported by loader."}

        success = strategy_loader.reload_strategy(strategy_name)
        
        if success:
            return {"success": True, "message": f"Strategy '{strategy_name}' reloaded."}
        else:
            raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found.")
    
    except Exception as e:
        logger.error(f"Error reloading strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Signal Predictor API on port {port}")
    uvicorn.run("signal_api:app", host="0.0.0.0", port=port, reload=True)
