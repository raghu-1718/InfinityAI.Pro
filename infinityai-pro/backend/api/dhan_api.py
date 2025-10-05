"""
Dhan API Router - Integration with Dhan trading platform
Provides market data, trading operations, and OAuth integration
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.dhan_api_service import dhan_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dhan", tags=["Dhan Integration"])

class MarketDataRequest(BaseModel):
    symbols: List[str]
    quote_type: Optional[str] = "real_time"

class SingleSymbolRequest(BaseModel):
    symbol: str

@router.get("/status")
async def get_dhan_status():
    """
    Get Dhan API service status and connectivity
    """
    try:
        # Test connectivity with a simple request
        test_result = await dhan_service.get_market_quote(['NSE_IDX|Nifty 50'])
        
        is_connected = test_result is not None and 'data' in test_result
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "dhan_api": {
                "connected": is_connected,
                "service_status": "operational" if is_connected else "disconnected",
                "base_url": "https://api.dhan.co",
                "version": "v2"
            },
            "authentication": {
                "api_key_configured": bool(dhan_service.api_key),
                "access_token_configured": bool(dhan_service.access_token)
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking Dhan status: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "dhan_api": {
                "connected": False,
                "service_status": "error",
                "error": str(e)
            }
        }

@router.post("/market-data")
async def get_market_data(request: MarketDataRequest):
    """
    Get real-time market data for multiple symbols
    """
    try:
        if not request.symbols:
            raise HTTPException(status_code=400, detail="At least one symbol is required")
        
        if len(request.symbols) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 symbols allowed per request")
        
        # Get market quotes
        market_data = await dhan_service.get_market_quote(request.symbols)
        
        if not market_data or 'data' not in market_data:
            raise HTTPException(status_code=404, detail="No market data available")
        
        # Format response
        formatted_data = []
        for symbol, data in market_data['data'].items():
            formatted_data.append({
                "symbol": symbol,
                "ltp": data.get('LTP', 0),
                "open": data.get('open', 0),
                "high": data.get('high', 0),
                "low": data.get('low', 0),
                "close": data.get('close', 0),
                "volume": data.get('volume', 0),
                "change": data.get('change', 0),
                "change_percent": data.get('pChange', 0),
                "timestamp": data.get('timestamp', datetime.now().isoformat())
            })
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_symbols": len(formatted_data),
            "data": formatted_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=f"Market data request failed: {str(e)}")

@router.get("/market-data/{symbol}")
async def get_single_symbol_data(symbol: str):
    """
    Get market data for a single symbol
    """
    try:
        market_data = await dhan_service.get_market_quote([symbol])
        
        if not market_data or 'data' not in market_data or symbol not in market_data['data']:
            raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")
        
        data = market_data['data'][symbol]
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "data": {
                "ltp": data.get('LTP', 0),
                "open": data.get('open', 0),
                "high": data.get('high', 0),
                "low": data.get('low', 0),
                "close": data.get('close', 0),
                "volume": data.get('volume', 0),
                "change": data.get('change', 0),
                "change_percent": data.get('pChange', 0),
                "timestamp": data.get('timestamp', datetime.now().isoformat()),
                "52_week_high": data.get('52WeekHigh', 0),
                "52_week_low": data.get('52WeekLow', 0),
                "market_cap": data.get('marketCap', 0),
                "pe_ratio": data.get('peRatio', 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data for symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Symbol data request failed: {str(e)}")

@router.get("/supported-symbols")
async def get_supported_symbols():
    """
    Get list of supported symbols and instruments
    """
    try:
        # This would ideally come from Dhan's instrument master
        # For now, return a curated list
        
        symbols = {
            "indices": [
                {
                    "symbol": "NSE_IDX|Nifty 50",
                    "name": "Nifty 50",
                    "exchange": "NSE",
                    "type": "INDEX",
                    "segment": "EQUITY"
                },
                {
                    "symbol": "NSE_IDX|Nifty Bank",
                    "name": "Nifty Bank",
                    "exchange": "NSE", 
                    "type": "INDEX",
                    "segment": "EQUITY"
                },
                {
                    "symbol": "NSE_IDX|Nifty IT",
                    "name": "Nifty IT",
                    "exchange": "NSE",
                    "type": "INDEX", 
                    "segment": "EQUITY"
                }
            ],
            "equities": [
                {
                    "symbol": "NSE_EQ|INE062A01020",
                    "name": "TCS",
                    "exchange": "NSE",
                    "type": "EQUITY",
                    "segment": "EQ",
                    "sector": "Information Technology"
                },
                {
                    "symbol": "NSE_EQ|INE009A01021", 
                    "name": "Infosys",
                    "exchange": "NSE",
                    "type": "EQUITY",
                    "segment": "EQ",
                    "sector": "Information Technology"
                },
                {
                    "symbol": "NSE_EQ|INE040A01034",
                    "name": "HDFC Bank",
                    "exchange": "NSE",
                    "type": "EQUITY",
                    "segment": "EQ", 
                    "sector": "Financial Services"
                },
                {
                    "symbol": "NSE_EQ|INE002A01018",
                    "name": "Reliance Industries",
                    "exchange": "NSE",
                    "type": "EQUITY",
                    "segment": "EQ",
                    "sector": "Oil Gas & Consumable Fuels"
                },
                {
                    "symbol": "NSE_EQ|INE467B01029",
                    "name": "ITC",
                    "exchange": "NSE", 
                    "type": "EQUITY",
                    "segment": "EQ",
                    "sector": "Fast Moving Consumer Goods"
                }
            ]
        }
        
        total_symbols = len(symbols["indices"]) + len(symbols["equities"])
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_symbols": total_symbols,
            "categories": {
                "indices": len(symbols["indices"]),
                "equities": len(symbols["equities"])
            },
            "symbols": symbols
        }
        
    except Exception as e:
        logger.error(f"Error getting supported symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported symbols: {str(e)}")

@router.get("/portfolio")
async def get_portfolio():
    """
    Get user's portfolio information
    """
    try:
        # This would get actual portfolio data from Dhan
        # For now, return mock data
        
        portfolio_data = {
            "account_info": {
                "account_id": "DHAN123456",
                "client_name": "Demo User",
                "account_type": "INDIVIDUAL",
                "status": "ACTIVE"
            },
            "holdings": [
                {
                    "symbol": "NSE_EQ|INE062A01020",
                    "name": "TCS",
                    "quantity": 100,
                    "avg_price": 3450.00,
                    "current_price": 3520.25,
                    "invested_value": 345000.00,
                    "current_value": 352025.00,
                    "pnl": 7025.00,
                    "pnl_percent": 2.04,
                    "sector": "IT"
                },
                {
                    "symbol": "NSE_EQ|INE040A01034",
                    "name": "HDFC Bank",
                    "quantity": 50,
                    "avg_price": 1680.50,
                    "current_price": 1725.75,
                    "invested_value": 84025.00,
                    "current_value": 86287.50,
                    "pnl": 2262.50,
                    "pnl_percent": 2.69,
                    "sector": "Banking"
                }
            ],
            "positions": [],
            "summary": {
                "total_invested": 429025.00,
                "current_value": 438312.50,
                "total_pnl": 9287.50,
                "total_pnl_percent": 2.16,
                "available_margin": 50000.00,
                "used_margin": 0.00
            }
        }
        
        return {
            "status": "success", 
            "timestamp": datetime.now().isoformat(),
            "portfolio": portfolio_data
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Portfolio request failed: {str(e)}")

@router.get("/orders")
async def get_orders(status: Optional[str] = None):
    """
    Get order history and status
    """
    try:
        # This would get actual order data from Dhan
        # For now, return mock data
        
        orders = [
            {
                "order_id": "DH12345001",
                "symbol": "NSE_EQ|INE062A01020", 
                "name": "TCS",
                "order_type": "LIMIT",
                "transaction_type": "BUY",
                "quantity": 10,
                "price": 3500.00,
                "status": "COMPLETE",
                "executed_quantity": 10,
                "executed_price": 3498.50,
                "order_time": "2025-01-04T09:15:30",
                "execution_time": "2025-01-04T09:16:45"
            },
            {
                "order_id": "DH12345002",
                "symbol": "NSE_EQ|INE040A01034",
                "name": "HDFC Bank", 
                "order_type": "MARKET",
                "transaction_type": "BUY",
                "quantity": 5,
                "price": 0.00,
                "status": "PENDING",
                "executed_quantity": 0,
                "executed_price": 0.00,
                "order_time": "2025-01-04T10:30:15",
                "execution_time": None
            }
        ]
        
        # Filter by status if provided
        if status:
            orders = [order for order in orders if order["status"] == status.upper()]
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(), 
            "total_orders": len(orders),
            "orders": orders
        }
        
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail=f"Orders request failed: {str(e)}")

@router.get("/health")
async def dhan_health_check():
    """
    Health check for Dhan API integration
    """
    try:
        # Test basic connectivity
        test_result = await dhan_service.get_market_quote(['NSE_IDX|Nifty 50'])
        is_healthy = test_result is not None
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Dhan API Integration",
            "version": "v2",
            "connectivity": {
                "api_accessible": is_healthy,
                "authentication": "configured" if dhan_service.access_token else "missing",
                "base_url": "https://api.dhan.co"
            }
        }
        
    except Exception as e:
        logger.error(f"Dhan health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Dhan API Integration",
            "error": str(e)
        }