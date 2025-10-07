from fastapi import APIRouter, Request, HTTPException
from services.kill_switch import is_enabled, set_enabled, get_consecutive_failures, reset_failures

router = APIRouter(prefix="/api/trading", tags=["Trading"])

@router.get("/status")
def get_trading_status():
    return {
        "status": "Trading API active",
        "kill_switch_enabled": is_enabled(),
        "consecutive_failures": get_consecutive_failures()
    }


@router.post("/enable")
async def enable_trading():
    set_enabled(True)
    return {"ok": True, "message": "Trading enabled"}


@router.post("/disable")
async def disable_trading():
    set_enabled(False)
    return {"ok": True, "message": "Trading disabled"}

@router.post("/signal")
async def get_signal(symbol: str):
    from services.ai_models import generate_signals, compute_features
    from data.instruments import MarketDataFetcher
    import pandas as pd
    import datetime
    import numpy as np

    fetcher = MarketDataFetcher()
    if symbol in ["NIFTY", "BANKNIFTY", "SENSEX", "GIFTNIFTY"]:
        df = await fetcher.fetch_nse_index(symbol)
    else:
        df = await fetcher.fetch_mc_commodities(symbol)
    df = compute_features(df)
    signal = generate_signals(df)
    return {"symbol": symbol, "signal": signal}

@router.post("/order")
async def place_order(symbol: str, qty: int, order_type: str):
    from services.broker_dhan import BrokerAPI
    broker = BrokerAPI(api_key="YOUR_API_KEY", access_token="YOUR_ACCESS_TOKEN")
    result = await broker.place_order(symbol, qty, order_type)
    return result

@router.get("/dhan/health")
async def dhan_health():
    """Basic Dhan readiness: returns fund limits (profile) if token is set."""
    from utils.config import CONFIG
    from services.broker_dhan import DhanAdapter
    try:
        if not CONFIG.BROKER.get("access_token") or not CONFIG.BROKER.get("client_id"):
            return {"ok": False, "error": "Missing Dhan credentials"}
        adapter = DhanAdapter(CONFIG.BROKER.get("client_id"), CONFIG.BROKER.get("access_token"), CONFIG.BROKER.get("data_api_key"), CONFIG.BROKER.get("data_api_secret"))
        prof = adapter.get_fund_limits()
        return {"ok": True, "fund_limits": prof}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.get("/dhan/quote/{symbol}")
async def dhan_quote(symbol: str):
    from services.broker_dhan import DhanAdapter
    from utils.config import CONFIG
    try:
        adapter = DhanAdapter(CONFIG.BROKER.get("client_id"), CONFIG.BROKER.get("access_token"), CONFIG.BROKER.get("data_api_key"), CONFIG.BROKER.get("data_api_secret"))
        q = await adapter.get_quote_async(symbol)
        return {"ok": q is not None, "quote": q}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.post("/paper/start-once")
async def paper_start_once():
    """Run one cycle of PaperBot to verify end-to-end trading loop without real orders."""
    from services.paper_bot import PaperBot
    from utils.config import CONFIG
    try:
        bot = PaperBot(CONFIG)
        ok = await bot.run_once()
        return {"ok": bool(ok), "equity": bot.equity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dhan/token")
async def dhan_token_update(request: dict):
    """Handle Dhan token refresh webhook"""
    from utils.config import CONFIG
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Dhan sends the new access token in the request body
        new_token = request.get("access_token")
        if not new_token:
            return {"error": "No access_token provided"}

        # Update the config with new token
        CONFIG.BROKER["access_token"] = new_token

        logger.info("Dhan access token updated via webhook")
        return {"message": "Token updated successfully"}

    except Exception as e:
        logger.error(f"Failed to update Dhan token: {e}")
        return {"error": str(e)}


@router.get("/dhan/callback")
async def dhan_oauth_callback(code: str | None = None, state: str | None = None, access_token: str | None = None):
    """OAuth redirect handler for Dhan
    - Dhan may redirect with a temporary code that must be exchanged for an access token
    - Some flows may provide access_token directly
    This endpoint captures those parameters and (for now) stores access_token if present.
    """
    from utils.config import CONFIG
    import logging

    logger = logging.getLogger(__name__)

    try:
        if access_token:
            # Direct token delivered in query (if Dhan returns it this way)
            CONFIG.BROKER["access_token"] = access_token
            logger.info("Dhan access token updated via OAuth callback")
            return {"message": "Access token received and stored", "state": state}

        if code:
            # If a code is provided, exchange step should occur here.
            # For security, we do not auto-exchange without client secret. Implement in BrokerAPI.
            logger.info(f"Dhan OAuth code received: {code}")
            return {
                "message": "Authorization code received. Exchange this code server-side for an access token.",
                "code": code,
                "state": state
            }

        raise HTTPException(status_code=400, detail="Missing 'code' or 'access_token' in callback")

    except Exception as e:
        logger.error(f"Dhan OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dhan/webhook")
async def dhan_event_webhook(payload: dict, request: Request | None = None):
    """Generic Dhan postback webhook for order/trade events.
    Configure this URL in Dhan dashboard for updates (order status, trade executions, etc.).
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        event_type = payload.get("event") or payload.get("type")
        logger.info(f"Dhan webhook event received: {event_type} | payload: {payload}")
        # TODO: route events to internal handlers (orders, positions, etc.)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Dhan webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
