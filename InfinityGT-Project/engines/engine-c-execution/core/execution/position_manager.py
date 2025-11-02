from __future__ import annotations

from typing import Dict
from datetime import datetime
from .types import Position, TradeOrder, TransactionType


class PositionManager:
    """
    Tracks positions and daily PnL in-memory.
    In production, persist to a DB. For Cloud Run ephemeral instances,
    aggregate via external store if needed.
    """

    def __init__(self) -> None:
        self.positions: Dict[str, Position] = {}
        self.daily_pnl: float = 0.0

    def snapshot(self) -> Dict[str, Position]:
        return dict(self.positions)

    def get_daily_pnl(self) -> float:
        return float(self.daily_pnl)

    def update_after_execution(self, order: TradeOrder) -> None:
        symbol = order.symbol
        exec_price = float(order.execution_price or order.price or 0.0)

        if symbol in self.positions:
            pos = self.positions[symbol]
            if order.transaction_type == TransactionType.BUY:
                total_cost = (pos.quantity * pos.average_price) + (order.quantity * exec_price)
                total_qty = pos.quantity + order.quantity
                pos.average_price = total_cost / max(total_qty, 1)
                pos.quantity = total_qty
                pos.current_price = exec_price
            else:  # SELL reduces position
                # Realized PnL for quantity closed
                qty_closed = min(pos.quantity, order.quantity)
                self.daily_pnl += (exec_price - pos.average_price) * qty_closed
                pos.quantity -= order.quantity
                pos.current_price = exec_price
                if pos.quantity <= 0:
                    # Close position when zero; residual quantity set to 0
                    del self.positions[symbol]
                    return
        else:
            if order.transaction_type == TransactionType.BUY:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=int(order.quantity),
                    average_price=exec_price,
                    current_price=exec_price,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                    entry_time=order.executed_at or datetime.now(),
                )
            # For SELL without existing pos, treat as short if your broker supports.
