from ..core.utils import setup_logger
log = setup_logger("RiskOptimizer")

class RiskOptimizer:
    def optimize_risk(self, position):
        qty = int(position.get("netQty", 0) or 0)
        volatility = abs(float(position.get("unrealizedProfit", 0) or 0)) / 1000
        adjusted_qty = max(1, int(qty * (1 - volatility)))
        log.info(f"Optimized Qty: {adjusted_qty} based on volatility {volatility:.2f}")
        return adjusted_qty
