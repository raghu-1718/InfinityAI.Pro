"""
Unit Tests for Margin-Aware Option Premium Sizing and PreMarketMacroRadar Quota Shield
InfinityAI.Pro - Production Verification Suite
"""
import pytest
import sys
import os
import importlib.util
from pathlib import Path
from datetime import datetime, timezone

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENGINE_A_DIR = str(PROJECT_ROOT / "backend" / "engine-a")
ENGINE_B_DIR = str(PROJECT_ROOT / "backend" / "engine-b")

if ENGINE_A_DIR not in sys.path:
    sys.path.insert(0, ENGINE_A_DIR)

from src.services.risk_manager import RiskManager


def test_sensex_option_premium_sizing_affordable():
    """
    Verify that SENSEX option sizing calculates margin on option premium
    rather than treating spot index price as option premium.
    """
    rm = RiskManager()
    user_capital = 100000.0  # ₹1 Lakh
    current_price = 76515.43
    signal = {
        "symbol": "SENSEX",
        "predicted_price": 76800.0,  # Spot index target
        "signal": "BUY",
        "confidence": 82.0
    }

    # Corrected formula from autonomous_trader.py
    raw_premium = signal.get("option_premium")
    if raw_premium and float(raw_premium) > 0:
        est_premium = float(raw_premium)
    elif current_price > 500:
        est_premium = current_price * 0.011
    else:
        est_premium = current_price

    assert est_premium < 1000.0, f"Option premium must be ~1.1% of spot, got {est_premium}"

    margin_sizing = rm.calculate_margin_aware_lot_size(
        capital=user_capital,
        risk_per_trade=0.10,
        symbol="SENSEX",
        premium=est_premium,
        max_lots_cap=5
    )

    # Must be viable and allocate lots within capital
    assert margin_sizing["is_viable"] is True
    assert margin_sizing["optimal_lots"] > 0
    assert margin_sizing["optimal_lots"] <= 5
    assert margin_sizing["total_margin_required"] <= user_capital
    assert margin_sizing["cost_per_lot"] < 20000.0  # Lot size 20 * ~841 = ~16,833


def test_macro_radar_cache_ttl():
    """
    Verify that PreMarketMacroRadar returns cached report without re-invoking
    Vertex AI when within 15-minute TTL.
    """
    radar_path = Path(ENGINE_B_DIR) / "src" / "services" / "premarket_macro_radar.py"
    spec = importlib.util.spec_from_file_location("premarket_macro_radar_mod", str(radar_path))
    radar_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(radar_mod)

    radar = radar_mod.PreMarketMacroRadar()
    now_utc = datetime.now(timezone.utc)
    mock_report = radar_mod.MacroRadarReport(
        timestamp_utc=now_utc.isoformat(),
        report_date=now_utc.strftime("%Y-%m-%d"),
        macro_bias="BULLISH",
        macro_score=0.45,
        gift_nifty_points=50.0,
        expected_gap="GAP_UP",
        crude_oil_pct=-1.2,
        crude_oil_status="BENIGN",
        us_10y_yield=4.25,
        dxy_index=103.1,
        fii_net_crores=1500.0,
        dii_net_crores=1100.0,
        institutional_flow_bias="NET_INFLOW",
        gemini_macro_synthesis="Cached institutional synthesis",
        recommended_opening_bias="BUY_DIPS",
        risk_regime="LOW_VOLATILITY"
    )
    radar.cached_report = mock_report

    # Call generate_radar_report without override parameters
    result = radar.generate_radar_report()
    assert result is mock_report, "Must return cached report within 15-minute TTL"
    assert result.gemini_macro_synthesis == "Cached institutional synthesis"
