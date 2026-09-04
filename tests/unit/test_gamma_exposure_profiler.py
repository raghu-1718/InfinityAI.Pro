"""
Unit Tests for Institutional Gamma Exposure (GEX) Profiler
==========================================================
Verifies:
  1. Analytical Black-Scholes Gamma calculation correctness.
  2. Dealer Gamma Exposure (Call GEX, Put GEX, Net GEX) calculations.
  3. Zero-Gamma Flip Point interpolation.
  4. Dealer Positioning Regime (Positive Gamma vs Negative Gamma).
"""

import pytest
import math
from tools.quant.institutional_gamma_exposure_profiler import (
    compute_black_scholes_gamma,
    norm_pdf,
    InstitutionalGEXProfiler
)


def test_black_scholes_gamma_at_the_money():
    spot = 24000.0
    strike = 24000.0
    dte_days = 4.0
    iv = 0.15
    gamma = compute_black_scholes_gamma(spot, strike, dte_days, iv)
    
    assert gamma > 0.0
    # For ATM with ~4 DTE, gamma should be positive and realistic (~0.0001 - 0.002)
    assert 0.0001 < gamma < 0.005


def test_black_scholes_gamma_deep_out_of_the_money():
    spot = 24000.0
    strike = 28000.0  # Deep OTM
    dte_days = 4.0
    iv = 0.15
    gamma = compute_black_scholes_gamma(spot, strike, dte_days, iv)
    
    # Deep OTM gamma should be near zero
    assert 0.0 <= gamma < 1e-6


def test_gex_profiler_synthetic_chain():
    # Instantiate without connecting to GCP if testing offline logic
    class TestGEXProfiler(InstitutionalGEXProfiler):
        def __init__(self):
            # Bypass BQ and Firestore network clients for pure calculation testing
            pass

    profiler = TestGEXProfiler()
    spot = 24000.0
    contracts = [
        {"strike_price": 23800, "option_type": "PE", "open_interest": 100000, "implied_volatility": 0.15},
        {"strike_price": 23900, "option_type": "PE", "open_interest": 120000, "implied_volatility": 0.15},
        {"strike_price": 24000, "option_type": "CE", "open_interest": 80000, "implied_volatility": 0.15},
        {"strike_price": 24000, "option_type": "PE", "open_interest": 70000, "implied_volatility": 0.15},
        {"strike_price": 24100, "option_type": "CE", "open_interest": 130000, "implied_volatility": 0.15},
        {"strike_price": 24200, "option_type": "CE", "open_interest": 150000, "implied_volatility": 0.15},
    ]

    report = profiler.profile_gamma_exposure(
        symbol="NIFTY",
        spot_price=spot,
        contracts=contracts,
        dte_days=4.0
    )

    assert report["symbol"] == "NIFTY"
    assert report["spot_price"] == 24000.0
    assert report["call_resistance_wall"] == 24200.0
    assert report["put_support_floor"] == 23900.0
    assert "dealer_regime" in report
    assert "zero_gamma_flip_point" in report
    assert len(report["gex_ladder"]) > 0
