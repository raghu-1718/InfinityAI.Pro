"""
InfinityAI.Pro — Live Option Chain, IV Skew & Max Pain Analytics Engine
=======================================================================
Engine B | Category: Institutional Intelligence | Version: 2.0.0

Calculates:
  1. Put-Call Ratio (PCR_OI and PCR_Volume)
  2. Max Pain Strike (Minimum Option Writer Loss Strike)
  3. Implied Volatility (IV) Smile & Downside Put Skew
  4. Open Interest (OI) Buildup Classification (Long/Short Buildup/Unwinding)
  5. Major Support & Resistance Concentration Zones
"""

import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from scipy.stats import norm
import numpy as np

logger = logging.getLogger("InfinityAI.OptionChainAnalytics")

# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class OptionStrikeData:
    strike: float
    ce_oi: int
    ce_oi_change: int
    ce_volume: int
    ce_ltp: float
    ce_iv: float
    pe_oi: int
    pe_oi_change: int
    pe_volume: int
    pe_ltp: float
    pe_iv: float


@dataclass
class OptionChainSummary:
    underlying: str
    spot_price: float
    expiry_date: str
    total_ce_oi: int
    total_pe_oi: int
    pcr_oi: float
    pcr_volume: float
    max_pain_strike: float
    major_support_strike: float
    major_resistance_strike: float
    atm_strike: float
    atm_iv: float
    iv_skew_25d: float  # (25d Put IV - 25d Call IV)
    sentiment_bias: str # "BULLISH", "BEARISH", "NEUTRAL"
    oi_buildups: Dict[str, List[float]]  # {"long_buildup": [...], "short_buildup": [...]}
    raw_strikes: List[Dict[str, Any]] = field(default_factory=list)


# ==============================================================================
# Core Option Chain Analytics Engine
# ==============================================================================

