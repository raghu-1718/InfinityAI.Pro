from ..core.utils import setup_logger
from ..providers.dhan_rest import DhanREST
log = setup_logger("HedgeAgent")

class HedgeAgent:
    def __init__(self):
        self.api = DhanREST()

    def evaluate(self, order):
        hedge_type = "SELL" if order.get("transactionType") == "BUY" else "BUY"
        qty = int(order.get("quantity", 0) or 0)
        price = float(order.get("price", 0) or 0)
        hedge_order = {
            "dhanClientId": order.get("dhanClientId"),
            "transactionType": hedge_type,
            "exchangeSegment": order.get("exchangeSegment", "NSE_FNO"),
            "productType": "INTRADAY",
            "orderType": "LIMIT",
            "securityId": order.get("securityId"),
            "quantity": max(1, qty // 2),
            "price": price * 1.01 if price else 0,
            "validity": "DAY"
        }
        log.info(f"🛡️  Auto-Hedge Order Prepared: {hedge_order}")
        return hedge_order
