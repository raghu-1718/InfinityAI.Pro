import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import aiohttp
from .interfaces import NewsProvider
from .models import NewsItem

class NewsAPIAIProvider(NewsProvider):
    """NewsAPI.ai (Event Registry) - semantic news search with events and concepts."""
    
    @property
    def name(self) -> str:
        return "newsapi-ai"
    
    def __init__(self):
        self.api_key = os.getenv("PROVIDER_NEWSAPI_AI_API_KEY")
        self.base_url = "https://eventregistry.org/api/v1"
        self.timeout = 30
        if not self.api_key:
            raise RuntimeError("PROVIDER_NEWSAPI_AI_API_KEY not set in environment")
    
    async def fetch_news(self, topics: List[str]) -> List[NewsItem]:
        """
        Fetch articles with semantic understanding.
        Supports concepts, sentiment, and event detection.
        Free: 2000 tokens/day; Rate: 5 concurrent requests max.
        """
        all_articles = []
        async with aiohttp.ClientSession() as session:
            for topic in topics:
                try:
                    params = {
                        "action": "getArticles",
                        "keyword": topic,
                        "apiKey": self.api_key,
                        "resultType": "articles",
                        "sortBy": "date",
                        "maxItems": 50,
                        "lang": "eng",
                    }
                    async with session.get(self.base_url, params=params, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for article in data.get("articles", {}).get("results", []):
                                item = NewsItem(
                                    id=article.get("id", ""),
                                    title=article.get("title", ""),
                                    body=article.get("body", ""),
                                    published_at=datetime.fromisoformat(article.get("dateTime", "").replace("Z", "+00:00")),
                                    symbols=[topic],
                                    source=article.get("source", {}).get("title", "Unknown"),
                                    url=article.get("url"),
                                    language="en",
                                )
                                all_articles.append(item)
                except Exception as e:
                    print(f"Error fetching news for {topic} from NewsAPI.ai: {e}")
                    await asyncio.sleep(1)  # Respect rate limits (5 concurrent max)
        return all_articles
    
    async def fetch_events(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch events (groupings of related articles) with semantic understanding.
        Useful for tracking market-moving events.
        """
        all_events = []
        async with aiohttp.ClientSession() as session:
            for keyword in keywords:
                try:
                    params = {
                        "action": "getEvents",
                        "keyword": keyword,
                        "apiKey": self.api_key,
                        "resultType": "events",
                        "sortBy": "date",
                        "maxItems": 20,
                        "lang": "eng",
                    }
                    async with session.get(self.base_url, params=params, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for event in data.get("events", {}).get("results", []):
                                all_events.append({
                                    "id": event.get("id"),
                                    "title": event.get("title"),
                                    "summary": event.get("summary"),
                                    "concepts": event.get("concepts", []),
                                    "article_count": event.get("articleCount"),
                                    "date": event.get("eventDate"),
                                })
                except Exception as e:
                    print(f"Error fetching events for {keyword}: {e}")
                    await asyncio.sleep(1)
        return all_events
