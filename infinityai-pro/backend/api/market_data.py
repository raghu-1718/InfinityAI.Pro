"""
Market Data API Endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from services.market_data_manager import market_data_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["Market Data"])

class MarketDataRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    limit: int = 100

@router.get("/quote/{symbol}")
async def get_real_time_quote(symbol: str):
    """Get real-time quote for symbol"""
    
    try:
        quote = await market_data_manager.get_real_time_quote(symbol)
        
        return {
            "success": True,
            "symbol": symbol,
            "data": quote,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get quote for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical/{symbol}")
async def get_historical_data(symbol: str, timeframe: str = "1h", limit: int = 100):
    """Get historical data for symbol"""
    
    try:
        data = await market_data_manager.get_historical_data(symbol, timeframe, limit)
        
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get historical data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/indices")
async def get_major_indices():
    """Get major market indices"""
    
    try:
        indices = ['NIFTY', 'BANKNIFTY', 'SENSEX', 'NIFTY_MIDCAP', 'NIFTY_SMALLCAP']
        results = {}
        
        for index in indices:
            try:
                quote = await market_data_manager.get_real_time_quote(index)
                results[index] = quote
            except Exception as e:
                logger.error(f"Failed to get {index}: {e}")
                results[index] = {"error": str(e)}
        
        return {
            "success": True,
            "indices": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/{symbol}")
async def get_market_news(symbol: str, limit: int = 20):
    """Get market news for symbol"""
    
    try:
        news = await market_data_manager.get_market_news(symbol, limit)
        
        return {
            "success": True,
            "symbol": symbol,
            "news": news,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment/{symbol}")
async def get_social_sentiment(symbol: str):
    """Get social sentiment for symbol"""
    
    try:
        sentiment = await market_data_manager.get_social_sentiment(symbol)
        
        return {
            "success": True,
            "symbol": symbol,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get sentiment for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))