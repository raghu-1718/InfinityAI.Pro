"""
Engine B - AI Signal Processing Service
InfinityAI.Pro Trading Platform

GPU-accelerated AI consumer for processing market signals with:
- Ensemble machine learning models
- Multi-cloud GPU acceleration
- Real-time risk assessment
- Adaptive model selection
- Signal confidence scoring
"""

import os
import asyncio
import json
import time
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import numpy as np
import pandas as pd
from enum import Enum

import redis
import asyncpg
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configuration and utilities
from utils.config import get_settings
from utils.logging_config import setup_logging, get_structured_logger
from utils.metrics import MetricsCollector
from utils.circuit_breaker import CircuitBreaker

# Initialize logging
setup_logging()
logger = get_structured_logger(__name__)
settings = get_settings()

# Global state
kafka_consumer: Optional[AIOKafkaConsumer] = None
kafka_producer: Optional[AIOKafkaProducer] = None
redis_client: Optional[redis.Redis] = None
postgres_pool: Optional[asyncpg.Pool] = None
metrics_collector: Optional[MetricsCollector] = None

# AI Models
ai_models = {}
model_circuit_breaker: Optional[CircuitBreaker] = None

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    BUY_STRONG = "BUY_STRONG"
    SELL_STRONG = "SELL_STRONG"

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"

@dataclass
class MarketSignal:
    """Market signal from Engine A"""
    symbol: str
    timestamp: float
    signal_type: str
    confidence: float
    price: float
    volume: int
    indicators: Dict[str, float]
    metadata: Dict[str, Any]

@dataclass
class AISignal:
    """AI-processed signal with risk assessment"""
    signal_id: str
    symbol: str
    timestamp: float
    original_signal: str
    ai_signal: str
    confidence: float
    risk_score: float
    risk_level: str
    expected_return: float
    stop_loss: float
    target_price: float
    position_size: float
    model_ensemble: List[str]
    features: Dict[str, float]
    metadata: Dict[str, Any]

class TransformerPriceModel(nn.Module):
    """Transformer-based price prediction model"""
    
    def __init__(self, input_dim=50, hidden_dim=256, num_heads=8, num_layers=6):
        super().__init__()
        self.input_projection = nn.Linear(input_dim, hidden_dim)
        self.positional_encoding = PositionalEncoding(hidden_dim)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=0.1,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        
        self.output_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, 3)  # [price_change, confidence, risk]
        )
    
    def forward(self, x):
        # x shape: (batch_size, seq_len, features)
        x = self.input_projection(x)
        x = self.positional_encoding(x)
        x = self.transformer(x)
        
        # Use the last timestep for prediction
        x = x[:, -1, :]
        return self.output_head(x)

