"""
Equity Analysis & Target Tracking API Routes
InfinityAI.Pro - Institutional Algorithmic Trading Platform
Handles Pub/Sub push webhooks and direct REST triggers for equity scanning,
target monitoring, and BigQuery synchronization.
"""

import base64
import json
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel

from src.services.equity_scanner import EQUITY_SCANNER, EQUITY_UNIVERSE
from src.services.equity_target_monitor import EQUITY_TARGET_MONITOR
from src.services.equity_bigquery_sync import EQUITY_BQ_SYNC
from src.services.idempotency import IDEMPOTENCY_MANAGER

logger = logging.getLogger("InfinityAI.EquityRoutes")
router = APIRouter(prefix="/api/v1/equity", tags=["Equity Analysis Pipeline"])

class PubSubEnvelope(BaseModel):
    message: Optional[Dict[str, Any]] = None
    subscription: Optional[str] = None

@router.get("/status")
async def get_equity_pipeline_status():
    """Returns current status and health of the Equity Analysis Pipeline"""
    try:
        return {
            "status": "online",
            "pipeline": "NSE_EQ_ANALYSIS_AND_TARGET_TRACKING",
            "universe_size": len(EQUITY_UNIVERSE),
            "engine": "engine-a",
            "firestore_collection": "equity_signals_ledger",
            "bigquery_table": "market_data.equity_signals"
        }
    except Exception as e:
        logger.error(f"Error fetching equity pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pubsub/scan")
async def handle_pubsub_equity_scan(envelope: Optional[PubSubEnvelope] = None):
    """
    Pub/Sub Push Webhook for Equity Universe Scanning.
    Triggered by Cloud Scheduler via topic `equity-scan-requests`.
    """
    message_id = None
    if envelope and envelope.message:
        message_id = envelope.message.get("message_id") or envelope.message.get("messageId")
    
    logger.info(f"📥 Received Pub/Sub trigger for Equity Universe Scan [Message ID: {message_id}]")

    # Application-level idempotency check
    if message_id:
        allowed = IDEMPOTENCY_MANAGER.check_and_claim_message(
            message_id=message_id,
            handler_name="EQUITY_SCAN",
            topic="equity-scan-requests"
        )
        if not allowed:
            return {
                "status": "skipped_duplicate_message",
                "message_id": message_id,
                "reason": "DUPLICATE_PUBSUB_MESSAGE_ID"
            }

    try:
        # Run equity scanner across universe
        signals = await EQUITY_SCANNER.scan_universe()
        
        # Sync newly created signals to BigQuery
        sync_result = EQUITY_BQ_SYNC.sync_all_firestore_to_bigquery()

        logger.info(f"✅ Equity Scan complete: {len(signals)} setups generated | BigQuery Synced: {sync_result.get('synced_successfully')}")
        return {
            "status": "success",
            "event": "EQUITY_SCAN_EXECUTED",
            "message_id": message_id,
            "generated_signals_count": len(signals),
            "bigquery_sync": sync_result
        }
    except Exception as e:
        logger.error(f"❌ Failed during Pub/Sub equity scan: {e}")
        # Always return 200/202 to Pub/Sub to prevent infinite retry loops on internal non-fatal errors
        return {"status": "error", "error": str(e)}

@router.post("/pubsub/target-check")
async def handle_pubsub_equity_target_check(envelope: Optional[PubSubEnvelope] = None):
    """
    Pub/Sub Push Webhook for Equity Target Monitoring.
    Triggered by Cloud Scheduler every 60s via topic `equity-target-check`.
    """
    message_id = None
    if envelope and envelope.message:
        message_id = envelope.message.get("message_id") or envelope.message.get("messageId")
    
    logger.info(f"📥 Received Pub/Sub trigger for Equity Target Monitoring [Message ID: {message_id}]")

    # Application-level idempotency check
    if message_id:
        allowed = IDEMPOTENCY_MANAGER.check_and_claim_message(
            message_id=message_id,
            handler_name="EQUITY_TARGET_CHECK",
            topic="equity-target-check"
        )
        if not allowed:
            return {
                "status": "skipped_duplicate_message",
                "message_id": message_id,
                "reason": "DUPLICATE_PUBSUB_MESSAGE_ID"
            }

    try:
        # Check active open positions against Dhan live quotes
        results = await EQUITY_TARGET_MONITOR.check_and_update_targets()

        # Sync any resolved signals to BigQuery
        sync_result = EQUITY_BQ_SYNC.sync_all_firestore_to_bigquery()

        logger.info(f"✅ Target Monitor cycle complete: {results.get('open_signals_checked')} checked | {results.get('targets_hit')} targets hit | {results.get('stopped_out')} stopped out")
        return {
            "status": "success",
            "event": "EQUITY_TARGET_CHECK_EXECUTED",
            "message_id": message_id,
            "monitor_results": results,
            "bigquery_sync": sync_result
        }
    except Exception as e:
        logger.error(f"❌ Failed during Pub/Sub equity target check: {e}")
        return {"status": "error", "error": str(e)}

@router.post("/scan")
async def direct_equity_scan(watchlist: Optional[List[Dict[str, str]]] = None):
    """Direct REST trigger for equity scan"""
    signals = await EQUITY_SCANNER.scan_universe(watchlist)
    sync_result = EQUITY_BQ_SYNC.sync_all_firestore_to_bigquery()
    return {"status": "success", "signals": signals, "bigquery_sync": sync_result}

@router.post("/target-check")
async def direct_target_check():
    """Direct REST trigger for equity target check"""
    results = await EQUITY_TARGET_MONITOR.check_and_update_targets()
    sync_result = EQUITY_BQ_SYNC.sync_all_firestore_to_bigquery()
    return {"status": "success", "results": results, "bigquery_sync": sync_result}
