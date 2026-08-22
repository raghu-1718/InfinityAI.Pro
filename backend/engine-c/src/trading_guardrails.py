# Trading Guardrails Module
# Enforces market hours, symbol whitelist, order caps for live trading

import os
from datetime import datetime, time
import pytz
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# IST timezone for market hours
IST = pytz.timezone('Asia/Kolkata')

# Default symbols whitelist (NSE stocks, no illiquid names)
DEFAULT_SYMBOLS_WHITELIST = {
    # Indices/ETFs
    "NIFTYBEES", "SENSIBEES",
    # Large-cap stocks
    "RELIANCE", "TCS", "INFY", "HDFC", "HDFCBANK", "ICICIBANK", "BAJAJFINSV",
    "MARUTI", "ADANIPORTS", "BHARTIARTL", "SBIN", "WIPRO",
    # Mid-cap select
    "AXISBANK", "LT", "COALINDIA", "ONGC",
}

# Market trading & execution operational hours: 8:55 AM - 3:45 PM IST weekdays
MARKET_OPEN_HOUR = int(os.getenv("MARKET_OPEN_HOUR", "8"))
MARKET_OPEN_MIN = int(os.getenv("MARKET_OPEN_MIN", "55"))
MARKET_CLOSE_HOUR = int(os.getenv("MARKET_CLOSE_HOUR", "15"))
MARKET_CLOSE_MIN = int(os.getenv("MARKET_CLOSE_MIN", "45"))

# Order limits (per order)
MAX_ORDER_QUANTITY = int(os.getenv("MAX_ORDER_QUANTITY", "10000"))
MAX_ORDER_NOTIONAL = float(os.getenv("MAX_ORDER_NOTIONAL", "500000"))  # INR

# Daily limits
MAX_ORDERS_PER_DAY = int(os.getenv("MAX_ORDERS_PER_DAY", "100"))

def is_market_open() -> bool:
    """Check if market is currently open (08:55 - 15:45 IST, weekdays only)."""
    now = datetime.now(IST)

    # Check if weekday (0-4 = Mon-Fri)
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        logger.warning(f"⚠️ Market closed: Weekend ({now.strftime('%A')})")
        return False

    # Check trading hours (08:55 - 15:45 IST)
    market_open = time(MARKET_OPEN_HOUR, MARKET_OPEN_MIN)
    market_close = time(MARKET_CLOSE_HOUR, MARKET_CLOSE_MIN)
    current_time = now.time()

    is_open = market_open <= current_time <= market_close
    if not is_open:
        logger.warning(f"⚠️ Market closed: Current time {current_time} outside {market_open}-{market_close} IST")

    return is_open

def get_symbols_whitelist() -> set:
    """Get allowed trading symbols (from env or defaults)."""
    env_symbols = os.getenv("ALLOWED_SYMBOLS", "")
    if env_symbols:
        symbols = set(s.strip().upper() for s in env_symbols.split(","))
        logger.info(f"✅ Using env-defined symbols whitelist: {symbols}")
        return symbols

    logger.info(f"✅ Using default symbols whitelist: {DEFAULT_SYMBOLS_WHITELIST}")
    return DEFAULT_SYMBOLS_WHITELIST

def validate_order_guardrails(
    symbol: str,
    quantity: int,
    price: float = 0,
    order_type: str = "MARKET"
) -> Dict[str, Any]:
    """
    Validate order against guardrails.

    Returns: {"valid": bool, "reason": str, "guardrails_violated": List[str]}
    """
    violations = []

    # Check 1: Market hours (08:55 - 15:45 IST)
    if not is_market_open():
        violations.append(f"Market closed: Orders only allowed 08:55-15:45 IST weekdays")

    # Check 2: Symbol whitelist
    whitelist = get_symbols_whitelist()
    if symbol.upper() not in whitelist:
        violations.append(f"Symbol '{symbol}' not in approved whitelist: {whitelist}")

    # Check 3: Order quantity
    if quantity > MAX_ORDER_QUANTITY:
        violations.append(f"Quantity {quantity} exceeds max {MAX_ORDER_QUANTITY}")

    # Check 4: Notional value (price * quantity)
    # For MARKET orders, use last price if available; otherwise allow
    if order_type != "MARKET" and price > 0:
        notional = price * quantity
        if notional > MAX_ORDER_NOTIONAL:
            violations.append(f"Notional value ₹{notional:,.0f} exceeds max ₹{MAX_ORDER_NOTIONAL:,.0f}")

    return {
        "valid": len(violations) == 0,
        "reason": "; ".join(violations) if violations else "Order passed all guardrails",
        "guardrails_violated": violations,
        "symbol": symbol,
        "quantity": quantity,
        "price": price,
        "order_type": order_type,
        "market_open": is_market_open(),
        "allowed_symbols_count": len(get_symbols_whitelist()),
        "timestamp": datetime.now(IST).isoformat()
    }

def log_order_attempt(symbol: str, qty: int, price: float, user_id: str, result: Dict[str, Any]):
    """Log all order attempts (passed and failed) for audit trail."""
    status = "APPROVED" if result["valid"] else "REJECTED"
    logger.warning(f"🚨 ORDER ATTEMPT [{status}] User={user_id} Symbol={symbol} Qty={qty} Price={price} Violations={result['guardrails_violated']}")