class PositionalEncoding(nn.Module):
    """Positional encoding for transformer"""
    
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        
        div_term = torch.exp(torch.arange(0, d_model, 2).float() *
                           -(np.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        self.register_buffer('pe', pe.unsqueeze(0))
    
    def forward(self, x):
        return x + self.pe[:, :x.size(1)]

class EnsembleAIProcessor:
    """Ensemble AI processor with multiple models"""
    
    def __init__(self, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.device = device
        self.models = {}
        self.scalers = {}
        self.feature_windows = {}
        self.model_weights = {}
        
        logger.info(f"Initializing AI processor on device: {device}")
        
    async def initialize_models(self):
        """Initialize all AI models"""
        try:
            # Load pre-trained transformer model
            await self._load_transformer_model()
            
            # Load ensemble models
            await self._load_ensemble_models()
            
            # Load feature scalers
            await self._load_scalers()
            
            logger.info("All AI models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            raise
    
    async def _load_transformer_model(self):
        """Load transformer-based price prediction model"""
        try:
            model_path = "/app/models/transformer_price_model.pt"
            
            # Try to load pre-trained model, otherwise create new
            try:
                self.models['transformer'] = torch.load(model_path, map_location=self.device)
                logger.info("Loaded pre-trained transformer model")
            except FileNotFoundError:
                self.models['transformer'] = TransformerPriceModel().to(self.device)
                logger.info("Created new transformer model")
            
            self.model_weights['transformer'] = 0.4
            
        except Exception as e:
            logger.error(f"Error loading transformer model: {e}")
            raise
    
    async def _load_ensemble_models(self):
        """Load ensemble of classical ML models"""
        try:
            model_configs = {
                'random_forest': {
                    'class': RandomForestRegressor,
                    'params': {
                        'n_estimators': 200,
                        'max_depth': 15,
                        'random_state': 42,
                        'n_jobs': -1
                    },
                    'weight': 0.25
                },
                'gradient_boost': {
                    'class': GradientBoostingRegressor,
                    'params': {
                        'n_estimators': 150,
                        'max_depth': 8,
                        'learning_rate': 0.1,
                        'random_state': 42
                    },
                    'weight': 0.35
                }
            }
            
            for model_name, config in model_configs.items():
                try:
                    model_path = f"/app/models/{model_name}.joblib"
                    self.models[model_name] = joblib.load(model_path)
                    logger.info(f"Loaded pre-trained {model_name} model")
                except FileNotFoundError:
                    self.models[model_name] = config['class'](**config['params'])
                    logger.info(f"Created new {model_name} model")
                
                self.model_weights[model_name] = config['weight']
            
        except Exception as e:
            logger.error(f"Error loading ensemble models: {e}")
            raise
    
    async def _load_scalers(self):
        """Load feature scalers"""
        try:
            scaler_names = ['price_scaler', 'volume_scaler', 'indicator_scaler']
            
            for scaler_name in scaler_names:
                try:
                    scaler_path = f"/app/models/{scaler_name}.joblib"
                    self.scalers[scaler_name] = joblib.load(scaler_path)
                    logger.info(f"Loaded {scaler_name}")
                except FileNotFoundError:
                    self.scalers[scaler_name] = StandardScaler()
                    logger.info(f"Created new {scaler_name}")
                    
        except Exception as e:
            logger.error(f"Error loading scalers: {e}")
            raise
    
    async def process_signal(self, market_signal: MarketSignal, 
                           historical_data: pd.DataFrame) -> AISignal:
        """Process market signal through AI ensemble"""
        start_time = time.time()
        
        try:
            # Extract features
            features = await self._extract_features(market_signal, historical_data)
            
            # Get predictions from ensemble
            predictions = await self._get_ensemble_predictions(features)
            
            # Calculate risk assessment
            risk_score, risk_level = await self._assess_risk(features, predictions)
            
            # Generate trading parameters
            trading_params = await self._generate_trading_params(
                market_signal, predictions, risk_score
            )
            
            # Create AI signal
            ai_signal = AISignal(
                signal_id=str(uuid.uuid4()),
                symbol=market_signal.symbol,
                timestamp=time.time(),
                original_signal=market_signal.signal_type,
                ai_signal=predictions['signal'],
                confidence=predictions['confidence'],
                risk_score=risk_score,
                risk_level=risk_level.value,
                expected_return=trading_params['expected_return'],
                stop_loss=trading_params['stop_loss'],
                target_price=trading_params['target_price'],
                position_size=trading_params['position_size'],
                model_ensemble=list(self.models.keys()),
                features=features,
                metadata={
                    'processing_time': time.time() - start_time,
                    'model_weights': self.model_weights,
                    'raw_predictions': predictions['raw']
                }
            )
            
            # Record metrics
            if metrics_collector:
                await metrics_collector.histogram(
                    'ai_processing_latency_ms',
                    (time.time() - start_time) * 1000,
                    tags={'symbol': market_signal.symbol}
                )
                await metrics_collector.increment(
                    'ai_signals_generated_total',
                    tags={'symbol': market_signal.symbol, 'signal': ai_signal.ai_signal}
                )
            
            logger.info(
                f"AI signal generated",
                symbol=market_signal.symbol,
                signal=ai_signal.ai_signal,
                confidence=ai_signal.confidence,
                risk_level=ai_signal.risk_level
            )
            
            return ai_signal
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            if metrics_collector:
                await metrics_collector.increment('ai_processing_errors_total')
            raise
    
    async def _extract_features(self, signal: MarketSignal, 
                              historical_data: pd.DataFrame) -> Dict[str, float]:
        """Extract comprehensive features for AI models"""
        try:
            features = {}
            
            # Price-based features
            current_price = signal.price
            features['current_price'] = current_price
            
            if len(historical_data) > 0:
                # Price momentum features
                features['price_change_1m'] = (current_price - historical_data['close'].iloc[-1]) / historical_data['close'].iloc[-1]
                features['price_change_5m'] = (current_price - historical_data['close'].iloc[-5]) / historical_data['close'].iloc[-5] if len(historical_data) >= 5 else 0
                features['price_change_15m'] = (current_price - historical_data['close'].iloc[-15]) / historical_data['close'].iloc[-15] if len(historical_data) >= 15 else 0
                
                # Volatility features
                returns = historical_data['close'].pct_change().dropna()
                features['volatility_1h'] = returns.tail(60).std() if len(returns) >= 60 else 0
                features['volatility_4h'] = returns.tail(240).std() if len(returns) >= 240 else 0
                
                # Volume features
                features['volume_ratio'] = signal.volume / historical_data['volume'].tail(20).mean() if len(historical_data) >= 20 else 1.0
                features['volume_trend'] = historical_data['volume'].tail(10).corr(pd.Series(range(10))) if len(historical_data) >= 10 else 0
            
            # Technical indicators from signal
            features.update(signal.indicators)
            
            # Market microstructure features
            features['bid_ask_spread'] = signal.metadata.get('bid_ask_spread', 0.001)
            features['market_impact'] = signal.metadata.get('market_impact', 0.0)
            features['order_flow'] = signal.metadata.get('order_flow', 0.0)
            
            # Time-based features
            now = datetime.fromtimestamp(signal.timestamp)
            features['hour'] = now.hour / 24.0
            features['minute'] = now.minute / 60.0
            features['day_of_week'] = now.weekday() / 6.0
            
            # Market regime features
            features['market_regime'] = await self._detect_market_regime(historical_data)
            features['trend_strength'] = signal.indicators.get('adx', 0) / 100.0
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}
    
    async def _get_ensemble_predictions(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Get predictions from ensemble of models"""
        try:
            predictions = {}
            raw_predictions = {}
            
            # Prepare feature array
            feature_array = np.array(list(features.values())).reshape(1, -1)
            
            # Get predictions from each model
            weighted_price_change = 0
            weighted_confidence = 0
            weighted_risk = 0
            
            for model_name, model in self.models.items():
                try:
                    if model_name == 'transformer':
                        pred = await self._predict_transformer(model, features)
                    else:
                        pred = model.predict(feature_array)[0] if hasattr(model, 'predict') else 0
                    
                    # Parse prediction based on model output
                    if isinstance(pred, (list, np.ndarray)) and len(pred) >= 3:
                        price_change, confidence, risk = pred[:3]
                    else:
                        price_change, confidence, risk = pred, 0.5, 0.5
                    
                    weight = self.model_weights.get(model_name, 0.1)
                    weighted_price_change += price_change * weight
                    weighted_confidence += confidence * weight
                    weighted_risk += risk * weight
                    
                    raw_predictions[model_name] = {
                        'price_change': float(price_change),
                        'confidence': float(confidence),
                        'risk': float(risk)
                    }
                    
                except Exception as e:
                    logger.warning(f"Model {model_name} prediction failed: {e}")
                    continue
            
            # Determine signal type
            if weighted_price_change > 0.02:  # > 2% expected return
                signal_type = SignalType.BUY_STRONG.value
            elif weighted_price_change > 0.005:  # > 0.5% expected return
                signal_type = SignalType.BUY.value
            elif weighted_price_change < -0.02:  # < -2% expected return
                signal_type = SignalType.SELL_STRONG.value
            elif weighted_price_change < -0.005:  # < -0.5% expected return
                signal_type = SignalType.SELL.value
            else:
                signal_type = SignalType.HOLD.value
            
            predictions = {
                'signal': signal_type,
                'price_change': weighted_price_change,
                'confidence': max(0.1, min(0.95, weighted_confidence)),
                'risk': max(0.1, min(0.9, weighted_risk)),
                'raw': raw_predictions
            }
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting ensemble predictions: {e}")
            return {
                'signal': SignalType.HOLD.value,
                'price_change': 0.0,
                'confidence': 0.5,
                'risk': 0.5,
                'raw': {}
            }
    
    async def _predict_transformer(self, model, features: Dict[str, float]) -> np.ndarray:
        """Get prediction from transformer model"""
        try:
            # Create sequence from features (simplified)
            feature_values = list(features.values())
            
            # Pad or truncate to expected input size
            if len(feature_values) < 50:
                feature_values.extend([0.0] * (50 - len(feature_values)))
            else:
                feature_values = feature_values[:50]
            
            # Create sequence tensor
            sequence = torch.tensor(feature_values, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(self.device)
            
            model.eval()
            with torch.no_grad():
                prediction = model(sequence)
                return prediction.cpu().numpy()[0]
                
        except Exception as e:
            logger.error(f"Transformer prediction error: {e}")
            return np.array([0.0, 0.5, 0.5])
    
    async def _assess_risk(self, features: Dict[str, float], 
                         predictions: Dict[str, Any]) -> Tuple[float, RiskLevel]:
        """Comprehensive risk assessment"""
        try:
            risk_factors = []
            
            # Market volatility risk
            volatility = features.get('volatility_1h', 0.02)
            vol_risk = min(1.0, volatility / 0.05)  # Normalize by 5% volatility
            risk_factors.append(vol_risk * 0.25)
            
            # Position size risk (based on volume)
            volume_ratio = features.get('volume_ratio', 1.0)
            volume_risk = 1.0 / (1.0 + volume_ratio)  # Lower volume = higher risk
            risk_factors.append(volume_risk * 0.15)
            
            # Prediction uncertainty risk
            confidence = predictions.get('confidence', 0.5)
            uncertainty_risk = 1.0 - confidence
            risk_factors.append(uncertainty_risk * 0.3)
            
            # Market microstructure risk
            bid_ask_spread = features.get('bid_ask_spread', 0.001)
            spread_risk = min(1.0, bid_ask_spread / 0.01)
            risk_factors.append(spread_risk * 0.1)
            
            # Trend consistency risk
            trend_strength = features.get('trend_strength', 0.5)
            trend_risk = 1.0 - trend_strength
            risk_factors.append(trend_risk * 0.2)
            
            # Calculate overall risk score
            risk_score = sum(risk_factors)
            
            # Determine risk level
            if risk_score < 0.25:
                risk_level = RiskLevel.LOW
            elif risk_score < 0.5:
                risk_level = RiskLevel.MEDIUM
            elif risk_score < 0.75:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.EXTREME
            
            return risk_score, risk_level
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return 0.5, RiskLevel.MEDIUM
    
    async def _generate_trading_params(self, signal: MarketSignal, 
                                     predictions: Dict[str, Any], 
                                     risk_score: float) -> Dict[str, float]:
        """Generate trading parameters based on AI analysis"""
        try:
            current_price = signal.price
            expected_return = predictions['price_change']
            confidence = predictions['confidence']
            
            # Calculate position size based on Kelly criterion with risk adjustment
            kelly_fraction = (confidence * expected_return) / (risk_score + 0.01)
            position_size = max(0.01, min(0.2, kelly_fraction * 0.5))  # Cap at 20%
            
            # Calculate stop loss (dynamic based on volatility and risk)
            volatility = signal.indicators.get('volatility', 0.02)
            stop_loss_pct = max(0.01, min(0.05, volatility * 2 + risk_score * 0.02))
            
            if expected_return > 0:
                stop_loss = current_price * (1 - stop_loss_pct)
                target_price = current_price * (1 + abs(expected_return) * confidence)
            else:
                stop_loss = current_price * (1 + stop_loss_pct)
                target_price = current_price * (1 - abs(expected_return) * confidence)
            
            return {
                'expected_return': expected_return,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'target_price': target_price
            }
            
        except Exception as e:
            logger.error(f"Error generating trading params: {e}")
            return {
                'expected_return': 0.0,
                'position_size': 0.01,
                'stop_loss': signal.price * 0.98,
                'target_price': signal.price * 1.02
            }
    
    async def _detect_market_regime(self, historical_data: pd.DataFrame) -> float:
        """Detect current market regime (trending vs ranging)"""
        try:
            if len(historical_data) < 50:
                return 0.5  # Neutral
            
            # Calculate trend strength using ADX-like logic
            high = historical_data['high'].tail(50)
            low = historical_data['low'].tail(50)
            close = historical_data['close'].tail(50)
            
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Average True Range
            atr = tr.rolling(14).mean()
            
            # Price range vs ATR
            price_range = close.max() - close.min()
            avg_atr = atr.mean()
            
            if avg_atr > 0:
                regime_score = min(1.0, price_range / (avg_atr * 14))
            else:
                regime_score = 0.5
            
            return regime_score
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return 0.5

# Global AI processor
ai_processor: Optional[EnsembleAIProcessor] = None

async def initialize_ai_models():
    """Initialize AI models"""
    global ai_processor, model_circuit_breaker
    
    # Initialize circuit breaker for AI models
    model_circuit_breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=30,
        half_open_max_calls=2,
        name="AI_Models"
    )
    
    ai_processor = EnsembleAIProcessor()
    await ai_processor.initialize_models()
    
    logger.info("AI models initialized successfully")

async def get_historical_data(symbol: str, lookback_minutes: int = 240) -> pd.DataFrame:
    """Get historical market data for the symbol"""
    try:
        # Try Redis cache first
        cache_key = f"history:{symbol}:{lookback_minutes}"
        cached_data = await redis_client.get(cache_key)
        
        if cached_data:
            data = json.loads(cached_data)
            return pd.DataFrame(data)
        
        # Get from database
        async with postgres_pool.acquire() as conn:
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM market_data_1m
                WHERE symbol = $1 AND timestamp >= $2
                ORDER BY timestamp
            """
            
            cutoff_time = time.time() - (lookback_minutes * 60)
            rows = await conn.fetch(query, symbol, cutoff_time)
            
            if rows:
                df = pd.DataFrame(rows)
                # Cache for 1 minute
                await redis_client.setex(
                    cache_key, 60, 
                    json.dumps(df.to_dict('records'))
                )
                return df
            else:
                return pd.DataFrame()
                
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        return pd.DataFrame()

async def consume_market_signals():
    """Consume market signals from Kafka and process with AI"""
    global kafka_consumer, ai_processor
    
    while True:
        try:
            if not kafka_consumer:
                await initialize_kafka_consumer()
            
            async for message in kafka_consumer:
                start_time = time.time()
                
                try:
                    signal_data = json.loads(message.value.decode('utf-8'))
                    
                    # Parse market signal
                    market_signal = MarketSignal(
                        symbol=signal_data['symbol'],
                        timestamp=signal_data['timestamp'],
                        signal_type=signal_data['signal_type'],
                        confidence=signal_data['confidence'],
                        price=signal_data['price'],
                        volume=signal_data['volume'],
                        indicators=signal_data['indicators'],
                        metadata=signal_data.get('metadata', {})
                    )
                    
                    # Get historical data
                    historical_data = await get_historical_data(market_signal.symbol)
                    
                    # Process with AI
                    if ai_processor and model_circuit_breaker and not model_circuit_breaker.is_open():
                        try:
                            ai_signal = await ai_processor.process_signal(market_signal, historical_data)
                            
                            # Publish AI signal to Kafka
                            await publish_ai_signal(ai_signal)
                            
                            model_circuit_breaker.record_success()
                            
                        except Exception as e:
                            model_circuit_breaker.record_failure()
                            logger.error(f"AI processing failed: {e}")
                            
                            # Publish fallback signal
                            await publish_fallback_signal(market_signal)
                    
                    else:
                        # Circuit breaker is open or AI not ready
                        await publish_fallback_signal(market_signal)
                    
                    # Record processing metrics
                    if metrics_collector:
                        await metrics_collector.histogram(
                            'signal_processing_latency_ms',
                            (time.time() - start_time) * 1000,
                            tags={'symbol': market_signal.symbol}
                        )
                        await metrics_collector.increment(
                            'market_signals_processed_total',
                            tags={'symbol': market_signal.symbol}
                        )
                    
                except Exception as e:
                    logger.error(f"Error processing market signal: {e}")
                    if metrics_collector:
                        await metrics_collector.increment('signal_processing_errors_total')
                        
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
            await asyncio.sleep(5)

async def publish_ai_signal(ai_signal: AISignal):
    """Publish AI-processed signal to Kafka"""
    try:
        signal_data = asdict(ai_signal)
        signal_json = json.dumps(signal_data, default=str)
        
        await kafka_producer.send(
            'infinityai.ai_signals',
            value=signal_json.encode('utf-8'),
            key=ai_signal.symbol.encode('utf-8')
        )
        
        logger.info(
            f"AI signal published",
            symbol=ai_signal.symbol,
            signal=ai_signal.ai_signal,
            confidence=ai_signal.confidence
        )
        
    except Exception as e:
        logger.error(f"Error publishing AI signal: {e}")

async def publish_fallback_signal(market_signal: MarketSignal):
    """Publish fallback signal when AI processing fails"""
    try:
        fallback_signal = AISignal(
            signal_id=str(uuid.uuid4()),
            symbol=market_signal.symbol,
            timestamp=time.time(),
            original_signal=market_signal.signal_type,
            ai_signal=market_signal.signal_type,  # Pass through
            confidence=max(0.3, market_signal.confidence * 0.8),  # Reduce confidence
            risk_score=0.7,  # Higher risk due to no AI processing
            risk_level=RiskLevel.HIGH.value,
            expected_return=0.002 if market_signal.signal_type == 'BUY' else -0.002,
            stop_loss=market_signal.price * 0.98,
            target_price=market_signal.price * 1.02,
            position_size=0.05,  # Small position size
            model_ensemble=['fallback'],
            features={},
            metadata={'fallback': True, 'reason': 'AI processing unavailable'}
        )
        
        await publish_ai_signal(fallback_signal)
        
    except Exception as e:
        logger.error(f"Error publishing fallback signal: {e}")

async def initialize_kafka_consumer():
    """Initialize Kafka consumer"""
    global kafka_consumer
    
    kafka_consumer = AIOKafkaConsumer(
        'infinityai.market_signals',
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id='engine-b-ai',
        auto_offset_reset='latest',
        enable_auto_commit=True,
        value_deserializer=lambda m: m.decode('utf-8') if m else None
    )
    await kafka_consumer.start()
    logger.info("Kafka consumer initialized")

async def initialize_kafka_producer():
    """Initialize Kafka producer"""
    global kafka_producer
    
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v
    )
    await kafka_producer.start()
    logger.info("Kafka producer initialized")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global redis_client, postgres_pool, metrics_collector
    global kafka_consumer, kafka_producer
    
    # Startup
    logger.info("Starting Engine B - AI Signal Processing Service")
    
    try:
        # Initialize Redis (optional)
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            try:
                await redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis ping failed: {e}")
                redis_client = None
        except Exception as e:
            logger.warning(f"Redis init skipped: {e}")
            redis_client = None
        
        # Initialize PostgreSQL (optional)
        try:
            postgres_pool = await asyncpg.create_pool(settings.DATABASE_URL)
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.warning(f"PostgreSQL init skipped: {e}")
            postgres_pool = None
        
        # Initialize metrics collector (optional)
        try:
            metrics_collector = MetricsCollector(redis_client) if redis_client else None
        except Exception as e:
            logger.warning(f"Metrics collector init skipped: {e}")
            metrics_collector = None
        
        # Initialize AI models (non-fatal on failure; service should still start)
        try:
            await initialize_ai_models()
        except Exception as e:
            logger.warning(f"AI models initialization failed: {e}")
        
        # Initialize Kafka (optional)
        try:
            await initialize_kafka_consumer()
            await initialize_kafka_producer()
            # Start background tasks
            asyncio.create_task(consume_market_signals())
        except Exception as e:
            logger.warning(f"Kafka initialization skipped: {e}")
        
        logger.info("Engine B initialized (degraded mode possible if dependencies missing)")
        
        yield
        
    except Exception as e:
        logger.error(f"Engine B startup failed: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Engine B")
        
        if kafka_consumer:
            await kafka_consumer.stop()
        if kafka_producer:
            await kafka_producer.stop()
        if redis_client:
            try:
                await redis_client.close()
            except Exception:
                pass
        if postgres_pool:
            await postgres_pool.close()
        
        logger.info("Engine B shutdown completed")

# FastAPI app
app = FastAPI(
    title="InfinityAI Engine B - AI Signal Processing",
    description="GPU-accelerated AI signal processing with ensemble models",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    gpu_available = torch.cuda.is_available()
    gpu_count = torch.cuda.device_count() if gpu_available else 0
    
    status = {
        "engine": "ENGINE_B",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "kafka": kafka_consumer is not None,
            "redis": redis_client is not None,
            "postgres": postgres_pool is not None,
            "ai_models": ai_processor is not None,
            "model_circuit_breaker": model_circuit_breaker.status if model_circuit_breaker else "unknown"
        },
        "gpu_info": {
            "available": gpu_available,
            "count": gpu_count,
            "memory_allocated": torch.cuda.memory_allocated() if gpu_available else 0,
            "memory_reserved": torch.cuda.memory_reserved() if gpu_available else 0
        }
    }
    
    return status

@app.get("/models/status")
async def get_models_status():
    """Get AI models status"""
    if not ai_processor:
        raise HTTPException(status_code=503, detail="AI processor not initialized")
    
    status = {
        "models": list(ai_processor.models.keys()),
        "model_weights": ai_processor.model_weights,
        "device": ai_processor.device,
        "circuit_breaker": model_circuit_breaker.get_stats() if model_circuit_breaker else None
    }
    
    return status

@app.get("/metrics")
async def get_metrics():
    """Get engine metrics"""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not initialized")
    
    return await metrics_collector.get_all_metrics()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info",
        access_log=True
    )
