#!/usr/bin/env python3
"""
Strategy Optimization for Equity Indices
Tests multiple MA combinations to find optimal parameters
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple
import itertools

class StrategyOptimizer:
    """Optimize MA crossover parameters for different symbols"""

    def __init__(self, data_dir: str = "data/yahoo_historical"):
        self.data_dir = Path(data_dir)
        self.results = {}

    def load_data(self, symbol: str, interval: str = "1d", period: str = "1y") -> pd.DataFrame:
        """Load historical data from CSV"""
        file_path = self.data_dir / symbol / f"{symbol}_{interval}_{period}.csv"

        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            return None

        df = pd.read_csv(file_path)
        df.columns = [c.lower() for c in df.columns]
        df['timestamp'] = pd.to_datetime(df['date'] if 'date' in df.columns else df['timestamp'])
        return df.sort_values('timestamp').reset_index(drop=True)

    def backtest_strategy(self, df: pd.DataFrame, ma_short: int, ma_long: int,
                         initial_capital: float = 1000000) -> Dict:
        """Backtest with specific MA parameters"""
        if df is None or len(df) < ma_long:
            return None

        df = df.copy()
        df['ma_short'] = df['close'].rolling(ma_short).mean()
        df['ma_long'] = df['close'].rolling(ma_long).mean()
        df['signal'] = 0
        df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1
        df.loc[df['ma_short'] < df['ma_long'], 'signal'] = -1

        cash = initial_capital
        position = 0
        entry_price = 0
        entry_date = None
        trades = []
        equity = []

        for i in range(ma_long, len(df)):
            price = df['close'].iloc[i]
            signal = df['signal'].iloc[i]
            prev_signal = df['signal'].iloc[i-1] if i > ma_long else 0
            date = df['timestamp'].iloc[i]

            # Exit position (crossover from buy to sell)
            if position > 0 and signal == -1 and prev_signal == 1:
                exit_price = price
                pnl = (exit_price - entry_price) * position
                gross_pnl = pnl
                commission = (entry_price * position + exit_price * position) * 0.0005
                net_pnl = pnl - commission

                trades.append({
                    'entry_date': str(entry_date),
                    'exit_date': str(date),
                    'entry_price': float(entry_price),
                    'exit_price': float(exit_price),
                    'shares': int(position),
                    'gross_pnl': float(gross_pnl),
                    'commission': float(commission),
                    'net_pnl': float(net_pnl),
                    'return_pct': float((exit_price - entry_price) / entry_price * 100)
                })

                cash += position * exit_price - commission
                position = 0
                entry_price = 0
                entry_date = None

            # Enter position (crossover from sell to buy)
            elif position == 0 and signal == 1 and prev_signal == -1:
                risk_amount = cash * 0.02  # 2% risk per trade
                position = int(risk_amount / price)
                entry_price = price
                entry_date = date
                commission = price * position * 0.0005
                cash -= position * price + commission

            # Track equity
            current_equity = cash + (position * price if position > 0 else 0)
            equity.append(current_equity)

        # Close any open position at end
        if position > 0:
            exit_price = df['close'].iloc[-1]
            pnl = (exit_price - entry_price) * position
            commission = (entry_price * position + exit_price * position) * 0.0005
            net_pnl = pnl - commission

            trades.append({
                'entry_date': str(entry_date),
                'exit_date': str(df['timestamp'].iloc[-1]),
                'entry_price': float(entry_price),
                'exit_price': float(exit_price),
                'shares': int(position),
                'gross_pnl': float(pnl),
                'commission': float(commission),
                'net_pnl': float(net_pnl),
                'return_pct': float((exit_price - entry_price) / entry_price * 100)
            })

            cash += position * exit_price - commission

        # Calculate metrics
        final_equity = cash
        total_pnl = sum(t['net_pnl'] for t in trades)
        wins = len([t for t in trades if t['net_pnl'] > 0])
        losses = len(trades) - wins

        # Sharpe ratio (simplified)
        if len(equity) > 0:
            returns = np.diff(equity) / equity[:-1] if len(equity) > 1 else [0]
            sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0
        else:
            sharpe = 0

        # Max drawdown
        peak = initial_capital
        max_dd = 0
        for eq in equity:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd

        return {
            'ma_short': ma_short,
            'ma_long': ma_long,
            'trades': len(trades),
            'wins': wins,
            'losses': losses,
            'win_rate': float(wins / len(trades) * 100) if len(trades) > 0 else 0,
            'total_pnl': float(total_pnl),
            'total_return_pct': float((final_equity - initial_capital) / initial_capital * 100),
            'sharpe_ratio': float(sharpe),
            'max_drawdown': float(max_dd * 100),
            'avg_trade_pnl': float(total_pnl / len(trades)) if len(trades) > 0 else 0,
            'trade_details': trades
        }

    def optimize_symbol(self, symbol: str, interval: str = "1d", period: str = "1y") -> Dict:
        """Find optimal MA parameters for a symbol"""
        print(f"\n{'='*70}")
        print(f"Optimizing {symbol} ({interval}, {period})")
        print(f"{'='*70}")

        df = self.load_data(symbol, interval, period)
        if df is None:
            return None

        print(f"Data loaded: {len(df)} candles from {df['timestamp'].min()} to {df['timestamp'].max()}")

        # Test multiple MA combinations
        ma_combinations = [
            (5, 20),   # Fast: 5/20
            (10, 30),  # Medium-fast: 10/30
            (20, 50),  # Standard: 20/50
            (50, 200), # Slow: 50/200
            (12, 26),  # MACD-like: 12/26
            (8, 21),   # Fibonacci: 8/21
            (9, 21),   # Short-term: 9/21
            (15, 45),  # Mid-range: 15/45
        ]

        best_result = None
        best_score = -999999
        all_results = []

        for ma_short, ma_long in ma_combinations:
            result = self.backtest_strategy(df, ma_short, ma_long)
            if result and result['trades'] > 0:
                # Score = Total Return + Sharpe - MaxDD
                score = result['total_return_pct'] + result['sharpe_ratio'] - result['max_drawdown']
                result['optimization_score'] = float(score)
                all_results.append(result)

                print(f"MA({ma_short}/{ma_long}): {result['trades']} trades, "
                      f"P&L: Rs.{result['total_pnl']:,.0f}, "
                      f"Return: {result['total_return_pct']:.2f}%, "
                      f"Sharpe: {result['sharpe_ratio']:.2f}, "
                      f"Score: {score:.2f}")

                if score > best_score:
                    best_score = score
                    best_result = result
            else:
                print(f"MA({ma_short}/{ma_long}): No trades or insufficient data")

        if best_result:
            print(f"\n==> BEST PARAMETERS: MA({best_result['ma_short']}/{best_result['ma_long']})")
            print(f"   Trades: {best_result['trades']}, Win Rate: {best_result['win_rate']:.1f}%")
            print(f"   Total P&L: Rs.{best_result['total_pnl']:,.2f}")
            print(f"   Return: {best_result['total_return_pct']:.2f}%")
            print(f"   Sharpe: {best_result['sharpe_ratio']:.2f}")
            print(f"   Max DD: {best_result['max_drawdown']:.2f}%")
        else:
            print("\n>>> No profitable strategy found")

        return {
            'symbol': symbol,
            'interval': interval,
            'period': period,
            'best_result': best_result,
            'all_results': all_results
        }

    def optimize_all(self, symbols: List[str], interval: str = "1d", period: str = "1y"):
        """Optimize all symbols"""
        results = {}

        for symbol in symbols:
            result = self.optimize_symbol(symbol, interval, period)
            if result:
                results[symbol] = result

        # Save results
        output_file = Path("data/strategy_optimization_results.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n{'='*70}")
        print(f"OPTIMIZATION COMPLETE")
        print(f"{'='*70}")
        print(f"Results saved to: {output_file}")

        # Summary table
        print(f"\nOPTIMAL PARAMETERS SUMMARY:")
        print(f"{'Symbol':<12} {'MA Params':<12} {'Trades':<8} {'Return %':<10} {'Sharpe':<8}")
        print(f"{'-'*70}")

        for symbol, data in results.items():
            if data['best_result']:
                br = data['best_result']
                print(f"{symbol:<12} "
                      f"MA({br['ma_short']}/{br['ma_long']}){'':>5} "
                      f"{br['trades']:<8} "
                      f"{br['total_return_pct']:>8.2f}% "
                      f"{br['sharpe_ratio']:>7.2f}")
            else:
                print(f"{symbol:<12} No signals found")

        return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Optimize MA crossover strategy")
    parser.add_argument('--symbols', type=str, default='NIFTY,BANKNIFTY,FINNIFTY,SENSEX',
                       help='Comma-separated symbols')
    parser.add_argument('--interval', type=str, default='1d',
                       help='Interval (1d, 1h, 15m)')
    parser.add_argument('--period', type=str, default='1y',
                       help='Period (6m, 1y, 3y)')
    parser.add_argument('--data-dir', type=str, default='data/yahoo_historical',
                       help='Data directory')

    args = parser.parse_args()

    symbols = args.symbols.split(',')

    optimizer = StrategyOptimizer(data_dir=args.data_dir)
    results = optimizer.optimize_all(symbols, args.interval, args.period)
