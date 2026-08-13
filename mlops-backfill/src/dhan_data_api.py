"""
Dhan Data API Integration (Phase 2) - CORRECTED

New endpoints for real-time market data using user's API Key/Secret.
Uses dhanhq library for market data access with CORRECT method signatures.
Enhanced with Options Analytics and Greeks calculations.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from .dhan_client_wrapper import create_dhan_client
import numpy as np

# Import Options Analytics
try:
    from .options_analytics import get_greeks_calculator
    GREEKS_AVAILABLE = True
except ImportError:
    GREEKS_AVAILABLE = False

# Response models
class MarketQuoteResponse(BaseModel):
    status: str
    data: dict

class HistoricalDataResponse(BaseModel):
    status: str
    data: List[dict]
    
class OptionChainResponse(BaseModel):
    status: str
    data: dict

# Create router
data_router = APIRouter(prefix="/api/dhan/market", tags=["Market Data"])

@data_router.get("/quotes")
async def get_market_quotes(
    security_ids: str = Query(..., description="Comma-separated security IDs"),
    exchange_segment: str = Query("NSE_EQ", description="Exchange segment"),
    user_id: str = Query(..., description="User ID for credential lookup")
):
    """
    Get real-time market quotes (OHLC data) for given security IDs.
    Uses Dhan ohlc_data API.
    """
    try:
        from src.user_credentials import get_credentials_manager
        
        credentials_manager = get_credentials_manager()
        if not credentials_manager:
            raise HTTPException(status_code=503, detail="Credentials manager unavailable")
        
        # Get user credentials
        creds_response = await credentials_manager.get_user_credentials(user_id)
        if not creds_response or not creds_response.get("credentials"):
            raise HTTPException(status_code=401, detail="API credentials not configured")
        
        # Extract decrypted credentials from nested dict
        creds = creds_response["credentials"]
        
        # Use dhanhq REST API for quotes
        from dhanhq import dhanhq
        client = create_dhan_client(creds["client_id"], creds["access_token"])
        
        # Parse security IDs
        sec_ids = [int(s.strip()) for s in security_ids.split(",")]
        
        # Fetch OHLC data - format: {exchange_segment: [security_ids]}
        securities = {exchange_segment: sec_ids}
        ohlc_response = client.ohlc_data(securities=securities)
        
        return {
            "status": "success",
            "data": ohlc_response,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@data_router.get("/historical")
async def get_historical_data(
    security_id: str = Query(..., description="Security ID"),
    exchange_segment: str = Query(..., description="Exchange segment (NSE_EQ, NSE_FNO, etc)"),
    instrument_type: str = Query(..., description="Instrument type (EQUITY, INDEX, etc)"),
    from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query("daily", description="Interval: daily or minute"),
    user_id: str = Query(..., description="User ID")
):
    """
    Get historical OHLCV data (up to 5 years) for charting.
    Uses Dhan Historical Data API.
    """
    try:
        from src.user_credentials import get_credentials_manager
        
        credentials_manager = get_credentials_manager()
        if not credentials_manager:
            raise HTTPException(status_code=503, detail="Credentials manager unavailable")
        
        creds_response = await credentials_manager.get_user_credentials(user_id)
        if not creds_response or not creds_response.get("credentials"):
            raise HTTPException(status_code=401, detail="API credentials not configured")
        
        creds = creds_response["credentials"]
        
        # Use dhanhq library to fetch historical data
        from dhanhq import dhanhq
        client = create_dhan_client(creds["client_id"], creds["access_token"])
        
        # Fetch historical data using correct method signature
        if interval == "daily":
            historical_data = client.historical_daily_data(
                security_id=security_id,
                exchange_segment=exchange_segment,
                instrument_type=instrument_type,
                from_date=from_date,
                to_date=to_date
            )
        else:
            # Intraday minute data
            historical_data = client.intraday_minute_data(
                security_id=security_id,
                exchange_segment=exchange_segment,
                instrument_type=instrument_type,
                from_date=from_date,
                to_date=to_date
            )
        
        return {
            "status": "success",
            "data": historical_data if historical_data else [],
            "symbol": security_id,
            "from": from_date,
            "to": to_date,
            "interval": interval
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@data_router.get("/depth")
async def get_market_depth(
    security_ids: str = Query(..., description="Comma-separated security IDs"),
    exchange_segment: str = Query("NSE_EQ", description="Exchange segment"),
    user_id: str = Query(..., description="User ID")
):
    """
    Get market depth (order book) via quote_data (includes full market depth).
    """
    try:
        from src.user_credentials import get_credentials_manager
        
        credentials_manager = get_credentials_manager()
        if not credentials_manager:
            raise HTTPException(status_code=503, detail="Credentials manager unavailable")
        
        creds_response = await credentials_manager.get_user_credentials(user_id)
        if not creds_response or not creds_response.get("credentials"):
            raise HTTPException(status_code=401, detail="Credentials not found")
        
        creds = creds_response["credentials"]
        
        from dhanhq import dhanhq
        client = create_dhan_client(creds["client_id"], creds["access_token"])
        
        # Parse security IDs
        sec_ids = [int(s.strip()) for s in security_ids.split(",")]
        
        # Fetch quote data (includes market depth)
        securities = {exchange_segment: sec_ids}
        depth_data = client.quote_data(securities=securities)
        
        return {
            "status": "success",
            "data": depth_data,
            "exchange_segment": exchange_segment
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@data_router.get("/options/chain")
async def get_option_chain(
    under_security_id: int = Query(..., description="Underlying security ID (e.g., 13 for NIFTY)"),
    under_exchange_segment: str = Query(..., description="Underlying exchange segment (e.g., IDX_I)"),
    expiry: str = Query(..., description="Expiry date (YYYY-MM-DD)"),
    user_id: str = Query(..., description="User ID")
):
    """
    Get option chain data for a given underlying and expiry.
    """
    try:
        from src.user_credentials import get_credentials_manager
        
        credentials_manager = get_credentials_manager()
        if not credentials_manager:
            raise HTTPException(status_code=503, detail="Credentials manager unavailable")
        
        creds_response = await credentials_manager.get_user_credentials(user_id)
        if not creds_response or not creds_response.get("credentials"):
            raise HTTPException(status_code=401, detail="Credentials not found")
        
        creds = creds_response["credentials"]
        
        from dhanhq import dhanhq
        client = create_dhan_client(creds["client_id"], creds["access_token"])
        
        # Fetch option chain with correct parameters
        option_chain = client.option_chain(
            under_security_id=under_security_id,
            under_exchange_segment=under_exchange_segment,
            expiry=expiry
        )
        
        return {
            "status": "success",
            "data": option_chain,
            "underlying": under_security_id,
            "expiry": expiry
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@data_router.get("/options/expired")
async def get_expired_options(
    security_id: int = Query(..., description="Security ID"),
    exchange_segment: str = Query(..., description="Exchange segment"),
    instrument_type: str = Query(..., description="Instrument type"),
    expiry_flag: str = Query(..., description="MONTH or WEEK"),
    expiry_code: int = Query(..., description="Expiry code"),
    strike: str = Query(..., description="Strike (ATM, ITM, OTM or specific price)"),
    drv_option_type: str = Query(..., description="CALL or PUT"),
    from_date: str = Query(..., description="From date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="To date (YYYY-MM-DD)"),
    user_id: str = Query(..., description="User ID")
):
    """
    Get expired options data for analysis.
    """
    try:
        from src.user_credentials import get_credentials_manager
        
        credentials_manager = get_credentials_manager()
        if not credentials_manager:
            raise HTTPException(status_code=503, detail="Credentials manager unavailable")
        
        creds_response = await credentials_manager.get_user_credentials(user_id)
        if not creds_response or not creds_response.get("credentials"):
            raise HTTPException(status_code=401, detail="Credentials not found")
        
        creds = creds_response["credentials"]
        
        from dhanhq import dhanhq
        client = create_dhan_client(creds["client_id"], creds["access_token"])
        
        # Fetch expired options data
        expired_data = client.expired_options_data(
            security_id=security_id,
            exchange_segment=exchange_segment,
            instrument_type=instrument_type,
            expiry_flag=expiry_flag,
            expiry_code=expiry_code,
            strike=strike,
            drv_option_type=drv_option_type,
            required_data=["open", "high", "low", "close", "volume"],
            from_date=from_date,
            to_date=to_date
        )
        
        return {
            "status": "success",
            "data": expired_data if expired_data else [],
            "security_id": security_id,
            "from": from_date,
            "to": to_date
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@data_router.get("/commodities/quotes")
async def get_commodity_quotes(
    symbols: Optional[str] = Query(None, description="Comma-separated commodity symbols (GOLD,SILVER,CRUDEOIL,NATURALGAS)"),
    user_id: str = Query(..., description="User ID")
):
    """
    Get real-time quotes for MCX commodity futures.
    If no symbols specified, returns quotes for all active commodities.
    """
    try:
        from src.user_credentials import get_credentials_manager
        from src.commodity_utils import get_active_commodities, get_commodity_by_symbol, get_commodity_trading_window
        
        # Get user credentials
        credentials_manager = get_credentials_manager()
        if not credentials_manager:
            raise HTTPException(status_code=503, detail="Credentials manager unavailable")
        
        creds_response = await credentials_manager.get_user_credentials(user_id)
        if not creds_response or not creds_response.get("credentials"):
            raise HTTPException(status_code=401, detail="Credentials not found")
        
        creds = creds_response["credentials"]
        
        from dhanhq import dhanhq
        client = create_dhan_client(creds["client_id"], creds["access_token"])
        
        # Get commodity configuration
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
            commodities = [get_commodity_by_symbol(s) for s in symbol_list]
            commodities = [c for c in commodities if c is not None]
        else:
            commodities = get_active_commodities()
        
        if not commodities:
            raise HTTPException(status_code=404, detail="No active commodities found")
        
        # Fetch quotes for all commodities
        quotes = []
        for commodity in commodities:
            try:
                # Fetch OHLC data for MCX commodity
                securities = {commodity['exchange_segment']: [int(commodity['security_id'])]}
                ohlc_response = client.ohlc_data(securities=securities)
                
                quotes.append({
                    "symbol": commodity['symbol'],
                    "display_name": commodity['display_name'],
                    "security_id": commodity['security_id'],
                    "lot_size": commodity['lot_size'],
                    "quote": ohlc_response.get('data', {}) if ohlc_response else {},
                    "exchange": commodity['exchange_segment']
                })
            except Exception as e:
                print(f"⚠️ Error fetching quote for {commodity['symbol']}: {e}")
                quotes.append({
                    "symbol": commodity['symbol'],
                    "display_name": commodity['display_name'],
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "data": quotes,
            "market_status": get_commodity_trading_window(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@data_router.get("/commodities/status")
async def get_commodity_market_status():
    """
    Get MCX commodity market status and trading hours.
    """
    try:
        from src.commodity_utils import get_commodity_trading_window, get_active_commodities
        
        return {
            "status": "success",
            "market_window": get_commodity_trading_window(),
            "active_commodities": [
                {
                    "symbol": c['symbol'],
                    "display_name": c['display_name'],
                    "lot_size": c['lot_size']
                }
                for c in get_active_commodities()
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
