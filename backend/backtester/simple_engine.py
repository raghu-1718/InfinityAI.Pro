#!/usr/bin/env python3
"""
Simplified Backtester for InfinityAI.Pro
Standalone implementation without external dependencies
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample OHLCV data generator for testing
def generate_sample_data(symbol: str, days: int = 252) -> pd.DataFrame:
    """Generate realistic sample OHLCV data"""
    np.random.seed(hash(symbol) % (2**32))

    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    # Base prices by symbol
    base_prices = {
        'NIFTY': 25683,
        'BANKNIFTY': 59252,
        'FINNIFTY': 38027,
        'SENSEX': 83576,
        'GOLD': 4490,
        'CRUDEOIL': 59
    }

    base_price = base_prices.get(symbol, 100)

    # Generate realistic price movements
    returns = np.random.normal(0.0005, 0.015, days)
    closes = base_price * np.exp(np.cumsum(returns))

    # Generate OHLC from closes
    data = {
        'timestamp': dates,
        'open': closes * (1 + np.random.normal(0, 0.005, days)),
        'high': closes * (1 + np.abs(np.random.normal(0, 0.01, days))),
        'low': closes * (1 - np.abs(np.random.normal(0, 0.01, days))),
        'close': closes,
        'volume': np.random.uniform(1000000, 50000000, days)
    }

    df = pd.DataFrame(data)
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)

    return df


class SimpleBacktester:
    """Simple MA Crossover + Risk Management Backtester"""

    def __init__(self, initial_capital: float = 1000000, commission: float = 0.0005):
        self.initial_capital = initial_capital
        self.commission = commission
        self.cash = initial_capital
        self.position = 0  # shares held
        self.entry_price = 0
        self.entry_date = None
        self.trades = []
        self.equity_curve = [initial_capital]
        self.dates = []

    def calculate_signals(self, df: pd.DataFrame, ma_short: int = 20, ma_long: int = 50) -> pd.DataFrame:
        """Calculate MA Crossover signals"""
        df['ma_short'] = df['close'].rolling(ma_short).mean()
        df['ma_long'] = df['close'].rolling(ma_long).mean()
        df['signal'] = 0

        df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1  # Buy
        df.loc[df['ma_short'] < df['ma_long'], 'signal'] = -1  # Sell

        return df

    def backtest(self, df: pd.DataFrame) -> Dict:
        """Run backtest on OHLCV data"""
        df = self.calculate_signals(df)

        results = {
            'trades': [],
            'wins': 0,
            'losses': 0,
            'total_pnl': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0
        }

        for i in range(100, len(df)):  # Start after MA period
            current_price = df['close'].iloc[i]
            signal = df['signal'].iloc[i]
            date = df['timestamp'].iloc[i]

            # Exit signal
            if self.position > 0 and signal == -1:
                pnl = (current_price - self.entry_price) * self.position
                pnl_after_commission = pnl - (self.entry_price * self.position * self.commission * 2)

                self.cash += current_price * self.position + pnl_after_commission

                results['trades'].append({
                    'entry_date': self.entry_date.isoformat() if self.entry_date else None,
                    'exit_date': date.isoformat(),
                    'entry_price': float(self.entry_price),
                    'exit_price': float(current_price),
                    'shares': int(self.position),
                    'pnl': float(pnl_after_commission),
                    'return_pct': float((pnl_after_commission / (self.entry_price * self.position)) * 100) if self.entry_price > 0 else 0
                })

                if pnl_after_commission > 0:
                    results['wins'] += 1
                else:
                    results['losses'] += 1

                results['total_pnl'] += pnl_after_commission
                self.position = 0
                self.entry_price = 0

            # Entry signal
            elif self.position == 0 and signal == 1:
                risk_amount = self.cash * 0.02  # 2% risk per trade
                self.position = int(risk_amount / current_price)
                self.entry_price = current_price
                self.entry_date = date
                self.cash -= current_price * self.position

            # Calculate equity
            current_equity = self.cash
            if self.position > 0:
                current_equity += self.position * current_price

            self.equity_curve.append(current_equity)
            self.dates.append(date)

        # Calculate metrics
        equity_array = np.array(self.equity_curve)
        returns = np.diff(equity_array) / equity_array[:-1]

        results['final_capital'] = float(self.cash + self.position * df['close'].iloc[-1])
        results['total_return_pct'] = float(((results['final_capital'] - self.initial_capital) / self.initial_capital) * 100)

        if len(returns) > 0:
            results['sharpe_ratio'] = float(np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0

        # Max drawdown
        cummax = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - cummax) / cummax
        results['max_drawdown'] = float(np.min(drawdown) * 100)

        results['win_rate'] = float((results['wins'] / (results['wins'] + results['losses']) * 100)) if (results['wins'] + results['losses']) > 0 else 0

        return results


def main():
    parser = argparse.ArgumentParser(description='Run backtests on symbols')
    parser.add_argument('--symbols', nargs='+', default=['NIFTY', 'BANKNIFTY', 'FINNIFTY'])
    parser.add_argument('--output-json', default='data/backtest_results.json')

    args = parser.parse_args()

    print("\n╔══════════════════════════════════════════════════════════════════════╗")
    print("║              📊 STEP 2: BACKTEST EXECUTION (Simplified)            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝\n")

    all_results = {}

    for symbol in args.symbols:
        logger.info(f"\n🔄 Running backtest for {symbol}...")

        # Generate sample data
        df = generate_sample_data(symbol, days=252)

        # Run backtest
        bt = SimpleBacktester()
        results = bt.backtest(df)

        all_results[symbol] = results

        # Print results
        logger.info(f"✅ {symbol} Backtest Complete:")
        logger.info(f"   Final Capital: ₹{results['final_capital']:,.0f}")
        logger.info(f"   Total Return: {results['total_return_pct']:+.2f}%")
        logger.info(f"   Win Rate: {results['win_rate']:.1f}%")
        logger.info(f"   Total Trades: {results['wins'] + results['losses']}")
        logger.info(f"   Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        logger.info(f"   Max Drawdown: {results['max_drawdown']:.2f}%")

    # Save results
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'strategy': 'MA Crossover (20/50)',
        'initial_capital': 1000000,
        'results': all_results
    }

    import os
    os.makedirs(os.path.dirname(args.output_json) or '.', exist_ok=True)

    with open(args.output_json, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"\n✅ Results saved to {args.output_json}")
    logger.info(f"\n╔══════════════════════════════════════════════════════════════════════╗")
    logger.info(f"║                      ✅ STEP 2 COMPLETE                            ║")
    logger.info(f"╚══════════════════════════════════════════════════════════════════════╝\n")


if __name__ == '__main__':
    main()
