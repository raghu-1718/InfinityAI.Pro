class BreakoutStrategy:
    def evaluate(self, data):
        price = data.get("price", 0)
        resistance = data.get("resistance", 0)
        support = data.get("support", 0)

        if price > resistance:
            return {"action": "BUY", "symbol": data.get("symbol"), "reason": "Break above resistance"}
        elif price < support:
            return {"action": "SELL", "symbol": data.get("symbol"), "reason": "Break below support"}
        else:
            return {"action": "HOLD", "symbol": data.get("symbol"), "reason": "Within support and resistance"}
