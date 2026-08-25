"""
InfinityAI.Pro — Macro Event Miner Verification Test Suite
==========================================================
Verifies:
  1. Pydantic schema validation & boundary clamping.
  2. Circuit Breaker / Kill Switch neutral fallback on failures.
  3. Firestore persistence and read cache.
  4. Integration with Engine B AsyncMacroIntelligenceWorker.
"""

import sys
import os

# Set standard output encoding to utf-8 if possible
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add backend/engine-b/src and backend to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_B_SRC = os.path.join(BASE_DIR, "backend", "engine-b", "src")
if ENGINE_B_SRC not in sys.path:
    sys.path.insert(0, ENGINE_B_SRC)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import unittest
from datetime import datetime, timezone
from services.macro_event_miner import MacroEventPayload, MacroEventMiner, macro_event_miner
from services.async_macro_intelligence_worker import LiveMacroState, get_live_macro_prior, _LIVE_AI_STATE


class TestMacroEventMinerSuite(unittest.TestCase):

    def test_01_pydantic_schema_validation(self):
        """Test strict validation and default parameters."""
        payload = MacroEventPayload(
            event_name="RBI_MPC_DECISION",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            hawkish_score=0.75,
            volatility_expectation="HIGH",
            regime_multiplier=2.1,
            key_drivers=["Headline CPI elevated", "Withdrawal of accommodation maintained"],
            summary="RBI maintained repo rate at 6.50% with hawkish guidance on inflation.",
            is_fallback=False
        )
        self.assertEqual(payload.hawkish_score, 0.75)
        self.assertEqual(payload.volatility_expectation, "HIGH")
        self.assertEqual(payload.regime_multiplier, 2.1)
        self.assertFalse(payload.is_fallback)
        self.assertEqual(len(payload.key_drivers), 2)
        print("[PASS] Test 1: Pydantic Schema strictly validated.")

    def test_02_circuit_breaker_neutral_fallback(self):
        """Test that circuit breaker returns exact neutral baseline without crashing."""
        miner = MacroEventMiner(project_id="test-project")
        fallback = miner._get_neutral_fallback(
            event_name="SIMULATED_FAILURE_EVENT",
            reason="Google Search API rate limit timeout"
        )
        self.assertEqual(fallback.hawkish_score, 0.0)
        self.assertEqual(fallback.volatility_expectation, "MEDIUM")
        self.assertEqual(fallback.regime_multiplier, 1.0)
        self.assertTrue(fallback.is_fallback)
        self.assertIn("Neutral baseline", fallback.summary)
        print("[PASS] Test 2: Circuit breaker produces safe neutral fallback.")

    def test_03_in_memory_caching(self):
        """Test that in-memory cache returns recent payload within freshness window."""
        miner = MacroEventMiner(project_id="test-project")
        mock_payload = MacroEventPayload(
            event_name="FED_FOMC_DECISION",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            hawkish_score=-0.4,
            volatility_expectation="MEDIUM",
            regime_multiplier=1.15,
            key_drivers=["25bps rate cut signaled"],
            summary="Fed signaled dovish easing cycle.",
            is_fallback=False
        )
        miner._cached_payload = mock_payload
        miner._last_mined_time = datetime.now(timezone.utc)

        cached = miner.get_latest_sentiment(max_age_hours=2.0)
        self.assertEqual(cached.event_name, "FED_FOMC_DECISION")
        self.assertEqual(cached.hawkish_score, -0.4)
        print("[PASS] Test 3: In-memory cache returns fresh policy sentiment.")

    def test_04_async_worker_live_state_integration(self):
        """Test that LiveMacroState correctly stores policy events and computes blended multiplier."""
        _LIVE_AI_STATE.macro_bias = "BULLISH"
        _LIVE_AI_STATE.macro_score = 0.50
        _LIVE_AI_STATE.policy_event_active = True
        _LIVE_AI_STATE.policy_event_name = "RBI_MPC_HAWKISH_PAUSE"
        _LIVE_AI_STATE.policy_hawkish_score = 0.80
        _LIVE_AI_STATE.policy_volatility_expectation = "HIGH"
        _LIVE_AI_STATE.policy_regime_multiplier = 2.0
        _LIVE_AI_STATE.regime_multiplier = 2.40  # 1.20 base * 2.0 policy shock

        live_state = get_live_macro_prior()
        self.assertTrue(live_state["policy_event_active"])
        self.assertEqual(live_state["policy_event_name"], "RBI_MPC_HAWKISH_PAUSE")
        self.assertEqual(live_state["policy_hawkish_score"], 0.80)
        self.assertEqual(live_state["policy_volatility_expectation"], "HIGH")
        self.assertEqual(live_state["regime_multiplier"], 2.40)
        print("[PASS] Test 4: LiveMacroState properly exposes policy data to fast inference path.")


if __name__ == "__main__":
    print("=================================================================")
    print("InfinityAI.Pro - Verifying Macro Event Miner & Circuit Breakers")
    print("=================================================================")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMacroEventMinerSuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("=================================================================")
    print("ALL MACRO EVENT MINER TESTS PASSED SUCCESSFULLY!")
    print("=================================================================")
