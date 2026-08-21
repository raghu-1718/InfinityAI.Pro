"""
Autonomous Shadow Signal Logger & Telemetry Vault
InfinityAI.Pro - Institutional Algorithmic Trading Platform
Automatically records all Tri-Model ML & Gemini signals into Cloud Firestore
without requiring manual trading execution or live capital risk.
"""

import os
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from google.cloud import firestore

try:
    from shared.tax_calculator import calculate_options_roundtrip_charges
except ImportError:
    try:
        from tax_calculator import calculate_options_roundtrip_charges
    except ImportError:
        def calculate_options_roundtrip_charges(*args, **kwargs):
            return {"grand_total_charges": 55.0}

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
COLLECTION_NAME = "ai_signals_ledger"

class ShadowSignalLogger:
    """Manages autonomous shadow signal logging and outcome resolution in Firestore"""

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        try:
            self.db = firestore.Client(project=self.project_id)
            logger.info(f"✅ ShadowSignalLogger connected to Firestore [{self.project_id}]")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Firestore: {e}")
            self.db = None

    def log_shadow_signal(
        self,
        symbol: str,
        spot_price: float,
        decision: str,  # "BUY_CALL", "BUY_PUT", "NEUTRAL"
        confidence_score: float,
        catboost_prob: float,
        lightgbm_prob: float,
        xgboost_prob: float,
        gemini_sentiment: str = "NEUTRAL",
        lot_size: int = 65,
        risk_reward_ratio: str = "1:2.0"
    ) -> Optional[Dict[str, Any]]:
        """
        Logs a generated trading signal into Firestore in SHADOW_OBSERVATION mode.
        """
        if not self.db:
            logger.warning("Firestore client not initialized. Skipping signal log.")
            return None

        # Filter out low conviction noise (<0.55 and >0.45)
        if decision == "NEUTRAL" or (0.45 < confidence_score < 0.55):
            logger.info(f"Signal for {symbol} is neutral/low confidence ({confidence_score:.3f}). Skipping ledger commit.")
            return None

        now_utc = datetime.now(timezone.utc)
        # Indian Standard Time (UTC+5:30)
        ist_time = now_utc + timedelta(hours=5, minutes=30)
        timestamp_str = ist_time.strftime("%Y-%m-%d %H:%M:%S IST")
        signal_id = f"SIG_{ist_time.strftime('%Y%m%d_%H%M%S')}_{symbol}"

        # Lot Size determination (SEBI / NSE / BSE 2026 Mandate)
        sym_u = symbol.upper()
        if "BANKNIFTY" in sym_u:
            actual_lot_size = 30
        elif "FINNIFTY" in sym_u:
            actual_lot_size = 60
        elif "MIDCP" in sym_u:
            actual_lot_size = 120
        elif "SENSEX" in sym_u:
            actual_lot_size = 20
        elif "NIFTY" in sym_u:
            actual_lot_size = 65
        else:
            actual_lot_size = 65

        # Option Bracket Calculation (Option Buying Only)
        # ATM Premium estimated at ~1.0% to 1.2% of underlying
        est_premium = round(spot_price * 0.011, 2)
        strike = round(spot_price / 50.0) * 50  # 50-point strike rounding
        option_type = "CE" if "CALL" in decision.upper() else "PE"
        contract_name = f"{symbol} {int(strike)} {option_type}"

        # Configured 15% Take-Profit Target and 12% Minimum Stop-Loss
        target_pct = 0.15      # +15% Minimum Profit Target (Configurable)
        stop_loss_pct = 0.12   # -12% Minimum Stop-Loss (Configurable)
        target_prem = round(est_premium * (1.0 + target_pct), 2)
        stop_loss_prem = round(est_premium * (1.0 - stop_loss_pct), 2)

        # Statutory taxes & Dhan brokerage estimate
        charges = calculate_options_roundtrip_charges(
            premium=est_premium,
            lot_size=actual_lot_size,
            lots=1,
            exchange="NSE"
        )
        tax_cost = charges.get("grand_total_charges", 55.0)

        payload = {
            "signal_id": signal_id,
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_ist": timestamp_str,
            "date": ist_time.strftime("%Y-%m-%d"),
            "month": ist_time.strftime("%Y-%m"),
            "symbol": symbol,
            "spot_price": spot_price,
            "decision": decision,
            "confidence_score": round(confidence_score, 4),
            "model_breakdown": {
                "catboost_prob": round(catboost_prob, 4),
                "lightgbm_prob": round(lightgbm_prob, 4),
                "xgboost_prob": round(xgboost_prob, 4),
                "gemini_sentiment": gemini_sentiment
            },
            "trade_bracket": {
                "contract": contract_name,
                "strike": strike,
                "option_type": option_type,
                "entry_premium": est_premium,
                "target_premium": target_prem,
                "target_percent": target_pct * 100,
                "stop_loss_premium": stop_loss_prem,
                "stop_loss_percent": stop_loss_pct * 100,
                "trailing_stop_loss_active": True,
                "risk_reward": "1:1.25 (Trailing)",
                "lot_size": actual_lot_size
            },
            "execution_mode": "SHADOW_OBSERVATION",
            "outcome_status": "OPEN",
            "estimated_tax_brokerage": tax_cost,
            "exit_premium": None,
            "gross_pnl": None,
            "net_pnl": None,
            "resolved_at": None
        }

        try:
            self.db.collection(COLLECTION_NAME).document(signal_id).set(payload)
            logger.info(f"✅ Shadow Signal committed to Firestore: [{signal_id}] -> {decision} on {symbol}")
            return payload
        except Exception as e:
            logger.error(f"❌ Failed to write shadow signal to Firestore: {e}")
            return None

    def resolve_signal_outcome(
        self,
        signal_id: str,
        current_spot: float,
        is_eod_squareoff: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Checks open signal and updates outcome (TARGET_HIT, STOP_LOSS_HIT, or EOD_SQUAREOFF).
        """
        if not self.db:
            return None

        doc_ref = self.db.collection(COLLECTION_NAME).document(signal_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None

        data = doc.to_dict()
        if data.get("outcome_status") != "OPEN":
            return data  # Already resolved

        bracket = data.get("trade_bracket", {})
        entry_prem = bracket.get("entry_premium", 100.0)
        target_prem = bracket.get("target_premium", 150.0)
        stop_prem = bracket.get("stop_loss_premium", 75.0)
        lot_size = bracket.get("lot_size", 65)
        decision = data.get("decision", "BUY_CALL")
        initial_spot = data.get("spot_price", current_spot)
        tax_cost = data.get("estimated_tax_brokerage", 55.0)

        # Underlying price move percentage
        spot_pct_move = (current_spot - initial_spot) / initial_spot if initial_spot > 0 else 0.0
        
        # Approximate option premium delta leverage (~20x delta multiplier on % move)
        if "CALL" in decision:
            simulated_exit_prem = entry_prem * (1.0 + (spot_pct_move * 20))
        else:
            simulated_exit_prem = entry_prem * (1.0 - (spot_pct_move * 20))

        simulated_exit_prem = max(1.0, simulated_exit_prem)

        outcome_status = "OPEN"
        if simulated_exit_prem >= target_prem:
            outcome_status = "TARGET_HIT"
            simulated_exit_prem = target_prem
        elif simulated_exit_prem <= stop_prem:
            outcome_status = "STOP_LOSS_HIT"
            simulated_exit_prem = stop_prem
        elif is_eod_squareoff:
            outcome_status = "EOD_SQUAREOFF"

        if outcome_status != "OPEN":
            gross_pnl = (simulated_exit_prem - entry_prem) * lot_size
            net_pnl = gross_pnl - tax_cost
            
            now_utc = datetime.now(timezone.utc)
            ist_time = now_utc + timedelta(hours=5, minutes=30)
            
            updates = {
                "outcome_status": outcome_status,
                "exit_premium": round(simulated_exit_prem, 2),
                "gross_pnl": round(gross_pnl, 2),
                "net_pnl": round(net_pnl, 2),
                "resolved_at": ist_time.strftime("%Y-%m-%d %H:%M:%S IST")
            }
            
            doc_ref.update(updates)
            logger.info(f"🎯 Signal [{signal_id}] Resolved -> {outcome_status} | Net PnL: ₹{net_pnl:+.2f}")
            data.update(updates)
            return data

        return data
