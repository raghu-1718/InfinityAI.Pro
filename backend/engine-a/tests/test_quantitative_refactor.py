"""
InfinityAI.Pro — Quantitative Strategy & Risk Architecture Refactor Test Suite
=============================================================================
Post-Audit of Revision engine-a-00196-2jg (October 09, 2026)
Simulates and validates:
  1. Multi-Model Consensus & Discordance Gate:
     - XGBoost at 33% (with LightGBM at 73%) triggers REGIME_CHOP_CONSOLIDATION and routes to PULLBACK_LIMIT_ONLY.
     - Min model probability >= 0.45 permits standard market execution.
  2. Pullback Entry Confirmation Engine:
     - Holds signals in observation queue (VWAP distance <= 5 pts, fast RSI < 45).
     - 180s timeout invalidates candidate with status PULLBACK_TIMEOUT_DISCARD.
     - Confirmed pullback records pullback_wait_duration_ms.
  3. Spot-Anchored Structural Stops:
     - Spot remains above structural support while option premium temporarily draws down -10% or -15%:
       Position strictly remains OPEN (Noise immunity).
     - Spot breaking structural support triggers STRUCTURAL_SPOT_SUPPORT_BREACH.
     - Catastrophic -25% premium collapse triggers EMERGENCY_PREMIUM_STOP_HIT.
  4. Asymmetric Multi-Tier Profit Trailing Engine:
     - Even lot sizing enforced (min 2 lots).
     - +6.0% premium spike dynamically ratchets SL to entry_premium + 1.00 in active_positions.
     - +12% to +15% gain books 50% partial profit and records tier1_hit_timestamp.
     - Tier 2 runner trails spot trend structure without static cap until trend reversal.
"""

import pytest
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.services.ml_consensus_gate import MultiModelConsensusGate
from src.services.pullback_execution_manager import PullbackExecutionManager
from src.services.structural_risk_manager import StructuralRiskManager
from src.services.asymmetric_trade_lifecycle import AsymmetricTradeLifecycle
from src.services.shadow_signal_logger import ShadowSignalLogger


