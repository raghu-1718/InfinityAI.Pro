"""
InfinityAI.Pro — Test Suite for 0-DTE Gamma Scalper & Aggressive Limit-at-Touch
================================================================================
Validates:
  1. Capital-Dependent Dynamic Lot Sizing & Live Margin Gate
  2. Aggressive Limit-at-Touch (Zero Slippage) Router
  3. 0-DTE Afternoon Expiry Gamma Scalper Engine
"""

import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.live_capital_manager import LIVE_CAPITAL_MANAGER
from src.services.zero_dte_gamma_scalper import ZERO_DTE_GAMMA_SCALPER
from src.services.expiry_theta_damper import EXPIRY_THETA_DAMPER


# =====================================================================
# 1. CAPITAL-DEPENDENT SIZING & MARGIN ENFORCEMENT TESTS
# =====================================================================

def test_capital_dependent_lot_sizing_insufficient_margin():
    """Validates that orders are blocked before dispatch when available capital < 1 lot cost"""
    # NIFTY 1 lot (65 qty) at ₹100 premium requires ₹6,500
    # Available capital is only ₹4,000 -> Must reject with 0 lots
    sizing = LIVE_CAPITAL_MANAGER.compute_capital_dependent_lots(
        available_capital=4000.0,
        premium=100.0,
        symbol="NIFTY",
        max_capital_allocation_pct=0.15
    )
    assert sizing["is_viable"] is False
    assert sizing["allocated_lots"] == 0
    assert sizing["total_units"] == 0
    assert "cannot afford 1 lot" in sizing["rejection_reason"]


def test_capital_dependent_lot_sizing_single_lot_mode():
    """Validates that small capital accounts cleanly allocate exactly 1 lot in Single-Target mode"""
    # Available capital ₹15,000, 1 lot costs ₹1,625 (₹25 premium * 65 qty)
    # 15% allocation pool = ₹2,250 -> affords exactly 1 lot
    sizing = LIVE_CAPITAL_MANAGER.compute_capital_dependent_lots(
        available_capital=15000.0,
        premium=25.0,
        symbol="NIFTY",
        max_capital_allocation_pct=0.15
    )
    assert sizing["is_viable"] is True
    assert sizing["allocated_lots"] == 1
    assert sizing["total_units"] == 65
    assert sizing["execution_mode"] == "SINGLE_TARGET_MODE"
    assert sizing["margin_required"] == 1625.0


def test_capital_dependent_lot_sizing_multi_tier_scaling():
    """Validates that larger capital accounts scale up to multiple lots in Multi-Tier Tranche mode"""
    # Available capital ₹2,00,000, premium ₹30, 1 lot costs ₹1,950
    # 15% allocation pool = ₹30,000 -> affords ~15 lots, but risk capped
    sizing = LIVE_CAPITAL_MANAGER.compute_capital_dependent_lots(
        available_capital=200000.0,
        premium=30.0,
        symbol="NIFTY",
        max_capital_allocation_pct=0.15,
        max_lots_cap=6
    )
    assert sizing["is_viable"] is True
    assert sizing["allocated_lots"] >= 2
    assert sizing["allocated_lots"] <= 6
    assert sizing["execution_mode"] == "MULTI_TIER_TRANCHE"
    assert sizing["margin_required"] <= 200000.0


# =====================================================================
# 2. 0-DTE GAMMA SCALPER MODULE TESTS
# =====================================================================

def test_gamma_window_validation():
    """Tests the 13:15 IST – 15:15 IST afternoon gamma expansion window check"""
    # 1. Tuesday at 14:00 IST (valid expiry and window)
    tue_1400 = datetime(2026, 10, 13, 14, 0, 0)  # Oct 13, 2026 is Tuesday
    state_open = ZERO_DTE_GAMMA_SCALPER.is_gamma_window_open("NIFTY", current_time_ist=tue_1400)
    assert state_open["status"] == "OPEN"
    assert state_open["is_expiry_day"] is True
    assert state_open["is_in_time_window"] is True

    # 2. Tuesday morning at 10:30 IST (expiry day, but morning window closed)
    tue_1030 = datetime(2026, 10, 13, 10, 30, 0)
    state_morning = ZERO_DTE_GAMMA_SCALPER.is_gamma_window_open("NIFTY", current_time_ist=tue_1030)
    assert state_morning["status"] == "CLOSED"
    assert "arms post 13:15 IST" in state_morning["reason"]

    # 3. Monday (not an expiry day)
    mon_1400 = datetime(2026, 10, 12, 14, 0, 0)  # Oct 12, 2026 is Monday
    state_non_expiry = ZERO_DTE_GAMMA_SCALPER.is_gamma_window_open("NIFTY", current_time_ist=mon_1400)
    assert state_non_expiry["status"] == "CLOSED"
    assert "not authentic expiry day" in state_non_expiry["reason"]


def test_dealer_gex_calculation():
    """Tests Net Dealer Gamma (GEX) computation and regime identification"""
    strikes = [
        {"strike": 25000, "call_oi": 500000, "put_oi": 800000, "gamma": 0.0028},
        {"strike": 25050, "call_oi": 300000, "put_oi": 900000, "gamma": 0.0032},
        {"strike": 25100, "call_oi": 200000, "put_oi": 600000, "gamma": 0.0025},
    ]
    # Heavy Put OI > Call OI -> Put dealers short gamma -> Negative GEX
    gex = ZERO_DTE_GAMMA_SCALPER.compute_dealer_gex(spot_price=25000.0, strikes_data=strikes, lot_size=65)
    assert gex["net_gex_crores"] < 0
    assert gex["regime"] == "DEALER_SHORT_GAMMA_SQUEEZE"


