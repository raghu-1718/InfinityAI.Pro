"""
InfinityAI.Pro — Expiry Day 0DTE/1DTE Gamma Pinning & Theta Shield Engine
=========================================================================
Engine A | Production Grade | Version: 3.0.0

Specialized risk shield for Tuesday NSE Expiry (NIFTY/BANKNIFTY) and Thursday BSE Expiry (SENSEX):
  1. Real-Time Max Pain Calculation:
     - Continuously computes total option buyer loss at every strike:
       Total Loss(K) = sum_i( Call_OI_i * max(0, K - Strike_i) + Put_OI_i * max(0, Strike_i - K) )
     - Pinning Target = Strike K with Minimum Total Loss.

  2. 0DTE Gamma Spike Detection:
     - Detects extreme Gamma acceleration (|Gamma| > 0.0030) indicating high risk of explosive intraday reversal.

  3. Afternoon Theta Shield (Post 13:30 IST):
     - Dynamically tightens trailing profit lock buffer to +4% guaranteed floor to prevent late-afternoon 3:00 PM theta crush.
"""

import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from .expiry_theta_damper import EXPIRY_THETA_DAMPER

logger = logging.getLogger("InfinityAI.ExpiryGammaShield")

class ExpiryGammaPinningShield:
    """Institutional Expiry-Day Gamma Pinning & Theta Shield Engine"""

    def __init__(self):
        self.gamma_spike_threshold = 0.0030  # High Gamma threshold for 0DTE options
        self.theta_shield_start_hour = 13    # 13:30 IST
        self.theta_shield_start_minute = 30

    def compute_max_pain_strike(
        self,
        strikes_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Computes the theoretical Max Pain strike from strike-wise Call & Put Open Interest.
        """
        if not strikes_data:
            return {"max_pain_strike": 24200, "pinning_probability": 0.50, "min_loss_crores": 0.0}

        strikes = [s.get("strike", 0.0) for s in strikes_data if s.get("strike", 0.0) > 0]
        if not strikes:
            return {"max_pain_strike": 24200, "pinning_probability": 0.50, "min_loss_crores": 0.0}

        min_total_loss = float("inf")
        best_strike = strikes[0]

        for test_k in strikes:
            total_loss = 0.0
            for row in strikes_data:
                k = row.get("strike", 0.0)
                call_oi = row.get("call_oi", 0)
                put_oi = row.get("put_oi", 0)

                # Loss on Calls if market settles at test_k
                call_loss = max(0.0, test_k - k) * call_oi
                # Loss on Puts if market settles at test_k
                put_loss = max(0.0, k - test_k) * put_oi
                total_loss += (call_loss + put_loss)

            if total_loss < min_total_loss:
                min_total_loss = total_loss
                best_strike = test_k

        return {
            "max_pain_strike": int(best_strike),
            "min_loss_crores": round(min_total_loss / 1e7, 2),
            "strikes_evaluated": len(strikes)
        }

    def evaluate_expiry_shield(
        self,
        symbol: str,
        spot_price: float,
        live_greeks: Dict[str, float],
        entry_premium: float,
        current_premium: float,
        highest_observed_premium: float,
        strikes_oi_data: Optional[List[Dict[str, Any]]] = None,
        current_time_ist: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Evaluates real-time 0DTE/1DTE Gamma Spike and Theta Shield conditions.
        """
        if current_time_ist is None:
            now_utc = datetime.now(timezone.utc)
            current_time_ist = now_utc + timedelta(hours=5, minutes=30)

        is_expiry = EXPIRY_THETA_DAMPER.is_expiry_day(symbol, current_time_ist)
        gamma = live_greeks.get("Gamma", live_greeks.get("gamma", 0.0018))
        theta = live_greeks.get("Theta", live_greeks.get("theta", -45.0))

        # Check for 0DTE Gamma Spike
        is_gamma_spike = abs(gamma) >= self.gamma_spike_threshold

        # Check for Afternoon Theta Zone (>= 13:30 IST on Expiry Day)
        time_decimal = current_time_ist.hour + (current_time_ist.minute / 60.0)
        is_afternoon_theta_zone = is_expiry and (time_decimal >= 13.5)

        # Max Pain Evaluation
        max_pain_info = self.compute_max_pain_strike(strikes_oi_data or [])
        max_pain_strike = max_pain_info["max_pain_strike"]
        distance_from_max_pain_pts = round(spot_price - max_pain_strike, 2)
        pinning_gravity = "STRONG_PINNING_MAGNET" if abs(distance_from_max_pain_pts) <= 50.0 else "DRIFTING"

        # Trailing Stop Adjustment Invariants
        peak_gain_pct = (highest_observed_premium - entry_premium) / entry_premium if entry_premium > 0 else 0.0
        tightened_trailing_sl = entry_premium * 0.89  # Default baseline
        shield_mode = "STANDARD_OPERATION"

        if is_afternoon_theta_zone:
            shield_mode = "AFTERNOON_THETA_SHIELD_ACTIVE"
            if peak_gain_pct >= 0.08:
                # Tighten trailing stop aggressively to protect against rapid 3 PM theta crush
                tightened_trailing_sl = round(entry_premium * (1.0 + max(0.04, peak_gain_pct - 0.04)), 2)
            else:
                tightened_trailing_sl = round(entry_premium * 0.94, 2) # Tighten max stop to -6%
        elif is_gamma_spike:
            shield_mode = "GAMMA_SPIKE_PROTECTION_ACTIVE"
            if peak_gain_pct >= 0.08:
                tightened_trailing_sl = round(entry_premium * (1.0 + max(0.03, peak_gain_pct - 0.05)), 2)

        return {
            "symbol": symbol,
            "is_expiry_day": is_expiry,
            "shield_mode": shield_mode,
            "is_gamma_spike": is_gamma_spike,
            "live_gamma": round(gamma, 6),
            "live_theta": round(theta, 2),
            "is_afternoon_theta_zone": is_afternoon_theta_zone,
            "max_pain_strike": max_pain_strike,
            "distance_from_max_pain_pts": distance_from_max_pain_pts,
            "pinning_gravity": pinning_gravity,
            "tightened_trailing_sl": round(tightened_trailing_sl, 2),
            "timestamp_ist": current_time_ist.strftime("%Y-%m-%d %H:%M:%S IST")
        }

EXPIRY_GAMMA_SHIELD = ExpiryGammaPinningShield()
