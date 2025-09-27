# services/broker_coinswitch.py
"""
CoinSwitch PRO API Broker Adapter for Crypto Trading
Production-ready adapter for InfinityAI.Pro crypto trading
"""

import asyncio
import logging
import time
import hmac
import hashlib
import requests
from typing import Any, Callable, Dict, List, Optional, Union
from utils.config import CONFIG

logger = logging.getLogger(__name__)


class CoinSwitchAdapter:
    """
    CoinSwitch PRO API v2 Broker Adapter for Crypto Trading
    Supports BTC, ETH, and other cryptocurrencies on CoinSwitch PRO
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://api-trading.coinswitch.co"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip(" /")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-AUTH-APIKEY": self.api_key
        })

    def _sign(self, path: str, params: Dict[str, Any]) -> str:
        """
        Create HMAC-SHA256 signature for CoinSwitch PRO API v2
        """
        # Sort params by key
        sorted_items = sorted(params.items())
        encoded = "&".join(f"{k}={v}" for k, v in sorted_items)
        payload = f"{path}?{encoded}"

        # Create signature
        signature = hmac.new(
            self.api_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _request(self, method: str, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make authenticated request to CoinSwitch PRO API
        """
        params = params or {}
        params["timestamp"] = int(time.time() * 1000)

        signature = self._sign(path, params)

        headers = self.session.headers.copy()
        headers["X-AUTH-SIGNATURE"] = signature

        url = f"{self.base_url}{path}"

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=params, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, json=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"CoinSwitch API request failed: {e}")
            return {"status": "error", "message": str(e)}

    # Public Market Data Methods

    def ping(self) -> Dict[str, Any]:
        """Test API connectivity"""
        return self._request("GET", "/trade/api/v2/ping")

    def get_24h_ticker_all(self) -> Dict[str, Any]:
        """Get 24hr ticker data for all trading pairs"""
        return self._request("GET", "/trade/api/v2/24hr/all-pairs/ticker")

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get 24hr ticker data for specific symbol"""
        return self._request("GET", "/trade/api/v2/24hr/ticker", {"symbol": symbol})

    def get_depth(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        """Get order book depth for symbol"""
        return self._request("GET", "/trade/api/v2/depth", {"symbol": symbol, "limit": limit})

    # Private Trading Methods

    def validate_keys(self) -> Dict[str, Any]:
        """Validate API key and secret"""
        return self._request("GET", "/trade/api/v2/validate/keys")

    def create_order(self, symbol: str, side: str, quantity: float,
                    price: Optional[float] = None, order_type: str = "limit") -> Dict[str, Any]:
        """
        Create a new order

        Args:
            symbol: Trading pair (e.g., "BTCINR", "ETHINR")
            side: "buy" or "sell"
            quantity: Amount to trade
            price: Limit price (required for limit orders)
            order_type: "limit" or "market"
        """
        payload = {
            "symbol": symbol,
            "side": side.lower(),
            "quantity": quantity,
            "type": order_type.lower()
        }

        if price is not None:
            payload["price"] = price

        return self._request("POST", "/trade/api/v2/order", payload)

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order"""
        return self._request("DELETE", "/trade/api/v2/order", {"order_id": order_id})

    def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get all open orders, optionally filtered by symbol"""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/trade/api/v2/orders", params)

    def get_portfolio(self) -> Dict[str, Any]:
        """Get user portfolio/balances"""
        return self._request("GET", "/trade/api/v2/user/portfolio")

    # InfinityAI.Pro Integration Methods

    def get_profile(self) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
        try:
            portfolio = self.get_portfolio()
            if portfolio.get("status") == "success":
                return portfolio
            return None
        except Exception as e:
            logger.error(f"Error fetching CoinSwitch profile: {e}")
            return None

    def get_fund_limits(self) -> Optional[Dict[str, Any]]:
        """Get account balance/limits"""
        try:
            portfolio = self.get_portfolio()
            if portfolio.get("status") == "success":
                return portfolio
            return None
        except Exception as e:
            logger.error(f"Error fetching CoinSwitch fund limits: {e}")
            return None

    async def get_quote_async(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Async method to get real-time quote for InfinityAI.Pro"""
        try:
            # Convert symbol format if needed (e.g., "BTCINR" -> "BTCINR")
            ticker = self.get_ticker(symbol)
            if ticker.get("status") == "success":
                data = ticker.get("data", {})
                return {
                    "symbol": symbol,
                    "last_price": float(data.get("lastPrice", 0)),
                    "bid_price": float(data.get("bidPrice", 0)),
                    "ask_price": float(data.get("askPrice", 0)),
                    "volume": float(data.get("volume", 0)),
                    "high_24h": float(data.get("highPrice", 0)),
                    "low_24h": float(data.get("lowPrice", 0)),
                    "price_change_24h": float(data.get("priceChange", 0)),
                    "price_change_percent_24h": float(data.get("priceChangePercent", 0)),
                    "timestamp": int(time.time() * 1000)
                }
            return None
        except Exception as e:
            logger.error(f"Error getting CoinSwitch quote for {symbol}: {e}")
            return None

    def execute_trade(self, strategy: Dict[str, Any], creds: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute trade for InfinityAI.Pro trading system
        Compatible with existing DhanAdapter interface
        """
        try:
            if strategy["action"] == "HOLD":
                return {"status": "skipped", "reason": "HOLD action"}

            # Map action to CoinSwitch side
            side = "buy" if strategy["action"] == "BUY" else "sell"

            # Get symbol and quantity
            symbol = strategy["symbol"]
            quantity = strategy.get("quantity", 1)

            # For crypto, we need to handle different symbol formats
            # Convert from internal format to CoinSwitch format
            if symbol.endswith("_CRYPTO"):
                symbol = symbol.replace("_CRYPTO", "")

            # Ensure symbol is in CoinSwitch format (e.g., "BTCINR", "ETHINR")
            if not symbol.endswith("INR"):
                symbol = f"{symbol}INR"

            # Determine order type and price
            order_type = "market"  # Default to market orders for crypto
            price = None

            # For limit orders, we might want to calculate a price
            if "price" in strategy:
                order_type = "limit"
                price = strategy["price"]

            # Execute the order
            result = self.create_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_type=order_type
            )

            if result.get("status") == "success":
                return {
                    "status": "success",
                    "order_details": {
                        "orderId": result.get("data", {}).get("orderId", f"coinswitch_{int(time.time())}"),
                        "status": "PLACED",
                        "symbol": symbol,
                        "quantity": quantity,
                        "transactionType": side.upper(),
                        "orderType": order_type.upper()
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("message", "Unknown error"),
                    "details": result
                }

        except Exception as e:
            logger.error(f"CoinSwitch trade execution error: {e}")
            return {
                "status": "error",
                "message": f"Trade execution failed: {str(e)}"
            }

    async def get_instruments_async(self) -> List[Dict[str, Any]]:
        """Get available trading instruments"""
        try:
            ticker_data = self.get_24h_ticker_all()
            if ticker_data.get("status") == "success":
                instruments = []
                for item in ticker_data.get("data", []):
                    instruments.append({
                        "symbol": item.get("symbol", ""),
                        "baseAsset": item.get("baseAsset", ""),
                        "quoteAsset": item.get("quoteAsset", ""),
                        "lastPrice": float(item.get("lastPrice", 0)),
                        "volume": float(item.get("volume", 0)),
                        "priceChangePercent": float(item.get("priceChangePercent", 0))
                    })
                return instruments
            return []
        except Exception as e:
            logger.error(f"Error fetching CoinSwitch instruments: {e}")
            return []

    def close(self):
        """Close the adapter and cleanup resources"""
        if self.session:
            self.session.close()