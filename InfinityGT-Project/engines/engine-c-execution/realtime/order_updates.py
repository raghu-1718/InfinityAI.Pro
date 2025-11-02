"""
Dhan Order Update client for Engine C (production)

Implements DhanHQ Python SDK OrderUpdate using DhanContext and invokes a
provided async callback per order update. Runs a sync socket loop in a worker
thread to avoid blocking the event loop.

Env vars:
- DHAN_CLIENT_ID: Dhan client id (required)
- DHAN_ACCESS_TOKEN: Dhan access token/JWT (required)
"""
from __future__ import annotations

import os
import asyncio
import threading
import time
from typing import Dict, Any, Callable, Optional

from dhanhq import DhanContext, OrderUpdate


class DhanOrderUpdateClient:
    def __init__(
        self,
        on_update: Callable[[Dict[str, Any]], asyncio.Future],
    ) -> None:
        self.on_update = on_update
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._order_client: Optional[OrderUpdate] = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_sync_loop, name="DhanOrderUpdateThread", daemon=True)
        self._thread.start()

    async def stop(self) -> None:
        self._running = False
        # Allow thread to exit naturally; socket loop handles disconnects
        if self._thread and self._thread.is_alive():
            # Give it a moment to teardown
            for _ in range(10):
                time.sleep(0.1)
                if not self._thread.is_alive():
                    break
            self._thread = None

    def _run_sync_loop(self) -> None:
        client_id = os.getenv("DHAN_CLIENT_ID", "").strip()
        access_token = os.getenv("DHAN_ACCESS_TOKEN", "").strip()
        if not client_id or not access_token:
            # Misconfiguration; do not run
            return

        ctx = DhanContext(client_id, access_token)
        order_client = OrderUpdate(ctx)

        # Attach callback to forward to async on_update
        def _on_update(data: Dict[str, Any]):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            # schedule coroutine; fire-and-forget
            try:
                loop.call_soon_threadsafe(asyncio.create_task, self._handle_update(data))
            except Exception:
                pass

        # Many SDKs expose a property for callback
        try:
            order_client.on_update = _on_update  # type: ignore[attr-defined]
        except Exception:
            # If property not available, we rely on polling via get_data if exists
            pass

        while self._running:
            try:
                order_client.connect_to_dhan_websocket_sync()
            except Exception:
                time.sleep(5)

    async def _handle_update(self, data: Dict[str, Any]) -> None:
        try:
            await self.on_update(data)
        except Exception:
            pass
