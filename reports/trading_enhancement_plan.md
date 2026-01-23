# Trading Capabilities Enhancement Plan

**InfinityAI.Pro Advanced Features Roadmap**
**Version:** 2.0
**Date:** 2026-01-22
**Project:** galvanic-pulsar-482815-h0

---

## Executive Summary

This document outlines the technical roadmap for advancing InfinityAI.Pro from basic LIVE trading to a comprehensive institutional-grade trading platform. The plan spans Q2-Q4 2026 and focuses on four strategic pillars:

1. **Multi-Broker Support** (Q2) - Zerodha Kite, Upstox API integration
2. **Advanced Order Types** (Q2) - Iceberg, OCO, bracket, trailing stop
3. **Options Strategies** (Q3) - Iron condor, spreads, Greeks calculator
4. **Enhanced Risk Analytics** (Q3) - Portfolio Greeks, VaR stress testing

**Business Impact:** These enhancements address 75% of competitor gaps and enable TAM expansion from 250K to 600K users (₹600 Cr → ₹1,440 Cr SAM).

---

## Q2 2026: Multi-Broker Support

### Strategic Rationale

**Problem:** DhanHQ has ~5% broker market share. Zerodha (50%), Upstox (15%) collectively represent 65% of Indian retail traders.

**Opportunity:** Multi-broker support expands addressable market from 125K DhanHQ users to 1.6M+ Zerodha/Upstox users.

**Revenue Impact:** ₹6 Cr → ₹38 Cr SAM expansion (6x increase)

---

### Technical Architecture

#### 1. Broker Abstraction Layer

**Create `IBrokerAdapter` interface:**

```python
# backend/shared/brokers/broker_adapter.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"
    BRACKET = "BRACKET"
    COVER = "COVER"
    AMO = "AMO"  # After Market Order

class OrderStatus(Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class BrokerType(Enum):
    DHAN_HQ = "dhan_hq"
    ZERODHA = "zerodha"
    UPSTOX = "upstox"
    ANGEL_ONE = "angel_one"  # Future
    FYERS = "fyers"  # Future

class IBrokerAdapter(ABC):
    """
    Unified interface for all broker integrations.

    All adapters MUST implement these methods with standardized
    return types to ensure Engine-C can execute trades across
    any broker without code changes.
    """

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with broker API.

        Args:
            credentials: Dict with broker-specific auth keys
                - DhanHQ: {"client_id": str, "access_token": str}
                - Zerodha: {"api_key": str, "access_token": str}
                - Upstox: {"access_token": str}

        Returns:
            bool: True if authentication successful
        """
        pass

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        quantity: int,
        order_type: OrderType,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        product: str = "MIS",  # MIS/CNC/NRML
        validity: str = "DAY",  # DAY/IOC
        **kwargs
    ) -> Dict[str, Any]:
        """
        Place order with broker.

        Returns:
            {
                "order_id": str,
                "status": OrderStatus,
                "message": str,
                "timestamp": datetime
            }
        """
        pass

    @abstractmethod
    async def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Modify existing order"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel existing order"""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get real-time order status"""
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.

        Returns:
            List of positions:
            [{
                "symbol": str,
                "quantity": int,
                "avg_price": float,
                "current_price": float,
                "pnl": float,
                "pnl_percent": float
            }]
        """
        pass

    @abstractmethod
    async def get_holdings(self) -> List[Dict[str, Any]]:
        """Get long-term holdings (delivery positions)"""
        pass

    @abstractmethod
    async def get_funds(self) -> Dict[str, float]:
        """
        Get account funds.

        Returns:
            {
                "available_cash": float,
                "used_margin": float,
                "available_margin": float,
                "opening_balance": float
            }
        """
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote.

        Returns:
            {
                "symbol": str,
                "ltp": float,
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": int,
                "timestamp": datetime
            }
        """
        pass

    @abstractmethod
    async def subscribe_websocket(
        self,
        symbols: List[str],
        callback: callable
    ) -> None:
        """
        Subscribe to real-time WebSocket feed.

        Args:
            symbols: List of symbols to subscribe
            callback: Function called on each tick
                signature: async def callback(tick: Dict[str, Any])
        """
        pass

    @abstractmethod
    async def unsubscribe_websocket(self, symbols: List[str]) -> None:
        """Unsubscribe from WebSocket feed"""
        pass
```

---

#### 2. DhanHQ Adapter (Refactor Existing)

