"""
Unit and Regression Tests for Expiry Calendar and Theta Damper Service.
InfinityAI.Pro - Phase 2 Regression Suite
Verifies SEBI / NSE Mandated Expiry Calendars:
- NIFTY: Weekly on Tuesday (shifts backward on exchange holidays)
- MIDCPNIFTY, BANKNIFTY, FINNIFTY: Monthly on the last Tuesday of the month
"""

import sys
from pathlib import Path
from datetime import date, datetime

# Ensure engine-a is on path
_engine_a_dir = Path(__file__).resolve().parent.parent / "backend" / "engine-a"
if str(_engine_a_dir) not in sys.path:
    sys.path.insert(0, str(_engine_a_dir))

from src.services.expiry_theta_damper import (
    EXPIRY_THETA_DAMPER,
    is_expiry_day,
    get_authentic_expiry_date,
    NSE_HOLIDAYS_2026,
)


def test_midcpnifty_october_19_2026_not_expiry():
    """
    Monday, October 19, 2026 was incorrectly treated as weekly MIDCPNIFTY expiry
    by outdated pre-Nov 2024 logic.
    Under SEBI / NSE circular, MIDCPNIFTY only expires monthly on the last Tuesday.
    Assert is_expiry_day("MIDCPNIFTY", date(2026, 10, 19)) returns False.
    """
    mon_oct_19 = date(2026, 10, 19)
    assert not is_expiry_day("MIDCPNIFTY", mon_oct_19)
    assert not EXPIRY_THETA_DAMPER.is_expiry_day("MIDCPNIFTY", mon_oct_19)


def test_midcpnifty_october_27_2026_is_true_expiry():
    """
    Tuesday, October 27, 2026 is the last Tuesday of October 2026.
    Assert is_expiry_day("MIDCPNIFTY", date(2026, 10, 27)) returns True.
    """
    tue_oct_27 = date(2026, 10, 27)
    assert is_expiry_day("MIDCPNIFTY", tue_oct_27)
    assert EXPIRY_THETA_DAMPER.is_expiry_day("MIDCPNIFTY", tue_oct_27)


def test_banknifty_and_finnifty_monthly_schedule():
    """
    BANKNIFTY and FINNIFTY also follow the monthly last-Tuesday schedule.
    Monday, Oct 19, 2026: NOT expiry.
    Tuesday, Oct 27, 2026: TRUE monthly expiry.
    """
    mon_oct_19 = date(2026, 10, 19)
    tue_oct_27 = date(2026, 10, 27)

    assert not is_expiry_day("BANKNIFTY", mon_oct_19)
    assert not is_expiry_day("FINNIFTY", mon_oct_19)

    assert is_expiry_day("BANKNIFTY", tue_oct_27)
    assert is_expiry_day("FINNIFTY", tue_oct_27)


def test_nifty_weekly_tuesday_and_holiday_shift():
    """
    NIFTY expires weekly on Tuesday.
    However, Tuesday Oct 20, 2026 is an NSE holiday (Dussehra).
    Per exchange rules, weekly expiry shifts to the preceding trading day (Monday, Oct 19, 2026).
    """
    assert "2026-10-20" in NSE_HOLIDAYS_2026

    mon_oct_19 = date(2026, 10, 19)
    tue_oct_20 = date(2026, 10, 20)
    tue_oct_27 = date(2026, 10, 27)

    # Monday Oct 19 is active NIFTY weekly expiry due to Tuesday holiday shift
    assert is_expiry_day("NIFTY", mon_oct_19)
    # Tuesday Oct 20 is a holiday, so market is closed
    assert not is_expiry_day("NIFTY", tue_oct_20)
    # Tuesday Oct 27 is standard weekly NIFTY expiry
    assert is_expiry_day("NIFTY", tue_oct_27)


def test_expiry_date_retrieval():
    """Verify get_authentic_expiry_date returns expected contract date."""
    target_date = date(2026, 10, 15)
    # For NIFTY on Oct 15, 2026, next Tuesday is Oct 20 (holiday) -> shifts to Oct 19
    nifty_exp = get_authentic_expiry_date("NIFTY", target_date)
    assert nifty_exp == date(2026, 10, 19)

    # For MIDCPNIFTY on Oct 15, 2026, monthly expiry is Oct 27, 2026
    midcp_exp = get_authentic_expiry_date("MIDCPNIFTY", target_date)
    assert midcp_exp == date(2026, 10, 27)
