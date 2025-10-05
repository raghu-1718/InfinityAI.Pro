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

class StrategyType(Enum):
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    SENTIMENT = "sentiment"
    SCALPING = "scalping"
    SWING = "swing"
    AI_HYBRID = "ai_hybrid"

@dataclass
class TradingOpportunity:
    symbol: str
    signal: TradingSignal
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    strategy: StrategyType
    reasoning: str
    risk_reward: float
    timestamp: datetime

@dataclass
class MarketAnalysis:
    symbol: str
    trend: str
    volatility: float
    support_levels: List[float]
    resistance_levels: List[float]
    technical_indicators: Dict[str, float]
    sentiment_score: float
    news_impact: str
    ai_confidence: float

class AITradingStrategyEngine:
    """AI-powered trading strategy engine with real-time analysis"""
    
    def __init__(self):
        # Strategy configurations
        self.active_strategies = [
            StrategyType.MOMENTUM,
            StrategyType.MEAN_REVERSION, 
            StrategyType.SENTIMENT,
            StrategyType.AI_HYBRID
        ]
        
        # Market data cache
        self.price_history: Dict[str, List[Dict]] = {}
        self.analysis_cache: Dict[str, MarketAnalysis] = {}
        
        # AI/ML parameters
        self.lookback_periods = 20
        self.volatility_threshold = 0.02
        self.momentum_threshold = 0.015
        self.confidence_threshold = 0.7
        
        # Risk management
        self.max_risk_per_trade = 0.02  # 2%
        self.max_portfolio_risk = 0.10  # 10%
        
        # Strategy weights
        self.strategy_weights = {
            StrategyType.MOMENTUM: 0.25,
            StrategyType.MEAN_REVERSION: 0.20,
            StrategyType.SENTIMENT: 0.15,
            StrategyType.AI_HYBRID: 0.40
        }
        
        # Performance tracking
        self.strategy_performance = {strategy: {"wins": 0, "losses": 0, "total_pnl": 0} 
                                   for strategy in StrategyType}
    
    async def analyze_market_comprehensive(self, symbols: List[str]) -> Dict[str, Any]:
        """Comprehensive market analysis using AI/ML techniques"""
        
        logger.info(f"Starting comprehensive analysis for {len(symbols)} symbols")
        
        try:
            # Fetch real-time market data
            market_data = await dhan_api_service.get_live_quote(symbols)
            
            if not market_data.get("success"):
                logger.error("Failed to fetch market data")
                return {"success": False, "error": "Market data unavailable"}
            
            quotes = market_data.get("quotes", {})
            analyses = {}
            opportunities = []
            
            # Process each symbol
            for symbol, quote_data in quotes.items():
                try:
                    # Update price history
                    await self._update_price_history(symbol, quote_data)
                    
                    # Perform technical analysis
                    analysis = await self._perform_technical_analysis(symbol, quote_data)
                    
                    # Generate trading signals
                    signal_results = await self._generate_trading_signals(symbol, analysis, quote_data)
                    
                    # Find trading opportunities
                    opportunity = await self._identify_trading_opportunity(symbol, analysis, signal_results)
                    
                    analyses[symbol] = {
                        "analysis": analysis.__dict__ if analysis else {},
                        "signals": signal_results,
                        "opportunity": opportunity.__dict__ if opportunity else None,
                        "current_price": quote_data.get("ltp", 0),
                        "real_data": quote_data.get("real_data", False)
                    }
                    
                    if opportunity and opportunity.confidence >= self.confidence_threshold:
                        opportunities.append(opportunity)
                        
                except Exception as e:
                    logger.error(f"Analysis error for {symbol}: {e}")
                    continue
            
            # Rank opportunities by confidence and risk-reward
            opportunities = sorted(opportunities, key=lambda x: (x.confidence * x.risk_reward), reverse=True)
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "symbols_analyzed": len(analyses),
                "market_overview": self._generate_market_overview(analyses),
                "symbol_analyses": analyses,
                "top_opportunities": [op.__dict__ for op in opportunities[:5]],
                "strategy_performance": self.strategy_performance,
                "data_source": market_data.get("data_source", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_price_history(self, symbol: str, quote_data: Dict[str, Any]):
        """Update price history for technical analysis"""
        
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        price_point = {
            "timestamp": datetime.now(),
            "open": quote_data.get("open", 0),
            "high": quote_data.get("high", 0),
            "low": quote_data.get("low", 0),
            "close": quote_data.get("ltp", 0),
            "volume": quote_data.get("volume", 0)
        }
        
        self.price_history[symbol].append(price_point)
        
        # Keep only recent data (last 100 points)
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]
    
    async def _perform_technical_analysis(self, symbol: str, quote_data: Dict[str, Any]) -> MarketAnalysis:
        """Perform comprehensive technical analysis"""
        
        try:
            history = self.price_history.get(symbol, [])
            current_price = quote_data.get("ltp", 0)
            
            if len(history) < self.lookback_periods:
                # Generate basic analysis for new symbols
                return self._generate_basic_analysis(symbol, quote_data)
            
            # Convert to pandas DataFrame for analysis
            df = pd.DataFrame(history)
            
            # Technical indicators
            sma_20 = df['close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else current_price
            ema_12 = df['close'].ewm(span=12).mean().iloc[-1] if len(df) >= 12 else current_price
            
            # Volatility
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0.2
            
            # Support and resistance
            recent_highs = df['high'].tail(20).max() if len(df) >= 20 else current_price * 1.02\n            recent_lows = df['low'].tail(20).min() if len(df) >= 20 else current_price * 0.98\n            \n            # Trend determination\n            if current_price > sma_20 * 1.02:\n                trend = \"BULLISH\"\n            elif current_price < sma_20 * 0.98:\n                trend = \"BEARISH\"\n            else:\n                trend = \"SIDEWAYS\"\n            \n            # AI confidence based on multiple factors\n            trend_strength = abs(current_price - sma_20) / sma_20\n            volume_factor = min(quote_data.get(\"volume\", 100000) / 1000000, 1.0)\n            \n            ai_confidence = min((\n                0.4 * (1 - volatility) +  # Lower volatility = higher confidence\n                0.3 * trend_strength +     # Stronger trend = higher confidence\n                0.3 * volume_factor        # Higher volume = higher confidence\n            ), 0.95)\n            \n            return MarketAnalysis(\n                symbol=symbol,\n                trend=trend,\n                volatility=volatility,\n                support_levels=[recent_lows, current_price * 0.98],\n                resistance_levels=[recent_highs, current_price * 1.02],\n                technical_indicators={\n                    \"sma_20\": sma_20,\n                    \"ema_12\": ema_12,\n                    \"rsi\": random.uniform(30, 70),  # Simulated RSI\n                    \"macd\": random.uniform(-0.5, 0.5)  # Simulated MACD\n                },\n                sentiment_score=random.uniform(-1, 1),  # Simulated sentiment\n                news_impact=\"NEUTRAL\",\n                ai_confidence=ai_confidence\n            )\n            \n        except Exception as e:\n            logger.error(f\"Technical analysis error for {symbol}: {e}\")\n            return self._generate_basic_analysis(symbol, quote_data)\n    \n    def _generate_basic_analysis(self, symbol: str, quote_data: Dict[str, Any]) -> MarketAnalysis:\n        \"\"\"Generate basic analysis for symbols with limited history\"\"\"\n        \n        current_price = quote_data.get(\"ltp\", 0)\n        change_percent = quote_data.get(\"change_percent\", 0)\n        \n        # Determine trend from price change\n        if change_percent > 1:\n            trend = \"BULLISH\"\n        elif change_percent < -1:\n            trend = \"BEARISH\"\n        else:\n            trend = \"SIDEWAYS\"\n        \n        return MarketAnalysis(\n            symbol=symbol,\n            trend=trend,\n            volatility=0.25,  # Default volatility\n            support_levels=[current_price * 0.98, current_price * 0.95],\n            resistance_levels=[current_price * 1.02, current_price * 1.05],\n            technical_indicators={\n                \"sma_20\": current_price,\n                \"ema_12\": current_price,\n                \"rsi\": 50 + change_percent * 5,\n                \"macd\": change_percent / 100\n            },\n            sentiment_score=min(max(change_percent / 5, -1), 1),\n            news_impact=\"NEUTRAL\",\n            ai_confidence=0.6\n        )\n    \n    async def _generate_trading_signals(self, symbol: str, analysis: MarketAnalysis, \n                                      quote_data: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Generate trading signals from multiple strategies\"\"\"\n        \n        current_price = quote_data.get(\"ltp\", 0)\n        signals = {}\n        \n        # Momentum Strategy\n        momentum_signal = self._momentum_strategy(analysis, quote_data)\n        signals[\"momentum\"] = momentum_signal\n        \n        # Mean Reversion Strategy  \n        mean_reversion_signal = self._mean_reversion_strategy(analysis, quote_data)\n        signals[\"mean_reversion\"] = mean_reversion_signal\n        \n        # Sentiment Strategy\n        sentiment_signal = self._sentiment_strategy(analysis, quote_data)\n        signals[\"sentiment\"] = sentiment_signal\n        \n        # AI Hybrid Strategy\n        ai_hybrid_signal = self._ai_hybrid_strategy(analysis, quote_data, signals)\n        signals[\"ai_hybrid\"] = ai_hybrid_signal\n        \n        # Weighted final signal\n        final_signal = self._calculate_weighted_signal(signals)\n        signals[\"final\"] = final_signal\n        \n        return signals\n    \n    def _momentum_strategy(self, analysis: MarketAnalysis, quote_data: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Momentum-based trading strategy\"\"\"\n        \n        change_percent = quote_data.get(\"change_percent\", 0)\n        volume = quote_data.get(\"volume\", 0)\n        \n        # Strong momentum criteria\n        if change_percent > 2 and volume > 500000 and analysis.trend == \"BULLISH\":\n            signal = TradingSignal.BUY\n            confidence = min(0.8, 0.5 + abs(change_percent) / 10)\n        elif change_percent < -2 and volume > 500000 and analysis.trend == \"BEARISH\":\n            signal = TradingSignal.SELL\n            confidence = min(0.8, 0.5 + abs(change_percent) / 10)\n        elif abs(change_percent) > self.momentum_threshold:\n            signal = TradingSignal.BUY if change_percent > 0 else TradingSignal.SELL\n            confidence = 0.6\n        else:\n            signal = TradingSignal.HOLD\n            confidence = 0.4\n        \n        return {\n            \"signal\": signal.value,\n            \"confidence\": confidence,\n            \"reason\": f\"Momentum: {change_percent:.2f}% with {volume:,} volume\"\n        }\n    \n    def _mean_reversion_strategy(self, analysis: MarketAnalysis, quote_data: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Mean reversion strategy\"\"\"\n        \n        current_price = quote_data.get(\"ltp\", 0)\n        sma_20 = analysis.technical_indicators.get(\"sma_20\", current_price)\n        \n        price_deviation = (current_price - sma_20) / sma_20\n        \n        if price_deviation < -0.03:  # Price 3% below average\n            signal = TradingSignal.BUY\n            confidence = min(0.75, 0.5 + abs(price_deviation) * 10)\n        elif price_deviation > 0.03:  # Price 3% above average\n            signal = TradingSignal.SELL\n            confidence = min(0.75, 0.5 + abs(price_deviation) * 10)\n        else:\n            signal = TradingSignal.HOLD\n            confidence = 0.4\n        \n        return {\n            \"signal\": signal.value,\n            \"confidence\": confidence,\n            \"reason\": f\"Mean reversion: {price_deviation:.2%} from SMA20\"\n        }\n    \n    def _sentiment_strategy(self, analysis: MarketAnalysis, quote_data: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Sentiment-based strategy\"\"\"\n        \n        sentiment_score = analysis.sentiment_score\n        \n        if sentiment_score > 0.6:\n            signal = TradingSignal.BUY\n            confidence = min(0.7, 0.4 + sentiment_score * 0.4)\n        elif sentiment_score < -0.6:\n            signal = TradingSignal.SELL\n            confidence = min(0.7, 0.4 + abs(sentiment_score) * 0.4)\n        else:\n            signal = TradingSignal.HOLD\n            confidence = 0.3\n        \n        return {\n            \"signal\": signal.value,\n            \"confidence\": confidence,\n            \"reason\": f\"Sentiment score: {sentiment_score:.2f}\"\n        }\n    \n    def _ai_hybrid_strategy(self, analysis: MarketAnalysis, quote_data: Dict[str, Any], \n                           other_signals: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"AI hybrid strategy combining multiple factors\"\"\"\n        \n        # Collect signals from other strategies\n        momentum_conf = other_signals.get(\"momentum\", {}).get(\"confidence\", 0)\n        mean_rev_conf = other_signals.get(\"mean_reversion\", {}).get(\"confidence\", 0)\n        sentiment_conf = other_signals.get(\"sentiment\", {}).get(\"confidence\", 0)\n        \n        # AI confidence weighting\n        ai_confidence = analysis.ai_confidence\n        volatility_factor = max(0.3, 1 - analysis.volatility)\n        \n        # Combined confidence\n        combined_confidence = (\n            0.3 * momentum_conf +\n            0.25 * mean_rev_conf +\n            0.2 * sentiment_conf +\n            0.25 * ai_confidence\n        ) * volatility_factor\n        \n        # Determine signal based on consensus\n        buy_signals = sum(1 for s in other_signals.values() \n                         if s.get(\"signal\") in [\"BUY\", \"STRONG_BUY\"])\n        sell_signals = sum(1 for s in other_signals.values() \n                          if s.get(\"signal\") in [\"SELL\", \"STRONG_SELL\"])\n        \n        if buy_signals >= 2 and combined_confidence > 0.6:\n            signal = TradingSignal.STRONG_BUY if combined_confidence > 0.8 else TradingSignal.BUY\n        elif sell_signals >= 2 and combined_confidence > 0.6:\n            signal = TradingSignal.STRONG_SELL if combined_confidence > 0.8 else TradingSignal.SELL\n        else:\n            signal = TradingSignal.HOLD\n        \n        return {\n            \"signal\": signal.value,\n            \"confidence\": combined_confidence,\n            \"reason\": f\"AI Hybrid: {buy_signals} buy, {sell_signals} sell signals\"\n        }\n    \n    def _calculate_weighted_signal(self, signals: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Calculate final weighted trading signal\"\"\"\n        \n        weighted_score = 0\n        total_weight = 0\n        \n        for strategy_name, signal_data in signals.items():\n            if strategy_name == \"ai_hybrid\":\n                continue  # Skip AI hybrid in weighting to avoid double counting\n                \n            strategy_type = StrategyType(strategy_name) if strategy_name in [s.value for s in StrategyType] else None\n            if not strategy_type:\n                continue\n                \n            weight = self.strategy_weights.get(strategy_type, 0)\n            confidence = signal_data.get(\"confidence\", 0)\n            signal_value = self._signal_to_numeric(signal_data.get(\"signal\", \"HOLD\"))\n            \n            weighted_score += weight * confidence * signal_value\n            total_weight += weight * confidence\n        \n        # Add AI hybrid with higher weight\n        ai_signal = signals.get(\"ai_hybrid\", {})\n        ai_weight = self.strategy_weights.get(StrategyType.AI_HYBRID, 0.4)\n        ai_confidence = ai_signal.get(\"confidence\", 0)\n        ai_signal_value = self._signal_to_numeric(ai_signal.get(\"signal\", \"HOLD\"))\n        \n        weighted_score += ai_weight * ai_confidence * ai_signal_value\n        total_weight += ai_weight * ai_confidence\n        \n        if total_weight > 0:\n            final_score = weighted_score / total_weight\n            final_confidence = min(total_weight, 1.0)\n        else:\n            final_score = 0\n            final_confidence = 0.3\n        \n        # Convert numeric score back to signal\n        if final_score > 0.6:\n            final_signal = TradingSignal.BUY\n        elif final_score < -0.6:\n            final_signal = TradingSignal.SELL\n        else:\n            final_signal = TradingSignal.HOLD\n        \n        return {\n            \"signal\": final_signal.value,\n            \"confidence\": final_confidence,\n            \"score\": final_score,\n            \"reason\": \"Weighted average of all strategies\"\n        }\n    \n    def _signal_to_numeric(self, signal: str) -> float:\n        \"\"\"Convert signal to numeric value for calculations\"\"\"\n        signal_map = {\n            \"STRONG_BUY\": 1.0,\n            \"BUY\": 0.5,\n            \"HOLD\": 0.0,\n            \"SELL\": -0.5,\n            \"STRONG_SELL\": -1.0\n        }\n        return signal_map.get(signal, 0.0)\n    \n    async def _identify_trading_opportunity(self, symbol: str, analysis: MarketAnalysis, \n                                          signals: Dict[str, Any]) -> Optional[TradingOpportunity]:\n        \"\"\"Identify concrete trading opportunities\"\"\"\n        \n        final_signal = signals.get(\"final\", {})\n        signal_type = final_signal.get(\"signal\", \"HOLD\")\n        confidence = final_signal.get(\"confidence\", 0)\n        \n        if signal_type == \"HOLD\" or confidence < self.confidence_threshold:\n            return None\n        \n        current_price = analysis.technical_indicators.get(\"sma_20\", 0)\n        \n        if signal_type in [\"BUY\", \"STRONG_BUY\"]:\n            entry_price = current_price\n            stop_loss = min(analysis.support_levels) if analysis.support_levels else current_price * 0.95\n            target_price = max(analysis.resistance_levels) if analysis.resistance_levels else current_price * 1.05\n            \n        else:  # SELL or STRONG_SELL\n            entry_price = current_price\n            stop_loss = max(analysis.resistance_levels) if analysis.resistance_levels else current_price * 1.05\n            target_price = min(analysis.support_levels) if analysis.support_levels else current_price * 0.95\n        \n        # Calculate risk-reward ratio\n        risk = abs(entry_price - stop_loss)\n        reward = abs(target_price - entry_price)\n        risk_reward = reward / risk if risk > 0 else 1.0\n        \n        # Only consider opportunities with good risk-reward\n        if risk_reward < 1.5:\n            return None\n        \n        return TradingOpportunity(\n            symbol=symbol,\n            signal=TradingSignal(signal_type),\n            confidence=confidence,\n            entry_price=entry_price,\n            target_price=target_price,\n            stop_loss=stop_loss,\n            strategy=StrategyType.AI_HYBRID,\n            reasoning=final_signal.get(\"reason\", \"\"),\n            risk_reward=risk_reward,\n            timestamp=datetime.now()\n        )\n    \n    def _generate_market_overview(self, analyses: Dict[str, Dict]) -> Dict[str, Any]:\n        \"\"\"Generate overall market overview\"\"\"\n        \n        if not analyses:\n            return {\"status\": \"No data available\"}\n        \n        trends = []\n        opportunities = 0\n        avg_confidence = 0\n        \n        for symbol, data in analyses.items():\n            analysis = data.get(\"analysis\", {})\n            opportunity = data.get(\"opportunity\")\n            \n            if analysis.get(\"trend\"):\n                trends.append(analysis[\"trend\"])\n            \n            if opportunity:\n                opportunities += 1\n                avg_confidence += opportunity.get(\"confidence\", 0)\n        \n        # Calculate market sentiment\n        bullish_count = trends.count(\"BULLISH\")\n        bearish_count = trends.count(\"BEARISH\")\n        sideways_count = trends.count(\"SIDEWAYS\")\n        \n        if bullish_count > bearish_count + sideways_count:\n            market_sentiment = \"BULLISH\"\n        elif bearish_count > bullish_count + sideways_count:\n            market_sentiment = \"BEARISH\"\n        else:\n            market_sentiment = \"MIXED\"\n        \n        avg_confidence = (avg_confidence / opportunities) if opportunities > 0 else 0\n        \n        return {\n            \"market_sentiment\": market_sentiment,\n            \"bullish_stocks\": bullish_count,\n            \"bearish_stocks\": bearish_count,\n            \"sideways_stocks\": sideways_count,\n            \"trading_opportunities\": opportunities,\n            \"average_confidence\": avg_confidence,\n            \"recommendation\": self._get_market_recommendation(market_sentiment, avg_confidence)\n        }\n    \n    def _get_market_recommendation(self, sentiment: str, confidence: float) -> str:\n        \"\"\"Get overall market recommendation\"\"\"\n        \n        if sentiment == \"BULLISH\" and confidence > 0.7:\n            return \"Strong market conditions. Consider increasing long positions.\"\n        elif sentiment == \"BEARISH\" and confidence > 0.7:\n            return \"Weak market conditions. Consider defensive positions or hedging.\"\n        elif confidence > 0.6:\n            return \"Selective opportunities available. Focus on high-confidence trades.\"\n        else:\n            return \"Mixed market conditions. Exercise caution and wait for clearer signals.\"\n\n# Global instance\nai_trading_strategy_engine = AITradingStrategyEngine()