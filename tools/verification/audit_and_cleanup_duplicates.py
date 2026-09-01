"""
Audit and Backfill Cleanup Script for Equity Signals Ledger
Identifies duplicate OPEN/SCANNED signals for the same symbol in Firestore `equity_signals_ledger`,
marks secondary duplicates as `CLOSED_DUPLICATE` with audit notes, and syncs to BigQuery.
"""

import os
from collections import defaultdict
from datetime import datetime, timezone
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "engine-a")))
from src.services.equity_bigquery_sync import EquityBigQuerySync

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
COLLECTION_NAME = "equity_signals_ledger"

def main():
    print("=" * 85)
    print("INFINITYAI.PRO - AUDIT & BACKFILL CLEANUP FOR DUPLICATE EQUITY SIGNALS")
    print("=" * 85)

    db = firestore.Client(project=PROJECT_ID)
    signals_ref = db.collection(COLLECTION_NAME)

    # 1. Fetch all OPEN or SCANNED signals
    print("\n[1] FETCHING ALL ACTIVE (OPEN/SCANNED) SIGNALS...")
    active_docs = list(
        signals_ref.where(filter=FieldFilter("status", "in", ["OPEN", "SCANNED"])).stream()
    )
    print(f"Total active documents found: {len(active_docs)}")

    symbol_map = defaultdict(list)
    for doc in active_docs:
        d = doc.to_dict()
        d["_doc_id"] = doc.id
        sym = d.get("symbol", "UNKNOWN")
        symbol_map[sym].append(d)

    print(f"Distinct symbols in active state: {len(symbol_map)}")

    # 2. Identify and resolve duplicates
    print("\n[2] AUDITING AND RESOLVING DUPLICATES...")
    duplicates_found = 0
    updated_signals = []

    for sym, doc_list in symbol_map.items():
        if len(doc_list) > 1:
            duplicates_found += (len(doc_list) - 1)
            print(f"\n[DUPLICATE DETECTED] Found {len(doc_list)} active signals for symbol [{sym}]:")
            
            # Sort by scan_timestamp descending (keep the latest/primary signal open)
            doc_list.sort(key=lambda x: x.get("scan_timestamp", ""), reverse=True)
            primary_doc = doc_list[0]
            duplicate_docs = doc_list[1:]

            print(f"   -> [KEEP OPEN] Primary: {primary_doc['_doc_id']} (Scanned: {primary_doc.get('scan_timestamp_ist', primary_doc.get('scan_timestamp'))})")

            now_iso = datetime.now(timezone.utc).isoformat()

            for dup in duplicate_docs:
                dup_id = dup["_doc_id"]
                update_payload = {
                    "status": "CLOSED_DUPLICATE",
                    "closed_at": now_iso,
                    "close_reason": f"DUPLICATE_SIGNAL_BACKFILL_AUDIT: Closed in favor of primary signal [{primary_doc['_doc_id']}]",
                    "returns_pct": 0.0,
                    "actual_exit_price": dup.get("buy_price")
                }
                signals_ref.document(dup_id).update(update_payload)
                print(f"   -> [MARKED CLOSED_DUPLICATE]: {dup_id}")
                dup.update(update_payload)
                updated_signals.append(dup)
        else:
            doc = doc_list[0]
            print(f"[OK] [{sym}] Single active signal: {doc['_doc_id']} @ Rs {doc.get('buy_price')}")

    print(f"\nTotal duplicate signals resolved: {duplicates_found}")

    # 3. Trigger BigQuery Sync
    if updated_signals:
        print("\n[3] SYNCING UPDATED RECORDS TO BIGQUERY...")
        try:
            from google.cloud import bigquery
            bq_sync = EquityBigQuerySync(project_id=PROJECT_ID)
            sync_res = bq_sync.sync_all_firestore_to_bigquery()
            print(f"BigQuery Sync Result: {sync_res}")
        except Exception as e:
            print(f"BigQuery sync warning: {e}")

    # 4. Final Verification Query
    print("\n[4] POST-CLEANUP VERIFICATION QUERY...")
    post_active = list(
        signals_ref.where(filter=FieldFilter("status", "in", ["OPEN", "SCANNED"])).stream()
    )
    post_map = defaultdict(list)
    for doc in post_active:
        d = doc.to_dict()
        post_map[d.get("symbol", "UNKNOWN")].append(doc.id)

    max_active_per_symbol = max([len(v) for v in post_map.values()]) if post_map else 0

    print(f"\n{'Symbol':<12} | {'Active Signals Count':<22} | {'Active Signal ID'}")
    print("-" * 75)
    for sym in sorted(post_map.keys()):
        sids = ", ".join(post_map[sym])
        print(f"{sym:<12} | {len(post_map[sym]):<22} | {sids}")

    print("-" * 75)
    print(f"Verification Result: Total Active = {len(post_active)}, Max per Symbol = {max_active_per_symbol}")
    if max_active_per_symbol <= 1:
        print("[SUCCESS] Zero concurrent duplicate active signals exist in Firestore!")
    else:
        print("[ERROR] Duplicates still detected.")
    print("=" * 85)

if __name__ == "__main__":
    main()