```python
# backend/shared/brokers/dhan_adapter.py

from dhanhq import dhanhq
from .broker_adapter import IBrokerAdapter, OrderType, OrderStatus

class DhanAdapter(IBrokerAdapter):
    def __init__(self):
        self.client: Optional[dhanhq] = None

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        try:
            self.client = dhanhq(
                client_id=credentials["client_id"],
                access_token=credentials["access_token"]
            )
            # Test connection
            funds = self.client.get_fund_limits()
            return funds is not None
        except Exception as e:
            logger.error(f"DhanHQ auth failed: {e}")
            return False

    async def place_order(
        self,
        symbol: str,
        quantity: int,
        order_type: OrderType,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        product: str = "MIS",
        validity: str = "DAY",
        **kwargs
    ) -> Dict[str, Any]:
        # Map OrderType to DhanHQ constants
        dhan_order_type = self._map_order_type(order_type)

        try:
            response = self.client.place_order(
                security_id=symbol,
                exchange_segment="NSE_EQ",
                transaction_type="BUY" if quantity > 0 else "SELL",
                quantity=abs(quantity),
                order_type=dhan_order_type,
                price=price or 0,
                trigger_price=trigger_price or 0,
                product_type=product,
                validity=validity
            )

            return {
                "order_id": response["orderId"],
                "status": self._map_status(response["orderStatus"]),
                "message": response.get("remarks", "Order placed"),
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"DhanHQ order failed: {e}")
            return {
                "order_id": None,
                "status": OrderStatus.REJECTED,
                "message": str(e),
                "timestamp": datetime.now()
            }

    async def get_positions(self) -> List[Dict[str, Any]]:
        positions = self.client.get_positions()
        return [
            {
                "symbol": pos["tradingSymbol"],
                "quantity": pos["netQty"],
                "avg_price": pos["avgPrice"],
                "current_price": pos["ltp"],
                "pnl": pos["realizedProfit"] + pos["unrealizedProfit"],
                "pnl_percent": (
                    (pos["ltp"] - pos["avgPrice"]) / pos["avgPrice"] * 100
                    if pos["avgPrice"] > 0 else 0
                )
            }
            for pos in positions if pos["netQty"] != 0
        ]

    # ... implement remaining methods
```

---

#### 3. Zerodha Kite Adapter

```python
# backend/shared/brokers/zerodha_adapter.py

from kiteconnect import KiteConnect
from .broker_adapter import IBrokerAdapter, OrderType, OrderStatus

class ZerodhaAdapter(IBrokerAdapter):
    """
    Zerodha Kite Connect API Adapter.

    Docs: https://kite.trade/docs/connect/v3/
    Cost: FREE (no API charges)
    Rate Limits: 3 req/s (trading), 10 req/s (market data)
    """

    def __init__(self):
        self.kite: Optional[KiteConnect] = None

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        try:
            api_key = credentials["api_key"]
            access_token = credentials["access_token"]

            self.kite = KiteConnect(api_key=api_key)
            self.kite.set_access_token(access_token)

            # Verify by fetching profile
            profile = self.kite.profile()
            logger.info(f"Zerodha authenticated: {profile['user_name']}")
            return True
        except Exception as e:
            logger.error(f"Zerodha auth failed: {e}")
            return False

    async def place_order(
        self,
        symbol: str,
        quantity: int,
        order_type: OrderType,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        product: str = "MIS",
        validity: str = "DAY",
        **kwargs
    ) -> Dict[str, Any]:
        # Map to Kite constants
        kite_order_type = self._map_order_type(order_type)
        transaction_type = self.kite.TRANSACTION_TYPE_BUY if quantity > 0 else self.kite.TRANSACTION_TYPE_SELL

        try:
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=symbol,
                transaction_type=transaction_type,
                quantity=abs(quantity),
                order_type=kite_order_type,
                price=price,
                trigger_price=trigger_price,
                product=product,
                validity=validity
            )

            return {
                "order_id": order_id,
                "status": OrderStatus.PENDING,
                "message": "Order placed successfully",
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"Zerodha order failed: {e}")
            return {
                "order_id": None,
                "status": OrderStatus.REJECTED,
                "message": str(e),
                "timestamp": datetime.now()
            }

    async def subscribe_websocket(
        self,
        symbols: List[str],
        callback: callable
    ) -> None:
        """
        Zerodha WebSocket for real-time ticks.

        Note: Requires KiteTicker (separate package)
        """
        from kiteconnect import KiteTicker

        kws = KiteTicker(self.kite.api_key, self.kite.access_token)

        def on_ticks(ws, ticks):
            # Convert Zerodha tick format to standard format
            for tick in ticks:
                standardized_tick = {
                    "symbol": tick["tradingsymbol"],
                    "ltp": tick["last_price"],
                    "volume": tick["volume_traded"],
                    "timestamp": tick["timestamp"]
                }
                asyncio.create_task(callback(standardized_tick))

        kws.on_ticks = on_ticks
        kws.connect(threaded=True)

        # Subscribe to instrument tokens
        instrument_tokens = [
            self.kite.ltp(f"NSE:{sym}")["instrument_token"]
            for sym in symbols
        ]
        kws.subscribe(instrument_tokens)
        kws.set_mode(kws.MODE_FULL, instrument_tokens)

    # ... implement remaining methods
```

---

#### 4. Upstox Adapter

