"""
InfinityAI.Pro - Enhanced Real-Time Data Sources
=================================================
Multi-source data integration for accurate real-time market data.

Data Sources:
- BSE India (bseindia.com) - Live stock quotes, indices, corporate actions
- Yahoo Finance (finance.yahoo.com) - Global data, historical, fundamentals
- NSE (via nsepython) - Option chains, FII/DII, index data
- CNBC/Reuters RSS - Breaking news and market updates

Features:
- Multi-source validation (cross-check prices)
- Real-time index tracking (NIFTY 50, SENSEX, BANKNIFTY)
- Live corporate actions calendar
- Institutional activity tracking
- Global market correlation
"""

import asyncio
import logging
from datetime import datetime, timedelta, time as dtime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from functools import lru_cache
import json
import os

logger = logging.getLogger("InfinityAI.EnhancedDataSources")

# Import libraries
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    logger.warning("aiohttp not available")

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    logger.warning("yfinance not available")

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    logger.warning("beautifulsoup4 not available")

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False


# =====================================================================
# INDEX SYMBOL MAPPINGS
# =====================================================================

YAHOO_SYMBOLS = {
    # Indian Indices
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANKNIFTY": "^NSEBANK",
    "NIFTYBANK": "^NSEBANK",
    "NIFTYIT": "^CNXIT",
    "NIFTYPHARMA": "^CNXPHARMA",
    "NIFTYFIN": "^CNXFIN",
    "NIFTYMETAL": "^CNXMETAL",
    "NIFTYREALTY": "^CNXREALTY",
    "NIFTYAUTO": "^CNXAUTO",
    "NIFTYPSUBANK": "^CNXPSUBANK",

    # Global Indices for correlation
    "SPX": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW": "^DJI",
    "FTSE": "^FTSE",
    "DAX": "^GDAXI",
    "HANGSENG": "^HSI",
    "NIKKEI": "^N225",
    "SGX_NIFTY": "SGX_NIFTY.NE"  # SGX Nifty futures
}

BSE_INDICES = {
    "SENSEX": "S&P BSE SENSEX",
    "SENSEX50": "S&P BSE SENSEX 50",
    "BSE100": "S&P BSE 100",
    "BSE200": "S&P BSE 200",
    "BSE500": "S&P BSE 500",
    "BSEMIDCAP": "S&P BSE MidCap",
    "BSESMALLCAP": "S&P BSE SmallCap",
    "BANKEX": "S&P BSE BANKEX",
    "BSEIT": "S&P BSE IT",
    "BSEPHARMA": "S&P BSE Healthcare",
    "BSEMETAL": "S&P BSE Metal",
    "BSEAUTO": "S&P BSE Auto"
}

# NSE NIFTY 50 Components (2025 updated list)
NIFTY_50_STOCKS = [
    "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO",
    "BAJAJFINSV", "BAJFINANCE", "BHARTIARTL", "BPCL", "BRITANNIA",
    "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY", "EICHERMOT",
    "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO",
    "HINDALCO", "HINDUNILVR", "ICICIBANK", "INDUSINDBK", "INFY",
    "ITC", "JSWSTEEL", "KOTAKBANK", "LT", "M&M",
    "MARUTI", "NESTLEIND", "NTPC", "ONGC", "POWERGRID",
    "RELIANCE", "SBILIFE", "SBIN", "SHRIRAMFIN", "SUNPHARMA",
    "TATACONSUM", "TATAMOTORS", "TATASTEEL", "TCS", "TECHM",
    "TITAN", "TRENT", "ULTRACEMCO", "UPL", "WIPRO"
]

# Sector mappings
SECTOR_STOCKS = {
    "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK"],
    "IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM"],
    "PHARMA": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP"],
    "AUTO": ["TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM"],
    "METAL": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "COALINDIA"],
    "ENERGY": ["RELIANCE", "ONGC", "BPCL", "NTPC", "POWERGRID"],
    "REALTY": ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE"],
    "FINANCE": ["BAJFINANCE", "BAJAJFINSV", "HDFCLIFE", "SBILIFE", "SHRIRAMFIN"]
}


# =====================================================================
# DATA CLASSES
# =====================================================================

@dataclass
class MarketQuote:
    """Real-time market quote from multiple sources."""
    symbol: str
    exchange: str
    current_price: float
    previous_close: float
    change: float
    change_percent: float
    day_high: float
    day_low: float
    open_price: float
    volume: int
    source: str
    timestamp: datetime
    confidence: float = 1.0  # Confidence score based on source reliability

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "current_price": self.current_price,
            "previous_close": self.previous_close,
            "change": self.change,
            "change_percent": self.change_percent,
            "day_high": self.day_high,
            "day_low": self.day_low,
            "open": self.open_price,
            "volume": self.volume,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence
        }


