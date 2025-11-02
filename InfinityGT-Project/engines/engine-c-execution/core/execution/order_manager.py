from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, Optional

from .risk_manager import RiskManager
from .types import TradeOrder, OrderStatus, TransactionType
from .position_manager import PositionManager
from ..broker.adapter_factory import get_broker_adapter


class OrderManager:
    """
    Orchestrates order lifecycle:
    - risk checks via RiskManager
    - route to broker via adapter
    - update positions via PositionManager
    """

    def __init__(
        self,
        risk_manager: RiskManager,
        position_manager: PositionManager,
        kill_switch: bool = False,
    ) -> None:
        self.risk_manager = risk_manager
        self.position_manager = position_manager
        self.kill_switch = kill_switch

    async def place_order(
        self,
        broker: str,
        broker_context: Dict[str, Any],
        order: TradeOrder,
        account_state: Optional[Dict[str, Any]] = None,
        market_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if self.kill_switch:
            return {
                "ok": False,
                "status": "blocked",
                "reason": "kill_switch_enabled",
            }

        # 1) Risk check using current positions and daily pnl
        risk = self.risk_manager.assess(
            symbol=order.symbol,
            quantity=order.quantity,
            price=order.price,
            side=order.transaction_type,
            positions=self.position_manager.positions,
            daily_pnl=self.position_manager.get_daily_pnl(),
        )
        if not risk.passed:
            return {
                "ok": False,
                "status": "rejected",
                "risk": asdict(risk),
            }

        # 2) Route to broker via adapter's async place_order
        adapter = get_broker_adapter(broker, **broker_context)
        result: Dict[str, Any] = await adapter.place_order(
            symbol=order.symbol,
            quantity=order.quantity,
            price=order.price,
            order_type=order.order_type.value,
            transaction_type=order.transaction_type.value,
        )
        ok = bool(result.get("success"))

        # 3) Update order and positions on success
        if ok:
            order.status = OrderStatus.EXECUTED
            order.execution_price = result.get("price") or order.price
            order.executed_at = datetime.now()
            self.position_manager.update_after_execution(order)
        else:
            order.status = OrderStatus.REJECTED

        return {
            "ok": ok,
            "broker": broker,
            "order": asdict(order),
            "risk": asdict(risk),
            "broker_result": result,
        }
