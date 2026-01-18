"""
Calendar Spread Strategy
Buy far-month option, Sell near-month option
Profits from time decay differential
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class CalendarSpreadStrategy:
    """
    Calendar Spread (Time Spread): Buy long-dated + Sell short-dated
    
    Use Case: Expect minimal price movement, profit from theta decay
    Max Profit: At strike at near expiration
    Max Loss: Net premium paid
    Best: Low volatility + time passing
    """
    
    def __init__(self, strike, near_premium, far_premium, quantity=1):
        self.strike = strike
        self.near_premium = near_premium  # Premium received (sold)
        self.far_premium = far_premium    # Premium paid (bought)
        self.quantity = quantity
        self.net_premium = far_premium - near_premium  # Debit
        
    def calculate_payoff(self, spot_prices, far_value_at_near_expiry):
        """
        Calendar spread payoff at near expiration
        far_value_at_near_expiry: value of far-month option when near expires
        """
        payoffs = []
        
        for i, spot in enumerate(spot_prices):
            # Near option expires (we sold this)
            if spot < self.strike:
                near_pnl = self.near_premium  # Expired worthless, keep premium
            else:
                near_pnl = self.near_premium - (spot - self.strike)
            
            # Far option still has value (we own this)
            far_pnl = far_value_at_near_expiry[i] - self.far_premium
            
            total_pnl = (near_pnl + far_pnl) * self.quantity
            payoffs.append({'spot': spot, 'pnl': total_pnl})
        
        return pd.DataFrame(payoffs)
    
    def get_strategy_summary(self):
        return {
            'strategy': 'Calendar_Spread',
            'strike': self.strike,
            'net_cost': round(self.net_premium, 2),
            'max_loss': round(self.net_premium * self.quantity, 2),
            'max_profit': 'Variable (depends on far option value)',
            'best_scenario': 'Stock at strike at near expiration'
        }


class ProtectiveCollarStrategy:
    """
    Protective Collar: Own stock + Buy put + Sell call
    
    Use Case: Downside protection with capped upside
    Max Loss: Stock price - Put strike - Net credit/debit
    Max Gain: Call strike - Stock price + Net credit/debit
    """
    
    def __init__(self, stock_price, put_strike, call_strike, 
                 put_premium, call_premium, shares=100):
        self.stock_price = stock_price
        self.put_strike = put_strike
        self.call_strike = call_strike
        self.put_premium = put_premium  # Premium paid
        self.call_premium = call_premium  # Premium received
        self.shares = shares
        self.net_cost = put_premium - call_premium
        
    def calculate_payoff(self, spot_prices):
        """Calculate P&L at expiration"""
        payoffs = []
        
        for spot in spot_prices:
            # Stock P&L
            stock_pnl = (spot - self.stock_price) * self.shares
            
            # Put P&L (protection)
            if spot < self.put_strike:
                put_pnl = (self.put_strike - spot) - self.put_premium
            else:
                put_pnl = -self.put_premium
            
            # Call P&L (capped upside)
            if spot > self.call_strike:
                call_pnl = -(spot - self.call_strike) + self.call_premium
            else:
                call_pnl = self.call_premium
            
            total_pnl = stock_pnl + (put_pnl + call_pnl) * self.shares
            payoffs.append({'spot': spot, 'pnl': total_pnl})
        
        return pd.DataFrame(payoffs)
    
    def get_strategy_summary(self):
        max_loss = (self.stock_price - self.put_strike - self.net_cost) * self.shares
        max_gain = (self.call_strike - self.stock_price + self.net_cost) * self.shares
        
        return {
            'strategy': 'Protective_Collar',
            'stock_price': self.stock_price,
            'put_strike': self.put_strike,
            'call_strike': self.call_strike,
            'net_cost': round(self.net_cost, 2),
            'max_loss': round(max_loss, 2),
            'max_gain': round(max_gain, 2),
            'protection_level': f"{self.put_strike} ({((self.stock_price - self.put_strike)/self.stock_price * 100):.1f}% below)"
        }


class RatioSpreadStrategy:
    """
    Ratio Spread: Buy 1 option, Sell 2+ options at different strike
    
    Use Case: Neutral to slightly bullish/bearish
    Risk: Unlimited on one side
    """
    
    def __init__(self, buy_strike, sell_strike, buy_qty, sell_qty,
                 buy_premium, sell_premium):
        self.buy_strike = buy_strike
        self.sell_strike = sell_strike
        self.buy_qty = buy_qty
        self.sell_qty = sell_qty
        self.buy_premium = buy_premium
        self.sell_premium = sell_premium
        self.net_premium = (buy_premium * buy_qty) - (sell_premium * sell_qty)
        
    def calculate_payoff(self, spot_prices, option_type='call'):
        """Calculate P&L"""
        payoffs = []
        
        for spot in spot_prices:
            if option_type == 'call':
                # Buy calls
                buy_pnl = max(spot - self.buy_strike, 0) - self.buy_premium
                # Sell calls
                sell_pnl = -(max(spot - self.sell_strike, 0) - self.sell_premium)
            else:  # put
                buy_pnl = max(self.buy_strike - spot, 0) - self.buy_premium
                sell_pnl = -(max(self.sell_strike - spot, 0) - self.sell_premium)
            
            total_pnl = (buy_pnl * self.buy_qty + sell_pnl * self.sell_qty)
            payoffs.append({'spot': spot, 'pnl': total_pnl})
        
        return pd.DataFrame(payoffs)
    
    def get_strategy_summary(self):
        return {
            'strategy': 'Ratio_Spread',
            'buy': f"{self.buy_qty} @ {self.buy_strike}",
            'sell': f"{self.sell_qty} @ {self.sell_strike}",
            'ratio': f"1:{self.sell_qty / self.buy_qty}",
            'net_cost': round(self.net_premium, 2),
            'risk': 'Unlimited above/below sell strike'
        }


# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("  ADVANCED OPTION STRATEGIES")
    print("=" * 80)
    
    # Calendar Spread
    print("\n1. CALENDAR SPREAD")
    cal = CalendarSpreadStrategy(
        strike=18000,
        near_premium=50,   # Sell Jan expiry
        far_premium=100,   # Buy Feb expiry
        quantity=50
    )
    print(cal.get_strategy_summary())
    
    # Protective Collar
    print("\n2. PROTECTIVE COLLAR")
    collar = ProtectiveCollarStrategy(
        stock_price=1450,
        put_strike=1400,   # Protection
        call_strike=1500,  # Cap upside
        put_premium=20,
        call_premium=15,
        shares=100
    )
    print(collar.get_strategy_summary())
    
    # Ratio Spread
    print("\n3. RATIO SPREAD (1:2)")
    ratio = RatioSpreadStrategy(
        buy_strike=18000,
        sell_strike=18200,
        buy_qty=1,
        sell_qty=2,
        buy_premium=100,
        sell_premium=50
    )
    print(ratio.get_strategy_summary())
    
    print("\n" + "=" * 80)
    print("  ALL ADVANCED STRATEGIES READY")
    print("=" * 80)
