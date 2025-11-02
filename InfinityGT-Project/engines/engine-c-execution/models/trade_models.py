from dataclasses import dataclass
from typing import Optional

@dataclass
class Trade:
    tradeId: str
    orderId: str
    symbol: str
    qty: int
    price: float
    side: str
    timestamp: str
    pnl: Optional[float] = None
