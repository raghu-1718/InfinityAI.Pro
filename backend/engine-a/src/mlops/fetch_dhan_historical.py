"""
InfinityAI.Pro — Dhan Historical Bootstrap Ingestion Engine
============================================================
Pulls multi-year historical OHLCV data from Dhan API v2 across the equity universe 
and index underlyings, storing sanitized bars into BigQuery `market_data.historical_ohlcv_backtest`.
"""

import os
import sys
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import httpx
import pandas as pd
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DhanHistoricalIngestion")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
ENGINE_C_URL = os.getenv("ENGINE_C_URL", "https://engine-c-r2f5flt77q-el.a.run.app")

# Universe Mapping
EQUITY_UNIVERSE = [
    {"symbol": "RELIANCE", "security_id": "2885", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "TCS", "security_id": "11536", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "HDFCBANK", "security_id": "1333", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "ICICIBANK", "security_id": "1594", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "INFY", "security_id": "4963", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "BHARTIARTL", "security_id": "10604", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "SBIN", "security_id": "3045", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "ITC", "security_id": "1660", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "LT", "security_id": "11723", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "HINDUNILVR", "security_id": "11483", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "TATAMOTORS", "security_id": "3456", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "AXISBANK", "security_id": "5900", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "KOTAKBANK", "security_id": "1922", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "M&M", "security_id": "2031", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "SUNPHARMA", "security_id": "3351", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "MARUTI", "security_id": "10999", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "NTPC", "security_id": "11630", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "BAJFINANCE", "security_id": "317", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "TITAN", "security_id": "3506", "segment": "NSE_EQ", "instrument": "EQUITY"},
    {"symbol": "LICI", "security_id": "1394", "segment": "NSE_EQ", "instrument": "EQUITY"},
]

INDEX_UNIVERSE = [
    {"symbol": "NIFTY", "security_id": "13", "segment": "IDX_I", "instrument": "INDEX"},
    {"symbol": "BANKNIFTY", "security_id": "25", "segment": "IDX_I", "instrument": "INDEX"},
    {"symbol": "FINNIFTY", "security_id": "27", "segment": "IDX_I", "instrument": "INDEX"},
    {"symbol": "SENSEX", "security_id": "51", "segment": "IDX_I", "instrument": "INDEX"},
]

TABLE_ID = f"{PROJECT_ID}.market_data.historical_ohlcv_backtest"

def ensure_bigquery_table(bq_client: bigquery.Client):
    """Creates the historical OHLCV BigQuery table if not present."""
    schema = [
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("security_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("exchange_segment", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("instrument_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("bar_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("timestamp_epoch", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("open", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("high", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("low", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("close", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("volume", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
    ]

    table = bigquery.Table(TABLE_ID, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="bar_date"
    )
    table.clustering_fields = ["symbol", "exchange_segment"]
    bq_client.create_table(table, exists_ok=True)
    logger.info(f"✅ BigQuery table verified: {TABLE_ID}")

def fetch_symbol_history(
    symbol_info: Dict[str, str],
    from_date: str = "2024-01-01",
    to_date: str = "2026-08-31"
) -> List[Dict[str, Any]]:
    """Fetches historical bars for a single instrument from Engine C gateway."""
    url = f"{ENGINE_C_URL}/api/dhan/market/historical"
    params = {
        "security_id": symbol_info["security_id"],
        "exchange_segment": symbol_info["segment"],
        "instrument_type": symbol_info["instrument"],
        "from_date": from_date,
        "to_date": to_date,
        "interval": "daily"
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                logger.error(f"❌ Failed to fetch {symbol_info['symbol']} ({resp.status_code}): {resp.text[:200]}")
                return []

            raw = resp.json()
            data_outer = raw.get("data", {})
            data_dict = data_outer.get("data", {}) if isinstance(data_outer, dict) and "data" in data_outer else (data_outer if isinstance(data_outer, dict) else {})
            
            if not isinstance(data_dict, dict) or "open" not in data_dict:
                logger.warning(f"⚠️ No OHLCV bars found for {symbol_info['symbol']}")
                return []

            opens = data_dict.get("open", [])
            highs = data_dict.get("high", [])
            lows = data_dict.get("low", [])
            closes = data_dict.get("close", [])
            volumes = data_dict.get("volume", [0.0] * len(opens))
            timestamps = data_dict.get("timestamp", data_dict.get("start_Time", []))

            rows = []
            now_ts = datetime.now(timezone.utc).isoformat()

            for i in range(len(opens)):
                ts_val = timestamps[i] if i < len(timestamps) else 0.0
                dt_obj = datetime.fromtimestamp(ts_val, tz=timezone.utc) if ts_val > 1000000 else datetime.strptime(from_date, "%Y-%m-%d")
                bar_date = dt_obj.strftime("%Y-%m-%d")

                rows.append({
                    "symbol": symbol_info["symbol"],
                    "security_id": symbol_info["security_id"],
                    "exchange_segment": symbol_info["segment"],
                    "instrument_type": symbol_info["instrument"],
                    "bar_date": bar_date,
                    "timestamp_epoch": float(ts_val),
                    "open": float(opens[i]),
                    "high": float(highs[i]),
                    "low": float(lows[i]),
                    "close": float(closes[i]),
                    "volume": float(volumes[i]) if i < len(volumes) and volumes[i] is not None else 0.0,
                    "ingested_at": now_ts
                })

            logger.info(f"📊 {symbol_info['symbol']} ({symbol_info['instrument']}): Fetched {len(rows)} daily bars.")
            return rows

    except Exception as e:
        logger.error(f"❌ Exception fetching {symbol_info['symbol']}: {e}")
        return []

def run_bootstrap_ingestion(from_date: str = "2024-01-01", to_date: str = "2026-08-31"):
    """Runs complete historical bootstrap across equities and indices."""
    bq_client = bigquery.Client(project=PROJECT_ID)
    ensure_bigquery_table(bq_client)

    all_instruments = EQUITY_UNIVERSE + INDEX_UNIVERSE
    logger.info(f"🚀 Starting Dhan Historical Bootstrap for {len(all_instruments)} instruments ({from_date} -> {to_date})...")

    all_rows = []
    for idx, item in enumerate(all_instruments, start=1):
        logger.info(f"[{idx}/{len(all_instruments)}] Fetching {item['symbol']} ({item['security_id']})...")
        rows = fetch_symbol_history(item, from_date=from_date, to_date=to_date)
        if rows:
            all_rows.extend(rows)
        # Strict Dhan 1 req/sec rate limit throttle
        time.sleep(1.05)

    if not all_rows:
        logger.error("❌ No rows collected. Aborting BigQuery insertion.")
        return 0

    df = pd.DataFrame(all_rows)
    df["bar_date"] = pd.to_datetime(df["bar_date"]).dt.date
    df["ingested_at"] = pd.to_datetime(df["ingested_at"])

    logger.info(f"💾 Ingesting {len(df):,} total historical bars into {TABLE_ID} via BigQuery staging...")
    
    # Use load_table_from_dataframe with write_disposition WRITE_TRUNCATE or WRITE_APPEND
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    load_job = bq_client.load_table_from_dataframe(df, TABLE_ID, job_config=job_config)
    load_job.result()

    logger.info(f"🎉 Dhan Historical Bootstrap Complete! Ingested {len(df):,} rows into {TABLE_ID}.")
    return len(df)

if __name__ == "__main__":
    run_bootstrap_ingestion()
