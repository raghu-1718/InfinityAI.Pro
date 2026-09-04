"""
Timeframe Regimes Simulation Tool (Task 4)
==========================================
Simulates internal system ticks across all three institutional market regimes:
  1. 09:45 IST -> Morning Opening Expansion (ADX Threshold = 18.0, ML Threshold = 0.65, Theta Damper = False)
  2. 12:15 IST -> Mid-Day Lunch Chop Trap    (ADX Threshold = 24.0, ML Threshold = 0.65, Theta Damper = True)
  3. 14:30 IST -> Afternoon Institutional Sweep (ADX Threshold = 19.0, ML Threshold = 0.65, Theta Damper = False)
  4. 10:45 IST -> Transition / Default Regime (ADX Threshold = 20.0, ML Threshold = 0.70, Theta Damper = False)

Verifies dynamic gate adaptation and live logging buffer output.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure engine-a src in path
sys.path.insert(0, os.path.abspath("backend/engine-a"))

from src.services.market_regime_thresholds import (
    get_current_market_regime,
    IST_TIMEZONE
)
from src.services.autonomous_trader import AutonomousTrader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RegimeSimulation")


async def run_timeframe_regimes_simulation():
    logger.info("================================================================================")
    logger.info("   TIME-OF-DAY ADAPTIVE REGIME GATE SIMULATION (ENGINE A AUTONOMOUS TRADER)     ")
    logger.info("================================================================================")

    mock_risk = MagicMock()
    mock_risk.calculate_margin_aware_lot_size.return_value = {
        "is_viable": True,
        "optimal_lots": 2,
        "total_units": 130,
        "total_margin_required": 18500.0,
        "lot_size": 65,
        "max_risk_amount": 1500.0
    }
    mock_risk.score_risk.return_value = {"recommendation": "PROCEED", "risk_level": "LOW"}
    mock_risk.validate_net_profitability.return_value = {"is_viable": True, "net_roi": 0.18, "total_fees": 84.50}

    with patch("src.services.autonomous_trader.CircuitBreaker"), \
         patch("src.services.autonomous_trader.AuditLogger"):
        trader = AutonomousTrader(risk_manager=mock_risk)

    trader.audit_logger = MagicMock()

    simulation_scenarios = [
        {
            "scenario": "Scenario 1: Morning Opening Expansion",
            "ist_time": "09:45:00",
            "dt": datetime(2026, 9, 7, 9, 45, 0, tzinfo=IST_TIMEZONE),
            "adx": 18.5,       # >= 18.0 -> Passes Regime 1
            "confidence": 0.67, # >= 0.65 -> Passes Regime 1
            "expected_regime": "REGIME_1",
            "expected_adx_thresh": 18.0,
            "expected_damper": False,
            "expected_outcome": "APPROVED"
        },
        {
            "scenario": "Scenario 2: Mid-Day Lunch Chop Trap (Low ADX Veto)",
            "ist_time": "12:15:00",
            "dt": datetime(2026, 9, 7, 12, 15, 0, tzinfo=IST_TIMEZONE),
            "adx": 20.5,       # < 24.0 -> VETOED in Regime 2!
            "confidence": 0.68,
            "expected_regime": "REGIME_2",
            "expected_adx_thresh": 24.0,
            "expected_damper": True,
            "expected_outcome": "VETOED_BY_ADX"
        },
        {
            "scenario": "Scenario 3: Mid-Day Lunch Chop Trap (High ADX + Theta Damper)",
            "ist_time": "12:45:00",
            "dt": datetime(2026, 9, 7, 12, 45, 0, tzinfo=IST_TIMEZONE),
            "adx": 25.5,       # >= 24.0 -> Passes Regime 2 ADX
            "confidence": 0.68, # >= 0.65 -> Passes ML
            "expected_regime": "REGIME_2",
            "expected_adx_thresh": 24.0,
            "expected_damper": True,
            "expected_outcome": "APPROVED_WITH_THETA_DAMPER"
        },
        {
            "scenario": "Scenario 4: Afternoon Institutional Sweep",
            "ist_time": "14:30:00",
            "dt": datetime(2026, 9, 7, 14, 30, 0, tzinfo=IST_TIMEZONE),
            "adx": 19.2,       # >= 19.0 -> Passes Regime 3
            "confidence": 0.66, # >= 0.65 -> Passes Regime 3
            "expected_regime": "REGIME_3",
            "expected_adx_thresh": 19.0,
            "expected_damper": False,
            "expected_outcome": "APPROVED"
        },
        {
            "scenario": "Scenario 5: Off-Market / Transition Hours",
            "ist_time": "10:45:00",
            "dt": datetime(2026, 9, 7, 10, 45, 0, tzinfo=IST_TIMEZONE),
            "adx": 19.5,       # < 20.0 -> Fails Default Regime ADX
            "confidence": 0.68, # < 0.70 -> Fails Default Regime ML
            "expected_regime": "REGIME_DEFAULT",
            "expected_adx_thresh": 20.0,
            "expected_damper": False,
            "expected_outcome": "VETOED_BY_DEFAULT_REGIME"
        }
    ]

    audit_summary = []

    for item in simulation_scenarios:
        logger.info(f"\n--------------------------------------------------------------------------------")
        logger.info(f"▶️ Testing: {item['scenario']} ({item['ist_time']} IST)")
        
        signal = {
            "symbol": "NIFTY",
            "signal": "BUY",
            "confidence": item["confidence"],
            "adx": item["adx"],
            "current_price": 24250.0,
            "timestamp": item["dt"].isoformat(),
            "strikes_oi": []
        }

        # Check regime calculation directly
        reg = get_current_market_regime(item["dt"])
        assert reg.regime_id == item["expected_regime"]
        assert reg.adx_threshold == item["expected_adx_thresh"]
        assert reg.theta_decay_damper == item["expected_damper"]

        trader.audit_logger.reset_mock()

        with patch.object(trader, "validate_signal_freshness", return_value=True), \
             patch.object(trader, "_execute_trade", new_callable=AsyncMock) as mock_exec, \
             patch("src.services.autonomous_trader.MTF_CONFLUENCE_FILTER") as mock_mtf, \
             patch("src.services.autonomous_trader.OI_ACCELERATION_TRACKER") as mock_oi:

            mock_mtf.evaluate_confluence.return_value = {"is_approved": True, "confluence_score": 0.85}
            mock_oi.evaluate_oi_velocity.return_value = {
                "conviction_multiplier": 1.0,
                "call_wall_detected": False,
                "put_wall_detected": False
            }

            await trader._process_signal(signal)

            executed = mock_exec.called
            rejections = trader.audit_logger.log_trade_rejected.call_args_list
            reject_reason = rejections[0][0][2] if rejections else "NONE"

            if executed:
                actual_outcome = "APPROVED_WITH_THETA_DAMPER" if reg.theta_decay_damper else "APPROVED"
            else:
                actual_outcome = f"VETOED ({reject_reason})"

            logger.info(f"   • Regime Identified: [{reg.name}] (ID: {reg.regime_id})")
            logger.info(f"   • Dynamic ADX Threshold: {reg.adx_threshold:.1f} (Incoming: {item['adx']:.1f})")
            logger.info(f"   • Dynamic ML Threshold:  {reg.ml_threshold:.2f} (Incoming: {item['confidence']:.2f})")
            logger.info(f"   • Theta Decay Damper:    {reg.theta_decay_damper}")
            logger.info(f"   • Final Gate Action:     {actual_outcome}")

            audit_summary.append({
                "time_ist": item["ist_time"],
                "regime": reg.name,
                "adx_in": item["adx"],
                "adx_req": reg.adx_threshold,
                "ml_in": item["confidence"],
                "ml_req": reg.ml_threshold,
                "damper": reg.theta_decay_damper,
                "result": actual_outcome
            })

    logger.info("\n================================================================================")
    logger.info("   TIMEFRAME REGIMES AUDIT MATRIX                                               ")
    logger.info("================================================================================")
    print(f"{'Time (IST)':<12} | {'Regime Name':<32} | {'ADX In/Req':<12} | {'ML In/Req':<12} | {'Damper':<8} | {'Outcome'}")
    print("-" * 105)
    for r in audit_summary:
        adx_str = f"{r['adx_in']:.1f}/{r['adx_req']:.1f}"
        ml_str = f"{r['ml_in']:.2f}/{r['ml_req']:.2f}"
        print(f"{r['time_ist']:<12} | {r['regime']:<32} | {adx_str:<12} | {ml_str:<12} | {str(r['damper']):<8} | {r['result']}")
    print("-" * 105)

    return audit_summary

if __name__ == "__main__":
    asyncio.run(run_timeframe_regimes_simulation())
