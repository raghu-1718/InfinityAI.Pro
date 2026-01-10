#!/usr/bin/env python3
"""
Momentum-based Trading Strategies for Trending Markets
Optimized for BANKNIFTY, FINNIFTY, SENSEX (strong uptrend indices)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Signal:
    """Trading signal with metadata"""
    timestamp: datetime
    symbol: str
    strategy: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    price: float
    indicator_values: Dict[str, float]
    confidence: float  # 0-1 confidence score


class RSIStrategy:
    """Relative Strength Index Strategy - Momentum Oscillator"""

    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        """
        Args:
            period: RSI calculation period (default 14)
            oversold: RSI level for oversold condition (default 30)
            overbought: RSI level for overbought condition (default 70)
        """
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.name = f"RSI({period})"

    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """Generate trading signals based on RSI"""
        df = df.copy()
        df['rsi'] = self.calculate_rsi(df['close'])

        signals = []
        position = None  # Track current position

        for i in range(self.period + 1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]

            # RSI crossed above oversold (from below) - BUY signal
            if prev_row['rsi'] < self.oversold and row['rsi'] >= self.oversold and position != 'LONG':
                signals.append(Signal(
                    timestamp=row['timestamp'],
                    symbol=row.get('symbol', 'UNKNOWN'),
                    strategy=self.name,
                    signal_type='BUY',
                    price=row['close'],
                    indicator_values={'rsi': row['rsi']},
                    confidence=min(1.0, (self.oversold - prev_row['rsi']) / 10)
                ))
                position = 'LONG'

            # RSI crossed below overbought (from above) - SELL signal
            elif prev_row['rsi'] > self.overbought and row['rsi'] <= self.overbought and position == 'LONG':
                signals.append(Signal(
                    timestamp=row['timestamp'],
                    symbol=row.get('symbol', 'UNKNOWN'),
                    strategy=self.name,
                    signal_type='SELL',
                    price=row['close'],
                    indicator_values={'rsi': row['rsi']},
                    confidence=min(1.0, (prev_row['rsi'] - self.overbought) / 10)
                ))
                position = None

        return signals

    def backtest(self, df: pd.DataFrame, initial_capital: float = 1000000) -> Dict:
        """Backtest RSI strategy"""
        signals = self.generate_signals(df)

        cash = initial_capital
        position = 0
        entry_price = 0
        trades = []

        for signal in signals:
            if signal.signal_type == 'BUY' and position == 0:
                position = int((cash * 0.95) / signal.price)  # Use 95% of capital
                entry_price = signal.price
                cash -= position * signal.price

            elif signal.signal_type == 'SELL' and position > 0:
                pnl = (signal.price - entry_price) * position
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': signal.price,
                    'quantity': position,
                    'pnl': pnl,
                    'return_pct': ((signal.price - entry_price) / entry_price) * 100
                })
                cash += position * signal.price
                position = 0

        # Calculate final equity (including open position if any)
        final_price = df['close'].iloc[-1] if len(df) > 0 else 0
        final_equity = cash + (position * final_price if position > 0 else 0)

        # Calculate metrics
        total_pnl = sum(t['pnl'] for t in trades)
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] < 0]

        # Calculate Sharpe ratio (simplified)
        if trades:
            returns = [t['return_pct'] for t in trades]
            sharpe = (np.mean(returns) / np.std(returns)) if len(returns) > 1 and np.std(returns) > 0 else 0
        else:
            sharpe = 0

        return {
            'strategy': self.name,
            'trades': len(trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins) / len(trades) * 100) if trades else 0,
            'total_pnl': total_pnl,
            'final_equity': final_equity,
            'return_pct': ((final_equity - initial_capital) / initial_capital) * 100,
            'sharpe_ratio': sharpe,
            'avg_win': np.mean([t['pnl'] for t in wins]) if wins else 0,
            'avg_loss': np.mean([t['pnl'] for t in losses]) if losses else 0,
            'max_drawdown': self._calculate_max_drawdown(trades, initial_capital)
        }

    def _calculate_max_drawdown(self, trades: List[Dict], initial_capital: float) -> float:
        """Calculate maximum drawdown percentage"""
        equity_curve = [initial_capital]
        for trade in trades:
            equity_curve.append(equity_curve[-1] + trade['pnl'])

        if len(equity_curve) < 2:
            return 0

        peak = equity_curve[0]
        max_dd = 0

        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = ((peak - equity) / peak) * 100
            if dd > max_dd:
                max_dd = dd

        return max_dd


class MACDStrategy:
    """MACD (Moving Average Convergence Divergence) Strategy"""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """
        Args:
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line EMA period (default 9)
        """
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
        self.name = f"MACD({fast},{slow},{signal})"

    def calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD, Signal, and Histogram"""
        ema_fast = prices.ewm(span=self.fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """Generate trading signals based on MACD crossovers"""
        df = df.copy()
        df['macd'], df['signal'], df['histogram'] = self.calculate_macd(df['close'])

        signals = []
        position = None

        for i in range(self.slow + self.signal_period, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]

            # MACD crosses above signal line - BUY
            if prev_row['macd'] < prev_row['signal'] and row['macd'] >= row['signal'] and position != 'LONG':
                signals.append(Signal(
                    timestamp=row['timestamp'],
                    symbol=row.get('symbol', 'UNKNOWN'),
                    strategy=self.name,
                    signal_type='BUY',
                    price=row['close'],
                    indicator_values={
                        'macd': row['macd'],
                        'signal': row['signal'],
                        'histogram': row['histogram']
                    },
                    confidence=min(1.0, abs(row['histogram']) / row['close'] * 100)
                ))
                position = 'LONG'

            # MACD crosses below signal line - SELL
            elif prev_row['macd'] > prev_row['signal'] and row['macd'] <= row['signal'] and position == 'LONG':
                signals.append(Signal(
                    timestamp=row['timestamp'],
                    symbol=row.get('symbol', 'UNKNOWN'),
                    strategy=self.name,
                    signal_type='SELL',
                    price=row['close'],
                    indicator_values={
                        'macd': row['macd'],
                        'signal': row['signal'],
                        'histogram': row['histogram']
                    },
                    confidence=min(1.0, abs(row['histogram']) / row['close'] * 100)
                ))
                position = None

        return signals

    def backtest(self, df: pd.DataFrame, initial_capital: float = 1000000) -> Dict:
        """Backtest MACD strategy using same logic as RSI"""
        signals = self.generate_signals(df)

        cash = initial_capital
        position = 0
        entry_price = 0
        trades = []

        for signal in signals:
            if signal.signal_type == 'BUY' and position == 0:
                position = int((cash * 0.95) / signal.price)
                entry_price = signal.price
                cash -= position * signal.price

            elif signal.signal_type == 'SELL' and position > 0:
                pnl = (signal.price - entry_price) * position
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': signal.price,
                    'quantity': position,
                    'pnl': pnl,
                    'return_pct': ((signal.price - entry_price) / entry_price) * 100
                })
                cash += position * signal.price
                position = 0

        final_price = df['close'].iloc[-1] if len(df) > 0 else 0
        final_equity = cash + (position * final_price if position > 0 else 0)
        total_pnl = sum(t['pnl'] for t in trades)
        wins = [t for t in trades if t['pnl'] > 0]

        if trades:
            returns = [t['return_pct'] for t in trades]
            sharpe = (np.mean(returns) / np.std(returns)) if len(returns) > 1 and np.std(returns) > 0 else 0
        else:
            sharpe = 0

        return {
            'strategy': self.name,
            'trades': len(trades),
            'wins': len(wins),
            'losses': len(trades) - len(wins),
            'win_rate': (len(wins) / len(trades) * 100) if trades else 0,
            'total_pnl': total_pnl,
            'final_equity': final_equity,
            'return_pct': ((final_equity - initial_capital) / initial_capital) * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown': RSIStrategy()._calculate_max_drawdown(trades, initial_capital)
        }