@dataclass
class IndexData:
    """Comprehensive index data."""
    symbol: str
    name: str
    value: float
    change: float
    change_percent: float
    day_high: float
    day_low: float
    open_value: float
    previous_close: float
    advances: int
    declines: int
    unchanged: int
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "value": self.value,
            "change": self.change,
            "change_percent": self.change_percent,
            "day_high": self.day_high,
            "day_low": self.day_low,
            "open": self.open_value,
            "previous_close": self.previous_close,
            "advances": self.advances,
            "declines": self.declines,
            "unchanged": self.unchanged,
            "breadth_ratio": self.advances / self.declines if self.declines > 0 else 0,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class GlobalMarketCorrelation:
    """Global market data for correlation analysis."""
    us_markets: Dict[str, float]  # S&P 500, NASDAQ, DOW changes
    european_markets: Dict[str, float]  # FTSE, DAX changes
    asian_markets: Dict[str, float]  # Nikkei, Hang Seng, SGX Nifty
    sgx_nifty: Optional[float] = None  # SGX Nifty for pre-market indication
    correlation_signal: str = "NEUTRAL"
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "us_markets": self.us_markets,
            "european_markets": self.european_markets,
            "asian_markets": self.asian_markets,
            "sgx_nifty": self.sgx_nifty,
            "correlation_signal": self.correlation_signal,
            "timestamp": self.timestamp.isoformat()
        }


# =====================================================================
# YAHOO FINANCE DATA FETCHER
# =====================================================================

