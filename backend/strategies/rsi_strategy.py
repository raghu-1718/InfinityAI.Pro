"""
RSI Mean Reversion Strategy
Simple but effective strategy that buys oversold and sells overbought conditions
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class RSIStrategy:
    """
    RSI Mean Reversion Strategy
    - Buy when RSI < oversold_threshold (default 30)
    - Sell when RSI > overbought_threshold (default 70)
    - Exit when RSI crosses back to neutral (40-60 range)
    """
    
    def __init__(self, period=14, oversold=30, overbought=70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.name = f"RSI_{period}_{oversold}_{overbought}"
    
    def calculate_rsi(self, prices):
        """Calculate RSI indicator"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = pd.Series(gains).rolling(window=self.period).mean()
        avg_loss = pd.Series(losses).rolling(window=self.period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Prepend NaN for first element to match original length
        rsi = np.concatenate([[50], rsi.fillna(50).values])  # Add first element
        return rsi    
    def generate_signals(self, df):
        """
        Generate buy/sell signals
        Returns DataFrame with 'signal' column: 1=buy, -1=sell, 0=hold
        """
        df = df.copy()
        df['RSI'] = self.calculate_rsi(df['close'].values)
        
        # Initialize signals
        df['signal'] = 0
        
        # Buy signal: RSI crosses below oversold
        df.loc[df['RSI'] < self.oversold, 'signal'] = 1
        
        # Sell signal: RSI crosses above overbought
        df.loc[df['RSI'] > self.overbought, 'signal'] = -1
        
        return df
    
    def backtest(self, df, initial_capital=100000, position_size=0.1):
        """
        Backtest the strategy
        
        Args:
            df: DataFrame with OHLCV data
            initial_capital: Starting capital
            position_size: Fraction of capital per trade (0.1 = 10%)
        
        Returns:
            Dictionary with performance metrics
        """
        df = self.generate_signals(df)
        
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = [initial_capital]
        
        for i in range(1, len(df)):
            current_price = df.iloc[i]['close']
            signal = df.iloc[i]['signal']
            rsi = df.iloc[i]['RSI']
            
            # Entry logic
            if signal == 1 and position == 0:  # Buy signal
                shares = int((capital * position_size) / current_price)
                if shares > 0:
                    position = shares
                    entry_price = current_price
                    cost = shares * current_price
                    capital -= cost
            
            # Exit logic (when RSI returns to normal range)
            elif position > 0 and rsi > 50:  # Exit when RSI above 50
                proceeds = position * current_price
                capital += proceeds
                profit = proceeds - (position * entry_price)
                profit_pct = (profit / (position * entry_price)) * 100
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'shares': position,
                   'profit': profit,
                    'profit_pct': profit_pct,
                    'rsi_entry': df.iloc[i-1]['RSI'] if i > 0 else 50,
                    'rsi_exit': rsi
                })
                
                position = 0
                entry_price = 0
            
            # Calculate current equity
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
        max_equity = max(equity_curve)
        min_equity = min(equity_curve)
        max_drawdown = ((max_equity - min_equity) / max_equity) * 100
        
        avg_win = trades_df[trades_df['profit'] > 0]['profit'].mean() if winning_trades > 0 else 0
        avg_loss = abs(trades_df[trades_df['profit'] < 0]['profit'].mean()) if len(trades) - winning_trades > 0 else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        
        return {
            'strategy_name': self.name,
            'total_trades': len(trades),
            'winning_trades': winning_trades,
            'losing_trades': len(trades) - winning_trades,
            'win_rate': round(win_rate, 2),
            'accuracy': round(win_rate, 2),  # For RSI, win rate = accuracy
            'total_return': round(total_return, 2),
            'max_drawdown': round(max_drawdown, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'initial_capital': initial_capital,
            'final_capital': round(equity_curve[-1], 2),
            'trades': trades_df.to_dict('records'),
            'equity_curve': equity_curve
        }

def generate_sample_data(symbol="RELIANCE", days=365):
    """Generate sample OHLCV data for testing"""
    np.random.seed(42)
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Simulate realistic price movement
    base_price = 2500
    returns = np.random.normal(0.001, 0.02, days)
    prices = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
        'high': prices * (1 + np.random.uniform(0, 0.02, days)),
        'low': prices * (1 - np.random.uniform(0, 0.02, days)),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, days)
    })
    
    df['symbol'] = symbol
    return df

def main():
    """Test the RSI strategy"""
    print("=" * 80)
    print("  RSI MEAN REVERSION STRATEGY - BACKTEST")
    print("=" * 80)
    
    # Generate sample data for RELIANCE
    print("\n[INFO] Generating sample historical data for RELIANCE (365 days)...")
    df = generate_sample_data("RELIANCE", days=365)
    print(f"[OK] Generated {len(df)} days of data")
    print(f"     Price range: Rs. {df['close'].min():.2f} - Rs. {df['close'].max():.2f}")
    
    # Test strategy
    print("\n[INFO] Testing RSI Strategy (Period=14, Oversold=30, Overbought=70)...")
    strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    
    results = strategy.backtest(df, initial_capital=100000, position_size=0.1)
    
    # Display results
    print("\n" + "=" * 80)
    print("  BACKTEST RESULTS")
    print("=" * 80)
    
    print(f"\nStrategy: {results['strategy_name']}")
    print(f"Period: {len(df)} days")
    print(f"Initial Capital: Rs. {results['initial_capital']:,.0f}")
    print(f"Final Capital: Rs. {results['final_capital']:,.0f}")
    
    print(f"\nPerformance Metrics:")
    print(f"  Total Return: {results['total_return']}%")
    print(f"  Max Drawdown: {results['max_drawdown']}%")
    print(f"  Total Trades: {results['total_trades']}")
    print(f"  Winning Trades: {results['winning_trades']}")
    print(f"  Losing Trades: {results['losing_trades']}")
    print(f"  Win Rate: {results['win_rate']}%")
    print(f"  ACCURACY: {results['accuracy']}%")
    print(f"  Avg Win: Rs. {results['avg_win']:,.2f}")
    print(f"  Avg Loss: Rs. {results['avg_loss']:,.2f}")
    print(f"  Profit Factor: {results['profit_factor']:.2f}")
    
    # Show sample trades
    if results['trades']:
        print(f"\nSample Trades (first 5):")
        for i, trade in enumerate(results['trades'][:5], 1):
            print(f"  {i}. Entry: Rs. {trade['entry_price']:.2f}, Exit: Rs. {trade['exit_price']:.2f}, " +
                  f"Profit: Rs. {trade['profit']:.2f} ({trade['profit_pct']:.2f}%)")
    
    print("\n" + "=" * 80)
    print(f"  STRATEGY ACCURACY: {results['accuracy']}%")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    main()
