# backend/services/broker_abstraction.py
"""
Unified Broker Abstraction Layer for InfinityAI.Pro
Abstracts between Dhan (traditional markets) and CoinSwitch (crypto) APIs
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class BrokerError(Exception):
    """Base exception for broker-related errors"""
    pass

class OrderNotFoundError(BrokerError):
    """Raised when an order is not found"""
    pass

class InsufficientFundsError(BrokerError):
    """Raised when there are insufficient funds"""
    pass

class MarketClosedError(BrokerError):
    """Raised when market is closed"""
    pass

class BrokerCredentials:
    """Container for broker credentials"""
    def __init__(self, api_key: str, api_secret: Optional[str] = None,
                 access_token: Optional[str] = None, request_token: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.request_token = request_token

class Order:
    """Unified order representation"""
    def __init__(self, order_id: str, symbol: str, side: str, quantity: float,
                 price: Optional[float] = None, order_type: str = "limit",
                 status: str = "pending", timestamp: Optional[datetime] = None):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side  # 'buy' or 'sell'
        self.quantity = quantity
        self.price = price
        self.order_type = order_type  # 'limit', 'market', etc.
        self.status = status  # 'pending', 'completed', 'cancelled', 'rejected'
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "order_type": self.order_type,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class Position:
    """Unified position representation"""
    def __init__(self, symbol: str, quantity: float, average_price: float,
                 current_price: float, pnl: float, pnl_percentage: float):
        self.symbol = symbol
        self.quantity = quantity
        self.average_price = average_price
        self.current_price = current_price
        self.pnl = pnl
        self.pnl_percentage = pnl_percentage

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "average_price": self.average_price,
            "current_price": self.current_price,
            "pnl": self.pnl,
            "pnl_percentage": self.pnl_percentage
        }

class Quote:
    """Unified market quote representation"""
    def __init__(self, symbol: str, price: float, change: float,
                 change_percent: float, volume: Optional[int] = None,
                 high: Optional[float] = None, low: Optional[float] = None,
                 timestamp: Optional[datetime] = None):
        self.symbol = symbol
        self.price = price
        self.change = change
        self.change_percent = change_percent
        self.volume = volume
        self.high = high
        self.low = low
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "change": self.change,
            "change_percent": self.change_percent,
            "volume": self.volume,
            "high": self.high,
            "low": self.low,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class BrokerAdapter(ABC):
    """Abstract base class for broker adapters"""

    def __init__(self, credentials: BrokerCredentials):
        self.credentials = credentials
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize connection to broker"""
        pass

    @abstractmethod
    async def place_order(self, symbol: str, side: str, quantity: float,
                         price: Optional[float] = None, order_type: str = "limit") -> Order:
        """Place a new order"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        pass

    @abstractmethod
    async def get_orders(self) -> List[Order]:
        """Get all orders"""
        pass

    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get a specific order by ID"""
        pass

    @abstractmethod
    async def get_portfolio(self) -> List[Position]:
        """Get current portfolio positions"""
        pass

    @abstractmethod
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Get market quotes for symbols"""
        pass

    @abstractmethod
    async def get_historical_data(self, symbol: str, interval: str,
                                days: int = 30) -> List[Dict[str, Any]]:
        """Get historical market data"""
        pass

    @abstractmethod
    def get_broker_type(self) -> str:
        """Return broker type identifier"""
        pass

    @abstractmethod
    def supports_asset_type(self, asset_type: str) -> bool:
        """Check if broker supports given asset type"""
        pass

class DhanBrokerAdapter(BrokerAdapter):
    """Dhan broker adapter for traditional Indian markets"""

    def __init__(self, credentials: BrokerCredentials):
        super().__init__(credentials)
        self.base_url = "https://api.dhan.co"
        self.session_token = None

    def get_broker_type(self) -> str:
        return "dhan"

    def supports_asset_type(self, asset_type: str) -> bool:
        return asset_type in ["traditional", "stocks", "equity", "commodity"]

    async def initialize(self) -> bool:
        """Initialize Dhan connection using request token flow"""
        try:
            if not self.credentials.request_token:
                raise BrokerError("Dhan requires request token for initialization")

            # Exchange request token for access token
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v2/token",
                    json={
                        "api_key": self.credentials.api_key,
                        "request_token": self.credentials.request_token
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.session_token = data.get("access_token")
                        return True
                    else:
                        error_data = await response.json()
                        raise BrokerError(f"Dhan auth failed: {error_data}")

        except Exception as e:
            self.logger.error(f"Dhan initialization failed: {e}")
            return False

    async def place_order(self, symbol: str, side: str, quantity: float,
                         price: Optional[float] = None, order_type: str = "limit") -> Order:
        """Place order via Dhan API"""
        if not self.session_token:
            raise BrokerError("Dhan not initialized")

        try:
            order_data = {
                "dhanClientId": self.credentials.api_key,
                "transactionType": "BUY" if side.lower() == "buy" else "SELL",
                "exchangeSegment": "NSE_EQ",  # Default to NSE equity
                "productType": "INTRADAY",
                "orderType": order_type.upper(),
                "validity": "DAY",
                "securityId": symbol,
                "quantity": int(quantity),
                "price": price or 0,
                "triggerPrice": 0
            }

            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.session_token}"}
                async with session.post(
                    f"{self.base_url}/v2/orders",
                    json=order_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return Order(
                            order_id=result["orderId"],
                            symbol=symbol,
                            side=side,
                            quantity=quantity,
                            price=price,
                            order_type=order_type,
                            status="pending"
                        )
                    else:
                        error_data = await response.json()
                        if "insufficient funds" in str(error_data).lower():
                            raise InsufficientFundsError(f"Dhan: {error_data}")
                        raise BrokerError(f"Dhan order failed: {error_data}")

        except aiohttp.ClientError as e:
            raise BrokerError(f"Dhan API error: {e}")

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel Dhan order"""
        if not self.session_token:
            raise BrokerError("Dhan not initialized")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.session_token}"}
                async with session.delete(
                    f"{self.base_url}/v2/orders/{order_id}",
                    headers=headers
                ) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Dhan cancel order failed: {e}")
            return False

    async def get_orders(self) -> List[Order]:
        """Get Dhan orders"""
        if not self.session_token:
            raise BrokerError("Dhan not initialized")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.session_token}"}
                async with session.get(
                    f"{self.base_url}/v2/orders",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        orders_data = await response.json()
                        return [
                            Order(
                                order_id=order["orderId"],
                                symbol=order["securityId"],
                                side=order["transactionType"].lower(),
                                quantity=order["quantity"],
                                price=order.get("price"),
                                status=order["orderStatus"].lower(),
                                timestamp=datetime.fromisoformat(order["orderTimestamp"])
                            )
                            for order in orders_data
                        ]
                    return []
        except Exception as e:
            self.logger.error(f"Dhan get orders failed: {e}")
            return []

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get specific Dhan order"""
        orders = await self.get_orders()
        return next((order for order in orders if order.order_id == order_id), None)

    async def get_portfolio(self) -> List[Position]:
        """Get Dhan portfolio"""
        if not self.session_token:
            raise BrokerError("Dhan not initialized")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.session_token}"}
                async with session.get(
                    f"{self.base_url}/v2/holdings",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        holdings = await response.json()
                        positions = []

                        for holding in holdings:
                            # Get current price (simplified - would need quotes API)
                            current_price = holding.get("lastPrice", holding["avgCostPrice"])
                            pnl = (current_price - holding["avgCostPrice"]) * holding["totalQty"]

                            positions.append(Position(
                                symbol=holding["tradingSymbol"],
                                quantity=holding["totalQty"],
                                average_price=holding["avgCostPrice"],
                                current_price=current_price,
                                pnl=pnl,
                                pnl_percentage=(pnl / (holding["avgCostPrice"] * holding["totalQty"])) * 100
                            ))

                        return positions
                    return []
        except Exception as e:
            self.logger.error(f"Dhan get portfolio failed: {e}")
            return []

    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Get Dhan market quotes"""
        if not self.session_token:
            raise BrokerError("Dhan not initialized")

        quotes = {}
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.session_token}"}

                for symbol in symbols:
                    async with session.get(
                        f"{self.base_url}/v2/marketfeed/{symbol}",
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            quote_data = await response.json()
                            quotes[symbol] = Quote(
                                symbol=symbol,
                                price=quote_data.get("lastPrice", 0),
                                change=quote_data.get("netChange", 0),
                                change_percent=quote_data.get("percentChange", 0),
                                volume=quote_data.get("volume"),
                                high=quote_data.get("ohlc", {}).get("high"),
                                low=quote_data.get("ohlc", {}).get("low")
                            )
        except Exception as e:
            self.logger.error(f"Dhan get quotes failed: {e}")

        return quotes

    async def get_historical_data(self, symbol: str, interval: str,
                                days: int = 30) -> List[Dict[str, Any]]:
        """Get Dhan historical data"""
        if not self.session_token:
            raise BrokerError("Dhan not initialized")

        try:
            # Convert interval to Dhan format
            interval_map = {
                "1m": "1", "5m": "5", "15m": "15", "1h": "60", "1d": "D"
            }
            dhan_interval = interval_map.get(interval, "D")

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.session_token}"}
                async with session.get(
                    f"{self.base_url}/v2/charts/{symbol}",
                    params={
                        "from": start_date.strftime("%Y-%m-%d"),
                        "to": end_date.strftime("%Y-%m-%d"),
                        "interval": dhan_interval
                    },
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [
                            {
                                "timestamp": datetime.fromtimestamp(candle[0]/1000),
                                "open": candle[1],
                                "high": candle[2],
                                "low": candle[3],
                                "close": candle[4],
                                "volume": candle[5]
                            }
                            for candle in data
                        ]
                    return []
        except Exception as e:
            self.logger.error(f"Dhan get historical data failed: {e}")
            return []

class CoinSwitchBrokerAdapter(BrokerAdapter):
    """CoinSwitch broker adapter for cryptocurrency trading"""

    def __init__(self, credentials: BrokerCredentials):
        super().__init__(credentials)
        self.base_url = "https://api-trading.coinswitch.co"
        self.session_initialized = False

    def get_broker_type(self) -> str:
        return "coinswitch"

    def supports_asset_type(self, asset_type: str) -> bool:
        return asset_type in ["crypto", "cryptocurrency", "bitcoin", "ethereum"]

    async def initialize(self) -> bool:
        """Initialize CoinSwitch connection"""
        try:
            if not self.credentials.api_key or not self.credentials.api_secret:
                raise BrokerError("CoinSwitch requires API key and secret")

            # Test connection with ping
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/trade/api/v2/ping") as response:
                    if response.status == 200:
                        self.session_initialized = True
                        return True
                    return False
        except Exception as e:
            self.logger.error(f"CoinSwitch initialization failed: {e}")
            return False

    def _sign_request(self, path: str, params: Dict[str, Any]) -> str:
        """Generate HMAC-SHA256 signature for CoinSwitch"""
        import hmac
        import hashlib

        keys = sorted(params.keys())
        query = "&".join([f"{k}={params[k]}" for k in keys])
        payload = f"{path}?{query}"

        signature = hmac.new(
            self.credentials.api_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make authenticated request to CoinSwitch"""
        if not self.session_initialized:
            raise BrokerError("CoinSwitch not initialized")

        params = params or {}
        params["timestamp"] = int(datetime.now().timestamp() * 1000)

        signature = self._sign_request(path, params)

        headers = {
            "Content-Type": "application/json",
            "X-AUTH-APIKEY": self.credentials.api_key,
            "X-AUTH-SIGNATURE": signature
        }

        url = f"{self.base_url}{path}"

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, params=params, headers=headers) as response:
                    return await response.json()
            elif method == "POST":
                async with session.post(url, json=params, headers=headers) as response:
                    return await response.json()
            elif method == "DELETE":
                async with session.delete(url, json=params, headers=headers) as response:
                    return await response.json()
            else:
                raise BrokerError(f"Unsupported HTTP method: {method}")

    async def place_order(self, symbol: str, side: str, quantity: float,
                         price: Optional[float] = None, order_type: str = "limit") -> Order:
        """Place CoinSwitch order"""
        try:
            order_params = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "type": order_type
            }

            if price and order_type == "limit":
                order_params["price"] = price

            result = await self._request("POST", "/trade/api/v2/order", order_params)

            if result.get("code") == 200:
                return Order(
                    order_id=result["data"]["orderId"],
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price,
                    order_type=order_type,
                    status="pending"
                )
            else:
                error_msg = result.get("msg", "Unknown error")
                if "insufficient" in error_msg.lower():
                    raise InsufficientFundsError(f"CoinSwitch: {error_msg}")
                raise BrokerError(f"CoinSwitch order failed: {error_msg}")

        except Exception as e:
            raise BrokerError(f"CoinSwitch place order failed: {e}")

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel CoinSwitch order"""
        try:
            result = await self._request("DELETE", "/trade/api/v2/order", {"order_id": order_id})
            return result.get("code") == 200
        except Exception as e:
            self.logger.error(f"CoinSwitch cancel order failed: {e}")
            return False

    async def get_orders(self) -> List[Order]:
        """Get CoinSwitch orders"""
        try:
            result = await self._request("GET", "/trade/api/v2/orders", {})

            if result.get("code") == 200:
                return [
                    Order(
                        order_id=order["orderId"],
                        symbol=order["symbol"],
                        side=order["side"],
                        quantity=order["origQty"],
                        price=order.get("price"),
                        status=order["status"].lower(),
                        timestamp=datetime.fromtimestamp(order["time"] / 1000)
                    )
                    for order in result.get("data", [])
                ]
            return []
        except Exception as e:
            self.logger.error(f"CoinSwitch get orders failed: {e}")
            return []

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get specific CoinSwitch order"""
        orders = await self.get_orders()
        return next((order for order in orders if order.order_id == order_id), None)

    async def get_portfolio(self) -> List[Position]:
        """Get CoinSwitch portfolio"""
        try:
            result = await self._request("GET", "/trade/api/v2/user/portfolio", {})

            if result.get("code") == 200:
                positions = []
                for asset in result.get("data", []):
                    if float(asset.get("free", 0)) + float(asset.get("locked", 0)) > 0:
                        # Note: CoinSwitch doesn't provide P&L directly
                        # Would need to calculate from trades or use current prices
                        positions.append(Position(
                            symbol=f"{asset['asset']}INR",  # Assuming INR pairs
                            quantity=float(asset["free"]) + float(asset["locked"]),
                            average_price=0,  # Would need to track this separately
                            current_price=0,  # Would need quotes API
                            pnl=0,
                            pnl_percentage=0
                        ))
                return positions
            return []
        except Exception as e:
            self.logger.error(f"CoinSwitch get portfolio failed: {e}")
            return []

    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Get CoinSwitch market quotes"""
        quotes = {}
        try:
            for symbol in symbols:
                result = await self._request("GET", "/trade/api/v2/24hr/ticker", {"symbol": symbol})

                if result.get("code") == 200:
                    data = result["data"]
                    quotes[symbol] = Quote(
                        symbol=symbol,
                        price=float(data["lastPrice"]),
                        change=float(data["priceChange"]),
                        change_percent=float(data["priceChangePercent"]),
                        volume=int(float(data["volume"])),
                        high=float(data["highPrice"]),
                        low=float(data["lowPrice"])
                    )
        except Exception as e:
            self.logger.error(f"CoinSwitch get quotes failed: {e}")

        return quotes

    async def get_historical_data(self, symbol: str, interval: str,
                                days: int = 30) -> List[Dict[str, Any]]:
        """Get CoinSwitch historical data"""
        try:
            # CoinSwitch uses different interval formats
            interval_map = {
                "1m": "1m", "5m": "5m", "15m": "15m",
                "1h": "1h", "4h": "4h", "1d": "1d"
            }
            cs_interval = interval_map.get(interval, "1d")

            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            result = await self._request("GET", "/trade/api/v2/klines", {
                "symbol": symbol,
                "interval": cs_interval,
                "startTime": start_time,
                "endTime": end_time,
                "limit": 1000
            })

            if result.get("code") == 200:
                return [
                    {
                        "timestamp": datetime.fromtimestamp(candle[0] / 1000),
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                        "volume": float(candle[5])
                    }
                    for candle in result.get("data", [])
                ]
            return []
        except Exception as e:
            self.logger.error(f"CoinSwitch get historical data failed: {e}")
            return []

class UnifiedBrokerManager:
    """Unified broker manager that abstracts between multiple brokers"""

    def __init__(self):
        self.brokers: Dict[str, BrokerAdapter] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def register_broker(self, name: str, broker: BrokerAdapter) -> None:
        """Register a broker adapter"""
        self.brokers[name] = broker
        self.logger.info(f"Registered broker: {name} ({broker.get_broker_type()})")

    def get_broker_for_asset(self, asset_type: str) -> Optional[BrokerAdapter]:
        """Get appropriate broker for asset type"""
        for broker in self.brokers.values():
            if broker.supports_asset_type(asset_type):
                return broker
        return None

    def get_broker(self, name: str) -> Optional[BrokerAdapter]:
        """Get broker by name"""
        return self.brokers.get(name)

    async def initialize_all_brokers(self) -> Dict[str, bool]:
        """Initialize all registered brokers"""
        results = {}
        for name, broker in self.brokers.items():
            try:
                success = await broker.initialize()
                results[name] = success
                status = "initialized" if success else "failed"
                self.logger.info(f"Broker {name} {status}")
            except Exception as e:
                results[name] = False
                self.logger.error(f"Broker {name} initialization error: {e}")
        return results

    async def place_unified_order(self, asset_type: str, symbol: str, side: str,
                                quantity: float, price: Optional[float] = None,
                                order_type: str = "limit") -> Order:
        """Place order using appropriate broker for asset type"""
        broker = self.get_broker_for_asset(asset_type)
        if not broker:
            raise BrokerError(f"No broker supports asset type: {asset_type}")

        return await broker.place_order(symbol, side, quantity, price, order_type)

    async def get_unified_portfolio(self) -> Dict[str, List[Position]]:
        """Get portfolio from all brokers"""
        portfolio = {}
        for name, broker in self.brokers.items():
            try:
                positions = await broker.get_portfolio()
                portfolio[name] = positions
            except Exception as e:
                self.logger.error(f"Failed to get portfolio from {name}: {e}")
                portfolio[name] = []
        return portfolio

    async def get_unified_quotes(self, symbols: List[str], asset_type: str) -> Dict[str, Quote]:
        """Get quotes using appropriate broker"""
        broker = self.get_broker_for_asset(asset_type)
        if not broker:
            return {}

        return await broker.get_quotes(symbols)

# Example usage and integration points
async def demo_broker_abstraction():
    """Demonstrate unified broker abstraction"""

    # Initialize broker manager
    manager = UnifiedBrokerManager()

    # Register Dhan for traditional markets
    dhan_creds = BrokerCredentials(
        api_key="your_dhan_api_key",
        request_token="user_request_token_from_login"
    )
    dhan_broker = DhanBrokerAdapter(dhan_creds)
    manager.register_broker("dhan", dhan_broker)

    # Register CoinSwitch for crypto
    coinswitch_creds = BrokerCredentials(
        api_key="your_coinswitch_api_key",
        api_secret="your_coinswitch_api_secret"
    )
    coinswitch_broker = CoinSwitchBrokerAdapter(coinswitch_creds)
    manager.register_broker("coinswitch", coinswitch_broker)

    # Initialize all brokers
    init_results = await manager.initialize_all_brokers()
    print("Broker initialization results:", init_results)

    # Place unified orders (system automatically chooses correct broker)
    try:
        # Traditional market order (goes to Dhan)
        stock_order = await manager.place_unified_order(
            "traditional", "RELIANCE", "buy", 10, 2500.0
        )
        print(f"Stock order placed: {stock_order.to_dict()}")

        # Crypto order (goes to CoinSwitch)
        crypto_order = await manager.place_unified_order(
            "crypto", "BTCINR", "buy", 0.001, 4500000.0
        )
        print(f"Crypto order placed: {crypto_order.to_dict()}")

    except BrokerError as e:
        print(f"Order placement failed: {e}")

    # Get unified portfolio
    portfolio = await manager.get_unified_portfolio()
    print("Unified portfolio:", {
        broker: [pos.to_dict() for pos in positions]
        for broker, positions in portfolio.items()
    })

    # Get quotes
    stock_quotes = await manager.get_unified_quotes(["RELIANCE", "TCS"], "traditional")
    crypto_quotes = await manager.get_unified_quotes(["BTCINR", "ETHINR"], "crypto")

    print("Stock quotes:", {k: v.to_dict() for k, v in stock_quotes.items()})
    print("Crypto quotes:", {k: v.to_dict() for k, v in crypto_quotes.items()})

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Run demo
    asyncio.run(demo_broker_abstraction())