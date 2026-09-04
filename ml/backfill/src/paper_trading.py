"""
Paper Trading Module

Simulates order execution without placing real trades.
Used for backtesting, paper trading mode, and API testing.

Features:
- Simulates order fills with realistic slippage
- Maintains virtual portfolio state
- Tracks P&L for simulation
- Generates fake order IDs for tracking
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class PaperOrder:
    """Represents a simulated order"""
    order_id: str
    symbol: str
    transaction_type: str  # BUY/SELL
    quantity: int
    price: float
    order_type: str  # MARKET/LIMIT/STOPLOSS
    status: str  # PENDING/FILLED/REJECTED/CANCELLED
    timestamp: datetime
    remarks: str = ""


@dataclass
class PaperPosition:
    """Represents a simulated position"""
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    entry_time: datetime


class PaperTradingEngine:
    """Simulates trading without real capital"""

    def __init__(self, initial_capital: float = 1000000.0, slippage_pct: float = 0.001):
        """
        Initialize paper trading engine

        Args:
            initial_capital: Starting cash amount
            slippage_pct: Slippage percentage (0.001 = 0.1%)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.slippage_pct = slippage_pct
        self.positions: Dict[str, PaperPosition] = {}
        self.orders: Dict[str, PaperOrder] = {}
        self.trades: List[Dict] = []
        self.pnl_history: List[float] = []

    def place_order(
        self,
        symbol: str,
        transaction_type: str,
        quantity: int,
        price: float,
        order_type: str = "MARKET",
        trigger_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Simulate order placement

        Args:
            symbol: Trading symbol (e.g., 'NIFTY')
            transaction_type: BUY or SELL
            quantity: Order quantity
            price: Limit price (0 for MARKET orders)
            order_type: MARKET, LIMIT, STOPLOSS
            trigger_price: For STOPLOSS orders

        Returns:
            Order confirmation dict
        """
        order_id = f"PAPER-{uuid.uuid4().hex[:8].upper()}"

        try:
            # Validate order
            if quantity <= 0:
                return {
                    "status": "failure",
                    "remarks": "Quantity must be positive",
                    "order_id": order_id
                }

            if transaction_type.upper() not in ["BUY", "SELL"]:
                return {
                    "status": "failure",
                    "remarks": "Invalid transaction type. Use BUY or SELL",
                    "order_id": order_id
                }

            # Calculate order value with slippage
            order_price = price if price > 0 else price  # For MARKET, use latest price
            order_value = quantity * order_price
            slippage = order_value * self.slippage_pct
            total_cost = order_value + slippage if transaction_type.upper() == "BUY" else order_value - slippage

            # Validate cash for BUY orders
            if transaction_type.upper() == "BUY" and total_cost > self.cash:
                return {
                    "status": "failure",
                    "remarks": f"Insufficient funds. Required: {total_cost:.2f}, Available: {self.cash:.2f}",
                    "order_id": order_id
                }

            # Create order record
            order = PaperOrder(
                order_id=order_id,
                symbol=symbol.upper(),
                transaction_type=transaction_type.upper(),
                quantity=quantity,
                price=order_price,
                order_type=order_type.upper(),
                status="FILLED",  # Paper orders fill immediately
                timestamp=datetime.utcnow(),
                remarks="Paper trading simulation"
            )

            self.orders[order_id] = order

            # Execute order immediately (paper trading)
            self._execute_paper_trade(symbol, transaction_type, quantity, order_price)

            logger.info(
                f"📄 Paper order filled: {order_id} | {symbol} | "
                f"{transaction_type} {quantity} @ {order_price:.2f}"
            )

            return {
                "status": "success",
                "order_id": order_id,
                "symbol": symbol,
                "transaction_type": transaction_type.upper(),
                "quantity": quantity,
                "price": order_price,
                "order_type": order_type.upper(),
                "remarks": "PAPER TRADE - Simulated execution",
                "timestamp": datetime.utcnow().isoformat(),
                "warning": "This is a paper trade simulation, not a real trade"
            }

        except Exception as e:
            logger.error(f"Paper order error: {e}")
            return {
                "status": "failure",
                "remarks": str(e),
                "order_id": order_id
            }

    def _execute_paper_trade(self, symbol: str, transaction_type: str, quantity: int, price: float):
        """Execute simulated trade"""
        symbol = symbol.upper()
        transaction_type = transaction_type.upper()

        if transaction_type == "BUY":
            # Update cash
            cost = quantity * price * (1 + self.slippage_pct)
            self.cash -= cost

            # Update or create position
            if symbol in self.positions:
                pos = self.positions[symbol]
                # Calculate weighted average entry price
                total_qty = pos.quantity + quantity
                pos.entry_price = (
                    (pos.quantity * pos.entry_price + quantity * price) / total_qty
                )
                pos.quantity = total_qty
            else:
                self.positions[symbol] = PaperPosition(
                    symbol=symbol,
                    quantity=quantity,
                    entry_price=price,
                    current_price=price,
                    entry_time=datetime.utcnow()
                )

        elif transaction_type == "SELL":
            if symbol not in self.positions:
                raise ValueError(f"No position to sell for {symbol}")

            pos = self.positions[symbol]
            if pos.quantity < quantity:
                raise ValueError(f"Insufficient position: Have {pos.quantity}, trying to sell {quantity}")

            # Calculate profit/loss
            revenue = quantity * price * (1 - self.slippage_pct)
            cost = quantity * pos.entry_price
            pnl = revenue - cost

            # Record trade
            self.trades.append({
                "symbol": symbol,
                "entry_price": pos.entry_price,
                "exit_price": price,
                "quantity": quantity,
                "pnl": pnl,
                "pnl_pct": (pnl / cost) * 100 if cost > 0 else 0,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Update cash
            self.cash += revenue

            # Update position
            pos.quantity -= quantity
            if pos.quantity == 0:
                del self.positions[symbol]
            else:
                pos.current_price = price

        self.pnl_history.append(self.get_portfolio_value())

    def get_portfolio_value(self) -> float:
        """Get total portfolio value (cash + positions)"""
        position_value = sum(
            pos.quantity * pos.current_price
            for pos in self.positions.values()
        )
        return self.cash + position_value

    def get_portfolio_state(self) -> Dict[str, Any]:
        """Get complete portfolio state"""
        total_value = self.get_portfolio_value()
        pnl = total_value - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0

        return {
            "mode": "PAPER_TRADING",
            "initial_capital": self.initial_capital,
            "current_cash": self.cash,
            "positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "position_value": pos.quantity * pos.current_price
                }
                for symbol, pos in self.positions.items()
            },
            "portfolio_value": total_value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "total_trades": len(self.trades),
            "open_positions": len(self.positions),
            "timestamp": datetime.utcnow().isoformat()
        }

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a paper order"""
        if order_id not in self.orders:
            return {"status": "failure", "remarks": "Order not found"}

        order = self.orders[order_id]
        if order.status == "FILLED":
            return {"status": "failure", "remarks": "Cannot cancel filled order"}

        order.status = "CANCELLED"
        return {
            "status": "success",
            "order_id": order_id,
            "remarks": "Paper order cancelled"
        }

    def get_order_history(self) -> List[Dict]:
        """Get all orders"""
        return [
            {
                "order_id": order.order_id,
                "symbol": order.symbol,
                "transaction_type": order.transaction_type,
                "quantity": order.quantity,
                "price": order.price,
                "order_type": order.order_type,
                "status": order.status,
                "timestamp": order.timestamp.isoformat()
            }
            for order in self.orders.values()
        ]

    def get_trade_history(self) -> List[Dict]:
        """Get completed trades"""
        return self.trades

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate trading statistics"""
        if not self.trades:
            return {"status": "No trades executed yet"}

        pnls = [t["pnl"] for t in self.trades]
        winning_trades = [t for t in self.trades if t["pnl"] > 0]

        return {
            "total_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(self.trades) - len(winning_trades),
            "win_rate": len(winning_trades) / len(self.trades) * 100 if self.trades else 0,
            "total_pnl": sum(pnls),
            "avg_pnl_per_trade": sum(pnls) / len(self.trades) if self.trades else 0,
            "max_profit": max(pnls) if pnls else 0,
            "max_loss": min(pnls) if pnls else 0
        }


# Global paper trading engine instance
_paper_engine: Optional[PaperTradingEngine] = None


def get_paper_engine() -> PaperTradingEngine:
    """Get or create global paper trading engine"""
    global _paper_engine
    if _paper_engine is None:
        _paper_engine = PaperTradingEngine(initial_capital=1000000.0)
    return _paper_engine


def reset_paper_engine():
    """Reset paper trading engine"""
    global _paper_engine
    _paper_engine = PaperTradingEngine(initial_capital=1000000.0)
