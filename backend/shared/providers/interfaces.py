from abc import ABC, abstractmethod
from typing import List

from .models import Quote, NewsItem

class MarketDataProvider(ABC):
    """Abstract interface for market data providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def fetch_quotes(self, symbols: List[str]) -> List[Quote]:
        """Fetch latest quotes for given symbols."""
        ...

class NewsProvider(ABC):
    """Abstract interface for news providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def fetch_news(self, topics: List[str]) -> List[NewsItem]:
        """Fetch latest news articles for given topics/symbols."""
        ...
