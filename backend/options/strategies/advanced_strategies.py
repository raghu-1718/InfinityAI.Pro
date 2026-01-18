"""
Bear Put Spread Strategy
Bearish strategy with limited risk and reward
"""
import pandas as pd
import numpy as np

class BearPutSpreadStrategy:
    """
    Bear Put Spread: Buy higher strike put + Sell lower strike put
    
    Use Case: Moderately bearish outlook
    Max Profit: (Higher Strike - Lower Strike) - Net Premium
    Max Loss: Net premium paid
    Breakeven: Higher Strike - Net Premium
    """
    
    def __init__(self, buy_strike, sell_strike, buy_premium, sell_premium, quantity=1):
        self.buy_strike = buy_strike
        self.sell_strike = sell_strike
        self.buy_premium = buy_premium
        self.sell_premium = sell_premium
        self.quantity = quantity
        self.strategy_name = "Bear_Put_Spread"
        
        # Net premium (debit paid)
        self.net_premium = buy_premium - sell_premium
    
    def calculate_payoff(self, spot_prices):
        """Calculate P&L at different spot prices"""
        payoffs = []
        
        for spot in spot_prices:
            # Long put payoff (higher strike)
            if spot < self.buy_strike:
                long_put_pnl = (self.buy_strike - spot) - self.buy_premium
            else:
                long_put_pnl = -self.buy_premium
            
            # Short put payoff (lower strike)
            if spot < self.sell_strike:
                short_put_pnl = -(self.sell_strike - spot) + self.sell_premium
            else:
                short_put_pnl = self.sell_premium
            
            total_pnl = (long_put_pnl + short_put_pnl) * self.quantity
            payoffs.append({'spot': spot, 'pnl': total_pnl})
        
        return pd.DataFrame(payoffs)
    
    def calculate_breakeven(self):
        """Higher strike - Net premium"""
        return self.buy_strike - self.net_premium
    
    def calculate_max_profit(self):
        """Spread width - Net premium"""
        return (self.buy_strike - self.sell_strike - self.net_premium) * self.quantity
    
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


class LongStraddleStrategy:
    """
    Long Straddle: Buy ATM Call + Buy ATM Put
    
    Use Case: Expect big move but unsure of direction (high volatility)
    Max Profit: Unlimited
    Max Loss: Total premium paid
    Breakeven: Strike ± Total Premium
    """
    
    def __init__(self, strike, call_premium, put_premium, quantity=1):
        self.strike = strike
        self.call_premium = call_premium
        self.put_premium = put_premium
        self.quantity = quantity
        self.total_premium = call_premium + put_premium
    
    def calculate_payoff(self, spot_prices):
        """Calculate P&L"""
        payoffs = []
        
        for spot in spot_prices:
            # Call payoff
            if spot > self.strike:
                call_pnl = (spot - self.strike) - self.call_premium
            else:
                call_pnl = -self.call_premium
            
            # Put payoff
            if spot < self.strike:
                put_pnl = (self.strike - spot) - self.put_premium
            else:
                put_pnl = -self.put_premium
            
            total_pnl = (call_pnl + put_pnl) * self.quantity
            payoffs.append({'spot': spot, 'pnl': total_pnl})
        
        return pd.DataFrame(payoffs)
    
    def get_strategy_summary(self):
        return {
            'strategy': 'Long_Straddle',
            'strike': self.strike,
            'total_premium': self.total_premium,
            'breakeven_upper': self.strike + self.total_premium,
            'breakeven_lower': self.strike - self.total_premium,
            'max_loss': self.total_premium * self.quantity,
            'max_profit': 'Unlimited'
        }


