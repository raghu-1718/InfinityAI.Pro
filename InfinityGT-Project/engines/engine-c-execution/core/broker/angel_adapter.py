"""
Angel One broker adapter (SmartAPI HTTP interface)

Implements an async place_order method compatible with the OrderManager flow,
using the Angel One order placement REST API.

Security: Do NOT hardcode credentials. Provide via Secret Manager or env.
Constructor accepts overrides; otherwise reads from environment variables:
    - ANGEL_API_KEY
    - ANGEL_ACCESS_TOKEN
    - ANGEL_CLIENT_LOCAL_IP
    - ANGEL_CLIENT_PUBLIC_IP
    - ANGEL_MAC_ADDRESS

References:
    Official endpoint (subject to change):
    https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/placeOrder
"""
from __future__ import annotations

import os
from typing import Any, Dict
import aiohttp


class AngelAdapter:
    ORDER_URL = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/placeOrder"

    def __init__(
        self,
        api_key: str | None = None,
        access_token: str | None = None,
        local_ip: str | None = None,
        public_ip: str | None = None,
        mac_address: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("ANGEL_API_KEY", "")
        self.access_token = access_token or os.getenv("ANGEL_ACCESS_TOKEN", "")
        self.local_ip = local_ip or os.getenv("ANGEL_CLIENT_LOCAL_IP", "127.0.0.1")
        self.public_ip = public_ip or os.getenv("ANGEL_CLIENT_PUBLIC_IP", "127.0.0.1")
        self.mac_address = mac_address or os.getenv("ANGEL_MAC_ADDRESS", "00:00:00:00:00:00")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-PrivateKey": self.api_key,
            "X-SourceID": "WEB",
            "X-ClientLocalIP": self.local_ip,
            "X-ClientPublicIP": self.public_ip,
            "X-MACAddress": self.mac_address,
        }

    @staticmethod
    def _map_order_type(order_type: str) -> str:
        ot = (order_type or "").upper()
        if ot == "MARKET":
            return "MARKET"
        if ot == "LIMIT":
            return "LIMIT"
        if ot in ("STOP_LOSS", "SL", "STOPLOSS"):
            return "STOPLOSS"
        return "MARKET"

    @staticmethod
    def _map_txn_type(transaction_type: str) -> str:
        t = (transaction_type or "").upper()
        return "BUY" if t == "BUY" else "SELL"

    async def place_order(
        self,
        *,
        symbol: str,
        quantity: int,
        price: float,
        order_type: str,
        transaction_type: str,
        exchange: str = "NSE",
        product_type: str = "INTRADAY",
        duration: str = "DAY",
        symboltoken: str | None = None,
        variety: str = "NORMAL",
    ) -> Dict[str, Any]:
        """Place an order via Angel One REST API.

        Note: Some accounts require symboltoken. If not provided, the API may reject.
        """
        headers = self._headers()
        payload: Dict[str, Any] = {
            "variety": variety,
            "tradingsymbol": symbol,
            "transactiontype": self._map_txn_type(transaction_type),
            "exchange": exchange,
            "ordertype": self._map_order_type(order_type),
            "producttype": product_type,
            "duration": duration,
            "quantity": int(quantity),
        }
        # Include price only for non-market orders
        if payload["ordertype"] != "MARKET":
            payload["price"] = float(price)
        if symboltoken:
            payload["symboltoken"] = str(symboltoken)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.ORDER_URL, json=payload, headers=headers, timeout=15) as resp:
                    try:
                        data = await resp.json()
                    except Exception:
                        data = {"raw": (await resp.text())[:1000]}

                    if resp.status == 200:
                        # Angel generally returns a data block with orderid
                        order_id = None
                        if isinstance(data, dict):
                            d = data.get("data") or {}
                            order_id = d.get("orderid") or d.get("order_id")
                        return {
                            "success": True,
                            "broker": "angel",
                            "order_id": order_id,
                            "raw": data,
                        }
                    return {
                        "success": False,
                        "broker": "angel",
                        "code": resp.status,
                        "error": data,
                    }
            except Exception as e:
                return {
                    "success": False,
                    "broker": "angel",
                    "error": str(e),
                }
