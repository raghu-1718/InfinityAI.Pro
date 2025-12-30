"""
InfinityAI.Pro - News Integration for Market Sentiment
========================================================
Fetches real-time news from multiple sources for market sentiment analysis.

Sources:
- Google News RSS (Free)
- NewsAPI (API key required)
- Economic Times RSS
- Moneycontrol RSS

Features:
- Real-time market news fetching
- Sentiment classification
- Symbol-specific news filtering
- Multi-source aggregation
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import hashlib
import os

logger = logging.getLogger("InfinityAI.NewsIntegration")

# Try importing required libraries
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    logger.warning("aiohttp not available. Install with: pip install aiohttp")

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    logger.warning("feedparser not available. Install with: pip install feedparser")


# =====================================================================
# NEWS DATA CLASSES
# =====================================================================

@dataclass
class NewsArticle:
    """Represents a single news article."""
    id: str
    title: str
    summary: str
    url: str
    source: str
    published: datetime
    sentiment: str = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
    relevance: float = 0.0  # 0-1 relevance score
    symbols: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "source": self.source,
            "published": self.published.isoformat(),
            "sentiment": self.sentiment,
            "relevance": self.relevance,
            "symbols": self.symbols
        }


@dataclass
class NewsFeed:
    """Aggregated news feed."""
    articles: List[NewsArticle]
    overall_sentiment: str
    bullish_count: int
    bearish_count: int
    neutral_count: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "articles": [a.to_dict() for a in self.articles],
            "overall_sentiment": self.overall_sentiment,
            "bullish_count": self.bullish_count,
            "bearish_count": self.bearish_count,
            "neutral_count": self.neutral_count,
            "timestamp": self.timestamp.isoformat()
        }


# =====================================================================
# RSS FEED SOURCES
# =====================================================================

RSS_FEEDS = {
    "economic_times": {
        "markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "stocks": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
        "commodities": "https://economictimes.indiatimes.com/markets/commodities/rssfeeds/1808152121.cms"
    },
    "moneycontrol": {
        "markets": "https://www.moneycontrol.com/rss/MCtopnews.xml",
        "business": "https://www.moneycontrol.com/rss/business.xml"
    },
    "livemint": {
        "markets": "https://www.livemint.com/rss/markets",
        "economy": "https://www.livemint.com/rss/economy"
    },
    "google_news": {
        "indian_stocks": "https://news.google.com/rss/search?q=indian+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
        "nifty": "https://news.google.com/rss/search?q=nifty+50&hl=en-IN&gl=IN&ceid=IN:en",
        "sensex": "https://news.google.com/rss/search?q=sensex+bse&hl=en-IN&gl=IN&ceid=IN:en"
    }
}

# Sentiment keywords
BULLISH_KEYWORDS = [
    "surge", "rally", "gain", "rise", "jump", "soar", "bull", "bullish",
    "record high", "new high", "outperform", "upgrade", "buy", "strong",
    "recovery", "positive", "growth", "profit", "beat", "exceed"
]

BEARISH_KEYWORDS = [
    "fall", "drop", "decline", "crash", "plunge", "slump", "bear", "bearish",
    "low", "sell", "weak", "downgrade", "concern", "fear", "loss", "miss",
    "negative", "warning", "risk", "correction", "volatile"
]

# Major stock keywords for relevance
STOCK_KEYWORDS = {
    "RELIANCE": ["reliance", "ril", "jio", "mukesh ambani"],
    "TCS": ["tcs", "tata consultancy", "tata tech"],
    "HDFCBANK": ["hdfc bank", "hdfc", "sashidhar jagdishan"],
    "INFY": ["infosys", "infy", "salil parekh"],
    "ICICIBANK": ["icici bank", "icici"],
    "SBIN": ["sbi", "state bank", "state bank of india"],
    "BHARTIARTL": ["bharti airtel", "airtel", "sunil mittal"],
    "ITC": ["itc", "itc limited"],
    "KOTAKBANK": ["kotak", "kotak mahindra"],
    "LT": ["l&t", "larsen", "larsen toubro"],
    "NIFTY": ["nifty", "nifty 50", "nifty50", "nifty index"],
    "BANKNIFTY": ["bank nifty", "banknifty", "nifty bank"],
    "SENSEX": ["sensex", "bse sensex", "bse index"]
}


# =====================================================================
# NEWS FETCHER
# =====================================================================

class NewsAggregator:
    """Aggregates news from multiple sources."""

    def __init__(self, cache_duration_minutes: int = 5):
        """Initialize the news aggregator."""
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self._cache: Dict[str, tuple] = {}  # (articles, timestamp)
        self._newsapi_key = os.getenv("NEWSAPI_KEY")

        logger.info("NewsAggregator initialized")

    async def fetch_all_news(
        self,
        categories: List[str] = None,
        max_articles: int = 50
    ) -> NewsFeed:
        """
        Fetch news from all configured sources.

        Args:
            categories: Specific categories to fetch ('markets', 'economy', etc.)
            max_articles: Maximum number of articles to return

        Returns:
            Aggregated NewsFeed
        """
        if categories is None:
            categories = ["markets", "stocks", "nifty"]

        all_articles = []

        # Fetch from RSS feeds
        if HAS_FEEDPARSER:
            for source, feeds in RSS_FEEDS.items():
                for category, url in feeds.items():
                    if any(cat.lower() in category.lower() for cat in categories) or \
                       any(cat.lower() in url.lower() for cat in categories):
                        articles = await self._fetch_rss(url, source)
                        all_articles.extend(articles)

        # Fetch from NewsAPI if available
        if self._newsapi_key and HAS_AIOHTTP:
            api_articles = await self._fetch_newsapi(categories)
            all_articles.extend(api_articles)

        # Deduplicate by title similarity
        unique_articles = self._deduplicate(all_articles)

        # Sort by published date (newest first)
        unique_articles.sort(key=lambda x: x.published, reverse=True)

        # Limit to max_articles
        unique_articles = unique_articles[:max_articles]

        # Calculate overall sentiment
        bullish = sum(1 for a in unique_articles if a.sentiment == "BULLISH")
        bearish = sum(1 for a in unique_articles if a.sentiment == "BEARISH")
        neutral = sum(1 for a in unique_articles if a.sentiment == "NEUTRAL")

        if bullish > bearish + 3:
            overall = "BULLISH"
        elif bearish > bullish + 3:
            overall = "BEARISH"
        else:
            overall = "NEUTRAL"

        return NewsFeed(
            articles=unique_articles,
            overall_sentiment=overall,
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral
        )

    async def fetch_symbol_news(
        self,
        symbol: str,
        max_articles: int = 20
    ) -> NewsFeed:
        """
        Fetch news specific to a stock symbol.

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'NIFTY')
            max_articles: Maximum articles to return

        Returns:
            NewsFeed with symbol-specific news
        """
        # Build Google News search URL
        keywords = STOCK_KEYWORDS.get(symbol.upper(), [symbol.lower()])
        search_query = "+".join(keywords[:2])
        url = f"https://news.google.com/rss/search?q={search_query}+stock&hl=en-IN&gl=IN&ceid=IN:en"

        articles = []

        if HAS_FEEDPARSER:
            articles = await self._fetch_rss(url, "google_news")

        # Also check cached general news for this symbol
        all_news = await self.fetch_all_news(["markets", "stocks"])
        symbol_related = [
            a for a in all_news.articles
            if symbol.upper() in a.symbols or
            any(kw.lower() in a.title.lower() for kw in keywords)
        ]
        articles.extend(symbol_related)

        # Deduplicate and limit
        unique = self._deduplicate(articles)[:max_articles]

        bullish = sum(1 for a in unique if a.sentiment == "BULLISH")
        bearish = sum(1 for a in unique if a.sentiment == "BEARISH")
        neutral = sum(1 for a in unique if a.sentiment == "NEUTRAL")

        if bullish > bearish + 2:
            overall = "BULLISH"
        elif bearish > bullish + 2:
            overall = "BEARISH"
        else:
            overall = "NEUTRAL"

        return NewsFeed(
            articles=unique,
            overall_sentiment=overall,
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral
        )

    async def _fetch_rss(
        self,
        url: str,
        source: str
    ) -> List[NewsArticle]:
        """Fetch and parse RSS feed."""
        cache_key = hashlib.md5(url.encode()).hexdigest()

        # Check cache
        if cache_key in self._cache:
            articles, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return articles

        try:
            # Use asyncio to run feedparser
            feed = await asyncio.to_thread(feedparser.parse, url)

            articles = []
            for entry in feed.entries[:20]:  # Limit per feed
                # Parse published date
                published = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except:
                        pass

                # Get summary
                summary = ""
                if hasattr(entry, 'summary'):
                    summary = self._clean_html(entry.summary)[:300]
                elif hasattr(entry, 'description'):
                    summary = self._clean_html(entry.description)[:300]

                # Create article
                article = NewsArticle(
                    id=hashlib.md5(entry.title.encode()).hexdigest()[:12],
                    title=entry.title,
                    summary=summary,
                    url=entry.link if hasattr(entry, 'link') else "",
                    source=source,
                    published=published
                )

                # Analyze sentiment
                article.sentiment = self._analyze_sentiment(article.title + " " + article.summary)

                # Find related symbols
                article.symbols = self._find_symbols(article.title + " " + article.summary)

                articles.append(article)

            # Update cache
            self._cache[cache_key] = (articles, datetime.now())

            return articles

        except Exception as e:
            logger.error(f"Error fetching RSS from {url}: {e}")
            return []

    async def _fetch_newsapi(
        self,
        categories: List[str]
    ) -> List[NewsArticle]:
        """Fetch from NewsAPI."""
        if not self._newsapi_key or not HAS_AIOHTTP:
            return []

        articles = []

        try:
            # Build query
            query = " OR ".join([f'"{cat}"' for cat in categories])
            url = (
                f"https://newsapi.org/v2/everything?"
                f"q=({query}) AND (indian stock market OR NSE OR BSE)&"
                f"language=en&sortBy=publishedAt&"
                f"apiKey={self._newsapi_key}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()

                        for item in data.get("articles", [])[:20]:
                            published = datetime.now()
                            if item.get("publishedAt"):
                                try:
                                    published = datetime.fromisoformat(
                                        item["publishedAt"].replace("Z", "+00:00")
                                    )
                                except:
                                    pass

                            article = NewsArticle(
                                id=hashlib.md5(item["title"].encode()).hexdigest()[:12],
                                title=item["title"],
                                summary=item.get("description", "")[:300],
                                url=item.get("url", ""),
                                source=item.get("source", {}).get("name", "NewsAPI"),
                                published=published
                            )

                            article.sentiment = self._analyze_sentiment(
                                article.title + " " + article.summary
                            )
                            article.symbols = self._find_symbols(
                                article.title + " " + article.summary
                            )

                            articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")

        return articles

    def _analyze_sentiment(self, text: str) -> str:
        """Simple keyword-based sentiment analysis."""
        text_lower = text.lower()

        bullish_score = sum(1 for kw in BULLISH_KEYWORDS if kw in text_lower)
        bearish_score = sum(1 for kw in BEARISH_KEYWORDS if kw in text_lower)

        if bullish_score > bearish_score + 1:
            return "BULLISH"
        elif bearish_score > bullish_score + 1:
            return "BEARISH"
        return "NEUTRAL"

    def _find_symbols(self, text: str) -> List[str]:
        """Find stock symbols mentioned in text."""
        text_lower = text.lower()
        found = []

        for symbol, keywords in STOCK_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                found.append(symbol)

        return list(set(found))

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def _deduplicate(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles by title similarity."""
        seen_titles = set()
        unique = []

        for article in articles:
            # Normalize title for comparison
            title_key = re.sub(r'[^a-z0-9]', '', article.title.lower())[:50]

            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique.append(article)

        return unique


