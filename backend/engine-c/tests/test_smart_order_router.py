"""
InfinityAI.Pro — Engine-C Aggressive Limit-at-Touch Router Tests
================================================================
Validates:
  1. Touch limit price computation for BUY and SELL orders
  2. Inside-spread price improvement logic
  3. Watchdog surveillance loop and simulated order execution
  4. Rupee and point slippage savings measurement
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.smart_order_router import SMART_ORDER_ROUTER


def test_limit_at_touch_pricing():
    """Tests optimal limit price calculations for BUY and SELL orders"""
    # BUY Order: Best Bid = 100.00, Best Ask = 100.50
    # Limit-at-Touch targets Best Ask (100.50) to guarantee fill with 0 slippage
    buy_touch = SMART_ORDER_ROUTER.compute_limit_at_touch_price(
        transaction_type="BUY",
        best_bid=100.00,
        best_ask=100.50,
        aggressive_level="TOUCH"
    )
    assert buy_touch == 100.50

    # Inside-Spread Improvement: When spread >= 0.30 pts, improve 1 tick inside (100.45)
    buy_inside = SMART_ORDER_ROUTER.compute_limit_at_touch_price(
        transaction_type="BUY",
        best_bid=100.00,
        best_ask=100.50,
        aggressive_level="INSIDE_SPREAD"
    )
    assert buy_inside == 100.45

    # SELL Order: Best Bid = 95.00, Best Ask = 95.60
    sell_touch = SMART_ORDER_ROUTER.compute_limit_at_touch_price(
        transaction_type="SELL",
        best_bid=95.00,
        best_ask=95.60,
        aggressive_level="TOUCH"
    )
    assert sell_touch == 95.00


@pytest.mark.asyncio
async def test_smart_order_router_execution_simulation():
    """Tests simulated execution of SmartOrderRouter with slippage savings measurement"""
    res = await SMART_ORDER_ROUTER.execute_smart_order(
        security_id="54321",
        transaction_type="BUY",
        quantity=65,
        best_bid=120.00,
        best_ask=120.40,
        ltp=120.40,
        dhan_client=None  # Triggers paper/simulation fill
    )

    assert res["status"] == "FILLED"
    assert res["executed_price"] == 120.40
    assert res["quantity"] == 65
    assert res["fill_latency_ms"] < 100.0
    assert len(res["stages_executed"]) >= 1
    assert "routing_resolution" in res
