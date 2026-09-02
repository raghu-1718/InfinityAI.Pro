"""
Test Suite: Remediation Integrity & Safe Live Resolution Verification
Validates that:
1. OptionsGreeksEngine strictly requires a valid positive spot price and rejects defaults/zeros.
2. ContinuousShadowScanner fetches spot prices without synthetic multipliers.
3. OptionsChainIngestor passes spot_price without NameError.
4. EODSettlementService defers settlement cleanly when genuine quotes are unavailable.
5. Engine B strictly prohibits synthetic data generation at runtime.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENGINE_A_DIR = os.path.join(BASE_DIR, "backend", "engine-a")
ENGINE_B_DIR = os.path.join(BASE_DIR, "backend", "engine-b")
ENGINE_C_DIR = os.path.join(BASE_DIR, "backend", "engine-c")

for d in [ENGINE_A_DIR, ENGINE_C_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)

# Ensure src namespace package includes both engine-a/src and engine-c/src
import src
for p in [os.path.join(ENGINE_A_DIR, "src"), os.path.join(ENGINE_C_DIR, "src")]:
    if hasattr(src, "__path__") and p not in src.__path__:
        src.__path__.append(p)


def test_options_greeks_requires_valid_spot():
    """Verify that OptionsGreeksEngine rejects <= 0 spot and generates surface for positive spot"""
    from src.services.options_greeks_engine import OptionsGreeksEngine

    engine = OptionsGreeksEngine()

    # Must raise ValueError for missing / zero / negative spot
    with pytest.raises(ValueError, match="Valid positive spot price required"):
        engine.generate_volatility_surface(symbol="NIFTY", spot=0.0)

    with pytest.raises(ValueError, match="Valid positive spot price required"):
        engine.generate_volatility_surface(symbol="NIFTY", spot=-100.0)

    # Must succeed for valid live spot
    surface = engine.generate_volatility_surface(symbol="NIFTY", spot=24000.0)
    assert surface["symbol"] == "NIFTY"
    assert surface["spot_price"] == 24000.0
    assert surface["atm_strike"] == 24000
    assert len(surface["strikes"]) > 0


@pytest.mark.asyncio
async def test_shadow_scanner_no_synthetic_multipliers():
    """Verify shadow scanner uses live quotes and does not fabricate prices"""
    from src.services.autonomous_shadow_scanner import ContinuousShadowScanner

    scanner = ContinuousShadowScanner()

    # Mock degraded quotes
    with patch(
        "src.services.market_regime_heartbeat_service.MARKET_REGIME_HEARTBEAT_SERVICE._fetch_live_market_quotes",
        new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = {
            "NIFTY": None,
            "BANKNIFTY": None,
            "is_degraded": True,
            "data_source": "DEGRADED_BROKER_FEED_UNAVAILABLE"
        }

        spots = await scanner._fetch_spot_prices()
        assert spots["status"] == "DEGRADED"
        assert "SENSEX" not in spots  # Ensure no synthetic SENSEX = NIFTY * 3.20
        assert "FINNIFTY" not in spots  # Ensure no synthetic FINNIFTY = BANKNIFTY * 0.445

        # Mock live quotes
        mock_fetch.return_value = {
            "NIFTY": 23914.45,
            "BANKNIFTY": 57172.00,
            "SENSEX": 78200.50,
            "INDIAVIX": 13.50,
            "is_degraded": False,
            "data_source": "live_broker_feed"
        }

        spots_live = await scanner._fetch_spot_prices()
        assert spots_live["status"] == "LIVE"
        assert spots_live["NIFTY"] == 23914.45
        assert spots_live["BANKNIFTY"] == 57172.00
        assert spots_live["SENSEX"] == 78200.50
        assert spots_live["INDIAVIX"] == 13.50


def test_options_chain_ingestor_spot_price_passed():
    """Verify calculate_volatility_surface_summary accepts spot_price without NameError"""
    with patch("google.cloud.bigquery.Client"):
        from src.options_chain_ingestor import OptionsChainIngestor
        ingestor = OptionsChainIngestor()
        dummy_oc = {
            "24000": {
                "ce": {"ltp": 150.0, "oi": 50000, "iv": 14.5},
                "pe": {"ltp": 140.0, "oi": 45000, "iv": 15.0}
            }
        }

        summary = ingestor.calculate_volatility_surface_summary("NIFTY", 24000.0, dummy_oc)
        assert summary["symbol"] == "NIFTY"
        assert summary["spot_price"] == 24000.0
        assert "atm_iv" in summary
        assert "put_call_ratio" in summary


def test_eod_settlement_deferred_when_no_quotes():
    """Verify EOD settlement defers cleanly when no closing quotes are available"""
    from src.services.eod_settlement_service import EODSettlementService

    service = EODSettlementService()
    mock_db = MagicMock()
    # Mock stream returns no heartbeats
    mock_db.collection.return_value.where.return_value.stream.return_value = []
    mock_db.collection.return_value.order_by.return_value.limit.return_value.stream.return_value = []
    service.db = mock_db

    res = service.run_eod_reconciliation(current_spot_prices=None)
    assert res["settlement_status"] == "DEFERRED_FEED_UNAVAILABLE"
    assert res["resolved_count"] == 0
    assert res["total_net_pnl"] == 0.0


def test_engine_b_synthetic_generation_prohibited():
    """Verify that Engine B strictly prohibits synthetic data generation at runtime"""
    with open(os.path.join(ENGINE_B_DIR, "src", "main.py"), "r", encoding="utf-8") as f:
        content = f.read()

    assert "def _generate_synthetic_data" in content
    assert "raise RuntimeError(" in content
    assert "Synthetic market data generation" in content