class TestQuantitativeStrategyRefactor:
    """Test suite validating the 4 core quantitative refactor modules"""

    # =========================================================================
    # Test 1: Multi-Model Consensus & Discordance Gate (XGBoost at 33%)
    # =========================================================================
    def test_xgboost_discordance_triggers_regime_chop_consolidation(self):
        """
        Verify that severe model divergence (XGBoost at 33%, LightGBM at 73%)
        triggers REGIME_CHOP_CONSOLIDATION and routes to PULLBACK_LIMIT_ONLY.
        """
        cb_prob = 0.65
        lgb_prob = 0.73
        xgb_prob = 0.33  # Severe divergence < 0.40

        eval_res = MultiModelConsensusGate.evaluate_consensus(
            catboost_prob=cb_prob,
            lightgbm_prob=lgb_prob,
            xgboost_prob=xgb_prob,
            decision="BUY_CALL"
        )

        assert eval_res["is_discordant"] is True, "Must flag model discordance"
        assert eval_res["consensus_passed"] is False, "Consensus must not pass"
        assert eval_res["market_state"] == "REGIME_CHOP_CONSOLIDATION"
        assert eval_res["execution_route"] == "PULLBACK_LIMIT_ONLY"
        assert eval_res["ml_consensus_min"] == 0.33
        assert "DISCORDANCE_DETECTED" in eval_res["reason"]

    def test_high_consensus_permits_standard_market_execution(self):
        """
        Verify that when all models agree (min >= 0.45), standard market execution is permitted.
        """
        cb_prob = 0.62
        lgb_prob = 0.68
        xgb_prob = 0.58

        eval_res = MultiModelConsensusGate.evaluate_consensus(
            catboost_prob=cb_prob,
            lightgbm_prob=lgb_prob,
            xgboost_prob=xgb_prob,
            decision="BUY_CALL"
        )

        assert eval_res["is_discordant"] is False
        assert eval_res["consensus_passed"] is True
        assert eval_res["market_state"] == "REGIME_TRENDING_CONSENSUS"
        assert eval_res["execution_route"] == "STANDARD_MARKET_ALLOWED"
        assert eval_res["ml_consensus_min"] == 0.58

    # =========================================================================
    # Test 2: Pullback Entry Confirmation Engine
    # =========================================================================
    def test_pullback_observation_and_vwap_touch_confirmation(self):
        """
        Verify pullback engine confirms entry when spot is within 5.0 pts of VWAP.
        """
        pem = PullbackExecutionManager()
        symbol = "NIFTY"
        raw_signal = {"symbol": symbol, "decision": "BUY_CALL", "spot_price": 22450.0}

        # Register candidate
        pem.register_candidate_signal(symbol, raw_signal)
        assert symbol in pem.pending_queue

        # Tick 1: Spot is far from VWAP (diff = 15 pts), RSI is high (65.0) -> Not confirmed
        res_tick1 = pem.check_pending_signal(
            symbol=symbol,
            current_spot=22460.0,
            live_vwap=22445.0,
            rsi_1m_period_5=65.0
        )
        assert res_tick1 is None
        assert symbol in pem.pending_queue

        # Tick 2: Spot pulls back to VWAP (diff = 3.0 pts <= 5.0 pts threshold) -> Confirmed!
        res_tick2 = pem.check_pending_signal(
            symbol=symbol,
            current_spot=22448.0,
            live_vwap=22445.0,
            rsi_1m_period_5=48.0
        )
        assert res_tick2 is not None
        assert res_tick2["status"] == "PULLBACK_CONFIRMED"
        assert "pullback_wait_duration_ms" in res_tick2
        assert symbol not in pem.pending_queue

    def test_pullback_timeout_after_180_seconds_discards_safely(self):
        """
        Verify that candidate held longer than 180 seconds is safely discarded
        with status PULLBACK_TIMEOUT_DISCARD rather than chasing at candle tops.
        """
        pem = PullbackExecutionManager()
        symbol = "BANKNIFTY"
        raw_signal = {"symbol": symbol, "decision": "BUY_CALL", "spot_price": 48200.0}

        pem.register_candidate_signal(symbol, raw_signal)
        # Mock creation time to 185 seconds ago
        pem.pending_queue[symbol]["created_at"] = datetime.fromtimestamp(
            time.time() - 185, tz=timezone.utc
        )

        res = pem.check_pending_signal(
            symbol=symbol,
            current_spot=48250.0,
            live_vwap=48180.0,
            rsi_1m_period_5=68.0
        )
        assert res is not None
        assert res["status"] == "PULLBACK_TIMEOUT_DISCARD"
        assert symbol not in pem.pending_queue

    # =========================================================================
    # Test 3: Spot-Anchored Structural Stops (Noise Immunity)
    # =========================================================================
    def test_spot_intact_with_option_drawdown_keeps_position_open(self):
        """
        Simulation of October 09 defect:
        Spot is 22,410 (above VWAP 22,400 - 8 = 22,392 and prior 15m low 22,385),
        while option premium temporarily draws down -10% (100 -> 90).
        Position MUST REMAIN OPEN without being shaken out by option noise.
        """
        entry_premium = 100.0
        current_premium = 90.0  # -10% option drawdown
        current_spot = 22410.0
        live_vwap = 22400.0
        prior_15m_low = 22385.0

        eval_res = StructuralRiskManager.evaluate_structural_stop(
            decision="BUY_CALL",
            current_spot=current_spot,
            live_vwap=live_vwap,
            entry_premium=entry_premium,
            current_premium=current_premium,
            prior_15m_low=prior_15m_low
        )

        assert eval_res["is_stop_triggered"] is False, "Position must NOT be stopped out on noise"
        assert eval_res["structural_support_intact"] is True
        assert eval_res["spot_structural_sl"] == min(prior_15m_low, live_vwap - 8.0)
        assert eval_res["premium_drawdown_pct"] == -10.0

    def test_spot_support_breakdown_triggers_exit(self):
        """
        Verify that if underlying index drops below structural support (e.g. 22,380 < 22,392),
        exit is triggered strictly on spot breakdown.
        """
        entry_premium = 100.0
        current_premium = 88.0
        current_spot = 22380.0  # Below support 22,392
        live_vwap = 22400.0
        prior_15m_low = 22395.0

        eval_res = StructuralRiskManager.evaluate_structural_stop(
            decision="BUY_CALL",
            current_spot=current_spot,
            live_vwap=live_vwap,
            entry_premium=entry_premium,
            current_premium=current_premium,
            prior_15m_low=prior_15m_low
        )

        assert eval_res["is_stop_triggered"] is True
        assert eval_res["exit_reason"] == "STRUCTURAL_SPOT_SUPPORT_BREACH"
        assert eval_res["is_emergency_stop"] is False

    def test_emergency_option_circuit_breaker_triggers_at_minus_25_percent(self):
        """
        Verify that a -25% option collapse (100 -> 74) triggers the emergency circuit breaker
        even if spot hasn't breached support yet (protects against black-swan freeze/IV crush).
        """
        entry_premium = 100.0
        current_premium = 74.0  # -26% drop <= 75.0 floor
        current_spot = 22450.0  # Spot is still fine
        live_vwap = 22400.0

        eval_res = StructuralRiskManager.evaluate_structural_stop(
            decision="BUY_CALL",
            current_spot=current_spot,
            live_vwap=live_vwap,
            entry_premium=entry_premium,
            current_premium=current_premium
        )

        assert eval_res["is_stop_triggered"] is True
        assert eval_res["is_emergency_stop"] is True
        assert eval_res["exit_reason"] == "EMERGENCY_PREMIUM_STOP_HIT"

    # =========================================================================
    # Test 4: Asymmetric Multi-Tier Profit Trailing Engine
    # =========================================================================
    def test_even_lot_sizing_enforcement(self):
        """
        Verify lot sizing is enforced in even multiples of lots (min 2 lots).
        """
        # NIFTY lot size 65
        qty_1lot_req, lots_1 = AsymmetricTradeLifecycle.enforce_even_lots(65, requested_lots=1)
        assert lots_1 == 2, "1 lot requested must be rounded up to 2 lots"
        assert qty_1lot_req == 130

        # BANKNIFTY lot size 30 with 3 lots requested
        qty_3lot_req, lots_3 = AsymmetricTradeLifecycle.enforce_even_lots(30, requested_lots=3)
        assert lots_3 == 4, "3 lots requested must be rounded up to 4 lots (even)"
        assert qty_3lot_req == 120

    def test_six_percent_premium_spike_shifts_sl_to_entry_plus_one(self):
        """
        Verify that when option premium gains >= +6.0% (e.g. 100 -> 106.5),
        Stop Loss dynamically ratchets to entry_premium + 1.00 (101.00).
        """
        entry_prem = 100.0
        current_prem = 106.50  # +6.5% gain
        initial_sl = 75.00

        res = AsymmetricTradeLifecycle.evaluate_lifecycle_state(
            entry_premium=entry_prem,
            current_premium=current_prem,
            highest_observed_premium=current_prem,
            current_sl_premium=initial_sl,
            tier1_booked=False,
            lot_size=65,
            total_lots=2,
            remaining_lots=2
        )

        assert res["current_sl_premium"] == 101.00, "SL must ratchet to entry + 1.00"
        assert res["active_tier_label"] == "BREAKEVEN_RATCHET_ACTIVE"
        assert res["tier1_booked"] is False
        assert res["remaining_lots"] == 2

    def test_tier1_partial_booking_at_twelve_to_fifteen_percent(self):
        """
        Verify that when option premium gains >= +12% (e.g. 100 -> 113.0),
        50% position (1 lot) is booked, tier1_hit_timestamp is set, and 1 lot runs.
        """
        entry_prem = 100.0
        current_prem = 113.00  # +13% gain
        current_sl = 101.00

        res = AsymmetricTradeLifecycle.evaluate_lifecycle_state(
            entry_premium=entry_prem,
            current_premium=current_prem,
            highest_observed_premium=current_prem,
            current_sl_premium=current_sl,
            tier1_booked=False,
            lot_size=65,
            total_lots=2,
            remaining_lots=2
        )

        assert res["tier1_booked"] is True
        assert res["tier1_hit_timestamp"] is not None
        assert res["remaining_lots"] == 1
        assert len(res["actions_to_execute"]) == 1
        assert res["actions_to_execute"][0]["action"] == "PARTIAL_MARKET_EXIT"
        assert res["actions_to_execute"][0]["lots_to_exit"] == 1
        assert res["actions_to_execute"][0]["qty_to_exit"] == 65
        assert res["active_tier_label"] == "TIER1_PARTIAL_PROFIT_BOOKED"

    def test_tier2_runner_trails_until_spot_trend_reversal(self):
        """
        Verify that after Tier 1 is booked, the remaining runner continues running
        without static target cap until spot trend structure confirms reversal.
        """
        entry_prem = 100.0
        current_prem = 145.00  # +45% runner gain
        current_sl = 101.00

        # Step A: Trend intact -> Runner remains active
        res_running = AsymmetricTradeLifecycle.evaluate_lifecycle_state(
            entry_premium=entry_prem,
            current_premium=current_prem,
            highest_observed_premium=current_prem,
            current_sl_premium=current_sl,
            tier1_booked=True,
            tier1_hit_timestamp="2026-10-09T10:30:00Z",
            is_spot_trend_reversed=False,
            lot_size=65,
            total_lots=2,
            remaining_lots=1
        )
        assert res_running["lifecycle_status"] == "POSITION_ACTIVE"
        assert res_running["active_tier_label"] == "TIER2_RUNNER_ACTIVE"
        assert len(res_running["actions_to_execute"]) == 0

        # Step B: Spot trend structure confirms reversal -> Runner exits!
        res_exit = AsymmetricTradeLifecycle.evaluate_lifecycle_state(
            entry_premium=entry_prem,
            current_premium=142.00,
            highest_observed_premium=145.00,
            current_sl_premium=current_sl,
            tier1_booked=True,
            tier1_hit_timestamp="2026-10-09T10:30:00Z",
            is_spot_trend_reversed=True,
            lot_size=65,
            total_lots=2,
            remaining_lots=1
        )
        assert res_exit["lifecycle_status"] == "RUNNER_EXITED_ON_TREND_REVERSAL"
        assert res_exit["active_tier_label"] == "RUNNER_COMPLETED"
        assert len(res_exit["actions_to_execute"]) == 1
        assert res_exit["actions_to_execute"][0]["action"] == "FULL_MARKET_EXIT"
        assert res_exit["actions_to_execute"][0]["lots_to_exit"] == 1

    # =========================================================================
    # Test 5: End-to-End ShadowSignalLogger Integration & Firestore Schemas
    # =========================================================================
    def test_shadow_signal_logger_e2e_integration_with_telemetry(self):
        """
        Verify that log_shadow_signal commits structured telemetry fields:
          - ml_consensus_min
          - spot_structural_sl
          - pullback_wait_duration_ms
          - tier1_hit_timestamp
        And sets active_positions document for real-time risk monitoring.
        """
        logger_service = ShadowSignalLogger()
        mock_db = MagicMock()
        logger_service.db = mock_db

        payload = logger_service.log_shadow_signal(
            symbol="NIFTY",
            spot_price=22450.0,
            decision="BUY_CALL",
            confidence_score=0.75,
            catboost_prob=0.72,
            lightgbm_prob=0.78,
            xgboost_prob=0.68,
            live_vwap=22445.0,
            prior_15m_low=22420.0,
            pullback_wait_duration_ms=45000,
            requested_lots=2
        )

        assert payload is not None
        assert payload["ml_consensus_min"] == 0.68
        assert payload["spot_structural_sl"] == min(22420.0, 22445.0 - 8.0)  # 22420.0
        assert payload["pullback_wait_duration_ms"] == 45000
        assert payload["tier1_hit_timestamp"] is None
        assert payload["tier1_booked"] is False
        assert payload["total_lots"] == 2
        assert payload["trade_bracket"]["lot_size"] == 130  # 65 * 2

        # Verify calls to Firestore collections: ai_signals_ledger and active_positions
        collections_called = [call[0][0] for call in mock_db.collection.call_args_list]
        assert "ai_signals_ledger" in collections_called
        assert "active_positions" in collections_called
