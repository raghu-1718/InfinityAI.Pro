import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .position_manager import position_manager, Position
from .order_manager import order_manager, Order, OrderStatus

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class RiskLimits:
    max_position_size: int = 1000
    max_daily_loss: float = 10000.0
    max_drawdown: float = 0.20  # 20%
    max_leverage: float = 3.0
    max_orders_per_minute: int = 10
    max_concentration: float = 0.30  # 30% of portfolio in single symbol
    stop_loss_percentage: float = 0.05  # 5%
    position_timeout_hours: int = 24

@dataclass
class RiskMetrics:
    current_drawdown: float = 0.0
    daily_pnl: float = 0.0
    portfolio_value: float = 0.0
    leverage_ratio: float = 0.0
    largest_position_pct: float = 0.0
    orders_last_minute: int = 0
    risk_level: RiskLevel = RiskLevel.LOW

class RiskManager:
    def __init__(self):
        self.user_limits: Dict[str, RiskLimits] = {}
        self.user_metrics: Dict[str, RiskMetrics] = {}
        self.order_timestamps: Dict[str, List[datetime]] = {}
        self.daily_start_values: Dict[str, float] = {}
        self.risk_callbacks: List[callable] = []
        
    def add_risk_callback(self, callback):
        """Add callback for risk events"""
        self.risk_callbacks.append(callback)
        
    def set_user_limits(self, user_id: str, limits: RiskLimits):
        """Set risk limits for a user"""
        self.user_limits[user_id] = limits
        logger.info(f"Updated risk limits for user {user_id}")
        
    def get_user_limits(self, user_id: str) -> RiskLimits:
        """Get risk limits for a user"""
        return self.user_limits.get(user_id, RiskLimits())
        
    async def validate_order(self, order: Order) -> Tuple[bool, str]:
        """Validate if order passes risk checks"""
        user_id = order.user_id
        limits = self.get_user_limits(user_id)
        
        # Check position size limit
        current_position = position_manager.get_position(user_id, order.symbol)
        new_position_size = order.quantity
        if current_position:
            if order.side == "BUY":
                new_position_size = current_position.quantity + order.quantity
            else:
                new_position_size = abs(current_position.quantity - order.quantity)
                
        if new_position_size > limits.max_position_size:
            return False, f"Position size {new_position_size} exceeds limit {limits.max_position_size}"
            
        # Check order frequency
        if not self._check_order_frequency(user_id, limits.max_orders_per_minute):
            return False, f"Order frequency exceeds limit of {limits.max_orders_per_minute} per minute"
            
        # Check daily loss limit
        metrics = await self._calculate_risk_metrics(user_id)
        if metrics.daily_pnl < -limits.max_daily_loss:
            return False, f"Daily loss {abs(metrics.daily_pnl)} exceeds limit {limits.max_daily_loss}"
            
        # Check drawdown limit
        if metrics.current_drawdown > limits.max_drawdown:
            return False, f"Drawdown {metrics.current_drawdown:.2%} exceeds limit {limits.max_drawdown:.2%}"
            
        # Check concentration limit
        portfolio_value = metrics.portfolio_value
        if portfolio_value > 0:
            position_value = new_position_size * (order.price or 100)  # Use order price or estimate
            concentration = position_value / portfolio_value
            if concentration > limits.max_concentration:
                return False, f"Position concentration {concentration:.2%} exceeds limit {limits.max_concentration:.2%}"
                
        return True, "Order passed risk checks"
        
    async def monitor_positions(self, user_id: str):
        """Monitor positions for risk violations"""
        limits = self.get_user_limits(user_id)
        positions = position_manager.get_user_positions(user_id)
        
        for position in positions:
            # Check stop loss
            if position.quantity != 0 and position.market_price > 0:
                loss_pct = (position.avg_price - position.market_price) / position.avg_price
                if position.quantity > 0 and loss_pct > limits.stop_loss_percentage:
                    await self._trigger_stop_loss(position)
                elif position.quantity < 0 and loss_pct < -limits.stop_loss_percentage:
                    await self._trigger_stop_loss(position)
                    
            # Check position timeout
            position_age = datetime.now() - position.created_at
            if position_age > timedelta(hours=limits.position_timeout_hours):
                await self._notify_callbacks(position, "POSITION_TIMEOUT")
                
    async def _calculate_risk_metrics(self, user_id: str) -> RiskMetrics:
        """Calculate current risk metrics for user"""
        positions = position_manager.get_user_positions(user_id, active_only=False)
        pnl_data = position_manager.get_total_pnl(user_id)
        
        # Calculate portfolio value (simplified)
        portfolio_value = sum(abs(p.quantity * p.market_price) for p in positions if p.market_price > 0)
        if portfolio_value == 0:
            portfolio_value = 100000  # Default portfolio value
            
        # Calculate daily PnL
        daily_pnl = pnl_data["total_pnl"]
        
        # Calculate drawdown
        if user_id not in self.daily_start_values:
            self.daily_start_values[user_id] = portfolio_value
        start_value = self.daily_start_values[user_id]
        current_drawdown = max(0, (start_value - portfolio_value) / start_value) if start_value > 0 else 0
        
        # Calculate leverage
        total_exposure = sum(abs(p.quantity * p.market_price) for p in positions if p.market_price > 0)
        leverage_ratio = total_exposure / portfolio_value if portfolio_value > 0 else 0
        
        # Find largest position percentage
        largest_position_pct = 0
        if portfolio_value > 0:
            position_values = [abs(p.quantity * p.market_price) for p in positions if p.market_price > 0]
            if position_values:
                largest_position_pct = max(position_values) / portfolio_value
                
        # Count recent orders
        orders_last_minute = self._count_recent_orders(user_id, minutes=1)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(current_drawdown, daily_pnl, leverage_ratio)
        
        metrics = RiskMetrics(
            current_drawdown=current_drawdown,
            daily_pnl=daily_pnl,
            portfolio_value=portfolio_value,
            leverage_ratio=leverage_ratio,
            largest_position_pct=largest_position_pct,
            orders_last_minute=orders_last_minute,
            risk_level=risk_level
        )
        
        self.user_metrics[user_id] = metrics
        return metrics
        
    def _check_order_frequency(self, user_id: str, max_per_minute: int) -> bool:
        """Check if order frequency is within limits"""
        now = datetime.now()
        if user_id not in self.order_timestamps:
            self.order_timestamps[user_id] = []
            
        # Clean old timestamps
        cutoff = now - timedelta(minutes=1)
        self.order_timestamps[user_id] = [
            ts for ts in self.order_timestamps[user_id] if ts > cutoff
        ]
        
        # Check limit
        if len(self.order_timestamps[user_id]) >= max_per_minute:
            return False
            
        # Add current timestamp
        self.order_timestamps[user_id].append(now)
        return True
        
    def _count_recent_orders(self, user_id: str, minutes: int) -> int:
        """Count orders in the last N minutes"""
        if user_id not in self.order_timestamps:
            return 0
            
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return len([ts for ts in self.order_timestamps[user_id] if ts > cutoff])
        
    def _calculate_risk_level(self, drawdown: float, daily_pnl: float, leverage: float) -> RiskLevel:
        """Calculate overall risk level"""
        risk_score = 0
        
        # Drawdown contribution
        if drawdown > 0.15:
            risk_score += 3
        elif drawdown > 0.10:
            risk_score += 2
        elif drawdown > 0.05:
            risk_score += 1
            
        # Daily PnL contribution
        if daily_pnl < -5000:
            risk_score += 3
        elif daily_pnl < -2000:
            risk_score += 2
        elif daily_pnl < -1000:
            risk_score += 1
            
        # Leverage contribution
        if leverage > 2.5:
            risk_score += 3
        elif leverage > 2.0:
            risk_score += 2
        elif leverage > 1.5:
            risk_score += 1
            
        # Determine risk level
        if risk_score >= 7:
            return RiskLevel.CRITICAL
        elif risk_score >= 5:
            return RiskLevel.HIGH
        elif risk_score >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
            
    async def _trigger_stop_loss(self, position: Position):
        """Trigger stop loss for a position"""
        logger.warning(f"Triggering stop loss for {position.symbol} user {position.user_id}")
        
        # Create stop loss order
        from .order_manager import Order, OrderType
        stop_order = Order(
            symbol=position.symbol,
            side="SELL" if position.quantity > 0 else "BUY",
            quantity=abs(position.quantity),
            order_type=OrderType.MARKET,
            user_id=position.user_id,
            strategy_id="RISK_STOP_LOSS",
            metadata={"reason": "stop_loss_triggered"}
        )
        
        await order_manager.create_order(stop_order)
        await self._notify_callbacks(position, "STOP_LOSS_TRIGGERED")
        
    async def _notify_callbacks(self, data: Any, event_type: str):
        """Notify all registered callbacks of risk events"""
        for callback in self.risk_callbacks:
            try:
                await callback(data, event_type)
            except Exception as e:
                logger.error(f"Error in risk callback: {e}")

# Global risk manager instance
risk_manager = RiskManager()