```python
# backend/shared/brokers/upstox_adapter.py

import upstox_client
from .broker_adapter import IBrokerAdapter, OrderType, OrderStatus

class UpstoxAdapter(IBrokerAdapter):
    """
    Upstox API v2 Adapter.

    Docs: https://upstox.com/developer/api-documentation/
    Cost: FREE (no API charges)
    Rate Limits: 25 req/s (trading), 25 req/s (market data)
    """

    def __init__(self):
        self.client: Optional[upstox_client.ApiClient] = None
        self.order_api: Optional[upstox_client.OrderApi] = None

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        try:
            configuration = upstox_client.Configuration()
            configuration.access_token = credentials["access_token"]

            self.client = upstox_client.ApiClient(configuration)
            self.order_api = upstox_client.OrderApi(self.client)

            # Verify by fetching profile
            user_api = upstox_client.UserApi(self.client)
            profile = user_api.get_profile()
            logger.info(f"Upstox authenticated: {profile.data.user_name}")
            return True
        except Exception as e:
            logger.error(f"Upstox auth failed: {e}")
            return False

    async def place_order(
        self,
        symbol: str,
        quantity: int,
        order_type: OrderType,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        product: str = "MIS",
        validity: str = "DAY",
        **kwargs
    ) -> Dict[str, Any]:
        # Map to Upstox constants
        upstox_order_type = self._map_order_type(order_type)
        transaction_type = "BUY" if quantity > 0 else "SELL"

        try:
            body = upstox_client.PlaceOrderRequest(
                quantity=abs(quantity),
                product=product,
                validity=validity,
                price=price or 0,
                tag="InfinityAI",
                instrument_token=f"NSE_EQ|{symbol}",
                order_type=upstox_order_type,
                transaction_type=transaction_type,
                disclosed_quantity=0,
                trigger_price=trigger_price or 0,
                is_amo=False
            )

            response = self.order_api.place_order(body)

            return {
                "order_id": response.data.order_id,
                "status": OrderStatus.PENDING,
                "message": "Order placed successfully",
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"Upstox order failed: {e}")
            return {
                "order_id": None,
                "status": OrderStatus.REJECTED,
                "message": str(e),
                "timestamp": datetime.now()
            }

    # ... implement remaining methods
```

---

### Integration with Engine-C

**Update `backend/engine-c/src/main.py`:**

```python
from backend.shared.brokers import BrokerFactory, BrokerType

# Store user's preferred broker in Firestore
# /users/{uid}/settings/broker_config
# {
#   "broker": "zerodha",  # dhan_hq, zerodha, upstox
#   "credentials": {...}  # Encrypted credentials
# }

@app.post("/api/v1/orders/place")
async def place_order(
    order: OrderRequest,
    user_id: str = Depends(get_current_user)
):
    # Get user's broker preference
    user_doc = firestore_client.collection("users").document(user_id).get()
    broker_type = user_doc.get("broker_config.broker", "dhan_hq")
    credentials = user_doc.get("broker_config.credentials")

    # Get broker adapter
    broker = await BrokerFactory.create_broker(
        broker_type=BrokerType(broker_type),
        credentials=credentials
    )

    # Place order
    result = await broker.place_order(
        symbol=order.symbol,
        quantity=order.quantity,
        order_type=order.order_type,
        price=order.price,
        trigger_price=order.trigger_price,
        product=order.product,
        validity=order.validity
    )

    # Log to Firestore
    await log_order(user_id, result)

    return result
```

---

### Broker Factory

```python
# backend/shared/brokers/factory.py

from typing import Dict
from .broker_adapter import IBrokerAdapter, BrokerType
from .dhan_adapter import DhanAdapter
from .zerodha_adapter import ZerodhaAdapter
from .upstox_adapter import UpstoxAdapter

class BrokerFactory:
    _adapters: Dict[BrokerType, type] = {
        BrokerType.DHAN_HQ: DhanAdapter,
        BrokerType.ZERODHA: ZerodhaAdapter,
        BrokerType.UPSTOX: UpstoxAdapter,
    }

    @classmethod
    async def create_broker(
        cls,
        broker_type: BrokerType,
        credentials: Dict[str, str]
    ) -> IBrokerAdapter:
        adapter_class = cls._adapters.get(broker_type)
        if not adapter_class:
            raise ValueError(f"Unsupported broker: {broker_type}")

        broker = adapter_class()
        authenticated = await broker.authenticate(credentials)

        if not authenticated:
            raise RuntimeError(f"Failed to authenticate with {broker_type}")

        return broker
```

---

### UI Changes

**1. Broker Selection (Settings Page):**

```typescript
// frontend/src/components/BrokerSettings.tsx

const BrokerSettings = () => {
  const [selectedBroker, setSelectedBroker] = useState("dhan_hq");
  const [credentials, setCredentials] = useState({});

  const brokerOptions = [
    {
      id: "dhan_hq",
      name: "DhanHQ",
      logo: "/brokers/dhan.png",
      features: ["Zero Brokerage", "NSE/BSE/MCX"],
      marketShare: "5%"
    },
    {
      id: "zerodha",
      name: "Zerodha",
      logo: "/brokers/zerodha.png",
      features: ["₹20/order", "NSE/BSE/MCX/NFO"],
      marketShare: "50%"
    },
    {
      id: "upstox",
      name: "Upstox",
      logo: "/brokers/upstox.png",
      features: ["₹20/order", "NSE/BSE/MCX/NFO"],
      marketShare: "15%"
    }
  ];

  return (
    <div className="grid grid-cols-3 gap-4">
      {brokerOptions.map(broker => (
        <BrokerCard
          key={broker.id}
          {...broker}
          selected={selectedBroker === broker.id}
          onClick={() => handleBrokerSelect(broker.id)}
        />
      ))}
    </div>
  );
};
```

**2. Credential Input Forms:**

Each broker requires different credentials:

- **DhanHQ:** Client ID + Access Token
- **Zerodha:** API Key + Access Token (via OAuth)
- **Upstox:** Access Token (via OAuth)