class BollingerBandsStrategy:
    """Bollinger Bands Mean Reversion Strategy"""

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        """
        Args:
            period: SMA period for middle band (default 20)
            std_dev: Number of standard deviations for bands (default 2.0)
        """
        self.period = period
        self.std_dev = std_dev
        self.name = f"BB({period},{std_dev})"

    def calculate_bands(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        middle_band = prices.rolling(window=self.period).mean()
        std = prices.rolling(window=self.period).std()

        upper_band = middle_band + (std * self.std_dev)
        lower_band = middle_band - (std * self.std_dev)

        return upper_band, middle_band, lower_band

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """Generate signals based on Bollinger Band touches"""
        df = df.copy()
        df['upper_band'], df['middle_band'], df['lower_band'] = self.calculate_bands(df['close'])
        df['bb_width'] = ((df['upper_band'] - df['lower_band']) / df['middle_band']) * 100

        signals = []
        position = None

        for i in range(self.period + 1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]

            # Price touches or crosses below lower band - BUY (oversold)
            if row['close'] <= row['lower_band'] and prev_row['close'] > prev_row['lower_band'] and position != 'LONG':
                signals.append(Signal(
                    timestamp=row['timestamp'],
                    symbol=row.get('symbol', 'UNKNOWN'),
                    strategy=self.name,
                    signal_type='BUY',
                    price=row['close'],
                    indicator_values={
                        'upper_band': row['upper_band'],
                        'middle_band': row['middle_band'],
                        'lower_band': row['lower_band'],
                        'bb_width': row['bb_width']
                    },
                    confidence=min(1.0, (row['lower_band'] - row['close']) / row['close'] * 100)
                ))
                position = 'LONG'

            # Price touches or crosses above upper band - SELL (overbought)
            elif row['close'] >= row['upper_band'] and position == 'LONG':
                signals.append(Signal(
                    timestamp=row['timestamp'],
                    symbol=row.get('symbol', 'UNKNOWN'),
                    strategy=self.name,
                    signal_type='SELL',
                    price=row['close'],
                    indicator_values={
                        'upper_band': row['upper_band'],
                        'middle_band': row['middle_band'],
                        'lower_band': row['lower_band'],
                        'bb_width': row['bb_width']
                    },
                    confidence=min(1.0, (row['close'] - row['upper_band']) / row['close'] * 100)
                ))
                position = None

        return signals

    def backtest(self, df: pd.DataFrame, initial_capital: float = 1000000) -> Dict:
        """Backtest Bollinger Bands strategy"""
        signals = self.generate_signals(df)

        cash = initial_capital
        position = 0
        entry_price = 0
        trades = []

        for signal in signals:
            if signal.signal_type == 'BUY' and position == 0:
                position = int((cash * 0.95) / signal.price)
                entry_price = signal.price
                cash -= position * signal.price

            elif signal.signal_type == 'SELL' and position > 0:
                pnl = (signal.price - entry_price) * position
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': signal.price,
                    'quantity': position,
                    'pnl': pnl,
                    'return_pct': ((signal.price - entry_price) / entry_price) * 100
                })
                cash += position * signal.price
                position = 0

        final_price = df['close'].iloc[-1] if len(df) > 0 else 0
        final_equity = cash + (position * final_price if position > 0 else 0)
        total_pnl = sum(t['pnl'] for t in trades)
        wins = [t for t in trades if t['pnl'] > 0]

        if trades:
            returns = [t['return_pct'] for t in trades]
            sharpe = (np.mean(returns) / np.std(returns)) if len(returns) > 1 and np.std(returns) > 0 else 0
        else:
            sharpe = 0

        return {
            'strategy': self.name,
            'trades': len(trades),
            'wins': len(wins),
            'losses': len(trades) - len(wins),
            'win_rate': (len(wins) / len(trades) * 100) if trades else 0,
            'total_pnl': total_pnl,
            'final_equity': final_equity,
            'return_pct': ((final_equity - initial_capital) / initial_capital) * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown': RSIStrategy()._calculate_max_drawdown(trades, initial_capital)
        }


