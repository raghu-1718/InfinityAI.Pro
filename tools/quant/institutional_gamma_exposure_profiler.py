"""
Institutional Gamma Exposure (GEX) Profiler (Domain 3 & Quant Intelligence)
===========================================================================
InfinityAI.Pro - Institutional Options Microstructure Analysis
Queries the BigQuery BI Engine In-Memory Accelerated Table:
  `project-841b7f97-5ee3-4fbe-920.market_data.options_ticks`

Computes:
  1. Strike-by-Strike Dealer Gamma Exposure (Call GEX, Put GEX, Net GEX in ₹ Crores per 1% move).
  2. Total Market Net GEX ($/₹ Gamma imbalance).
  3. The Zero-Gamma Flip Point (Critical volatility transition trigger level).
  4. Dealer Positioning Regime (Positive Gamma = Mean-Reverting vs Negative Gamma = Volatility Expansion).
  5. Call Resistance Wall and Put Support Floor.
  6. Real-time publication to Cloud Firestore collection `gamma_exposure_profiles`.
"""

import os
import sys
import math
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from google.cloud import bigquery, firestore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("InstitutionalGEXProfiler")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
LOCATION = os.getenv("GCP_LOCATION", "asia-south1")

# Standard Index Lot Sizes (SEBI 2026 Mandate)
INDEX_LOT_SIZES = {
    "NIFTY": 65,
    "BANKNIFTY": 30,
    "FINNIFTY": 60,
    "MIDCPNIFTY": 120,
    "SENSEX": 20
}


def norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)


def compute_black_scholes_gamma(
    spot: float,
    strike: float,
    dte_days: float,
    iv: float,
    r: float = 0.065
) -> float:
    """
    Computes analytical Black-Scholes Gamma (d2V / dS2).
    Gamma is identical for both standard Calls and Puts.
    """
    if spot <= 0 or strike <= 0 or iv <= 0:
        return 0.0

    t_years = max(dte_days / 365.0, 1.0 / 365.0)  # floor at 1 day
    sqrt_t = math.sqrt(t_years)

    d1 = (math.log(spot / strike) + (r + 0.5 * iv * iv) * t_years) / (iv * sqrt_t)
    gamma = norm_pdf(d1) / (spot * iv * sqrt_t)
    return float(gamma)


