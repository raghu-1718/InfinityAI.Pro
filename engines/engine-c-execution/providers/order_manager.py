from .dhan_rest import DhanREST
from ..analytics.ai_signal_model import AISignalModel
from ..analytics.hedge_agent import HedgeAgent
from ..core.utils import setup_logger

log = setup_logger("OrderManager")

class OrderManager:
    def __init__(self):
        self.api = DhanREST()
        self.ai = AISignalModel()
        self.hedge_agent = HedgeAgent()

    def place_order(self, order_payload):
        signal_strength = self.ai.validate_signal(order_payload)
        if signal_strength < 0.6:
            log.warning("Order rejected — AI signal weak.")
            return {"status": "rejected", "reason": "weak_signal"}
        order_resp = self.api.place_order(order_payload)
        log.info(f"✅ Order placed: {order_resp}")
        self.hedge_agent.evaluate(order_payload)
        return order_resp
