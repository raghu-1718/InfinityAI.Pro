import numpy as np
import pandas as pd


def ema(series: pd.Series, length: int = 20) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    gain_ewm = pd.Series(gain, index=series.index).ewm(alpha=1/length, adjust=False).mean()
    loss_ewm = pd.Series(loss, index=series.index).ewm(alpha=1/length, adjust=False).mean()
    rs = gain_ewm / (loss_ewm + 1e-12)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def bbands(series: pd.Series, length: int = 20, std: float = 2.0) -> tuple[pd.Series, pd.Series]:
    ma = series.rolling(window=length, min_periods=1).mean()
    sd = series.rolling(window=length, min_periods=1).std(ddof=0)
    upper = ma + std * sd
    lower = ma - std * sd
    return upper, lower


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    # Return MACD line similar to pandas_ta default key "MACD_12_26_9"
    return macd_line
