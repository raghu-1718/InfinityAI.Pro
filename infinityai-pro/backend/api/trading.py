from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def get_trading_status():
    return {"status": "Trading API active"}

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
