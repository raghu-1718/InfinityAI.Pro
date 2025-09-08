

# Production-ready, SDK-based, context-aware Dhan broker adapter
import asyncio
from dhanhq import dhanhq, DhanContext  # type: ignore
import logging

logger = logging.getLogger(__name__)


from typing import Any, Callable, Dict, List, Optional

class DhanAdapter:
    context: 'DhanContext'  # type: ignore

    def __init__(self, client_id: str, access_token: str) -> None:
        self.context = DhanContext(client_id, access_token)  # type: ignore
        self.dhan = dhanhq(self.context)  # type: ignore

    def get_auth_headers(self) -> Dict[str, str]:
        return {
            "access-token":  ,
            "X-Client-Id": self.context.client_id,
        }

    def get_profile(self) -> Optional[Any]:
        try:
            resp = self.dhan.profile()
            return resp
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            return None

    def execute_trade(self, strategy: Dict[str, Any], creds: Dict[str, str]) -> Dict[str, Any]:
        if strategy["action"] == "HOLD":
            return {"status": "skipped", "reason": "HOLD action"}

        payload = {
            "transaction_type": strategy["action"],
            "exchange": "NSE",
            "symbol": strategy["symbol"],
            "quantity": strategy.get("quantity", 1),
            "product_type": "INTRADAY",
            "price": 0.0,
            "validity": "DAY",
            "order_type": "MARKET",
            "source": "API"
        }
        try:
            resp = self.dhan.place_order(payload)
            logger.info(f"Order placed: {resp}")
            return {
                "status": "success",
                "order_details": resp,
            }
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

    async def get_quote_async(self, symbol: str) -> Optional[Any]:
        loop = asyncio.get_event_loop()
        try:
            resp = await loop.run_in_executor(None, self.dhan.quote, {"exchange": "NSE", "symbol": symbol})
            return resp
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None

    async def subscribe_market_feed(self, symbols: List[str], callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to Dhan market feed for given symbols and process each tick with callback.
        Requires Data API subscription. Uses dhanhq SDK's MarketFeed (if available) or raw websocket.
        """
        import websockets
        import json
        ws_url = "wss://api.dhan.co/marketfeed"  # Confirm with Dhan docs if endpoint changes
        headers = {
            "access-token": self.context.access_token,
            "X-Client-Id": self.context.client_id,
        }
        subscribe_msg = {
            "action": "subscribe",
            "symbols": symbols,
            "feedType": "marketdata"
        }
        async with websockets.connect(ws_url, extra_headers=headers) as ws:
            await ws.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to market feed for {symbols}")
            while True:
                try:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    callback(data)
                except Exception as e:
                    logger.error(f"Market feed error: {e}")
                    break
