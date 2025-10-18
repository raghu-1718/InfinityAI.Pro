import numpy as np
import pandas as pd
from .ta_utils import rsi as rsi_ta, ema as ema_ta, bbands as bbands_ta, macd as macd_ta

BASIC_FEATURES = [
    "price","volume","rsi","ema_20","ema_50",
    "bollinger_upper","bollinger_lower","macd",
    "price_change_1h","price_change_4h","volume_ratio"
]

def extract_snapshot_features(market_data: dict) -> np.ndarray:
    f = [
        float(market_data.get("price", market_data.get("last_price", 100))),
        float(market_data.get("volume", 10000)),
        float(market_data.get("rsi", 50)),
        float(market_data.get("ema_20", market_data.get("price", 100))),
        float(market_data.get("ema_50", market_data.get("price", 100))),
        float(market_data.get("bollinger_upper", 105)),
        float(market_data.get("bollinger_lower", 95)),
        float(market_data.get("macd", 0)),
        float(market_data.get("price_change_1h", 0)),
        float(market_data.get("price_change_4h", 0)),
        float(market_data.get("volume_ratio", 1.0)),
    ]
    return np.array(f, dtype=float).reshape(1, -1)

def enrich_ohlc_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["rsi"] = rsi_ta(df["Close"], length=14)
    df["ema_20"] = ema_ta(df["Close"], length=20)
    df["ema_50"] = ema_ta(df["Close"], length=50)
    upper, lower = bbands_ta(df["Close"], length=20, std=2)
    df["bollinger_upper"] = upper
    df["bollinger_lower"] = lower
    df["macd"] = macd_ta(df["Close"])  # approximates MACD_12_26_9 line
    df["price_change_1h"] = df["Close"].pct_change(12)
    df["price_change_4h"] = df["Close"].pct_change(48)
    df["volume_ratio"] = df["Volume"] / df["Volume"].rolling(20).mean()
    df = df.fillna(method="bfill").fillna(method="ffill")
    return df
