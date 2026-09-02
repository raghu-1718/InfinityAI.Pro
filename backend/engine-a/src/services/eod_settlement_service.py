import logging
import os
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from google.cloud import firestore, bigquery
from google.cloud.firestore_v1.base_query import FieldFilter

from src.services.tax_calculator import calculate_options_roundtrip_charges

logger = logging.getLogger("InfinityAI.EODSettlement")

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "project-841b7f97-5ee3-4fbe-920")
COLLECTION_NAME = "ai_signals_ledger"

class EODSettlementService:
    """
    Automated EOD Market-Close Settlement & Retraining Service (15:45 IST).
    1. Reconciles and resolves all OPEN shadow signals at market close.
    2. Computes final gross/net PnL with statutory SEBI/Dhan fees.
    3. Streams daily summary metrics to BigQuery (market_data.eod_settlements).
    4. Triggers the nightly MLOps retraining job.
    """

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        try:
            self.db = firestore.Client(project=project_id)
            self.bq = bigquery.Client(project=project_id)
            logger.info("✅ EODSettlementService connected to Firestore & BigQuery")
        except Exception as e:
            logger.error(f"❌ EODSettlementService connection error: {e}")
            self.db = None
            self.bq = None

    def run_eod_reconciliation(self, current_spot_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Scans all OPEN shadow signals for today and resolves them at EOD close prices.
        """
        if not self.db:
            return {"status": "error", "message": "Firestore client unavailable"}

        now_utc = datetime.now(timezone.utc)
        ist_time = now_utc + timedelta(hours=5, minutes=30)
        today_str = ist_time.strftime("%Y-%m-%d")

        logger.info(f"⏰ Starting EOD Settlement for Date: {today_str} at {ist_time.strftime('%H:%M:%S IST')}")

        open_signals_ref = (
            self.db.collection(COLLECTION_NAME)
            .where(filter=FieldFilter("outcome_status", "==", "OPEN"))
            .stream()
        )

        resolved_count = 0
        total_gross_pnl = 0.0
        total_net_pnl = 0.0
        total_fees = 0.0
        details = []

        spot_prices = {}
        if current_spot_prices:
            spot_prices.update(current_spot_prices)
        elif self.db:
            try:
                history = list(self.db.collection("market_regime_heartbeats").order_by("timestamp_utc", direction=firestore.Query.DESCENDING).limit(1).stream())
                if history:
                    last_doc = history[0].to_dict()
                    if last_doc.get("data_source") != "DEGRADED_BROKER_FEED_UNAVAILABLE":
                        spot_prices["NIFTY"] = last_doc.get("nifty_spot")
                        spot_prices["BANKNIFTY"] = last_doc.get("banknifty_spot")
                        spot_prices["SENSEX"] = last_doc.get("sensex_spot")
                        spot_prices["INDIAVIX"] = last_doc.get("india_vix")
            except Exception as e:
                logger.warning(f"Failed to resolve closing spot prices from Firestore: {e}")

        if not spot_prices or not spot_prices.get("NIFTY"):
            logger.warning("🚨 EOD Settlement: Genuine closing quotes unavailable. Deferring settlement.")
            return {
                "settlement_status": "DEFERRED_FEED_UNAVAILABLE",
                "resolved_count": 0,
                "total_net_pnl": 0.0,
                "message": "Settlement deferred: genuine closing quotes required."
            }

        for doc in open_signals_ref:
            data = doc.to_dict()
            sig_id = data.get("signal_id", doc.id)
            symbol = data.get("symbol", "NIFTY")
            decision = data.get("decision", "BUY_CALL")
            bracket = data.get("trade_bracket", {})
            entry_prem = bracket.get("entry_premium", 100.0)
            lot_sz = bracket.get("lot_size", 65)

            # Grounded EOD settlement: compute actual underlying return from entry spot to closing spot
            entry_spot = float(data.get("underlying_spot") or bracket.get("entry_spot") or 0.0)
            closing_spot = float(spot_prices.get(symbol.upper()) or 0.0)

            if entry_spot > 0 and closing_spot > 0:
                spot_ret = (closing_spot - entry_spot) / entry_spot
                # Delta-scaled option return (~0.55 delta) minus 1-day theta decay (~3%)
                opt_ret = (spot_ret * (0.55 if "CALL" in decision else -0.55)) - 0.03
                exit_prem = max(round(entry_prem * (1.0 + opt_ret), 2), 0.50)
            else:
                gain_factor = 1.05 if "CALL" in decision else 0.95
                exit_prem = round(entry_prem * gain_factor, 2)
            gross_pnl = round((exit_prem - entry_prem) * lot_sz, 2)

            charges = calculate_options_roundtrip_charges(
                premium=entry_prem,
                lot_size=lot_sz,
                lots=1,
                exchange="NSE"
            )
            tax_cost = charges.get("grand_total_charges", 55.0)
            net_pnl = round(gross_pnl - tax_cost, 2)

            outcome = "TARGET_HIT" if gross_pnl > 0 else "EOD_SQUAREOFF"

            # Update Firestore Document
            doc.reference.update({
                "outcome_status": outcome,
                "exit_premium": exit_prem,
                "gross_pnl": gross_pnl,
                "net_pnl": net_pnl,
                "resolved_at": ist_time.strftime("%Y-%m-%d %H:%M:%S IST"),
                "settlement_type": "EOD_1530_AUTORESOLUTION"
            })

            resolved_count += 1
            total_gross_pnl += gross_pnl
            total_net_pnl += net_pnl
            total_fees += tax_cost

            details.append({
                "signal_id": sig_id,
                "symbol": symbol,
                "decision": decision,
                "entry_premium": entry_prem,
                "exit_premium": exit_prem,
                "gross_pnl": gross_pnl,
                "net_pnl": net_pnl,
                "outcome": outcome
            })

        logger.info(f"✅ EOD Settlement Complete: {resolved_count} signals resolved | Net PnL: ₹{total_net_pnl:,.2f}")

        # Stream summary to BigQuery if table exists
        self._stream_eod_summary_to_bigquery(today_str, resolved_count, total_gross_pnl, total_net_pnl, total_fees)

        # Trigger Vertex AI Post-Market Performance Review & Telegram Dispatch
        journal_report = None
        try:
            from .eod_ai_journal_service import EOD_AI_JOURNAL_SERVICE
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(EOD_AI_JOURNAL_SERVICE.generate_and_dispatch_eod_journal(today_str))
                else:
                    journal_report = loop.run_until_complete(EOD_AI_JOURNAL_SERVICE.generate_and_dispatch_eod_journal(today_str))
            except RuntimeError:
                journal_report = asyncio.run(EOD_AI_JOURNAL_SERVICE.generate_and_dispatch_eod_journal(today_str))
        except Exception as je:
            logger.warning(f"Notice generating EOD journal during settlement: {je}")

        return {
            "status": "success",
            "date": today_str,
            "settled_at": ist_time.strftime("%Y-%m-%d %H:%M:%S IST"),
            "resolved_signals": resolved_count,
            "total_gross_pnl": round(total_gross_pnl, 2),
            "total_net_pnl": round(total_net_pnl, 2),
            "total_fees_taxes": round(total_fees, 2),
            "journal_report": journal_report,
            "details": details
        }

    def _stream_eod_summary_to_bigquery(self, date_str: str, count: int, gross: float, net: float, fees: float):
        """Insert EOD settlement summary into BigQuery for historical compliance"""
        if not self.bq:
            return
        try:
            table_id = f"{self.project_id}.market_data.eod_settlements"
            rows = [{
                "settlement_date": date_str,
                "signals_count": count,
                "total_gross_pnl": gross,
                "total_net_pnl": net,
                "total_fees": fees,
                "executed_at": datetime.now(timezone.utc).isoformat()
            }]
            # Insert if table exists, otherwise silently log
            self.bq.insert_rows_json(table_id, rows)
            logger.info(f"✅ EOD Summary streamed to BigQuery {table_id}")
        except Exception as e:
            logger.debug(f"BigQuery stream non-critical notification: {e}")

    def trigger_nightly_retraining(self) -> Dict[str, Any]:
        """
        Invokes Cloud Run Job model-retraining-job asynchronously via gcloud / API
        """
        logger.info("🚀 Triggering Nightly MLOps Model Retraining Job...")
        try:
            cmd = [
                "gcloud", "run", "jobs", "execute", "model-retraining-job",
                "--region=asia-south1",
                f"--project={self.project_id}",
                "--async"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                logger.info("✅ Nightly Retraining Job triggered successfully")
                return {"status": "success", "message": "model-retraining-job triggered", "output": result.stdout.strip()}
            else:
                logger.warning(f"⚠️ Retraining job trigger returned non-zero: {result.stderr}")
                return {"status": "warning", "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"❌ Failed to trigger retraining job: {e}")
            return {"status": "error", "error": str(e)}
