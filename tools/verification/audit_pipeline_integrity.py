import os
from collections import defaultdict
from google.cloud import firestore, bigquery
import pandas as pd

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"

def run_audit():
    db = firestore.Client(project=PROJECT_ID)
    bq = bigquery.Client(project=PROJECT_ID)

    print("================================================================================")
    print("                INFINITYAI.PRO - SRE PIPELINE DATA INTEGRITY AUDIT              ")
    print("================================================================================\n")

    # 1. Firestore Active Signals Audit
    print(">>> 1. FIRESTORE ACTIVE SIGNALS AUDIT (status IN ['OPEN', 'SCANNED'])")
    active_docs = list(db.collection("equity_signals_ledger").where("status", "in", ["OPEN", "SCANNED"]).stream())
    
    symbol_map = defaultdict(list)
    for doc in active_docs:
        d = doc.to_dict()
        symbol_map[d.get("symbol")].append({
            "id": doc.id,
            "status": d.get("status"),
            "created_at": str(d.get("created_at")),
            "buy_price": d.get("buy_price")
        })

    print(f"| {'Symbol':<15} | {'Active Count':<12} | {'Status':<10} | {'Document ID':<35} |")
    print(f"| {':---':<15} | {':---':<12} | {':---':<10} | {':---':<35} |")
    has_duplicates = False
    for sym, items in sorted(symbol_map.items()):
        cnt = len(items)
        if cnt > 1:
            has_duplicates = True
        doc_ids = ", ".join(x["id"] for x in items)
        statuses = ", ".join(x["status"] for x in items)
        print(f"| {sym:<15} | {cnt:<12} | {statuses:<10} | {doc_ids:<35} |")

    print(f"\n[FIRESTORE VERIFICATION] Total Active Signals: {len(active_docs)} across {len(symbol_map)} unique symbols.")
    print(f"[FIRESTORE VERIFICATION] Any Symbol with >1 Concurrent Active Signal: {has_duplicates} (PASS = False)\n")

    # 2. Closed Duplicate Signals Audit
    print(">>> 2. FIRESTORE CLOSED_DUPLICATE AUDIT (Audit Backfill Cleanup)")
    dup_docs = list(db.collection("equity_signals_ledger").where("status", "==", "CLOSED_DUPLICATE").stream())
    print(f"Total CLOSED_DUPLICATE Records: {len(dup_docs)}")
    for doc in dup_docs:
        d = doc.to_dict()
        print(f"  - Document ID: {doc.id}")
        print(f"    Symbol:      {d.get('symbol')}")
        print(f"    Status:      {d.get('status')}")
        print(f"    Close Reason:{d.get('close_reason')}\n")

    # 3. BigQuery Synchronization Audit
    print(">>> 3. BIGQUERY RECONCILIATION AUDIT (market_data.equity_signals)")
    bq_sql = f"""
    SELECT 
        symbol, 
        COUNTIF(status IN ('OPEN', 'SCANNED')) as active_count,
        COUNTIF(status = 'CLOSED_DUPLICATE') as duplicate_count,
        COUNTIF(status NOT IN ('OPEN', 'SCANNED', 'CLOSED_DUPLICATE')) as other_count,
        COUNT(*) as total_records
    FROM `{PROJECT_ID}.market_data.equity_signals`
    GROUP BY symbol
    ORDER BY symbol
    """
    df_bq = bq.query(bq_sql).to_dataframe()
    print(f"| {'symbol':<15} | {'active_count':<12} | {'duplicate_count':<15} | {'other_count':<11} | {'total_records':<13} |")
    print(f"| {':---':<15} | {':---':<12} | {':---':<15} | {':---':<11} | {':---':<13} |")
    for _, row in df_bq.iterrows():
        print(f"| {row['symbol']:<15} | {row['active_count']:<12} | {row['duplicate_count']:<15} | {row['other_count']:<11} | {row['total_records']:<13} |")

    total_bq = df_bq['total_records'].sum()
    total_active_bq = df_bq['active_count'].sum()
    total_dup_bq = df_bq['duplicate_count'].sum()
    print(f"\n[BIGQUERY VERIFICATION] Total Synchronized Rows: {total_bq} | Active: {total_active_bq} | Duplicates: {total_dup_bq}")
    print("================================================================================\n")

if __name__ == "__main__":
    run_audit()
