"""
Iron Condor Strategy
Neutral strategy to profit from low volatility
"""
import pandas as pd
import numpy as np

class IronCondorStrategy:
    """
    Iron Condor: Sell OTM Put + Buy further OTM Put + Sell OTM Call + Buy further OTM Call
    
    Use Case: Profit when stock stays in a range
    Max Profit: Net premium received
    Max Loss: Width of spread - Premium
    Best Market: Low volatility, range-bound
    """
    
    def __init__(self, spot_price, sell_put_strike, buy_put_strike, 
                 sell_call_strike, buy_call_strike,
                 sell_put_premium, buy_put_premium, 
                 sell_call_premium, buy_call_premium, quantity=1):
        self.spot_price = spot_price
        self.sell_put_strike = sell_put_strike
        self.buy_put_strike = buy_put_strike
        self.sell_call_strike = sell_call_strike
        self.buy_call_strike = buy_call_strike
        self.sell_put_premium = sell_put_premium
        self.buy_put_premium = buy_put_premium
        self.sell_call_premium = sell_call_premium
        self.buy_call_premium = buy_call_premium
        self.quantity = quantity
        self.strategy_name = "Iron_Condor"
        
        # Net premium (credit received)
        self.net_premium = (sell_put_premium - buy_put_premium + 
                           sell_call_premium - buy_call_premium)
    
    def calculate_payoff(self, spot_prices):
        """Calculate P&L at different spot prices"""
        payoffs = []
        
        for spot in spot_prices:
            # Put spread P&L
            if spot < self.buy_put_strike:
                # Max loss on put side
                put_pnl = -(self.sell_put_strike - self.buy_put_strike)
            elif spot < self.sell_put_strike:
                put_pnl = -(self.sell_put_strike - spot)
            else:
                put_pnl = 0
            
            # Call spread P&L
            if spot > self.buy_call_strike:
                # Max loss on call side
                call_pnl = -(self.buy_call_strike - self.sell_call_strike)
            elif spot > self.sell_call_strike:
                call_pnl = -(spot - self.sell_call_strike)
            else:
                call_pnl = 0
            
            # Net premium received
            total_pnl = (put_pnl + call_pnl + self.net_premium) * self.quantity
            payoffs.append({'spot': spot, 'pnl': total_pnl})
        
        return pd.DataFrame(payoffs)
    
    def calculate_breakeven(self):
        """Two breakeven points"""
        lower_be = self.sell_put_strike - self.net_premium
        upper_be = self.sell_call_strike + self.net_premium
        return (round(lower_be, 2), round(upper_be, 2))
    
    def calculate_max_profit(self):
        """Net premium received"""
        return self.net_premium * self.quantity
    
    def calculate_max_loss(self):
        """Width of wider spread - Net premium"""
        put_spread_width = self.sell_put_strike - self.buy_put_strike
        call_spread_width = self.buy_call_strike - self.sell_call_strike
        max_spread = max(put_spread_width, call_spread_width)
        return (max_spread - self.net_premium) * self.quantity
    
    def get_strategy_summary(self):
        """Return strategy details"""
        be_lower, be_upper = self.calculate_breakeven()
        return {
            'strategy': self.strategy_name,
            'spot_price': self.spot_price,
            'profit_range': f"{self.sell_put_strike} - {self.sell_call_strike}",
            'breakeven_lower': be_lower,
            'breakeven_upper': be_upper,
            'net_premium': round(self.net_premium, 2),
            'max_profit': round(self.calculate_max_profit(), 2),
            'max_loss': round(self.calculate_max_loss(), 2),
            'risk_reward_ratio': round(self.calculate_max_profit() / self.calculate_max_loss(), 2)
        }

# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("  IRON CONDOR STRATEGY")
    print("=" * 80)
    
    # Example: Nifty at 18000
    # Sell 17900 Put @ 20, Buy 17800 Put @ 10
    # Sell 18100 Call @ 20, Buy 18200 Call @ 10
    # Net Premium = 20 - 10 + 20 - 10 = 20
    
    strategy = IronCondorStrategy(
        spot_price=18000,
        sell_put_strike=17900,
        buy_put_strike=17800,
        sell_call_strike=18100,
        buy_call_strike=18200,
        sell_put_premium=20,
        buy_put_premium=10,
        sell_call_premium=20,
        buy_call_premium=10,
        quantity=50  # Lot size
    )
    
    summary = strategy.get_strategy_summary()
    print("\nStrategy Setup:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Calculate payoff
    spot_range = np.arange(17700, 18300, 50)
    payoff_df = strategy.calculate_payoff(spot_range)
    
    print("\n\nPayoff Analysis:")
    print(payoff_df.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("  IRON CONDOR READY FOR DEPLOYMENT")
    print("=" * 80)
