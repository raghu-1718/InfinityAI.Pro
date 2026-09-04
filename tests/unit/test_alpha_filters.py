"""
Unit Tests for Engine A Alpha Filters (MTF Confluence + Restricted OI Acceleration)
InfinityAI.Pro - Production Verification Suite
"""
import pytest
import sys
from pathlib import Path

# Add engine-a src to sys.path
engine_a_path = Path(__file__).resolve().parent.parent.parent / "backend" / "engine-a"
if str(engine_a_path) not in sys.path:
    sys.path.insert(0, str(engine_a_path))

from src.services.mtf_confluence_filter import MTFConfluenceFilter, MTF_CONFLUENCE_FILTER
from src.services.options_oi_acceleration_tracker import RestrictedOIAccelerationTracker, OI_ACCELERATION_TRACKER


def test_mtf_confluence_filter_approved():
    """Verify that MTF Confluence Filter approves strong aligned trends with score >= 0.65."""
    filter_engine = MTFConfluenceFilter(min_confluence_threshold=0.65)
    snapshot = {
        "rsi": 62.0,
        "vwap": 24500.0,
        "macd": 15.0
    }
    res = filter_engine.evaluate_confluence(
        symbol="NIFTY",
        signal_type="BUY_CALL",
        current_price=24550.0,
        indicators_snapshot=snapshot
    )
    assert res["is_approved"] is True
    assert res["confluence_score"] >= 0.65
    assert res["action_status"] in ["APPROVED_HIGH_CONFLUENCE", "APPROVED_STANDARD"]


def test_mtf_confluence_filter_blocked_counter_trend():
    """Verify that MTF Confluence Filter blocks counter-trend chop when score < 0.65."""
    filter_engine = MTFConfluenceFilter(min_confluence_threshold=0.65)
    # Bearish indicator snapshot opposing a BUY_CALL
    snapshot = {
        "rsi": 38.0,
        "vwap": 24650.0,
        "macd": -25.0
    }
    res = filter_engine.evaluate_confluence(
        symbol="NIFTY",
        signal_type="BUY_CALL",
        current_price=24550.0,
        indicators_snapshot=snapshot
    )
    assert res["is_approved"] is False
    assert res["confluence_score"] < 0.65
    assert res["action_status"] == "BLOCKED_CHOP_FILTER"


def test_oi_acceleration_tracker_overhead_call_wall():
    """Verify that OI Acceleration Tracker detects overhead Call wall inside ATM +- 3 strikes."""
    tracker = RestrictedOIAccelerationTracker(max_strike_buffer=3, oi_threshold_pct=20.0)
    # NIFTY spot = 24510 -> ATM strike = 24500
    # Immediate overhead strike 24550 with +45% Call OI delta
    strikes_oi = [
        {"strike": 24400, "call_oi": 10000, "put_oi": 15000, "delta_oi_pct": 5.0, "option_type": "CE"},
        {"strike": 24500, "call_oi": 20000, "put_oi": 20000, "delta_oi_pct": 10.0, "option_type": "CE"},
        {"strike": 24550, "call_oi": 50000, "put_oi": 8000, "delta_oi_pct": 45.0, "option_type": "CE"},
        {"strike": 25500, "call_oi": 80000, "put_oi": 5000, "delta_oi_pct": 95.0, "option_type": "CE"}, # Far OTM noise - must be ignored!
    ]
    res = tracker.evaluate_oi_velocity("NIFTY", 24510.0, strikes_oi)
    assert res["call_wall_detected"] is True
    assert res["conviction_multiplier"] == 0.80
    assert any(w["strike"] == 24550 for w in res["active_walls"])
    # Ensure far OTM strike 25500 was ignored (strict ATM +- 3 SFATM filtering)
    assert not any(w["strike"] == 25500 for w in res["active_walls"])


def test_oi_acceleration_tracker_underlying_put_support():
    """Verify that OI Acceleration Tracker detects underlying Put support and boosts conviction."""
    tracker = RestrictedOIAccelerationTracker(max_strike_buffer=3, oi_threshold_pct=20.0)
    # NIFTY spot = 24510 -> ATM strike = 24500
    # Strike 24450 with +35% Put OI delta
    strikes_oi = [
        {"strike": 24450, "call_oi": 5000, "put_oi": 40000, "delta_oi_pct": 35.0, "option_type": "PE"},
        {"strike": 24500, "call_oi": 20000, "put_oi": 20000, "delta_oi_pct": 5.0, "option_type": "PE"},
    ]
    res = tracker.evaluate_oi_velocity("NIFTY", 24510.0, strikes_oi)
    assert res["put_wall_detected"] is True
    assert res["conviction_multiplier"] == 1.15
    assert any(w["strike"] == 24450 for w in res["active_walls"])


def test_autonomous_trader_strike_resolution_method_exists():
    """Verify AutonomousTrader has resolve_optimal_option_strike as a valid member method."""
    from src.services.autonomous_trader import AutonomousTrader
    assert hasattr(AutonomousTrader, "resolve_optimal_option_strike")
    assert callable(getattr(AutonomousTrader, "resolve_optimal_option_strike"))
