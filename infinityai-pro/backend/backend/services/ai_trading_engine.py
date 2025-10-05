"""
AI/ML Trading Strategy Engine - Real-time Market Analysis & Strategy Execution
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import random
from dataclasses import dataclass
from enum import Enum

from services.dhan_api_service import dhan_api_service

logger = logging.getLogger(__name__)

class TradingSignal(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

@dataclass
class TradingOpportunity:
    symbol: str
    signal: TradingSignal
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    reasoning: str
    risk_reward: float
    timestamp: datetime

class AITradingEngine:
    """AI-powered trading engine with real-time analysis"""
    
    def __init__(self):
        self.price_history: Dict[str, List[Dict]] = {}
        self.confidence_threshold = 0.7
        
    async def analyze_symbols(self, symbols: List[str]) -> Dict[str, Any]:
        """Comprehensive AI analysis of symbols"""
        
        logger.info(f"🧠 AI Analysis starting for {len(symbols)} symbols")
        
        try:
            # Fetch real-time data
            market_data = await dhan_api_service.get_live_quote(symbols)
            
            if not market_data.get("success"):
                logger.error("Failed to fetch market data")
                return {"success": False, "error": "Market data unavailable"}
            
            quotes = market_data.get("quotes", {})
            analyses = {}
            opportunities = []
            
            # Analyze each symbol
            for symbol, quote_data in quotes.items():
                try:
                    analysis = await self._analyze_symbol(symbol, quote_data)
                    analyses[symbol] = analysis
                    
                    # Check for trading opportunities
                    if analysis.get("opportunity") and analysis["opportunity"]["confidence"] >= self.confidence_threshold:
                        opportunities.append(analysis["opportunity"])
                        
                except Exception as e:
                    logger.error(f"Analysis error for {symbol}: {e}")
                    continue
            
            # Sort opportunities by confidence
            opportunities = sorted(opportunities, key=lambda x: x["confidence"], reverse=True)
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "symbols_analyzed": len(analyses),
                "market_overview": self._generate_market_overview(analyses),
                "symbol_analyses": analyses,
                "top_opportunities": opportunities[:5],
                "data_source": market_data.get("data_source", "dhan_api"),
                "real_data": market_data.get("data_source") == "dhan_api"
            }
            
        except Exception as e:
            logger.error(f"AI Analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_symbol(self, symbol: str, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive analysis on a single symbol"""
        
        current_price = quote_data.get("ltp", 0)
        change_percent = quote_data.get("change_percent", 0)
        volume = quote_data.get("volume", 0)
        
        # Technical Analysis
        technical = self._technical_analysis(quote_data)
        
        # Sentiment Analysis
        sentiment = self._sentiment_analysis(quote_data)
        
        # Risk Assessment
        risk = self._risk_assessment(quote_data)
        
        # AI Recommendation
        recommendation = self._ai_recommendation(technical, sentiment, risk, quote_data)
        
        # Trading Opportunity
        opportunity = self._identify_opportunity(symbol, technical, recommendation, quote_data)
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "change_percent": change_percent,
            "volume": volume,
            "technical": technical,
            "sentiment": sentiment,
            "risk": risk,
            "recommendation": recommendation,
            "opportunity": opportunity,
            "real_data": quote_data.get("real_data", False),
            "timestamp": datetime.now().isoformat()
        }
    
    def _technical_analysis(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform technical analysis"""
        
        ltp = quote_data.get("ltp", 0)
        change_percent = quote_data.get("change_percent", 0)
        volume = quote_data.get("volume", 0)
        high = quote_data.get("high", ltp)
        low = quote_data.get("low", ltp)
        
        # Trend determination
        if change_percent > 1.5:
            trend = "BULLISH"
            trend_strength = min(abs(change_percent) / 3, 1.0)
        elif change_percent < -1.5:
            trend = "BEARISH"
            trend_strength = min(abs(change_percent) / 3, 1.0)
        else:
            trend = "SIDEWAYS"
            trend_strength = 0.3
        
        # Support and resistance
        support = low * 0.99
        resistance = high * 1.01
        
        # Volume analysis
        volume_score = min(volume / 1000000, 1.0)  # Normalize volume
        
        return {
            "trend": trend,
            "trend_strength": trend_strength,
            "support_level": support,
            "resistance_level": resistance,
            "volume_score": volume_score,
            "volatility": abs(change_percent) / 100,
            "momentum": change_percent / 5  # Normalized momentum
        }
    
    def _sentiment_analysis(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market sentiment"""
        
        change_percent = quote_data.get("change_percent", 0)
        volume = quote_data.get("volume", 0)
        
        # Basic sentiment based on price action
        if change_percent > 2:
            sentiment = "VERY_POSITIVE"
            score = 0.8
        elif change_percent > 0.5:
            sentiment = "POSITIVE"
            score = 0.6
        elif change_percent < -2:
            sentiment = "VERY_NEGATIVE"
            score = -0.8
        elif change_percent < -0.5:
            sentiment = "NEGATIVE"
            score = -0.6
        else:
            sentiment = "NEUTRAL"
            score = 0
        
        # Volume confirmation
        volume_factor = min(volume / 500000, 1.0) if volume > 0 else 0.3
        confidence = volume_factor * 0.7 + 0.3
        
        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence,
            "volume_confirmation": volume_factor > 0.5
        }
    
    def _risk_assessment(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess trading risk"""
        
        change_percent = quote_data.get("change_percent", 0)
        ltp = quote_data.get("ltp", 0)
        high = quote_data.get("high", ltp)
        low = quote_data.get("low", ltp)
        
        # Volatility risk
        volatility = abs(change_percent)
        if volatility > 5:
            risk_level = "HIGH"
            risk_score = 0.8
        elif volatility > 2:
            risk_level = "MEDIUM"
            risk_score = 0.5
        else:
            risk_level = "LOW"
            risk_score = 0.2
        
        # Price range analysis
        if ltp > 0:
            range_percent = ((high - low) / ltp) * 100
        else:
            range_percent = 0
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "volatility": volatility,
            "range_percent": range_percent,
            "suitable_for_trading": risk_score < 0.7
        }
    
    def _ai_recommendation(self, technical: Dict, sentiment: Dict, risk: Dict, quote_data: Dict) -> Dict[str, Any]:
        """Generate AI-powered recommendation"""
        
        # Weighted scoring
        tech_score = 0
        if technical["trend"] == "BULLISH":
            tech_score = technical["trend_strength"] * 0.8
        elif technical["trend"] == "BEARISH":
            tech_score = -technical["trend_strength"] * 0.8
        
        sent_score = sentiment["score"] * sentiment["confidence"]
        risk_penalty = -risk["risk_score"] * 0.3
        
        # Combined AI score
        ai_score = tech_score * 0.5 + sent_score * 0.3 + risk_penalty * 0.2
        confidence = min((technical["trend_strength"] + sentiment["confidence"]) / 2, 0.95)
        
        # Generate recommendation
        if ai_score > 0.6 and risk["suitable_for_trading"]:
            action = "STRONG_BUY"
            reasoning = "Strong bullish signals with acceptable risk"
        elif ai_score > 0.3 and risk["suitable_for_trading"]:
            action = "BUY"
            reasoning = "Positive signals indicate upward potential"
        elif ai_score < -0.6 and risk["suitable_for_trading"]:
            action = "STRONG_SELL"
            reasoning = "Strong bearish signals with acceptable risk"
        elif ai_score < -0.3 and risk["suitable_for_trading"]:
            action = "SELL"
            reasoning = "Negative signals indicate downward pressure"
        else:
            action = "HOLD"
            reasoning = "Mixed signals or high risk - maintain current position"
        
        return {
            "action": action,
            "ai_score": ai_score,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_adjusted": risk["suitable_for_trading"]
        }
    
    def _identify_opportunity(self, symbol: str, technical: Dict, recommendation: Dict, quote_data: Dict) -> Optional[Dict[str, Any]]:
        """Identify concrete trading opportunities"""
        
        if recommendation["action"] == "HOLD":
            return None
        
        current_price = quote_data.get("ltp", 0)
        confidence = recommendation["confidence"]
        
        if confidence < self.confidence_threshold:
            return None
        
        # Calculate entry, target, and stop loss
        if recommendation["action"] in ["BUY", "STRONG_BUY"]:
            entry_price = current_price
            target_price = technical["resistance_level"]
            stop_loss = technical["support_level"]
        else:  # SELL or STRONG_SELL
            entry_price = current_price
            target_price = technical["support_level"]
            stop_loss = technical["resistance_level"]
        
        # Risk-reward calculation
        risk = abs(entry_price - stop_loss)
        reward = abs(target_price - entry_price)
        risk_reward = reward / risk if risk > 0 else 1.0
        
        # Only high-quality opportunities
        if risk_reward < 1.2:
            return None
        
        return {
            "symbol": symbol,
            "signal": recommendation["action"],
            "confidence": confidence,
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "risk_reward": risk_reward,
            "reasoning": recommendation["reasoning"],
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_market_overview(self, analyses: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate overall market overview"""
        
        if not analyses:
            return {"status": "No data available"}
        
        # Count trends
        bullish = sum(1 for a in analyses.values() if a.get("technical", {}).get("trend") == "BULLISH")
        bearish = sum(1 for a in analyses.values() if a.get("technical", {}).get("trend") == "BEARISH")
        sideways = sum(1 for a in analyses.values() if a.get("technical", {}).get("trend") == "SIDEWAYS")
        
        # Count opportunities
        opportunities = sum(1 for a in analyses.values() if a.get("opportunity"))
        
        # Overall sentiment
        if bullish > bearish + sideways:
            market_sentiment = "BULLISH"
        elif bearish > bullish + sideways:
            market_sentiment = "BEARISH"
        else:
            market_sentiment = "MIXED"
        
        # Average confidence
        confidences = [a.get("recommendation", {}).get("confidence", 0) for a in analyses.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "market_sentiment": market_sentiment,
            "bullish_count": bullish,
            "bearish_count": bearish,
            "sideways_count": sideways,
            "opportunities_count": opportunities,
            "average_confidence": avg_confidence,
            "total_symbols": len(analyses),
            "recommendation": self._get_market_recommendation(market_sentiment, avg_confidence, opportunities)
        }
    
    def _get_market_recommendation(self, sentiment: str, confidence: float, opportunities: int) -> str:
        """Get overall market recommendation"""
        
        if sentiment == "BULLISH" and confidence > 0.7 and opportunities > 0:
            return "🔥 Excellent market conditions! Multiple high-confidence opportunities available."
        elif sentiment == "BEARISH" and confidence > 0.7:
            return "⚠️ Bearish market detected. Consider defensive strategies or short positions."
        elif opportunities > 2:
            return "🎯 Selective opportunities available. Focus on highest confidence trades."
        elif confidence > 0.6:
            return "📊 Mixed conditions. Proceed with caution and proper risk management."
        else:
            return "⏳ Unclear market signals. Better to wait for more definitive trends."

# Global instance
ai_trading_engine = AITradingEngine()