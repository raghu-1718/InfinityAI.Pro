"""
Black-Scholes Analytical Greeks PDE Engine
"""
import math
from typing import Dict, Any

def compute_bs_greeks(
    spot: float,
    strike: float,
    dte_days: float,
    iv: float = 0.145,
    option_type: str = "CE",
    r: float = 0.068
) -> Dict[str, float]:
    """
    Computes analytical Black-Scholes price and first/second order Greeks.
    """
    T = max(dte_days / 365.0, 0.0001)
    sigma = max(iv, 0.01)
    d1 = (math.log(spot / strike) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    pdf_d1 = (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * d1 * d1)
    cdf_d1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
    cdf_d2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))

    if option_type.upper() in ["CE", "CALL", "BUY_CALL"]:
        price = spot * cdf_d1 - strike * math.exp(-r * T) * cdf_d2
        delta = cdf_d1
        theta = (-(spot * pdf_d1 * sigma) / (2.0 * math.sqrt(T)) - r * strike * math.exp(-r * T) * cdf_d2) / 365.0
    else:
        cdf_neg_d1 = 0.5 * (1.0 + math.erf(-d1 / math.sqrt(2.0)))
        cdf_neg_d2 = 0.5 * (1.0 + math.erf(-d2 / math.sqrt(2.0)))
        price = strike * math.exp(-r * T) * cdf_neg_d2 - spot * cdf_neg_d1
        delta = cdf_d1 - 1.0
        theta = (-(spot * pdf_d1 * sigma) / (2.0 * math.sqrt(T)) + r * strike * math.exp(-r * T) * cdf_neg_d2) / 365.0

    gamma = pdf_d1 / (spot * sigma * math.sqrt(T))
    vega = (spot * math.sqrt(T) * pdf_d1) / 100.0

    return {
        "price": max(0.05, round(price, 2)),
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta, 2),
        "vega": round(vega, 2)
    }
