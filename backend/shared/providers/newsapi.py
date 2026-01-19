import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
import aiohttp
from .interfaces import NewsProvider
from .models import NewsItem

class NewsAPIProvider(NewsProvider):
    """NewsAPI.org - aggregates news from 40k+ sources."""

    @property
    def name(self) -> str:
        return "newsapi"

    def __init__(self):
        self.api_key = os.getenv("PROVIDER_NEWSAPI_API_KEY")
        self.base_url = "https://newsapi.org/v2"
        self.timeout = 30
        if not self.api_key:
            raise RuntimeError("PROVIDER_NEWSAPI_API_KEY not set in environment")

    async def fetch_news(self, topics: List[str]) -> List[NewsItem]:
        """
        Fetch news articles by keywords/symbols.
        Topics can be stock symbols (AAPL, MSFT) or general keywords (crypto, AI).
        """
        all_articles = []
        async with aiohttp.ClientSession() as session:
            for topic in topics:
                try:
                    params = {
                        "q": topic,
                        "apiKey": self.api_key,
                        "pageSize": 50,
                        "sortBy": "publishedAt",
                    }
                    async with session.get(f"{self.base_url}/everything", params=params, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for article in data.get("articles", []):
                                item = NewsItem(
                                    id=article.get("url", ""),
                                    title=article.get("title", ""),
                                    body=article.get("description", ""),
                                    published_at=datetime.fromisoformat(article.get("publishedAt", "").replace("Z", "+00:00")),
                                    symbols=[topic],  # Topic is added as symbol reference
                                    source=article.get("source", {}).get("name", "Unknown"),
                                    url=article.get("url"),
                                    language="en",
                                )
                                all_articles.append(item)
                except Exception as e:
                    print(f"Error fetching news for {topic} from NewsAPI: {e}")
                    await asyncio.sleep(0.5)
        return all_articles

    async def fetch_headlines(self, country: str = "us") -> List[NewsItem]:
        """Fetch top headlines for a given country code."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "country": country,
                    "apiKey": self.api_key,
                    "pageSize": 50,
                }
                async with session.get(f"{self.base_url}/top-headlines", params=params, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        articles = []
                        for article in data.get("articles", []):
                            item = NewsItem(
                                id=article.get("url", ""),
                                title=article.get("title", ""),
                                body=article.get("description", ""),
                                published_at=datetime.fromisoformat(article.get("publishedAt", "").replace("Z", "+00:00")),
                                symbols=[],
                                source=article.get("source", {}).get("name", "Unknown"),
                                url=article.get("url"),
                                language="en",
                            )
                            articles.append(item)
                        return articles
        except Exception as e:
            print(f"Error fetching headlines: {e}")
        return []