class LongStrangleStrategy:
    """
    Long Strangle: Buy OTM Call + Buy OTM Put
    
    Use Case: Expect big move, cheaper than straddle
    Max Profit: Unlimited
    Max Loss: Total premium paid
    """
    
    def __init__(self, call_strike, put_strike, call_premium, put_premium, quantity=1):
        self.call_strike = call_strike
        self.put_strike = put_strike
        self.call_premium = call_premium
        self.put_premium = put_premium
        self.quantity = quantity
        self.total_premium = call_premium + put_premium
    
    def calculate_payoff(self, spot_prices):
        """Calculate P&L"""
        payoffs = []
        
        for spot in spot_prices:
            # Call payoff
            if spot > self.call_strike:
                call_pnl = (spot - self.call_strike) - self.call_premium
            else:
                call_pnl = -self.call_premium
            
            # Put payoff
            if spot < self.put_strike:
                put_pnl = (self.put_strike - spot) - self.put_premium
            else:
                put_pnl = -self.put_premium
            
            total_pnl = (call_pnl + put_pnl) * self.quantity
            payoffs.append({'spot': spot, 'pnl': total_pnl})
        
        return pd.DataFrame(payoffs)
    
    def get_strategy_summary(self):
        return {
            'strategy': 'Long_Strangle',
            'call_strike': self.call_strike,
            'put_strike': self.put_strike,
            'total_premium': self.total_premium,
            'breakeven_upper': self.call_strike + self.total_premium,
            'breakeven_lower': self.put_strike - self.total_premium,
            'max_loss': self.total_premium * self.quantity
        }


class ButterflySpreadStrategy:
    """
    Butterfly Spread: Buy 1 ITM + Sell 2 ATM + Buy 1 OTM
    
    Use Case: Expect stock to stay near ATM strike
    Max Profit: At ATM strike
    Max Loss: Limited to net premium
    """
    
    def __init__(self, lower_strike, middle_strike, upper_strike, 
                 lower_premium, middle_premium, upper_premium, quantity=1):
        self.lower_strike = lower_strike
        self.middle_strike = middle_strike
        self.upper_strike = upper_strike
        self.lower_premium = lower_premium
        self.middle_premium = middle_premium
        self.upper_premium = upper_premium
        self.quantity = quantity
        
        # Net premium
        self.net_premium = lower_premium - (2 * middle_premium) + upper_premium
    
    def calculate_payoff(self, spot_prices):
        """Calculate P&L"""
        payoffs = []
        
        for spot in spot_prices:
            # Lower call (buy 1)
            lower_pnl = max(spot - self.lower_strike, 0) - self.lower_premium
            
            # Middle calls (sell 2)
            middle_pnl = -2 * (max(spot - self.middle_strike, 0) - self.middle_premium)
            
            # Upper call (buy 1)
            upper_pnl = max(spot - self.upper_strike, 0) - self.upper_premium
            
            total_pnl = (lower_pnl + middle_pnl + upper_pnl) * self.quantity
            payoffs.append({'spot': spot, 'pnl': total_pnl})
        
        return pd.DataFrame(payoffs)
    
    def get_strategy_summary(self):
        max_profit = (self.middle_strike - self.lower_strike - self.net_premium) * self.quantity
        return {
            'strategy': 'Butterfly_Spread',
            'strikes': f"{self.lower_strike}/{self.middle_strike}/{self.upper_strike}",
            'net_premium': round(self.net_premium, 2),
            'max_profit': round(max_profit, 2),
            'max_profit_at': self.middle_strike,
            'max_loss': abs(self.net_premium) * self.quantity
        }


# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("  ADDITIONAL OPTIONS STRATEGIES")
    print("=" * 80)
    
    # Bear Put Spread
    print("\n1. BEAR PUT SPREAD (Bearish)")
    bear_put = BearPutSpreadStrategy(
        buy_strike=3500,
        sell_strike=3400,
        buy_premium=80,
        sell_premium=40,
        quantity=100
    )
    print(bear_put.get_strategy_summary())
    
    # Long Straddle
    print("\n2. LONG STRADDLE (High Volatility)")
    straddle = LongStraddleStrategy(
        strike=18000,
        call_premium=100,
        put_premium=100,
        quantity=50
    )
    print(straddle.get_strategy_summary())
    
    # Long Strangle
    print("\n3. LONG STRANGLE (Big Move Expected)")
    strangle = LongStrangleStrategy(
        call_strike=18200,
        put_strike=17800,
        call_premium=50,
        put_premium=50,
        quantity=50
    )
    print(strangle.get_strategy_summary())
    
    # Butterfly
    print("\n4. BUTTERFLY SPREAD (Neutral)")
    butterfly = ButterflySpreadStrategy(
        lower_strike=17900,
        middle_strike=18000,
        upper_strike=18100,
        lower_premium=120,
        middle_premium=80,
        upper_premium=50,
        quantity=50
    )
    print(butterfly.get_strategy_summary())
    
    print("\n" + "=" * 80)
    print("  ALL STRATEGIES READY")
    print("=" * 80)
