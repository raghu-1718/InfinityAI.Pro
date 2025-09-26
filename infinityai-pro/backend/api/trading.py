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

@router.get("/dhan/callback")
async def dhan_callback(code: str):
    import requests
    from utils.config import CONFIG
    response = requests.post("https://api.dhan.co/v2/token", data={
        "client_id": CONFIG.BROKER["client_id"],
        "client_secret": CONFIG.BROKER["client_secret"],
        "code": code,
        "grant_type": "authorization_code"
    })
    token_data = response.json()
    access_token = token_data.get("access_token")
    # Update config or save to file/env
    CONFIG.BROKER["access_token"] = access_token
    return {"message": "Access token updated", "access_token": access_token}
