#!/usr/bin/env python3
"""
Simple Backtest Engine - Pure Python implementation for validation
No external backtesting framework dependencies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, Tuple

# Generate sample OHLCV data
def generate_sample_data(symbol: str, days: int = 365, starting_price: float = 20000):
    """Generate realistic OHLCV data for backtesting"""
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Generate realistic price movements
    returns = np.random.normal(0.0005, 0.015, days)
    prices = starting_price * (1 + returns).cumprod()
    
    # Generate OHLCV
    data = {
        'datetime': dates,
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
        'high': prices * (1 + np.abs(np.random.normal(0.01, 0.01, days))),
        'low': prices * (1 - np.abs(np.random.normal(0.01, 0.01, days))),
        'close': prices,
        'volume': np.random.randint(1000000, 50000000, days),
    }
    
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    return df


def calculate_ma(prices: np.ndarray, period: int) -> np.ndarray:
    """Calculate Moving Average"""
    ma = np.full_like(prices, np.nan)
    for i in range(period - 1, len(prices)):
        ma[i] = np.mean(prices[i - period + 1:i + 1])
    return ma


def backtest_ma_crossover(df: pd.DataFrame, fast_period: int = 20, slow_period: int = 50,
                          initial_capital: float = 1000000.0, fees: float = 0.0005) -> Dict:
    """
    MA Crossover backtest using simple logic
    """
    
    prices = df['close'].values
    
    # Calculate MAs
    fast_ma = calculate_ma(prices, fast_period)
    slow_ma = calculate_ma(prices, slow_period)
    
    # Generate signals: 1 = buy, -1 = sell, 0 = hold
    signals = np.zeros(len(prices))
    position = 0  # 0 = no position, 1 = long
    entry_price = 0
    trades = []
    
    capital = initial_capital
    shares = 0
    equity_curve = [capital]
    
    for i in range(slow_period, len(prices)):
        price = prices[i]
        
        # Signal generation
        if not np.isnan(fast_ma[i]) and not np.isnan(slow_ma[i]):
            if fast_ma[i] > slow_ma[i] and position == 0:  # BUY
                # Buy with available capital
                shares = (capital * 0.95) / price  # Use 95% of capital
                capital -= shares * price * (1 + fees)
                entry_price = price
                position = 1
                trades.append({'date': i, 'type': 'buy', 'price': price, 'shares': shares})
                
            elif fast_ma[i] < slow_ma[i] and position == 1:  # SELL
                # Sell current position
                capital += shares * price * (1 - fees)
                pnl = (price - entry_price) * shares
                pnl_pct = (price - entry_price) / entry_price * 100
                trades.append({
                    'date': i,
                    'type': 'sell',
                    'price': price,
                    'shares': shares,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
                position = 0
                shares = 0
        
        # Calculate equity
        if position == 1:
            equity = capital + (shares * price)
        else:
            equity = capital
        
        equity_curve.append(equity)
    
    # Close position at end
    if position == 1:
        capital += shares * prices[-1] * (1 - fees)
    
    equity_curve = np.array(equity_curve)
    
    # Calculate metrics
    total_return = (equity_curve[-1] - initial_capital) / initial_capital
    daily_returns = np.diff(equity_curve) / equity_curve[:-1]
    
    # Filter out zero returns for Sharpe calculation
    nonzero_returns = daily_returns[daily_returns != 0]
    
    if len(nonzero_returns) > 0:
        sharpe = np.sqrt(252) * np.mean(nonzero_returns) / (np.std(nonzero_returns) + 1e-8)
    else:
        sharpe = 0
    
    # Max drawdown
    cummax = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - cummax) / cummax
    max_drawdown = np.min(drawdown)
    
    # Win rate
    closed_trades = [t for t in trades if t['type'] == 'sell']
    win_count = len([t for t in closed_trades if t.get('pnl', 0) > 0])
    win_rate = (win_count / len(closed_trades)) * 100 if closed_trades else 0
    
    # Profit factor
    wins = sum([t.get('pnl', 0) for t in closed_trades if t.get('pnl', 0) > 0])
    losses = abs(sum([t.get('pnl', 0) for t in closed_trades if t.get('pnl', 0) < 0]))
    profit_factor = wins / losses if losses > 0 else (1 if wins > 0 else 0)
    
    return {
        'symbol': df.index.name if hasattr(df.index, 'name') else 'UNKNOWN',
        'strategy': f'MA Crossover ({fast_period}/{slow_period})',
        'period_days': len(df),
        'candles': len(df),
        'performance': {
            'total_return_pct': float(total_return * 100),
            'annual_return_pct': float(total_return * 100),
            'sharpe_ratio': float(sharpe),
            'sortino_ratio': float(sharpe * 0.8),  # Approximation
            'max_drawdown_pct': float(max_drawdown * 100),
            'win_rate_pct': float(win_rate),
            'profit_factor': float(profit_factor),
        },
        'trades': {
            'total': len(closed_trades),
            'won': win_count,
            'lost': len(closed_trades) - win_count,
            'avg_pnl': float(np.mean([t.get('pnl', 0) for t in closed_trades]) if closed_trades else 0),
            'best_trade_pct': float(max([t.get('pnl_pct', 0) for t in closed_trades], default=0)),
            'worst_trade_pct': float(min([t.get('pnl_pct', 0) for t in closed_trades], default=0)),
        },
        'equity_final': float(equity_curve[-1]),
        'capital_used': float(initial_capital),
    }


def main():
    symbols = {
        'NIFTY': 20000,
        'BANKNIFTY': 45000,
        'FINNIFTY': 20000,
    }
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'backtests': {}
    }
    
    print("\n" + "="*80)
    print("🎯 BACKTEST ENGINE - Pure Python Implementation")
    print("="*80)
    
    for symbol, starting_price in symbols.items():
        print(f"\n📊 Backtesting {symbol}...")
        print("-" * 80)
        
        # Generate sample data
        df = generate_sample_data(symbol, days=365, starting_price=starting_price)
        df.index.name = symbol
        
        # Run backtest
        report = backtest_ma_crossover(df)
        results['backtests'][symbol] = report
        
        # Print results
        perf = report['performance']
        trades = report['trades']
        
        print(f"✅ {symbol} Backtest Complete")
        print(f"   Returns:           {perf['total_return_pct']:>8.2f}%")
        print(f"   Sharpe Ratio:      {perf['sharpe_ratio']:>8.2f}")
        print(f"   Max Drawdown:      {perf['max_drawdown_pct']:>8.2f}%")
        print(f"   Total Trades:      {trades['total']:>8}")
        print(f"   Win Rate:          {perf['win_rate_pct']:>8.2f}%")
        print(f"   Profit Factor:     {perf['profit_factor']:>8.2f}")
        print(f"   Final Equity:      ${report['equity_final']:>15,.2f}")
    
    # Save results
    output_dir = 'data/backtest_results'
    os.makedirs(output_dir, exist_ok=True)
    
    results_file = os.path.join(output_dir, f'backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print(f"✅ Results saved to: {results_file}")
    print("="*80)
    
    # Detailed Summary
    print("\n📈 PERFORMANCE SUMMARY")
    print("-" * 80)
    print(f"{'Symbol':<12} {'Return':<10} {'Sharpe':<8} {'DD':<8} {'Trades':<8} {'Win%':<8} {'PF':<8}")
    print("-" * 80)
    
    for symbol, report in results['backtests'].items():
        perf = report['performance']
        trades = report['trades']
        print(f"{symbol:<12} {perf['total_return_pct']:>8.2f}% {perf['sharpe_ratio']:>7.2f} "
              f"{perf['max_drawdown_pct']:>7.2f}% {trades['total']:>7} {perf['win_rate_pct']:>7.2f}% "
              f"{perf['profit_factor']:>7.2f}")
    
    print("\n🚀 Next Steps:")
    print("   1. Ingest real Dhan data:")
    print("      python tools/ingest_dhan_historical.py --credentials-user-id 1101302170")
    print("   2. Run live backtests with real data")
    print("   3. Deploy cloud orchestrator for automated backtesting")
    print("   4. Integrate results into trading dashboard")
    
    return results


if __name__ == '__main__':
    main()
