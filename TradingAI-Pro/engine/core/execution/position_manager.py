import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"

@dataclass
class Position:
    symbol: str
    user_id: str
    quantity: int = 0
    avg_price: float = 0.0
    market_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    side: PositionSide = PositionSide.FLAT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PositionManager:
    def __init__(self):
        self.positions: Dict[str, Position] = {}  # key: f"{user_id}:{symbol}"
        self.user_positions: Dict[str, List[str]] = {}
        self.position_callbacks: List[callable] = []
        
    def add_position_callback(self, callback):
        """Add callback for position updates"""
        self.position_callbacks.append(callback)
        
    def _get_position_key(self, user_id: str, symbol: str) -> str:
        return f"{user_id}:{symbol}"
        
    async def update_position(self, user_id: str, symbol: str, 
                            fill_qty: int, fill_price: float, side: str):
        """Update position based on trade execution"""
        position_key = self._get_position_key(user_id, symbol)
        
        if position_key not in self.positions:
            # Create new position
            position = Position(
                symbol=symbol,
                user_id=user_id,
                quantity=0,
                avg_price=0.0
            )
            self.positions[position_key] = position
            
            # Index by user
            if user_id not in self.user_positions:
                self.user_positions[user_id] = []
            self.user_positions[user_id].append(position_key)
        else:
            position = self.positions[position_key]
            
        # Calculate new position
        old_qty = position.quantity
        old_avg_price = position.avg_price
        
        if side == "BUY":
            new_qty = old_qty + fill_qty
        else:  # SELL
            new_qty = old_qty - fill_qty
            
        # Calculate realized PnL for closing trades
        if old_qty != 0 and ((old_qty > 0 and side == "SELL") or (old_qty < 0 and side == "BUY")):
            closing_qty = min(abs(old_qty), fill_qty)
            if side == "SELL":
                realized_pnl = closing_qty * (fill_price - old_avg_price)
            else:
                realized_pnl = closing_qty * (old_avg_price - fill_price)
            position.realized_pnl += realized_pnl
            
        # Update average price for opening trades
        if (old_qty >= 0 and side == "BUY") or (old_qty <= 0 and side == "SELL"):
            if old_qty == 0:
                position.avg_price = fill_price
            else:
                total_cost = old_qty * old_avg_price + fill_qty * fill_price
                position.avg_price = total_cost / new_qty if new_qty != 0 else 0
                
        position.quantity = new_qty
        position.updated_at = datetime.now()
        
        # Update position side
        if new_qty > 0:
            position.side = PositionSide.LONG
        elif new_qty < 0:
            position.side = PositionSide.SHORT
        else:
            position.side = PositionSide.FLAT
            
        logger.info(f"Updated position {symbol} for {user_id}: {old_qty} -> {new_qty}")
        await self._notify_callbacks(position, "UPDATED")
        
    async def update_market_price(self, symbol: str, price: float):
        """Update market price for all positions in this symbol"""
        updated_positions = []
        
        for position_key, position in self.positions.items():
            if position.symbol == symbol:
                position.market_price = price
                
                # Calculate unrealized PnL
                if position.quantity != 0:
                    position.unrealized_pnl = position.quantity * (price - position.avg_price)
                else:
                    position.unrealized_pnl = 0.0
                    
                position.updated_at = datetime.now()
                updated_positions.append(position)
                
        # Notify callbacks for all updated positions
        for position in updated_positions:
            await self._notify_callbacks(position, "PRICE_UPDATE")
            
    def get_position(self, user_id: str, symbol: str) -> Optional[Position]:
        """Get position for user and symbol"""
        position_key = self._get_position_key(user_id, symbol)
        return self.positions.get(position_key)
        
    def get_user_positions(self, user_id: str, active_only: bool = True) -> List[Position]:
        """Get all positions for a user"""
        position_keys = self.user_positions.get(user_id, [])
        positions = [self.positions[key] for key in position_keys if key in self.positions]
        
        if active_only:
            positions = [p for p in positions if p.quantity != 0]
            
        return positions
        
    def get_total_pnl(self, user_id: str) -> Dict[str, float]:
        """Get total PnL for user"""
        positions = self.get_user_positions(user_id, active_only=False)
        
        total_unrealized = sum(p.unrealized_pnl for p in positions)
        total_realized = sum(p.realized_pnl for p in positions)
        
        return {
            "unrealized_pnl": total_unrealized,
            "realized_pnl": total_realized,
            "total_pnl": total_unrealized + total_realized
        }
        
    async def _notify_callbacks(self, position: Position, event_type: str):
        """Notify all registered callbacks of position events"""
        for callback in self.position_callbacks:
            try:
                await callback(position, event_type)
            except Exception as e:
                logger.error(f"Error in position callback: {e}")

# Global position manager instance
position_manager = PositionManager()