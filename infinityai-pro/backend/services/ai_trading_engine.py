"""
AI Trading Engine - Comprehensive Market Analysis and Trading Signals
Integrates with Dhan API for real-time data and generates trading recommendations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import numpy as np
from dataclasses import dataclass

from .dhan_api_service import DhanAPIService

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    symbol: str
    action: str  # BUY, SELL, HOLD
    price: float
    confidence: float
    reason: str
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    quantity: Optional[int] = None
    risk_reward: Optional[float] = None

@dataclass
class MarketAnalysis:
    symbol: str
    current_price: float
    price_change: float
    price_change_percent: float
    volume_analysis: Dict[str, Any]
    technical_indicators: Dict[str, float]
    sentiment_score: float
    risk_level: str
    trading_signal: TradingSignal

class AITradingEngine:
    """Advanced AI Trading Engine with real-time analysis capabilities"""
    
    def __init__(self, dhan_service: DhanAPIService):
        self.dhan_service = dhan_service
        self.is_initialized = False
        self.market_indices = ['NSE_IDX|Nifty 50', 'NSE_IDX|Nifty Bank']
        self.popular_stocks = [
            'NSE_EQ|INE062A01020',  # TCS
            'NSE_EQ|INE009A01021',  # Infosys
            'NSE_EQ|INE467B01029',  # ITC
            'NSE_EQ|INE040A01034',  # HDFC Bank
            'NSE_EQ|INE002A01018'   # Reliance
        ]
        
    async def initialize(self):
        """Initialize the AI trading engine"""
        try:
            logger.info("Initializing AI Trading Engine...")
            self.is_initialized = True
            logger.info("✅ AI Trading Engine initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Trading Engine: {e}")
            raise

    async def analyze_symbol(self, security_id: str) -> MarketAnalysis:
        """Perform comprehensive analysis on a single symbol"""
        try:
            # Get real-time market data
            quote_data = await self.dhan_service.get_market_quote([security_id])
            
            if not quote_data or 'data' not in quote_data:
                raise ValueError(f"No market data available for {security_id}")
            
            symbol_data = quote_data['data'].get(security_id, {})
            
            # Extract basic price information
            current_price = float(symbol_data.get('LTP', 0))
            open_price = float(symbol_data.get('open', current_price))
            high_price = float(symbol_data.get('high', current_price))
            low_price = float(symbol_data.get('low', current_price))
            volume = int(symbol_data.get('volume', 0))
            
            # Calculate price change
            price_change = current_price - open_price
            price_change_percent = (price_change / open_price * 100) if open_price > 0 else 0
            
            # Perform technical analysis
            technical_indicators = await self._calculate_technical_indicators(
                current_price, open_price, high_price, low_price, volume
            )
            
            # Volume analysis
            volume_analysis = self._analyze_volume(volume, symbol_data)
            
            # Sentiment analysis
            sentiment_score = await self._analyze_sentiment(security_id, price_change_percent)
            
            # Risk assessment
            risk_level = self._assess_risk(technical_indicators, sentiment_score, price_change_percent)
            
            # Generate trading signal
            trading_signal = await self._generate_trading_signal(
                security_id, current_price, technical_indicators, 
                sentiment_score, risk_level, price_change_percent
            )
            
            return MarketAnalysis(
                symbol=security_id,
                current_price=current_price,
                price_change=price_change,
                price_change_percent=price_change_percent,
                volume_analysis=volume_analysis,
                technical_indicators=technical_indicators,
                sentiment_score=sentiment_score,
                risk_level=risk_level,
                trading_signal=trading_signal
            )
            
        except Exception as e:
            logger.error(f"Error analyzing symbol {security_id}: {e}")
            raise

    async def analyze_multiple_symbols(self, security_ids: List[str]) -> List[MarketAnalysis]:
        """Analyze multiple symbols concurrently"""
        tasks = [self.analyze_symbol(security_id) for security_id in security_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        analyses = []
        for result in results:
            if isinstance(result, MarketAnalysis):
                analyses.append(result)
            else:
                logger.error(f"Analysis failed: {result}")
                
        return analyses

    async def get_market_pulse(self) -> Dict[str, Any]:
        """Get overall market pulse and key statistics"""
        try:
            # Analyze key indices
            index_analyses = await self.analyze_multiple_symbols(self.market_indices)
            
            # Analyze popular stocks
            stock_analyses = await self.analyze_multiple_symbols(self.popular_stocks[:3])
            
            # Calculate market sentiment
            all_analyses = index_analyses + stock_analyses
            avg_sentiment = np.mean([analysis.sentiment_score for analysis in all_analyses]) if all_analyses else 0
            
            # Market statistics
            positive_signals = len([a for a in all_analyses if a.trading_signal.action == 'BUY'])
            negative_signals = len([a for a in all_analyses if a.trading_signal.action == 'SELL'])
            
            market_trend = "BULLISH" if positive_signals > negative_signals else "BEARISH" if negative_signals > positive_signals else "NEUTRAL"
            
            return {
                "timestamp": datetime.now().isoformat(),
                "market_trend": market_trend,
                "overall_sentiment": avg_sentiment,
                "indices_analysis": [
                    {
                        "symbol": analysis.symbol,
                        "price": analysis.current_price,
                        "change_percent": analysis.price_change_percent,
                        "signal": analysis.trading_signal.action
                    }
                    for analysis in index_analyses
                ],
                "top_stocks": [
                    {
                        "symbol": analysis.symbol,
                        "price": analysis.current_price,
                        "change_percent": analysis.price_change_percent,
                        "signal": analysis.trading_signal.action,
                        "confidence": analysis.trading_signal.confidence
                    }
                    for analysis in stock_analyses
                ],
                "signals_summary": {
                    "buy_signals": positive_signals,
                    "sell_signals": negative_signals,
                    "total_analyzed": len(all_analyses)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting market pulse: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "failed"
            }

    async def find_trading_opportunities(self, min_confidence: float = 0.7) -> List[Dict[str, Any]]:
        """Find high-confidence trading opportunities"""
        try:
            # Analyze popular stocks for opportunities
            analyses = await self.analyze_multiple_symbols(self.popular_stocks)
            
            opportunities = []
            for analysis in analyses:
                if analysis.trading_signal.confidence >= min_confidence and analysis.trading_signal.action != 'HOLD':
                    opportunities.append({
                        "symbol": analysis.symbol,
                        "action": analysis.trading_signal.action,
                        "price": analysis.current_price,
                        "confidence": analysis.trading_signal.confidence,
                        "reason": analysis.trading_signal.reason,
                        "risk_reward": analysis.trading_signal.risk_reward,
                        "stop_loss": analysis.trading_signal.stop_loss,
                        "target": analysis.trading_signal.target,
                        "risk_level": analysis.risk_level
                    })
            
            # Sort by confidence
            opportunities.sort(key=lambda x: x['confidence'], reverse=True)
            
            return opportunities[:10]  # Return top 10 opportunities
            
        except Exception as e:
            logger.error(f"Error finding trading opportunities: {e}")
            return []

    async def _calculate_technical_indicators(self, current: float, open_price: float, 
                                           high: float, low: float, volume: int) -> Dict[str, float]:
        """Calculate technical indicators"""
        try:
            # Basic indicators based on current session data
            price_range = high - low
            range_percent = (price_range / open_price * 100) if open_price > 0 else 0
            
            # Position in range
            if price_range > 0:
                position_in_range = (current - low) / price_range
            else:
                position_in_range = 0.5
                
            # Simple momentum indicator
            momentum = (current - open_price) / open_price if open_price > 0 else 0
            
            # Volume-price trend (simplified)
            vpt = volume * (momentum if momentum != 0 else 0.01)
            
            return {
                "price_range_percent": range_percent,
                "position_in_range": position_in_range,
                "momentum": momentum,
                "volume_price_trend": vpt,
                "volatility_score": min(range_percent / 2, 10),  # Normalized volatility
                "strength_index": position_in_range * 100  # RSI-like indicator
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}

    def _analyze_volume(self, volume: int, symbol_data: Dict) -> Dict[str, Any]:
        """Analyze volume patterns"""
        try:
            # Get average volume (using mock data for now)
            avg_volume = volume * 0.8  # Assume current is 20% above average
            
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            
            if volume_ratio > 1.5:
                volume_signal = "HIGH"
                volume_strength = "Strong"
            elif volume_ratio > 1.2:
                volume_signal = "ABOVE_AVERAGE"
                volume_strength = "Moderate"
            elif volume_ratio < 0.7:
                volume_signal = "LOW"
                volume_strength = "Weak"
            else:
                volume_signal = "NORMAL"
                volume_strength = "Normal"
                
            return {
                "current_volume": volume,
                "volume_ratio": volume_ratio,
                "volume_signal": volume_signal,
                "volume_strength": volume_strength
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume: {e}")
            return {"volume_signal": "UNKNOWN", "volume_strength": "Unknown"}

    async def _analyze_sentiment(self, security_id: str, price_change_percent: float) -> float:
        """Analyze market sentiment for the symbol"""
        try:
            # Basic sentiment based on price movement
            base_sentiment = 0.5 + (price_change_percent / 200)  # Normalize to 0-1
            
            # Clamp between 0 and 1
            sentiment = max(0, min(1, base_sentiment))
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 0.5

    def _assess_risk(self, technical_indicators: Dict[str, float], 
                    sentiment_score: float, price_change_percent: float) -> str:
        """Assess overall risk level"""
        try:
            risk_score = 0
            
            # Volatility risk
            volatility = technical_indicators.get('volatility_score', 0)
            if volatility > 5:
                risk_score += 2
            elif volatility > 3:
                risk_score += 1
                
            # Sentiment risk
            if sentiment_score < 0.3 or sentiment_score > 0.7:
                risk_score += 1
                
            # Price movement risk
            if abs(price_change_percent) > 3:
                risk_score += 2
            elif abs(price_change_percent) > 1:
                risk_score += 1
                
            if risk_score >= 4:
                return "HIGH"
            elif risk_score >= 2:
                return "MEDIUM"
            else:
                return "LOW"
                
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return "MEDIUM"

    async def _generate_trading_signal(self, security_id: str, current_price: float,
                                     technical_indicators: Dict[str, float], 
                                     sentiment_score: float, risk_level: str,
                                     price_change_percent: float) -> TradingSignal:
        """Generate trading signal based on analysis"""
        try:
            signal_strength = 0
            reasons = []
            
            # Technical analysis signals
            momentum = technical_indicators.get('momentum', 0)
            position_in_range = technical_indicators.get('position_in_range', 0.5)
            strength_index = technical_indicators.get('strength_index', 50)
            
            # Momentum signal
            if momentum > 0.02:  # 2% positive momentum
                signal_strength += 2
                reasons.append("Strong upward momentum")
            elif momentum < -0.02:  # 2% negative momentum
                signal_strength -= 2
                reasons.append("Strong downward momentum")
                
            # Position in range signal
            if position_in_range > 0.8:
                signal_strength += 1
                reasons.append("Price near day high")
            elif position_in_range < 0.2:
                signal_strength -= 1
                reasons.append("Price near day low")
                
            # Sentiment signal
            if sentiment_score > 0.6:
                signal_strength += 1
                reasons.append("Positive market sentiment")
            elif sentiment_score < 0.4:
                signal_strength -= 1
                reasons.append("Negative market sentiment")
                
            # Volume confirmation would go here
            
            # Determine action
            if signal_strength >= 3:
                action = "BUY"
                confidence = min(0.9, 0.6 + (signal_strength - 3) * 0.1)
            elif signal_strength <= -3:
                action = "SELL"
                confidence = min(0.9, 0.6 + abs(signal_strength + 3) * 0.1)
            else:
                action = "HOLD"
                confidence = 0.5
                
            # Calculate stop loss and target
            stop_loss = None
            target = None
            risk_reward = None
            
            if action == "BUY":
                stop_loss = current_price * 0.98  # 2% stop loss
                target = current_price * 1.06     # 6% target
                risk_reward = 3.0  # 6% gain / 2% loss
            elif action == "SELL":
                stop_loss = current_price * 1.02  # 2% stop loss
                target = current_price * 0.94     # 6% target
                risk_reward = 3.0
                
            return TradingSignal(
                symbol=security_id,
                action=action,
                price=current_price,
                confidence=confidence,
                reason="; ".join(reasons) if reasons else f"Neutral signal with {signal_strength} strength",
                stop_loss=stop_loss,
                target=target,
                risk_reward=risk_reward
            )
            
        except Exception as e:
            logger.error(f"Error generating trading signal: {e}")
            return TradingSignal(
                symbol=security_id,
                action="HOLD",
                price=current_price,
                confidence=0.5,
                reason=f"Analysis error: {str(e)}"
            )

    async def get_sector_analysis(self) -> Dict[str, Any]:
        """Analyze different market sectors"""
        try:
            # This would ideally analyze sector-wise stocks
            # For now, return a basic sector overview
            sectors = {
                "IT": {"trend": "BULLISH", "strength": 0.7, "top_stocks": ["TCS", "INFY"]},
                "Banking": {"trend": "NEUTRAL", "strength": 0.5, "top_stocks": ["HDFCBANK", "ICICIBANK"]},
                "FMCG": {"trend": "BEARISH", "strength": 0.3, "top_stocks": ["ITC", "HUL"]},
                "Auto": {"trend": "BULLISH", "strength": 0.6, "top_stocks": ["MARUTI", "TATAMOTORS"]},
                "Pharma": {"trend": "NEUTRAL", "strength": 0.4, "top_stocks": ["SUNPHARMA", "DRREDDY"]}
            }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "sectors": sectors,
                "market_leader": max(sectors.keys(), key=lambda k: sectors[k]["strength"]),
                "market_laggard": min(sectors.keys(), key=lambda k: sectors[k]["strength"])
            }
            
        except Exception as e:
            logger.error(f"Error in sector analysis: {e}")
            return {"error": str(e)}

    def get_system_status(self) -> Dict[str, Any]:
        """Get AI trading engine system status"""
        return {
            "initialized": self.is_initialized,
            "dhan_service_connected": self.dhan_service is not None,
            "supported_analyses": [
                "Technical Analysis",
                "Sentiment Analysis", 
                "Volume Analysis",
                "Risk Assessment",
                "Trading Signals"
            ],
            "last_updated": datetime.now().isoformat()
        }

# Global instance
ai_trading_engine = None

def get_ai_trading_engine() -> AITradingEngine:
    """Get the global AI trading engine instance"""
    global ai_trading_engine
    if ai_trading_engine is None:
        from .dhan_api_service import dhan_service
        ai_trading_engine = AITradingEngine(dhan_service)
    return ai_trading_engine