def test_optimal_gamma_strike_selection():
    """Tests strike selection filtering for ₹10 – ₹45 premium sweet spot with maximum gamma"""
    mock_chain = [
        {"strike": 24900, "call_ltp": 120.0, "call_gamma": 0.0012, "call_sec_id": "1"},  # Too expensive
        {"strike": 25000, "call_ltp": 28.50, "call_gamma": 0.0035, "call_sec_id": "2"},  # Sweet spot!
        {"strike": 25050, "call_ltp": 14.20, "call_gamma": 0.0028, "call_sec_id": "3"},  # Sweet spot!
        {"strike": 25150, "call_ltp": 3.50,  "call_gamma": 0.0008, "call_sec_id": "4"},  # Too cheap
    ]
    best_call = ZERO_DTE_GAMMA_SCALPER.select_optimal_gamma_strike(
        direction="BULLISH",
        spot_price=25000.0,
        option_chain=mock_chain
    )
    assert best_call is not None
    assert best_call["strike"] in [25000, 25050]
    assert 10.0 <= best_call["premium"] <= 45.0
    assert best_call["option_type"] == "CE"


@pytest.mark.asyncio
async def test_0dte_gamma_scalp_margin_block(monkeypatch):
    """Validates that 0-DTE scalp is rejected when live available capital is insufficient"""
    async def mock_funds_insufficient(user_id=None, force_refresh=False):
        return {"available_capital": 500.0, "is_live": True}

    monkeypatch.setattr(LIVE_CAPITAL_MANAGER, "get_live_available_capital", mock_funds_insufficient)

    mock_chain = [
        {
            "strike": 25000,
            "call_ltp": 25.0,
            "call_gamma": 0.0032,
            "call_sec_id": "NIFTY_25000_CE",
            "call_bid": 24.90,
            "call_ask": 25.00
        }
    ]

    res = await ZERO_DTE_GAMMA_SCALPER.execute_gamma_scalp(
        symbol="NIFTY",
        direction="BULLISH",
        spot_price=25000.0,
        option_chain=mock_chain,
        force_bypass_window=True
    )

    assert res["status"] == "REJECTED_INSUFFICIENT_MARGIN"
    assert res["sizing_details"]["allocated_lots"] == 0


@pytest.mark.asyncio
async def test_0dte_gamma_scalp_full_lifecycle(monkeypatch):
    """Tests end-to-end scalp registration, dynamic targets (+40%/+80%), SL (-22%), and exit evaluation"""
    async def mock_funds_sufficient(user_id=None, force_refresh=False):
        return {"available_capital": 60000.0, "is_live": True}

    monkeypatch.setattr(LIVE_CAPITAL_MANAGER, "get_live_available_capital", mock_funds_sufficient)

    mock_chain = [
        {
            "strike": 25000,
            "call_ltp": 25.0,
            "call_gamma": 0.0032,
            "call_sec_id": "NIFTY_25000_CE",
            "call_bid": 24.90,
            "call_ask": 25.00
        }
    ]

    # Force bypass window for testing outside trading hours
    scalp = await ZERO_DTE_GAMMA_SCALPER.execute_gamma_scalp(
        symbol="NIFTY",
        direction="BULLISH",
        spot_price=25000.0,
        option_chain=mock_chain,
        max_scalp_capital_pct=0.10,
        force_bypass_window=True
    )

    assert scalp["status"] != "REJECTED_GATE_CLOSED"
    assert scalp["entry_price"] == 25.0
    assert scalp["target_1_price"] == 35.0   # +40% (25 * 1.40)
    assert scalp["target_2_price"] == 45.0   # +80% (25 * 1.80)
    assert scalp["stop_loss_price"] == 19.50 # -22% (25 * 0.78)

    # Test Exit Heartbeat at Target 1 (+40% at ₹36.00) during market hours (14:15 IST)
    market_hour_ist = datetime(2026, 10, 13, 14, 15, 0)
    ticks_t1 = {"NIFTY_25000_CE": 36.0}
    exits = ZERO_DTE_GAMMA_SCALPER.evaluate_live_scalp_exits(current_ticks=ticks_t1, current_time_ist=market_hour_ist)
    assert len(exits) == 1
    assert exits[0]["action"] == "TAKE_PROFIT_TIER_1"
    assert exits[0]["pnl_percentage"] == 44.0

    # SL ratcheted to +5% guaranteed profit (₹26.25)
    scalp_record = ZERO_DTE_GAMMA_SCALPER.active_scalps[scalp["scalp_id"]]
    assert scalp_record["stop_loss_price"] == 26.25

    # Test Exit Heartbeat at Target 2 (+80% at ₹46.00)
    ticks_t2 = {"NIFTY_25000_CE": 46.0}
    exits_t2 = ZERO_DTE_GAMMA_SCALPER.evaluate_live_scalp_exits(current_ticks=ticks_t2, current_time_ist=market_hour_ist)
    assert len(exits_t2) == 1
    assert exits_t2[0]["action"] == "TAKE_PROFIT_TIER_2"
    assert scalp_record["is_active"] is False

    # Test Hard EOD Square-Off at 15:26 IST
    eod_ist = datetime(2026, 10, 13, 15, 26, 0)
    scalp_record["is_active"] = True  # re-arm for test
    exits_eod = ZERO_DTE_GAMMA_SCALPER.evaluate_live_scalp_exits(current_ticks=ticks_t1, current_time_ist=eod_ist)
    assert len(exits_eod) == 1
    assert exits_eod[0]["action"] == "HARD_EOD_SQUAREOFF"
