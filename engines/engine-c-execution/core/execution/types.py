from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"


class TransactionType(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class TradeOrder:
    order_id: str
    symbol: str
    quantity: int
    price: float
    order_type: OrderType
    transaction_type: TransactionType
    status: OrderStatus
    created_at: datetime
    executed_at: Optional[datetime] = None
    execution_price: Optional[float] = None
    fees: float = 0.0
    error_message: Optional[str] = None


@dataclass
class Position:
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    entry_time: datetime


@dataclass
class RiskCheck:
    passed: bool
    risk_score: float
    warnings: List[str]
    max_position_size: int
    current_exposure: float
