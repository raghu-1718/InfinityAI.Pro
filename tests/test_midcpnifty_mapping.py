"""
Unit and Regression Tests for MIDCPNIFTY SecurityId, Spot Price Sanity Bounds, and Strike Increments.
InfinityAI.Pro - Phase 1 Regression Suite
"""

import sys
from pathlib import Path
import pytest

# Ensure engine-a is on path
_engine_a_dir = Path(__file__).resolve().parent.parent / "backend" / "engine-a"
if str(_engine_a_dir) not in sys.path:
    sys.path.insert(0, str(_engine_a_dir))

from src.services.market_data_validator import (
    validate_index_spot,
    validate_or_raise,
    StaleMarketDataError,
    INDEX_SPOT_BOUNDS,
    INDEX_INSTRUMENT_SPEC,
    calculate_atm_strike,
    get_strike_step,
    get_dhan_security_id,
)


def test_midcpnifty_instrument_specs():
    """Verify MIDCPNIFTY Dhan Security ID, lot size, and strike step."""
    spec = INDEX_INSTRUMENT_SPEC["MIDCPNIFTY"]
    assert spec["security_id"] == "442"
    assert spec["lot_size"] == 120
    assert spec["strike_step"] == 25
    assert get_dhan_security_id("MIDCPNIFTY") == "442"
    assert get_strike_step("MIDCPNIFTY") == 25


def test_midcpnifty_corrupted_spot_rejection():
    """
    Assert that corrupted spot price 44,324.25 (swapped from BANKNIFTY) is strictly rejected.
    MIDCPNIFTY sanity bounds are 8,000 to 22,000.
    """
    corrupted_spot = 44324.25
    assert not validate_index_spot("MIDCPNIFTY", corrupted_spot)
    assert not validate_index_spot("MIDCPNIFTY", 43975.50)

    # Must raise ValueError when using validate_or_raise
    with pytest.raises(ValueError) as excinfo:
        validate_or_raise("MIDCPNIFTY", corrupted_spot)
    assert "OUT OF SANITY BOUNDS" in str(excinfo.value)


def test_midcpnifty_valid_spot_acceptance():
    """Assert valid NSE spot prices around 13,500 - 13,750 pass validation."""
    valid_spot_1 = 13708.50
    valid_spot_2 = 13565.15
    assert validate_index_spot("MIDCPNIFTY", valid_spot_1)
    assert validate_index_spot("MIDCPNIFTY", valid_spot_2)
    assert validate_or_raise("MIDCPNIFTY", valid_spot_1) == valid_spot_1


def test_midcpnifty_atm_strike_calculation():
    """
    Assert MIDCPNIFTY ATM strike calculation selects valid 25-point increment strikes.
    For spot 13,565.15, closest 25-pt strike is 13,575.
    For spot 13,708.50, closest 25-pt strike is 13,700.
    """
    strike_1 = calculate_atm_strike("MIDCPNIFTY", 13565.15)
    assert strike_1 == 13575
    assert strike_1 % 25 == 0

    strike_2 = calculate_atm_strike("MIDCPNIFTY", 13708.50)
    assert strike_2 == 13700
    assert strike_2 % 25 == 0

    strike_3 = calculate_atm_strike("MIDCPNIFTY", 13612.40)
    assert strike_3 == 13600
    assert strike_3 % 25 == 0


def test_stale_market_data_error():
    """Assert StaleMarketDataError is raised when tick data age exceeds threshold."""
    with pytest.raises(StaleMarketDataError) as excinfo:
        validate_index_spot("MIDCPNIFTY", 13600.0, age_seconds=45.0, max_age_seconds=30.0)
    assert "STALE MARKET DATA" in str(excinfo.value)


def test_other_index_spot_bounds():
    """Verify NIFTY, BANKNIFTY, and FINNIFTY sanity bounds and strike steps."""
    assert validate_index_spot("NIFTY", 25800.0)
    assert not validate_index_spot("NIFTY", 12000.0)
    assert calculate_atm_strike("NIFTY", 25824.0) == 25800
    assert get_strike_step("NIFTY") == 50

    assert validate_index_spot("BANKNIFTY", 51200.0)
    assert not validate_index_spot("BANKNIFTY", 13708.50)  # MIDCPNIFTY spot fed to BANKNIFTY
    assert calculate_atm_strike("BANKNIFTY", 51249.0) == 51200
    assert calculate_atm_strike("BANKNIFTY", 51260.0) == 51300
    assert get_strike_step("BANKNIFTY") == 100

    assert validate_index_spot("FINNIFTY", 24300.0)
    assert calculate_atm_strike("FINNIFTY", 24320.0) == 24300
    assert get_strike_step("FINNIFTY") == 50
