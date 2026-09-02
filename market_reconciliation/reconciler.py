"""
Market Data Reconciliation Engine
Compares primary broker ticks against independent secondary quotes to detect feed anomalies.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from market_reconciliation.primary_feed import PrimaryMarketFeed
from market_reconciliation.secondary_feed import SecondaryMarketFeed


class ReconciliationResult(BaseModel):
    symbol: str
    primary_price: float
    secondary_price: float
    discrepancy_pct: float
    threshold_pct: float
    status: str  # "PASS" or "FLAGGED"
    timestamp: str
    details: str


class MarketDataReconciler:
    """
    Automated dual-source market data reconciler.
    Flags any divergence exceeding tolerance threshold (default: 0.75%).
    """

    def __init__(
        self,
        primary_feed: Optional[PrimaryMarketFeed] = None,
        secondary_feed: Optional[SecondaryMarketFeed] = None
    ):
        self.primary_feed = primary_feed or PrimaryMarketFeed()
        self.secondary_feed = secondary_feed or SecondaryMarketFeed()

    async def reconcile_symbol(self, symbol: str, threshold_pct: float = 0.75) -> ReconciliationResult:
        """Fetch quotes from both feeds and reconcile divergence."""
        p_quote = await self.primary_feed.get_latest_quote(symbol)
        s_quote = await self.secondary_feed.get_latest_quote(symbol)

        return self.compute_discrepancy(
            primary_price=p_quote["last_price"],
            secondary_price=s_quote["last_price"],
            symbol=symbol,
            threshold_pct=threshold_pct
        )

    def compute_discrepancy(
        self,
        primary_price: float,
        secondary_price: float,
        symbol: str,
        threshold_pct: float = 0.75
    ) -> ReconciliationResult:
        """
        Compute divergence between two quote prices and check against tolerance threshold.
        """
        if secondary_price <= 0:
            raise ValueError("Secondary price must be positive.")

        discrepancy_pct = round((abs(primary_price - secondary_price) / secondary_price) * 100.0, 4)
        is_flagged = discrepancy_pct > threshold_pct

        status = "FLAGGED" if is_flagged else "PASS"
        if is_flagged:
            details = (
                f"ALERT: Price discrepancy {discrepancy_pct:.3f}% exceeds tolerance threshold of {threshold_pct}%. "
                f"Primary: {primary_price}, Secondary: {secondary_price}"
            )
        else:
            details = f"Reconciliation successful. Divergence is {discrepancy_pct:.3f}% (within {threshold_pct}%)."

        return ReconciliationResult(
            symbol=symbol.upper(),
            primary_price=primary_price,
            secondary_price=secondary_price,
            discrepancy_pct=discrepancy_pct,
            threshold_pct=threshold_pct,
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            details=details
        )
