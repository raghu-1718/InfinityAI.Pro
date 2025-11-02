import os
import sys
import asyncio
import types
import pytest


# Ensure the engine-c-execution package is importable
CURRENT_DIR = os.path.dirname(__file__)
ENGINE_C_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ENGINE_C_DIR not in sys.path:
    sys.path.insert(0, ENGINE_C_DIR)

from core.execution.position_manager import PositionManager
from core.execution.risk_manager import RiskManager
from core.execution.order_manager import OrderManager
from core.execution.types import (
    TradeOrder,
    OrderType,
    TransactionType,
    OrderStatus,
)


class _MockAdapterSuccess:
    async def place_order(self, *, symbol: str, quantity: int, price: float, order_type: str, transaction_type: str, **kwargs):
        return {"success": True, "price": price or 100.0}


@pytest.mark.asyncio
async def test_order_manager_happy_path(monkeypatch):
    # Arrange
    pm = PositionManager()
    rm = RiskManager(max_position_size_inr=1_000_000, max_daily_loss_inr=100_000)
    om = OrderManager(risk_manager=rm, position_manager=pm, kill_switch=False)

    # Monkeypatch broker adapter factory to return a mock adapter
    import core.execution.order_manager as omodule
    monkeypatch.setattr(omodule, "get_broker_adapter", lambda broker, **ctx: _MockAdapterSuccess())

    order = TradeOrder(
        order_id="TEST-1",
        symbol="RELIANCE",
        quantity=2,
        price=0.0,
        order_type=OrderType.MARKET,
        transaction_type=TransactionType.BUY,
        status=OrderStatus.PENDING,
        created_at=__import__("datetime").datetime.now(),
    )

    # Act
    result = await om.place_order(
        broker="dhan",
        broker_context={"client_id": "demo", "access_token": "token"},
        order=order,
    )

    # Assert
    assert result.get("ok") is True
    assert order.status == OrderStatus.EXECUTED
    snap = pm.snapshot()
    assert "RELIANCE" in snap
    assert snap["RELIANCE"].quantity == 2


class _MockAdapterRecorder:
    def __init__(self):
        self.called = False

    async def place_order(self, *args, **kwargs):
        self.called = True
        return {"success": True, "price": kwargs.get("price", 100.0)}


@pytest.mark.asyncio
async def test_order_manager_risk_rejection_avoids_broker(monkeypatch):
    # Arrange a very small position size limit to trigger rejection
    pm = PositionManager()
    rm = RiskManager(max_position_size_inr=1)  # any order with value > 1 INR is rejected
    om = OrderManager(risk_manager=rm, position_manager=pm, kill_switch=False)

    adapter = _MockAdapterRecorder()
    import core.execution.order_manager as omodule

    def _mock_get_adapter(broker, **ctx):
        adapter.called = True
        return adapter

    # We set the function but expect risk check to reject before this is used
    monkeypatch.setattr(omodule, "get_broker_adapter", _mock_get_adapter)

    order = TradeOrder(
        order_id="TEST-2",
        symbol="TCS",
        quantity=10,
        price=100.0,
        order_type=OrderType.MARKET,
        transaction_type=TransactionType.BUY,
        status=OrderStatus.PENDING,
        created_at=__import__("datetime").datetime.now(),
    )

    # Act
    result = await om.place_order(
        broker="dhan",
        broker_context={"client_id": "demo", "access_token": "token"},
        order=order,
    )

    # Assert
    assert result.get("ok") is False
    assert result.get("status") == "rejected"
    # Broker adapter must not be called on risk rejection
    assert adapter.called is False
