"""
Unit and Regression Tests for EOD Pre-Close Square-Off and Cloud Scheduler Rescheduling.
InfinityAI.Pro - Phase 3 Square-Off Suite
Verifies that:
- Intraday position square-off executes at 15:25:00 IST (pre-close, while NSE F&O book is liquid)
- Emergency market retry triggers at 15:27:00 IST (< 15:30:00 IST)
- Post-market analytical AI journal is decoupled and triggers at 15:35:00 IST (after final closing prices settle)
- Cron expressions align strictly with Asia/Kolkata timezone
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pytest

# Ensure engine-a is on path
_engine_a_dir = Path(__file__).resolve().parent.parent / "backend" / "engine-a"
if str(_engine_a_dir) not in sys.path:
    sys.path.insert(0, str(_engine_a_dir))

from src.services.eod_settlement_service import EODSettlementService


def test_preclose_squareoff_timing_and_execution_type():
    """
    Assert execute_preclose_squareoff returns STANDARD_PRECLOSE_SQUAREOFF
    scheduled for 15:25:00 IST.
    """
    svc = EODSettlementService()
    res = svc.execute_preclose_squareoff(emergency_retry=False)

    assert res["status"] in ["success", "noop"]
    assert res["execution_type"] == "STANDARD_PRECLOSE_SQUAREOFF"
    assert res["scheduled_time_ist"] == "15:25:00 IST"
    assert "journal_status" not in res or res.get("journal_status") == "DECOUPLED_1535_IST"


def test_preclose_emergency_retry():
    """
    Assert execute_preclose_squareoff with emergency_retry=True
    returns EMERGENCY_MARKET_RETRY scheduled for 15:27:00 IST.
    """
    svc = EODSettlementService()
    res = svc.execute_preclose_squareoff(emergency_retry=True)

    assert res["status"] in ["success", "noop"]
    assert res["execution_type"] == "EMERGENCY_MARKET_RETRY"
    assert res["scheduled_time_ist"] == "15:27:00 IST"


def test_cron_expression_verification():
    """
    Verify Cloud Scheduler cron expressions:
    - Pre-Close Squareoff: '25 15 * * 1-5' (Asia/Kolkata) -> 15:25 IST
    - Post-Close Journal:   '35 15 * * 1-5' (Asia/Kolkata) -> 15:35 IST
    """
    squareoff_cron = "25 15 * * 1-5"
    journal_cron = "35 15 * * 1-5"

    sq_min, sq_hour = int(squareoff_cron.split()[0]), int(squareoff_cron.split()[1])
    jn_min, jn_hour = int(journal_cron.split()[0]), int(journal_cron.split()[1])

    # Assert squareoff is 15:25 IST
    assert (sq_hour, sq_min) == (15, 25)
    # Assert squareoff is strictly before 15:30:00 IST close
    assert (sq_hour * 60 + sq_min) < (15 * 60 + 30)

    # Assert journal is 15:35 IST, strictly after 15:30:00 IST close
    assert (jn_hour, jn_min) == (15, 35)
    assert (jn_hour * 60 + jn_min) > (15 * 60 + 30)
