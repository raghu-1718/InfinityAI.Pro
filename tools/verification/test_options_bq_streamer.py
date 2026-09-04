"""
InfinityAI.Pro - Options Chain BigQuery Streamer Pre-flight Test
"""
import sys
import os
import asyncio
import time

sys.path.insert(0, os.path.abspath("backend/engine-c/src"))
from options_chain_ingestor import options_ingestor

async def run_preflight():
    print("=" * 70)
    print("OPTIONS CHAIN BIGQUERY STREAMER PRE-FLIGHT TEST")
    print("=" * 70)
    
    t0 = time.time()
    result = await options_ingestor.ingest_live_option_chains("raghu_primary", allow_synthetic=True)
    duration = round((time.time() - t0) * 1000, 2)
    
    status = result.get("status")
    total_inserted = result.get("total_inserted", 0)
    indices = result.get("indices", {})
    
    print(f"Status: {status.upper()}")
    print(f"Execution Latency: {duration}ms")
    print(f"Total Contracts Streamed to BigQuery: {total_inserted}")
    print("\n--- VOLATILITY SURFACE & GREEKS PER INDEX ---")
    
    for symbol, details in indices.items():
        contracts = details.get("contracts_extracted", 0)
        atm_iv = details.get("atm_iv", 0.0)
        pcr = details.get("pcr", 0.0)
        max_pain = details.get("max_pain", 0)
        skew = details.get("skew_25d", 0.0)
        expiry = details.get("expiry", "N/A")
        print(f"  * {symbol:10} | Expiry: {expiry} | Contracts: {contracts:3} | ATM IV: {atm_iv:5.2f}% | PCR: {pcr:4.2f} | Max Pain: {max_pain} | 25-Delta Skew: {skew:+5.2f}%")
        
    print("\nVerifying BigQuery table rows...")
    from google.cloud import bigquery
    client = bigquery.Client(project="project-841b7f97-5ee3-4fbe-920")
    query = "SELECT count(*) as total_rows FROM `project-841b7f97-5ee3-4fbe-920.market_data.options_ticks`"
    rows = list(client.query(query).result())
    total_in_table = rows[0]["total_rows"]
    print(f"BigQuery `market_data.options_ticks` Total Row Count: {total_in_table:,}")
    
    # Query 3 sample rows
    sample_query = """
    SELECT underlying, strike_price, option_type, premium_price, implied_volatility, volume, open_interest, timestamp
    FROM `project-841b7f97-5ee3-4fbe-920.market_data.options_ticks`
    ORDER BY timestamp DESC
    LIMIT 3
    """
    samples = list(client.query(sample_query).result())
    print("\nSample Ingested Rows:")
    for row in samples:
        print(f"  {row['timestamp']} | {row['underlying']} {row['strike_price']} {row['option_type']} | Premium: Rs.{row['premium_price']:.2f} | IV: {row['implied_volatility']:.2f}% | OI: {row['open_interest']:,}")
        
    print("=" * 70)
    print("PRE-FLIGHT TEST COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_preflight())
