#!/usr/bin/env python3
"""
Local CSV Backtester for InfinityAI.Pro
Reads historical data from local Yahoo Finance CSV files
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
import argparse
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalBacktester:
    """MA Crossover Backtester with Local CSV Loading"""

    def __init__(
        self,
        initial_capital: float = 1000000,
        commission: float = 0.0005,
        risk_per_trade: float = 0.02,
        ma_short: int = 20,
        ma_long: int = 50
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.risk_per_trade = risk_per_trade
        self.ma_short = ma_short
        self.ma_long = ma_long

        self.cash = initial_capital
        self.position = 0
        self.entry_price = 0
        self.entry_date = None
        self.trades = []
        self.equity_curve = [initial_capital]
        self.dates = []

    def load_data_from_csv(
        self,
        data_dir: str,
        symbol: str,
        interval: str = '1d',
        period: str = '1y'
    ) -> Optional[pd.DataFrame]:
        """
        Load historical data from local CSV

        Args:
            data_dir: Local data directory
            symbol: Symbol name (NIFTY, BANKNIFTY, etc.)
            interval: Time interval (1d, 1h, 15m)
            period: Period (6m, 1y, 3y)

        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            # Construct file path
            file_path = os.path.join(data_dir, symbol, f"{symbol}_{interval}_{period}.csv")

            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None

            # Load CSV
            df = pd.read_csv(file_path)

            # Ensure proper column names (case-insensitive)
            df.columns = [col.lower() for col in df.columns]

            # Parse date
            if 'date' in df.columns:
                df['timestamp'] = pd.to_datetime(df['date'])
                df = df.drop('date', axis=1)
            elif 'timestamp' not in df.columns:
                logger.error(f"No date/timestamp column found in {file_path}")
                return None

            # Validate required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"Missing columns in {file_path}: {missing_cols}")
                return None

            # Sort by date
            df = df.sort_values('timestamp').reset_index(drop=True)

            logger.info(f"✅ Loaded {len(df)} candles from {file_path}")
            return df

        except Exception as e:
            logger.error(f"❌ Error loading data: {str(e)}")
            return None

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MA Crossover signals"""
        df['ma_short'] = df['close'].rolling(self.ma_short).mean()
        df['ma_long'] = df['close'].rolling(self.ma_long).mean()
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

        # Reset state
        self.cash = self.initial_capital
        self.position = 0
        self.entry_price = 0
        self.entry_date = None
        self.trades = []
        self.equity_curve = [self.initial_capital]
        self.dates = []

        # Start after MA warm-up period
        for i in range(self.ma_long, len(df)):
            current_price = df['close'].iloc[i]
            signal = df['signal'].iloc[i]
            date = df['timestamp'].iloc[i]

            # Exit signal
            if self.position > 0 and signal == -1:
                gross_pnl = (current_price - self.entry_price) * self.position
                commission_cost = (self.entry_price * self.position * self.commission) + \
                                  (current_price * self.position * self.commission)
                net_pnl = gross_pnl - commission_cost

                self.cash += current_price * self.position

                results['trades'].append({
                    'entry_date': str(self.entry_date) if self.entry_date else None,
                    'exit_date': str(date),
                    'entry_price': float(self.entry_price),
                    'exit_price': float(current_price),
                    'shares': int(self.position),
                    'gross_pnl': float(gross_pnl),
                    'commission': float(commission_cost),
                    'net_pnl': float(net_pnl),
                    'return_pct': float((net_pnl / (self.entry_price * self.position)) * 100) if self.entry_price > 0 else 0
                })

                if net_pnl > 0:
                    results['wins'] += 1
                else:
                    results['losses'] += 1

                results['total_pnl'] += net_pnl
                self.position = 0
                self.entry_price = 0

            # Entry signal
            elif self.position == 0 and signal == 1:
                risk_amount = self.cash * self.risk_per_trade
                self.position = int(risk_amount / current_price)
                if self.position > 0:
                    self.entry_price = current_price
                    self.entry_date = date
                    self.cash -= current_price * self.position

            # Calculate equity
            current_equity = self.cash
            if self.position > 0:
                current_equity += self.position * current_price

            self.equity_curve.append(current_equity)
            self.dates.append(date)

        # Calculate final metrics
        equity_array = np.array(self.equity_curve)
        returns = np.diff(equity_array) / equity_array[:-1]

        results['final_capital'] = float(self.cash + (self.position * df['close'].iloc[-1] if self.position > 0 else 0))
        results['total_return_pct'] = float(((results['final_capital'] - self.initial_capital) / self.initial_capital) * 100)
        results['win_rate'] = float((results['wins'] / (results['wins'] + results['losses']) * 100) if (results['wins'] + results['losses']) > 0 else 0)

        # Max drawdown
        peak = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - peak) / peak
        results['max_drawdown'] = float(np.min(drawdown) * 100)

        # Sharpe ratio (annualized)
        if len(returns) > 0 and np.std(returns) > 0:
            results['sharpe_ratio'] = float((np.mean(returns) / np.std(returns)) * np.sqrt(252))
        else:
            results['sharpe_ratio'] = 0.0

        # Average trade metrics
        if results['wins'] + results['losses'] > 0:
            results['avg_trade_pnl'] = float(results['total_pnl'] / (results['wins'] + results['losses']))
        else:
            results['avg_trade_pnl'] = 0.0

        logger.info(f"Backtest complete: {results['wins']} wins, {results['losses']} losses, {results['win_rate']:.2f}% win rate")

        return results


async def main():
    parser = argparse.ArgumentParser(description='Run backtests on local Yahoo Finance data')
    parser.add_argument(
        '--symbols',
        nargs='+',
        default=['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX', 'GOLD', 'CRUDEOIL'],
        help='Symbols to backtest'
    )
    parser.add_argument(
        '--interval',
        default='1d',
        choices=['1d', '1h', '15m'],
        help='Time interval'
    )
    parser.add_argument(
        '--period',
        default='1y',
        choices=['6m', '1y', '3y'],
        help='Period to backtest'
    )
    parser.add_argument(
        '--data-dir',
        default='data/yahoo_historical',
        help='Local data directory'
    )
    parser.add_argument(
        '--output-json',
        default='data/backtest_results.json',
        help='Output JSON file path'
    )
    parser.add_argument(
        '--initial-capital',
        type=float,
        default=1000000,
        help='Initial capital in INR'
    )
    parser.add_argument(
        '--ma-short',
        type=int,
        default=20,
        help='Short MA period'
    )
    parser.add_argument(
        '--ma-long',
        type=int,
        default=50,
        help='Long MA period'
    )

    args = parser.parse_args()

    logger.info("╔═══════════════════════════════════════════════════════╗")
    logger.info("║      YAHOO FINANCE BACKTESTER - REAL DATA            ║")
    logger.info("╚═══════════════════════════════════════════════════════╝")
    logger.info(f"Symbols: {', '.join(args.symbols)}")
    logger.info(f"Interval: {args.interval}, Period: {args.period}")
    logger.info(f"Data Dir: {args.data_dir}")
    logger.info(f"Initial Capital: ₹{args.initial_capital:,.0f}")
    logger.info(f"Strategy: MA({args.ma_short}/{args.ma_long}) Crossover\n")

    all_results = {}

    for symbol in args.symbols:
        logger.info(f"{'='*60}")
        logger.info(f"🔍 Backtesting {symbol} ({args.interval}, {args.period})")
        logger.info(f"{'='*60}")

        backtester = LocalBacktester(
            initial_capital=args.initial_capital,
            commission=0.0005,
            risk_per_trade=0.02,
            ma_short=args.ma_short,
            ma_long=args.ma_long
        )

        # Load data from local CSV
        df = backtester.load_data_from_csv(
            data_dir=args.data_dir,
            symbol=symbol,
            interval=args.interval,
            period=args.period
        )

        if df is None:
            logger.warning(f"⚠️  Skipping {symbol} - no data available")
            continue

        # Run backtest
        results = backtester.backtest(df)
        results['symbol'] = symbol
        results['interval'] = args.interval
        results['period'] = args.period
        results['data_points'] = len(df)
        results['date_range'] = {
            'start': str(df['timestamp'].iloc[0]) if not isinstance(df['timestamp'].iloc[0], str) else df['timestamp'].iloc[0],
            'end': str(df['timestamp'].iloc[-1]) if not isinstance(df['timestamp'].iloc[-1], str) else df['timestamp'].iloc[-1]
        }

        all_results[symbol] = results

        # Print summary
        logger.info(f"\n📊 {symbol} Results:")
        logger.info(f"  Total Trades: {results['wins'] + results['losses']}")
        logger.info(f"  Win Rate: {results['win_rate']:.2f}%")
        logger.info(f"  Total PnL: ₹{results['total_pnl']:,.2f}")
        logger.info(f"  Total Return: {results['total_return_pct']:.2f}%")
        logger.info(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        logger.info(f"  Max Drawdown: {results['max_drawdown']:.2f}%\n")

    # Save results
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)

    output = {
        'timestamp': datetime.now().isoformat(),
        'config': {
            'interval': args.interval,
            'period': args.period,
            'initial_capital': args.initial_capital,
            'ma_short': args.ma_short,
            'ma_long': args.ma_long,
            'data_dir': args.data_dir
        },
        'results': all_results,
        'summary': {
            'total_symbols': len(all_results),
            'avg_win_rate': float(np.mean([r['win_rate'] for r in all_results.values()])) if all_results else 0,
            'avg_sharpe': float(np.mean([r['sharpe_ratio'] for r in all_results.values()])) if all_results else 0,
            'total_pnl': float(sum([r['total_pnl'] for r in all_results.values()])) if all_results else 0
        }
    }

    with open(args.output_json, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info(f"\n✅ Results saved to {args.output_json}")
    logger.info(f"\n{'='*60}")
    logger.info(f"📈 OVERALL SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Symbols Tested: {output['summary']['total_symbols']}")
    logger.info(f"Average Win Rate: {output['summary']['avg_win_rate']:.2f}%")
    logger.info(f"Average Sharpe Ratio: {output['summary']['avg_sharpe']:.2f}")
    logger.info(f"Combined PnL: ₹{output['summary']['total_pnl']:,.2f}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
