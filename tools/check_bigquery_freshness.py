"""
BigQuery Data Freshness & Retraining Audit Script
InfinityAI.Pro - Exact Telemetry & Dataset Verification
"""
from google.cloud import bigquery
import json

def check_freshness():
    project_id = "project-841b7f97-5ee3-4fbe-920"
    client = bigquery.Client(project=project_id)

    print("=== 1. market_data.live_ticks (PubSub Stream in asia-south1) ===")
    try:
        q1 = f"SELECT COUNT(*) as total_rows, MIN(publish_time) as min_ts, MAX(publish_time) as max_ts FROM `{project_id}.market_data.live_ticks`"
        for r in client.query(q1, location="asia-south1").result():
            print(f"  Total Rows: {r.total_rows}")
            print(f"  Earliest Publish Time: {r.min_ts}")
            print(f"  Latest Publish Time  : {r.max_ts}")

        q1_samples = f"SELECT publish_time, data FROM `{project_id}.market_data.live_ticks` ORDER BY publish_time DESC LIMIT 3"
        print("  Recent streaming samples:")
        for r in client.query(q1_samples, location="asia-south1").result():
            print(f"    [{r.publish_time}] Data: {r.data[:100]}...")
    except Exception as e:
        print(f"  Query Error: {e}")

    print("\n=== 2. infinity_dataset.market_ticks_history (ML Dataset) ===")
    try:
        q2 = f"""
        SELECT 
            COUNT(*) as total_rows, 
            MIN(timestamp) as min_ts, 
            MAX(timestamp) as max_ts,
            COUNT(DISTINCT DATE(timestamp)) as unique_days
        FROM `{project_id}.infinity_dataset.market_ticks_history`
        """
        for r in client.query(q2).result():
            print(f"  Total Rows: {r.total_rows:,}")
            print(f"  Unique Trading Days: {r.unique_days}")
            print(f"  Earliest Timestamp: {r.min_ts}")
            print(f"  Latest Timestamp  : {r.max_ts}")

        q2_recent = f"""
        SELECT DATE(timestamp) as dt, COUNT(*) as cnt, AVG(rsi_14) as avg_rsi
        FROM `{project_id}.infinity_dataset.market_ticks_history`
        GROUP BY dt
        ORDER BY dt DESC
        LIMIT 7
        """
        print("  Recent Trading Dates in ML Dataset:")
        for r in client.query(q2_recent).result():
            print(f"    Date: {r.dt} -> {r.cnt:,} rows | Avg RSI: {r.avg_rsi:.1f}")
    except Exception as e:
        print(f"  Query Error: {e}")

if __name__ == "__main__":
    check_freshness()
