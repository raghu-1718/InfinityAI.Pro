from datetime import datetime
from backtest.config import SLIPPAGE_PCT, BROKERAGE_PER_TRADE

class SimulatedExecutionEngine:
    def execute(self, side, price, qty):
        slip = price * SLIPPAGE_PCT
        fill_price = price + slip if side == "BUY" else price - slip

        return {
            "side": side,
            "price": fill_price,
            "qty": qty,
            "brokerage": BROKERAGE_PER_TRADE,
            "timestamp": datetime.utcnow()
        }
