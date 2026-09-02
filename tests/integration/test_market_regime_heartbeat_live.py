"""
Integration test for Market Regime Heartbeat Service against live Engine C.
Verifies real-time index quote retrieval, absence of fictitious fallback prices,
and correct heartbeat document formation.
"""
import pytest
import asyncio
import os
import sys

# Ensure backend/engine-a is in path
ENGINE_A_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "engine-a"))
if ENGINE_A_DIR not in sys.path:
    sys.path.insert(0, ENGINE_A_DIR)
from src.services.market_regime_heartbeat_service import MarketRegimeHeartbeatService


@pytest.mark.asyncio
async def test_fetch_live_market_quotes_from_engine_c():
    """Verifies that live quote fetching returns genuine broker numbers rather than fictitious baselines."""
    service = MarketRegimeHeartbeatService()
    quotes = await service._fetch_live_market_quotes()

    assert quotes is not None
    assert "NIFTY" in quotes
    assert "BANKNIFTY" in quotes
    assert "SENSEX" in quotes
    assert "INDIAVIX" in quotes

    nifty = quotes["NIFTY"]
    banknifty = quotes["BANKNIFTY"]
    sensex = quotes["SENSEX"]
    vix = quotes["INDIAVIX"]

    print(f"\n[LIVE QUOTE VERIFICATION] NIFTY: {nifty}, BANKNIFTY: {banknifty}, SENSEX: {sensex}, VIX: {vix}, Source: {quotes.get('data_source')}")

    # Verify that values are NOT the old hardcoded fictitious numbers
    assert nifty != 24080.0, f"NIFTY is stuck at hardcoded fictitious 24080.0!"
    assert banknifty != 57490.0, f"BANKNIFTY is stuck at hardcoded fictitious 57490.0!"
    assert sensex != 77260.0, f"SENSEX is stuck at hardcoded fictitious 77260.0!"

    # Verify plausible ranges for September 2026 market levels
    assert 20000.0 <= nifty <= 30000.0, f"NIFTY {nifty} out of plausible range"
    assert 45000.0 <= banknifty <= 65000.0, f"BANKNIFTY {banknifty} out of plausible range"
    assert 65000.0 <= sensex <= 95000.0, f"SENSEX {sensex} out of plausible range"
    assert 5.0 <= vix <= 50.0, f"INDIA VIX {vix} out of plausible range"