**3. OAuth Flow (Zerodha/Upstox):**

```python
# backend/engine-c/src/routes/oauth.py

@app.get("/api/v1/oauth/zerodha/authorize")
async def zerodha_authorize(user_id: str):
    """Redirect user to Zerodha login"""
    api_key = os.getenv("ZERODHA_API_KEY")
    redirect_url = f"https://api.infinityai.pro/oauth/zerodha/callback"

    kite_login_url = (
        f"https://kite.zerodha.com/connect/login"
        f"?api_key={api_key}"
        f"&v=3"
        f"&redirect_url={redirect_url}"
    )

    return RedirectResponse(kite_login_url)

@app.get("/api/v1/oauth/zerodha/callback")
async def zerodha_callback(request_token: str, user_id: str):
    """Handle Zerodha callback, exchange request_token for access_token"""
    kite = KiteConnect(api_key=os.getenv("ZERODHA_API_KEY"))

    session = kite.generate_session(
        request_token=request_token,
        api_secret=os.getenv("ZERODHA_API_SECRET")
    )

    access_token = session["access_token"]

    # Store encrypted credentials in Firestore
    await store_broker_credentials(
        user_id=user_id,
        broker="zerodha",
        credentials={
            "api_key": os.getenv("ZERODHA_API_KEY"),
            "access_token": access_token
        }
    )

    return RedirectResponse("https://infinityai.pro/dashboard?broker_connected=true")
```

---

### Testing & Validation

**1. Sandbox Testing:**

- DhanHQ: Demo account (500K virtual capital)
- Zerodha: Kite Connect sandbox (historical data, no real orders)
- Upstox: Sandbox environment

**2. Adapter Unit Tests:**

```python
# backend/tests/brokers/test_zerodha_adapter.py

import pytest
from backend.shared.brokers import ZerodhaAdapter, OrderType

@pytest.mark.asyncio
async def test_zerodha_place_order():
    adapter = ZerodhaAdapter()
    await adapter.authenticate({
        "api_key": "test_api_key",
        "access_token": "test_access_token"
    })

    result = await adapter.place_order(
        symbol="RELIANCE",
        quantity=1,
        order_type=OrderType.MARKET,
        product="MIS"
    )

    assert result["status"] == OrderStatus.PENDING
    assert result["order_id"] is not None
```

**3. Integration Tests:**

Test complete order flow with each broker in sandbox mode.

---

### Deployment Plan

**Week 1-2:**

- ✅ Create `IBrokerAdapter` interface
- ✅ Refactor DhanHQ to use adapter pattern
- ✅ Implement `BrokerFactory`

**Week 3-4:**

- ✅ Implement Zerodha adapter
- ✅ Implement Upstox adapter
- ✅ Unit tests (90% coverage)

**Week 5-6:**

- ✅ OAuth flows (Zerodha, Upstox)
- ✅ UI broker selection
- ✅ Integration tests (sandbox)

**Week 7-8:**

- ✅ Beta testing (10 users)
- ✅ Production rollout (gradual, 100 users/week)

---

## Q2 2026: Advanced Order Types

### Strategic Rationale

**Problem:** Current platform only supports MARKET and LIMIT orders. Traders need advanced order types for risk management:

- **Iceberg orders:** Hide large order size (reduce slippage)
- **OCO (One-Cancels-Other):** Manage risk with paired orders
- **Bracket orders:** Automate entry + SL + target
- **Trailing stop loss:** Lock in profits as price moves favorably

**Opportunity:** These features are standard in AlgoTest (competitor) but missing in Zerodha Streak.

---

### Technical Implementation

#### 1. Iceberg Orders

**Concept:** Split large order into smaller "visible" chunks to prevent market impact.

**Example:** Sell 10,000 shares of RELIANCE in 100-share chunks (100 orders).

**Implementation:**

```python
# backend/shared/orders/iceberg_order.py

class IcebergOrder:
    """
    Iceberg order: Execute large quantity in small visible chunks.

    Example:
        total_qty = 10000
        visible_qty = 100
        => Place 100 orders of 100 shares each
    """

    def __init__(
        self,
        broker: IBrokerAdapter,
        symbol: str,
        total_quantity: int,
        visible_quantity: int,
        order_type: OrderType = OrderType.LIMIT,
        price: Optional[float] = None,
        delay_seconds: float = 2.0
    ):
        self.broker = broker
        self.symbol = symbol
        self.total_quantity = total_quantity
        self.visible_quantity = visible_quantity
        self.order_type = order_type
        self.price = price
        self.delay_seconds = delay_seconds

        self.executed_quantity = 0
        self.orders: List[str] = []  # Order IDs

    async def execute(self) -> Dict[str, Any]:
        """
        Execute iceberg order in chunks.

        Returns:
            {
                "status": "COMPLETED" | "PARTIAL" | "FAILED",
                "executed_quantity": int,
                "total_quantity": int,
                "orders": List[str],  # Order IDs
                "avg_price": float
            }
        """
        remaining = self.total_quantity

        while remaining > 0:
            # Determine chunk size
            chunk_qty = min(remaining, self.visible_quantity)

            # Place order
            result = await self.broker.place_order(
                symbol=self.symbol,
                quantity=chunk_qty,
                order_type=self.order_type,
                price=self.price
            )

            if result["status"] == OrderStatus.REJECTED:
                logger.error(f"Iceberg order chunk failed: {result['message']}")
                break

            self.orders.append(result["order_id"])

            # Wait for execution
            await self._wait_for_execution(result["order_id"])

            # Update executed quantity
            order_status = await self.broker.get_order_status(result["order_id"])
            self.executed_quantity += order_status["filled_quantity"]
            remaining -= chunk_qty

            # Delay before next chunk
            await asyncio.sleep(self.delay_seconds)

        # Calculate average price
        avg_price = await self._calculate_avg_price()

        return {
            "status": "COMPLETED" if self.executed_quantity == self.total_quantity else "PARTIAL",
            "executed_quantity": self.executed_quantity,
            "total_quantity": self.total_quantity,
            "orders": self.orders,
            "avg_price": avg_price
        }

    async def _wait_for_execution(self, order_id: str, timeout: int = 60):
        """Wait for order to be executed or timeout"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = await self.broker.get_order_status(order_id)

            if status["status"] in [OrderStatus.COMPLETE, OrderStatus.REJECTED]:
                return

            await asyncio.sleep(1)

    async def _calculate_avg_price(self) -> float:
        """Calculate weighted average price across all chunks"""
        total_value = 0
        total_qty = 0

        for order_id in self.orders:
            order = await self.broker.get_order_status(order_id)
            total_value += order["filled_quantity"] * order["avg_price"]
            total_qty += order["filled_quantity"]

        return total_value / total_qty if total_qty > 0 else 0
```

