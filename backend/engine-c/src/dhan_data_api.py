"""
Dhan Data API Integration (Phase 2)
Single-Tenant real-time 24/7 telemetry endpoints for market quotes, positions, holdings, orders, funds, and option chain.
Primary Owner Client ID: 1101302170 (raghu_primary)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
try:
    from .dhan_client_wrapper import create_dhan_client
except ImportError:
    from dhan_client_wrapper import create_dhan_client
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
        logger.error(f"❌ Dhan credentials not found for resolved_id: {resolved_id}")
        raise HTTPException(status_code=401, detail="Dhan credentials not configured in single-tenant vault")

    client_id = creds_response.get("dhan_client_id") or creds_response.get("client_id") or PRIMARY_CLIENT_ID
    access_token = creds_response.get("dhan_access_token") or creds_response.get("access_token")

    if not client_id or not access_token:
        raise HTTPException(status_code=401, detail="Missing client_id or access_token in credentials vault")

    # CRITICAL: Strip trailing \r\n from decrypted credentials.
    # Dhan token renewal and Firestore reads can inject trailing newlines
    # causing 'Invalid leading whitespace, reserved character(s)' HTTP header errors.
    client_id = str(client_id).strip()
    access_token = str(access_token).strip()

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
        
        # Safe parsing: Dhan SDK may return a string on auth/network failure instead of dict
        if isinstance(funds_resp, str):
            logger.error(f"Dhan get_fund_limits returned string instead of dict: {funds_resp[:200]}")
            raise HTTPException(status_code=502, detail=f"Dhan API returned unexpected format: {funds_resp[:200]}")
        funds_data = funds_resp.get("data", {}) if isinstance(funds_resp, dict) and "data" in funds_resp else (funds_resp if isinstance(funds_resp, dict) else {})
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
        # Safe parsing: Dhan SDK may return a string on auth/network failure
        if isinstance(pos_resp, str):
            logger.error(f"Dhan get_positions returned string instead of dict: {pos_resp[:200]}")
            raise HTTPException(status_code=502, detail=f"Dhan API returned unexpected format: {pos_resp[:200]}")
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
        # Safe parsing: Dhan SDK may return a string on auth/network failure
        if isinstance(hold_resp, str):
            logger.error(f"Dhan get_holdings returned string instead of dict: {hold_resp[:200]}")
            raise HTTPException(status_code=502, detail=f"Dhan API returned unexpected format: {hold_resp[:200]}")
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
        # Safe parsing: Dhan SDK may return a string on auth/network failure
        if isinstance(orders_resp, str):
            logger.error(f"Dhan get_order_list returned string instead of dict: {orders_resp[:200]}")
            raise HTTPException(status_code=502, detail=f"Dhan API returned unexpected format: {orders_resp[:200]}")
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
        # Safe parsing: Dhan SDK may return a string on auth/network failure
        if isinstance(trades_resp, str):
            logger.error(f"Dhan get_trade_book returned string instead of dict: {trades_resp[:200]}")
            raise HTTPException(status_code=502, detail=f"Dhan API returned unexpected format: {trades_resp[:200]}")
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
# Helper Utilities for Robust Parameter & Exchange Segment Normalization
# ==============================================================================
import re

def normalize_exchange_segment(seg: Optional[str]) -> str:
    """Normalizes various exchange segment aliases to standard DhanHQ v2 segments."""
    s = (seg or "").strip().upper()
    if s in ("IDX_I", "INDEX", "NSE_INDEX", "NSE_IDX", "IDX", "INDICES"):
        return "IDX_I"
    if s in ("NSE_FNO", "FNO", "NFO", "NSE_FUT", "NSE_OPT"):
        return "NSE_FNO"
    if s in ("NSE_EQ", "NSE", "EQUITY", "EQ"):
        return "NSE_EQ"
    if s in ("MCX_COMM", "MCX", "COMMODITY", "COMM"):
        return "MCX_COMM"
    if s in ("BSE_EQ", "BSE"):
        return "BSE_EQ"
    if s in ("BSE_FNO", "BFO"):
        return "BSE_FNO"
    return s or "NSE_EQ"

def parse_security_ids(sec_param: Any, fallback_param: Any = None) -> List[int]:
    """Safely extracts integer security IDs regardless of parameter swap or string tokens."""
    text = str(sec_param or "")
    digits = re.findall(r"\d+", text)
    if not digits and fallback_param:
        digits = re.findall(r"\d+", str(fallback_param))
    if not digits:
        return [13, 25] # Default NIFTY, BANKNIFTY
    return [int(d) for d in digits]


# ==============================================================================
# 5B. Dhan Connection Status & Token Management
# ==============================================================================
class DhanCredentialUpdateRequest(BaseModel):
    client_id: str
    access_token: str
    user_id: Optional[str] = "raghu_primary"

@data_router.get("/api/dhan/connection/status")
async def get_dhan_connection_status(
    user_id: Optional[str] = Query(None, description="User ID or Dhan Client ID")
):
    """
    Live 24/7 DhanHQ API connection probe.
    Tests credentials against live DhanHQ servers and reports authentication health.
    """
    try:
        from src.user_credentials import get_credentials_manager
        mgr = get_credentials_manager()
        resolved_id = await mgr.resolve_user_id(user_id)
        creds = await mgr.get_user_credentials(resolved_id)
        if not creds or not creds.get("access_token"):
            return {
                "status": "not_configured",
                "is_authenticated": False,
                "client_id": PRIMARY_CLIENT_ID,
                "message": "DhanHQ access token not found in single-tenant Firestore vault"
            }

        client_id = creds.get("client_id") or PRIMARY_CLIENT_ID
        access_token = creds.get("access_token")
        client = create_dhan_client(client_id, access_token)

        # Probe live fundlimit endpoint
        funds_resp = client.get_fund_limits()
        is_auth_ok = True
        err_msg = None

        if isinstance(funds_resp, dict):
            if funds_resp.get("status") == "failed" or "errorCode" in funds_resp or "errorType" in funds_resp:
                is_auth_ok = False
                err_msg = funds_resp.get("errorMessage") or funds_resp.get("remarks") or str(funds_resp)

        return {
            "status": "connected" if is_auth_ok else "auth_expired",
            "is_authenticated": is_auth_ok,
            "dhan_client_id": client_id,
            "user_id": resolved_id,
            "token_preview": f"{access_token[:12]}...{access_token[-6:]}" if len(access_token) > 20 else "***",
            "error_detail": err_msg,
            "verified_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "is_authenticated": False,
            "error": str(e),
            "verified_at": datetime.utcnow().isoformat()
        }


@data_router.post("/api/dhan/credentials/update")
async def update_dhan_credentials(req: DhanCredentialUpdateRequest):
    """
    Saves & AES-256-GCM encrypts updated DhanHQ Client ID & 24/7 Access Token in Firestore Vault.
    """
    try:
        from src.user_credentials import get_credentials_manager
        mgr = get_credentials_manager()
        save_res = await mgr.save_user_credentials(
            user_id=req.user_id or "raghu_primary",
            client_id=req.client_id,
            access_token=req.access_token.strip()
        )
        return {
            "status": "success",
            "message": "DhanHQ credentials encrypted & stored successfully in single-tenant vault",
            "data": save_res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update credentials: {e}")


# ==============================================================================
# 6. Live Market Quotes (/api/dhan/market/quotes)
# ==============================================================================
@data_router.get("/api/dhan/market/quotes")
@data_router.get("/api/dhan/quotes/live")
async def get_market_quotes(
    security_ids: Optional[str] = Query(None, description="Comma-separated security IDs"),
    exchange_segment: Optional[str] = Query(None, description="Exchange segment (Defaults to IDX_I if not passed)"),
    user_id: Optional[str] = Query(None, description="User ID or Client ID (Defaults to primary vault)")
):
    """Live LTP, Open, High, Low, Close, Volume, VWAP, Change % directly from DhanHQ marketfeed"""
    norm_seg = normalize_exchange_segment(exchange_segment or "IDX_I")
    if not security_ids:
        # Provide institutional defaults based on exchange segment
        if norm_seg == "IDX_I":
            security_ids = "13,25,51,21"  # NIFTY, BANKNIFTY, SENSEX, INDIA VIX
        else:
            security_ids = "1333,11536,2885"  # HDFCBANK, TCS, RELIANCE
    sec_ids = parse_security_ids(security_ids, fallback_param=exchange_segment)
    
    try:
        client, client_id, resolved_id = await get_dhan_client_for_user(user_id)
        securities = {norm_seg: sec_ids}
        ohlc_response = client.ohlc_data(securities=securities)
        
        # Safe parsing: Dhan SDK may return a string on auth/network failure
        if isinstance(ohlc_response, str):
            logger.error(f"Dhan ohlc_data returned string instead of dict: {ohlc_response[:200]}")
            return {
                "status": "error",
                "message": f"Dhan API returned unexpected format. Token may need renewal.",
                "raw_response": ohlc_response[:200],
                "exchange_segment": norm_seg,
                "security_ids": sec_ids,
                "timestamp": datetime.utcnow().isoformat()
            }

        # Check for Dhan API failure response
        if isinstance(ohlc_response, dict) and ohlc_response.get("status") == "failed":
            error_data = ohlc_response.get("data", {})
            return {
                "status": "auth_required" if "808" in str(error_data) else "error",
                "message": "DhanHQ Live Marketfeed Auth Error (DH-901). Token renewal required.",
                "dhan_response": ohlc_response,
                "exchange_segment": norm_seg,
                "security_ids": sec_ids,
                "timestamp": datetime.utcnow().isoformat()
            }

        return {
            "status": "live",
            "data": ohlc_response,
            "exchange_segment": norm_seg,
            "security_ids": sec_ids,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error querying live Dhan quotes: {e}")
        raise HTTPException(status_code=502, detail=f"Dhan Marketfeed Gateway error: {e}")


# ==============================================================================
# 6B. Real-Time LTP Gateway (/api/dhan/market/ltp & /api/dhan/ltp)
# ==============================================================================
@data_router.get("/api/dhan/market/ltp")
@data_router.get("/api/dhan/ltp")
@data_router.get("/api/market/ltp")
async def get_market_ltp(
    security_id: Optional[str] = Query("13", description="Security ID (13 for NIFTY, 25 for BANKNIFTY)"),
    security_ids: Optional[str] = Query(None, description="Alternative alias for security_id"),
    exchange_segment: Optional[str] = Query("IDX_I", description="Exchange segment (IDX_I, NSE_FNO, NSE_EQ)"),
    segment: Optional[str] = Query(None, description="Alternative alias for exchange_segment"),
    user_id: Optional[str] = Query(None, description="User ID or Client ID (Defaults to primary vault)")
):
    """
    Real-Time Last Traded Price (LTP) Gateway for Engine B and Frontend.
    Extracts live LTP, OHLC, and price change directly from DhanHQ marketfeed.
    """
    raw_sec = security_ids or security_id or "13"
    sec_ids = parse_security_ids(raw_sec, fallback_param=exchange_segment)
    norm_seg = normalize_exchange_segment(segment or exchange_segment or "IDX_I")
    primary_id = sec_ids[0] if sec_ids else 13

    try:
        client, client_id, resolved_id = await get_dhan_client_for_user(user_id)
        securities = {norm_seg: sec_ids}
        ohlc_resp = client.ohlc_data(securities=securities)

        # Safe parsing: Dhan SDK may return a string on auth/network failure
        if isinstance(ohlc_resp, str):
            logger.error(f"Dhan ohlc_data (LTP) returned string instead of dict: {ohlc_resp[:200]}")
            return {
                "status": "error",
                "security_id": primary_id,
                "exchange_segment": norm_seg,
                "message": f"Dhan API returned unexpected format. Token may need renewal.",
                "raw_response": ohlc_resp[:200],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        ohlc_dict = ohlc_resp.get("data", {}) if isinstance(ohlc_resp, dict) and "data" in ohlc_resp else (ohlc_resp if isinstance(ohlc_resp, dict) else {})
        
        # DhanHQ v2 API wraps payloads inside {"status": "success", "data": {"data": {<segment>: ...}}}
        # Safely unwrap redundant 'data' dictionary layers until the segment key is found
        while isinstance(ohlc_dict, dict) and "data" in ohlc_dict and norm_seg not in ohlc_dict and norm_seg.lower() not in ohlc_dict:
            ohlc_dict = ohlc_dict["data"]
        
        if isinstance(ohlc_resp, dict) and ohlc_resp.get("status") == "failed":
            return {
                "status": "auth_required",
                "security_id": primary_id,
                "exchange_segment": norm_seg,
                "message": "DhanHQ Live Marketfeed Auth Error (DH-901). Token renewal required.",
                "dhan_response": ohlc_resp,
                "timestamp": datetime.utcnow().isoformat()
            }

        seg_data = ohlc_dict.get(norm_seg, {}) or ohlc_dict.get(norm_seg.lower(), {})
        sec_obj = seg_data.get(str(primary_id)) or seg_data.get(primary_id) or {}

        ltp = float(sec_obj.get("last_price") or sec_obj.get("ltp") or sec_obj.get("ohlc", {}).get("close") or 0.0)
        open_p = float(sec_obj.get("ohlc", {}).get("open") or ltp)
        high_p = float(sec_obj.get("ohlc", {}).get("high") or ltp)
        low_p = float(sec_obj.get("ohlc", {}).get("low") or ltp)
        close_p = float(sec_obj.get("ohlc", {}).get("close") or ltp)

        change_pct = round(((ltp - open_p) / open_p) * 100.0, 2) if open_p > 0 else 0.0

        return {
            "status": "live",
            "security_id": primary_id,
            "exchange_segment": norm_seg,
            "data": {
                "ltp": round(ltp, 2),
                "open": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(close_p, 2),
                "change_pct": change_pct
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error querying Dhan LTP: {e}")
        raise HTTPException(status_code=502, detail=f"Dhan Marketfeed LTP Gateway error: {e}")


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
@data_router.post("/api/v1/options/sync-bigquery")
@data_router.get("/api/v1/options/sync-bigquery")
@data_router.post("/api/v1/options/stream/trigger")
@data_router.get("/api/v1/options/stream/trigger")
@data_router.post("/api/dhan/options/stream-surface")
@data_router.get("/api/dhan/options/stream-surface")
async def sync_options_to_bigquery(
    user_id: Optional[str] = Query("raghu_primary", description="User ID for vault credentials"),
    preflight: bool = Query(False, description="Enable preflight test mode with synthetic generation fallback")
):
    """Real-time pipeline to compute IV Smile, Greeks, and stream Option Chains into BigQuery market_data.options_ticks"""
    try:
        from .options_chain_ingestor import options_ingestor
        result = await options_ingestor.ingest_live_option_chains(user_id=user_id or "raghu_primary", allow_synthetic=preflight)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync options surface: {e}")

@data_router.get("/api/v1/options/preflight-test")
async def options_preflight_test(
    user_id: Optional[str] = Query("raghu_primary", description="User ID for vault credentials")
):
    """Pre-flight test verifying end-to-end options streaming into BigQuery market_data.options_ticks"""
    try:
        from .options_chain_ingestor import options_ingestor
        result = await options_ingestor.ingest_live_option_chains(user_id=user_id or "raghu_primary", allow_synthetic=True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Options preflight test failed: {e}")

@data_router.post("/api/v1/options/stream/start")
async def start_options_streaming(
    interval_seconds: int = Query(60, description="Streaming interval in seconds"),
    user_id: Optional[str] = Query("raghu_primary", description="User ID for credentials")
):
    """Start autonomous background streaming loop during market hours"""
    try:
        from .options_chain_ingestor import options_ingestor
        return options_ingestor.start_background_streaming(interval_seconds=interval_seconds, user_id=user_id or "raghu_primary")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@data_router.post("/api/v1/options/stream/stop")
async def stop_options_streaming():
    """Stop autonomous background streaming loop"""
    try:
        from .options_chain_ingestor import options_ingestor
        return options_ingestor.stop_background_streaming()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@data_router.get("/api/dhan/options/surface-summary/{symbol}")
@data_router.get("/api/v1/options/surface-summary/{symbol}")
async def get_volatility_surface_summary(symbol: str = "NIFTY"):
    """Fetches real-time IV Smile, ATM IV, 25-Delta Put Skew, Max Pain, and PCR for an index."""
    try:
        from google.cloud import firestore
        db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920"))
        doc = db.collection("options_volatility_surface").document(symbol.upper()).get()
        if doc.exists:
            return {"status": "success", "data": doc.to_dict()}
        raise HTTPException(status_code=404, detail=f"No volatility surface recorded yet for symbol {symbol.upper()}. Run /api/dhan/options/sync-bigquery to ingest.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ==============================================================================
# 8. Historical Chart Data (/api/dhan/market/historical)
# ==============================================================================
@data_router.get("/api/dhan/market/historical")
@data_router.get("/api/dhan/historical")
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
