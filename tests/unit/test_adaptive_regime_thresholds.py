"""
Unit Tests: Time-of-Day Adaptive Regime Thresholds (Domain 1)
=============================================================
Validates:
1. State-aware market regime parsing across Indian Standard Time (Asia/Kolkata).
2. Regime 1 (09:15 - 10:30 IST): ADX=18.0, ML=0.65, Theta Damper=False.
3. Regime 2 (11:30 - 13:30 IST): ADX=24.0, ML=0.65, Theta Damper=True.
4. Regime 3 (13:45 - 15:15 IST): ADX=19.0, ML=0.65, Theta Damper=False.
5. Default Regime (Off-market / Transitions): ADX=20.0, ML=0.70, Theta Damper=False.
6. AutonomousTrader dynamic gating against regime thresholds.
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from unittest.mock import MagicMock, AsyncMock, patch

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENGINE_A_DIR = str(BASE_DIR / "backend" / "engine-a")
if ENGINE_A_DIR not in sys.path:
    sys.path.insert(0, ENGINE_A_DIR)

import src
engine_a_src = os.path.join(ENGINE_A_DIR, "src")
if hasattr(src, "__path__") and engine_a_src not in src.__path__:
    src.__path__.append(engine_a_src)

from src.services.market_regime_thresholds import (
    get_current_market_regime,
    MarketRegimeConfig,
    IST_TIMEZONE
)


def test_regime_1_morning_opening_expansion():
    """Verify 09:45 IST maps to Regime 1 (ADX 18.0, ML 0.65, Damper False)"""
    dt_ist = datetime(2026, 9, 7, 9, 45, 0, tzinfo=IST_TIMEZONE)
    regime = get_current_market_regime(dt_ist)

    assert regime.regime_id == "REGIME_1"
    assert "Morning" in regime.name
    assert regime.adx_threshold == 18.0
    assert regime.ml_threshold == 0.65
    assert regime.theta_decay_damper is False


def test_regime_2_midday_lunch_chop_trap():
    """Verify 12:15 IST maps to Regime 2 (ADX 24.0, ML 0.65, Damper True)"""
    dt_ist = datetime(2026, 9, 7, 12, 15, 0, tzinfo=IST_TIMEZONE)
    regime = get_current_market_regime(dt_ist)

    assert regime.regime_id == "REGIME_2"
    assert "Chop" in regime.name
    assert regime.adx_threshold == 24.0
    assert regime.ml_threshold == 0.65
    assert regime.theta_decay_damper is True


def test_regime_3_afternoon_institutional_sweep():
    """Verify 14:30 IST maps to Regime 3 (ADX 19.0, ML 0.65, Damper False)"""
    dt_ist = datetime(2026, 9, 7, 14, 30, 0, tzinfo=IST_TIMEZONE)
    regime = get_current_market_regime(dt_ist)

    assert regime.regime_id == "REGIME_3"
    assert "Afternoon" in regime.name
    assert regime.adx_threshold == 19.0
    assert regime.ml_threshold == 0.65
    assert regime.theta_decay_damper is False


def test_regime_default_transition_and_offmarket():
    """Verify 10:45 IST (transition) and 18:00 IST (post-market) map to Default Regime (ADX 20.0, ML 0.70)"""
    dt_transition = datetime(2026, 9, 7, 10, 45, 0, tzinfo=IST_TIMEZONE)
    r_trans = get_current_market_regime(dt_transition)
    assert r_trans.regime_id == "REGIME_DEFAULT"
    assert r_trans.adx_threshold == 20.0
    assert r_trans.ml_threshold == 0.70
    assert r_trans.theta_decay_damper is False

    dt_evening = datetime(2026, 9, 7, 18, 0, 0, tzinfo=IST_TIMEZONE)
    r_eve = get_current_market_regime(dt_evening)
    assert r_eve.regime_id == "REGIME_DEFAULT"
    assert r_eve.adx_threshold == 20.0
    assert r_eve.ml_threshold == 0.70


def test_utc_to_ist_conversion_integrity():
    """Verify UTC input correctly translates to IST hour"""
    # 04:15 UTC == 09:45 IST -> Regime 1
    dt_utc = datetime(2026, 9, 7, 4, 15, 0, tzinfo=timezone.utc)
    regime = get_current_market_regime(dt_utc)
    assert regime.regime_id == "REGIME_1"
    assert regime.adx_threshold == 18.0


@pytest.mark.asyncio
async def test_autonomous_trader_regime_gating():
    """Verify AutonomousTrader rejects signal when ADX < dynamic threshold or ML < threshold"""
    mock_risk = MagicMock()
    with patch("src.services.autonomous_trader.CircuitBreaker"), \
         patch("src.services.autonomous_trader.AuditLogger"):
        from src.services.autonomous_trader import AutonomousTrader
        trader = AutonomousTrader(risk_manager=mock_risk)

    trader.audit_logger = MagicMock()

    # 12:15 IST (Regime 2 requires ADX >= 24.0)
    tick_time = datetime(2026, 9, 7, 12, 15, 0, tzinfo=IST_TIMEZONE).isoformat()

    # Signal with ADX 20.0 (passes Regime 1 but FAILS Regime 2 ADX 24.0)
    low_adx_signal = {
        "symbol": "NIFTY",
        "signal": "BUY",
        "confidence": 0.68,
        "adx": 20.0,
        "current_price": 24200.0,
        "timestamp": tick_time,
    }

    with patch.object(trader, "validate_signal_freshness", return_value=True), \
         patch.object(trader, "_execute_trade", new_callable=AsyncMock) as mock_exec:

        await trader._process_signal(low_adx_signal)
        mock_exec.assert_not_called()
        trader.audit_logger.log_trade_rejected.assert_called_once()
        assert trader.audit_logger.log_trade_rejected.call_args[0][2] == "LOW_ADX_MOMENTUM_REGIME"

    trader.audit_logger.reset_mock()

    # Signal with Confidence 0.62 (FAILS Regime 2 ML 0.65)
    low_ml_signal = {
        "symbol": "NIFTY",
        "signal": "BUY",
        "confidence": 0.62,
        "adx": 26.0,
        "current_price": 24200.0,
        "timestamp": tick_time,
    }

    with patch.object(trader, "validate_signal_freshness", return_value=True), \
         patch.object(trader, "_execute_trade", new_callable=AsyncMock) as mock_exec:

        await trader._process_signal(low_ml_signal)
        mock_exec.assert_not_called()
        trader.audit_logger.log_trade_rejected.assert_called_once()
        assert trader.audit_logger.log_trade_rejected.call_args[0][2] == "LOW_ML_CONFIDENCE_REGIME"