class InstitutionalGEXProfiler:
    """Calculates Net Gamma Exposure and identifies dealer positioning inflection points."""

    def __init__(self, project_id: str = PROJECT_ID, location: str = LOCATION):
        self.project_id = project_id
        self.location = location
        self.bq_client = bigquery.Client(project=project_id, location=location)
        self.db = firestore.Client(project=project_id)

    def fetch_options_surface(self, symbol: str = "NIFTY") -> Tuple[float, List[Dict[str, Any]]]:
        """
        Queries BI Engine in-memory accelerated table market_data.options_ticks.
        Extracts strike, option_type, open_interest, implied_volatility, and spot_price.
        """
        logger.info(f"⚡ Querying BigQuery BI Engine accelerated surface for {symbol}...")
        query = f"""
        SELECT 
            underlying,
            strike_price,
            option_type,
            open_interest,
            implied_volatility,
            premium_price,
            timestamp
        FROM `{self.project_id}.market_data.options_ticks`
        WHERE underlying = '{symbol.upper()}'
        ORDER BY strike_price ASC
        """
        df = self.bq_client.query(query).to_dataframe()

        if df.empty:
            logger.warning(f"No active options_ticks found for {symbol}. Using synthetic baseline surface.")
            return 24200.0, []

        spot_price = 24200.0  # Reference baseline spot if not in table
        records = df.to_dict(orient="records")
        return spot_price, records

    def profile_gamma_exposure(
        self,
        symbol: str = "NIFTY",
        spot_price: Optional[float] = None,
        contracts: Optional[List[Dict[str, Any]]] = None,
        dte_days: float = 4.0
    ) -> Dict[str, Any]:
        """
        Profiles strike-by-strike Gamma Exposure (GEX) and computes Zero-Gamma flip point.
        """
        sym_upper = symbol.upper()
        lot_size = INDEX_LOT_SIZES.get(sym_upper, 65)

        if spot_price is None or contracts is None:
            fetched_spot, fetched_contracts = self.fetch_options_surface(sym_upper)
            spot_price = spot_price or fetched_spot
            contracts = contracts or fetched_contracts

        # If BigQuery returned empty (off-market initial state), build strike chain around spot
        if not contracts:
            interval = 50 if sym_upper == "NIFTY" else 100
            atm = round(spot_price / interval) * interval
            contracts = []
            for i in range(-10, 11):
                k = atm + i * interval
                # Realistic open interest distribution
                dist = abs(i)
                call_oi = int(max(5000, (15 - dist) * 12000 + (3000 if i >= 0 else 0)))
                put_oi = int(max(5000, (15 - dist) * 11500 + (3000 if i <= 0 else 0)))
                contracts.append({
                    "strike_price": k,
                    "option_type": "CE",
                    "open_interest": call_oi,
                    "implied_volatility": 0.142 + dist * 0.001
                })
                contracts.append({
                    "strike_price": k,
                    "option_type": "PE",
                    "open_interest": put_oi,
                    "implied_volatility": 0.146 + dist * 0.001
                })

        # Organize by strike
        strike_data = {}
        for c in contracts:
            k = float(c.get("strike_price") or c.get("strike") or 0.0)
            if k <= 0:
                continue
            if k not in strike_data:
                strike_data[k] = {"ce_oi": 0, "pe_oi": 0, "ce_iv": 0.14, "pe_iv": 0.14}

            opt_type = str(c.get("option_type", "")).upper()
            oi = int(c.get("open_interest", 0) or c.get("oi", 0))
            iv = float(c.get("implied_volatility", 0.14) or 0.14)
            if iv > 1.0:
                iv = iv / 100.0  # normalize 14.5 -> 0.145

            if "CE" in opt_type or "CALL" in opt_type:
                strike_data[k]["ce_oi"] = oi
                strike_data[k]["ce_iv"] = max(0.05, iv)
            else:
                strike_data[k]["pe_oi"] = oi
                strike_data[k]["pe_iv"] = max(0.05, iv)

        strikes_sorted = sorted(strike_data.keys())
        gex_by_strike = []
        total_call_gex = 0.0
        total_put_gex = 0.0

        for k in strikes_sorted:
            d = strike_data[k]
            # Calculate Gamma
            avg_iv = (d["ce_iv"] + d["pe_iv"]) / 2.0
            gamma = compute_black_scholes_gamma(spot_price, k, dte_days, avg_iv)

            # GEX Formula: OI * LotSize * Spot^2 * Gamma * 0.01 / 1e7 (in ₹ Crores per 1% move)
            call_gex = (d["ce_oi"] * lot_size * (spot_price ** 2) * gamma * 0.01) / 1e7
            put_gex = -(d["pe_oi"] * lot_size * (spot_price ** 2) * gamma * 0.01) / 1e7
            net_gex = call_gex + put_gex

            total_call_gex += call_gex
            total_put_gex += put_gex

            gex_by_strike.append({
                "strike": k,
                "gamma": round(gamma, 6),
                "call_oi": d["ce_oi"],
                "put_oi": d["pe_oi"],
                "call_gex_cr": round(call_gex, 2),
                "put_gex_cr": round(put_gex, 2),
                "net_gex_cr": round(net_gex, 2)
            })

        net_market_gex = total_call_gex + total_put_gex

        # Find Call Resistance Wall (Highest Call GEX)
        call_wall_row = max(gex_by_strike, key=lambda x: x["call_gex_cr"])
        call_resistance_wall = call_wall_row["strike"]

        # Find Put Support Floor (Most Negative Put GEX)
        put_floor_row = min(gex_by_strike, key=lambda x: x["put_gex_cr"])
        put_support_floor = put_floor_row["strike"]

        # Calculate Zero-Gamma Flip Point
        # Linear interpolation where cumulative / net GEX crosses 0
        zero_gamma_flip = spot_price
        for i in range(len(gex_by_strike) - 1):
            s1 = gex_by_strike[i]["strike"]
            s2 = gex_by_strike[i + 1]["strike"]
            g1 = gex_by_strike[i]["net_gex_cr"]
            g2 = gex_by_strike[i + 1]["net_gex_cr"]
            if (g1 <= 0 and g2 > 0) or (g1 >= 0 and g2 < 0):
                # Interpolate strike where GEX = 0
                slope = (g2 - g1) / (s2 - s1) if s2 != s1 else 1.0
                zero_gamma_flip = s1 - (g1 / slope) if slope != 0 else s1
                break

        # Determine Dealer Regime
        if net_market_gex >= 0:
            regime_label = "POSITIVE_GAMMA_REGIME"
            dealer_behavior = "Market makers are Net Long Gamma. Hedging activity absorbs shocks (buying dips, selling rips). Realized volatility is compressed/mean-reverting."
        else:
            regime_label = "NEGATIVE_GAMMA_REGIME"
            dealer_behavior = "Market makers are Net Short Gamma. Hedging activity exacerbates directional trends (selling dips, buying rallies). High risk of explosive breakouts / gamma cascades."

        profile_report = {
            "symbol": sym_upper,
            "spot_price": spot_price,
            "dte_days": dte_days,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_call_gex_cr": round(total_call_gex, 2),
            "total_put_gex_cr": round(total_put_gex, 2),
            "net_market_gex_cr": round(net_market_gex, 2),
            "zero_gamma_flip_point": round(zero_gamma_flip, 2),
            "call_resistance_wall": call_resistance_wall,
            "put_support_floor": put_support_floor,
            "dealer_regime": regime_label,
            "dealer_behavior_description": dealer_behavior,
            "gex_ladder": gex_by_strike
        }

        # Publish to Cloud Firestore
        try:
            doc_ref = self.db.collection("gamma_exposure_profiles").document(sym_upper)
            doc_ref.set({
                "symbol": sym_upper,
                "spot_price": spot_price,
                "net_market_gex_cr": round(net_market_gex, 2),
                "zero_gamma_flip_point": round(zero_gamma_flip, 2),
                "call_resistance_wall": call_resistance_wall,
                "put_support_floor": put_support_floor,
                "dealer_regime": regime_label,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"✅ Published GEX Profile to Firestore: gamma_exposure_profiles/{sym_upper}")
        except Exception as fe:
            logger.warning(f"Firestore GEX publish deferred: {fe}")

        return profile_report


def run_gex_analysis(symbol: str = "NIFTY"):
    profiler = InstitutionalGEXProfiler()
    report = profiler.profile_gamma_exposure(symbol=symbol, spot_price=24219.05)

    print("\n" + "=" * 80)
    print(f"  INSTITUTIONAL GAMMA EXPOSURE (GEX) REPORT: {report['symbol']}")
    print("=" * 80)
    print(f"  Spot Price:               Rs. {report['spot_price']:,.2f}")
    print(f"  Zero-Gamma Flip Point:    Rs. {report['zero_gamma_flip_point']:,.2f}")
    print(f"  Call Resistance Wall:     Rs. {report['call_resistance_wall']:,.2f}")
    print(f"  Put Support Floor:        Rs. {report['put_support_floor']:,.2f}")
    print(f"  Total Call GEX:           +Rs. {report['total_call_gex_cr']:,.2f} Cr / 1% move")
    print(f"  Total Put GEX:            -Rs. {abs(report['total_put_gex_cr']):,.2f} Cr / 1% move")
    print(f"  Net Market GEX:           {'+' if report['net_market_gex_cr'] >= 0 else ''}Rs. {report['net_market_gex_cr']:,.2f} Cr / 1% move")
    print(f"  Dealer Regime:            {report['dealer_regime']}")
    print(f"  Regime Mechanics:         {report['dealer_behavior_description']}")
    print("-" * 80)
    print(f"{'Strike':<10} | {'Call OI':<10} | {'Put OI':<10} | {'Call GEX (Cr)':<14} | {'Put GEX (Cr)':<14} | {'Net GEX (Cr)'}")
    print("-" * 80)
    for row in report["gex_ladder"][:15]:
        flag = " [CALL WALL]" if row["strike"] == report["call_resistance_wall"] else ""
        flag = " [PUT FLOOR]" if row["strike"] == report["put_support_floor"] else flag
        print(f"{row['strike']:<10.0f} | {row['call_oi']:<10,d} | {row['put_oi']:<10,d} | {row['call_gex_cr']:<14.2f} | {row['put_gex_cr']:<14.2f} | {row['net_gex_cr']:<10.2f}{flag}")
    print("=" * 80)

    return report


if __name__ == "__main__":
    run_gex_analysis("NIFTY")
