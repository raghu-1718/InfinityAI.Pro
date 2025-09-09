import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LIMIT = "STOP_LIMIT"
    BRACKET = "BRACKET"
    COVER = "COVER"

@dataclass
class Order:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    side: str = ""  # BUY/SELL
    quantity: int = 0
    order_type: OrderType = OrderType.MARKET
    price: float = 0.0
    stop_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    broker_order_id: Optional[str] = None
    filled_quantity: int = 0
    avg_fill_price: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    user_id: str = ""
    strategy_id: str = ""
    parent_order_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class OrderManager:
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.user_orders: Dict[str, List[str]] = {}
        self.symbol_orders: Dict[str, List[str]] = {}
        self.pending_orders: List[str] = []
        self.order_callbacks: List[callable] = []
        
    def add_order_callback(self, callback):
        """Add callback for order status updates"""
        self.order_callbacks.append(callback)
        
    async def create_order(self, order: Order) -> str:
        """Create and validate a new order"""
        # Validate order
        if not self._validate_order(order):
            raise ValueError("Invalid order parameters")
            
        # Store order
        self.orders[order.id] = order
        
        # Index by user and symbol
        if order.user_id not in self.user_orders:
            self.user_orders[order.user_id] = []
        self.user_orders[order.user_id].append(order.id)
        
        if order.symbol not in self.symbol_orders:
            self.symbol_orders[order.symbol] = []
        self.symbol_orders[order.symbol].append(order.id)
        
        if order.status == OrderStatus.PENDING:
            self.pending_orders.append(order.id)
            
        logger.info(f"Created order {order.id} for {order.symbol}")
        await self._notify_callbacks(order, "CREATED")
        return order.id
        
    async def update_order_status(self, order_id: str, status: OrderStatus, 
                                 broker_order_id: Optional[str] = None,
                                 filled_qty: int = 0, fill_price: float = 0.0):
        """Update order status from broker feedback"""
        if order_id not in self.orders:
            logger.warning(f"Order {order_id} not found for status update")
            return
            
        order = self.orders[order_id]
        old_status = order.status
        
        order.status = status
        order.updated_at = datetime.now()
        
        if broker_order_id:
            order.broker_order_id = broker_order_id
            
        if filled_qty > 0:
            order.filled_quantity += filled_qty
            # Update average fill price
            if order.avg_fill_price == 0:
                order.avg_fill_price = fill_price
            else:
                total_value = (order.avg_fill_price * (order.filled_quantity - filled_qty) + 
                              fill_price * filled_qty)
                order.avg_fill_price = total_value / order.filled_quantity
                
        # Remove from pending if no longer pending
        if old_status == OrderStatus.PENDING and status != OrderStatus.PENDING:
            if order_id in self.pending_orders:
                self.pending_orders.remove(order_id)
                
        logger.info(f"Updated order {order_id} status: {old_status} -> {status}")
        await self._notify_callbacks(order, "UPDATED")
        
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id not in self.orders:
            return False
            
        order = self.orders[order_id]
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            return False
            
        await self.update_order_status(order_id, OrderStatus.CANCELLED)
        return True
        
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)
        
    def get_user_orders(self, user_id: str, status: Optional[OrderStatus] = None) -> List[Order]:
        """Get all orders for a user, optionally filtered by status"""
        order_ids = self.user_orders.get(user_id, [])
        orders = [self.orders[oid] for oid in order_ids if oid in self.orders]
        
        if status:
            orders = [o for o in orders if o.status == status]
            
        return sorted(orders, key=lambda x: x.created_at, reverse=True)
        
    def get_symbol_orders(self, symbol: str, active_only: bool = True) -> List[Order]:
        """Get all orders for a symbol"""
        order_ids = self.symbol_orders.get(symbol, [])
        orders = [self.orders[oid] for oid in order_ids if oid in self.orders]
        
        if active_only:
            active_statuses = [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
            orders = [o for o in orders if o.status in active_statuses]
            
        return orders
        
    def get_pending_orders(self) -> List[Order]:
        """Get all pending orders"""
        return [self.orders[oid] for oid in self.pending_orders if oid in self.orders]
        
    def _validate_order(self, order: Order) -> bool:
        """Validate order parameters"""
        if not order.symbol or not order.side or order.quantity <= 0:
            return False
            
        if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and order.price <= 0:
            return False
            
        if order.order_type in [OrderType.STOP_LOSS, OrderType.STOP_LIMIT] and order.stop_price <= 0:
            return False
            
        return True
        
    async def _notify_callbacks(self, order: Order, event_type: str):
        """Notify all registered callbacks of order events"""
        for callback in self.order_callbacks:
            try:
                await callback(order, event_type)
            except Exception as e:
                logger.error(f"Error in order callback: {e}")

# Global order manager instance
order_manager = OrderManager()