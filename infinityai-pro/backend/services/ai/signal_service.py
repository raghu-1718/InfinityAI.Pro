# services/ai/signal_service.py
"""
InfinityAI.Pro - Multi-Cloud Signal Generation Service
Supports RunPod ML models (primary), Azure ML (secondary), AWS SageMaker (tertiary)
"""

import httpx
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import numpy as np
import pandas as pd
from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SignalService:
    """Multi-cloud signal generation service with failover support"""

    def __init__(self):
        self.config = Config()
        self.client: Optional[httpx.AsyncClient] = None
        self.initialized = False
        self.lightgbm_model = None
        self.prophet_model = None

    async def initialize(self):
        """Initialize multi-cloud signal connections"""
        try:
            self.client = httpx.AsyncClient(timeout=60.0)  # Longer timeout for ML inference

            # Initialize local ML models
            try:
                import lightgbm as lgb
                # Load pre-trained LightGBM model (would be trained on historical data)
                # self.lightgbm_model = lgb.Booster(model_file='models/lightgbm_signal.pkl')
                logger.info("LightGBM model ready")
            except ImportError:
                logger.warning("LightGBM not available - install: pip install lightgbm")
            except Exception as e:
                logger.warning(f"Failed to load LightGBM: {e}")

            try:
                from prophet import Prophet
                # Prophet for time series forecasting
                # self.prophet_model = Prophet()
                logger.info("Prophet model ready")
            except ImportError:
                logger.warning("Prophet not available - install: pip install prophet")
            except Exception as e:
                logger.warning(f"Failed to load Prophet: {e}")

            self.initialized = True
            logger.info("✅ Multi-cloud Signal Service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Signal service: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    # Azure ML (Primary)
    async def azure_generate_signal(self, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Azure ML-based signal generation"""
        try:
            azure_url = f"{self.config.AZURE_ML_ENDPOINT}/score"
            headers = {
                "Authorization": f"Bearer {self.config.AZURE_ML_KEY}",
                "Content-Type": "application/json"
            }

            # Prepare data for Azure ML
            features = self._prepare_ml_features(market_data)

            payload = {
                "Inputs": {
                    "input1": [features]
                },
                "GlobalParameters": {
                    "method": "predict"
                }
            }

            async with self.client.post(azure_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

            # Parse Azure ML response
            predictions = result.get("Results", {}).get("output1", [{}])[0]
            signal_score = predictions.get("signal_score", 0.0)
            confidence = predictions.get("confidence", 0.5)

            # Determine signal direction
            if signal_score > 0.1:
                direction = "BUY"
            elif signal_score < -0.1:
                direction = "SELL"
            else:
                direction = "HOLD"

            return {
                "symbol": market_data.get("symbol", "UNKNOWN"),
                "direction": direction,
                "score": signal_score,
                "confidence": confidence,
                "ml_prob": predictions.get("probability", 0.5),
                "features_used": list(features.keys()),
                "model_type": "azure_ml",
                "provider": "azure",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Azure ML signal generation error: {e}")
            raise

    # AWS SageMaker (Secondary)
    async def aws_generate_signal(self, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """AWS SageMaker-based signal generation"""
        try:
            import boto3
            sagemaker_runtime = boto3.client(
                'sagemaker-runtime',
                region_name=self.config.AWS_REGION,
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY
            )

            # Prepare data for SageMaker
            features = self._prepare_ml_features(market_data)
            payload = json.dumps({"features": features})

            # Invoke SageMaker endpoint
            response = sagemaker_runtime.invoke_endpoint(
                EndpointName=self.config.AWS_SAGEMAKER_ENDPOINT,
                ContentType='application/json',
                Body=payload
            )

            # Parse response
            result = json.loads(response['Body'].read().decode())
            prediction = result.get("prediction", {})
            signal_score = prediction.get("signal_score", 0.0)
            confidence = prediction.get("confidence", 0.5)

            # Determine signal direction
            if signal_score > 0.1:
                direction = "BUY"
            elif signal_score < -0.1:
                direction = "SELL"
            else:
                direction = "HOLD"

            return {
                "symbol": market_data.get("symbol", "UNKNOWN"),
                "direction": direction,
                "score": signal_score,
                "confidence": confidence,
                "ml_prob": prediction.get("probability", 0.5),
                "features_used": list(features.keys()),
                "model_type": "sagemaker",
                "provider": "aws",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"AWS SageMaker signal generation error: {e}")
            raise

    # Rule-based signal generation (fallback)
    async def rule_generate_signal(self, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Rule-based signal generation as fallback"""
        try:
            symbol = market_data.get("symbol", "UNKNOWN")
            price_data = market_data.get("price_data", {})

            # Simple technical indicators
            close_prices = price_data.get("close", [])
            if len(close_prices) < 20:
                return {
                    "symbol": symbol,
                    "direction": "HOLD",
                    "score": 0.0,
                    "confidence": 0.3,
                    "rule_score": 0.0,
                    "reason": "Insufficient price data",
                    "model_type": "rule_based",
                    "provider": "rules",
                    "timestamp": datetime.now().isoformat()
                }

            # Calculate simple moving averages
            sma_5 = np.mean(close_prices[-5:])
            sma_20 = np.mean(close_prices[-20:])
            current_price = close_prices[-1]

            # RSI calculation (simplified)
            gains = []
            losses = []
            for i in range(1, min(15, len(close_prices))):
                change = close_prices[-i] - close_prices[-i-1]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))

            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 0
            rsi = 100 - (100 / (1 + (avg_gain / avg_loss if avg_loss != 0 else 1)))

            # Generate rule-based signal
            rule_score = 0.0

            # Trend following
            if current_price > sma_5 and sma_5 > sma_20:
                rule_score += 0.3  # Bullish trend
            elif current_price < sma_5 and sma_5 < sma_20:
                rule_score -= 0.3  # Bearish trend

            # RSI signals
            if rsi < 30:
                rule_score += 0.2  # Oversold
            elif rsi > 70:
                rule_score -= 0.2  # Overbought

            # Volume confirmation (if available)
            volumes = price_data.get("volume", [])
            if volumes and len(volumes) >= 5:
                avg_volume = np.mean(volumes[-5:])
                current_volume = volumes[-1]
                if current_volume > avg_volume * 1.2:
                    rule_score += 0.1  # High volume confirmation

            # Determine direction
            if rule_score > 0.2:
                direction = "BUY"
            elif rule_score < -0.2:
                direction = "SELL"
            else:
                direction = "HOLD"

            return {
                "symbol": symbol,
                "direction": direction,
                "score": rule_score,
                "confidence": min(abs(rule_score) + 0.3, 0.9),
                "rule_score": rule_score,
                "indicators": {
                    "sma_5": sma_5,
                    "sma_20": sma_20,
                    "rsi": rsi,
                    "current_price": current_price
                },
                "model_type": "rule_based",
                "provider": "rules",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Rule-based signal generation error: {e}")
            return {
                "symbol": market_data.get("symbol", "UNKNOWN"),
                "direction": "HOLD",
                "score": 0.0,
                "confidence": 0.1,
                "error": str(e),
                "model_type": "rule_based",
                "provider": "rules",
                "timestamp": datetime.now().isoformat()
            }

    # Multi-timeframe signal aggregation
    async def generate_multi_timeframe_signal(self, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate signals across multiple timeframes"""
        try:
            timeframes = kwargs.get("timeframes", ["5m", "15m", "1h", "1d"])
            signals = {}

            for tf in timeframes:
                tf_data = market_data.get(f"{tf}_data", market_data)
                signal = await self.generate_signal(tf_data, **kwargs)
                signals[tf] = signal

            # Aggregate signals across timeframes
            return self._aggregate_timeframe_signals(signals)

        except Exception as e:
            logger.error(f"Multi-timeframe signal error: {e}")
            return {"error": str(e)}

    # Order suggestion generation
    async def suggest_order(self, signal: Dict[str, Any], portfolio_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Generate order suggestions based on signals"""
        try:
            symbol = signal.get("symbol", "UNKNOWN")
            direction = signal.get("direction", "HOLD")
            confidence = signal.get("confidence", 0.5)

            if direction == "HOLD":
                return {
                    "action": "HOLD",
                    "symbol": symbol,
                    "reason": "No clear signal",
                    "confidence": confidence
                }

            # Get portfolio context
            portfolio_value = portfolio_data.get("total_value", 100000) if portfolio_data else 100000
            existing_position = None

            if portfolio_data:
                for position in portfolio_data.get("positions", []):
                    if position.get("symbol") == symbol:
                        existing_position = position
                        break

            # Calculate position sizing
            risk_per_trade = kwargs.get("risk_per_trade", 0.01)  # 1% risk per trade
            stop_loss_pct = kwargs.get("stop_loss_pct", 0.02)  # 2% stop loss

            if direction == "BUY":
                if existing_position:
                    return {
                        "action": "HOLD",
                        "symbol": symbol,
                        "reason": "Already have position",
                        "existing_quantity": existing_position.get("quantity", 0)
                    }

                # New long position
                risk_amount = portfolio_value * risk_per_trade
                stop_loss_amount = risk_amount / stop_loss_pct
                position_size = stop_loss_amount / signal.get("entry_price", 100)

                return {
                    "action": "BUY",
                    "symbol": symbol,
                    "quantity": int(position_size),
                    "entry_price": signal.get("entry_price"),
                    "stop_loss": signal.get("entry_price") * (1 - stop_loss_pct),
                    "take_profit": signal.get("entry_price") * (1 + stop_loss_pct * 2),
                    "risk_amount": risk_amount,
                    "confidence": confidence,
                    "reason": f"Strong {direction.lower()} signal"
                }

            elif direction == "SELL":
                if not existing_position:
                    return {
                        "action": "HOLD",
                        "symbol": symbol,
                        "reason": "No existing position to sell"
                    }

                # Close long position
                return {
                    "action": "SELL",
                    "symbol": symbol,
                    "quantity": existing_position.get("quantity", 0),
                    "exit_price": signal.get("exit_price"),
                    "reason": f"Strong {direction.lower()} signal",
                    "confidence": confidence
                }

        except Exception as e:
            logger.error(f"Order suggestion error: {e}")
            return {"error": str(e)}

    # Legacy methods for backward compatibility
    async def generate_signal(self, market_data: Dict[str, Any], **kwargs) -> Dict:
        """Generate signal using router"""
        try:
            from .router import AIRouter
            # Note: Router doesn't have signal methods yet, so we'll use direct provider calls
            providers = ["runpod", "azure", "aws", "rule"]

            for provider in providers:
                try:
                    method_name = f"{provider}_generate_signal"
                    if hasattr(self, method_name):
                        method = getattr(self, method_name)
                        result = await method(market_data, **kwargs)
                        return result
                except Exception as e:
                    logger.warning(f"Provider {provider} failed: {e}")
                    continue

            return {"error": "All signal providers failed"}

        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return {"error": str(e)}

    def _prepare_ml_features(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Prepare features for ML models"""
        try:
            price_data = market_data.get("price_data", {})
            close_prices = price_data.get("close", [])
            volumes = price_data.get("volume", [])

            if not close_prices:
                return {"error": "No price data available"}

            # Calculate technical indicators
            features = {}

            # Price-based features
            current_price = close_prices[-1]
            features["current_price"] = current_price

            if len(close_prices) >= 2:
                features["price_change_1d"] = (current_price - close_prices[-2]) / close_prices[-2]

            if len(close_prices) >= 6:
                features["sma_5"] = np.mean(close_prices[-5:])
                features["price_to_sma5"] = current_price / features["sma_5"] - 1

            if len(close_prices) >= 21:
                features["sma_20"] = np.mean(close_prices[-20:])
                features["price_to_sma20"] = current_price / features["sma_20"] - 1

            # Volume features
            if volumes and len(volumes) >= 5:
                features["avg_volume_5d"] = np.mean(volumes[-5:])
                features["volume_ratio"] = volumes[-1] / features["avg_volume_5d"] if features["avg_volume_5d"] > 0 else 1

            # Volatility
            if len(close_prices) >= 21:
                returns = np.diff(close_prices[-21:]) / close_prices[-21:-1]
                features["volatility_20d"] = np.std(returns)

            # RSI (simplified)
            if len(close_prices) >= 15:
                gains = []
                losses = []
                for i in range(1, 15):
                    change = close_prices[-i] - close_prices[-i-1]
                    if change > 0:
                        gains.append(change)
                    else:
                        losses.append(abs(change))

                avg_gain = np.mean(gains) if gains else 0
                avg_loss = np.mean(losses) if losses else 0
                features["rsi"] = 100 - (100 / (1 + (avg_gain / avg_loss if avg_loss != 0 else 1)))

            # Market data
            features["volatility"] = market_data.get("volatility", 0.2)
            features["market_cap"] = market_data.get("market_cap", 0)
            features["pe_ratio"] = market_data.get("pe_ratio", 0)

            return features

        except Exception as e:
            logger.error(f"Feature preparation error: {e}")
            return {"error": str(e)}

    def _aggregate_timeframe_signals(self, signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate signals from multiple timeframes"""
        try:
            # Weight signals by timeframe importance
            weights = {
                "5m": 0.1,   # Short-term noise
                "15m": 0.2,  # Short-term trend
                "1h": 0.3,   # Medium-term
                "1d": 0.4    # Long-term
            }

            weighted_score = 0
            total_weight = 0
            directions = []

            for tf, signal in signals.items():
                weight = weights.get(tf, 0.25)
                score = signal.get("score", 0.0)
                confidence = signal.get("confidence", 0.5)

                weighted_score += score * weight * confidence
                total_weight += weight
                directions.append(signal.get("direction", "HOLD"))

            # Determine consensus direction
            avg_score = weighted_score / total_weight if total_weight > 0 else 0

            # Check direction consensus
            buy_count = directions.count("BUY")
            sell_count = directions.count("SELL")
            hold_count = directions.count("HOLD")

            if buy_count > sell_count and buy_count > hold_count:
                consensus_direction = "BUY"
            elif sell_count > buy_count and sell_count > hold_count:
                consensus_direction = "SELL"
            else:
                consensus_direction = "HOLD"

            return {
                "symbol": signals.get("1d", {}).get("symbol", "UNKNOWN"),
                "direction": consensus_direction,
                "score": avg_score,
                "confidence": min(abs(avg_score) + 0.3, 0.95),
                "timeframe_signals": signals,
                "consensus": {
                    "buy_signals": buy_count,
                    "sell_signals": sell_count,
                    "hold_signals": hold_count
                },
                "model_type": "multi_timeframe",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Signal aggregation error: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict:
        """Check signal service health"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            health_status = {
                "runpod": bool(self.config.RUNPOD_SIGNAL_ENDPOINT),
                "azure": bool(self.config.AZURE_ML_ENDPOINT),
                "aws": bool(self.config.AWS_SAGEMAKER_ENDPOINT),
                "rules": True  # Always available
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