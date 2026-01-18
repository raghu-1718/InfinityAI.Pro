"""
Enhanced RSI Strategy with Risk Management
Adds stop-loss and take-profit for better risk control
"""
import pandas as pd
import numpy as np
from datetime import datetime

class EnhancedRSIStrategy:
    """
    Enhanced RSI Mean Reversion with Risk Management
    - Buy when RSI < oversold
    - Sell when RSI > overbought
    - Stop Loss: 5% below entry
    - Take Profit: 3% above entry (3:1 risk-reward if SL at 1%)
    """
    
    def __init__(self, period=14, oversold=30, overbought=70, stop_loss_pct=5.0, take_profit_pct=3.0):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.name = f"Enhanced_RSI_{period}_{oversold}_{overbought}_SL{stop_loss_pct}_TP{take_profit_pct}"
    
    def calculate_rsi(self, prices):
        """Calculate RSI indicator"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = pd.Series(gains).rolling(window=self.period).mean()
        avg_loss = pd.Series(losses).rolling(window=self.period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        rsi = np.concatenate([[50], rsi.fillna(50).values])
        return rsi
    
    def backtest(self, df, initial_capital=100000, position_size=0.15):
        """
        Backtest with risk management
        """
        df = df.copy()
        df['RSI'] = self.calculate_rsi(df['close'].values)
        
        capital = initial_capital
        position = 0
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        trades = []
        equity_curve = [initial_capital]
        
        for i in range(1, len(df)):
            current_price = df.iloc[i]['close']
            rsi = df.iloc[i]['RSI']
            
            # Entry logic
            if rsi < self.oversold and position == 0:
                shares = int((capital * position_size) / current_price)
                if shares > 0:
                    position = shares
                    entry_price = current_price
                    stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
                    take_profit = entry_price * (1 + self.take_profit_pct / 100)
                    capital -= shares * current_price
            
            # Exit logic
            elif position > 0:
                exit_triggered = False
                exit_reason = ""
                
                # Stop Loss
                if current_price <= stop_loss:
                    exit_triggered = True
                    exit_reason = "Stop Loss"
                
                # Take Profit
                elif current_price >= take_profit:
                    exit_triggered = True
                    exit_reason = "Take Profit"
                
                # RSI exit (normal exit when RSI > 50)
                elif rsi > 50:
                    exit_triggered = True
                    exit_reason = "RSI Exit"
                
                if exit_triggered:
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
                        'exit_reason': exit_reason,
                        'sl': stop_loss,
                        'tp': take_profit
                    })
                    
                    position = 0
            
            current_equity = capital + (position * current_price if position > 0 else 0)
            equity_curve.append(current_equity)
        
        # Calculate metrics
        if not trades:
            return {'total_trades': 0, 'accuracy': 0, 'message': 'No trades'}
        
        trades_df = pd.DataFrame(trades)
        winning_trades = len(trades_df[trades_df['profit'] > 0])
        win_rate = (winning_trades / len(trades)) * 100
        total_return = ((equity_curve[-1] - initial_capital) / initial_capital) * 100
        
        return {
            'strategy_name': self.name,
            'total_trades': len(trades),
            'winning_trades': winning_trades,
            'win_rate': round(win_rate, 2),
            'accuracy': round(win_rate, 2),
            'total_return': round(total_return, 2),
            'final_capital': round(equity_curve[-1], 2),
            'sl_exits': len(trades_df[trades_df['exit_reason'] == 'Stop Loss']),
            'tp_exits': len(trades_df[trades_df['exit_reason'] == 'Take Profit']),
            'normal_exits': len(trades_df[trades_df['exit_reason'] == 'RSI Exit']),
            'trades': trades_df.to_dict('records')
        }

# Test
if __name__ == "__main__":
    import sys
    sys.path.append('.')
    from rsi_strategy import generate_sample_data
    
    print("=" * 80)
    print("  ENHANCED RSI STRATEGY WITH RISK MANAGEMENT")
    print("=" * 80)
    
    df = generate_sample_data("RELIANCE", days=365)
    
    strategy = EnhancedRSIStrategy(
        period=14,
        oversold=30,
        overbought=70,
        stop_loss_pct=5.0,
        take_profit_pct=3.0
    )
    
    results = strategy.backtest(df)
    
    print(f"\nResults:")
    print(f"  Accuracy: {results['accuracy']}%")
    print(f"  Total Return: {results['total_return']}%")
    print(f"  Total Trades: {results['total_trades']}")
    print(f"  Winning: {results['winning_trades']}")
    print(f"  Stop Loss Exits: {results['sl_exits']}")
    print(f"  Take Profit Exits: {results['tp_exits']}")
    print(f"  Normal Exits: {results['normal_exits']}")