---

#### 2. OCO (One-Cancels-Other) Orders

**Concept:** Place two orders simultaneously; when one executes, cancel the other.

**Use Case:**

- Long position in RELIANCE at ₹2,500
- Place OCO: (1) Take profit at ₹2,600, (2) Stop loss at ₹2,450
- If price hits ₹2,600, sell and cancel stop loss
- If price hits ₹2,450, sell and cancel take profit

**Implementation:**

```python
# backend/shared/orders/oco_order.py

class OCOOrder:
    """
    One-Cancels-Other: Two orders where execution of one cancels the other.

    Typical use: Take profit + Stop loss
    """

    def __init__(
        self,
        broker: IBrokerAdapter,
        symbol: str,
        quantity: int,
        order_1: Dict[str, Any],  # {"type": "LIMIT", "price": 2600}
        order_2: Dict[str, Any],  # {"type": "STOP_LOSS", "trigger": 2450}
    ):
        self.broker = broker
        self.symbol = symbol
        self.quantity = quantity
        self.order_1 = order_1
        self.order_2 = order_2

        self.order_1_id: Optional[str] = None
        self.order_2_id: Optional[str] = None
        self.executed_order_id: Optional[str] = None

    async def execute(self) -> Dict[str, Any]:
        """
        Place both orders and monitor. Cancel the other when one executes.
        """
        # Place Order 1 (e.g., take profit)
        result_1 = await self.broker.place_order(
            symbol=self.symbol,
            quantity=self.quantity,
            order_type=OrderType(self.order_1["type"]),
            price=self.order_1.get("price")
        )
        self.order_1_id = result_1["order_id"]

        # Place Order 2 (e.g., stop loss)
        result_2 = await self.broker.place_order(
            symbol=self.symbol,
            quantity=self.quantity,
            order_type=OrderType(self.order_2["type"]),
            trigger_price=self.order_2.get("trigger"),
            price=self.order_2.get("price")
        )
        self.order_2_id = result_2["order_id"]

        # Monitor both orders
        await self._monitor_orders()

        return {
            "executed_order_id": self.executed_order_id,
            "cancelled_order_id": self.order_2_id if self.executed_order_id == self.order_1_id else self.order_1_id,
            "status": "COMPLETED"
        }

    async def _monitor_orders(self):
        """Monitor both orders; cancel other when one executes"""
        while True:
            # Check Order 1
            status_1 = await self.broker.get_order_status(self.order_1_id)
            if status_1["status"] == OrderStatus.COMPLETE:
                # Cancel Order 2
                await self.broker.cancel_order(self.order_2_id)
                self.executed_order_id = self.order_1_id
                return

            # Check Order 2
            status_2 = await self.broker.get_order_status(self.order_2_id)
            if status_2["status"] == OrderStatus.COMPLETE:
                # Cancel Order 1
                await self.broker.cancel_order(self.order_1_id)
                self.executed_order_id = self.order_2_id
                return

            await asyncio.sleep(1)
```

---

#### 3. Bracket Orders

**Concept:** Automate entry + stop loss + target in a single order.

**Example:**

- Buy RELIANCE at ₹2,500
- Stop loss: ₹2,450 (exit if price drops 2%)
- Target: ₹2,600 (exit if price rises 4%)

**Implementation:**

