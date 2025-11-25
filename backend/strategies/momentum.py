#!/usr/bin/env python3
"""
Momentum Trading Strategy (copied into Iaminfinity workspace)
"""

import numpy as np
from typing import Dict, Any, List
from datetime import datetime

STRATEGY_INFO = {
    "name": "Momentum Strategy",
    "type": "Trend Following",
    "timeframe": "Intraday/Swing",
    "risk_level": "Medium",
    "indicators": ["RSI", "MACD", "ADX", "Volume"],
    "description": "Trades in direction of strong momentum with RSI and MACD confirmation"
}

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    if len(prices) < slow:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
    prices_array = np.array(prices)
    ema_fast = _ema(prices_array, fast)
    ema_slow = _ema(prices_array, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(np.array([macd_line] * signal), signal)
    histogram = macd_line - signal_line
    return {"macd": float(macd_line), "signal": float(signal_line), "histogram": float(histogram)}

def _ema(data: np.ndarray, period: int) -> float:
    if len(data) == 0:
        return 0.0
    multiplier = 2 / (period + 1)
    ema = data[0]
    for price in data[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    return ema

def calculate_adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    if len(highs) < period + 1:
        return 25.0
    tr_list = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        tr_list.append(tr)
    if not tr_list:
        return 25.0
    atr = np.mean(tr_list[-period:])
    dm_plus = sum([max(highs[i] - highs[i-1], 0) for i in range(1, len(highs))])
    dm_minus = sum([max(lows[i-1] - lows[i], 0) for i in range(1, len(lows))])
    if atr == 0:
        return 25.0
    di_plus = (dm_plus / len(tr_list)) / atr * 100
    di_minus = (dm_minus / len(tr_list)) / atr * 100
    if (di_plus + di_minus) == 0:
        return 25.0
    dx = abs(di_plus - di_minus) / (di_plus + di_minus) * 100
    return min(dx, 100.0)

def run(data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    symbol = data.get("symbol", "UNKNOWN")
    close = data.get("close", 0.0)
    prices = data.get("prices", [close])
    highs = data.get("highs", prices)
    lows = data.get("lows", prices)
    volume = data.get("volume", 0)
    if len(prices) < 26:
        return {"signal": "HOLD", "confidence": 0.0, "reason": "Insufficient data", "symbol": symbol, "timestamp": datetime.now().isoformat()}
    rsi = calculate_rsi(prices)
    macd = calculate_macd(prices)
    adx = calculate_adx(highs, lows, prices)
    sma_20 = np.mean(prices[-20:])
    sma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else sma_20
    signal = "HOLD"
    confidence = 0.0
    if rsi > 50 and rsi < 70 and macd["histogram"] > 0 and close > sma_20 and adx > 25:
        signal = "BUY"
        confidence = min((rsi - 50) / 20 + 0.5, 1.0)
    elif rsi < 50 and rsi > 30 and macd["histogram"] < 0 and close < sma_20 and adx > 25:
        signal = "SELL"
        confidence = min((50 - rsi) / 20 + 0.5, 1.0)
    atr = np.std(prices[-14:]) * 1.5
    stop_loss = close - atr if signal == "BUY" else close + atr
    target = close + (atr * 2) if signal == "BUY" else close - (atr * 2)
    result = {"signal": signal, "confidence": round(confidence, 2), "symbol": symbol, "entry_price": round(close, 2), "stop_loss": round(stop_loss, 2), "target": round(target, 2), "indicators": {"rsi": round(rsi,2), "macd_histogram": round(macd["histogram"],2), "adx": round(adx,2)}, "timestamp": datetime.now().isoformat(), "strategy": "momentum"}
    return result

def validate(data: Dict[str, Any]) -> Dict[str, bool]:
    return {"has_symbol": "symbol" in data, "has_close": "close" in data, "has_prices": "prices" in data and len(data.get("prices", [])) >= 26, "valid": all(["symbol" in data, "close" in data, "prices" in data, len(data.get("prices", [])) >= 26])}