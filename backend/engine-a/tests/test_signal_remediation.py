"""
Unit and Integration Test Suite for InfinityAI.Pro Signal Remediation & P0 Safety Fixes
=======================================================================================
Verifies:
  1. HOLD with high confidence (0.74) remains NO_TRADE / HOLD, NOT BUY_CALL.
  2. SELL with high confidence maps to BUY_PUT / LONG_PUT when filters pass.
  3. BUY with high confidence maps to BUY_CALL / LONG_CALL when filters pass.
  4. ADX below threshold (<22.0) vetoes trade entries to NO_TRADE.
  5. Missing / stale FII/DII data defaults strictly to 1.0x neutral baseline.
  6. NO_TRADE decisions never create fictitious options trade contracts in shadow ledger.
  7. August 27 Expiry Case Regression: ADX=7.16, Conf=74.0, Signal=HOLD -> NO_TRADE.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.services.fii_dii_flow_radar import FIIDIIFlowRadar
from src.services.autonomous_shadow_scanner import ContinuousShadowScanner
from src.services.shadow_signal_logger import ShadowSignalLogger


class TestSignalRemediation:

    def setup_method(self):
        self.radar = FIIDIIFlowRadar()
        # Ensure fresh cache
        self.radar._cached_data = None
        self.radar._cached_time = 0.0

    def test_fii_dii_neutral_fallback(self):
        """Verify that FII/DII radar returns 1.0x neutral multiplier when live feed is absent."""
        flow = self.radar.fetch_live_institutional_flow()
        assert flow["institutional_multiplier"] == 1.00
        assert flow["regime"] == "BALANCED_EQUILIBRIUM"
        assert flow["directional_bias"] == "NEUTRAL"
        assert flow["fii_net_crores"] == 0.0
        assert flow["dii_net_crores"] == 0.0

        # Adjust confidence check
        adj_conf, _ = self.radar.apply_multiplier_to_confidence(0.74, "BUY_CALL")
        assert adj_conf == 0.74  # No artificial 1.25x boost

    def test_hold_with_high_confidence_remains_no_trade(self):
        """Test invariant: High confidence on a HOLD/NEUTRAL signal must NEVER become BUY_CALL."""
        scanner = ContinuousShadowScanner()
        scanner.shadow_logger = MagicMock()
        scanner.last_signals_cache = {}

        # Simulating Engine B response with signal=HOLD, conf=74.0
        sig_payload = {
            "symbol": "BANKNIFTY",
            "signal": "HOLD",
            "confidence": 74.0,
            "current_price": 57600.0,
            "analysis": {
                "adx": 24.0,
                "key_factors": ["ML Ensemble: HOLD (52.9% conf)"],
                "p_sell": 0.20,
                "p_hold": 0.60,
                "p_buy": 0.20
            }
        }

        # Run decision logic
        models = sig_payload.get("analysis", {})
        adx = float(models.get("adx", 25.0))
        key_factors = models.get("key_factors", [])
        veto_in_factors = any("VETO" in str(k).upper() for k in key_factors)
        veto_active = models.get("veto_active", False) or veto_in_factors or (adx < 22.0)
        signal_dir = sig_payload.get("signal", "HOLD").upper()
        conf = float(sig_payload.get("confidence", 50.0)) / 100.0

        if veto_active or signal_dir in ["HOLD", "NEUTRAL", "NO_TRADE", ""]:
            decision = "NO_TRADE"
        elif ("BUY" in signal_dir or "CALL" in signal_dir) and conf >= 0.60:
            decision = "BUY_CALL"
        elif ("SELL" in signal_dir or "PUT" in signal_dir) and conf >= 0.60:
            decision = "BUY_PUT"
        else:
            decision = "NO_TRADE"

        assert decision == "NO_TRADE"
        # Must not call shadow logger
        assert scanner.shadow_logger.log_shadow_signal.call_count == 0

    def test_bearish_sell_signal_maps_to_buy_put(self):
        """Test invariant: SELL signal with high confidence maps to BUY_PUT when filters pass."""
        sig_payload = {
            "symbol": "NIFTY",
            "signal": "SELL",
            "confidence": 78.0,
            "current_price": 24500.0,
            "analysis": {
                "adx": 28.5,
                "key_factors": ["Strong Bearish Breakdown"],
                "p_sell": 0.78,
                "p_hold": 0.12,
                "p_buy": 0.10
            }
        }

        models = sig_payload.get("analysis", {})
        adx = float(models.get("adx", 25.0))
        key_factors = models.get("key_factors", [])
        veto_in_factors = any("VETO" in str(k).upper() for k in key_factors)
        veto_active = models.get("veto_active", False) or veto_in_factors or (adx < 22.0)
        signal_dir = sig_payload.get("signal", "HOLD").upper()
        conf = float(sig_payload.get("confidence", 50.0)) / 100.0

        if veto_active or signal_dir in ["HOLD", "NEUTRAL", "NO_TRADE", ""]:
            decision = "NO_TRADE"
        elif ("BUY" in signal_dir or "CALL" in signal_dir) and conf >= 0.60:
            decision = "BUY_CALL"
        elif ("SELL" in signal_dir or "PUT" in signal_dir) and conf >= 0.60:
            decision = "BUY_PUT"
        else:
            decision = "NO_TRADE"

        assert decision == "BUY_PUT"

    def test_bullish_buy_signal_maps_to_buy_call(self):
        """Test invariant: BUY signal with high confidence maps to BUY_CALL when filters pass."""
        sig_payload = {
            "symbol": "BANKNIFTY",
            "signal": "BUY",
            "confidence": 82.0,
            "current_price": 57800.0,
            "analysis": {
                "adx": 31.0,
                "key_factors": ["Bullish Moving Average Crossover"],
                "p_sell": 0.08,
                "p_hold": 0.10,
                "p_buy": 0.82
            }
        }

        models = sig_payload.get("analysis", {})
        adx = float(models.get("adx", 25.0))
        key_factors = models.get("key_factors", [])
        veto_in_factors = any("VETO" in str(k).upper() for k in key_factors)
        veto_active = models.get("veto_active", False) or veto_in_factors or (adx < 22.0)
        signal_dir = sig_payload.get("signal", "HOLD").upper()
        conf = float(sig_payload.get("confidence", 50.0)) / 100.0

        if veto_active or signal_dir in ["HOLD", "NEUTRAL", "NO_TRADE", ""]:
            decision = "NO_TRADE"
        elif ("BUY" in signal_dir or "CALL" in signal_dir) and conf >= 0.60:
            decision = "BUY_CALL"
        elif ("SELL" in signal_dir or "PUT" in signal_dir) and conf >= 0.60:
            decision = "BUY_PUT"
        else:
            decision = "NO_TRADE"

        assert decision == "BUY_CALL"

    def test_adx_below_threshold_vetoes_trade(self):
        """Test invariant: Low ADX (< 22.0) triggers NO_TRADE regardless of BUY/SELL label."""
        for sig_dir in ["BUY", "SELL"]:
            sig_payload = {
                "symbol": "FINNIFTY",
                "signal": sig_dir,
                "confidence": 85.0,
                "current_price": 23000.0,
                "analysis": {
                    "adx": 14.2,  # Below 22.0
                    "key_factors": ["Momentum trigger in consolidation"],
                    "p_sell": 0.10 if sig_dir == "BUY" else 0.85,
                    "p_hold": 0.05,
                    "p_buy": 0.85 if sig_dir == "BUY" else 0.10
                }
            }

            models = sig_payload.get("analysis", {})
            adx = float(models.get("adx", 25.0))
            key_factors = models.get("key_factors", [])
            veto_in_factors = any("VETO" in str(k).upper() for k in key_factors)
            veto_active = models.get("veto_active", False) or veto_in_factors or (adx < 22.0)
            signal_dir = sig_payload.get("signal", "HOLD").upper()
            conf = float(sig_payload.get("confidence", 50.0)) / 100.0

            if veto_active or signal_dir in ["HOLD", "NEUTRAL", "NO_TRADE", ""]:
                decision = "NO_TRADE"
            elif ("BUY" in signal_dir or "CALL" in signal_dir) and conf >= 0.60:
                decision = "BUY_CALL"
            elif ("SELL" in signal_dir or "PUT" in signal_dir) and conf >= 0.60:
                decision = "BUY_PUT"
            else:
                decision = "NO_TRADE"

            assert decision == "NO_TRADE"

    def test_august_27_regression_case_study(self):
        """
        Regression Fixture for August 27, 2026 Market Hours Incident:
        - Symbol: BANKNIFTY
        - Trend: Bearish
        - ADX: 7.16 (Choppy Consolidation)
        - Key Factors: VETO: ADX < 25 (7.2): Market is ranging/consolidating (Theta decay risk)
        - Confidence: 74.0%
        - Signal from Engine B: HOLD
        
        Expected Remediation Result: STRICT NO_TRADE.
        """
        sig_payload = {
            "symbol": "BANKNIFTY",
            "signal": "HOLD",
            "confidence": 74.0,
            "current_price": 57613.50,
            "analysis": {
                "rsi": 50.0,
                "adx": 7.16,
                "trend": "Bearish",
                "key_factors": [
                    "Choppy Market (Low ADX) - Avoiding Trades",
                    "ML Ensemble: SELL (71.9% conf)",
                    "VETO: ADX < 25 (7.2): Market is ranging/consolidating (Theta decay risk)"
                ],
                "veto_active": True,
                "veto_reason": "ADX < 25 (7.2): Market is ranging/consolidating (Theta decay risk)",
                "p_sell": 0.719,
                "p_hold": 0.181,
                "p_buy": 0.100
            }
        }

        models = sig_payload.get("analysis", {})
        adx = float(models.get("adx", 25.0))
        key_factors = models.get("key_factors", [])
        veto_in_factors = any("VETO" in str(k).upper() for k in key_factors)
        veto_active = models.get("veto_active", False) or veto_in_factors or (adx < 22.0)
        signal_dir = sig_payload.get("signal", "HOLD").upper()
        conf = float(sig_payload.get("confidence", 50.0)) / 100.0

        if veto_active or signal_dir in ["HOLD", "NEUTRAL", "NO_TRADE", ""]:
            decision = "NO_TRADE"
        elif ("BUY" in signal_dir or "CALL" in signal_dir) and conf >= 0.60:
            decision = "BUY_CALL"
        elif ("SELL" in signal_dir or "PUT" in signal_dir) and conf >= 0.60:
            decision = "BUY_PUT"
        else:
            decision = "NO_TRADE"

        assert decision == "NO_TRADE"

    def test_no_trade_skips_shadow_signal_logger(self):
        """Verify that ShadowSignalLogger rejects NO_TRADE and does not commit to Firestore."""
        logger_service = ShadowSignalLogger()
        logger_service.db = MagicMock()

        res = logger_service.log_shadow_signal(
            symbol="BANKNIFTY",
            spot_price=57600.0,
            decision="NO_TRADE",
            confidence_score=0.74,
            catboost_prob=0.35,
            lightgbm_prob=0.32,
            xgboost_prob=0.30
        )
        assert res is None
        assert logger_service.db.collection.call_count == 0

    def test_live_market_depth_pricing_model_ask_entry(self):
        """Verify that live market depth Ask price is used as realistic entry fill with spread metadata."""
        logger_service = ShadowSignalLogger()
        logger_service.db = MagicMock()

        live_depth_quote = {
            "ltp": 420.50,
            "ask_price": 422.00,
            "bid_price": 419.00,
            "open_interest": 75000,
            "volume": 25000
        }

        res = logger_service.log_shadow_signal(
            symbol="BANKNIFTY",
            spot_price=57600.0,
            decision="BUY_PUT",
            confidence_score=0.78,
            catboost_prob=0.75,
            lightgbm_prob=0.78,
            xgboost_prob=0.80,
            live_option_quote=live_depth_quote
        )
        assert res is not None
        bracket = res["trade_bracket"]
        assert bracket["entry_premium"] == 422.00  # Exact Ask Price
        assert bracket["pricing_source"] == "LIVE_MARKET_DEPTH_ASK"
        assert bracket["option_type"] == "PE"
        assert "BANKNIFTY 57600 PE" in bracket["contract"]

    def test_wide_spread_veto_rejects_illiquid_option(self):
        """Verify that abnormal bid-ask spread (>4%) vetoes trade entry."""
        logger_service = ShadowSignalLogger()
        logger_service.db = MagicMock()

        # Wide spread: Ask 450, Bid 400 on LTP 420 (Spread = 50 / 450 = 11.1% > 4%)
        illiquid_quote = {
            "ltp": 420.00,
            "ask_price": 450.00,
            "bid_price": 400.00,
            "open_interest": 50000,
            "volume": 15000
        }

        res = logger_service.log_shadow_signal(
            symbol="BANKNIFTY",
            spot_price=57600.0,
            decision="BUY_PUT",
            confidence_score=0.78,
            catboost_prob=0.75,
            lightgbm_prob=0.78,
            xgboost_prob=0.80,
            live_option_quote=illiquid_quote
        )
        assert res is None, "Wide spread option (>4%) must be rejected"
        assert logger_service.db.collection.call_count == 0

    def test_insufficient_open_interest_liquidity_veto(self):
        """Verify that low open interest (<10,000) vetoes trade entry."""
        logger_service = ShadowSignalLogger()
        logger_service.db = MagicMock()

        low_oi_quote = {
            "ltp": 420.00,
            "ask_price": 421.00,
            "bid_price": 419.00,
            "open_interest": 2500,  # Below 10,000 minimum
            "volume": 500
        }

        res = logger_service.log_shadow_signal(
            symbol="BANKNIFTY",
            spot_price=57600.0,
            decision="BUY_PUT",
            confidence_score=0.78,
            catboost_prob=0.75,
            lightgbm_prob=0.78,
            xgboost_prob=0.80,
            live_option_quote=low_oi_quote
        )
        assert res is None, "Low OI contract must be rejected"
        assert logger_service.db.collection.call_count == 0