```python
# backend/shared/orders/bracket_order.py

class BracketOrder:
    """
    Bracket order: Entry + Stop Loss + Target in one order.

    Automatically places SL and target orders after entry is filled.
    """

    def __init__(
        self,
        broker: IBrokerAdapter,
        symbol: str,
        quantity: int,
        entry_price: float,
        stop_loss: float,
        target: float,
        order_type: OrderType = OrderType.LIMIT
    ):
        self.broker = broker
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.target = target
        self.order_type = order_type

        self.entry_order_id: Optional[str] = None
        self.sl_order_id: Optional[str] = None
        self.target_order_id: Optional[str] = None

    async def execute(self) -> Dict[str, Any]:
        """
        Place entry order. Once filled, place SL and target orders (OCO).
        """
        # 1. Place entry order
        entry_result = await self.broker.place_order(
            symbol=self.symbol,
            quantity=self.quantity,
            order_type=self.order_type,
            price=self.entry_price
        )
        self.entry_order_id = entry_result["order_id"]

        # 2. Wait for entry to fill
        await self._wait_for_entry()

        # 3. Place SL and Target as OCO
        oco = OCOOrder(
            broker=self.broker,
            symbol=self.symbol,
            quantity=-self.quantity,  # Exit position (reverse direction)
            order_1={"type": "LIMIT", "price": self.target},
            order_2={"type": "STOP_LOSS", "trigger": self.stop_loss}
        )

        oco_result = await oco.execute()

        return {
            "entry_order_id": self.entry_order_id,
            "exit_order_id": oco_result["executed_order_id"],
            "status": "COMPLETED"
        }

    async def _wait_for_entry(self):
        """Wait for entry order to be filled"""
        while True:
            status = await self.broker.get_order_status(self.entry_order_id)
            if status["status"] == OrderStatus.COMPLETE:
                return
            await asyncio.sleep(1)
```

---

#### 4. Trailing Stop Loss

**Concept:** Dynamically adjust stop loss as price moves in favorable direction.

**Example:**

- Buy RELIANCE at ₹2,500
- Trailing SL: 2% below highest price
- Price rises to ₹2,600 → SL adjusts to ₹2,548 (2% below ₹2,600)
- Price rises to ₹2,700 → SL adjusts to ₹2,646 (2% below ₹2,700)
- Price drops to ₹2,646 → Exit triggered

**Implementation:**

```python
# backend/shared/orders/trailing_stop_loss.py

class TrailingStopLoss:
    """
    Trailing stop loss: Adjust SL dynamically as price moves favorably.

    Monitors real-time price and updates stop loss order.
    """

    def __init__(
        self,
        broker: IBrokerAdapter,
        symbol: str,
        quantity: int,
        entry_price: float,
        trail_percent: float = 2.0,  # 2% trailing stop
        check_interval: float = 5.0  # Check every 5 seconds
    ):
        self.broker = broker
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.trail_percent = trail_percent
        self.check_interval = check_interval

        self.highest_price = entry_price
        self.current_sl = entry_price * (1 - trail_percent / 100)
        self.sl_order_id: Optional[str] = None

    async def execute(self) -> Dict[str, Any]:
        """
        Monitor price and update trailing SL.
        """
        # 1. Place initial SL order
        sl_result = await self.broker.place_order(
            symbol=self.symbol,
            quantity=-self.quantity,  # Exit
            order_type=OrderType.STOP_LOSS,
            trigger_price=self.current_sl
        )
        self.sl_order_id = sl_result["order_id"]

        # 2. Monitor price and update SL
        while True:
            # Get current price
            quote = await self.broker.get_quote(self.symbol)
            current_price = quote["ltp"]

            # Update highest price
            if current_price > self.highest_price:
                self.highest_price = current_price

                # Calculate new SL
                new_sl = self.highest_price * (1 - self.trail_percent / 100)

                # Only update if new SL is higher than current SL
                if new_sl > self.current_sl:
                    # Modify SL order
                    await self.broker.modify_order(
                        order_id=self.sl_order_id,
                        trigger_price=new_sl
                    )
                    self.current_sl = new_sl
                    logger.info(f"Trailing SL updated: ₹{new_sl:.2f}")

            # Check if SL triggered
            sl_status = await self.broker.get_order_status(self.sl_order_id)
            if sl_status["status"] == OrderStatus.COMPLETE:
                return {
                    "sl_order_id": self.sl_order_id,
                    "exit_price": sl_status["avg_price"],
                    "status": "TRIGGERED"
                }

            await asyncio.sleep(self.check_interval)
```

---

### API Integration

**New endpoints in Engine-C:**

```python
@app.post("/api/v1/orders/iceberg")
async def place_iceberg_order(
    symbol: str,
    total_quantity: int,
    visible_quantity: int,
    price: float,
    user_id: str = Depends(get_current_user)
):
    broker = await get_user_broker(user_id)

    iceberg = IcebergOrder(
        broker=broker,
        symbol=symbol,
        total_quantity=total_quantity,
        visible_quantity=visible_quantity,
        order_type=OrderType.LIMIT,
        price=price
    )

    result = await iceberg.execute()
    return result

@app.post("/api/v1/orders/bracket")
async def place_bracket_order(
    symbol: str,
    quantity: int,
    entry_price: float,
    stop_loss: float,
    target: float,
    user_id: str = Depends(get_current_user)
):
    broker = await get_user_broker(user_id)

    bracket = BracketOrder(
        broker=broker,
        symbol=symbol,
        quantity=quantity,
        entry_price=entry_price,
        stop_loss=stop_loss,
        target=target
    )

    result = await bracket.execute()
    return result
```

---

## Q3 2026: Options Strategies

### Strategic Rationale

**Problem:** Current platform only supports equity trading. Options market represents 25% of Indian retail trading volume (Sensibull has 25% market share).

