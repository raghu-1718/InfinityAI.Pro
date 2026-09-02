"""
Integration Tests for Live Market Data & Dual-Source Reconciliation Engine
"""
import pytest
from market_reconciliation.primary_feed import PrimaryMarketFeed
from market_reconciliation.secondary_feed import SecondaryMarketFeed
from market_reconciliation.reconciler import MarketDataReconciler
from market_reconciliation.scheduled_runner import run_reconciliation_batch, scheduled_audit_loop


@pytest.mark.asyncio
async def test_primary_and_secondary_feed_connectivity():
    """Verify both feeds return valid market quotes with required fields."""
    p_feed = PrimaryMarketFeed()
    s_feed = SecondaryMarketFeed()

    p_quote = await p_feed.get_latest_quote("NIFTY")
    s_quote = await s_feed.get_latest_quote("NIFTY")

    assert p_quote["symbol"] == "NIFTY"
    assert p_quote["last_price"] > 0
    assert p_quote["source"] == "dhanhq_primary"

    assert s_quote["symbol"] == "NIFTY"
    assert s_quote["last_price"] > 0
    assert s_quote["source"] == "secondary_independent"


@pytest.mark.asyncio
async def test_reconciliation_pass_under_threshold():
    """Verify dual-source prices within 0.75% tolerance produce PASS status."""
    reconciler = MarketDataReconciler()
    result = await reconciler.reconcile_symbol("NIFTY", threshold_pct=0.75)

    assert result.status == "PASS"
    assert result.discrepancy_pct <= 0.75
    assert result.symbol == "NIFTY"
    assert "Reconciliation successful" in result.details


def test_reconciliation_flags_discrepancy_above_threshold():
    """Verify that price divergence exceeding tolerance produces FLAGGED status."""
    reconciler = MarketDataReconciler()
    # Injected divergence: Primary 25,000 vs Secondary 24,500 (~2.04% diff)
    result = reconciler.compute_discrepancy(
        primary_price=25000.0,
        secondary_price=24500.0,
        symbol="NIFTY",
        threshold_pct=0.75
    )

    assert result.status == "FLAGGED"
    assert result.discrepancy_pct > 0.75
    assert "ALERT: Price discrepancy" in result.details


@pytest.mark.asyncio
async def test_scheduled_reconciliation_audit_loop():
    """Verify scheduled multi-tick reconciliation runner completes multiple audit cycles."""
    history = await scheduled_audit_loop(iterations=2, interval_sec=0.1)

    assert len(history) == 2
    assert all(h["passed"] is True for h in history)
    for cycle in history:
        assert len(cycle["results"]) == 3  # NIFTY, BANKNIFTY, FINNIFTY
