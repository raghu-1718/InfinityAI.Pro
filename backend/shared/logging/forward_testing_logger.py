"""
InfinityAI.Pro — Dedicated Cloud Logging Stream for 30-Day Forward-Testing
==========================================================================
Logs structured performance telemetry to an isolated Cloud Logging sink:
`projects/project-841b7f97-5ee3-4fbe-920/logs/infinity-forward-testing-30d`

Tracks:
1. Precision & Recall metrics per evaluated regime
2. Multi-model consensus conviction vs realized alpha
3. Microstructure bid-ask spread & simulated execution slippage
4. Cumulative PnL, drawdowns, and capital utilization within the ₹30k boundary
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from google.cloud import logging as gcp_logging

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
LOG_STREAM_NAME = "infinity-forward-testing-30d"

class ForwardTestingLogger:
    """Dedicated logger that streams structured quantitative metrics to GCP Cloud Logging."""

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        self.logger_client = None
        self.cloud_logger = None
        try:
            self.logger_client = gcp_logging.Client(project=self.project_id)
            self.cloud_logger = self.logger_client.logger(LOG_STREAM_NAME)
        except Exception as e:
            logging.warning(f"Cloud Logging forward-testing client warning: {e}")

    def log_trade_evaluation(
        self,
        setup_id: str,
        symbol: str,
        direction: str,
        master_rank: int,
        is_top_10: bool,
        composite_score: float,
        moe_conviction: float,
        adx: float,
        entry_spot: float,
        simulated_fill_price: float,
        slippage_bps: float,
        allocated_lots: int,
        margin_utilized: float,
        available_margin: float,
        notes: str = ""
    ):
        """Logs trade setup qualification and capital allocation telemetry."""
        payload = {
            "event_type": "MASTER_TRADE_EVALUATION",
            "setup_id": setup_id,
            "symbol": symbol,
            "direction": direction,
            "master_rank": master_rank,
            "is_top_10": is_top_10,
            "composite_score": round(composite_score, 4),
            "moe_conviction": round(moe_conviction, 4),
            "adx": round(adx, 2),
            "entry_spot": round(entry_spot, 2),
            "simulated_fill_price": round(simulated_fill_price, 2),
            "slippage_bps": round(slippage_bps, 2),
            "allocated_lots": allocated_lots,
            "margin_utilized": round(margin_utilized, 2),
            "available_margin": round(available_margin, 2),
            "capital_boundary": 30000.0,
            "notes": notes,
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        }

        if self.cloud_logger:
            try:
                self.cloud_logger.log_struct(payload, severity="INFO")
            except Exception as e:
                logging.debug(f"Cloud Logging struct log notice: {e}")
        else:
            logging.info(f"[{LOG_STREAM_NAME}] {json.dumps(payload)}")

    def log_trade_resolution(
        self,
        setup_id: str,
        symbol: str,
        direction: str,
        master_rank: int,
        entry_premium: float,
        exit_premium: float,
        gross_pnl_inr: float,
        net_pnl_inr: float,
        holding_duration_seconds: float,
        outcome_status: str,
        alpha_decay_factor: float = 0.0,
        trailing_sl_ratchet_count: int = 0
    ):
        """Logs realized trade resolution, precision/recall, and alpha decay telemetry."""
        is_win = (net_pnl_inr > 0)
        payload = {
            "event_type": "MASTER_TRADE_RESOLUTION",
            "setup_id": setup_id,
            "symbol": symbol,
            "direction": direction,
            "master_rank": master_rank,
            "entry_premium": round(entry_premium, 2),
            "exit_premium": round(exit_premium, 2),
            "gross_pnl_inr": round(gross_pnl_inr, 2),
            "net_pnl_inr": round(net_pnl_inr, 2),
            "is_win": is_win,
            "outcome_status": outcome_status,
            "holding_duration_s": round(holding_duration_seconds, 1),
            "alpha_decay_factor": round(alpha_decay_factor, 4),
            "trailing_sl_ratchets": trailing_sl_ratchet_count,
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        }

        if self.cloud_logger:
            try:
                severity = "INFO" if is_win else "WARNING"
                self.cloud_logger.log_struct(payload, severity=severity)
            except Exception as e:
                logging.debug(f"Cloud Logging struct log notice: {e}")
        else:
            logging.info(f"[{LOG_STREAM_NAME}] {json.dumps(payload)}")

FORWARD_TESTING_LOGGER = ForwardTestingLogger()