**Opportunity:** Options automation is complex and underserved. Most platforms (Zerodha Streak, TradingView) don't support options strategies.

---

### Options Strategies Roadmap

#### 1. Iron Condor

**Concept:** Neutral strategy to profit from low volatility.

**Structure:**

- Sell OTM call (higher strike)
- Buy farther OTM call (hedge)
- Sell OTM put (lower strike)
- Buy farther OTM put (hedge)

**Example (NIFTY at 21,000):**

- Sell 21,500 CE (collect ₹100 premium)
- Buy 21,600 CE (pay ₹50 premium)
- Sell 20,500 PE (collect ₹100 premium)
- Buy 20,400 PE (pay ₹50 premium)
- **Net credit:** ₹100 (max profit if NIFTY stays between 20,500-21,500)

**Implementation:**

```python
# backend/shared/strategies/iron_condor.py

class IronCondorStrategy:
    """
    Iron Condor: 4-leg options strategy for neutral markets.

    Max profit = Net premium collected
    Max loss = Strike width - Net premium
    """

    def __init__(
        self,
        broker: IBrokerAdapter,
        symbol: str,
        expiry: datetime,
        call_short_strike: float,
        call_long_strike: float,
        put_short_strike: float,
        put_long_strike: float,
        lot_size: int = 1
    ):
        self.broker = broker
        self.symbol = symbol
        self.expiry = expiry
        self.call_short_strike = call_short_strike
        self.call_long_strike = call_long_strike
        self.put_short_strike = put_short_strike
        self.put_long_strike = put_long_strike
        self.lot_size = lot_size

    async def execute(self) -> Dict[str, Any]:
        """
        Execute all 4 legs of iron condor.
        """
        # 1. Sell OTM call
        call_short = await self.broker.place_order(
            symbol=self._get_option_symbol("CE", self.call_short_strike),
            quantity=-self.lot_size,
            order_type=OrderType.MARKET
        )

        # 2. Buy farther OTM call
        call_long = await self.broker.place_order(
            symbol=self._get_option_symbol("CE", self.call_long_strike),
            quantity=self.lot_size,
            order_type=OrderType.MARKET
        )

        # 3. Sell OTM put
        put_short = await self.broker.place_order(
            symbol=self._get_option_symbol("PE", self.put_short_strike),
            quantity=-self.lot_size,
            order_type=OrderType.MARKET
        )

        # 4. Buy farther OTM put
        put_long = await self.broker.place_order(
            symbol=self._get_option_symbol("PE", self.put_long_strike),
            quantity=self.lot_size,
            order_type=OrderType.MARKET
        )

        # Calculate net credit
        net_credit = await self._calculate_net_credit([
            call_short, call_long, put_short, put_long
        ])

        return {
            "strategy": "iron_condor",
            "legs": [call_short, call_long, put_short, put_long],
            "net_credit": net_credit,
            "max_profit": net_credit,
            "max_loss": (self.call_long_strike - self.call_short_strike) - net_credit,
            "status": "COMPLETED"
        }

    def _get_option_symbol(self, option_type: str, strike: float) -> str:
        """
        Construct option symbol.

        Format: NIFTY22JAN21500CE (NIFTY, 22 JAN, 21500 strike, CE)
        """
        expiry_str = self.expiry.strftime("%y%b").upper()
        return f"{self.symbol}{expiry_str}{int(strike)}{option_type}"
```

---

#### 2. Greeks Calculator

**Concept:** Calculate option Greeks (Delta, Gamma, Theta, Vega, Rho) for risk management.

**Implementation:**

