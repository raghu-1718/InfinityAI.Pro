import numpy as np
import pandas as pd

class TechnicalAnalytics:
    def __init__(self):
        self.symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFCBANK"]

    async def get_signals(self):
        signals = []
        for sym in self.symbols:
            prices = np.random.normal(1000, 10, 50).tolist()  # Replace with real price fetch
            ind = self.calculate_indicators(prices)
            sig = self.generate_signal(sym, prices[-1], ind)
            signals.append(sig)
        return signals

    def calculate_indicators(self, prices):
        df = pd.DataFrame({"close": prices})
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        ema_20 = df["close"].ewm(span=20).mean()
        ema_50 = df["close"].ewm(span=50).mean()
        rolling_mean = df["close"].rolling(window=20).mean()
        rolling_std = df["close"].rolling(window=20).std()
        bollinger_upper = rolling_mean + (rolling_std * 2)
        bollinger_lower = rolling_mean - (rolling_std * 2)
        ema_12 = df["close"].ewm(span=12).mean()
        ema_26 = df["close"].ewm(span=26).mean()
        macd = ema_12 - ema_26
        return {
            "rsi": float(rsi.iloc[-1]),
            "ema_20": float(ema_20.iloc[-1]),
            "ema_50": float(ema_50.iloc[-1]),
            "bollinger_upper": float(bollinger_upper.iloc[-1]),
            "bollinger_lower": float(bollinger_lower.iloc[-1]),
            "macd": float(macd.iloc[-1])
        }

    def generate_signal(self, symbol, price, indicators):
        buys, sells = 0, 0
        if indicators["rsi"] < 30: buys += 1
        if indicators["rsi"] > 70: sells += 1
        if indicators["ema_20"] > indicators["ema_50"]: buys += 1
        if indicators["ema_20"] < indicators["ema_50"]: sells += 1
        signal = "BUY" if buys > sells else "SELL" if sells > buys else "HOLD"
        conf = 60 + 10 * abs(buys - sells)
        return {
            "symbol": symbol,
            "price": price,
            "signal_type": signal,
            "confidence": conf,
            "indicators": indicators
        }
