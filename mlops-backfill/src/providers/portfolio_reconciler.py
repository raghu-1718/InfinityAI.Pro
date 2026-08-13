from .dhan_rest import DhanREST
from ..core.utils import setup_logger

log = setup_logger("Reconciler")

class PortfolioReconciler:
    def __init__(self):
        self.api = DhanREST()
        self.last_state = {}

    def reconcile(self):
        positions = self.api.get_positions()
        holdings = self.api.get_holdings()
        trades = self.api.get_trades()

        pnl = 0.0
        for pos in positions or []:
            unrealized = float(pos.get("unrealizedProfit", 0) or 0)
            realized = float(pos.get("realizedProfit", 0) or 0)
            pnl += unrealized + realized

        self.last_state = {"pnl": pnl, "positions": positions, "holdings": holdings, "trades": trades}
        log.info(f"💹 Total PnL: ₹{pnl:.2f}")
        return self.last_state
