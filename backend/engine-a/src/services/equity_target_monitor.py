"""
Real-Time Equity Target Monitoring & Resolution Engine
InfinityAI.Pro - Institutional Algorithmic Trading Platform
Periodically monitors all OPEN equity positions, batch queries live LTPs
via DhanHQ API v2 (enforcing 1 req/sec limits), evaluates Target / Stop-Loss / Expiry,
updates Firestore `equity_signals_ledger`, and emits Pub/Sub events.
"""

import os
import time
import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from google.cloud import firestore
try:
    from google.cloud import pubsub_v1
except ImportError:
    pubsub_v1 = None
from google.cloud.firestore_v1.base_query import FieldFilter
import httpx
from src.services.alert_dispatcher import ALERT_DISPATCHER

logger = logging.getLogger("InfinityAI.EquityTargetMonitor")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
COLLECTION_NAME = "equity_signals_ledger"
PUBSUB_TOPIC_TARGET_HIT = os.getenv("PUBSUB_EQUITY_TARGET_HIT", "equity-target-hit")
ENGINE_C_URL = os.getenv("ENGINE_C_URL", "https://engine-c-r2f5flt77q-el.a.run.app")

def extract_quotes_dict(raw_data: Any) -> Dict[str, Any]:
    """Unpacks nested Dhan quote dictionary to retrieve the NSE_EQ map"""
    d = raw_data
    while isinstance(d, dict) and "data" in d and "NSE_EQ" not in d:
        d = d["data"]
    if isinstance(d, dict) and "NSE_EQ" in d:
        return d["NSE_EQ"]
    if isinstance(d, dict) and "data" in d and isinstance(d["data"], dict) and "NSE_EQ" in d["data"]:
        return d["data"]["NSE_EQ"]
    return {}

