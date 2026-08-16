"""
InfinityAI.Pro - Institutional Real-Time Options Chain Ingestion Engine
Streams live option contracts, Greeks, and liquidity from DhanHQ v2 API into BigQuery market_data.options_ticks.
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

logger = logging.getLogger("options_chain_ingestor")

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
                from google.cloud import bigquery
                self._bq_client = bigquery.Client(project=self.project_id)
            except Exception as e:
                logger.warning(f"BigQuery client init fallback: {e}")
                self._bq_client = None
        return self._bq_client

    async def ingest_live_option_chains(self, user_id: str = "raghu_primary") -> Dict[str, Any]:
        """
        Polls DhanHQ v2 Option Chain API for all supported indices and inserts ticks into BigQuery.
        """
        t0 = time.time()
        creds = await self.credentials_manager.get_user_credentials(user_id)
        client_id = creds.get("client_id") or creds.get("dhan_client_id")
        access_token = creds.get("access_token") or creds.get("dhan_access_token")

        if not access_token or not client_id:
            logger.error("❌ Dhan credentials unavailable in Firestore Vault for options ingestion")
            return {"status": "error", "message": "Dhan credentials not found"}

        headers = {
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

            # 1. Resolve nearest active expiry
            exp_url = "https://api.dhan.co/v2/optionchain/expirylist"
            exp_payload = {"UnderlyingScrip": sec_id, "UnderlyingSeg": segment}
            target_expiry = None

            try:
                exp_resp = requests.post(exp_url, headers=headers, json=exp_payload, timeout=8)
                if exp_resp.status_code == 200:
                    exp_list = exp_resp.json().get("data", []) or []
                    if exp_list:
                        target_expiry = exp_list[0]
            except Exception as e:
                logger.warning(f"Failed to fetch expiry for {symbol}: {e}")

            if not target_expiry:
                continue

            # 2. Fetch full option chain depth
            oc_url = "https://api.dhan.co/v2/optionchain"
            oc_payload = {
                "UnderlyingScrip": sec_id,
                "UnderlyingSeg": segment,
                "Expiry": target_expiry
            }

            try:
                oc_resp = requests.post(oc_url, headers=headers, json=oc_payload, timeout=10)
                if oc_resp.status_code == 200:
                    data = oc_resp.json().get("data", {})
                    oc_dict = data.get("oc", {}) or {}
                    symbol_rows = 0

                    for strike_str, strike_info in oc_dict.items():
                        try:
                            strike_price = int(float(strike_str))
                        except Exception:
                            continue

                        # Call Option (CE)
                        ce = strike_info.get("ce", {})
                        if ce:
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
                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                })
                                symbol_rows += 1

                        # Put Option (PE)
                        pe = strike_info.get("pe", {})
                        if pe:
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
                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                })
                                symbol_rows += 1

                    indices_summary[symbol] = {
                        "expiry": target_expiry,
                        "contracts_extracted": symbol_rows
                    }
            except Exception as e:
                logger.error(f"Error fetching option chain for {symbol}: {e}")

        # 3. Stream in batches into BigQuery options_ticks
        total_inserted = 0
        batch_size = 500
        for i in range(0, len(rows_to_insert), batch_size):
            batch = rows_to_insert[i:i + batch_size]
            errors = self.bq_client.insert_rows_json(self.table_id, batch)
            if not errors:
                total_inserted += len(batch)
            else:
                logger.error(f"BigQuery streaming error: {errors[:2]}")

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
