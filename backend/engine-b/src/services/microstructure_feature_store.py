"""
InfinityAI.Pro — Microstructure & Options Greeks Feature Store
==============================================================
Engine B | Production Grade | Version: 3.0.0

Ingests real-time order book depth (top 5 bids/asks), volatility surface Greeks,
and institutional smart money futures flows to produce an 8-dimensional institutional
feature matrix for the Tri-Model ML Ensemble:

  1. rsi_14: 14-period Relative Strength Index
  2. macd_crossover: Fast/Slow EMA momentum trigger (-1, 0, 1)
  3. vwap_distance: Percentage distance of current price from Volume-Weighted Average Price
  4. atr_volatility: Average True Range normalized volatility
  5. order_book_imbalance_5d: (Sum(BidQty_5) - Sum(AskQty_5)) / Sum(TotalQty_5) ∈ [-1.0, 1.0]
  6. iv_skew_ratio: IV(25-Delta Put) / IV(25-Delta Call) (Options Fear Gauge)
  7. gamma_exposure_index: Dealer Net Gamma Exposure (GEX) acceleration proxy
  8. fii_futures_net_delta: Normalized FII institutional futures long/short flow conviction
"""

import math
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger("InfinityAI.MicrostructureFeatureStore")

class MicrostructureFeatureStore:
    """Institutional 8-Feature Vector Generator"""

    def __init__(self):
        self.feature_names = [
            "rsi_14",
            "macd_crossover",
            "vwap_distance",
            "atr_volatility",
            "order_book_imbalance_5d",
            "iv_skew_ratio",
            "gamma_exposure_index",
            "fii_futures_net_delta"
        ]

    def compute_order_book_imbalance(
        self,
        bids: Optional[List[Dict[str, float]]] = None,
        asks: Optional[List[Dict[str, float]]] = None
    ) -> float:
        """
        Computes 5-depth Order Book Imbalance (OBI):
        OBI = (Total Bid Qty - Total Ask Qty) / (Total Bid Qty + Total Ask Qty)
        """
        if not bids or not asks:
            return 0.0

        bid_qty = sum(b.get("quantity", 0.0) for b in bids[:5])
        ask_qty = sum(a.get("quantity", 0.0) for a in asks[:5])
        total_qty = bid_qty + ask_qty

        if total_qty <= 0:
            return 0.0
        return float(np.clip((bid_qty - ask_qty) / total_qty, -1.0, 1.0))

    def compute_iv_skew(
        self,
        put_25d_iv: float = 0.1850,
        call_25d_iv: float = 0.1620
    ) -> float:
        """
        Computes 25-Delta Put/Call IV Skew Ratio.
        Skew > 1.10 indicates institutional downside hedging (Bearish/Fear).
        Skew < 0.95 indicates call buying frenzy (Bullish/Greed).
        """
        if call_25d_iv <= 0:
            return 1.0
        return round(float(put_25d_iv / call_25d_iv), 4)

    def compute_gamma_exposure_index(
        self,
        spot_price: float,
        atm_gamma: float,
        open_interest: int = 5000000
    ) -> float:
        """
        Estimates Net Dealer Gamma Exposure (GEX):
        GEX = (Gamma * Spot^2 * OI * 0.01) / 1e9 (Scaled in ₹ Billions)
        """
        if spot_price <= 0:
            return 0.0
        gex = (atm_gamma * (spot_price ** 2) * open_interest * 0.01) / 1e9
        return round(float(gex), 4)

    def generate_institutional_feature_vector(
        self,
        rsi_14: float,
        macd_crossover: int,
        vwap_distance: float,
        atr_volatility: float,
        bids: Optional[List[Dict[str, float]]] = None,
        asks: Optional[List[Dict[str, float]]] = None,
        put_iv: float = 0.1850,
        call_iv: float = 0.1620,
        spot_price: float = 0.0,
        atm_gamma: float = 0.0018,
        fii_long_short_ratio: float = 1.25
    ) -> Dict[str, Any]:
        """
        Assembles full 8-dimensional institutional feature vector.
        """
        if spot_price <= 0:
            raise ValueError("Valid positive spot_price is required to compute gamma exposure index.")
        obi = self.compute_order_book_imbalance(bids, asks)
        skew = self.compute_iv_skew(put_iv, call_iv)
        gex = self.compute_gamma_exposure_index(spot_price, atm_gamma)
        # Normalized FII delta: (Ratio - 1.0) / 1.0 clamped to [-1.0, 1.0]
        fii_delta = float(np.clip((fii_long_short_ratio - 1.0), -1.0, 1.0))

        vector = {
            "rsi_14": round(float(rsi_14), 2),
            "macd_crossover": int(macd_crossover),
            "vwap_distance": round(float(vwap_distance), 4),
            "atr_volatility": round(float(atr_volatility), 4),
            "order_book_imbalance_5d": round(obi, 4),
            "iv_skew_ratio": round(skew, 4),
            "gamma_exposure_index": round(gex, 4),
            "fii_futures_net_delta": round(fii_delta, 4)
        }
        
        feature_array = np.array([vector[f] for f in self.feature_names], dtype=np.float32)
        return {
            "feature_dict": vector,
            "feature_array": feature_array,
            "feature_names": self.feature_names
        }

MICROSTRUCTURE_STORE = MicrostructureFeatureStore()
