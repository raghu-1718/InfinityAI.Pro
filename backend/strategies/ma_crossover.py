"""
Moving Average Crossover Strategy
Classic trend-following strategy
"""
import pandas as pd
import numpy as np
from datetime import datetime

class MAStrategy:
    """
    Moving Average Crossover Strategy
    - Buy when fast MA crosses above slow MA (golden cross)
    - Sell when fast MA crosses below slow MA (death cross)
    """
    
    def __init__(self, fast_period=9, slow_period=21):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.name = f"MA_{fast_period}_{slow_period}"
    
    def generate_signals(self, df):
        """Generate buy/sell signals"""
        df = df.copy()
        
        # Calculate moving averages
        df['MA_fast'] = df['close'].rolling(window=self.fast_period).mean()
        df['MA_slow'] = df['close'].rolling(window=self.slow_period).mean()
        
        # Generate signals
        df['signal'] = 0
        
        # Buy when fast crosses above slow
        df.loc[(df['MA_fast'] > df['MA_slow']) & 
               (df['MA_fast'].shift(1) <= df['MA_slow'].shift(1)), 'signal'] = 1
        
        # Sell when fast crosses below slow
        df.loc[(df['MA_fast'] < df['MA_slow']) & 
               (df['MA_fast'].shift(1) >= df['MA_slow'].shift(1)), 'signal'] = -1
        
        return df
    
    def backtest(self, df, initial_capital=100000, position_size=0.2):
        """Backtest the strategy"""
        df = self.generate_signals(df)
        
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = [initial_capital]
        
        for i in range(1, len(df)):
            current_price = df.iloc[i]['close']
            signal = df.iloc[i]['signal']
            
            # Buy signal
            if signal == 1 and position == 0:
                shares = int((capital * position_size) / current_price)
                if shares > 0:
                    position = shares
                    entry_price = current_price
                    capital -= shares * current_price
            
            # Sell signal
            elif signal == -1 and position > 0:
                proceeds = position * current_price
                capital += proceeds
                profit = proceeds - (position * entry_price)
                profit_pct = (profit / (position * entry_price)) * 100
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'shares': position,
                    'profit': profit,
                    'profit_pct': profit_pct
                })
                
                position = 0
                entry_price = 0
            
            # Track equity
            current_equity = capital + (position * current_price if position > 0 else 0)
            equity_curve.append(current_equity)
        
        # Calculate metrics
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'accuracy': 0,
                'message': 'No trades executed'
            }
        
        trades_df = pd.DataFrame(trades)
        winning_trades = len(trades_df[trades_df['profit'] > 0])
        win_rate = (winning_trades / len(trades)) * 100
        
        total_return = ((equity_curve[-1] - initial_capital) / initial_capital) * 100
        
        return {
            'strategy_name': self.name,
            'total_trades': len(trades),
            'winning_trades': winning_trades,
            'losing_trades': len(trades) - winning_trades,
            'win_rate': round(win_rate, 2),
            'accuracy': round(win_rate, 2),
            'total_return': round(total_return, 2),
            'initial_capital': initial_capital,
            'final_capital': round(equity_curve[-1], 2),
            'trades': trades_df.to_dict('records')
        }

# Import sample data generator from RSI strategy
import sys
sys.path.append('.')
from rsi_strategy import generate_sample_data

def main():
    """Test MA Crossover strategy"""
    print("=" * 80)
    print("  MA CROSSOVER STRATEGY - BACKTEST")
    print("=" * 80)
    
    df = generate_sample_data("BANK NIFTY", days=365)
    print(f"\n[INFO] Testing on {len(df)} days of data")
    
    strategy = MAStrategy(fast_period=9, slow_period=21)
    results = strategy.backtest(df)
    
    print("\n" + "=" * 80)
    print("  RESULTS")
    print("=" * 80)
    print(f"\nStrategy: {results['strategy_name']}")
    print(f"Total Return: {results['total_return']}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']}%")
    print(f"ACCURACY: {results['accuracy']}%")
    
    return results

if __name__ == "__main__":
    main()
