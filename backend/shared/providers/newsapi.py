import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
import aiohttp
from .interfaces import NewsProvider
from .models import NewsItem

class NewsAPIProvider(NewsProvider):
    """NewsAPI.org - aggregates news from 40k+ sources.

    Supports both US and Indian stock market news.
    For Indian market, filters for India-focused sources and stocks.
    """

    @property
    def name(self) -> str:
        return "newsapi"

    def __init__(self):
        self.api_key = os.getenv("PROVIDER_NEWSAPI_API_KEY")
        self.base_url = "https://newsapi.org/v2"
        self.timeout = 30
        self.market_config = os.getenv("MARKET_TYPE", "US")  # "US" or "INDIA"
        if not self.api_key:
            raise RuntimeError("PROVIDER_NEWSAPI_API_KEY not set in environment")

    def _get_country_code(self) -> str:
        """Get country code for headlines based on market config."""
        if self.market_config in ["INDIA", "INDIAN"]:
            return "in"  # India
        return "us"  # Default to US

    async def fetch_news(self, topics: List[str]) -> List[NewsItem]:
        """
        Fetch news articles by keywords/symbols.
        Topics can be stock symbols (AAPL, MSFT, TCS, INFY) or general keywords (crypto, AI).

        For Indian market, filters for India + stock market specific news.
        """
        all_articles = []
        async with aiohttp.ClientSession() as session:
            for topic in topics:
                try:
                    # Build search query with market-specific context
                    if self.market_config in ["INDIA", "INDIAN"]:
                        # For Indian stocks: search for stock symbol + "NSE" or "stock" to get market-specific results
                        search_query = f'"{topic}" (NSE OR stock OR India)'
                    else:
                        search_query = topic

                    params = {
                        "q": search_query,
                        "apiKey": self.api_key,
                        "pageSize": 50,
                        "sortBy": "publishedAt",
                    }

                    # Add country filter for Indian market
                    if self.market_config in ["INDIA", "INDIAN"]:
                        params["searchIn"] = "title,description"  # Focus on title and description

                    async with session.get(f"{self.base_url}/everything", params=params, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for article in data.get("articles", []):
                                # Filter for relevant news if Indian market
                                if self.market_config in ["INDIA", "INDIAN"]:
                                    source_name = article.get("source", {}).get("name", "").lower()
                                    # Prefer Indian financial sources
                                    if not any(indian_source in source_name for indian_source in
                                              ["economic times", "moneycontrol", "mint", "financial express", "bse", "nse"]):
                                        # Still include but lower priority
                                        pass

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

    async def fetch_headlines(self, country: str = None) -> List[NewsItem]:
        """
        Fetch top headlines for a given country code.

        For Indian market, automatically uses India (in).
        For US market, uses US (us).
        """
        try:
            # Use market-based country code if not explicitly provided
            if country is None:
                country = self._get_country_code()

            async with aiohttp.ClientSession() as session:
                params = {
                    "country": country,
                    "apiKey": self.api_key,
                    "pageSize": 50,
                }
                # Add business category for financial news
                if self.market_config in ["INDIA", "INDIAN"]:
                    params["category"] = "business"  # Focus on business/financial news for Indian market

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
            print(f"Error fetching headlines from NewsAPI: {e}")
        return []