class EquityTargetMonitor:
    """Monitors active open equity signals against live market price action"""

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        try:
            self.db = firestore.Client(project=self.project_id)
            logger.info(f"EquityTargetMonitor connected to Firestore [{self.project_id}]")
        except Exception as e:
            logger.error(f"Failed to connect to Firestore: {e}")
            self.db = None

        try:
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(self.project_id, PUBSUB_TOPIC_TARGET_HIT)
        except Exception as e:
            logger.warning(f"Pub/Sub Publisher initialization notice: {e}")
            self.publisher = None

    async def fetch_batch_quotes(self, security_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Single batch quote request to Dhan gateway (rate-limit compliant: 1 req for up to 1000 IDs)"""
        quotes = {}
        if not security_ids:
            return quotes

        try:
            sec_str = ",".join(list(set(security_ids)))
            url = f"{ENGINE_C_URL}/api/dhan/market/quotes?security_ids={sec_str}&exchange_segment=NSE_EQ"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    raw_data = resp.json()
                    nse_eq = extract_quotes_dict(raw_data)
                    for sid, val in nse_eq.items():
                        if isinstance(val, dict):
                            ltp = float(val.get("last_price") or 0.0)
                            ohlc = val.get("ohlc", {})
                            if ltp > 0:
                                quotes[str(sid)] = {
                                    "ltp": ltp,
                                    "open": float(ohlc.get("open", ltp)),
                                    "high": float(ohlc.get("high", ltp)),
                                    "low": float(ohlc.get("low", ltp)),
                                    "close": float(ohlc.get("close", ltp)),
                                }
        except Exception as e:
            logger.error(f"Error fetching batch quotes from Dhan gateway: {e}")
        return quotes

    def format_duration(self, seconds: int) -> str:
        """Converts elapsed seconds into human-readable duration"""
        if seconds < 60:
            return f"{seconds}s"
        mins = seconds // 60
        hrs = mins // 60
        rem_mins = mins % 60
        days = hrs // 24
        rem_hrs = hrs % 24
        if days > 0:
            return f"{days}d {rem_hrs}h {rem_mins}m"
        if hrs > 0:
            return f"{hrs}h {rem_mins}m"
        return f"{mins}m"

    async def check_and_update_targets(self, simulated_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Scans all OPEN equity signals, evaluates against latest LTP & OHLC,
        resolves Target Hit / Stop Loss / Expiry, and updates Firestore.
        """
        if not self.db:
            return {"error": "Firestore not initialized", "checked": 0, "resolved": 0}

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "open_signals_checked": 0,
            "targets_hit": 0,
            "stopped_out": 0,
            "expired": 0,
            "still_open": 0,
            "resolved_signals": []
        }

        try:
            # 1. Query all OPEN equity signals
            query = self.db.collection(COLLECTION_NAME).where(filter=FieldFilter("status", "==", "OPEN"))
            open_docs = list(query.stream())
            results["open_signals_checked"] = len(open_docs)

            if not open_docs:
                logger.info("No OPEN equity signals in ledger to monitor.")
                return results

            # 2. Extract unique security IDs
            sec_ids = [str(doc.to_dict().get("security_id")) for doc in open_docs if doc.to_dict().get("security_id")]
            
            # 3. Batch fetch live quotes
            live_quotes = await self.fetch_batch_quotes(sec_ids)

            now_utc = datetime.now(timezone.utc)
            ist_time = now_utc + timedelta(hours=5, minutes=30)
            now_iso = now_utc.isoformat()

            for doc in open_docs:
                data = doc.to_dict()
                sig_id = doc.id
                sec_id = str(data.get("security_id"))
                sym = data.get("symbol")
                buy_p = float(data.get("buy_price", 0.0))
                target_p = float(data.get("target_price", 0.0))
                sl_p = float(data.get("stop_loss_price", 0.0))
                scan_ts_str = data.get("scan_timestamp")
                max_days = int(data.get("max_holding_days", 5))

                # Determine current price & intraday high/low
                if simulated_prices and sym in simulated_prices:
                    ltp = float(simulated_prices[sym])
                    high_p = ltp
                    low_p = ltp
                elif simulated_prices and sec_id in simulated_prices:
                    ltp = float(simulated_prices[sec_id])
                    high_p = ltp
                    low_p = ltp
                elif sec_id in live_quotes:
                    q = live_quotes[sec_id]
                    ltp = q["ltp"]
                    high_p = q["high"]
                    low_p = q["low"]
                else:
                    results["still_open"] += 1
                    continue

                # Calculate holding duration
                try:
                    scan_dt = datetime.fromisoformat(scan_ts_str.replace("Z", "+00:00"))
                    elapsed_seconds = int((now_utc - scan_dt).total_seconds())
                except Exception:
                    elapsed_seconds = 0

                is_target_hit = (high_p >= target_p) or (ltp >= target_p)
                is_sl_hit = (low_p <= sl_p) or (ltp <= sl_p)
                is_expired = (elapsed_seconds > (max_days * 86400))

                new_status = "OPEN"
                exit_price = None

                if is_target_hit:
                    new_status = "TARGET_HIT"
                    exit_price = max(target_p, ltp)
                    results["targets_hit"] += 1
                elif is_sl_hit:
                    new_status = "STOPPED_OUT"
                    exit_price = min(sl_p, ltp)
                    results["stopped_out"] += 1
                elif is_expired:
                    new_status = "EXPIRED"
                    exit_price = ltp
                    results["expired"] += 1
                else:
                    results["still_open"] += 1
                    continue

                # Compute exact returns
                returns_abs = round(exit_price - buy_p, 2)
                returns_pct = round((returns_abs / buy_p * 100), 2) if buy_p > 0 else 0.0
                time_str = self.format_duration(elapsed_seconds)

                update_payload = {
                    "status": new_status,
                    "target_hit_timestamp": now_iso,
                    "target_hit_timestamp_ist": ist_time.strftime("%Y-%m-%d %H:%M:%S IST"),
                    "actual_exit_price": round(exit_price, 2),
                    "time_to_target_seconds": elapsed_seconds,
                    "time_to_target_str": time_str,
                    "returns_pct": returns_pct,
                    "returns_absolute": returns_abs,
                    "resolved_at": ist_time.strftime("%Y-%m-%d %H:%M:%S IST")
                }

                # Update Firestore document
                self.db.collection(COLLECTION_NAME).document(sig_id).update(update_payload)
                logger.info(f"Equity Signal Resolved: [{sig_id}] -> {new_status} | Exit: Rs {exit_price} | Ret: {returns_pct:+}% | Duration: {time_str}")

                event_data = {**data, **update_payload}

                # Publish event to Pub/Sub
                if self.publisher and self.topic_path:
                    try:
                        self.publisher.publish(self.topic_path, data=json.dumps(event_data).encode("utf-8"), signal_id=sig_id, status=new_status)
                    except Exception as ex:
                        logger.warning(f"Pub/Sub publish error: {ex}")

                # Dispatch Telegram & Multi-Channel Alert
                try:
                    await ALERT_DISPATCHER.dispatch_equity_outcome_alert(event_data)
                except Exception as ex:
                    logger.warning(f"Telegram equity outcome alert error: {ex}")

                results["resolved_signals"].append({
                    "signal_id": sig_id,
                    "symbol": sym,
                    "status": new_status,
                    "exit_price": exit_price,
                    "returns_pct": returns_pct,
                    "time_to_target": time_str
                })

            return results
        except Exception as e:
            logger.error(f"Error during equity target monitoring cycle: {e}")
            results["error"] = str(e)
            return results

EQUITY_TARGET_MONITOR = EquityTargetMonitor()
