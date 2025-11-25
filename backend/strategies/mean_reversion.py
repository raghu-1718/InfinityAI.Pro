#!/usr/bin/env python3
"""
Mean Reversion Trading Strategy (copied into Iaminfinity workspace)
"""

import numpy as np
from typing import Dict, Any, List
from datetime import datetime

STRATEGY_INFO = {
    "name": "Mean Reversion Strategy",
    "type": "Counter-Trend",
    "timeframe": "Intraday",
    "risk_level": "Medium-High",
    "indicators": ["Bollinger Bands", "RSI", "Stochastic"],
    "description": "Trades reversals from extreme overbought/oversold levels"
}

def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
    if len(prices) < period:
        avg = np.mean(prices)
        return {"upper": avg, "middle": avg, "lower": avg, "bandwidth": 0.0}
    recent_prices = prices[-period:]
    middle = np.mean(recent_prices)
    std = np.std(recent_prices)
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    bandwidth = ((upper - lower) / middle) * 100
    return {"upper": float(upper), "middle": float(middle), "lower": float(lower), "bandwidth": float(bandwidth)}

def calculate_stochastic(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Dict[str, float]:
    if len(closes) < period:
        return {"k": 50.0, "d": 50.0}
    recent_highs = highs[-period:]
    recent_lows = lows[-period:]
    current_close = closes[-1]
    highest_high = max(recent_highs)
    lowest_low = min(recent_lows)
    if highest_high == lowest_low:
        k = 50.0
    else:
        k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
    d = k
    return {"k": float(k), "d": float(d)}

def calculate_z_score(prices: List[float], period: int = 20) -> float:
    if len(prices) < period:
        return 0.0
    recent_prices = prices[-period:]
    mean = np.mean(recent_prices)
    std = np.std(recent_prices)
    if std == 0:
        return 0.0
    current_price = prices[-1]
    z_score = (current_price - mean) / std
    return float(z_score)

def run(data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    symbol = data.get("symbol", "UNKNOWN")
    close = data.get("close", 0.0)
    prices = data.get("prices", [close])
    highs = data.get("highs", prices)
    lows = data.get("lows", prices)
    volume = data.get("volume", 0)
    if len(prices) < 20:
        return {"signal": "HOLD", "confidence": 0.0, "reason": "Insufficient data", "symbol": symbol, "timestamp": datetime.now().isoformat()}
    bb = calculate_bollinger_bands(prices)
    stoch = calculate_stochastic(highs, lows, prices)
    z_score = calculate_z_score(prices)
    rsi = _calculate_rsi(prices)
    signal = "HOLD"
    confidence = 0.0
    reasons = []
    bb_position = ((close - bb["lower"]) / (bb["upper"] - bb["lower"])) * 100 if bb["upper"] != bb["lower"] else 50
    if (close < bb["lower"]) or (rsi < 30 and stoch["k"] < 20) or (z_score < -2):
        signal = "BUY"
        confidence = min(abs(z_score) / 3, 1.0)
        reasons.append("Oversold conditions detected")
    elif (close > bb["upper"]) or (rsi > 70 and stoch["k"] > 80) or (z_score > 2):
        signal = "SELL"
        confidence = min(abs(z_score) / 3, 1.0)
        reasons.append("Overbought conditions detected")
    entry = close
    target = bb["middle"]
    stop_loss = bb["lower"] - (bb["upper"] - bb["lower"]) * 0.25 if signal == "BUY" else bb["upper"] + (bb["upper"] - bb["lower"]) * 0.25 if signal == "SELL" else close
    risk = abs(entry - stop_loss)
    reward = abs(target - entry)
    risk_reward = (reward / risk) if risk > 0 else 0
    result = {
        "signal": signal,
        "confidence": round(confidence, 2),
        "symbol": symbol,
        "entry_price": round(entry, 2),
        "stop_loss": round(stop_loss, 2),
        "target": round(target, 2),
        "risk_reward": round(risk_reward, 2),
        "indicators": {"bb_upper": round(bb["upper"], 2), "bb_middle": round(bb["middle"], 2), "bb_lower": round(bb["lower"], 2), "z_score": round(z_score, 2)},
        "reasons": reasons,
        "timestamp": datetime.now().isoformat(),
        "strategy": "mean_reversion"
    }
    return result

def _calculate_rsi(prices: List[float], period: int = 14) -> float:
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

def validate(data: Dict[str, Any]) -> Dict[str, bool]:
    return {"has_symbol": "symbol" in data, "has_close": "close" in data, "has_prices": "prices" in data and len(data.get("prices", [])) >= 20, "valid": all(["symbol" in data, "close" in data, "prices" in data, len(data.get("prices", [])) >= 20])}