"""
Dhan Data API Integration (Phase 2)
Single-Tenant real-time 24/7 telemetry endpoints for market quotes, positions, holdings, orders, funds, and option chain.
Primary Owner Client ID: 1101302170 (raghu_primary)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from .dhan_client_wrapper import create_dhan_client
import logging
import os

logger = logging.getLogger(__name__)

PRIMARY_USER_ID = os.getenv("PRIMARY_USER_ID", "raghu_primary")
PRIMARY_CLIENT_ID = os.getenv("PRIMARY_CLIENT_ID", "1101302170")

# Import Options Analytics
try:
    from .options_analytics import get_greeks_calculator
    GREEKS_AVAILABLE = True
except ImportError:
    GREEKS_AVAILABLE = False

# Helper for resolving user credentials
async def get_dhan_client_for_user(user_id: Optional[str] = None):
    """Retrieve and decrypt DhanHQ credentials from Firestore vault with Single-Tenant auto-resolution"""
    from src.user_credentials import get_credentials_manager
    credentials_manager = get_credentials_manager()
    if not credentials_manager:
        raise HTTPException(status_code=503, detail="Credentials manager unavailable")

    resolved_id = await credentials_manager.resolve_user_id(user_id)
    creds_response = await credentials_manager.get_user_credentials(resolved_id)

    if not creds_response:
        raise HTTPException(status_code=401, detail="Dhan credentials not configured in single-tenant vault")

    client_id = creds_response.get("dhan_client_id") or creds_response.get("client_id") or PRIMARY_CLIENT_ID
    access_token = creds_response.get("dhan_access_token") or creds_response.get("access_token")

    if not client_id or not access_token:
        raise HTTPException(status_code=401, detail="Missing client_id or access_token in credentials vault")

    return create_dhan_client(client_id, access_token), client_id, resolved_id


# Create router
data_router = APIRouter(tags=["Dhan Real-Time Telemetry & Market Data"])

# ==============================================================================
# 1. Capital & Margins (/api/dhan/funds)
# ==============================================================================
@data_router.get("/api/dhan/funds")
async def get_dhan_funds(user_id: Optional[str] = Query(None, description="User ID or Dhan Client ID (Defaults to primary vault)")):
    """Live Available Margin, SOD Limit, Collateral Amount, Utilized Margin, Withdrawable Balance"""
    try:
        client, client_id, resolved_id = await get_dhan_client_for_user(user_id)
        funds_resp = client.get_fund_limits()
        
        funds_data = funds_resp.get("data", {}) if isinstance(funds_resp, dict) and "data" in funds_resp else funds_resp
        return {
            "status": "success",
            "user_id": resolved_id,
            "dhan_client_id": client_id,
            "funds": {
                "availableBalance": funds_data.get("availabelBalance", 0) or funds_data.get("availableBalance", 0) or 0,
                "utilizedMargin": funds_data.get("utilizedAmount", 0) or funds_data.get("utilizedMargin", 0) or 0,
                "sodLimit": funds_data.get("sodLimit", 0) or 0,
                "collateralAmount": funds_data.get("collateralAmount", 0) or 0,
                "withdrawableBalance": funds_data.get("withdrawableBalance", 0) or 0,
                "raw": funds_data
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# 2. Active Positions (/api/dhan/positions)
# ==============================================================================
@data_router.get("/api/dhan/positions")
async def get_dhan_positions(user_id: Optional[str] = Query(None, description="User ID or Dhan Client ID (Defaults to primary vault)")):
    """Real-time Unrealized P&L, Realized P&L, Quantities, Buy/Sell Avg Prices, Product Types"""
    try:
        client, client_id, resolved_id = await get_dhan_client_for_user(user_id)
        pos_resp = client.get_positions()
        pos_list = pos_resp.get("data", []) if isinstance(pos_resp, dict) and "data" in pos_resp else (pos_resp if isinstance(pos_resp, list) else [])
        
        total_unrealized = sum(p.get("unrealizedProfit", 0) for p in pos_list if isinstance(p, dict))
        total_realized = sum(p.get("realizedProfit", 0) for p in pos_list if isinstance(p, dict))
        
        return {
            "status": "success",
            "user_id": resolved_id,
            "dhan_client_id": client_id,
            "count": len(pos_list),
            "summary": {
                "totalUnrealizedPnl": total_unrealized,
                "totalRealizedPnl": total_realized,
                "netPnl": total_unrealized + total_realized
            },
            "positions": pos_list,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# 3. Equity Holdings (/api/dhan/holdings)
# ==============================================================================
@data_router.get("/api/dhan/holdings")
async def get_dhan_holdings(user_id: Optional[str] = Query(None, description="User ID or Dhan Client ID (Defaults to primary vault)")):
    """Portfolio Value, Total Investment Cost, Overall P&L %, Stocks List, ISIN, Day's Gain/Loss"""
    try:
        client, client_id, resolved_id = await get_dhan_client_for_user(user_id)
        hold_resp = client.get_holdings()
        hold_list = hold_resp.get("data", []) if isinstance(hold_resp, dict) and "data" in hold_resp else (hold_resp if isinstance(hold_resp, list) else [])
        
        total_value = sum(h.get("currentValue", 0) or (h.get("buyAvg", 0) * h.get("totalQty", 0)) for h in hold_list if isinstance(h, dict))
        total_invested = sum(h.get("investedValue", 0) or (h.get("buyAvg", 0) * h.get("totalQty", 0)) for h in hold_list if isinstance(h, dict))
        
        return {
            "status": "success",
            "user_id": resolved_id,
            "dhan_client_id": client_id,
            "count": len(hold_list),
            "summary": {
                "totalValue": total_value,
                "totalInvested": total_invested,
                "overallPnl": total_value - total_invested
            },
            "holdings": hold_list,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# 4. Order Book & History (/api/dhan/orders)
# ==============================================================================
@data_router.get("/api/dhan/orders")
async def get_dhan_orders(user_id: Optional[str] = Query(None, description="User ID or Dhan Client ID (Defaults to primary vault)")):
    """Live Pending Orders, Executed Orders, Cancelled/Rejected Reasons, Average Execution Price"""
    try:
        client, client_id, resolved_id = await get_dhan_client_for_user(user_id)
        orders_resp = client.get_order_list()
        orders_list = orders_resp.get("data", []) if isinstance(orders_resp, dict) and "data" in orders_resp else (orders_resp if isinstance(orders_resp, list) else [])
        
        return {
            "status": "success",
            "user_id": resolved_id,
            "dhan_client_id": client_id,
            "count": len(orders_list),
            "orders": orders_list,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# 5. Trade Ledger (/api/dhan/trades)
# ==============================================================================
@data_router.get("/api/dhan/trades")
async def get_dhan_trades(user_id: Optional[str] = Query(None, description="User ID or Dhan Client ID (Defaults to primary vault)")):
    """Completed Execution Logs, Order Fill Rates, Execution Price"""
    try:
        client, client_id, resolved_id = await get_dhan_client_for_user(user_id)
        trades_resp = client.get_trade_book()
        trades_list = trades_resp.get("data", []) if isinstance(trades_resp, dict) and "data" in trades_resp else (trades_resp if isinstance(trades_resp, list) else [])
        
        return {
            "status": "success",
            "user_id": resolved_id,
            "dhan_client_id": client_id,
            "count": len(trades_list),
            "trades": trades_list,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# 6. Live Market Quotes (/api/dhan/market/quotes)
# ==============================================================================
@data_router.get("/api/dhan/market/quotes")
async def get_market_quotes(
    security_ids: str = Query("1333,11536", description="Comma-separated security IDs"),
    exchange_segment: str = Query("NSE_EQ", description="Exchange segment"),
    user_id: Optional[str] = Query(None, description="User ID or Client ID (Defaults to primary vault)")
):
    """Live LTP, Open, High, Low, Close, Volume, VWAP, Change %"""
    try:
        client, client_id, resolved_id = await get_dhan_client_for_user(user_id)
        sec_ids = [int(s.strip()) for s in security_ids.split(",") if s.strip()]
        securities = {exchange_segment: sec_ids}
        ohlc_response = client.ohlc_data(securities=securities)
        
        return {
            "status": "success",
            "data": ohlc_response,
            "exchange_segment": exchange_segment,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# 7. Option Chain & Greeks (/api/dhan/optionchain & /api/dhan/market/optionchain)
# ==============================================================================
@data_router.get("/api/dhan/optionchain")
@data_router.get("/api/dhan/market/optionchain")
async def get_option_chain(
    under_security_id: int = Query(13, description="Underlying security ID (13 for NIFTY, 25 for BANKNIFTY)"),
    under_exchange_segment: str = Query("IDX_I", description="Underlying exchange segment"),
    expiry: Optional[str] = Query(None, description="Expiry date (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="User ID or Client ID (Defaults to primary vault)")
):
    """Delta, Gamma, Theta, Vega, Implied Volatility (IV), Put-Call Ratio (PCR), Open Interest (OI)"""
    try:
        client, client_id, resolved_id = await get_dhan_client_for_user(user_id)
        
        # If expiry is not passed, fetch today's or next weekly expiry
        exp = expiry or (datetime.now() + timedelta(days=(3 - datetime.now().weekday()) % 7)).strftime("%Y-%m-%d")
        option_chain = client.option_chain(
            under_security_id=under_security_id,
            under_exchange_segment=under_exchange_segment,
            expiry=exp
        )
        
        return {
            "status": "success",
            "data": option_chain,
            "underlying": under_security_id,
            "expiry": exp,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@data_router.post("/api/dhan/options/sync-bigquery")
@data_router.get("/api/dhan/options/sync-bigquery")
async def sync_options_to_bigquery(
    user_id: Optional[str] = Query("raghu_primary", description="User ID for vault credentials")
):
    """Real-time pipeline to stream live Option Chain ticks for NIFTY, BANKNIFTY, SENSEX, FINNIFTY into BigQuery"""
    try:
        from .options_chain_ingestor import options_ingestor
        result = await options_ingestor.ingest_live_option_chains(user_id=user_id or "raghu_primary")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync options to BigQuery: {e}")



# ==============================================================================
# 8. Historical Chart Data (/api/dhan/market/historical)
# ==============================================================================
@data_router.get("/api/dhan/market/historical")
async def get_historical_data(
    security_id: str = Query("13", description="Security ID"),
    exchange_segment: str = Query("IDX_I", description="Exchange segment"),
    instrument_type: str = Query("INDEX", description="Instrument type"),
    from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query("daily", description="Interval: daily or minute"),
    user_id: Optional[str] = Query(None, description="User ID or Client ID (Defaults to primary vault)")
):
    """Get historical OHLCV data for charting"""
    try:
        client, client_id, resolved_id = await get_dhan_client_for_user(user_id)
        if interval == "daily":
            historical_data = client.historical_daily_data(
                security_id=security_id,
                exchange_segment=exchange_segment,
                instrument_type=instrument_type,
                from_date=from_date,
                to_date=to_date
            )
        else:
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


# ==============================================================================
# 9. Market Depth (/api/dhan/market/depth)
# ==============================================================================
@data_router.get("/api/dhan/market/depth")
async def get_market_depth(
    security_ids: str = Query("1333", description="Comma-separated security IDs"),
    exchange_segment: str = Query("NSE_EQ", description="Exchange segment"),
    user_id: Optional[str] = Query(None, description="User ID or Client ID (Defaults to primary vault)")
):
    """Get market depth (order book) via quote_data"""
    try:
        client, client_id, resolved_id = await get_dhan_client_for_user(user_id)
        sec_ids = [int(s.strip()) for s in security_ids.split(",") if s.strip()]
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
