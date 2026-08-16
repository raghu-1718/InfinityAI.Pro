"""
InfinityAI.Pro - Institutional Real-Time Options Chain Ingestion Engine
Streams live option contracts, Greeks, and liquidity from DhanHQ v2 API into BigQuery market_data.options_ticks.
Utilizes DhanClient wrapper for rate limiting and direct HTTP fallback for expirylist.
"""

import os
import time
import asyncio
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from google.cloud import bigquery

from .user_credentials import UserCredentialsManager
from .dhan_client_wrapper import create_dhan_client, DhanEnvironment

logger = logging.getLogger("options_chain_ingestor")
logger.setLevel(logging.INFO)

# Core Indian Index Underlyings for Options Ingestion
SUPPORTED_OPTIONS_INDICES = [
    {"symbol": "NIFTY", "sec_id": 13, "segment": "IDX_I"},
    {"symbol": "BANKNIFTY", "sec_id": 25, "segment": "IDX_I"},
    {"symbol": "SENSEX", "sec_id": 51, "segment": "IDX_I"},
    {"symbol": "FINNIFTY", "sec_id": 27, "segment": "IDX_I"},
    {"symbol": "MIDCPNIFTY", "sec_id": 442, "segment": "IDX_I"},
]

class OptionsChainIngestor:
    def __init__(self, project_id: str = "project-841b7f97-5ee3-4fbe-920"):
        self.project_id = project_id
        self.table_id = f"{project_id}.market_data.options_ticks"
        self.credentials_manager = UserCredentialsManager()
        self._bq_client = None

    @property
    def bq_client(self):
        if self._bq_client is None:
            try:
                self._bq_client = bigquery.Client(project=self.project_id)
                logger.info(f"BigQuery client initialized for project: {self.project_id}")
            except Exception as e:
                logger.error(f"Failed to initialize BigQuery client: {e}")
                self._bq_client = None
        return self._bq_client

    async def ingest_live_option_chains(self, user_id: str = "raghu_primary") -> Dict[str, Any]:
        """
        Polls DhanHQ v2 Option Chain API for all supported indices and inserts ticks into BigQuery.
        Leverages DhanClient wrapper for rate-limit handling where possible.
        """
        t0 = time.time()
        creds = await self.credentials_manager.get_user_credentials(user_id)
        client_id = creds.get("client_id") or creds.get("dhan_client_id")
        access_token = creds.get("access_token") or creds.get("dhan_access_token")

        if not access_token or not client_id:
            logger.error("❌ Dhan credentials unavailable in Firestore Vault for options ingestion")
            return {"status": "error", "message": "Dhan credentials not found"}

        # Initialize DhanClient wrapper for SDK calls (handles rate limits safely)
        dhan_client_wrapper = create_dhan_client(client_id, access_token, environment=DhanEnvironment.PRODUCTION)

        # Headers for direct HTTP requests (e.g., expirylist fallback)
        http_headers = {
            "access-token": access_token,
            "client-id": client_id,
            "Content-Type": "application/json"
        }

        rows_to_insert: List[Dict[str, Any]] = []
        indices_summary = {}

        for idx in SUPPORTED_OPTIONS_INDICES:
            symbol = idx["symbol"]
            sec_id = idx["sec_id"]
            segment = idx["segment"]

            # 1. Resolve nearest active expiry (Direct HTTP with strict 8s timeout)
            exp_url = "https://api.dhan.co/v2/optionchain/expirylist"
            exp_payload = {"UnderlyingScrip": sec_id, "UnderlyingSeg": segment}
            target_expiry = None

            try:
                exp_resp = requests.post(exp_url, headers=http_headers, json=exp_payload, timeout=8)
                exp_resp.raise_for_status()
                exp_list = exp_resp.json().get("data", []) or []
                if exp_list:
                    target_expiry = exp_list[0]
                else:
                    logger.warning(f"No expiry dates found for {symbol} from DhanHQ.")
            except requests.exceptions.Timeout:
                logger.error(f"Timeout fetching expiry for {symbol} from DhanHQ.")
            except Exception as e:
                logger.warning(f"Failed to fetch expiry for {symbol}: {e}")

            if not target_expiry:
                continue

            # 2. Fetch full option chain depth using DhanClient wrapper
            try:
                oc_data = dhan_client_wrapper.option_chain(
                    under_security_id=sec_id,
                    under_exchange_segment=segment,
                    expiry=target_expiry
                )

                if oc_data and oc_data.get("status") == "success":
                    oc_dict = oc_data.get("data", {}).get("oc", {}) or {}
                    symbol_rows = 0
                    current_timestamp = datetime.now(timezone.utc).isoformat()

                    for strike_str, strike_info in oc_dict.items():
                        try:
                            strike_price = int(float(strike_str))
                        except (ValueError, TypeError):
                            logger.warning(f"Skipping malformed strike price '{strike_str}' for {symbol}.")
                            continue

                        # Call Option (CE)
                        ce = strike_info.get("ce", {})
                        if ce and isinstance(ce, dict):
                            ce_ltp = float(ce.get("last_price") or ce.get("ltp") or 0.0)
                            if ce_ltp > 0:
                                rows_to_insert.append({
                                    "trade_id": f"{symbol}_{strike_price}_CE_{int(time.time()*1000)}",
                                    "underlying": symbol,
                                    "strike_price": strike_price,
                                    "option_type": "CE",
                                    "expiry_date": target_expiry,
                                    "premium_price": ce_ltp,
                                    "volume": int(ce.get("volume") or ce.get("vol") or 0),
                                    "open_interest": int(ce.get("oi") or ce.get("open_interest") or 0),
                                    "implied_volatility": float(ce.get("iv") or 0.0),
                                    "timestamp": current_timestamp
                                })
                                symbol_rows += 1

                        # Put Option (PE)
                        pe = strike_info.get("pe", {})
                        if pe and isinstance(pe, dict):
                            pe_ltp = float(pe.get("last_price") or pe.get("ltp") or 0.0)
                            if pe_ltp > 0:
                                rows_to_insert.append({
                                    "trade_id": f"{symbol}_{strike_price}_PE_{int(time.time()*1000)}",
                                    "underlying": symbol,
                                    "strike_price": strike_price,
                                    "option_type": "PE",
                                    "expiry_date": target_expiry,
                                    "premium_price": pe_ltp,
                                    "volume": int(pe.get("volume") or pe.get("vol") or 0),
                                    "open_interest": int(pe.get("oi") or pe.get("open_interest") or 0),
                                    "implied_volatility": float(pe.get("iv") or 0.0),
                                    "timestamp": current_timestamp
                                })
                                symbol_rows += 1

                    indices_summary[symbol] = {
                        "expiry": target_expiry,
                        "contracts_extracted": symbol_rows
                    }
                elif oc_data and oc_data.get("status") == "upstream_maintenance":
                    logger.warning(f"DhanHQ upstream maintenance for {symbol}. Skipping cycle.")
                else:
                    logger.error(f"Failed to fetch option chain for {symbol}: {oc_data.get('remarks', 'Unknown error')}")

            except Exception as e:
                logger.error(f"Error processing option chain for {symbol}: {e}")

        # 3. Stream in batches into BigQuery options_ticks (Optimized batch_size = 500)
        total_inserted = 0
        batch_size = 500

        if not self.bq_client:
            logger.critical("BigQuery client not initialized. Cannot insert rows.")
            return {"status": "error", "message": "BigQuery client not available"}

        if rows_to_insert:
            for i in range(0, len(rows_to_insert), batch_size):
                batch = rows_to_insert[i:i + batch_size]
                try:
                    errors = self.bq_client.insert_rows_json(self.table_id, batch)
                    if not errors:
                        total_inserted += len(batch)
                    else:
                        logger.error(f"BigQuery streaming errors for batch {i}: {errors[:5]}")
                except Exception as e:
                    logger.error(f"Unexpected BQ insert error at batch {i}: {e}")

        duration_ms = round((time.time() - t0) * 1000, 2)
        logger.info(f"✅ Options Ingestion: Streamed {total_inserted} contracts into {self.table_id} in {duration_ms}ms")

        return {
            "status": "success",
            "total_inserted": total_inserted,
            "latency_ms": duration_ms,
            "indices": indices_summary,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

options_ingestor = OptionsChainIngestor()
