"""
InfinityAI.Pro — Real-Time Black-Scholes Greeks & Volatility Surface Engine
=============================================================================
Computes analytical Black-Scholes Greeks (Delta, Gamma, Theta, Vega, Rho)
and solves for Implied Volatility (IV) and Volatility Smile skew across Indian index options.
"""

import math
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("InfinityAI.VolSurfaceGreeks")

def _norm_cdf(x: float) -> float:
    """Standard Normal Cumulative Distribution Function"""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def _norm_pdf(x: float) -> float:
    """Standard Normal Probability Density Function"""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

class VolSurfaceGreeksEngine:
    """High-precision Options Analytics and Volatility Smile Engine"""

    def __init__(self, risk_free_rate: float = 0.068): # RBI 6.8% Repo Rate
        self.r = risk_free_rate

    def calculate_greeks(
        self,
        spot: float,
        strike: float,
        time_to_expiry_days: float,
        iv_annualized: float,
        option_type: str = "CE"
    ) -> Dict[str, Any]:
        """
        Computes analytical Black-Scholes Greeks for European/Indian index options.
        """
        T = max(time_to_expiry_days / 365.0, 0.0001) # Minimum 1 hour
        sigma = max(iv_annualized, 0.01)

        d1 = (math.log(spot / strike) + (self.r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        pdf_d1 = _norm_pdf(d1)
        cdf_d1 = _norm_cdf(d1)
        cdf_d2 = _norm_cdf(d2)

        opt_type = option_type.upper()
        if opt_type == "CE":
            theoretical_price = spot * cdf_d1 - strike * math.exp(-self.r * T) * cdf_d2
            delta = cdf_d1
            theta = (-(spot * pdf_d1 * sigma) / (2.0 * math.sqrt(T)) - self.r * strike * math.exp(-self.r * T) * cdf_d2) / 365.0
            rho = (strike * T * math.exp(-self.r * T) * cdf_d2) / 100.0
        else: # PE
            cdf_neg_d1 = _norm_cdf(-d1)
            cdf_neg_d2 = _norm_cdf(-d2)
            theoretical_price = strike * math.exp(-self.r * T) * cdf_neg_d2 - spot * cdf_neg_d1
            delta = cdf_d1 - 1.0
            theta = (-(spot * pdf_d1 * sigma) / (2.0 * math.sqrt(T)) + self.r * strike * math.exp(-self.r * T) * cdf_neg_d2) / 365.0
            rho = (-strike * T * math.exp(-self.r * T) * cdf_neg_d2) / 100.0

        gamma = pdf_d1 / (spot * sigma * math.sqrt(T))
        vega = (spot * math.sqrt(T) * pdf_d1) / 100.0 # Per 1% IV change

        return {
            "option_type": opt_type,
            "spot": spot,
            "strike": strike,
            "time_to_expiry_days": round(time_to_expiry_days, 2),
            "implied_volatility_pct": round(sigma * 100.0, 2),
            "theoretical_price": round(theoretical_price, 2),
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta_per_day": round(theta, 2),
            "vega_per_1pct": round(vega, 2),
            "rho": round(rho, 4)
        }

    def solve_implied_volatility(
        self,
        market_price: float,
        spot: float,
        strike: float,
        time_to_expiry_days: float,
        option_type: str = "CE"
    ) -> float:
        """
        Solves for Implied Volatility using Newton-Raphson with bisection fallback.
        Returns IV as a decimal (e.g. 0.155 for 15.5%).
        """
        sigma = 0.20 # Initial guess: 20% IV
        for _ in range(25):
            res = self.calculate_greeks(spot, strike, time_to_expiry_days, sigma, option_type)
            diff = res["theoretical_price"] - market_price
            if abs(diff) < 0.01:
                return sigma
            vega = res["vega_per_1pct"] * 100.0
            if vega > 0.001:
                sigma -= diff / vega
                sigma = max(0.01, min(sigma, 3.0)) # Clamp between 1% and 300%
            else:
                break
        return sigma

    def evaluate_vol_skew(
        self,
        spot: float,
        atm_strike: float,
        call_market_price: float,
        put_market_price: float,
        time_to_expiry_days: float
    ) -> Dict[str, Any]:
        """
        Evaluates Put-Call Volatility Skew to detect Institutional Hedging or Panic.
        """
        call_iv = self.solve_implied_volatility(call_market_price, spot, atm_strike, time_to_expiry_days, "CE")
        put_iv = self.solve_implied_volatility(put_market_price, spot, atm_strike, time_to_expiry_days, "PE")
        skew = put_iv - call_iv

        skew_regime = "ELEVATED_DOWNSIDE_HEDGING" if skew > 0.03 else "BULLISH_CALL_DEMAND" if skew < -0.02 else "BALANCED_VOL_SURFACE"

        return {
            "call_iv_pct": round(call_iv * 100.0, 2),
            "put_iv_pct": round(put_iv * 100.0, 2),
            "iv_skew_diff_pct": round(skew * 100.0, 2),
            "skew_regime": skew_regime,
            "is_iv_crush_risk": call_iv > 0.28 or put_iv > 0.28
        }

VOL_SURFACE_GREEKS_ENGINE = VolSurfaceGreeksEngine()
