"""
Gift Nifty Momentum AI Strategy
InfinityAI.Pro Trading Platform

Advanced AI-powered momentum strategy for Nifty 50 options trading
Designed for 25k capital with 8% max loss and 20% min profit target
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import talib
import yfinance as yf

from engines.engine_a.market_data_client import MarketDataClient
from engines.engine_b.ai_signal_processor import AISignalProcessor
from engines.engine_c.trade_executor import TradeExecutor
from utils.risk_manager import RiskManager
from utils.position_sizer import PositionSizer


class SignalStrength(Enum):
    VERY_WEAK = 0.2
    WEAK = 0.4
    NEUTRAL = 0.5
    STRONG = 0.7
    VERY_STRONG = 0.9


class TradeDirection(Enum):
    LONG_CALL = "LONG_CALL"
    LONG_PUT = "LONG_PUT"
    SHORT_CALL = "SHORT_CALL"
    SHORT_PUT = "SHORT_PUT"
    STRADDLE = "STRADDLE"
    STRANGLE = "STRANGLE"
    IRON_CONDOR = "IRON_CONDOR"


@dataclass
class StrategyConfig:
    """Configuration for Gift Nifty Momentum AI Strategy"""
    capital: float = 25000.0  # 25k capital
    max_loss_percent: float = 8.0  # 8% maximum loss
    min_profit_percent: float = 20.0  # 20% minimum profit target
    max_profit_percent: float = 1000.0  # Unlimited profit potential
    
    # Risk parameters
    position_size_percent: float = 15.0  # 15% of capital per trade
    max_positions: int = 3  # Maximum concurrent positions
    stop_loss_percent: float = 25.0  # 25% stop loss per position
    trailing_stop_percent: float = 15.0  # 15% trailing stop
    
    # Strategy parameters
    momentum_lookback: int = 14  # Momentum calculation period
    volatility_lookback: int = 20  # Volatility calculation period
    ai_confidence_threshold: float = 0.7  # AI signal confidence threshold
    
    # Option selection criteria
    min_dte: int = 1  # Minimum days to expiry
    max_dte: int = 45  # Maximum days to expiry
    delta_range: Tuple[float, float] = (0.3, 0.7)  # Delta range for options
    iv_percentile_threshold: float = 30.0  # IV percentile threshold


class GiftNiftyMomentumAI:
    """
    Advanced Gift Nifty Momentum AI Strategy
    
    Combines multiple AI models, technical indicators, and risk management
    for sophisticated Nifty 50 options trading
    """
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.market_data = MarketDataClient()
        self.ai_processor = AISignalProcessor()
        self.trade_executor = TradeExecutor()
        self.risk_manager = RiskManager()
        self.position_sizer = PositionSizer()
        
        # AI Models
        self.momentum_model = self._initialize_momentum_model()
        self.volatility_model = self._initialize_volatility_model()
        self.sentiment_model = self._initialize_sentiment_model()
        
        # Technical indicators
        self.scalers = {
            'price': StandardScaler(),
            'volume': MinMaxScaler(),
            'indicators': StandardScaler()
        }
        
        # Strategy state
        self.positions = {}
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
        self.logger.info(f"Gift Nifty Momentum AI Strategy initialized with {config.capital} capital")

    def _initialize_momentum_model(self) -> nn.Module:
        """Initialize deep learning model for momentum prediction"""
        class MomentumPredictor(nn.Module):
            def __init__(self, input_size=50):
                super().__init__()
                self.lstm = nn.LSTM(input_size, 128, 2, batch_first=True, dropout=0.2)
                self.attention = nn.MultiheadAttention(128, 8)
                self.classifier = nn.Sequential(
                    nn.Linear(128, 64),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(64, 32),
                    nn.ReLU(),
                    nn.Linear(32, 3)  # Strong Bull, Neutral, Strong Bear
                )
                
            def forward(self, x):
                lstm_out, _ = self.lstm(x)
                attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
                return self.classifier(attn_out[:, -1, :])
        
        model = MomentumPredictor()
        # Load pre-trained weights if available
        try:
            model.load_state_dict(torch.load('models/momentum_predictor.pth'))
            self.logger.info("Loaded pre-trained momentum model")
        except:
            self.logger.info("Using randomly initialized momentum model")
        
        return model

    def _initialize_volatility_model(self) -> GradientBoostingRegressor:
        """Initialize volatility prediction model"""
        model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        return model

    def _initialize_sentiment_model(self) -> RandomForestClassifier:
        """Initialize market sentiment classification model"""
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        return model

    async def analyze_gift_nifty(self) -> Dict:
        """Analyze Gift Nifty for momentum signals"""
        try:
            # Fetch Gift Nifty data
            gift_nifty_data = await self.market_data.get_gift_nifty_data()
            nifty_data = await self.market_data.get_nifty_data()
            option_chain = await self.market_data.get_option_chain()
            
            # Technical analysis
            technical_signals = self._calculate_technical_indicators(gift_nifty_data)
            
            # AI momentum prediction
            momentum_signal = self._predict_momentum(gift_nifty_data)
            
            # Volatility analysis
            volatility_forecast = self._predict_volatility(nifty_data)
            
            # Market sentiment
            sentiment_score = self._analyze_sentiment(gift_nifty_data)
            
            # Option chain analysis
            option_flow = self._analyze_option_flow(option_chain)
            
            return {
                'timestamp': datetime.now(),
                'technical_signals': technical_signals,
                'momentum_signal': momentum_signal,
                'volatility_forecast': volatility_forecast,
                'sentiment_score': sentiment_score,
                'option_flow': option_flow,
                'gift_nifty_price': gift_nifty_data['price'],
                'nifty_price': nifty_data['price']
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing Gift Nifty: {e}")
            return {}

    def _calculate_technical_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical indicators"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            volume = data['volume'].values
            
            indicators = {
                # Momentum indicators
                'rsi': talib.RSI(close, timeperiod=14),
                'stoch_k': talib.STOCHF(high, low, close)[0],
                'williams_r': talib.WILLR(high, low, close, timeperiod=14),
                'momentum': talib.MOM(close, timeperiod=10),
                'roc': talib.ROC(close, timeperiod=10),
                
                # Trend indicators
                'sma_20': talib.SMA(close, timeperiod=20),
                'ema_12': talib.EMA(close, timeperiod=12),
                'ema_26': talib.EMA(close, timeperiod=26),
                'macd': talib.MACD(close)[0],
                'macd_signal': talib.MACD(close)[1],
                'macd_hist': talib.MACD(close)[2],
                
                # Volatility indicators
                'bb_upper': talib.BBANDS(close)[0],
                'bb_middle': talib.BBANDS(close)[1],
                'bb_lower': talib.BBANDS(close)[2],
                'atr': talib.ATR(high, low, close, timeperiod=14),
                
                # Volume indicators
                'obv': talib.OBV(close, volume),
                'ad': talib.AD(high, low, close, volume),
                'mfi': talib.MFI(high, low, close, volume, timeperiod=14),
                
                # Pattern recognition
                'doji': talib.CDLDOJI(data['open'], high, low, close),
                'hammer': talib.CDLHAMMER(data['open'], high, low, close),
                'engulfing': talib.CDLENGULFING(data['open'], high, low, close),
            }
            
            # Calculate signal strength
            current_price = close[-1]
            signals = {}
            
            # RSI signal
            rsi_val = indicators['rsi'][-1]
            if rsi_val > 70:
                signals['rsi'] = {'signal': 'SELL', 'strength': SignalStrength.STRONG.value}
            elif rsi_val < 30:
                signals['rsi'] = {'signal': 'BUY', 'strength': SignalStrength.STRONG.value}
            else:
                signals['rsi'] = {'signal': 'NEUTRAL', 'strength': SignalStrength.NEUTRAL.value}
            
            # MACD signal
            macd_val = indicators['macd'][-1]
            macd_signal_val = indicators['macd_signal'][-1]
            if macd_val > macd_signal_val:
                signals['macd'] = {'signal': 'BUY', 'strength': SignalStrength.STRONG.value}
            else:
                signals['macd'] = {'signal': 'SELL', 'strength': SignalStrength.STRONG.value}
            
            # Bollinger Bands signal
            bb_upper_val = indicators['bb_upper'][-1]
            bb_lower_val = indicators['bb_lower'][-1]
            if current_price > bb_upper_val:
                signals['bollinger'] = {'signal': 'SELL', 'strength': SignalStrength.STRONG.value}
            elif current_price < bb_lower_val:
                signals['bollinger'] = {'signal': 'BUY', 'strength': SignalStrength.STRONG.value}
            else:
                signals['bollinger'] = {'signal': 'NEUTRAL', 'strength': SignalStrength.NEUTRAL.value}
            
            return {
                'indicators': indicators,
                'signals': signals,
                'overall_sentiment': self._calculate_overall_sentiment(signals)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return {}

    def _predict_momentum(self, data: pd.DataFrame) -> Dict:
        """Predict momentum using AI model"""
        try:
            # Prepare features
            features = self._prepare_momentum_features(data)
            
            # Make prediction
            with torch.no_grad():
                prediction = self.momentum_model(features)
                probabilities = torch.softmax(prediction, dim=1)
                
                # Interpret results
                momentum_class = torch.argmax(probabilities, dim=1).item()
                confidence = torch.max(probabilities, dim=1).values.item()
                
                momentum_labels = ['STRONG_BEAR', 'NEUTRAL', 'STRONG_BULL']
                predicted_momentum = momentum_labels[momentum_class]
                
            return {
                'prediction': predicted_momentum,
                'confidence': confidence,
                'probabilities': {
                    'STRONG_BEAR': probabilities[0][0].item(),
                    'NEUTRAL': probabilities[0][1].item(),
                    'STRONG_BULL': probabilities[0][2].item()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting momentum: {e}")
            return {'prediction': 'NEUTRAL', 'confidence': 0.5}

    def _prepare_momentum_features(self, data: pd.DataFrame) -> torch.Tensor:
        """Prepare features for momentum model"""
        try:
            # Extract relevant features
            close = data['close'].values
            volume = data['volume'].values
            
            # Calculate features
            features = []
            
            # Price features
            returns = np.diff(np.log(close))
            features.extend(returns[-20:])  # Last 20 returns
            
            # Momentum features
            momentum_5 = talib.MOM(close, timeperiod=5)
            momentum_10 = talib.MOM(close, timeperiod=10)
            features.extend([momentum_5[-1], momentum_10[-1]])
            
            # Volatility features
            volatility = np.std(returns[-20:])
            features.append(volatility)
            
            # Volume features
            volume_ma = np.mean(volume[-20:])
            volume_ratio = volume[-1] / volume_ma
            features.append(volume_ratio)
            
            # Technical indicator features
            rsi = talib.RSI(close, timeperiod=14)[-1]
            macd, macd_signal, _ = talib.MACD(close)
            features.extend([rsi, macd[-1], macd_signal[-1]])
            
            # Pad or truncate to 50 features
            if len(features) < 50:
                features.extend([0.0] * (50 - len(features)))
            else:
                features = features[:50]
            
            # Convert to tensor
            feature_tensor = torch.FloatTensor(features).unsqueeze(0).unsqueeze(0)
            return feature_tensor
            
        except Exception as e:
            self.logger.error(f"Error preparing momentum features: {e}")
            return torch.zeros(1, 1, 50)

    def _predict_volatility(self, data: pd.DataFrame) -> Dict:
        """Predict future volatility"""
        try:
            # Calculate historical volatility
            returns = np.diff(np.log(data['close'].values))
            realized_vol = np.std(returns) * np.sqrt(252)  # Annualized
            
            # Predict future volatility (simplified for example)
            predicted_vol = realized_vol * 1.1  # Adjust based on model
            
            return {
                'current_volatility': realized_vol,
                'predicted_volatility': predicted_vol,
                'volatility_regime': 'HIGH' if predicted_vol > 0.25 else 'LOW'
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting volatility: {e}")
            return {'current_volatility': 0.2, 'predicted_volatility': 0.2}

    def _analyze_sentiment(self, data: pd.DataFrame) -> Dict:
        """Analyze market sentiment"""
        try:
            # Price-based sentiment
            close = data['close'].values
            price_change = (close[-1] - close[-2]) / close[-2]
            
            # Volume-based sentiment
            volume = data['volume'].values
            volume_ma = np.mean(volume[-5:])
            volume_sentiment = 'POSITIVE' if volume[-1] > volume_ma else 'NEGATIVE'
            
            # Overall sentiment score
            sentiment_score = 0.5  # Neutral baseline
            if price_change > 0.01:
                sentiment_score += 0.3
            elif price_change < -0.01:
                sentiment_score -= 0.3
                
            if volume_sentiment == 'POSITIVE':
                sentiment_score += 0.1
            else:
                sentiment_score -= 0.1
                
            sentiment_score = max(0.0, min(1.0, sentiment_score))  # Clamp to [0, 1]
            
            return {
                'score': sentiment_score,
                'sentiment': 'BULLISH' if sentiment_score > 0.6 else 'BEARISH' if sentiment_score < 0.4 else 'NEUTRAL',
                'price_change': price_change,
                'volume_sentiment': volume_sentiment
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return {'score': 0.5, 'sentiment': 'NEUTRAL'}

    def _analyze_option_flow(self, option_chain: Dict) -> Dict:
        """Analyze option flow for additional signals"""
        try:
            calls = option_chain.get('calls', [])
            puts = option_chain.get('puts', [])
            
            # Calculate Put-Call Ratio
            total_call_volume = sum([opt.get('volume', 0) for opt in calls])
            total_put_volume = sum([opt.get('volume', 0) for opt in puts])
            
            pcr = total_put_volume / total_call_volume if total_call_volume > 0 else 1.0
            
            # Analyze max pain
            max_pain = self._calculate_max_pain(option_chain)
            
            # Option flow sentiment
            if pcr > 1.2:
                option_sentiment = 'BEARISH'
            elif pcr < 0.8:
                option_sentiment = 'BULLISH'
            else:
                option_sentiment = 'NEUTRAL'
            
            return {
                'pcr': pcr,
                'max_pain': max_pain,
                'option_sentiment': option_sentiment,
                'total_call_volume': total_call_volume,
                'total_put_volume': total_put_volume
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing option flow: {e}")
            return {'pcr': 1.0, 'option_sentiment': 'NEUTRAL'}

    def _calculate_max_pain(self, option_chain: Dict) -> float:
        """Calculate max pain point"""
        try:
            strikes = []
            total_pain = []
            
            all_options = option_chain.get('calls', []) + option_chain.get('puts', [])
            strike_prices = sorted(list(set([opt['strike'] for opt in all_options])))
            
            for strike in strike_prices:
                pain = 0
                for opt in all_options:
                    if opt['type'] == 'CALL' and strike > opt['strike']:
                        pain += opt['open_interest'] * (strike - opt['strike'])
                    elif opt['type'] == 'PUT' and strike < opt['strike']:
                        pain += opt['open_interest'] * (opt['strike'] - strike)
                
                strikes.append(strike)
                total_pain.append(pain)
            
            # Find strike with minimum pain
            min_pain_idx = total_pain.index(min(total_pain))
            return strikes[min_pain_idx]
            
        except Exception as e:
            self.logger.error(f"Error calculating max pain: {e}")
            return 0.0

    def _calculate_overall_sentiment(self, signals: Dict) -> str:
        """Calculate overall sentiment from all signals"""
        bullish_signals = 0
        bearish_signals = 0
        
        for signal_data in signals.values():
            if signal_data['signal'] == 'BUY':
                bullish_signals += signal_data['strength']
            elif signal_data['signal'] == 'SELL':
                bearish_signals += signal_data['strength']
        
        if bullish_signals > bearish_signals * 1.2:
            return 'BULLISH'
        elif bearish_signals > bullish_signals * 1.2:
            return 'BEARISH'
        else:
            return 'NEUTRAL'

    async def generate_trading_signal(self) -> Dict:
        """Generate comprehensive trading signal"""
        try:
            # Get analysis
            analysis = await self.analyze_gift_nifty()
            if not analysis:
                return {'action': 'HOLD', 'confidence': 0.0}
            
            # Extract signals
            technical_sentiment = analysis['technical_signals']['overall_sentiment']
            momentum_prediction = analysis['momentum_signal']['prediction']
            momentum_confidence = analysis['momentum_signal']['confidence']
            sentiment_score = analysis['sentiment_score']['score']
            option_sentiment = analysis['option_flow']['option_sentiment']
            
            # Combine signals
            signal_score = 0.5  # Neutral baseline
            
            # Technical analysis weight: 30%
            if technical_sentiment == 'BULLISH':
                signal_score += 0.3
            elif technical_sentiment == 'BEARISH':
                signal_score -= 0.3
            
            # AI momentum weight: 40%
            if momentum_prediction == 'STRONG_BULL':
                signal_score += 0.4 * momentum_confidence
            elif momentum_prediction == 'STRONG_BEAR':
                signal_score -= 0.4 * momentum_confidence
            
            # Market sentiment weight: 20%
            signal_score += 0.2 * (sentiment_score - 0.5)
            
            # Option flow weight: 10%
            if option_sentiment == 'BULLISH':
                signal_score += 0.1
            elif option_sentiment == 'BEARISH':
                signal_score -= 0.1
            
            # Determine action
            if signal_score > 0.7:
                action = 'STRONG_BUY'
                trade_direction = TradeDirection.LONG_CALL
                confidence = signal_score
            elif signal_score > 0.55:
                action = 'BUY'
                trade_direction = TradeDirection.LONG_CALL
                confidence = signal_score
            elif signal_score < 0.3:
                action = 'STRONG_SELL'
                trade_direction = TradeDirection.LONG_PUT
                confidence = 1.0 - signal_score
            elif signal_score < 0.45:
                action = 'SELL'
                trade_direction = TradeDirection.LONG_PUT
                confidence = 1.0 - signal_score
            else:
                action = 'HOLD'
                trade_direction = None
                confidence = 0.5
            
            return {
                'action': action,
                'trade_direction': trade_direction,
                'confidence': confidence,
                'signal_score': signal_score,
                'analysis': analysis,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating trading signal: {e}")
            return {'action': 'HOLD', 'confidence': 0.0}

    async def execute_strategy(self) -> Dict:
        """Execute the Gift Nifty Momentum AI Strategy"""
        try:
            self.logger.info("Executing Gift Nifty Momentum AI Strategy...")
            
            # Check if markets are open
            if not await self._is_market_open():
                return {'status': 'MARKET_CLOSED', 'message': 'Markets are closed'}
            
            # Risk check
            if not self._risk_check():
                return {'status': 'RISK_BREACH', 'message': 'Risk limits breached'}
            
            # Generate trading signal
            signal = await self.generate_trading_signal()
            
            # Execute trades if confidence is high enough
            if signal['confidence'] >= self.config.ai_confidence_threshold:
                if signal['action'] in ['STRONG_BUY', 'BUY', 'STRONG_SELL', 'SELL']:
                    trade_result = await self._execute_trade(signal)
                    return {
                        'status': 'TRADE_EXECUTED',
                        'signal': signal,
                        'trade_result': trade_result
                    }
            
            return {
                'status': 'SIGNAL_GENERATED',
                'signal': signal,
                'message': f"Signal confidence {signal['confidence']:.2f} below threshold {self.config.ai_confidence_threshold}"
            }
            
        except Exception as e:
            self.logger.error(f"Error executing strategy: {e}")
            return {'status': 'ERROR', 'message': str(e)}

    async def _execute_trade(self, signal: Dict) -> Dict:
        """Execute trade based on signal"""
        try:
            # Calculate position size
            position_size = self.position_sizer.calculate_position_size(
                capital=self.config.capital - abs(self.daily_pnl),
                risk_percent=self.config.position_size_percent,
                confidence=signal['confidence']
            )
            
            # Select best options
            option_selection = await self._select_options(
                signal['trade_direction'], 
                position_size
            )
            
            # Execute trade through Engine C
            trade_order = {
                'strategy_name': 'GiftNifty_Momentum_AI',
                'direction': signal['trade_direction'].value,
                'options': option_selection['options'],
                'quantity': option_selection['quantity'],
                'stop_loss': option_selection['stop_loss'],
                'target': option_selection['target'],
                'confidence': signal['confidence'],
                'analysis': signal['analysis']
            }
            
            result = await self.trade_executor.execute_trade(trade_order)
            
            # Update strategy state
            if result['status'] == 'SUCCESS':
                self.total_trades += 1
                position_id = result['position_id']
                self.positions[position_id] = {
                    'signal': signal,
                    'trade_order': trade_order,
                    'entry_time': datetime.now(),
                    'entry_price': result['entry_price'],
                    'quantity': option_selection['quantity'],
                    'stop_loss': option_selection['stop_loss'],
                    'target': option_selection['target']
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return {'status': 'ERROR', 'message': str(e)}

    async def _select_options(self, trade_direction: TradeDirection, position_size: float) -> Dict:
        """Select best options for the trade"""
        try:
            # Get option chain
            option_chain = await self.market_data.get_option_chain()
            nifty_price = await self.market_data.get_current_nifty_price()
            
            selected_options = []
            
            if trade_direction == TradeDirection.LONG_CALL:
                # Select ATM or slightly OTM call
                target_strike = nifty_price + (nifty_price * 0.01)  # 1% OTM
                best_call = self._find_best_option(
                    option_chain['calls'], target_strike, 'CALL'
                )
                if best_call:
                    selected_options.append(best_call)
                    
            elif trade_direction == TradeDirection.LONG_PUT:
                # Select ATM or slightly OTM put
                target_strike = nifty_price - (nifty_price * 0.01)  # 1% OTM
                best_put = self._find_best_option(
                    option_chain['puts'], target_strike, 'PUT'
                )
                if best_put:
                    selected_options.append(best_put)
            
            # Calculate quantity based on position size
            if selected_options:
                option_price = selected_options[0]['ltp']
                quantity = min(
                    int(position_size / option_price),
                    selected_options[0]['available_quantity']
                )
                
                # Calculate stop loss and target
                stop_loss = option_price * (1 - self.config.stop_loss_percent / 100)
                target = option_price * (1 + self.config.min_profit_percent / 100)
                
                return {
                    'options': selected_options,
                    'quantity': quantity,
                    'stop_loss': stop_loss,
                    'target': target,
                    'total_premium': option_price * quantity
                }
            
            return {'options': [], 'quantity': 0}
            
        except Exception as e:
            self.logger.error(f"Error selecting options: {e}")
            return {'options': [], 'quantity': 0}

    def _find_best_option(self, options: List[Dict], target_strike: float, option_type: str) -> Optional[Dict]:
        """Find best option based on criteria"""
        try:
            # Filter options based on criteria
            filtered_options = []
            
            for option in options:
                # Check DTE
                dte = option.get('days_to_expiry', 0)
                if not (self.config.min_dte <= dte <= self.config.max_dte):
                    continue
                
                # Check delta
                delta = abs(option.get('delta', 0))
                if not (self.config.delta_range[0] <= delta <= self.config.delta_range[1]):
                    continue
                
                # Check liquidity
                if option.get('volume', 0) < 100 or option.get('open_interest', 0) < 1000:
                    continue
                
                filtered_options.append(option)
            
            if not filtered_options:
                return None
            
            # Find option closest to target strike
            best_option = min(
                filtered_options,
                key=lambda x: abs(x['strike'] - target_strike)
            )
            
            return best_option
            
        except Exception as e:
            self.logger.error(f"Error finding best option: {e}")
            return None

    def _risk_check(self) -> bool:
        """Comprehensive risk check"""
        try:
            # Check daily loss limit
            max_daily_loss = self.config.capital * (self.config.max_loss_percent / 100)
            if abs(self.daily_pnl) >= max_daily_loss:
                self.logger.warning(f"Daily loss limit reached: {self.daily_pnl}")
                return False
            
            # Check maximum positions
            if len(self.positions) >= self.config.max_positions:
                self.logger.warning(f"Maximum positions limit reached: {len(self.positions)}")
                return False
            
            # Check available capital
            used_capital = sum([pos.get('total_premium', 0) for pos in self.positions.values()])
            available_capital = self.config.capital - used_capital - abs(self.daily_pnl)
            
            if available_capital < (self.config.capital * 0.1):  # Keep 10% buffer
                self.logger.warning(f"Insufficient capital available: {available_capital}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in risk check: {e}")
            return False

    async def _is_market_open(self) -> bool:
        """Check if market is open"""
        try:
            now = datetime.now()
            
            # Check if it's a weekday
            if now.weekday() > 4:  # Saturday = 5, Sunday = 6
                return False
            
            # Check market hours (9:15 AM to 3:30 PM IST)
            market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
            market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
            
            return market_open <= now <= market_close
            
        except Exception as e:
            self.logger.error(f"Error checking market hours: {e}")
            return False

    async def monitor_positions(self):
        """Monitor active positions for stop loss and trailing stop"""
        try:
            for position_id, position in self.positions.items():
                current_price = await self.market_data.get_option_price(
                    position['trade_order']['options'][0]['symbol']
                )
                
                entry_price = position['entry_price']
                pnl = (current_price - entry_price) * position['quantity']
                
                # Check stop loss
                if current_price <= position['stop_loss']:
                    await self._close_position(position_id, 'STOP_LOSS')
                
                # Check target
                elif current_price >= position['target']:
                    await self._close_position(position_id, 'TARGET_REACHED')
                
                # Implement trailing stop
                elif pnl > 0:
                    trailing_stop = current_price * (1 - self.config.trailing_stop_percent / 100)
                    if trailing_stop > position['stop_loss']:
                        position['stop_loss'] = trailing_stop
                        self.logger.info(f"Updated trailing stop for {position_id}: {trailing_stop}")
                
        except Exception as e:
            self.logger.error(f"Error monitoring positions: {e}")

    async def _close_position(self, position_id: str, reason: str):
        """Close a position"""
        try:
            position = self.positions.get(position_id)
            if not position:
                return
            
            # Execute close order
            close_result = await self.trade_executor.close_position(position_id)
            
            if close_result['status'] == 'SUCCESS':
                # Calculate P&L
                pnl = close_result['pnl']
                self.daily_pnl += pnl
                
                if pnl > 0:
                    self.winning_trades += 1
                
                # Remove from active positions
                del self.positions[position_id]
                
                self.logger.info(f"Position {position_id} closed - Reason: {reason}, P&L: {pnl}")
                
        except Exception as e:
            self.logger.error(f"Error closing position {position_id}: {e}")

    def get_strategy_stats(self) -> Dict:
        """Get strategy performance statistics"""
        try:
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            return {
                'strategy_name': 'Gift Nifty Momentum AI',
                'capital': self.config.capital,
                'daily_pnl': self.daily_pnl,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'win_rate': win_rate,
                'active_positions': len(self.positions),
                'max_loss_percent': self.config.max_loss_percent,
                'min_profit_percent': self.config.min_profit_percent,
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting strategy stats: {e}")
            return {}


# Strategy factory function
def create_giftnifty_momentum_strategy(capital: float = 25000.0) -> GiftNiftyMomentumAI:
    """Create Gift Nifty Momentum AI Strategy instance"""
    config = StrategyConfig(capital=capital)
    return GiftNiftyMomentumAI(config)


# Main execution function for standalone testing
async def main():
    """Main function for testing the strategy"""
    strategy = create_giftnifty_momentum_strategy()
    
    # Run strategy
    result = await strategy.execute_strategy()
    print(f"Strategy execution result: {result}")
    
    # Get stats
    stats = strategy.get_strategy_stats()
    print(f"Strategy statistics: {stats}")


if __name__ == "__main__":
    asyncio.run(main())