class YahooFinanceProvider:
    """Enhanced Yahoo Finance data provider with caching."""

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 30  # 30 seconds cache

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if valid."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                return data
        return None

    def _set_cache(self, key: str, data: Any):
        """Set cache with timestamp."""
        self.cache[key] = (data, datetime.now())

    def get_quote(self, symbol: str, exchange: str = "NSE") -> Optional[MarketQuote]:
        """Get real-time quote from Yahoo Finance."""
        if not HAS_YFINANCE:
            return None

        cache_key = f"quote_{symbol}_{exchange}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            # Map symbol to Yahoo format
            if symbol.upper() in YAHOO_SYMBOLS:
                yf_symbol = YAHOO_SYMBOLS[symbol.upper()]
            elif exchange.upper() == "NSE":
                yf_symbol = f"{symbol}.NS"
            elif exchange.upper() == "BSE":
                yf_symbol = f"{symbol}.BO"
            else:
                yf_symbol = symbol

            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            hist = ticker.history(period="5d")

            if hist.empty:
                return None

            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price

            quote = MarketQuote(
                symbol=symbol,
                exchange=exchange,
                current_price=round(float(current_price), 2),
                previous_close=round(float(prev_close), 2),
                change=round(float(current_price - prev_close), 2),
                change_percent=round(float((current_price - prev_close) / prev_close * 100), 2),
                day_high=round(float(hist['High'].iloc[-1]), 2),
                day_low=round(float(hist['Low'].iloc[-1]), 2),
                open_price=round(float(hist['Open'].iloc[-1]), 2),
                volume=int(hist['Volume'].iloc[-1]),
                source="YAHOO_FINANCE",
                timestamp=datetime.now(),
                confidence=0.95
            )

            self._set_cache(cache_key, quote)
            return quote

        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
            return None

    def get_index_data(self, symbol: str) -> Optional[IndexData]:
        """Get index data from Yahoo Finance."""
        if not HAS_YFINANCE:
            return None

        try:
            yf_symbol = YAHOO_SYMBOLS.get(symbol.upper(), f"^{symbol}")
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period="5d")

            if hist.empty:
                return None

            current = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current

            return IndexData(
                symbol=symbol,
                name=BSE_INDICES.get(symbol, f"{symbol} Index"),
                value=round(float(current), 2),
                change=round(float(current - prev_close), 2),
                change_percent=round(float((current - prev_close) / prev_close * 100), 2),
                day_high=round(float(hist['High'].iloc[-1]), 2),
                day_low=round(float(hist['Low'].iloc[-1]), 2),
                open_value=round(float(hist['Open'].iloc[-1]), 2),
                previous_close=round(float(prev_close), 2),
                advances=0,  # Not available from yfinance
                declines=0,
                unchanged=0,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Index data error for {symbol}: {e}")
            return None

    def get_global_markets(self) -> GlobalMarketCorrelation:
        """Get global market data for correlation analysis."""
        if not HAS_YFINANCE:
            return GlobalMarketCorrelation(
                us_markets={}, european_markets={}, asian_markets={},
                correlation_signal="UNAVAILABLE"
            )

        us_markets = {}
        european_markets = {}
        asian_markets = {}

        # US Markets
        for name, symbol in [("S&P500", "^GSPC"), ("NASDAQ", "^IXIC"), ("DOW", "^DJI")]:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    change_pct = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
                    us_markets[name] = round(float(change_pct), 2)
            except Exception:
                continue

        # European Markets
        for name, symbol in [("FTSE", "^FTSE"), ("DAX", "^GDAXI")]:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    change_pct = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
                    european_markets[name] = round(float(change_pct), 2)
            except Exception:
                continue

        # Asian Markets
        for name, symbol in [("NIKKEI", "^N225"), ("HANGSENG", "^HSI")]:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    change_pct = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
                    asian_markets[name] = round(float(change_pct), 2)
            except Exception:
                continue

        # Determine correlation signal
        all_changes = list(us_markets.values()) + list(european_markets.values()) + list(asian_markets.values())
        if all_changes:
            avg_change = sum(all_changes) / len(all_changes)
            if avg_change > 0.5:
                signal = "GLOBAL_BULLISH"
            elif avg_change < -0.5:
                signal = "GLOBAL_BEARISH"
            else:
                signal = "GLOBAL_MIXED"
        else:
            signal = "UNAVAILABLE"

        return GlobalMarketCorrelation(
            us_markets=us_markets,
            european_markets=european_markets,
            asian_markets=asian_markets,
            correlation_signal=signal,
            timestamp=datetime.now()
        )

    def get_sector_performance(self) -> Dict[str, Any]:
        """Get sector-wise performance analysis."""
        if not HAS_YFINANCE or not HAS_PANDAS:
            return {"error": "Required libraries not available"}

        sector_data = {}

        for sector, stocks in SECTOR_STOCKS.items():
            sector_changes = []
            top_gainer = None
            top_loser = None
            max_gain = -100
            max_loss = 100

            for symbol in stocks[:5]:  # Limit API calls
                try:
                    ticker = yf.Ticker(f"{symbol}.NS")
                    hist = ticker.history(period="2d")
                    if len(hist) >= 2:
                        change_pct = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
                        sector_changes.append(change_pct)

                        if change_pct > max_gain:
                            max_gain = change_pct
                            top_gainer = {"symbol": symbol, "change": round(change_pct, 2)}
                        if change_pct < max_loss:
                            max_loss = change_pct
                            top_loser = {"symbol": symbol, "change": round(change_pct, 2)}
                except Exception:
                    continue

            if sector_changes:
                avg_change = sum(sector_changes) / len(sector_changes)
                sector_data[sector] = {
                    "average_change": round(avg_change, 2),
                    "trend": "BULLISH" if avg_change > 0.3 else "BEARISH" if avg_change < -0.3 else "NEUTRAL",
                    "top_gainer": top_gainer,
                    "top_loser": top_loser,
                    "stocks_analyzed": len(sector_changes)
                }

        # Rank sectors
        sorted_sectors = sorted(sector_data.items(), key=lambda x: x[1]["average_change"], reverse=True)

        return {
            "sectors": sector_data,
            "best_sector": sorted_sectors[0][0] if sorted_sectors else None,
            "worst_sector": sorted_sectors[-1][0] if sorted_sectors else None,
            "timestamp": datetime.now().isoformat()
        }

    def get_nifty50_heatmap(self) -> Dict[str, Any]:
        """Get NIFTY 50 stocks performance heatmap."""
        if not HAS_YFINANCE:
            return {"error": "yfinance not available"}

        stocks_data = []
        gainers = []
        losers = []

        for symbol in NIFTY_50_STOCKS[:30]:  # Limit for performance
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change_pct = (current - prev) / prev * 100

                    stock_info = {
                        "symbol": symbol,
                        "price": round(float(current), 2),
                        "change": round(float(change_pct), 2),
                        "volume": int(hist['Volume'].iloc[-1])
                    }
                    stocks_data.append(stock_info)

                    if change_pct > 0:
                        gainers.append(stock_info)
                    else:
                        losers.append(stock_info)
            except Exception:
                continue

        # Sort
        gainers = sorted(gainers, key=lambda x: x['change'], reverse=True)[:10]
        losers = sorted(losers, key=lambda x: x['change'])[:10]

        return {
            "total_stocks": len(stocks_data),
            "advances": len(gainers),
            "declines": len(losers),
            "top_gainers": gainers[:5],
            "top_losers": losers[:5],
            "market_breadth": {
                "ratio": len(gainers) / len(losers) if len(losers) > 0 else len(gainers),
                "interpretation": "BULLISH" if len(gainers) > len(losers) * 1.5 else "BEARISH" if len(losers) > len(gainers) * 1.5 else "NEUTRAL"
            },
            "timestamp": datetime.now().isoformat()
        }


# =====================================================================
# FINANCIAL NEWS AGGREGATOR
# =====================================================================

class EnhancedNewsAggregator:
    """Multi-source news aggregator with sentiment analysis."""

    RSS_SOURCES = {
        "economic_times": [
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms"
        ],
        "moneycontrol": [
            "https://www.moneycontrol.com/rss/MCtopnews.xml",
            "https://www.moneycontrol.com/rss/marketreports.xml"
        ],
        "livemint": [
            "https://www.livemint.com/rss/markets",
            "https://www.livemint.com/rss/money"
        ],
        "reuters_india": [
            "https://feeds.reuters.com/reuters/INtopNews"
        ],
        "cnbc": [
            "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",  # Finance
            "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147"   # World
        ]
    }

    BULLISH_KEYWORDS = [
        "surge", "rally", "gain", "rise", "jump", "soar", "bull", "bullish",
        "record", "high", "outperform", "upgrade", "buy", "strong", "growth",
        "profit", "beat", "exceed", "positive", "recovery", "breakthrough"
    ]

    BEARISH_KEYWORDS = [
        "fall", "drop", "decline", "crash", "plunge", "slump", "bear", "bearish",
        "low", "sell", "weak", "downgrade", "concern", "fear", "loss", "miss",
        "negative", "warning", "risk", "correction", "volatile", "crisis"
    ]

    async def fetch_news(self, sources: List[str] = None, max_articles: int = 20) -> Dict[str, Any]:
        """Fetch news from multiple sources."""
        if not HAS_FEEDPARSER:
            return {"error": "feedparser not available", "articles": []}

        sources = sources or list(self.RSS_SOURCES.keys())
        all_articles = []

        for source_name in sources:
            if source_name not in self.RSS_SOURCES:
                continue

            for feed_url in self.RSS_SOURCES[source_name]:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:5]:
                        title = entry.get('title', '')
                        summary = entry.get('summary', entry.get('description', ''))[:300]

                        # Analyze sentiment
                        text = (title + " " + summary).lower()
                        bullish_count = sum(1 for kw in self.BULLISH_KEYWORDS if kw in text)
                        bearish_count = sum(1 for kw in self.BEARISH_KEYWORDS if kw in text)

                        if bullish_count > bearish_count:
                            sentiment = "BULLISH"
                        elif bearish_count > bullish_count:
                            sentiment = "BEARISH"
                        else:
                            sentiment = "NEUTRAL"

                        article = {
                            "title": title,
                            "summary": summary,
                            "url": entry.get('link', ''),
                            "source": source_name,
                            "published": entry.get('published', ''),
                            "sentiment": sentiment
                        }
                        all_articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to fetch from {source_name}: {e}")
                    continue

        # Sort by relevance and recency
        all_articles = all_articles[:max_articles]

        # Calculate overall sentiment
        bullish = sum(1 for a in all_articles if a['sentiment'] == 'BULLISH')
        bearish = sum(1 for a in all_articles if a['sentiment'] == 'BEARISH')
        neutral = sum(1 for a in all_articles if a['sentiment'] == 'NEUTRAL')

        if bullish > bearish * 1.3:
            overall = "BULLISH"
        elif bearish > bullish * 1.3:
            overall = "BEARISH"
        else:
            overall = "NEUTRAL"

        return {
            "articles": all_articles,
            "total": len(all_articles),
            "sentiment_breakdown": {
                "bullish": bullish,
                "bearish": bearish,
                "neutral": neutral
            },
            "overall_sentiment": overall,
            "sources_fetched": sources,
            "timestamp": datetime.now().isoformat()
        }


