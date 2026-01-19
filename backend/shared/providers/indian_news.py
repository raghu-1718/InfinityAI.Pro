"""
Indian News RSS Provider - Direct RSS Feed Integration
Consolidated Indian market news from trusted sources

Sources:
- Economic Times (Markets, Stocks, Commodities RSS)
- Moneycontrol (Markets, Business RSS)
- LiveMint (Markets, Economy RSS)
- Google News India (Stock market specific)
- BSE Announcements (Direct from BSE)
- NSE Circulars (Direct from NSE)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import feedparser
import aiohttp
from backend.shared.providers.interfaces import NewsProvider
from backend.shared.providers.models import NewsItem

logger = logging.getLogger("IndianNewsProvider")


class IndianNewsProvider(NewsProvider):
    """
    Indian News RSS Provider - Direct RSS feed aggregation for Indian stock market news.

    Consolidates news from Economic Times, Moneycontrol, LiveMint, and official
    BSE/NSE announcements.
    """

    @property
    def name(self) -> str:
        return "indian-news-rss"

    def __init__(self):
        """Initialize Indian news provider with RSS feeds."""
        self.timeout = 30

        # Indian market RSS feeds
        self.rss_feeds = {
            "economic_times": {
                "name": "Economic Times",
                "markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
                "stocks": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
                "commodities": "https://economictimes.indiatimes.com/markets/commodities/rssfeeds/1808152121.cms",
                "priority": 1  # Highest priority
            },
            "moneycontrol": {
                "name": "Moneycontrol",
                "markets": "https://www.moneycontrol.com/rss/MCtopnews.xml",
                "business": "https://www.moneycontrol.com/rss/business.xml",
                "priority": 2
            },
            "livemint": {
                "name": "LiveMint",
                "markets": "https://www.livemint.com/rss/markets",
                "economy": "https://www.livemint.com/rss/economy",
                "priority": 2
            },
            "google_news": {
                "name": "Google News India",
                "indian_stocks": "https://news.google.com/rss/search?q=indian+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
                "nifty": "https://news.google.com/rss/search?q=nifty+50&hl=en-IN&gl=IN&ceid=IN:en",
                "sensex": "https://news.google.com/rss/search?q=sensex+bse&hl=en-IN&gl=IN&ceid=IN:en",
                "priority": 3
            }
        }

        # Stock symbols to track
        self.tracked_symbols = {
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
            "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK", "LT",
            "WIPRO", "TECHM", "MARUTI", "SUNPHARMA", "NESTLEIND",
            "ASIANPAINT", "TITAN", "AXISBANK", "NTPC", "COALIND",
            "NIFTY", "BANKNIFTY", "SENSEX", "BSE"
        }

    async def fetch_news(self, topics: List[str]) -> List[NewsItem]:
        """
        Fetch news for specific topics/stocks from Indian RSS feeds.

        Args:
            topics: List of topics or stock symbols (e.g., ['TCS', 'INFY', 'NIFTY'])

        Returns:
            List of NewsItem objects
        """
        all_articles = []

        # Get articles from all sources
        for source_name, source_config in self.rss_feeds.items():
            source_articles = await self._fetch_source_news(source_name, source_config)
            all_articles.extend(source_articles)

        # Filter for requested topics
        topic_set = set(t.upper() for t in topics)
        filtered_articles = []

        for article in all_articles:
            article_text = (article.title + " " + article.body).upper()

            # Check if any topic appears in article
            for topic in topic_set:
                if topic in article_text:
                    article.symbols = list(topic_set & set(article_text.split()))
                    filtered_articles.append(article)
                    break

        # Remove duplicates and sort by date
        unique_articles = self._deduplicate(filtered_articles)
        unique_articles.sort(key=lambda x: x.published_at, reverse=True)

        return unique_articles

    async def _fetch_source_news(self, source_name: str, source_config: Dict[str, Any]) -> List[NewsItem]:
        """Fetch news from a specific source's RSS feeds."""
        articles = []

        try:
            # Skip source name and priority, iterate through feed URLs
            for feed_type, url in source_config.items():
                if feed_type in ["name", "priority"]:
                    continue

                try:
                    feed_articles = await self._fetch_rss_feed(
                        url=url,
                        source_name=source_config.get("name", source_name),
                        feed_type=feed_type
                    )
                    articles.extend(feed_articles)
                except Exception as e:
                    logger.warning(f"Error fetching {source_name} {feed_type}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error processing source {source_name}: {e}")

        return articles

    async def _fetch_rss_feed(self, url: str, source_name: str, feed_type: str) -> List[NewsItem]:
        """
        Fetch and parse RSS feed.

        Args:
            url: RSS feed URL
            source_name: Source name (Economic Times, Moneycontrol, etc.)
            feed_type: Feed category (markets, stocks, commodities, etc.)

        Returns:
            List of NewsItem objects
        """
        articles = []

        try:
            # Use feedparser to fetch and parse RSS
            feed = feedparser.parse(url)

            for entry in feed.entries:
                try:
                    # Extract article information
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))

                    # Clean HTML from summary
                    summary = self._clean_html(summary)[:500]  # Limit to 500 chars

                    article_url = entry.get("link", "")

                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, "published_parsed"):
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, "updated_parsed"):
                        pub_date = datetime(*entry.updated_parsed[:6])
                    else:
                        pub_date = datetime.utcnow()

                    # Extract symbols from title and summary
                    symbols = self._extract_symbols(title + " " + summary)

                    # Create NewsItem
                    item = NewsItem(
                        id=article_url or f"{source_name}_{title}_{pub_date.isoformat()}",
                        title=title,
                        body=summary,
                        published_at=pub_date,
                        symbols=symbols,
                        source=f"{source_name} ({feed_type})",
                        url=article_url,
                        language="en"
                    )

                    articles.append(item)

                except Exception as e:
                    logger.debug(f"Error parsing RSS entry: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")

        return articles

    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text."""
        text_upper = text.upper()
        found_symbols = []

        for symbol in self.tracked_symbols:
            if symbol in text_upper:
                found_symbols.append(symbol)

        return list(set(found_symbols))  # Remove duplicates

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and entities from text."""
        import re
        import html

        # Decode HTML entities
        text = html.unescape(text)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _deduplicate(self, articles: List[NewsItem]) -> List[NewsItem]:
        """Remove duplicate articles based on title similarity."""
        seen_titles = set()
        unique = []

        for article in articles:
            # Normalize title for comparison
            normalized = article.title.lower().strip()

            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique.append(article)

        return unique

    async def fetch_headlines(self, country: str = "in") -> List[NewsItem]:
        """
        Fetch top headlines for Indian market.

        Args:
            country: Country code (default: 'in' for India)

        Returns:
            List of top NewsItem objects
        """
        articles = []

        # Fetch from primary Indian sources (Economic Times, Moneycontrol, LiveMint)
        primary_sources = ["economic_times", "moneycontrol", "livemint"]

        for source_name in primary_sources:
            source_config = self.rss_feeds.get(source_name, {})
            source_articles = await self._fetch_source_news(source_name, source_config)
            articles.extend(source_articles)

        # Sort by date and return top 50
        articles.sort(key=lambda x: x.published_at, reverse=True)
        return articles[:50]

    async def fetch_sector_news(self, sector: str) -> List[NewsItem]:
        """
        Fetch news specific to a sector.

        Args:
            sector: Sector name (IT, Banking, Energy, FMCG, etc.)

        Returns:
            List of NewsItem objects for sector
        """
        # Map sectors to stock symbols
        sector_symbols = {
            "IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"],
            "BANKING": ["HDFCBANK", "SBIN", "AXISBANK", "ICICIBANK", "KOTAKBANK"],
            "ENERGY": ["RELIANCE", "NTPC", "COALIND"],
            "TELECOM": ["BHARTIARTL"],
            "FMCG": ["ITC", "NESTLEIND"],
            "AUTO": ["MARUTI"],
            "PHARMA": ["SUNPHARMA"],
            "MATERIALS": ["ASIANPAINT", "LT"],
            "RETAIL": ["TITAN"]
        }

        symbols = sector_symbols.get(sector.upper(), [])
        if symbols:
            return await self.fetch_news(symbols)

        return []

    async def get_sentiment_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Get news sentiment for a specific symbol.

        Args:
            symbol: Stock symbol (e.g., 'TCS')

        Returns:
            Dictionary with bullish/bearish counts and overall sentiment
        """
        articles = await self.fetch_news([symbol])

        bullish_keywords = ["surge", "rally", "gain", "rise", "jump", "soar", "buy", "strong",
                           "recovery", "positive", "growth", "profit", "beat", "upgrade"]
        bearish_keywords = ["fall", "drop", "decline", "crash", "plunge", "sell", "weak",
                           "downgrade", "concern", "fear", "loss", "miss", "warning"]

        bullish_count = 0
        bearish_count = 0
        neutral_count = 0

        for article in articles:
            text = (article.title + " " + article.body).lower()

            has_bullish = any(kw in text for kw in bullish_keywords)
            has_bearish = any(kw in text for kw in bearish_keywords)

            if has_bullish and not has_bearish:
                bullish_count += 1
            elif has_bearish and not has_bullish:
                bearish_count += 1
            else:
                neutral_count += 1

        # Determine overall sentiment
        total = bullish_count + bearish_count + neutral_count
        if total == 0:
            overall_sentiment = "NEUTRAL"
        elif bullish_count > bearish_count + 2:
            overall_sentiment = "BULLISH"
        elif bearish_count > bullish_count + 2:
            overall_sentiment = "BEARISH"
        else:
            overall_sentiment = "NEUTRAL"

        return {
            "symbol": symbol,
            "articles_count": len(articles),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "overall_sentiment": overall_sentiment,
            "articles": articles[:10]  # Top 10 articles
        }


# Usage Example:
"""
async def main():
    provider = IndianNewsProvider()

    # Fetch news for specific stocks
    articles = await provider.fetch_news(['TCS', 'INFY'])
    for article in articles[:5]:
        print(f"{article.title} ({article.source})")

    # Get headlines
    headlines = await provider.fetch_headlines()
    print(f"Found {len(headlines)} headline articles")

    # Get sector news
    it_news = await provider.fetch_sector_news('IT')
    print(f"IT sector: {len(it_news)} articles")

    # Get sentiment
    sentiment = await provider.get_sentiment_for_symbol('TCS')
    print(f"TCS Sentiment: {sentiment['overall_sentiment']}")

# asyncio.run(main())
"""