class MultiStrategyEngine:
    """
    Execute multiple strategies and combine results
    Optimized for trending indices: BANKNIFTY, FINNIFTY, SENSEX
    """

    def __init__(self):
        self.strategies = {
            'RSI_14': RSIStrategy(period=14, oversold=30, overbought=70),
            'RSI_21': RSIStrategy(period=21, oversold=35, overbought=65),
            'MACD': MACDStrategy(fast=12, slow=26, signal=9),
            'MACD_Fast': MACDStrategy(fast=8, slow=17, signal=9),
            'BB_20': BollingerBandsStrategy(period=20, std_dev=2.0),
            'BB_50': BollingerBandsStrategy(period=50, std_dev=2.5)
        }

    def run_all_strategies(self, df: pd.DataFrame, symbol: str) -> Dict:
        """Run all strategies and return combined results"""
        df = df.copy()
        df['symbol'] = symbol

        results = {}
        all_signals = []

        for strategy_name, strategy in self.strategies.items():
            try:
                backtest_result = strategy.backtest(df)
                signals = strategy.generate_signals(df)

                results[strategy_name] = backtest_result
                all_signals.extend(signals)
            except Exception as e:
                results[strategy_name] = {'error': str(e)}

        # Find best performing strategy
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        if valid_results:
            best_strategy = max(valid_results.items(), key=lambda x: x[1].get('return_pct', -999))
            results['best_strategy'] = {
                'name': best_strategy[0],
                'return_pct': best_strategy[1]['return_pct'],
                'sharpe_ratio': best_strategy[1]['sharpe_ratio'],
                'win_rate': best_strategy[1]['win_rate']
            }

        # Get latest signals (most recent from each strategy)
        latest_signals = {}
        for signal in sorted(all_signals, key=lambda x: x.timestamp, reverse=True):
            if signal.strategy not in latest_signals:
                latest_signals[signal.strategy] = {
                    'timestamp': signal.timestamp.isoformat(),
                    'signal_type': signal.signal_type,
                    'price': signal.price,
                    'confidence': signal.confidence,
                    'indicators': signal.indicator_values
                }

        results['latest_signals'] = latest_signals

        return results

    def get_recommended_strategy(self, symbol: str) -> str:
        """Get recommended strategy based on symbol characteristics"""
        # For trending indices, prefer MACD and RSI
        trending_indices = ['BANKNIFTY', 'FINNIFTY', 'SENSEX']
        if symbol.upper() in trending_indices:
            return 'MACD'  # Best for trending markets
        else:
            return 'RSI_14'  # Default for other symbols
