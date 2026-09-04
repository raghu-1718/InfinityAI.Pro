"""
Feature Engineering for Financial Market AI Models
Generates momentum, volatility, and order flow features with strict zero lookahead bias.
"""
import numpy as np
import pandas as pd


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(window=period, min_periods=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period, min_periods=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def build_ml_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate technical, momentum, and volatility features.
    Guarantees no lookahead bias by shifting target forward while keeping features backward-looking.
    """
    data = df.copy()
    if "close" not in data.columns or "volume" not in data.columns:
        raise ValueError("Dataframe must contain 'close' and 'volume' columns.")

    # 1. Momentum Returns
    data["ret_1"] = data["close"].pct_change(1)
    data["ret_3"] = data["close"].pct_change(3)
    data["ret_5"] = data["close"].pct_change(5)

    # 2. RSI Indicator
    data["rsi_14"] = compute_rsi(data["close"], period=14)

    # 3. MACD
    ema12 = data["close"].ewm(span=12, adjust=False).mean()
    ema26 = data["close"].ewm(span=26, adjust=False).mean()
    data["macd"] = ema12 - ema26
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
    data["macd_hist"] = data["macd"] - data["macd_signal"]

    # 4. Volatility
    data["volatility_20"] = data["ret_1"].rolling(20).std() * np.sqrt(252)

    # 5. Volume Flow
    vol_sma20 = data["volume"].rolling(20).mean()
    data["volume_ratio"] = data["volume"] / vol_sma20.replace(0, 1)

    # 6. Put-Call Ratio (PCR) heuristic proxy
    data["pcr_proxy"] = 1.0 + (data["rsi_14"] - 50.0) / 100.0

    # 7. Target Variable: Forward 1-step Price Direction (Binary Classification)
    # Strictly shifted: feature values at row t predict return from t to t+1
    data["forward_return"] = data["close"].shift(-1) / data["close"] - 1.0
    data["target"] = (data["forward_return"] > 0).astype(int)

    # Drop rows with NaN from rolling calculations or target shift
    clean_data = data.dropna().copy()
    return clean_data
