from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Quote:
    symbol: str
    price: float
    timestamp: datetime
    source: str
    currency: Optional[str] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[float] = None

@dataclass
class NewsItem:
    id: str
    title: str
    body: str
    published_at: datetime
    symbols: List[str] = field(default_factory=list)
    source: str = "unknown"
    url: Optional[str] = None
    language: Optional[str] = None
