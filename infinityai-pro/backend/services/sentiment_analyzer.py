# sentiment_analyzer.py
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass

# Use the new AI manager instead of individual clients
from services.ai import ai_manager

logger = logging.getLogger(__name__)

@dataclass
class EnhancedSignal:
    """Trading signal enhanced with market intelligence"""
    original_signal: Dict
    market_intelligence: Optional[MarketIntelligence]
    ai_strategy: Optional[Any]  # From OpenAI
    sentiment_adjustment: float  # -1 to 1, how sentiment affects signal
    confidence_boost: float  # Additional confidence from news
    risk_adjustment: str  # low, medium, high
    final_score: float
    recommendation: str

class SentimentAnalyzer:
    """Combines market news sentiment with trading signals using comprehensive AI stack"""

    def __init__(self):
        self.intelligence_cache = {}  # Cache market intelligence
        self.cache_expiry = timedelta(minutes=15)  # Cache for 15 minutes
        self.ai_initialized = False

    async def initialize(self):
        """Initialize AI services"""
        if not self.ai_initialized:
            await ai_manager.initialize()
            self.ai_initialized = True
            logger.info("SentimentAnalyzer initialized with AI manager")

    async def close(self):
        """Close AI services"""
        await ai_manager.close()

    async def enhance_signal(self, signal: Dict) -> EnhancedSignal:
        """Enhance a trading signal with market intelligence"""
        try:
            symbol = signal.get('symbol', 'UNKNOWN')
            symbol_type = 'commodity' if 'MCX' in symbol else 'equity'

            # Get market intelligence for this symbol
            market_intel = await self._get_market_intelligence(symbol, symbol_type)

            # Generate AI strategy using the comprehensive AI stack
            ai_strategy = None
            try:
                ai_response = await ai_manager.generate_strategy(signal, market_context)
                if ai_response and 'strategy' in ai_response:
                    ai_strategy = ai_response['strategy']
            except Exception as e:
                logger.warning(f"AI strategy generation failed: {e}")

            # Calculate sentiment adjustment
            sentiment_adjustment = self._calculate_sentiment_adjustment(signal, market_intel)

            # Calculate confidence boost
            confidence_boost = self._calculate_confidence_boost(market_intel)

            # Determine risk adjustment
            risk_adjustment = self._assess_risk_level(signal, market_intel, ai_strategy)

            # Calculate final score
            original_score = signal.get('score', 0.0)
            final_score = original_score + sentiment_adjustment + confidence_boost

            # Generate final recommendation
            recommendation = self._generate_recommendation(signal, market_intel, ai_strategy, final_score)

            return EnhancedSignal(
                original_signal=signal,
                market_intelligence=market_intel,
                ai_strategy=ai_strategy,
                sentiment_adjustment=sentiment_adjustment,
                confidence_boost=confidence_boost,
                risk_adjustment=risk_adjustment,
                final_score=final_score,
                recommendation=recommendation
            )

        except Exception as e:
            logger.error(f"Error enhancing signal: {e}")
            # Return basic enhanced signal on error
            return EnhancedSignal(
                original_signal=signal,
                market_intelligence=None,
                ai_strategy=None,
                sentiment_adjustment=0.0,
                confidence_boost=0.0,
                risk_adjustment="medium",
                final_score=signal.get('score', 0.0),
                recommendation=signal.get('direction', 'HOLD')
            )

    async def _get_market_intelligence(self, symbol: str, symbol_type: str) -> Optional[MarketIntelligence]:
        """Get cached or fresh market intelligence using AI manager"""
        cache_key = f"{symbol}_{symbol_type}"
        now = datetime.now()

        # Check cache
        if cache_key in self.intelligence_cache:
            cached_data, timestamp = self.intelligence_cache[cache_key]
            if now - timestamp < self.cache_expiry:
                return cached_data

        # Get fresh intelligence using AI manager
        try:
            sentiment_data = await ai_manager.analyze_market_sentiment(symbol, [])

            if sentiment_data and 'sentiment_analysis' in sentiment_data:
                # Convert AI manager response to MarketIntelligence format
                from services.perplexity_client import MarketIntelligence, NewsSentiment

                # Create mock news items from AI analysis
                news_items = [
                    NewsSentiment(
                        headline=f"AI Analysis for {symbol}",
                        sentiment=sentiment_data.get('sentiment_analysis', {}).get('sentiment', 'neutral'),
                        confidence=0.8,
                        source="AI Manager Analysis",
                        timestamp=datetime.now(),
                        relevance_score=0.9,
                        key_entities=[symbol]
                    )
                ]

                intelligence = MarketIntelligence(
                    symbol=symbol,
                    news_items=news_items,
                    overall_sentiment=sentiment_data.get('sentiment_analysis', {}).get('sentiment', 'neutral'),
                    sentiment_score=0.0,  # Would need to parse from AI response
                    key_insights=sentiment_data.get('sentiment_analysis', {}).get('insights', []),
                    risk_factors=[],  # Would need to parse from AI response
                    opportunities=[]  # Would need to parse from AI response
                )

                self.intelligence_cache[cache_key] = (intelligence, now)
                return intelligence

        except Exception as e:
            logger.error(f"Error getting market intelligence from AI manager: {e}")

        return None

    def _calculate_sentiment_adjustment(self, signal: Dict, market_intel: Optional[MarketIntelligence]) -> float:
        """Calculate how sentiment affects the signal score"""
        if not market_intel:
            return 0.0

        sentiment_score = market_intel.sentiment_score
        signal_direction = signal.get('direction', 'HOLD')

        # Adjust based on signal direction and market sentiment
        if signal_direction == 'BUY':
            # Positive sentiment boosts buy signals, negative sentiment reduces them
            adjustment = sentiment_score * 0.1  # Max ±0.1 adjustment
        elif signal_direction == 'SELL':
            # Negative sentiment boosts sell signals, positive sentiment reduces them
            adjustment = -sentiment_score * 0.1
        else:
            adjustment = 0.0

        return adjustment

    def _calculate_confidence_boost(self, market_intel: Optional[MarketIntelligence]) -> float:
        """Calculate confidence boost from news quality and recency"""
        if not market_intel or not market_intel.news_items:
            return 0.0

        # Boost confidence if we have recent, relevant news
        boost = 0.0

        for news in market_intel.news_items:
            # Recent news (within last hour) gets more weight
            hours_old = (datetime.now() - news.timestamp).total_seconds() / 3600
            recency_boost = max(0, 1 - (hours_old / 24))  # Decay over 24 hours

            # High relevance and confidence boost more
            relevance_boost = news.relevance_score
            confidence_boost = news.confidence

            boost += (recency_boost * relevance_boost * confidence_boost) * 0.05  # Max 0.05 per news item

        return min(boost, 0.15)  # Cap at 0.15

    def _assess_risk_level(self, signal: Dict, market_intel: Optional[MarketIntelligence], ai_strategy: Optional[Any]) -> str:
        """Assess overall risk level for the trade"""
        risk_score = 0

        # Base risk from signal strength
        signal_score = signal.get('score', 0.0)
        if signal_score < 0.6:
            risk_score += 2  # High risk for weak signals
        elif signal_score < 0.7:
            risk_score += 1  # Medium risk

        # Risk from market sentiment
        if market_intel:
            if market_intel.overall_sentiment == 'negative':
                risk_score += 1
            if market_intel.sentiment_score < -0.5:
                risk_score += 1

            # Risk factors increase risk
            risk_score += len(market_intel.risk_factors)

        # AI strategy risk assessment
        if ai_strategy and hasattr(ai_strategy, 'risk_level'):
            if ai_strategy.risk_level == 'high':
                risk_score += 2
            elif ai_strategy.risk_level == 'medium':
                risk_score += 1

        # Determine final risk level
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"

    def _generate_recommendation(self, signal: Dict, market_intel: Optional[MarketIntelligence],
                               ai_strategy: Optional[Any], final_score: float) -> str:
        """Generate final trading recommendation"""
        original_action = signal.get('direction', 'HOLD')

        # If AI strategy exists and differs from original, consider it
        if ai_strategy and hasattr(ai_strategy, 'action'):
            ai_action = ai_strategy.action
            ai_confidence = getattr(ai_strategy, 'confidence', 0.5)

            # If AI confidence is high and differs from original, use AI recommendation
            if ai_confidence > 0.7 and ai_action != original_action:
                return f"{ai_action} (AI Override: {ai_action} with {ai_confidence:.1f} confidence)"
            elif ai_confidence > 0.8:
                return f"{ai_action} (Strong AI Confirmation)"

        # Use original signal with enhancements
        if final_score >= 0.75:
            return f"{original_action} (High Confidence: {final_score:.3f})"
        elif final_score >= 0.65:
            return f"{original_action} (Medium Confidence: {final_score:.3f})"
        elif final_score >= 0.55:
            return f"{original_action} (Low Confidence: {final_score:.3f})"
        else:
            return f"HOLD (Insufficient Confidence: {final_score:.3f})"

    async def get_market_overview(self) -> Dict:
        """Get overall market sentiment overview using AI manager"""
        try:
            # Use AI manager for comprehensive market analysis
            overview = await ai_manager.chat(
                "Provide a comprehensive overview of current market conditions, key trends, and trading implications for commodities and equities."
            )

            return {
                "market_sentiment": "analyzed",  # Would parse from AI response
                "key_developments": [],  # Would extract from AI response
                "risk_assessment": "moderate",  # Would assess from AI response
                "ai_analysis": overview.get('response', ''),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {"error": str(e)}

    async def analyze_portfolio_sentiment(self, portfolio_data: Dict) -> Dict:
        """Analyze sentiment impact on portfolio"""
        try:
            sentiments = {}

            # Analyze each position
            for position in portfolio_data.get('positions', []):
                symbol = position.get('symbol')
                if symbol:
                    intel = await self._get_market_intelligence(symbol, 'equity')
                    if intel:
                        sentiments[symbol] = {
                            'sentiment': intel.overall_sentiment,
                            'score': intel.sentiment_score,
                            'key_insights': intel.key_insights[:2]
                        }

            return {
                'portfolio_sentiment': sentiments,
                'overall_impact': self._calculate_portfolio_sentiment_impact(sentiments),
                'recommendations': self._generate_portfolio_recommendations(sentiments)
            }

        except Exception as e:
            logger.error(f"Error analyzing portfolio sentiment: {e}")
            return {"error": str(e)}

    def _calculate_portfolio_sentiment_impact(self, sentiments: Dict) -> str:
        """Calculate overall sentiment impact on portfolio"""
        if not sentiments:
            return "neutral"

        scores = [data['score'] for data in sentiments.values()]
        avg_score = sum(scores) / len(scores)

        if avg_score > 0.3:
            return "positive"
        elif avg_score < -0.3:
            return "negative"
        else:
            return "neutral"

    def _generate_portfolio_recommendations(self, sentiments: Dict) -> List[str]:
        """Generate portfolio recommendations based on sentiment"""
        recommendations = []

        positive_symbols = [s for s, data in sentiments.items() if data['score'] > 0.2]
        negative_symbols = [s for s, data in sentiments.items() if data['score'] < -0.2]

        if positive_symbols:
            recommendations.append(f"Consider increasing exposure to: {', '.join(positive_symbols[:3])}")

        if negative_symbols:
            recommendations.append(f"Consider reducing exposure to: {', '.join(negative_symbols[:3])}")

        if not recommendations:
            recommendations.append("Maintain current portfolio allocation")

        return recommendations