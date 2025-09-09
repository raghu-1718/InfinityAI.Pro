import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import numpy as np
import logging

from ..market_data.feed_manager import MarketTick
from ..execution.order_manager import Order, OrderType

logger = logging.getLogger(__name__)

@dataclass
class BreakoutSignal:
    symbol: str
    direction: str  # "LONG" or "SHORT"
    entry_price: float
    stop_loss: float
    target: float
    confidence: float
    timestamp: datetime
    volume_confirmation: bool = False
    momentum_confirmation: bool = False

class AdvancedBreakoutStrategy:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.lookback_period = config.get("lookback_period", 20)
        self.volume_threshold = config.get("volume_threshold", 1.5)
        self.momentum_threshold = config.get("momentum_threshold", 0.02)
        self.stop_loss_pct = config.get("stop_loss_pct", 0.02)
        self.target_ratio = config.get("target_ratio", 2.0)  # Risk:Reward
        self.min_confidence = config.get("min_confidence", 0.7)
        
        # Data storage
        self.price_history: Dict[str, List[float]] = {}
        self.volume_history: Dict[str, List[int]] = {}
        self.timestamp_history: Dict[str, List[datetime]] = {}
        self.support_resistance: Dict[str, Dict[str, float]] = {}
        self.active_signals: Dict[str, BreakoutSignal] = {}
        
    async def process_tick(self, tick: MarketTick) -> Optional[BreakoutSignal]:
        """Process market tick and generate breakout signals"""
        symbol = tick.symbol
        
        # Update price history
        self._update_history(tick)
        
        # Calculate support and resistance levels
        await self._calculate_levels(symbol)
        
        # Check for breakout conditions
        signal = await self._check_breakout(tick)
        
        if signal and signal.confidence >= self.min_confidence:
            self.active_signals[symbol] = signal
            logger.info(f"Generated breakout signal for {symbol}: {signal.direction} at {signal.entry_price}")
            return signal
            
        return None
        
    def _update_history(self, tick: MarketTick):
        """Update price and volume history"""
        symbol = tick.symbol
        
        # Initialize if needed
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            self.volume_history[symbol] = []
            self.timestamp_history[symbol] = []
            
        # Add new data
        self.price_history[symbol].append(tick.price)
        self.volume_history[symbol].append(tick.volume)
        self.timestamp_history[symbol].append(tick.timestamp)
        
        # Keep only recent data
        max_length = self.lookback_period * 2
        if len(self.price_history[symbol]) > max_length:
            self.price_history[symbol] = self.price_history[symbol][-max_length:]
            self.volume_history[symbol] = self.volume_history[symbol][-max_length:]
            self.timestamp_history[symbol] = self.timestamp_history[symbol][-max_length:]
            
    async def _calculate_levels(self, symbol: str):
        """Calculate support and resistance levels"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < self.lookback_period:
            return
            
        prices = np.array(self.price_history[symbol][-self.lookback_period:])
        
        # Calculate pivot points
        highs = []
        lows = []
        
        for i in range(2, len(prices) - 2):
            # Local high
            if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and 
                prices[i] > prices[i+1] and prices[i] > prices[i+2]):
                highs.append(prices[i])
                
            # Local low
            if (prices[i] < prices[i-1] and prices[i] < prices[i-2] and 
                prices[i] < prices[i+1] and prices[i] < prices[i+2]):
                lows.append(prices[i])
                
        # Calculate support and resistance
        resistance = np.mean(highs) if highs else prices.max()
        support = np.mean(lows) if lows else prices.min()
        
        # Store levels
        if symbol not in self.support_resistance:
            self.support_resistance[symbol] = {}
            
        self.support_resistance[symbol].update({
            "resistance": resistance,
            "support": support,
            "current_high": prices.max(),
            "current_low": prices.min(),
            "sma_20": prices.mean()
        })
        
    async def _check_breakout(self, tick: MarketTick) -> Optional[BreakoutSignal]:
        """Check for breakout conditions"""
        symbol = tick.symbol
        
        if symbol not in self.support_resistance:
            return None
            
        levels = self.support_resistance[symbol]
        current_price = tick.price
        
        # Check for resistance breakout (long signal)
        if current_price > levels["resistance"]:
            # Confirm with volume
            volume_confirmed = self._check_volume_confirmation(symbol)
            
            # Confirm with momentum
            momentum_confirmed = self._check_momentum_confirmation(symbol)
            
            # Calculate confidence
            confidence = self._calculate_confidence(symbol, "LONG", volume_confirmed, momentum_confirmed)
            
            if confidence >= self.min_confidence:
                stop_loss = current_price * (1 - self.stop_loss_pct)
                target = current_price + (current_price - stop_loss) * self.target_ratio
                
                return BreakoutSignal(
                    symbol=symbol,
                    direction="LONG",
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    target=target,
                    confidence=confidence,
                    timestamp=tick.timestamp,
                    volume_confirmation=volume_confirmed,
                    momentum_confirmation=momentum_confirmed
                )
                
        # Check for support breakdown (short signal)
        elif current_price < levels["support"]:
            # Confirm with volume
            volume_confirmed = self._check_volume_confirmation(symbol)
            
            # Confirm with momentum
            momentum_confirmed = self._check_momentum_confirmation(symbol)
            
            # Calculate confidence
            confidence = self._calculate_confidence(symbol, "SHORT", volume_confirmed, momentum_confirmed)
            
            if confidence >= self.min_confidence:
                stop_loss = current_price * (1 + self.stop_loss_pct)
                target = current_price - (stop_loss - current_price) * self.target_ratio
                
                return BreakoutSignal(
                    symbol=symbol,
                    direction="SHORT",
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    target=target,
                    confidence=confidence,
                    timestamp=tick.timestamp,
                    volume_confirmation=volume_confirmed,
                    momentum_confirmation=momentum_confirmed
                )
                
        return None
        
    def _check_volume_confirmation(self, symbol: str) -> bool:
        """Check if breakout is confirmed by volume"""
        if symbol not in self.volume_history or len(self.volume_history[symbol]) < 10:
            return False
            
        recent_volumes = self.volume_history[symbol][-5:]
        avg_volume = np.mean(self.volume_history[symbol][-20:]) if len(self.volume_history[symbol]) >= 20 else np.mean(self.volume_history[symbol])
        
        current_volume = recent_volumes[-1]
        return current_volume > avg_volume * self.volume_threshold
        
    def _check_momentum_confirmation(self, symbol: str) -> bool:
        """Check if breakout is confirmed by momentum"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 10:
            return False
            
        prices = self.price_history[symbol]
        if len(prices) < 5:
            return False
            
        # Calculate short-term momentum
        recent_change = (prices[-1] - prices[-5]) / prices[-5]
        return abs(recent_change) > self.momentum_threshold
        
    def _calculate_confidence(self, symbol: str, direction: str, volume_confirmed: bool, momentum_confirmed: bool) -> float:
        """Calculate signal confidence score"""
        confidence = 0.5  # Base confidence
        
        # Volume confirmation adds confidence
        if volume_confirmed:
            confidence += 0.2
            
        # Momentum confirmation adds confidence
        if momentum_confirmed:
            confidence += 0.2
            
        # Price distance from level adds confidence
        if symbol in self.support_resistance and symbol in self.price_history:
            levels = self.support_resistance[symbol]
            current_price = self.price_history[symbol][-1]
            
            if direction == "LONG":
                distance_pct = (current_price - levels["resistance"]) / levels["resistance"]
            else:
                distance_pct = (levels["support"] - current_price) / levels["support"]
                
            # More distance = more confidence (up to a point)
            distance_confidence = min(distance_pct * 10, 0.1)  # Cap at 0.1
            confidence += distance_confidence
            
        return min(confidence, 1.0)  # Cap at 1.0
        
    async def create_orders(self, signal: BreakoutSignal, user_id: str, quantity: int) -> List[Order]:
        """Create orders based on breakout signal"""
        orders = []
        
        # Main entry order
        entry_order = Order(
            symbol=signal.symbol,
            side="BUY" if signal.direction == "LONG" else "SELL",
            quantity=quantity,
            order_type=OrderType.MARKET,
            user_id=user_id,
            strategy_id="advanced_breakout",
            metadata={
                "signal_confidence": signal.confidence,
                "entry_reason": "breakout_signal",
                "target_price": signal.target,
                "stop_loss_price": signal.stop_loss
            }
        )
        orders.append(entry_order)
        
        # Stop loss order (bracket order)
        stop_order = Order(
            symbol=signal.symbol,
            side="SELL" if signal.direction == "LONG" else "BUY",
            quantity=quantity,
            order_type=OrderType.STOP_LOSS,
            stop_price=signal.stop_loss,
            user_id=user_id,
            strategy_id="advanced_breakout",
            parent_order_id=entry_order.id,
            metadata={
                "order_type": "stop_loss",
                "parent_signal": signal.symbol
            }
        )
        orders.append(stop_order)
        
        # Target order (bracket order)
        target_order = Order(
            symbol=signal.symbol,
            side="SELL" if signal.direction == "LONG" else "BUY",
            quantity=quantity,
            order_type=OrderType.LIMIT,
            price=signal.target,
            user_id=user_id,
            strategy_id="advanced_breakout",
            parent_order_id=entry_order.id,
            metadata={
                "order_type": "target",
                "parent_signal": signal.symbol
            }
        )
        orders.append(target_order)
        
        return orders
        
    def get_active_signals(self) -> Dict[str, BreakoutSignal]:
        """Get all active signals"""
        return self.active_signals.copy()
        
    def clear_signal(self, symbol: str):
        """Clear active signal for symbol"""
        if symbol in self.active_signals:
            del self.active_signals[symbol]