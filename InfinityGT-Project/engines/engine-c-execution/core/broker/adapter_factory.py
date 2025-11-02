"""
Broker adapter factory for Engine C.

Provides a unified interface to obtain a broker-specific adapter.
Currently supports:
- dhan: uses Engine C's native execution_service logic (handled in main.py)
- angel: thin HTTP adapter stub using Angel One public API contract (placeholder)

Note: For Dhan, Engine C already implements rich execution via execution_service.
This factory is mainly for future extensibility and to wire alternative brokers
without rewriting Engine C internals.
"""
from __future__ import annotations

from typing import Optional

try:
    from .angel_adapter import AngelAdapter
except Exception:
    AngelAdapter = None  # type: ignore

try:
    from .dhan_adapter import DhanAdapter
except Exception:
    DhanAdapter = None  # type: ignore


def get_adapter(broker: str):
    """Return an adapter instance for the given broker key.

    Supported values:
    - "dhan": handled natively in Engine C (returns None; call execution_service)
    - "angel": returns AngelAdapter instance if available
    """
    b = (broker or "").strip().lower()
    if b == "dhan":
        return None  # Backward-compat: Engine C handles Dhan natively in legacy path
    if b == "angel":
        if AngelAdapter is None:
            raise RuntimeError("Angel adapter not available")
        return AngelAdapter()
    raise ValueError(f"Unsupported broker: {broker}")


def get_broker_adapter(broker: str, **context):
    """Return a concrete adapter instance for broker routing.

    Args:
        broker: Broker key, e.g. "dhan" or "angel".
        **context: Extra params for adapter construction (e.g., client_id, access_token).

    Returns:
        Adapter instance implementing broker-specific calls.

    Raises:
        ValueError: if broker unsupported or required context missing.
    """
    b = (broker or "").strip().lower()
    if b == "dhan":
        if DhanAdapter is None:
            raise ValueError("Dhan adapter unavailable")
        client_id = context.get("client_id")
        token = context.get("access_token")
        if not client_id or not token:
            raise ValueError("Missing client_id/access_token for Dhan adapter")
        return DhanAdapter(client_id=client_id, access_token=token)
    if b == "angel":
        if AngelAdapter is None:
            raise ValueError("Angel adapter unavailable")
        return AngelAdapter(
            api_key=context.get("api_key"),
            access_token=context.get("access_token"),
            local_ip=context.get("local_ip"),
            public_ip=context.get("public_ip"),
            mac_address=context.get("mac_address"),
        )
    raise ValueError(f"Unsupported broker: {broker}")
