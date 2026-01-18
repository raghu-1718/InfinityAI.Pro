"""
Covered Call Strategy
Generate income by selling call options on stocks you own
"""
import pandas as pd
import numpy as np

class CoveredCallStrategy:
    """
    Covered Call: Own stock + Sell call option
    
    Use Case: Generate income from stable/slightly bullish stock
    Max Profit: Premium + (Strike - Stock Price)
    Max Loss: Stock price decline (minus premium received)
    Breakeven: Stock Price - Premium
    """
    
    def __init__(self, stock_price, strike_price, premium, quantity=100):
        self.stock_price = stock_price
        self.strike_price = strike_price
        self.premium = premium
        self.quantity = quantity
        self.strategy_name = "Covered_Call"
    
    def calculate_payoff(self, spot_prices):
        """
        Calculate P&L at different spot prices at expiry
        """
        payoffs = []
        
        for spot in spot_prices:
            # Stock P&L
            stock_pnl = (spot - self.stock_price) * self.quantity
            
            # Call option P&L (sold, so we lose if ITM)
            if spot > self.strike_price:
                call_pnl = -(spot - self.strike_price) * self.quantity
            else:
                call_pnl = 0
            
            # Premium received (profit)
            premium_income = self.premium * self.quantity
            
            total_pnl = stock_pnl + call_pnl + premium_income
            payoffs.append({'spot': spot, 'pnl': total_pnl})
        
        return pd.DataFrame(payoffs)
    
    def calculate_breakeven(self):
        """Stock price - premium received"""
        return self.stock_price - self.premium
    
    def calculate_max_profit(self):
        """Premium + (Strike - Stock Price) * Quantity"""
        return (self.premium + max(0, self.strike_price - self.stock_price)) * self.quantity
    
    def calculate_max_loss(self):
        """Unlimited downside (stock can go to zero)"""
        return (self.stock_price - self.premium) * self.quantity
    
    def get_strategy_summary(self):
        """Return strategy details"""
        return {
            'strategy': self.strategy_name,
            'stock_price': self.stock_price,
            'strike_price': self.strike_price,
            'premium': self.premium,
            'quantity': self.quantity,
            'breakeven': round(self.calculate_breakeven(), 2),
            'max_profit': round(self.calculate_max_profit(), 2),
            'max_loss': round(self.calculate_max_loss(), 2),
            'risk_reward': 'Limited Profit, High Risk (stock decline)'
        }

# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("  COVERED CALL STRATEGY")
    print("=" * 80)
    
    # Example: Own 100 shares of TCS at Rs. 3500
    # Sell Rs. 3600 call for Rs. 50 premium
    strategy = CoveredCallStrategy(
        stock_price=3500,
        strike_price=3600,
        premium=50,
        quantity=100
    )
    
    summary = strategy.get_strategy_summary()
    print("\nStrategy Setup:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Calculate payoff at different prices
    spot_range = np.arange(3300, 3800, 50)
    payoff_df = strategy.calculate_payoff(spot_range)
    
    print("\n\nPayoff Analysis:")
    print(payoff_df.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("  COVERED CALL READY FOR BACKTESTING")
    print("=" * 80)
