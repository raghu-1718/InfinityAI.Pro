"""
InfinityAI.Pro - In-depth Real-Time Forensic Investigation of Today's Activity (2026-09-15)
Author: Senior Algorithmic Engineer, DevOps Engineer & GCP Cloud Architect
"""

import sys
import os
import json
import time
from datetime import datetime, timezone, timedelta
from google.cloud import firestore, bigquery
try:
    from google.cloud import logging_v2
except ImportError:
    logging_v2 = None

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")

def run_investigation():
    print("=" * 90)
    print("🔍 INFINITYAI.PRO - FORENSIC INVESTIGATION FOR TODAY (2026-09-15)")
    print("=" * 90)

    db = firestore.Client(project=PROJECT_ID)
    bq = bigquery.Client(project=PROJECT_ID)

    # -------------------------------------------------------------
    # 1. Inspect Premarket Macro Report & Live Macro Prior for Today
    # -------------------------------------------------------------
    print("\n--- 1. PREMARKET REPORT & MACRO REGIME FOR TODAY ---")
    pm_ref = db.collection("premarket_macro_reports").document("PREMARKET_20260915")
    pm_doc = pm_ref.get()
    if pm_doc.exists:
        pm_data = pm_doc.to_dict()
        print("✅ PREMARKET_20260915 exists!")
        print(f"   Timestamp: {pm_data.get('timestamp')}")
        print(f"   Macro Regime: {pm_data.get('macro_regime')}")
        print(f"   Bias: {pm_data.get('macro_bias')}")
        print(f"   Composite Score: {pm_data.get('composite_score')}")
        print(f"   Regime Multiplier: {pm_data.get('regime_multiplier')}")
        print(f"   Headline Summary: {str(pm_data.get('headline_summary', pm_data.get('summary', '')))[:150]}")
    else:
        print("❌ PREMARKET_20260915 NOT found.")

    live_prior_ref = db.collection("market_regime_heartbeats").document("LIVE_MACRO_PRIOR")
    live_prior_doc = live_prior_ref.get()
    if live_prior_doc.exists:
        lp_data = live_prior_doc.to_dict()
        print("✅ LIVE_MACRO_PRIOR exists!")
        print(f"   Timestamp: {lp_data.get('timestamp')}")
        print(f"   Macro Regime: {lp_data.get('macro_regime')}")
        print(f"   Macro Bias: {lp_data.get('macro_bias')}")
        print(f"   Composite Score: {lp_data.get('composite_score')}")
    else:
        print("❌ LIVE_MACRO_PRIOR not found.")

    # -------------------------------------------------------------
    # 2. BigQuery Table Schemas & Recent Rows
    # -------------------------------------------------------------
    print("\n--- 2. BIGQUERY RECENT DATA & TABLE SCHEMAS ---")
    tables_to_inspect = ["market_data.live_ticks", "market_data.options_ticks", "market_data.equity_signals"]
    for t_name in tables_to_inspect:
        try:
            t = bq.get_table(f"{PROJECT_ID}.{t_name}")
            col_names = [f.name for f in t.schema]
            print(f"\nTable: {t_name}")
            print(f"   Columns: {col_names[:10]}")
            print(f"   Total Rows: {t.num_rows:,}")
            
            # Find timestamp column
            ts_col = next((c for c in col_names if "time" in c.lower() or "date" in c.lower() or "created" in c.lower()), None)
            if ts_col:
                q = f"SELECT max({ts_col}) as max_ts, min({ts_col}) as min_ts FROM `{PROJECT_ID}.{t_name}`"
                res = list(bq.query(q).result())
                if res:
                    print(f"   Time Range: {res[0]['min_ts']} to {res[0]['max_ts']}")
                
                # Check rows for today
                q_today = f"SELECT count(*) as today_cnt FROM `{PROJECT_ID}.{t_name}` WHERE {ts_col} >= '2026-09-15'"
                res_today = list(bq.query(q_today).result())
                if res_today:
                    print(f"   Rows Today (>= 2026-09-15): {res_today[0]['today_cnt']:,}")
        except Exception as e:
            print(f"   Error inspecting {t_name}: {e}")

    # -------------------------------------------------------------
    # 3. Cloud Logging: Engine A, B, C logs during Market Hours
    # -------------------------------------------------------------
    print("\n--- 3. CLOUD RUN LOGGING AUDIT (03:30 UTC to 10:30 UTC) ---")
    if logging_v2:
        try:
            log_client = logging_v2.Client(project=PROJECT_ID)
            # 03:30Z is 09:00 IST, 10:30Z is 16:00 IST
            log_filter = (
                'resource.type="cloud_run_revision" '
                'AND timestamp >= "2026-09-15T03:30:00Z" '
                'AND timestamp <= "2026-09-15T11:00:00Z"'
            )
            entries = list(log_client.list_entries(filter_=log_filter, max_results=60, order_by=logging_v2.DESCENDING))
            print(f"Found {len(entries)} Cloud Run log entries for today's market hours.")
            
            # Group by service
            services_seen = {}
            error_logs = []
            info_logs = []
            
            for e in entries:
                svc = e.resource.labels.get("service_name", "unknown")
                services_seen[svc] = services_seen.get(svc, 0) + 1
                msg = e.payload if isinstance(e.payload, str) else (e.payload.get("message") if isinstance(e.payload, dict) else str(e.payload))
                ts = e.timestamp.strftime("%H:%M:%S") if e.timestamp else ""
                
                if e.severity in ("ERROR", "CRITICAL", "WARNING"):
                    error_logs.append((ts, svc, e.severity, msg))
                else:
                    info_logs.append((ts, svc, msg))

            print(f"Service Activity Breakdown: {services_seen}")
            
            if error_logs:
                print(f"\n⚠️ Warnings / Errors Encountered Today ({len(error_logs)}):")
                for ts, svc, sev, msg in error_logs[:15]:
                    print(f"   [{ts} UTC] [{svc}] [{sev}] {str(msg)[:140]}")
            else:
                print("✅ Zero critical Cloud Run errors during market hours.")

            print(f"\nSample Operational Logs ({len(info_logs)}):")
            for ts, svc, msg in info_logs[:15]:
                print(f"   [{ts} UTC] [{svc}] {str(msg)[:140]}")

        except Exception as e:
            print(f"Cloud Logging error: {e}")
    else:
        print("google.cloud.logging_v2 not installed.")

    # -------------------------------------------------------------
    # 4. Scanner and Trade Signal Analysis
    # -------------------------------------------------------------
    print("\n--- 4. AUTONOMOUS SCANNER & TRI-MODEL DECISION AUDIT ---")
    # Let's check the logs or signals ledger for why no trades passed
    signals_ref = db.collection("signals")
    recent_signals = list(signals_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).stream())
    print(f"Recent Signals in 'signals' collection: {len(recent_signals)}")
    for s in recent_signals:
        s_data = s.to_dict()
        print(f"   Signal ID: {s.id} | Symbol: {s_data.get('symbol')} | Status: {s_data.get('status')} | Conf: {s_data.get('confidence')} | TS: {s_data.get('timestamp')}")

    ai_ledger = db.collection("ai_signals_ledger")
    recent_ai = list(ai_ledger.limit(10).stream())
    print(f"\nRecent in 'ai_signals_ledger': {len(recent_ai)}")
    for a in recent_ai:
        a_data = a.to_dict()
        print(f"   Doc ID: {a.id} | Symbol: {a_data.get('symbol')} | Status: {a_data.get('status')} | Unanimous: {a_data.get('unanimous')} | TS: {a_data.get('timestamp')}")

if __name__ == "__main__":
    run_investigation()
