import aiohttp
import os

class DhanProvider:
    def __init__(self):
        self.base_url = "https://api.dhan.co"
        self.access_token = os.getenv("DHAN_ACCESS_TOKEN", "")
        self.client_id = os.getenv("DHAN_CLIENT_ID", "")
        self.headers = {
            "access-token": self.access_token,
            "client-id": self.client_id,
            "Content-Type": "application/json"
        }

    async def get_positions(self):
        url = f"{self.base_url}/positions"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                return await resp.json()

    async def get_orders(self):
        url = f"{self.base_url}/orders"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                return await resp.json()

    async def get_option_chain(self, symbol: str):
        url = f"{self.base_url}/optionchain"
        payload = {"symbol": symbol}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as resp:
                return await resp.json()

    async def handle_callback(self, code: str):
        # Implement OAuth/token exchange logic here
        return {"status": "callback_received", "code": code}

    async def get_fundlimit(self):
        """Fetch account funds/limits (demat funds snapshot)."""
        url = f"{self.base_url}/fundlimit"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                return await resp.json()

    async def get_holdings(self):
        """Fetch current holdings (may return error when none)."""
        url = f"{self.base_url}/holdings"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                try:
                    return await resp.json()
                except Exception:
                    return []

    async def get_profile(self):
        """Best-effort user profile (if supported)."""
        # Some profiles are under v2 path; ignore failure gracefully
        url = f"{self.base_url}/v2/user/profile"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
            except Exception:
                pass
        return {"client_id": self.client_id}

    async def get_statement(self):
        """Return a lightweight trading statement. Fallback: map recent orders as statements."""
        try:
            orders = await self.get_orders()
            if isinstance(orders, list):
                # Normalize to simple statement rows
                rows = []
                for o in orders[:50]:  # limit
                    rows.append({
                        "orderId": o.get("orderId") or o.get("id"),
                        "symbol": o.get("tradingSymbol") or o.get("symbol"),
                        "side": o.get("transactionType") or o.get("side"),
                        "qty": o.get("quantity") or o.get("qty"),
                        "price": o.get("price") or o.get("avgPrice") or 0,
                        "status": o.get("orderStatus") or o.get("status"),
                        "time": o.get("orderTime") or o.get("timestamp")
                    })
                return {"source": "orders", "rows": rows}
        except Exception:
            pass
        return {"source": "none", "rows": []}
