# services/ai/sentiment_service.py
"""
InfinityAI.Pro - Multi-Cloud Sentiment Analysis Service
Supports FinBERT (primary), Azure Text Analytics (secondary), AWS Comprehend (tertiary)
"""

import httpx
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import re
from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SentimentService:
    """Multi-cloud sentiment analysis service with failover support"""

    def __init__(self):
        self.config = Config()
        self.client: Optional[httpx.AsyncClient] = None
        self.initialized = False
        self.finbert_model = None

    async def initialize(self):
        """Initialize multi-cloud sentiment connections"""
        try:
            self.client = httpx.AsyncClient(timeout=30.0)

            # Initialize FinBERT model
            try:
                from transformers import pipeline
                self.finbert_model = pipeline("sentiment-analysis",
                                           model="ProsusAI/finbert",
                                           tokenizer="ProsusAI/finbert")
                logger.info("✅ FinBERT model loaded")
            except ImportError:
                logger.warning("FinBERT not available - install transformers: pip install transformers torch")
            except Exception as e:
                logger.warning(f"Failed to load FinBERT: {e}")

            self.initialized = True
            logger.info("✅ Multi-cloud Sentiment Service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Sentiment service: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    # FinBERT (Primary - Local)
    async def finbert_analyze(self, text: str, **kwargs) -> Dict[str, Any]:
        """FinBERT sentiment analysis"""
        try:
            if not self.finbert_model:
                raise Exception("FinBERT model not loaded")

            # Clean and prepare text
            clean_text = self._clean_text(text)

            # Run sentiment analysis
            result = self.finbert_model(clean_text)[0]

            # Convert to standardized format
            sentiment = result['label'].lower()
            confidence = result['score']

            # Map FinBERT labels to standard sentiment
            sentiment_map = {
                'positive': 'bullish',
                'negative': 'bearish',
                'neutral': 'neutral'
            }

            return {
                "sentiment": sentiment_map.get(sentiment, sentiment),
                "confidence": confidence,
                "score": confidence if sentiment == 'positive' else -confidence if sentiment == 'negative' else 0.0,
                "provider": "finbert",
                "raw_result": result
            }

        except Exception as e:
            logger.error(f"FinBERT sentiment error: {e}")
            raise

    # Azure Text Analytics (Secondary)
    async def azure_analyze(self, text: str, **kwargs) -> Dict[str, Any]:
        """Azure Text Analytics sentiment analysis"""
        try:
            azure_url = f"{self.config.AZURE_TEXT_ANALYTICS_ENDPOINT}/text/analytics/v3.1/sentiment"
            headers = {
                "Ocp-Apim-Subscription-Key": self.config.AZURE_TEXT_ANALYTICS_KEY,
                "Content-Type": "application/json"
            }

            payload = {
                "documents": [
                    {
                        "id": "1",
                        "language": kwargs.get("language", "en"),
                        "text": text[:5120]  # Azure limit
                    }
                ]
            }

            async with self.client.post(azure_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

            if result.get("documents"):
                doc = result["documents"][0]
                sentiment = doc.get("sentiment", "neutral")
                confidence_scores = doc.get("confidenceScores", {})

                # Calculate score from confidence scores
                pos_score = confidence_scores.get("positive", 0.0)
                neg_score = confidence_scores.get("negative", 0.0)
                score = pos_score - neg_score

                return {
                    "sentiment": sentiment.lower(),
                    "confidence": max(pos_score, neg_score, confidence_scores.get("neutral", 0.0)),
                    "score": score,
                    "provider": "azure",
                    "confidence_scores": confidence_scores
                }
            else:
                raise Exception("No documents in Azure response")

        except Exception as e:
            logger.error(f"Azure Text Analytics error: {e}")
            raise

    # AWS Comprehend (Tertiary)
    async def aws_analyze(self, text: str, **kwargs) -> Dict[str, Any]:
        """AWS Comprehend sentiment analysis"""
        try:
            import boto3
            comprehend = boto3.client(
                'comprehend',
                region_name=self.config.AWS_REGION,
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY
            )

            # Detect sentiment
            response = comprehend.detect_sentiment(
                Text=text[:5000],  # AWS limit
                LanguageCode=kwargs.get("language", "en")
            )

            sentiment = response.get("Sentiment", "NEUTRAL").lower()
            sentiment_score = response.get("SentimentScore", {})

            # Calculate score
            pos_score = sentiment_score.get("Positive", 0.0)
            neg_score = sentiment_score.get("Negative", 0.0)
            score = pos_score - neg_score

            return {
                "sentiment": sentiment,
                "confidence": max(sentiment_score.values()),
                "score": score,
                "provider": "aws",
                "sentiment_score": sentiment_score
            }

        except Exception as e:
            logger.error(f"AWS Comprehend error: {e}")
            raise

    # Multi-source sentiment aggregation
    async def analyze_multi_source(self, sources: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Analyze sentiment from multiple sources and aggregate"""
        try:
            results = []

            for source in sources:
                text = source.get("text", "")
                source_type = source.get("type", "unknown")

                if not text:
                    continue

                # Analyze with primary provider
                try:
                    sentiment_result = await self.finbert_analyze(text, **kwargs)
                    sentiment_result["source_type"] = source_type
                    results.append(sentiment_result)
                except Exception as e:
                    logger.warning(f"Failed to analyze {source_type}: {e}")
                    continue

            if not results:
                return {"error": "No valid sources to analyze"}

            # Aggregate results
            return self._aggregate_sentiment_results(results)

        except Exception as e:
            logger.error(f"Multi-source sentiment error: {e}")
            return {"error": str(e)}

    # News sentiment analysis
    async def analyze_news_sentiment(self, news_articles: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Analyze sentiment from news articles"""
        try:
            sources = []
            for article in news_articles:
                sources.append({
                    "text": f"{article.get('title', '')} {article.get('content', '')}",
                    "type": "news"
                })

            return await self.analyze_multi_source(sources, **kwargs)

        except Exception as e:
            logger.error(f"News sentiment analysis error: {e}")
            return {"error": str(e)}

    # Social media sentiment analysis
    async def analyze_social_sentiment(self, social_posts: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Analyze sentiment from social media posts"""
        try:
            sources = []
            for post in social_posts:
                sources.append({
                    "text": post.get("content", ""),
                    "type": "social"
                })

            return await self.analyze_multi_source(sources, **kwargs)

        except Exception as e:
            logger.error(f"Social sentiment analysis error: {e}")
            return {"error": str(e)}

    # Legacy methods for backward compatibility
    async def analyze_sentiment(self, text: str, **kwargs) -> Dict:
        """Analyze sentiment using router"""
        try:
            from .router import AIRouter
            # Note: Router doesn't have sentiment methods yet, so we'll use direct provider calls
            providers = ["finbert", "azure", "aws"]

            for provider in providers:
                try:
                    method_name = f"{provider}_analyze"
                    if hasattr(self, method_name):
                        method = getattr(self, method_name)
                        result = await method(text, **kwargs)
                        return result
                except Exception as e:
                    logger.warning(f"Provider {provider} failed: {e}")
                    continue

            return {"error": "All sentiment providers failed"}

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"error": str(e)}

    async def get_market_sentiment(self, symbol: str, **kwargs) -> Dict:
        """Get overall market sentiment for a symbol"""
        try:
            # This would integrate with news APIs and social media feeds
            # For now, return mock data structure
            return {
                "symbol": symbol,
                "overall_sentiment": "neutral",
                "confidence": 0.5,
                "sources_analyzed": 0,
                "news_sentiment": {"bullish": 0, "bearish": 0, "neutral": 0},
                "social_sentiment": {"bullish": 0, "bearish": 0, "neutral": 0},
                "timestamp": datetime.now().isoformat(),
                "note": "Market sentiment analysis requires news API integration"
            }

        except Exception as e:
            logger.error(f"Error getting market sentiment: {e}")
            return {"error": str(e)}

    def _clean_text(self, text: str) -> str:
        """Clean text for sentiment analysis"""
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove mentions
        text = re.sub(r'@\w+', '', text)
        # Remove hashtags symbols but keep text
        text = re.sub(r'#', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()

    def _aggregate_sentiment_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate sentiment results from multiple sources"""
        if not results:
            return {"error": "No results to aggregate"}

        # Calculate weighted average
        total_weight = 0
        weighted_score = 0
        sentiment_counts = {"bullish": 0, "bearish": 0, "neutral": 0}

        for result in results:
            confidence = result.get("confidence", 0.5)
            score = result.get("score", 0.0)
            sentiment = result.get("sentiment", "neutral")

            weighted_score += score * confidence
            total_weight += confidence
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

        # Determine overall sentiment
        avg_score = weighted_score / total_weight if total_weight > 0 else 0
        if avg_score > 0.1:
            overall_sentiment = "bullish"
        elif avg_score < -0.1:
            overall_sentiment = "bearish"
        else:
            overall_sentiment = "neutral"

        return {
            "overall_sentiment": overall_sentiment,
            "average_score": avg_score,
            "confidence": total_weight / len(results),
            "sources_analyzed": len(results),
            "sentiment_distribution": sentiment_counts,
            "individual_results": results,
            "timestamp": datetime.now().isoformat()
        }

    async def health_check(self) -> Dict:
        """Check sentiment service health"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            health_status = {
                "finbert": self.finbert_model is not None,
                "azure": bool(self.config.AZURE_TEXT_ANALYTICS_KEY),
                "aws": bool(self.config.AWS_ACCESS_KEY_ID)
            }

            return {
                "status": "healthy" if any(health_status.values()) else "degraded",
                "providers": health_status,
                "multi_cloud": True
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }