"""
IV Surface Calculator
Calculate implied volatility surface from option prices
"""
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class IVSurfaceCalculator:
    """Calculate and manage implied volatility surface"""
    
    def __init__(self, risk_free_rate=0.05):
        self.risk_free_rate = risk_free_rate
    
    def black_scholes_price(self, S, K, T, r, sigma, option_type='call'):
        """Black-Scholes option pricing"""
        if T <= 0 or sigma <= 0:
            return 0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type == 'call':
            return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    def calculate_iv(self, market_price, S, K, T, r, option_type='call'):
        """
        Calculate implied volatility using Brent's method
        
        Returns IV as decimal (e.g., 0.20 for 20%)
        """
        try:
            if T <= 0 or market_price <= 0:
                return None
            
            # Define objective function
            def objective(sigma):
                return self.black_scholes_price(S, K, T, r, sigma, option_type) - market_price
            
            # IV bounds: 1% to 500%
            iv = brentq(objective, 0.01, 5.0, xtol=1e-6)
            return iv
        
        except Exception as e:
            logger.warning(f"IV calculation failed for K={K}: {e}")
            return None
    
    def calculate_iv_surface(self, option_chain: List[Dict[str, Any]], 
                            spot_price: float) -> Dict[str, Any]:
        """
        Calculate IV surface from option chain
        
        Args:
            option_chain: List of options with strike, expiry, price, type
            spot_price: Current spot price
        
        Returns:
            IV surface data (strikes × expiries × IV matrix)
        """
        try:
            # Group by expiry
            expiries = {}
            for option in option_chain:
                expiry = option.get('expiry')
                if expiry not in expiries:
                    expiries[expiry] = []
                expiries[expiry].append(option)
            
            # Calculate IV for each option
            surface_data = []
            
            for expiry, options in sorted(expiries.items()):
                expiry_date = pd.to_datetime(expiry)
                T = (expiry_date - datetime.now()).days / 365
                
                for opt in options:
                    strike = opt.get('strike')
                    price = opt.get('ltp')
                    opt_type = opt.get('type', 'call')
                    
                    if price and price > 0:
                        iv = self.calculate_iv(price, spot_price, strike, T, 
                                              self.risk_free_rate, opt_type)
                        
                        if iv:
                            surface_data.append({
                                'expiry': expiry,
                                'strike': strike,
                                'type': opt_type,
                                'price': price,
                                'iv': iv,
                                'moneyness': strike / spot_price,
                                'dte': T * 365
                            })
            
            # Build surface matrix
            strikes = sorted(set([d['strike'] for d in surface_data]))
            expiries_list = sorted(set([d['expiry'] for d in surface_data]))
            
            # Create IV matrix (strikes × expiries)
            iv_matrix = []
            for strike in strikes:
                iv_row = []
                for expiry in expiries_list:
                    # Find IV for this strike/expiry combo
                    iv_val = next((d['iv'] for d in surface_data 
                                  if d['strike'] == strike and d['expiry'] == expiry), None)
                    iv_row.append(iv_val)
                iv_matrix.append(iv_row)
            
            return {
                'strikes': strikes,
                'expiries': expiries_list,
                'iv_matrix': iv_matrix,
                'raw_data': surface_data,
                'spot_price': spot_price,
                'calculated_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"IV surface calculation error: {e}")
            return {}
    
    def get_iv_smile(self, expiry: str, surface_data: Dict) -> List[Dict]:
        """Extract IV smile for specific expiry"""
        try:
            expiry_idx = surface_data['expiries'].index(expiry)
            
            smile = []
            for i, strike in enumerate(surface_data['strikes']):
                iv = surface_data['iv_matrix'][i][expiry_idx]
                if iv:
                    smile.append({
                        'strike': strike,
                        'iv': iv,
                        'moneyness': strike / surface_data['spot_price']
                    })
            
            return smile
        except Exception as e:
            logger.error(f"IV smile extraction error: {e}")
            return []


# Demo
if __name__ == "__main__":
    import pandas as pd
    from datetime import datetime
    
    print("=" * 80)
    print("  IV SURFACE CALCULATOR")
    print("=" * 80)
    
    calc = IVSurfaceCalculator()
    
    # Test IV calculation
    print("\n[TEST] Single IV Calculation")
    market_price = 100
    iv = calc.calculate_iv(market_price, S=18000, K=18100, T=15/365, r=0.05, option_type='call')
    print(f"Market Price: Rs. {market_price}")
    print(f"Implied Volatility: {iv:.4f} ({iv*100:.2f}%)")
    
    print("\n[INFO] IV Surface Features:")
    print("  - Newton-Raphson method (via Brent)")
    print("  - Handles multiple expiries")
    print("  - Generates 3D surface data")
    print("  - IV smile extraction")
    
    print("\n" + "=" * 80)
    print("  IV SURFACE CALCULATOR READY")
    print("=" * 80)
