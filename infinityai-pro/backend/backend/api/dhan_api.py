"""
Dhan API Routes - OAuth, Trading, and Data APIs
"""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import json

from services.dhan_api_service import dhan_api_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dhan", tags=["Dhan Integration"])

# ========================
# Request/Response Models
# ========================

class AuthUrlRequest(BaseModel):
    user_id: str

class AuthUrlResponse(BaseModel):
    success: bool
    auth_url: Optional[str] = None
    error: Optional[str] = None

class AccountResponse(BaseModel):
    success: bool
    account: Optional[Dict[str, Any]] = None
    funds: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PortfolioResponse(BaseModel):
    success: bool
    holdings: Optional[Dict[str, Any]] = None
    positions: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class MarketDataResponse(BaseModel):
    success: bool
    quotes: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ========================
# OAuth Authentication Routes
# ========================

@router.post("/auth/get-url", response_model=AuthUrlResponse)
async def get_dhan_auth_url(request: AuthUrlRequest):
    """
    Generate Dhan OAuth URL for user authentication
    
    This URL should be opened in browser to authorize your app with Dhan
    """
    
    try:
        auth_url = dhan_api_service.get_auth_url(request.user_id)
        
        return AuthUrlResponse(
            success=True,
            auth_url=auth_url
        )
        
    except Exception as e:
        logger.error(f"Auth URL generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auth/callback")
async def dhan_auth_callback(
    code: str = Query(..., description="Authorization code from Dhan"),
    state: str = Query(..., description="State parameter with user ID")
):
    """
    OAuth callback endpoint - handles authorization code from Dhan
    
    This endpoint is called automatically by Dhan after user authorization
    """
    
    try:
        logger.info(f"Received Dhan callback - Code: {code[:10]}..., State: {state}")
        
        # Exchange authorization code for access token
        token_result = await dhan_api_service.exchange_code_for_token(code, state)
        
        if token_result.get("success"):
            user_id = token_result.get("user_id")
            
            # Return success response
            return {
                "success": True,
                "message": "Dhan account connected successfully!",
                "user_id": user_id,
                "connected_at": datetime.now().isoformat(),
                "redirect_to": f"https://infinity-ai-9utba60h7-infinityaipro.vercel.app/dashboard?dhan_connected=true"
            }
        else:
            logger.error(f"Token exchange failed: {token_result.get('error')}")
            return {
                "success": False,
                "error": token_result.get("error"),
                "redirect_to": f"https://infinity-ai-9utba60h7-infinityaipro.vercel.app/dashboard?dhan_error=true"
            }
            
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return {
            "success": False,
            "error": str(e),
            "redirect_to": f"https://infinity-ai-9utba60h7-infinityaipro.vercel.app/dashboard?dhan_error=true"
        }

@router.get("/connection-status/{user_id}")
async def get_connection_status(user_id: str):
    """Get user's Dhan connection status"""
    
    try:
        status = dhan_api_service.get_connection_status(user_id)
        
        return {
            "success": True,
            "connection": status
        }
        
    except Exception as e:
        logger.error(f"Connection status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disconnect/{user_id}")
