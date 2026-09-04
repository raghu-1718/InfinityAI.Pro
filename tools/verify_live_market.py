import os
import time
from datetime import datetime, timedelta, timezone
from google.cloud import bigquery

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
DATASET_ID = "market_data"
TABLE_ID = "live_ticks"
POLL_INTERVAL_SECONDS = 10
MAX_DELAY_MINUTES = 2

def verify_live_market():
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    print(f"--- Monitoring Live Ticks: {table_ref} ---")
    
    try:
        query = f"""
        SELECT 
            MAX(publish_time) as latest_timestamp
        FROM `{table_ref}`
        """
        results = list(client.query(query).result())[0]
        latest_ts = results.latest_timestamp
        
        now = datetime.now(timezone.utc)
        if latest_ts:
            lag = now - latest_ts
            status = "ACTIVE" if lag < timedelta(minutes=MAX_DELAY_MINUTES) else f"DELAYED (Lag: {str(lag).split('.')[0]})"
            print(f"[{now.strftime('%H:%M:%S')}] Status: {status} | Last Tick: {latest_ts.strftime('%H:%M:%S UTC')}")
        else:
            print(f"[{now.strftime('%H:%M:%S')}] Table is currently empty.")
    except Exception as e:
        print(f"Error querying BigQuery: {e}")

if __name__ == "__main__":
    try:
        verify_live_market()
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
