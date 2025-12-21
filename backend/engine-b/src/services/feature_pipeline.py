import numpy as np
import pandas as pd
from typing import Dict
from .ta_utils import rsi as rsi_ta, ema as ema_ta, bbands as bbands_ta, macd as macd_ta

BASIC_FEATURES = [
    "price", "volume", "rsi", "ema_20", "ema_50",
    "bollinger_upper", "bollinger_lower", "macd",
    "price_change_1h", "price_change_4h", "volume_ratio"
]

_DEFAULTS = {
    "price": 100.0,
    "volume": 10_000.0,
    "rsi": 50.0,
    "ema_20": 100.0,
    "ema_50": 100.0,
    "bollinger_upper": 105.0,
    "bollinger_lower": 95.0,
    "macd": 0.0,
    "price_change_1h": 0.0,
    "price_change_4h": 0.0,
    "volume_ratio": 1.0,
}


def _safe_float(v, default: float) -> float:
    try:
        f = float(v)
        if not np.isfinite(f):
            return default
        return f
    except Exception:
        return default


def extract_snapshot_features(market_data: Dict) -> np.ndarray:
    """
    Convert Engine-A snapshot into fixed-shape ML feature vector.
    Shape: (1, len(BASIC_FEATURES))
    """
    features = []

    for key in BASIC_FEATURES:
        if key == "price":
            val = market_data.get("price", market_data.get("last_price"))
        else:
            val = market_data.get(key)

        features.append(_safe_float(val, _DEFAULTS[key]))

    X = np.array(features, dtype=np.float64)

    # Final guard (never let NaN through)
    if not np.all(np.isfinite(X)):
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    return X.reshape(1, -1)


def enrich_ohlc_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add TA indicators to OHLCV dataframe.
    Defensive against missing columns & NaNs.
    """
    if df is None or df.empty:
        return df

    df = df.copy()

    # Normalize column names
    df.columns = [c.lower() for c in df.columns]

    if not {"close", "volume"}.issubset(df.columns):
        return df

    close = df["close"]
    volume = df["volume"]

    df["rsi"] = rsi_ta(close, length=14)
    df["ema_20"] = ema_ta(close, length=20)
    df["ema_50"] = ema_ta(close, length=50)

    upper, lower = bbands_ta(close, length=20, std=2)
    df["bollinger_upper"] = upper
    df["bollinger_lower"] = lower

    df["macd"] = macd_ta(close)

    df["price_change_1h"] = close.pct_change(12)
    df["price_change_4h"] = close.pct_change(48)

    vol_ma = volume.rolling(20).mean()
    df["volume_ratio"] = volume / vol_ma.replace(0, np.nan)

    df = df.ffill().bfill()

    return df