```python
# backend/shared/analytics/greeks.py

from scipy.stats import norm
import numpy as np

class GreeksCalculator:
    """
    Black-Scholes Greeks calculator.

    Delta: Rate of change of option price with underlying price
    Gamma: Rate of change of Delta
    Theta: Rate of time decay
    Vega: Sensitivity to volatility
    Rho: Sensitivity to interest rates
    """

    @staticmethod
    def calculate_greeks(
        spot: float,
        strike: float,
        time_to_expiry: float,  # Years
        volatility: float,  # Annualized (e.g., 0.20 for 20%)
        risk_free_rate: float = 0.06,  # 6% RBI rate
        option_type: str = "CE"  # CE or PE
    ) -> Dict[str, float]:
        """
        Calculate all Greeks for a single option.
        """
        # d1 and d2 from Black-Scholes
        d1 = (
            np.log(spot / strike) +
            (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry
        ) / (volatility * np.sqrt(time_to_expiry))

        d2 = d1 - volatility * np.sqrt(time_to_expiry)

        # Delta
        if option_type == "CE":
            delta = norm.cdf(d1)
        else:  # PE
            delta = norm.cdf(d1) - 1

        # Gamma (same for CE and PE)
        gamma = norm.pdf(d1) / (spot * volatility * np.sqrt(time_to_expiry))

        # Theta
        if option_type == "CE":
            theta = (
                -(spot * norm.pdf(d1) * volatility) / (2 * np.sqrt(time_to_expiry)) -
                risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
            ) / 365  # Daily theta
        else:  # PE
            theta = (
                -(spot * norm.pdf(d1) * volatility) / (2 * np.sqrt(time_to_expiry)) +
                risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2)
            ) / 365  # Daily theta

        # Vega (same for CE and PE)
        vega = spot * norm.pdf(d1) * np.sqrt(time_to_expiry) / 100  # Per 1% change in volatility

        # Rho
        if option_type == "CE":
            rho = strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2) / 100
        else:  # PE
            rho = -strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) / 100

        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho
        }

    @staticmethod
    def calculate_portfolio_greeks(
        positions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate aggregate Greeks for options portfolio.

        Args:
            positions: List of options positions
                [{
                    "symbol": "NIFTY22JAN21500CE",
                    "quantity": 100,
                    "spot": 21000,
                    "strike": 21500,
                    "expiry": "2022-01-27",
                    "volatility": 0.18,
                    "option_type": "CE"
                }]
        """
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        total_rho = 0

        for pos in positions:
            # Calculate time to expiry
            expiry = datetime.strptime(pos["expiry"], "%Y-%m-%d")
            time_to_expiry = (expiry - datetime.now()).days / 365

            # Calculate Greeks
            greeks = GreeksCalculator.calculate_greeks(
                spot=pos["spot"],
                strike=pos["strike"],
                time_to_expiry=time_to_expiry,
                volatility=pos["volatility"],
                option_type=pos["option_type"]
            )

            # Aggregate (weighted by quantity)
            total_delta += greeks["delta"] * pos["quantity"]
            total_gamma += greeks["gamma"] * pos["quantity"]
            total_theta += greeks["theta"] * pos["quantity"]
            total_vega += greeks["vega"] * pos["quantity"]
            total_rho += greeks["rho"] * pos["quantity"]

        return {
            "delta": total_delta,
            "gamma": total_gamma,
            "theta": total_theta,
            "vega": total_vega,
            "rho": total_rho
        }
```

---

## Q3 2026: Enhanced Risk Analytics

### VaR Stress Testing

**Concept:** Simulate portfolio losses under extreme market scenarios.

**Implementation:**

```python
# backend/shared/analytics/var_stress.py

class VaRStressTest:
    """
    Value at Risk stress testing with historical simulation.
    """

    @staticmethod
    async def calculate_var(
        portfolio: List[Dict[str, Any]],
        confidence_level: float = 0.95,  # 95% confidence
        time_horizon: int = 1,  # 1 day
        historical_days: int = 252  # 1 year
    ) -> Dict[str, float]:
        """
        Calculate portfolio VaR using historical simulation.

        Returns 95% VaR: Maximum expected loss in 1 day with 95% confidence
        """
        # 1. Get historical returns for each asset
        returns_matrix = []

        for position in portfolio:
            historical_data = await fetch_historical_data(
                symbol=position["symbol"],
                days=historical_days
            )

            # Calculate daily returns
            prices = [d["close"] for d in historical_data]
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            returns_matrix.append(returns)

        # 2. Calculate portfolio returns for each historical day
        portfolio_returns = []

        for day in range(historical_days):
            daily_portfolio_return = sum(
                position["weight"] * returns_matrix[i][day]
                for i, position in enumerate(portfolio)
            )
            portfolio_returns.append(daily_portfolio_return)

        # 3. Calculate VaR at confidence level
        portfolio_returns_sorted = sorted(portfolio_returns)
        var_index = int((1 - confidence_level) * len(portfolio_returns))
        var_return = portfolio_returns_sorted[var_index]

        # 4. Convert to rupee value
        portfolio_value = sum(pos["value"] for pos in portfolio)
        var_rupees = abs(var_return * portfolio_value)

        return {
            "var_percent": var_return * 100,  # -2.5% (example)
            "var_rupees": var_rupees,  # ₹25,000 loss expected at 95% confidence
            "confidence_level": confidence_level,
            "time_horizon_days": time_horizon
        }
```

---

## Deployment Timeline

**Q2 2026 (Apr-Jun):**

- Week 1-8: Multi-broker support (Zerodha, Upstox)
- Week 9-12: Advanced order types (iceberg, OCO, bracket, trailing stop)

**Q3 2026 (Jul-Sep):**

- Week 1-6: Options strategies (iron condor, spreads, covered call)
- Week 7-10: Greeks calculator + Portfolio Greeks
- Week 11-12: VaR stress testing

**Q4 2026 (Oct-Dec):**

- Week 1-4: Deep learning (LSTM for time-series forecasting)
- Week 5-8: Reinforcement learning (DQN agent for order placement)
- Week 9-12: US market integration (Interactive Brokers)

---

## Success Metrics

| Feature            | Metric                                | Target (Q2) | Target (Q3) | Target (Q4) |
| ------------------ | ------------------------------------- | ----------- | ----------- | ----------- |
| Multi-Broker       | Users with Zerodha/Upstox connected   | 30%         | 50%         | 70%         |
| Advanced Orders    | Iceberg/Bracket orders placed per day | 50          | 200         | 500         |
| Options Strategies | Iron condor/spreads executed per week | 10          | 50          | 100         |
| Options Users      | % of users trading options            | 5%          | 15%         | 25%         |
| Risk Analytics     | Users using VaR/Greeks                | 10%         | 30%         | 50%         |

---

**Report Generated:** 2026-01-22
**Next Review:** Q2 2026 (April 2026)
**Owner:** Platform Engineering Team
