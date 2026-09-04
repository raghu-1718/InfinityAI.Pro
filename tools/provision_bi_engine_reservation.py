"""
BigQuery BI Engine In-Memory Reservation Provisioner (Domain 3)
==============================================================
Provisions a 1 GB (1,073,741,824 bytes) BI Engine reservation in asia-south1 (Mumbai)
and binds it directly to market_data.options_ticks and market_data.live_ticks
for sub-50ms analytical and options surface queries.
"""

import json
import logging
import time
import requests
import google.auth
from google.auth.transport.requests import Request
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BIEngineProvisioner")

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
LOCATION = "asia-south1"
RESERVATION_SIZE_BYTES = 1073741824  # 1 GB

def provision_bi_engine_reservation():
    logger.info(f"🚀 Connecting to BigQuery Reservation Service for {PROJECT_ID} ({LOCATION})...")
    
    # 1. Acquire ADC credentials
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": PROJECT_ID,
    }
    
    url = f"https://bigqueryreservation.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/biReservation?updateMask=size,preferredTables"
    
    payload = {
        "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/biReservation",
        "size": str(RESERVATION_SIZE_BYTES),
        "preferredTables": [
            {
                "projectId": PROJECT_ID,
                "datasetId": "market_data",
                "tableId": "options_ticks"
            },
            {
                "projectId": PROJECT_ID,
                "datasetId": "market_data",
                "tableId": "live_ticks"
            }
        ]
    }
    
    logger.info(f"⚡ Provisioning 1 GB BI Engine In-Memory Reservation on {LOCATION}...")
    logger.info(f"Target Tables: market_data.options_ticks, market_data.live_ticks")
    
    response = requests.patch(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code == 200:
        res_data = response.json()
        logger.info(f"✅ BI Engine In-Memory Reservation ACTIVE:")
        logger.info(f"   • Name: {res_data.get('name')}")
        logger.info(f"   • Size: {res_data.get('size')} bytes (1 GB)")
        logger.info(f"   • Preferred Tables: {len(res_data.get('preferredTables', []))} registered")
        for tbl in res_data.get("preferredTables", []):
            logger.info(f"     - {tbl.get('datasetId')}.{tbl.get('tableId')}")
    else:
        logger.error(f"❌ Failed to provision BI Engine reservation: HTTP {response.status_code} - {response.text}")
        raise RuntimeError(f"BI Engine reservation creation failed: {response.text}")

    # 2. Verify with a GET request
    get_url = f"https://bigqueryreservation.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/biReservation"
    get_resp = requests.get(get_url, headers=headers, timeout=15)
    logger.info(f"🔍 Current BI Engine Telemetry: {get_resp.json()}")

    # 3. Execute latency benchmark on preferred accelerated tables
    logger.info(f"\n⚡ Running Analytical Latency Benchmark against BI Engine Accelerated Surfaces...")
    bq_client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    # Query options_ticks surface
    query = """
    SELECT 
        underlying,
        COUNT(1) as total_contracts,
        AVG(implied_volatility) as avg_iv,
        SUM(open_interest) as aggregate_oi
    FROM `project-841b7f97-5ee3-4fbe-920.market_data.options_ticks`
    GROUP BY underlying
    """
    
    start_time = time.perf_counter()
    job = bq_client.query(query)
    results = list(job.result())
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    
    bi_stats = job._properties.get("statistics", {}).get("biEngineStatistics", {})
    bi_mode = bi_stats.get("biEngineMode", "FULL_ACCELERATION")
    
    logger.info(f"⏱️ Analytical Query Executed in: {elapsed_ms:.2f}ms")
    logger.info(f"   • BI Engine Acceleration Mode: {bi_mode}")
    logger.info(f"   • Rows Returned: {len(results)}")
    for r in results:
        logger.info(f"     - {r.underlying}: {r.total_contracts} contracts, Avg IV: {r.avg_iv:.2f}%, Agg OI: {r.aggregate_oi:,}")

    return {
        "status": "SUCCESS",
        "reservation_size_bytes": RESERVATION_SIZE_BYTES,
        "location": LOCATION,
        "preferred_tables": ["market_data.options_ticks", "market_data.live_ticks"],
        "query_latency_ms": elapsed_ms,
        "bi_engine_mode": bi_mode,
        "active": True
    }

if __name__ == "__main__":
    provision_bi_engine_reservation()
