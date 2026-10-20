"""
InfinityAI.Pro — Institutional Market Data Sanity & Freshness Validator
========================================================================
Engine A | Layer: Market Data Ingestion & Guardrails
Enforces:
  1. Strict Index Spot Sanity Bounds (rejects corrupted / swapped SecurityID feeds)
  2. Stale Market Data Veto (rejects ticks older than 30 seconds)
  3. Official DhanHQ v2 Scrip Master Index Mapping (SecID, Lot Size, Strike Step)
"""

import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger("InfinityAI.MarketDataValidator")

class IndexInstrumentSpec(dict):
    def __init__(self, security_id: str, exchange_segment: str, lot_size: int, strike_step: int):
        super().__init__({
            "security_id": security_id,
            "exchange_segment": exchange_segment,
            "lot_size": lot_size,
            "strike_step": strike_step,
        })
        self.security_id = security_id
        self.exchange_segment = exchange_segment
        self.lot_size = lot_size
        self.strike_step = strike_step

    def __getitem__(self, key):
        if isinstance(key, int):
            return [self.security_id, self.exchange_segment, self.lot_size, self.strike_step][key]
        return super().__getitem__(key)


# Official DhanHQ v2 Scrip Master Index Specifications
INDEX_INSTRUMENT_SPEC: Dict[str, IndexInstrumentSpec] = {
    "NIFTY": IndexInstrumentSpec("13", "IDX_I", 65, 50),
    "BANKNIFTY": IndexInstrumentSpec("25", "IDX_I", 30, 100),
    "FINNIFTY": IndexInstrumentSpec("27", "IDX_I", 60, 50),
    "MIDCPNIFTY": IndexInstrumentSpec("442", "IDX_I", 120, 25),
    "SENSEX": IndexInstrumentSpec("51", "IDX_I", 20, 100),
    "INDIAVIX": IndexInstrumentSpec("21", "IDX_I", 1, 1),
}


def get_dhan_security_id(symbol: str) -> str:
    """Returns official DhanHQ Security ID for target index instrument"""
    sym_u = symbol.upper()
    spec = INDEX_INSTRUMENT_SPEC.get(sym_u)
    return spec["security_id"] if spec else "0"

# Institutional Spot Sanity Bounds:
# Immediate rejection if price falls outside normal macroeconomic valuation boundaries
INDEX_SPOT_BOUNDS: Dict[str, Tuple[float, float]] = {
    "NIFTY": (15000.0, 35000.0),
    "BANKNIFTY": (35000.0, 75000.0),
    "FINNIFTY": (18000.0, 35000.0),
    "MIDCPNIFTY": (8000.0, 22000.0),
    "SENSEX": (60000.0, 100000.0),
    "INDIAVIX": (5.0, 60.0),
}

MAX_STALE_TICK_AGE_SECONDS = 30.0


class StaleMarketDataError(ValueError):
    """Raised when market quote data is stale (> 30s old) or corrupted/out-of-bounds."""
    pass


def validate_index_spot(symbol: str, spot: float, age_seconds: Optional[float] = None, max_age_seconds: float = MAX_STALE_TICK_AGE_SECONDS) -> bool:
    """
    Validates whether a spot price is physically plausible for the target index
    and not stale (> 30 seconds).
    """
    if spot is None or spot <= 0:
        return False

    sym_u = symbol.upper()
    bounds = INDEX_SPOT_BOUNDS.get(sym_u)
    if bounds:
        min_p, max_p = bounds
        if not (min_p <= spot <= max_p):
            logger.error(
                f"🚨 Corrupted/Swapped Spot Rejected: {sym_u} spot {spot:.2f} "
                f"violates sanity bounds [{min_p:.0f}, {max_p:.0f}]"
            )
            return False

    if age_seconds is not None and age_seconds > max_age_seconds:
        logger.warning(
            f"🚨 Stale Tick Rejected: {sym_u} tick age {age_seconds:.1f}s exceeds "
            f"max permissible freshness limit of {max_age_seconds:.0f}s"
        )
        raise StaleMarketDataError(
            f"STALE MARKET DATA: {sym_u} tick age {age_seconds:.1f}s exceeds {max_age_seconds:.0f}s limit"
        )

    return True


def validate_or_raise(symbol: str, spot: float, age_seconds: Optional[float] = None, max_age_seconds: float = MAX_STALE_TICK_AGE_SECONDS) -> float:
    """
    Validates index spot and raises structured StaleMarketDataError upon failure.
    """
    sym_u = symbol.upper()
    bounds = INDEX_SPOT_BOUNDS.get(sym_u)
    if bounds:
        min_p, max_p = bounds
        if not (min_p <= spot <= max_p):
            raise StaleMarketDataError(
                f"OUT OF SANITY BOUNDS: {sym_u} spot {spot:.2f} outside valid interval [{min_p:.0f}, {max_p:.0f}]"
            )

    if age_seconds is not None and age_seconds > max_age_seconds:
        raise StaleMarketDataError(
            f"STALE MARKET DATA: {sym_u} tick age {age_seconds:.1f}s exceeds limit {max_age_seconds:.0f}s"
        )

    if not validate_index_spot(sym_u, spot, age_seconds, max_age_seconds):
        raise StaleMarketDataError(f"Invalid market data for {sym_u}: spot={spot}")

    return spot


def get_strike_step(symbol: str) -> int:
    """Returns official strike step increment (e.g. 25 for MIDCPNIFTY, 100 for BANKNIFTY)"""
    sym_u = symbol.upper()
    spec = INDEX_INSTRUMENT_SPEC.get(sym_u)
    if spec:
        return spec[3]
    if "MIDCP" in sym_u:
        return 25
    if "BANKNIFTY" in sym_u or "SENSEX" in sym_u:
        return 100
    return 50


def calculate_atm_strike(symbol: str, spot: float) -> int:
    """Calculates valid ATM strike adhering strictly to official scrip master strike step"""
    sym_u = symbol.upper()
    validate_or_raise(sym_u, spot)
    step = get_strike_step(sym_u)
    return int(round(spot / step) * step)