class OptionChainAnalyticsEngine:
    """
    Institutional quantitative engine analyzing NSE/BSE options matrix.
    """

    def __init__(self, risk_free_rate: float = 0.065):
        self.rf = risk_free_rate

    @staticmethod
    def _round_to_nearest_strike(spot: float, step: int) -> float:
        return round(spot / step) * step

    def calculate_max_pain(self, strikes_data: List[OptionStrikeData]) -> float:
        """
        Calculates the strike price at which option sellers (writers) face minimum total loss.
        """
        if not strikes_data:
            return 0.0

        all_strikes = [s.strike for s in strikes_data]
        min_loss = float("inf")
        max_pain_strike = all_strikes[0]

        for test_k in all_strikes:
            total_loss = 0.0
            for leg in strikes_data:
                # Loss on Calls if market expires at test_k
                ce_loss = max(0.0, test_k - leg.strike) * leg.ce_oi
                # Loss on Puts if market expires at test_k
                pe_loss = max(0.0, leg.strike - test_k) * leg.pe_oi
                total_loss += (ce_loss + pe_loss)

            if total_loss < min_loss:
                min_loss = total_loss
                max_pain_strike = test_k

        return max_pain_strike

    def classify_oi_buildup(self, price_change: float, oi_change: int) -> str:
        """Classifies institutional Open Interest accumulation patterns."""
        if price_change > 0 and oi_change > 0:
            return "LONG_BUILDUP"       # Bullish aggressive buying
        elif price_change < 0 and oi_change > 0:
            return "SHORT_BUILDUP"      # Bearish aggressive selling
        elif price_change > 0 and oi_change < 0:
            return "SHORT_COVERING"     # Bullish short squeeze
        elif price_change < 0 and oi_change < 0:
            return "LONG_UNWINDING"     # Bearish long liquidation
        return "NEUTRAL"

    def analyze_option_chain(
        self,
        underlying: str,
        spot_price: float,
        expiry_date: str,
        strikes_matrix: List[Dict[str, Any]]
    ) -> OptionChainSummary:
        """
        Processes full option chain matrix and outputs complete institutional analytics.
        """
        step = 50 if underlying in ["NIFTY", "FINNIFTY"] else (100 if underlying == "BANKNIFTY" else 100)
        atm_strike = self._round_to_nearest_strike(spot_price, step)

        parsed_strikes: List[OptionStrikeData] = []
        total_ce_oi = 0
        total_pe_oi = 0
        total_ce_vol = 0
        total_pe_vol = 0

        max_ce_oi = -1
        max_pe_oi = -1
        major_res_strike = spot_price
        major_sup_strike = spot_price

        atm_iv = 0.15
        otm_call_iv = 0.15
        otm_put_iv = 0.16

        buildups = {
            "long_buildup": [],
            "short_buildup": [],
            "short_covering": [],
            "long_unwinding": []
        }

        for row in strikes_matrix:
            strike = float(row.get("strike", 0.0))
            ce_oi = int(row.get("ce_oi", 0))
            ce_oi_chg = int(row.get("ce_oi_change", 0))
            ce_vol = int(row.get("ce_volume", 0))
            ce_ltp = float(row.get("ce_ltp", 0.0))
            ce_iv = float(row.get("ce_iv", 0.15))

            pe_oi = int(row.get("pe_oi", 0))
            pe_oi_chg = int(row.get("pe_oi_change", 0))
            pe_vol = int(row.get("pe_volume", 0))
            pe_ltp = float(row.get("pe_ltp", 0.0))
            pe_iv = float(row.get("pe_iv", 0.15))

            item = OptionStrikeData(
                strike=strike,
                ce_oi=ce_oi, ce_oi_change=ce_oi_chg, ce_volume=ce_vol, ce_ltp=ce_ltp, ce_iv=ce_iv,
                pe_oi=pe_oi, pe_oi_change=pe_oi_chg, pe_volume=pe_vol, pe_ltp=pe_ltp, pe_iv=pe_iv
            )
            parsed_strikes.append(item)

            total_ce_oi += ce_oi
            total_pe_oi += pe_oi
            total_ce_vol += ce_vol
            total_pe_vol += pe_vol

            # Major Resistance (Highest CE OI above spot)
            if strike >= spot_price and ce_oi > max_ce_oi:
                max_ce_oi = ce_oi
                major_res_strike = strike

            # Major Support (Highest PE OI below spot)
            if strike <= spot_price and pe_oi > max_pe_oi:
                max_pe_oi = pe_oi
                major_sup_strike = strike

            # ATM IV
            if abs(strike - atm_strike) < (step / 2.0):
                atm_iv = round((ce_iv + pe_iv) / 2.0, 4)

            # 25-Delta OTM Skew Proxies (~1-2% OTM)
            if strike == (atm_strike + (step * 2)):
                otm_call_iv = ce_iv
            if strike == (atm_strike - (step * 2)):
                otm_put_iv = pe_iv

            # Classify Buildups
            ce_pattern = self.classify_oi_buildup(row.get("ce_ltp_change", 0.0), ce_oi_chg)
            if ce_pattern in ["LONG_BUILDUP", "SHORT_COVERING"]:
                buildups["long_buildup"].append(strike)
            elif ce_pattern in ["SHORT_BUILDUP", "LONG_UNWINDING"]:
                buildups["short_buildup"].append(strike)

        # Ratios
        pcr_oi = round(total_pe_oi / max(total_ce_oi, 1), 3)
        pcr_vol = round(total_pe_vol / max(total_ce_vol, 1), 3)
        max_pain = self.calculate_max_pain(parsed_strikes)
        iv_skew = round(otm_put_iv - otm_call_iv, 4)

        # Sentiment Bias Derivation
        if pcr_oi > 1.25 and spot_price > max_pain:
            sentiment = "STRONGLY_BULLISH"
        elif pcr_oi > 1.05:
            sentiment = "MODERATELY_BULLISH"
        elif pcr_oi < 0.75 and spot_price < max_pain:
            sentiment = "STRONGLY_BEARISH"
        elif pcr_oi < 0.90:
            sentiment = "MODERATELY_BEARISH"
        else:
            sentiment = "NEUTRAL_RANGEBOUND"

        return OptionChainSummary(
            underlying=underlying,
            spot_price=spot_price,
            expiry_date=expiry_date,
            total_ce_oi=total_ce_oi,
            total_pe_oi=total_pe_oi,
            pcr_oi=pcr_oi,
            pcr_volume=pcr_vol,
            max_pain_strike=max_pain,
            major_support_strike=major_sup_strike,
            major_resistance_strike=major_res_strike,
            atm_strike=atm_strike,
            atm_iv=atm_iv,
            iv_skew_25d=iv_skew,
            sentiment_bias=sentiment,
            oi_buildups=buildups,
            raw_strikes=strikes_matrix
        )

# Global Instance
option_chain_engine = OptionChainAnalyticsEngine()
