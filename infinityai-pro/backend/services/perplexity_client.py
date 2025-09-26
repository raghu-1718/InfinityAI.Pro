# perplexity_client.py
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NewsSentiment:
    """News sentiment analysis result"""
    headline: str
    sentiment: str  # positive, negative, neutral
    confidence: float
    source: str
    timestamp: datetime
    relevance_score: float
    key_entities: List[str]

@dataclass
class MarketIntelligence:
    """Market intelligence from Perplexity"""
    symbol: str
    news_items: List[NewsSentiment]
    overall_sentiment: str
    sentiment_score: float  # -1 to 1
    key_insights: List[str]
    risk_factors: List[str]
    opportunities: List[str]

class PerplexityClient:
    """Perplexity API client for market intelligence and news analysis"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.session = None

        # Market-specific query templates
        self.query_templates = {
            "market_news": "What are the latest market-moving news and developments for {symbol} in the Indian stock market today? Include earnings, policy changes, and analyst updates.",
            "commodity_news": "Latest news and market developments for {symbol} commodity trading on MCX. Include global supply/demand factors, weather impacts, and geopolitical events.",
            "sector_analysis": "Current market sentiment and key developments in the {sector} sector in India. What are the major drivers and risks?",
            "macro_economic": "Latest macroeconomic news and policy developments affecting Indian markets. Include RBI, government policies, inflation data, and global economic indicators.",
            "geopolitical_risks": "Any geopolitical events or developments that could impact global commodity markets and Indian economy?"
        }

    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            )

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def query_market_intelligence(self, query: str, context: str = "") -> Optional[Dict]:
        """Query Perplexity for market intelligence"""
        try:
            await self.initialize()

            payload = {
                "model": "sonar-pro",  # Perplexity's advanced model
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a financial market analyst providing real-time market intelligence, news analysis, and sentiment insights. Focus on actionable information for trading decisions."
                    },
                    {
                        "role": "user",
                        "content": f"{context}\n\n{query}" if context else query
                    }
                ],
                "temperature": 0.1,  # Low temperature for factual responses
                "max_tokens": 1000
            }

            async with self.session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Perplexity API error: {response.status} - {await response.text()}")
                    return None

        except Exception as e:
            logger.error(f"Error querying Perplexity: {e}")
            return None

    async def get_symbol_news_sentiment(self, symbol: str, symbol_type: str = "equity") -> Optional[MarketIntelligence]:
        """Get news and sentiment analysis for a specific symbol"""
        try:
            # Choose appropriate query template
            if symbol_type == "commodity" and "MCX" in symbol:
                query = self.query_templates["commodity_news"].format(symbol=symbol.replace("MCX_", ""))
            else:
                query = self.query_templates["market_news"].format(symbol=symbol)

            # Add context for better analysis
            context = f"Analyze the current market sentiment and news for {symbol}. Provide sentiment scores, key insights, and trading implications."

            response = await self.query_market_intelligence(query, context)
            if not response:
                return None

            # Parse the response and extract structured intelligence
            content = response['choices'][0]['message']['content']

            # Extract sentiment and insights from the response
            intelligence = await self._parse_intelligence_response(content, symbol)

            return intelligence

        except Exception as e:
            logger.error(f"Error getting news sentiment for {symbol}: {e}")
            return None

    async def get_market_overview(self) -> Optional[Dict]:
        """Get overall market sentiment and key developments"""
        try:
            queries = [
                self.query_templates["macro_economic"],
                self.query_templates["geopolitical_risks"]
            ]

            results = []
            for query in queries:
                response = await self.query_market_intelligence(query)
                if response:
                    results.append(response['choices'][0]['message']['content'])

            if results:
                # Combine and analyze all market intelligence
                combined_content = "\n\n".join(results)
                market_overview = await self._parse_market_overview(combined_content)
                return market_overview

            return None

        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return None

    async def _parse_intelligence_response(self, content: str, symbol: str) -> MarketIntelligence:
        """Parse Perplexity response into structured market intelligence"""
        # This is a simplified parser - in production, you'd use more sophisticated NLP
        news_items = []
        key_insights = []
        risk_factors = []
        opportunities = []

        lines = content.split('\n')

        # Extract sentiment indicators
        sentiment_indicators = {
            'positive': ['bullish', 'positive', 'gains', 'up', 'rise', 'growth', 'strong'],
            'negative': ['bearish', 'negative', 'losses', 'down', 'fall', 'decline', 'weak', 'concern'],
            'neutral': ['stable', 'mixed', 'neutral', 'unchanged', 'steady']
        }

        overall_sentiment = "neutral"
        sentiment_score = 0.0

        # Simple sentiment analysis
        content_lower = content.lower()
        positive_count = sum(1 for word in sentiment_indicators['positive'] if word in content_lower)
        negative_count = sum(1 for word in sentiment_indicators['negative'] if word in content_lower)

        if positive_count > negative_count:
            overall_sentiment = "positive"
            sentiment_score = min(0.8, positive_count / max(1, positive_count + negative_count))
        elif negative_count > positive_count:
            overall_sentiment = "negative"
            sentiment_score = -min(0.8, negative_count / max(1, positive_count + negative_count))

        # Extract key insights (simplified)
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['bullish', 'bearish', 'opportunity', 'risk', 'concern']):
                if any(word in line.lower() for word in ['risk', 'concern', 'decline', 'fall']):
                    risk_factors.append(line)
                elif any(word in line.lower() for word in ['opportunity', 'bullish', 'growth', 'rise']):
                    opportunities.append(line)
                else:
                    key_insights.append(line)

        # Create sample news items (in production, parse actual news from response)
        news_items = [
            NewsSentiment(
                headline=f"Market Update for {symbol}",
                sentiment=overall_sentiment,
                confidence=abs(sentiment_score),
                source="Perplexity AI Analysis",
                timestamp=datetime.now(),
                relevance_score=0.8,
                key_entities=[symbol]
            )
        ]

        return MarketIntelligence(
            symbol=symbol,
            news_items=news_items,
            overall_sentiment=overall_sentiment,
            sentiment_score=sentiment_score,
            key_insights=key_insights[:3],  # Limit to top 3
            risk_factors=risk_factors[:3],
            opportunities=opportunities[:3]
        )

    async def _parse_market_overview(self, content: str) -> Dict:
        """Parse market overview from combined responses"""
        return {
            "market_sentiment": "neutral",  # Would be determined by analysis
            "key_developments": [],  # Would extract from content
            "risk_assessment": "moderate",  # Would analyze content
            "trading_implications": [],  # Would derive from analysis
            "raw_analysis": content
        }

    async def get_sentiment_score(self, text: str) -> float:
        """Get sentiment score for a text (-1 to 1)"""
        try:
            query = f"Analyze the sentiment of this text and provide a score from -1 (very negative) to 1 (very positive): '{text}'"

            response = await self.query_market_intelligence(query)
            if response:
                content = response['choices'][0]['message']['content']

                # Simple score extraction (in production, use better parsing)
                if "0." in content or "-0." in content:
                    # Try to extract decimal number
                    import re
                    scores = re.findall(r'-?\d+\.\d+', content)
                    if scores:
                        return float(scores[0])

            return 0.0  # Neutral default

        except Exception as e:
            logger.error(f"Error getting sentiment score: {e}")
            return 0.0