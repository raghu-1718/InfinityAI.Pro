"""
Options Greeks Calculator using Black-Scholes Model
Calculates Delta, Gamma, Theta, Vega, Rho for European options
"""

import numpy as np
from scipy.stats import norm
from typing import Dict, Optional
from datetime import datetime, timedelta
from enum import Enum


class OptionType(Enum):
    """Option type enumeration"""
    CALL = "CE"
    PUT = "PE"


class BlackScholesGreeks:
    """
    Black-Scholes Greeks Calculator for Options Risk Management.

    Greeks explained:
    - Delta: Rate of change of option price with underlying price (hedging ratio)
    - Gamma: Rate of change of Delta (curvature of option price)
    - Theta: Time decay (price erosion per day)
    - Vega: Sensitivity to volatility (price change per 1% vol change)
    - Rho: Sensitivity to interest rates (price change per 1% rate change)
    """

    @staticmethod
    def calculate_greeks(
        spot: float,
        strike: float,
        time_to_expiry: float,  # Years
        volatility: float,  # Annualized (e.g., 0.20 for 20%)
        risk_free_rate: float = 0.06,  # 6% RBI repo rate
        option_type: str = "CE"  # CE (Call) or PE (Put)
    ) -> Dict[str, float]:
        """
        Calculate all Greeks for a single option using Black-Scholes model.

        Args:
            spot: Current price of underlying
            strike: Strike price of option
            time_to_expiry: Time to expiry in years
            volatility: Annualized volatility (e.g., 0.18 for 18%)
            risk_free_rate: Risk-free interest rate (default 6%)
            option_type: "CE" for Call or "PE" for Put

        Returns:
            Dictionary with Greeks: delta, gamma, theta, vega, rho
        """
        if time_to_expiry <= 0:
            return {
                "delta": 1.0 if option_type == "CE" and spot > strike else 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "rho": 0.0
            }

        # d1 and d2 from Black-Scholes formula
        d1 = (
            np.log(spot / strike) +
            (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry
        ) / (volatility * np.sqrt(time_to_expiry))

        d2 = d1 - volatility * np.sqrt(time_to_expiry)

        # Delta
        if option_type == "CE":
            delta = norm.cdf(d1)
        else:  # PE
            delta = norm.cdf(d1) - 1

        # Gamma (same for Call and Put)
        gamma = norm.pdf(d1) / (spot * volatility * np.sqrt(time_to_expiry))

        # Theta (daily)
        if option_type == "CE":
            theta = (
                -(spot * norm.pdf(d1) * volatility) / (2 * np.sqrt(time_to_expiry)) -
                risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
            ) / 365  # Convert to daily theta
        else:  # PE
            theta = (
                -(spot * norm.pdf(d1) * volatility) / (2 * np.sqrt(time_to_expiry)) +
                risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2)
            ) / 365

        # Vega (per 1% change in volatility)
        vega = spot * norm.pdf(d1) * np.sqrt(time_to_expiry) / 100

        # Rho (per 1% change in interest rate)
        if option_type == "CE":
            rho = strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2) / 100
        else:  # PE
            rho = -strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) / 100

        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta, 4),
            "vega": round(vega, 4),
            "rho": round(rho, 4)
        }

    @staticmethod
    def calculate_option_price(
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float = 0.06,
        option_type: str = "CE"
    ) -> float:
        """Calculate theoretical option price using Black-Scholes"""
        if time_to_expiry <= 0:
            if option_type == "CE":
                return max(0, spot - strike)
            else:
                return max(0, strike - spot)

        d1 = (
            np.log(spot / strike) +
            (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry
        ) / (volatility * np.sqrt(time_to_expiry))

        d2 = d1 - volatility * np.sqrt(time_to_expiry)

        if option_type == "CE":
            price = spot * norm.cdf(d1) - strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
        else:
            price = strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - spot * norm.cdf(-d1)

        return round(price, 2)

    @staticmethod
    def calculate_portfolio_greeks(
        positions: list
    ) -> Dict[str, float]:
        """
        Calculate aggregate Greeks for options portfolio.

        Args:
            positions: List of options positions
                [{
                    "symbol": "NIFTY22JAN21500CE",
                    "quantity": 100,
                    "spot": 21000,
                    "strike": 21500,
                    "expiry": "2022-01-27",
                    "volatility": 0.18,
                    "option_type": "CE"
                }]

        Returns:
            Aggregate portfolio Greeks
        """
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        total_rho = 0

        for pos in positions:
            # Calculate time to expiry
            if isinstance(pos.get("expiry"), str):
                expiry = datetime.strptime(pos["expiry"], "%Y-%m-%d")
            else:
                expiry = pos["expiry"]

            time_to_expiry = max(0, (expiry - datetime.now()).days / 365)

            # Calculate Greeks
            greeks = BlackScholesGreeks.calculate_greeks(
                spot=pos["spot"],
                strike=pos["strike"],
                time_to_expiry=time_to_expiry,
                volatility=pos["volatility"],
                option_type=pos["option_type"]
            )

            # Aggregate (weighted by quantity)
            qty = pos.get("quantity", 0)
            total_delta += greeks["delta"] * qty
            total_gamma += greeks["gamma"] * qty
            total_theta += greeks["theta"] * qty
            total_vega += greeks["vega"] * qty
            total_rho += greeks["rho"] * qty

        return {
            "delta": round(total_delta, 2),
            "gamma": round(total_gamma, 4),
            "theta": round(total_theta, 2),
            "vega": round(total_vega, 2),
            "rho": round(total_rho, 2)
        }

    @staticmethod
    def calculate_implied_volatility(
        spot: float,
        strike: float,
        time_to_expiry: float,
        option_price: float,
        option_type: str = "CE",
        risk_free_rate: float = 0.06,
        max_iterations: int = 100,
        tolerance: float = 0.0001
    ) -> Optional[float]:
        """
        Calculate implied volatility using Newton-Raphson method.

        Args:
            spot: Current price of underlying
            strike: Strike price
            time_to_expiry: Time to expiry in years
            option_price: Market price of option
            option_type: "CE" or "PE"
            risk_free_rate: Risk-free rate
            max_iterations: Maximum iterations
            tolerance: Convergence tolerance

        Returns:
            Implied volatility (annualized) or None if not found
        """
        # Initial guess
        vol = 0.20  # 20%

        for i in range(max_iterations):
            # Calculate theoretical price
            theo_price = BlackScholesGreeks.calculate_option_price(
                spot, strike, time_to_expiry, vol, risk_free_rate, option_type
            )

            # Check convergence
            price_diff = theo_price - option_price
            if abs(price_diff) < tolerance:
                return round(vol, 4)

            # Calculate vega for Newton-Raphson
            greeks = BlackScholesGreeks.calculate_greeks(
                spot, strike, time_to_expiry, vol, risk_free_rate, option_type
            )
            vega = greeks["vega"] * 100  # Convert back to absolute vega

            if vega == 0:
                return None

            # Newton-Raphson update
            vol = vol - price_diff / vega

            # Bounds check
            if vol <= 0 or vol > 5:  # Volatility between 0% and 500%
                return None

        return None  # Did not converge

    @staticmethod
    def time_to_expiry_years(expiry_date: datetime) -> float:
        """Calculate time to expiry in years"""
        days = max(0, (expiry_date - datetime.now()).days)
        return days / 365.0


# Convenience function for quick calculations
def get_greeks(
    symbol: str,
    spot: float,
    strike: float,
    expiry: str,
    volatility: float = 0.18,
    option_type: str = "CE"
) -> Dict[str, float]:
    """
    Quick helper to get Greeks for an option.

    Example:
        >>> get_greeks("NIFTY22JAN21500CE", 21000, 21500, "2022-01-27", 0.18, "CE")
        {'delta': 0.4521, 'gamma': 0.000123, ...}
    """
    expiry_dt = datetime.strptime(expiry, "%Y-%m-%d")
    time_to_expiry = BlackScholesGreeks.time_to_expiry_years(expiry_dt)

    return BlackScholesGreeks.calculate_greeks(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        volatility=volatility,
        option_type=option_type
    )