# =====================================================================
# CONVENIENCE FUNCTIONS FOR GEMINI TOOLS
# =====================================================================

def get_market_news_live(category: str = "markets") -> Dict[str, Any]:
    """
    Get live market news for Gemini function calling.

    Args:
        category: News category ('markets', 'stocks', 'economy', 'global')

    Returns:
        Dict with news articles and sentiment
    """
    async def _fetch():
        aggregator = NewsAggregator()
        feed = await aggregator.fetch_all_news([category])
        return feed.to_dict()

    try:
        return asyncio.run(_fetch())
    except Exception as e:
        return {"error": str(e)}


def get_symbol_news_live(symbol: str) -> Dict[str, Any]:
    """
    Get live news for a specific symbol.

    Args:
        symbol: Stock symbol (e.g., 'RELIANCE')

    Returns:
        Dict with symbol-specific news
    """
    async def _fetch():
        aggregator = NewsAggregator()
        feed = await aggregator.fetch_symbol_news(symbol)
        return feed.to_dict()

    try:
        return asyncio.run(_fetch())
    except Exception as e:
        return {"error": str(e)}


# =====================================================================
# TESTING
# =====================================================================

if __name__ == "__main__":
    async def test_news():
        print("=" * 60)
        print("InfinityAI.Pro - News Integration Test")
        print("=" * 60)

        aggregator = NewsAggregator()

        # Test general market news
        print("\n📰 Fetching Market News...")
        feed = await aggregator.fetch_all_news(["markets", "stocks"])
        print(f"Total articles: {len(feed.articles)}")
        print(f"Overall sentiment: {feed.overall_sentiment}")
        print(f"Bullish: {feed.bullish_count}, Bearish: {feed.bearish_count}, Neutral: {feed.neutral_count}")

        print("\nTop 5 headlines:")
        for article in feed.articles[:5]:
            print(f"  [{article.sentiment}] {article.title[:60]}...")

        # Test symbol-specific news
        print("\n📈 Fetching RELIANCE News...")
        ril_feed = await aggregator.fetch_symbol_news("RELIANCE")
        print(f"RELIANCE articles: {len(ril_feed.articles)}")
        print(f"Sentiment: {ril_feed.overall_sentiment}")

        for article in ril_feed.articles[:3]:
            print(f"  [{article.sentiment}] {article.title[:60]}...")

    asyncio.run(test_news())
