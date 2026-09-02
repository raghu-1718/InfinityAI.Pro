"""
Middleware and Guardrail dependencies for InfinityAI.Pro
"""
import uuid
import os
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from backend.shared.structured_logging import set_trace_context, clear_trace_context

IST_TZ = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = dtime(9, 15)
MARKET_CLOSE = dtime(15, 30)


def is_market_open_ist() -> bool:
    """
    Check if Indian Capital Markets (NSE/BSE) are currently open in IST.
    Regular trading session: Monday-Friday 09:15 - 15:30 IST.
    """
    now_ist = datetime.now(IST_TZ)
    # Monday is 0, Sunday is 6
    if now_ist.weekday() >= 5:
        return False
    current_time = now_ist.time()
    return MARKET_OPEN <= current_time <= MARKET_CLOSE


def check_market_hours_guardrail(request: Request) -> None:
    """
    Hardcode HTTP 403 blocks for any live execution attempt outside 09:15-15:30 IST.
    Allows simulated paper trades in dev/test environments.
    """
    trading_mode = (
        request.headers.get("x-trading-mode")
        or os.getenv("TRADING_MODE", "paper")
    ).lower()

    # Check for test override header
    force_closed = request.headers.get("x-force-market-closed", "").lower() == "true"

    if trading_mode == "live":
        if force_closed or not is_market_open_ist():
            raise HTTPException(
                status_code=403,
                detail="Market closed. Live trade execution is strictly blocked outside 09:15–15:30 IST."
            )


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Idempotency and correlation tracking middleware.
    Injects/propagates x-correlation-id (max 30 chars) into logging context and response.
    """

    async def dispatch(self, request: Request, call_next):
        corr_id = request.headers.get("x-correlation-id")
        if not corr_id:
            corr_id = f"corr-{uuid.uuid4().hex[:12]}"
        elif len(corr_id) > 30:
            return Response(
                content='{"detail": "Correlation-Id header must not exceed 30 characters"}',
                status_code=400,
                media_type="application/json"
            )

        set_trace_context(trace_id=corr_id, request_id=corr_id, service_name="infinityai-backend")

        response = await call_next(request)
        response.headers["x-correlation-id"] = corr_id
        clear_trace_context()
        return response
