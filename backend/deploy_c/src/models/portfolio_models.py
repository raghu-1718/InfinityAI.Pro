from dataclasses import dataclass
from typing import List, Any

@dataclass
class Position:
    symbol: str
    netQty: int
    avgPrice: float
    currentPrice: float

@dataclass
class PortfolioState:
    pnl: float
    positions: List[Position]
    holdings: List[Any]
    trades: List[Any]
