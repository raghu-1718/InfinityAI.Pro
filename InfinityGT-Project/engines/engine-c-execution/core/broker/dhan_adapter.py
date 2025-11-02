"""
Dhan broker adapter for Engine C (Execution).

Encapsulates all HTTP calls to Dhan v2 API required for order placement
and portfolio retrieval. Does not manage OAuth flow or secret storage; the
caller passes the current client_id and access_token (rotated via Secret Manager).

Security: Never hardcode credentials. Always inject via runtime env or vault.
"""
from __future__ import annotations

import aiohttp
from typing import Any, Dict, Optional


class DhanAdapter:
    BASE_URL = "https://api.dhan.co/v2"

    def __init__(self, client_id: str, access_token: str) -> None:
        self.client_id = client_id
        self.access_token = access_token

    def set_token(self, token: str) -> None:
        self.access_token = token

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "access-token": self.access_token,
            "client-id": self.client_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def place_order(self,
                          symbol: str,
                          quantity: int,
                          price: float,
                          order_type: str,
                          transaction_type: str,
                          security_id: str = "2885",
                          exchange_segment: str = "NSE_EQ",
                          product_type: str = "INTRADAY",
                          validity: str = "DAY") -> Dict[str, Any]:
        payload = {
            "dhanClientId": self.client_id,
            "transactionType": transaction_type.upper(),
            "exchangeSegment": exchange_segment,
            "productType": product_type,
            "orderType": order_type.upper(),
            "validity": validity,
            "tradingSymbol": symbol,
            "securityId": security_id,
            "quantity": str(quantity),
            "disclosedQuantity": "0",
            "price": str(price if order_type.upper() != "MARKET" else 0),
            "afterMarketOrderFlag": "false",
        }
        url = f"{self.BASE_URL}/orders"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                data: Any
                try:
                    data = await response.json()
                except Exception:
                    data = {"raw": (await response.text())[:1000]}
                if response.status == 200 and isinstance(data, dict) and data.get("status") == "success":
                    return {
                        "success": True,
                        "order_id": (data.get("data", {}) or {}).get("orderId"),
                        "message": "Order executed successfully",
                        "broker": "dhan",
                        "raw": data,
                    }
                return {
                    "success": False,
                    "error": (data.get("message") if isinstance(data, dict) else "Unknown error"),
                    "details": data,
                    "code": response.status,
                    "broker": "dhan",
                }

    async def get_positions(self) -> Any:
        url = f"{self.BASE_URL}/positions"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                try:
                    return await resp.json()
                except Exception:
                    return []

    async def get_holdings(self) -> Any:
        url = f"{self.BASE_URL}/holdings"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                try:
                    return await resp.json()
                except Exception:
                    return []

    async def get_fundlimit(self) -> Any:
        # fundlimit endpoint sometimes appears at non /v2 path as well; prefer v2
        url = "https://api.dhan.co/fundlimit"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                try:
                    return await resp.json()
                except Exception:
                    return {"error": f"status={resp.status}"}
