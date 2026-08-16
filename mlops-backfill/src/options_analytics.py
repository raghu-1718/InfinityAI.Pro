"""
Options Analytics Module for Engine C
Implements Greeks calculation using Black-Scholes model
Integrated with Google Cloud Firestore for data persistence
"""
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class GreeksCalculator:
    """
    Calculate option Greeks using Black-Scholes model
    """
    
    def __init__(self, db_client: Optional[Any] = None):
        self.db = db_client
    
    def calculate_d1_d2(self, S: float, K: float, T: float, r: float, sigma: float):
        """
        Calculate d1 and d2 for Black-Scholes formula
        
        Args:
            S: Spot price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility (annualized)
        """
        if T <= 0:
            return 0, 0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return d1, d2
    
    def calculate_call_price(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Black-Scholes Call Option Price"""
        d1, d2 = self.calculate_d1_d2(S, K, T, r, sigma)
        call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return call_price
    
    def calculate_put_price(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Black-Scholes Put Option Price"""
        d1, d2 = self.calculate_d1_d2(S, K, T, r, sigma)
        put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return put_price
    
    def calculate_delta(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
        """
        Delta: Rate of change of option price with respect to underlying price
        Call: 0 to 1, Put: -1 to 0
        """
        d1, _ = self.calculate_d1_d2(S, K, T, r, sigma)
        
        if option_type.lower() == 'call':
            delta = norm.cdf(d1)
        else:  # put
            delta = norm.cdf(d1) - 1
        
        return delta
    
    def calculate_gamma(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Gamma: Rate of change of delta with respect to underlying price
        Same for both calls and puts
        """
        if T <= 0 or sigma <= 0:
            return 0
        
        d1, _ = self.calculate_d1_d2(S, K, T, r, sigma)
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        return gamma
    
    def calculate_theta(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
        """
        Theta: Rate of change of option price with respect to time (time decay)
        Usually negative (options lose value as expiration approaches)
        """
        if T <= 0:
            return 0
        
        d1, d2 = self.calculate_d1_d2(S, K, T, r, sigma)
        
        if option_type.lower() == 'call':
            theta = (- (S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) 
                    - r * K * np.exp(-r * T) * norm.cdf(d2))
        else:  # put
            theta = (- (S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) 
                    + r * K * np.exp(-r * T) * norm.cdf(-d2))
        
        # Convert to per-day theta (divide by 365)
        theta_per_day = theta / 365
        return theta_per_day
    
    def calculate_vega(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Vega: Rate of change of option price with respect to volatility
        Same for both calls and puts
        """
        if T <= 0:
            return 0
        
        d1, _ = self.calculate_d1_d2(S, K, T, r, sigma)
        vega = S * norm.pdf(d1) * np.sqrt(T)
        
        # Vega per 1% change in volatility
        vega_pct = vega / 100
        return vega_pct
    
    def calculate_rho(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
        """
        Rho: Rate of change of option price with respect to interest rate
        """
        if T <= 0:
            return 0
        
        _, d2 = self.calculate_d1_d2(S, K, T, r, sigma)
        
        if option_type.lower() == 'call':
            rho = K * T * np.exp(-r * T) * norm.cdf(d2)
        else:  # put
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)
        
        # Rho per 1% change in interest rate
        rho_pct = rho / 100
        return rho_pct
    
    def calculate_all_greeks(self, S: float, K: float, T: float, r: float, sigma: float, 
                            option_type: str = 'call') -> Dict[str, float]:
        """
        Calculate all Greeks at once
        
        Args:
            S: Spot price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate (e.g., 0.05 for 5%)
            sigma: Implied volatility (e.g., 0.20 for 20%)
            option_type: 'call' or 'put'
        
        Returns:
            Dictionary with all Greeks and theoretical price
        """
        try:
            # Theoretical Price
            if option_type.lower() == 'call':
                theo_price = self.calculate_call_price(S, K, T, r, sigma)
            else:
                theo_price = self.calculate_put_price(S, K, T, r, sigma)
            
            # Calculate all Greeks
            delta = self.calculate_delta(S, K, T, r, sigma, option_type)
            gamma = self.calculate_gamma(S, K, T, r, sigma)
            theta = self.calculate_theta(S, K, T, r, sigma, option_type)
            vega = self.calculate_vega(S, K, T, r, sigma)
            rho = self.calculate_rho(S, K, T, r, sigma, option_type)
            
            return {
                'theoretical_price': round(theo_price, 2),
                'delta': round(delta, 4),
                'gamma': round(gamma, 6),
                'theta': round(theta, 4),
                'vega': round(vega, 4),
                'rho': round(rho, 4),
                'spot_price': S,
                'strike_price': K,
                'time_to_expiry_years': T,
                'risk_free_rate': r,
                'implied_volatility': sigma,
                'option_type': option_type,
                'calculated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating Greeks: {e}")
            return {}
    
    def calculate_portfolio_greeks(self, positions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate aggregated portfolio Greeks
        
        Args:
            positions: List of position dicts with:
                - qty: position quantity (positive for long, negative for short)
                - spot_price, strike_price, time_to_expiry, iv, option_type
        """
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        total_rho = 0
        
        for pos in positions:
            qty = pos.get('qty', 1)
            
            greeks = self.calculate_all_greeks(
                S=pos['spot_price'],
                K=pos['strike_price'],
                T=pos['time_to_expiry'],
                r=pos.get('risk_free_rate', 0.05),
                sigma=pos['implied_volatility'],
                option_type=pos['option_type']
            )
            
            # Aggregate (multiply by quantity)
            total_delta += greeks['delta'] * qty
            total_gamma += greeks['gamma'] * qty
            total_theta += greeks['theta'] * qty
            total_vega += greeks['vega'] * qty
            total_rho += greeks['rho'] * qty
        
        return {
            'portfolio_delta': round(total_delta, 4),
            'portfolio_gamma': round(total_gamma, 6),
            'portfolio_theta': round(total_theta, 4),
            'portfolio_vega': round(total_vega, 4),
            'portfolio_rho': round(total_rho, 4),
            'num_positions': len(positions),
            'calculated_at': datetime.utcnow().isoformat()
        }
    
    async def store_greeks(self, user_id: str, position_id: str, greeks: Dict[str, Any]):
        """Store calculated Greeks in Google Cloud Firestore"""
        try:
            from src.user_credentials import get_credentials_manager
            manager = get_credentials_manager()
            if not manager or not manager.db:
                return

            doc_id = f"{user_id}_{position_id}"
            manager.db.collection("options_greeks").document(doc_id).set({
                "user_id": user_id,
                "position_id": position_id,
                "greeks": greeks,
                "updated_at": datetime.utcnow().isoformat()
            }, merge=True)
            logger.info(f"✅ Stored Greeks for user {user_id}, position {position_id}")
        except Exception as e:
            logger.error(f"Error storing Greeks in Firestore: {e}")

    async def get_greeks(self, user_id: str, position_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored Greeks from Google Cloud Firestore"""
        try:
            from src.user_credentials import get_credentials_manager
            manager = get_credentials_manager()
            if not manager or not manager.db:
                return None

            doc_id = f"{user_id}_{position_id}"
            doc = manager.db.collection("options_greeks").document(doc_id).get()
            if doc.exists:
                data = doc.to_dict()
                return data.get("greeks")
            return None
        except Exception as e:
            logger.error(f"Error retrieving Greeks from Firestore: {e}")
            return None


# Singleton instance
_greeks_calculator: Optional[GreeksCalculator] = None

def get_greeks_calculator(db_client: Optional[Any] = None) -> GreeksCalculator:
    """Get singleton instance of GreeksCalculator"""
    global _greeks_calculator
    if _greeks_calculator is None:
        _greeks_calculator = GreeksCalculator(db_client)
    return _greeks_calculator


# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("  GREEKS CALCULATOR - BLACK-SCHOLES MODEL")
    print("=" * 80)
    
    calc = GreeksCalculator()
    
    # Example: NIFTY 18000 Call, spot at 18100, 15 days to expiry
    greeks = calc.calculate_all_greeks(
        S=18100,           # Spot price
        K=18000,           # Strike price
        T=15/365,          # 15 days to expiry
        r=0.05,            # 5% risk-free rate
        sigma=0.15,        # 15% IV
        option_type='call'
    )
    
    print("\nCall Option Greeks:")
    print(f"  Theoretical Price: Rs. {greeks['theoretical_price']}")
    print(f"  Delta: {greeks['delta']} (moves {greeks['delta']:.2%} for 1 point move in spot)")
    print(f"  Gamma: {greeks['gamma']} (delta changes by this amount)")
    print(f"  Theta: {greeks['theta']} (loses Rs. {abs(greeks['theta']):.2f} per day)")
    print(f"  Vega: {greeks['vega']} (gains Rs. {greeks['vega']:.2f} for 1% IV increase)")
    print(f"  Rho: {greeks['rho']}")
    
    # Portfolio example
    print("\n\nPortfolio Greeks (Iron Condor):")
    positions = [
        {'qty': 50, 'spot_price': 18000, 'strike_price': 17900, 'time_to_expiry': 15/365, 'implied_volatility': 0.15, 'option_type': 'put'},   # Sell Put
        {'qty': -50, 'spot_price': 18000, 'strike_price': 17800, 'time_to_expiry': 15/365, 'implied_volatility': 0.16, 'option_type': 'put'},  # Buy Put
        {'qty': 50, 'spot_price': 18000, 'strike_price': 18100, 'time_to_expiry': 15/365, 'implied_volatility': 0.15, 'option_type': 'call'},  # Sell Call
        {'qty': -50, 'spot_price': 18000, 'strike_price': 18200, 'time_to_expiry': 15/365, 'implied_volatility': 0.16, 'option_type': 'call'}, # Buy Call
    ]
    
    portfolio_greeks = calc.calculate_portfolio_greeks(positions)
    print(f"  Portfolio Delta: {portfolio_greeks['portfolio_delta']}")
    print(f"  Portfolio Gamma: {portfolio_greeks['portfolio_gamma']}")
    print(f"  Portfolio Theta: {portfolio_greeks['portfolio_theta']}")
    print(f"  Portfolio Vega: {portfolio_greeks['portfolio_vega']}")
    
    print("\n" + "=" * 80)
    print("  GREEKS CALCULATOR READY FOR PRODUCTION")
    print("=" * 80)
