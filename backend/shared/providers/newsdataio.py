import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import aiohttp
from .interfaces import NewsProvider
from .models import NewsItem

class NewsDataIOProvider(NewsProvider):
    """NewsData.io - real-time global news aggregator with sentiment analysis.

    Supports both US and Indian (Hindi, English) news.
    For Indian market, automatically uses India country filter and Hindi language support.
    """

    @property
    def name(self) -> str:
        return "newsdata-io"

    def __init__(self):
        self.api_key = os.getenv("PROVIDER_NEWSDATAIO_API_KEY")
        self.base_url = "https://newsdata.io/api/1"
        self.timeout = 30
        self.market_config = os.getenv("MARKET_TYPE", "US")  # "US" or "INDIA"
        if not self.api_key:
            raise RuntimeError("PROVIDER_NEWSDATAIO_API_KEY not set in environment")

    def _get_language_list(self) -> str:
        """Get language filter for market."""
        if self.market_config in ["INDIA", "INDIAN"]:
            return "en,hi"  # English and Hindi for India
        return "en"  # English for US

    async def fetch_news(self, topics: List[str]) -> List[NewsItem]:
        """
        Fetch news by keywords/symbols.
        Supports multi-language, sentiment analysis, and real-time updates.
        Free tier: 2,000 calls/day; Premium: up to 100k/day.

        For Indian market, filters for India + supports Hindi language.
        """
        all_articles = []
        languages = self._get_language_list()

        async with aiohttp.ClientSession() as session:
            for topic in topics:
                try:
                    params = {
                        "apikey": self.api_key,
                        "q": topic,
                        "language": languages,
                        "limit": 50,
                        "sort": "recent",
                    }
                    # Add country filter for Indian market
                    if self.market_config in ["INDIA", "INDIAN"]:
                        params["country"] = "in"

                    async with session.get(f"{self.base_url}/news", params=params, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for article in data.get("results", []):
                                item = NewsItem(
                                    id=article.get("id", ""),
                                    title=article.get("title", ""),
                                    body=article.get("content", ""),
                                    published_at=datetime.fromisoformat(article.get("pubDate", "").replace("Z", "+00:00")),
                                    symbols=[topic],
                                    source=article.get("source_id", "Unknown"),
                                    url=article.get("link"),
                                    language=article.get("language", "en"),
                                )
                                all_articles.append(item)
                except Exception as e:
                    print(f"Error fetching news for {topic} from NewsData.io: {e}")
                    await asyncio.sleep(0.5)
        return all_articles

    async def fetch_by_country(self, country: str = None, limit: int = 50) -> List[NewsItem]:
        """
        Fetch news articles by country code (e.g., 'us', 'in', 'gb').

        For Indian market, automatically uses India (in).
        For US market, uses US (us).
        """
        try:
            if country is None:
                country = "in" if self.market_config in ["INDIA", "INDIAN"] else "us"

            languages = self._get_language_list()

            async with aiohttp.ClientSession() as session:
                params = {
                    "apikey": self.api_key,
                    "country": country,
                    "language": languages,
                    "limit": limit,
                    "sort": "recent",
                }
                async with session.get(f"{self.base_url}/news", params=params, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        articles = []
                        for article in data.get("results", []):
                            item = NewsItem(
                                id=article.get("id", ""),
                                title=article.get("title", ""),
                                body=article.get("content", ""),
                                published_at=datetime.fromisoformat(article.get("pubDate", "").replace("Z", "+00:00")),
                                symbols=[],
                                source=article.get("source_id", "Unknown"),
                                url=article.get("link"),
                                language=article.get("language", "en"),
                            )
                            articles.append(item)
                        return articles
        except Exception as e:
            print(f"Error fetching news by country: {e}")
        return []