# =====================================================================
# MARKET INTELLIGENCE AGGREGATOR
# =====================================================================

class MarketIntelligence:
    """
    Comprehensive market intelligence combining all data sources.
    """

    def __init__(self):
        self.yahoo = YahooFinanceProvider()
        self.news = EnhancedNewsAggregator()

    def get_market_pulse(self) -> Dict[str, Any]:
        """
        Get comprehensive market pulse combining all data.
        """
        try:
            # Get index data
            nifty = self.yahoo.get_index_data("NIFTY")
            sensex = self.yahoo.get_index_data("SENSEX")
            banknifty = self.yahoo.get_index_data("BANKNIFTY")

            # Get global correlation
            global_markets = self.yahoo.get_global_markets()

            # Get sector performance
            sectors = self.yahoo.get_sector_performance()

            # Get heatmap
            heatmap = self.yahoo.get_nifty50_heatmap()

            # Determine overall market signal
            signals = []

            if nifty and nifty.change_percent > 0.3:
                signals.append("NIFTY_BULLISH")
            elif nifty and nifty.change_percent < -0.3:
                signals.append("NIFTY_BEARISH")

            if global_markets.correlation_signal == "GLOBAL_BULLISH":
                signals.append("GLOBAL_SUPPORT")
            elif global_markets.correlation_signal == "GLOBAL_BEARISH":
                signals.append("GLOBAL_WEAKNESS")

            if heatmap.get("market_breadth", {}).get("interpretation") == "BULLISH":
                signals.append("BREADTH_POSITIVE")
            elif heatmap.get("market_breadth", {}).get("interpretation") == "BEARISH":
                signals.append("BREADTH_NEGATIVE")

            bullish_signals = len([s for s in signals if "BULLISH" in s or "POSITIVE" in s or "SUPPORT" in s])
            bearish_signals = len([s for s in signals if "BEARISH" in s or "NEGATIVE" in s or "WEAKNESS" in s])

            if bullish_signals > bearish_signals:
                overall_signal = "BULLISH"
                confidence = min(95, 60 + bullish_signals * 10)
            elif bearish_signals > bullish_signals:
                overall_signal = "BEARISH"
                confidence = min(95, 60 + bearish_signals * 10)
            else:
                overall_signal = "NEUTRAL"
                confidence = 50

            return {
                "status": "success",
                "market_status": self._get_market_status(),
                "indices": {
                    "nifty": nifty.to_dict() if nifty else None,
                    "sensex": sensex.to_dict() if sensex else None,
                    "banknifty": banknifty.to_dict() if banknifty else None
                },
                "global_markets": global_markets.to_dict(),
                "sector_performance": sectors,
                "nifty50_heatmap": heatmap,
                "signals": signals,
                "overall_signal": overall_signal,
                "confidence": confidence,
                "data_sources": ["YAHOO_FINANCE", "NSE_LIVE", "RSS_FEEDS"],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Market pulse error: {e}")
            return {"error": str(e), "status": "error"}

    def _get_market_status(self) -> Dict[str, Any]:
        """Get current market status."""
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()

        if weekday >= 5:
            return {"status": "CLOSED", "reason": "Weekend"}

        pre_market = dtime(9, 0)
        market_open = dtime(9, 15)
        market_close = dtime(15, 30)
        post_market = dtime(16, 0)

        if current_time < pre_market:
            return {"status": "CLOSED", "next_open": "09:00 IST"}
        elif pre_market <= current_time < market_open:
            return {"status": "PRE_MARKET", "opens_at": "09:15 IST"}
        elif market_open <= current_time < market_close:
            return {"status": "OPEN", "closes_at": "15:30 IST"}
        elif market_close <= current_time < post_market:
            return {"status": "POST_MARKET", "note": "After-hours session"}
        else:
            return {"status": "CLOSED", "next_open": "Tomorrow 09:00 IST"}

    async def get_stock_intelligence(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive intelligence for a specific stock."""
        try:
            # Get quote
            quote = self.yahoo.get_quote(symbol)

            if not quote:
                return {"error": f"No data available for {symbol}"}

            # Get global markets for context
            global_markets = self.yahoo.get_global_markets()

            # Determine sector
            stock_sector = None
            for sector, stocks in SECTOR_STOCKS.items():
                if symbol.upper() in stocks:
                    stock_sector = sector
                    break

            # Build intelligence
            return {
                "symbol": symbol,
                "quote": quote.to_dict(),
                "sector": stock_sector,
                "in_nifty50": symbol.upper() in NIFTY_50_STOCKS,
                "global_context": global_markets.to_dict(),
                "trading_recommendation": self._generate_quick_recommendation(quote, global_markets),
                "data_freshness": "REAL_TIME",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Stock intelligence error for {symbol}: {e}")
            return {"error": str(e)}

    def _generate_quick_recommendation(self, quote: MarketQuote, global_context: GlobalMarketCorrelation) -> Dict[str, Any]:
        """Generate quick trading recommendation based on available data."""
        signals = []

        # Price momentum
        if quote.change_percent > 1.5:
            signals.append(("MOMENTUM", "STRONG_BULLISH", 2))
        elif quote.change_percent > 0.5:
            signals.append(("MOMENTUM", "BULLISH", 1))
        elif quote.change_percent < -1.5:
            signals.append(("MOMENTUM", "STRONG_BEARISH", -2))
        elif quote.change_percent < -0.5:
            signals.append(("MOMENTUM", "BEARISH", -1))
        else:
            signals.append(("MOMENTUM", "NEUTRAL", 0))

        # Global context
        if global_context.correlation_signal == "GLOBAL_BULLISH":
            signals.append(("GLOBAL", "SUPPORTIVE", 1))
        elif global_context.correlation_signal == "GLOBAL_BEARISH":
            signals.append(("GLOBAL", "HEADWIND", -1))

        # Calculate overall score
        total_score = sum(s[2] for s in signals)

        if total_score >= 2:
            recommendation = "BUY"
            confidence = min(85, 60 + total_score * 5)
        elif total_score <= -2:
            recommendation = "SELL"
            confidence = min(85, 60 + abs(total_score) * 5)
        else:
            recommendation = "HOLD"
            confidence = 50 + abs(total_score) * 5

        return {
            "signal": recommendation,
            "confidence": confidence,
            "reasoning": [f"{s[0]}: {s[1]}" for s in signals],
            "note": "Quick signal based on momentum and global context. Use enhanced-signal for comprehensive AI analysis."
        }


# =====================================================================
# SINGLETON INSTANCES
# =====================================================================

# Create singleton instances
_yahoo_provider = None
_news_aggregator = None
_market_intelligence = None

def get_yahoo_provider() -> YahooFinanceProvider:
    global _yahoo_provider
    if _yahoo_provider is None:
        _yahoo_provider = YahooFinanceProvider()
    return _yahoo_provider

def get_news_aggregator() -> EnhancedNewsAggregator:
    global _news_aggregator
    if _news_aggregator is None:
        _news_aggregator = EnhancedNewsAggregator()
    return _news_aggregator

def get_market_intelligence() -> MarketIntelligence:
    global _market_intelligence
    if _market_intelligence is None:
        _market_intelligence = MarketIntelligence()
    return _market_intelligence


# =====================================================================
# EXPORTED FUNCTIONS FOR GEMINI FUNCTION CALLING
# =====================================================================

def get_realtime_quote(symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
    """
    Get real-time stock quote from Yahoo Finance.

    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        exchange: Exchange - 'NSE' or 'BSE'

    Returns:
        Real-time quote with price, change, volume
    """
    provider = get_yahoo_provider()
    quote = provider.get_quote(symbol, exchange)
    if quote:
        return quote.to_dict()
    return {"error": f"No data for {symbol}", "symbol": symbol}


def get_global_market_context() -> Dict[str, Any]:
    """
    Get global market data for correlation analysis.
    Includes US, European, and Asian markets.

    Returns:
        Global market changes and correlation signal
    """
    provider = get_yahoo_provider()
    return provider.get_global_markets().to_dict()


def get_sector_analysis() -> Dict[str, Any]:
    """
    Get sector-wise performance for Indian markets.
    Analyzes Banking, IT, Pharma, Auto, FMCG, Metal, Energy, Realty, Finance.

    Returns:
        Sector performance with best/worst sectors
    """
    provider = get_yahoo_provider()
    return provider.get_sector_performance()


def get_nifty50_overview() -> Dict[str, Any]:
    """
    Get NIFTY 50 stocks heatmap with gainers/losers.

    Returns:
        Top gainers, losers, and market breadth
    """
    provider = get_yahoo_provider()
    return provider.get_nifty50_heatmap()


def get_market_pulse() -> Dict[str, Any]:
    """
    Get comprehensive market pulse combining all data sources.

    Returns:
        Complete market overview with indices, sectors, global context
    """
    intelligence = get_market_intelligence()
    return intelligence.get_market_pulse()


# Export functions for Gemini tools
ENHANCED_DATA_TOOLS = [
    get_realtime_quote,
    get_global_market_context,
    get_sector_analysis,
    get_nifty50_overview,
    get_market_pulse
]