async def disconnect_dhan_account(user_id: str):
    """Disconnect user's Dhan account"""
    
    try:
        disconnected = await dhan_api_service.disconnect_user(user_id)
        
        return {
            "success": disconnected,
            "message": "Dhan account disconnected successfully" if disconnected else "User not connected"
        }
        
    except Exception as e:
        logger.error(f"Disconnect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# Account & Profile Routes
# ========================

@router.get("/account/{user_id}", response_model=AccountResponse)
async def get_account_details(user_id: str):
    """
    Get comprehensive account details including profile and funds
    
    Returns:
    - Account profile (name, email, mobile, PAN, etc.)
    - Funds and margin details
    - Trading permissions and segments
    """
    
    try:
        if not dhan_api_service.is_user_connected(user_id):
            raise HTTPException(status_code=401, detail="User not connected to Dhan")
        
        # Get account details
        account_result = await dhan_api_service.get_account_details(user_id)
        funds_result = await dhan_api_service.get_funds_and_margin(user_id)
        
        if account_result.get("success") and funds_result.get("success"):
            return AccountResponse(
                success=True,
                account=account_result.get("account"),
                funds=funds_result.get("funds")
            )
        else:
            error_msg = account_result.get("error") or funds_result.get("error")
            return AccountResponse(
                success=False,
                error=error_msg
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account details error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# Portfolio Routes  
# ========================

@router.get("/portfolio/{user_id}", response_model=PortfolioResponse)
async def get_portfolio_data(user_id: str):
    """
    Get complete portfolio data including holdings and positions
    
    Returns:
    - Long-term holdings/investments 
    - Live trading positions
    - P&L summary and breakdowns
    - Portfolio allocation and performance
    """
    
    try:
        if not dhan_api_service.is_user_connected(user_id):
            raise HTTPException(status_code=401, detail="User not connected to Dhan")
        
        # Get holdings and positions
        holdings_result = await dhan_api_service.get_holdings(user_id)
        positions_result = await dhan_api_service.get_positions(user_id)
        
        if holdings_result.get("success") and positions_result.get("success"):
            return PortfolioResponse(
                success=True,
                holdings=holdings_result.get("holdings"),
                positions=positions_result.get("positions")
            )
        else:
            error_msg = holdings_result.get("error") or positions_result.get("error")
            return PortfolioResponse(
                success=False,
                error=error_msg
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# Market Data Routes
# ========================

@router.post("/market-data", response_model=MarketDataResponse)
async def get_market_data(symbols: List[str]):
    """
    Get live market data for multiple symbols
    
    Supports:
    - NIFTY, BANKNIFTY, SENSEX indices
    - Individual stocks (RELIANCE, TCS, HDFC, etc.)
    - Real-time prices, changes, volume
    - Technical indicators
    """
    
    try:
        quotes_result = await dhan_api_service.get_live_quote(symbols)
        
        if quotes_result.get("success"):
            return MarketDataResponse(
                success=True,
                quotes=quotes_result.get("quotes")
            )
        else:
            return MarketDataResponse(
                success=False,
                error=quotes_result.get("error")
            )
            
    except Exception as e:
        logger.error(f"Market data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/live/{symbol}")
async def get_live_symbol_data(symbol: str):
    """Get live data for a specific symbol"""
    
    try:
        quotes_result = await dhan_api_service.get_live_quote([symbol])
        
        if quotes_result.get("success"):
            symbol_data = quotes_result.get("quotes", {}).get(symbol.upper())
            
            if symbol_data:
                return {
                    "success": True,
                    "symbol": symbol.upper(),
                    "data": symbol_data,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        else:
            raise HTTPException(status_code=500, detail=quotes_result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Live symbol data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# Trading Routes
# ========================

@router.post("/place-order/{user_id}")
async def place_trading_order(user_id: str, order_data: Dict[str, Any]):
    """
    Place a trading order through Dhan
    
    Supports:
    - Buy/Sell orders
    - Market/Limit/Stop orders
    - Intraday/Delivery products
    - Multiple exchanges (NSE, BSE, MCX, etc.)
    """
    
    try:
        if not dhan_api_service.is_user_connected(user_id):
            raise HTTPException(status_code=401, detail="User not connected to Dhan")
        
        order_result = await dhan_api_service.place_order(user_id, order_data)
        
        if order_result.get("success"):
            return {
                "success": True,
                "order_id": order_result.get("order_id"),
                "status": order_result.get("status"),
                "message": order_result.get("message"),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": order_result.get("error")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Place order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{user_id}")
async def get_order_history(user_id: str):
    """Get order history and status for user"""
    
    try:
        if not dhan_api_service.is_user_connected(user_id):
            raise HTTPException(status_code=401, detail="User not connected to Dhan")
        
        orders_result = await dhan_api_service.get_orders(user_id)
        
        if orders_result.get("success"):
            return {
                "success": True,
                "orders": orders_result.get("orders"),
                "total_orders": orders_result.get("total_orders"),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": orders_result.get("error")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get orders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# Utility Routes
# ========================

@router.get("/supported-symbols")
async def get_supported_symbols():
    """Get list of supported symbols and their Dhan security IDs"""
    
    return {
        "success": True,
        "symbols": {
            "indices": {
                "NIFTY": "25",
                "BANKNIFTY": "26",
                "SENSEX": "1"
            },
            "stocks": {
                "RELIANCE": "2885",
                "TCS": "3456",
                "HDFC": "1330",
                "ICICIBANK": "4963",
                "INFY": "408",
                "HDFCBANK": "1333"
            },
            "sectors": [
                "Banking", "IT", "Pharma", "Auto", "Energy", "FMCG"
            ]
        }
    }

@router.get("/integration-guide")
async def get_integration_guide():
    """
    Get step-by-step guide for Dhan integration
    
    Includes URLs needed for Dhan app setup
    """
    
    return {
        "success": True,
        "integration_guide": {
            "step_1": {
                "title": "Register Your App with Dhan",
                "description": "Create an app in Dhan Developer Console",
                "action": "Visit https://api.dhan.co and create new app"
            },
            "step_2": {
                "title": "Configure URLs",
                "urls": {
                    "redirect_uri": "https://infinity-ai-9utba60h7-infinityaipro.vercel.app/dhan-auth",
                    "postback_url": "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/dhan/auth/callback",
                    "data_postback_url": "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/dhan/data/callback"
                }
            },
            "step_3": {
                "title": "Get Credentials",
                "description": "Copy Client ID and Client Secret from Dhan console",
                "environment_variables": [
                    "DHAN_CLIENT_ID=your_client_id",
                    "DHAN_CLIENT_SECRET=your_client_secret"
                ]
            },
            "step_4": {
                "title": "Test Authorization",
                "endpoint": "/api/dhan/auth/get-url",
                "description": "Generate auth URL and complete OAuth flow"
            }
        }
    }