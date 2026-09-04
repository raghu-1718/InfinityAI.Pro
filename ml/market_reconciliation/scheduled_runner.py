"""
Scheduled Market Data Reconciliation Runner
Automates periodic drift checks between primary and secondary feeds.
"""
import asyncio
import logging
from typing import List, Dict, Any

from market_reconciliation.reconciler import MarketDataReconciler, ReconciliationResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reconciliation_runner")


async def run_reconciliation_batch(
    symbols: List[str] = None,
    threshold_pct: float = 0.75
) -> List[ReconciliationResult]:
    """
    Execute a single reconciliation sweep across specified instruments.
    """
    symbols = symbols or ["NIFTY", "BANKNIFTY", "FINNIFTY"]
    reconciler = MarketDataReconciler()
    results = []

    for sym in symbols:
        res = await reconciler.reconcile_symbol(sym, threshold_pct=threshold_pct)
        if res.status == "PASS":
            logger.info(f"[{res.status}] {sym}: Primary={res.primary_price}, Secondary={res.secondary_price}, Diff={res.discrepancy_pct:.3f}%")
        else:
            logger.warning(f"[{res.status}] {sym}: Diff={res.discrepancy_pct:.3f}% > {threshold_pct}%! Details: {res.details}")
        results.append(res)

    return results


async def scheduled_audit_loop(iterations: int = 3, interval_sec: float = 0.5) -> List[Dict[str, Any]]:
    """Run multiple audit cycles simulating scheduled cron behavior."""
    history = []
    for i in range(iterations):
        logger.info(f"Starting audit cycle {i + 1}/{iterations}...")
        batch = await run_reconciliation_batch()
        history.append({
            "cycle": i + 1,
            "results": [r.model_dump() for r in batch],
            "passed": all(r.status == "PASS" for r in batch)
        })
        if i < iterations - 1:
            await asyncio.sleep(interval_sec)
    return history


if __name__ == "__main__":
    records = asyncio.run(scheduled_audit_loop(iterations=2, interval_sec=0.2))
    print("Reconciliation Audit Summary:", records)
