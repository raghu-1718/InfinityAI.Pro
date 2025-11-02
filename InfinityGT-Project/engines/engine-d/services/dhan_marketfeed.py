"""
Dhan MarketFeed client for Engine D (production)

Implements DhanHQ Python SDK MarketFeed with DhanContext and broadcasts
incoming ticks to Engine D WebSocket channels. No demo mode.

Env vars:
- DHAN_CLIENT_ID: Dhan client id (required)
- DHAN_ACCESS_TOKEN: Dhan access token/JWT (required)
- DHAN_FEED: Comma-separated instrument specs: EXCHANGE:SECURITY_ID:MODE
    - EXCHANGE: NSE | NSE_FNO | BSE | BSE_FNO | MCX
    - MODE: TICKER | QUOTE | FULL
    Example: "NSE:1333:TICKER,NSE:11915:FULL"
- DHAN_FEED_VERSION: Defaults to "v2"
- DHAN_FEED_CHANNEL: Which WS channel to broadcast to (default: "signals")
"""
from __future__ import annotations

import os
import asyncio
from typing import Callable, List, Dict, Any, Optional, Tuple

from dhanhq import DhanContext, MarketFeed


class MarketFeedClient:
    def __init__(
        self,
        broadcast_fn: Callable[[Dict[str, Any], str], asyncio.Future],
        *,
        url: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        channel: str = "signals",
    ) -> None:
        self.channel = os.getenv("DHAN_FEED_CHANNEL", channel)
        self.broadcast_fn = broadcast_fn
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._mf: Optional[MarketFeed] = None
        self._ctx: Optional[DhanContext] = None
        self._instruments: List[Tuple[int, str, int]] = self._parse_feed_env()

    def start(self) -> None:
        if self._running:
            return
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._run())
        self._running = True

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except Exception:
                pass
        self._running = False

    async def _run(self) -> None:
        client_id = os.getenv("DHAN_CLIENT_ID", "").strip()
        access_token = os.getenv("DHAN_ACCESS_TOKEN", "").strip()
        if not client_id or not access_token:
            raise RuntimeError("DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN are required for MarketFeed")

        version = os.getenv("DHAN_FEED_VERSION", "v2")
        self._ctx = DhanContext(client_id, access_token)
        self._mf = MarketFeed(self._ctx, self._instruments, version)

        # Run the SDK loop in executor to avoid blocking
        loop = asyncio.get_event_loop()
        backoff = 1
        while True:
            try:
                await loop.run_in_executor(None, self._mf.run_forever)  # type: ignore[arg-type]
                # Drain data if available
                data = self._mf.get_data() if hasattr(self._mf, "get_data") else None
                if data is not None:
                    await self._handle_tick(data)
                backoff = 1
            except asyncio.CancelledError:
                # Disconnect on cancel
                try:
                    if self._mf:
                        self._mf.disconnect()
                except Exception:
                    pass
                break
            except Exception:
                await asyncio.sleep(min(backoff, 30))
                backoff *= 2

    async def _handle_tick(self, data: Dict[str, Any]) -> None:
        event = {
            "type": "tick",
            "data": data,
        }
        try:
            await self.broadcast_fn(event, self.channel)
        except Exception:
            pass

    def _parse_feed_env(self) -> List[Tuple[int, str, int]]:
        raw = os.getenv("DHAN_FEED", "").strip()
        if not raw:
            raise RuntimeError("DHAN_FEED is required. Format: EXCHANGE:SECURITY_ID:MODE e.g. NSE:1333:TICKER")
        mapping_ex = {
            "NSE": MarketFeed.NSE,
            "NSE_FNO": MarketFeed.NSE_FNO,
            "BSE": MarketFeed.BSE,
            "BSE_FNO": MarketFeed.BSE_FNO,
            "MCX": MarketFeed.MCX,
        }
        mapping_mode = {
            "TICKER": MarketFeed.Ticker,
            "QUOTE": MarketFeed.Quote,
            "FULL": MarketFeed.Full,
        }
        result: List[Tuple[int, str, int]] = []
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        for p in parts:
            try:
                ex, secid, mode = p.split(":")
                ex_val = mapping_ex[ex.upper()]
                mode_val = mapping_mode[mode.upper()]
                result.append((ex_val, secid, mode_val))
            except Exception:
                raise RuntimeError(f"Invalid DHAN_FEED item: '{p}'")
        return result


class MarketFeedService:
    """Thin wrapper to manage lifecycle from FastAPI lifespan."""

    def __init__(self) -> None:
        self._client: Optional[MarketFeedClient] = None

    def start(self, broadcaster: Any) -> None:  # Any to avoid import cycle
        async def _broadcast(event: Dict[str, Any], channel: str) -> None:
            # broadcaster has broadcast_custom_event(event_type, data, channel)
            try:
                await broadcaster.broadcast_custom_event(event.get("type", "tick"), event.get("data", {}), channel)
            except Exception:
                pass

        self._client = MarketFeedClient(broadcast_fn=_broadcast)
        self._client.start()

    async def stop(self) -> None:
        if self._client:
            await self._client.stop()
            self._client = None


# Singleton service
marketfeed_service = MarketFeedService()
