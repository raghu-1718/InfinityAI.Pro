"""
Firestore to BigQuery Synchronization Engine for Equity Signals
InfinityAI.Pro - Institutional Algorithmic Trading Platform
Mirrors `equity_signals_ledger` Firestore collection into BigQuery `market_data.equity_signals`
table with row-level validation, deduplication MERGE, and checksum reconciliation.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from google.cloud import firestore, bigquery

logger = logging.getLogger("InfinityAI.EquityBigQuerySync")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
COLLECTION_NAME = "equity_signals_ledger"
BQ_TABLE_ID = f"{PROJECT_ID}.market_data.equity_signals"

class EquityBigQuerySync:
    """Manages continuous and batch synchronization of equity signals to BigQuery"""

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        try:
            self.db = firestore.Client(project=self.project_id)
            self.bq_client = bigquery.Client(project=self.project_id)
            logger.info(f"✅ EquityBigQuerySync initialized for BigQuery [{BQ_TABLE_ID}]")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firestore/BigQuery clients: {e}")
            self.db = None
            self.bq_client = None

    def format_row_for_bq(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maps Firestore equity document to BigQuery schema types"""
        now_iso = datetime.now(timezone.utc).isoformat()
        
        analysis_method = doc_data.get("analysis_method", {})
        if isinstance(analysis_method, (dict, list)):
            analysis_str = json.dumps(analysis_method)
        else:
            analysis_str = str(analysis_method) if analysis_method else None

        scan_ts = doc_data.get("scan_timestamp")
        target_hit_ts = doc_data.get("target_hit_timestamp")

        return {
            "signal_id": str(doc_data.get("signal_id")),
            "symbol": str(doc_data.get("symbol")),
            "security_id": str(doc_data.get("security_id")),
            "exchange_segment": doc_data.get("exchange_segment", "NSE_EQ"),
            "scan_timestamp": scan_ts,
            "scan_date": doc_data.get("scan_date", scan_ts[:10] if scan_ts else datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            "buy_price": float(doc_data.get("buy_price")) if doc_data.get("buy_price") is not None else None,
            "target_price": float(doc_data.get("target_price")) if doc_data.get("target_price") is not None else None,
            "stop_loss_price": float(doc_data.get("stop_loss_price")) if doc_data.get("stop_loss_price") is not None else None,
            "status": doc_data.get("status", "OPEN"),
            "target_hit_timestamp": target_hit_ts,
            "time_to_target_seconds": int(doc_data.get("time_to_target_seconds")) if doc_data.get("time_to_target_seconds") is not None else None,
            "actual_exit_price": float(doc_data.get("actual_exit_price")) if doc_data.get("actual_exit_price") is not None else None,
            "returns_pct": float(doc_data.get("returns_pct")) if doc_data.get("returns_pct") is not None else None,
            "returns_absolute": float(doc_data.get("returns_absolute")) if doc_data.get("returns_absolute") is not None else None,
            "confidence_score": float(doc_data.get("confidence_score")) if doc_data.get("confidence_score") is not None else None,
            "analysis_method": analysis_str,
            "sync_timestamp": now_iso
        }

    def sync_single_document(self, doc_data: Dict[str, Any]) -> bool:
        """Inserts or updates a single equity record into BigQuery via MERGE statement"""
        if not self.bq_client:
            return False

        row = self.format_row_for_bq(doc_data)
        
        merge_query = f"""
        MERGE `{BQ_TABLE_ID}` T
        USING (
            SELECT
                @signal_id AS signal_id,
                @symbol AS symbol,
                @security_id AS security_id,
                @exchange_segment AS exchange_segment,
                PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*SZ', @scan_timestamp) AS scan_timestamp,
                PARSE_DATE('%Y-%m-%d', @scan_date) AS scan_date,
                @buy_price AS buy_price,
                @target_price AS target_price,
                @stop_loss_price AS stop_loss_price,
                @status AS status,
                CASE WHEN @target_hit_timestamp IS NOT NULL THEN PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*SZ', @target_hit_timestamp) ELSE NULL END AS target_hit_timestamp,
                @time_to_target_seconds AS time_to_target_seconds,
                @actual_exit_price AS actual_exit_price,
                @returns_pct AS returns_pct,
                @returns_absolute AS returns_absolute,
                @confidence_score AS confidence_score,
                @analysis_method AS analysis_method,
                CURRENT_TIMESTAMP() AS sync_timestamp
        ) S
        ON T.signal_id = S.signal_id AND T.scan_date = S.scan_date
        WHEN MATCHED THEN
            UPDATE SET
                status = S.status,
                target_hit_timestamp = S.target_hit_timestamp,
                time_to_target_seconds = S.time_to_target_seconds,
                actual_exit_price = S.actual_exit_price,
                returns_pct = S.returns_pct,
                returns_absolute = S.returns_absolute,
                sync_timestamp = S.sync_timestamp
        WHEN NOT MATCHED THEN
            INSERT (signal_id, symbol, security_id, exchange_segment, scan_timestamp, scan_date, buy_price, target_price, stop_loss_price, status, target_hit_timestamp, time_to_target_seconds, actual_exit_price, returns_pct, returns_absolute, confidence_score, analysis_method, sync_timestamp)
            VALUES (S.signal_id, S.symbol, S.security_id, S.exchange_segment, S.scan_timestamp, S.scan_date, S.buy_price, S.target_price, S.stop_loss_price, S.status, S.target_hit_timestamp, S.time_to_target_seconds, S.actual_exit_price, S.returns_pct, S.returns_absolute, S.confidence_score, S.analysis_method, S.sync_timestamp);
        """

        scan_ts = row["scan_timestamp"]
        if scan_ts and not scan_ts.endswith("Z"):
            scan_ts = scan_ts.split("+")[0] + "Z"

        hit_ts = row["target_hit_timestamp"]
        if hit_ts and not hit_ts.endswith("Z"):
            hit_ts = hit_ts.split("+")[0] + "Z"

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("signal_id", "STRING", row["signal_id"]),
                bigquery.ScalarQueryParameter("symbol", "STRING", row["symbol"]),
                bigquery.ScalarQueryParameter("security_id", "STRING", row["security_id"]),
                bigquery.ScalarQueryParameter("exchange_segment", "STRING", row["exchange_segment"]),
                bigquery.ScalarQueryParameter("scan_timestamp", "STRING", scan_ts),
                bigquery.ScalarQueryParameter("scan_date", "STRING", row["scan_date"]),
                bigquery.ScalarQueryParameter("buy_price", "FLOAT64", row["buy_price"]),
                bigquery.ScalarQueryParameter("target_price", "FLOAT64", row["target_price"]),
                bigquery.ScalarQueryParameter("stop_loss_price", "FLOAT64", row["stop_loss_price"]),
                bigquery.ScalarQueryParameter("status", "STRING", row["status"]),
                bigquery.ScalarQueryParameter("target_hit_timestamp", "STRING", hit_ts),
                bigquery.ScalarQueryParameter("time_to_target_seconds", "INT64", row["time_to_target_seconds"]),
                bigquery.ScalarQueryParameter("actual_exit_price", "FLOAT64", row["actual_exit_price"]),
                bigquery.ScalarQueryParameter("returns_pct", "FLOAT64", row["returns_pct"]),
                bigquery.ScalarQueryParameter("returns_absolute", "FLOAT64", row["returns_absolute"]),
                bigquery.ScalarQueryParameter("confidence_score", "FLOAT64", row["confidence_score"]),
                bigquery.ScalarQueryParameter("analysis_method", "STRING", row["analysis_method"]),
            ]
        )

        try:
            query_job = self.bq_client.query(merge_query, job_config=job_config)
            query_job.result()
            logger.info(f"✅ Synced equity signal {row['signal_id']} to BigQuery via MERGE")
            return True
        except Exception as e:
            logger.error(f"Failed to sync {row['signal_id']} to BigQuery: {e}")
            return False

    def sync_all_firestore_to_bigquery(self) -> Dict[str, Any]:
        """Performs full reconciliation sync of all Firestore equity documents into BigQuery"""
        if not self.db or not self.bq_client:
            return {"error": "Clients not initialized", "synced": 0}

        docs = list(self.db.collection(COLLECTION_NAME).stream())
        total_fs = len(docs)
        synced_count = 0
        failed_count = 0

        logger.info(f"🔄 Starting BigQuery reconciliation for {total_fs} Firestore equity documents...")

        for d in docs:
            success = self.sync_single_document(d.to_dict())
            if success:
                synced_count += 1
            else:
                failed_count += 1

        # Query BigQuery total count
        bq_count_query = f"SELECT COUNT(*) AS total_rows FROM `{BQ_TABLE_ID}`"
        bq_res = list(self.bq_client.query(bq_count_query).result())
        total_bq = bq_res[0].total_rows if bq_res else 0

        return {
            "firestore_total_docs": total_fs,
            "synced_successfully": synced_count,
            "sync_failed": failed_count,
            "bigquery_total_rows": total_bq,
            "checksum_status": "MATCH" if total_fs == total_bq else "COUNT_DELTA"
        }

EQUITY_BQ_SYNC = EquityBigQuerySync()
