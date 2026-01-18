"""
Bull Call Spread Strategy
Bullish strategy with limited risk and reward
"""
import pandas as pd
import numpy as np

class BullCallSpreadStrategy:
    """
    Bull Call Spread: Buy lower strike call + Sell higher strike call
    
    Use Case: Moderately bullish outlook
    Max Profit: (Higher Strike - Lower Strike) - Net Premium
    Max Loss: Net premium paid
    Breakeven: Lower Strike + Net Premium
    """
    
    def __init__(self, buy_strike, sell_strike, buy_premium, sell_premium, quantity=1):
        self.buy_strike = buy_strike
        self.sell_strike = sell_strike
        self.buy_premium = buy_premium
        self.sell_premium = sell_premium
        self.quantity = quantity
        self.strategy_name = "Bull_Call_Spread"
        
        # Net premium (debit paid)
        self.net_premium = buy_premium - sell_premium
    
    def calculate_payoff(self, spot_prices):
        """Calculate P&L at different spot prices"""
        payoffs = []
        
        for spot in spot_prices:
            # Long call payoff
            if spot > self.buy_strike:
                long_call_pnl = spot - self.buy_strike - self.buy_premium
            else:
                long_call_pnl = -self.buy_premium
            
            # Short call payoff
            if spot > self.sell_strike:
                short_call_pnl = -(spot - self.sell_strike) + self.sell_premium
            else:
                short_call_pnl = self.sell_premium
            
            total_pnl = (long_call_pnl + short_call_pnl) * self.quantity
            payoffs.append({'spot': spot, 'pnl': total_pnl})
        
        return pd.DataFrame(payoffs)
    
    def calculate_breakeven(self):
        """Lower strike + Net premium"""
        return self.buy_strike + self.net_premium
    
    def calculate_max_profit(self):
        """Spread width - Net premium"""
        return (self.sell_strike - self.buy_strike - self.net_premium) * self.quantity
    
    def calculate_max_loss(self):
        """Net premium paid"""
        return self.net_premium * self.quantity
    
    def get_strategy_summary(self):
        """Return strategy details"""
        return {
            'strategy': self.strategy_name,
            'buy_strike': self.buy_strike,
            'sell_strike': self.sell_strike,
            'net_premium': round(self.net_premium, 2),
            'breakeven': round(self.calculate_breakeven(), 2),
            'max_profit': round(self.calculate_max_profit(), 2),
            'max_loss': round(self.calculate_max_loss(), 2),
            'risk_reward_ratio': round(self.calculate_max_profit() / self.calculate_max_loss(), 2)
        }

# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("  BULL CALL SPREAD STRATEGY")
    print("=" * 80)
    
    # Example: Expect TCS to rise from 3400 to 3600
    # Buy 3400 Call @ 80
    # Sell 3600 Call @ 40
    # Net Premium = 80 - 40 = 40
    
    strategy = BullCallSpreadStrategy(
        buy_strike=3400,
        sell_strike=3600,
        buy_premium=80,
        sell_premium=40,
        quantity=100
    )
    
    summary = strategy.get_strategy_summary()
    print("\nStrategy Setup:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Calculate payoff
    spot_range = np.arange(3200, 3800, 100)
    payoff_df = strategy.calculate_payoff(spot_range)
    
    print("\n\nPayoff Analysis:")
    print(payoff_df.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("  BULL CALL SPREAD READY FOR EXECUTION")
    print("=" * 80)
