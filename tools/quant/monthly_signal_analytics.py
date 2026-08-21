import sys
import os
import json
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from google.cloud import firestore

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
COLLECTION_NAME = "ai_signals_ledger"
BASE_CAPITAL = 30000.0  # ₹30,000 baseline capital

print("=" * 105)
print("📊 INFINITYAI.PRO — AUTONOMOUS SHADOW SIGNALS & MONTH-END QUANTITATIVE AUDIT")
print(f"Project: {PROJECT_ID} | Collection: {COLLECTION_NAME} | Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
print("=" * 105)

db = firestore.Client(project=PROJECT_ID)
docs = list(db.collection(COLLECTION_NAME).stream())

print(f"\n[Telemetry Ingestion] Retrieved {len(docs)} total shadow signals from Firestore.")

if len(docs) == 0:
    if os.getenv("ALLOW_DEMO_LEDGER_SEED", "false").lower() == "true":
        print("ℹ️ No shadow signals recorded yet. Demo seed explicitly enabled via ALLOW_DEMO_LEDGER_SEED=true.")
        # Demo seed only when explicitly enabled (prevents accidental synthetic production telemetry)
        from services.shadow_signal_logger import ShadowSignalLogger
        logger_svc = ShadowSignalLogger(project_id=PROJECT_ID)

        sample_signals = [
            ("NIFTY", 24230.50, "BUY_CALL", 0.64, 0.65, 0.63, 0.64, "BULLISH (+0.75)", 65),
            ("BANKNIFTY", 52350.00, "BUY_CALL", 0.66, 0.68, 0.65, 0.65, "BULLISH (+0.80)", 30),
            ("FINNIFTY", 23150.25, "BUY_PUT", 0.38, 0.35, 0.40, 0.39, "BEARISH (-0.60)", 60),
            ("NIFTY", 24190.00, "BUY_PUT", 0.39, 0.37, 0.41, 0.39, "BEARISH (-0.55)", 65),
            ("BANKNIFTY", 52480.00, "BUY_CALL", 0.62, 0.63, 0.61, 0.62, "BULLISH (+0.60)", 30)
        ]
        for sym, spot, dec, conf, cb, lgb, xg, gem, lot in sample_signals:
            sig = logger_svc.log_shadow_signal(
                symbol=sym, spot_price=spot, decision=dec, confidence_score=conf,
                catboost_prob=cb, lightgbm_prob=lgb, xgboost_prob=xg, gemini_sentiment=gem, lot_size=lot
            )
            if sig:
                mock_exit_spot = spot * (1.008 if "CALL" in dec else 0.992)
                logger_svc.resolve_signal_outcome(sig["signal_id"], current_spot=mock_exit_spot, is_eod_squareoff=True)
        docs = list(db.collection(COLLECTION_NAME).stream())
    else:
        print("ℹ️ No shadow signals recorded yet. Demo seeding is disabled by default for production safety.")
        sys.exit(0)

records = []
for d in docs:
    data = d.to_dict()
    records.append({
        "Signal ID": data.get("signal_id"),
        "Date": data.get("date"),
        "Time (IST)": data.get("timestamp_ist", "")[-12:],
        "Symbol": data.get("symbol"),
        "Decision": data.get("decision"),
        "Confidence": f"{data.get('confidence_score', 0)*100:.1f}%",
        "Entry Prem": f"₹{data.get('trade_bracket', {}).get('entry_premium', 0):.2f}",
        "Exit Prem": f"₹{data.get('exit_premium', 0):.2f}" if data.get('exit_premium') else "Open",
        "Outcome": data.get("outcome_status", "OPEN"),
        "Gross PnL": data.get("gross_pnl") if data.get("gross_pnl") is not None else 0.0,
        "Taxes": data.get("estimated_tax_brokerage", 55.0),
        "Net PnL": data.get("net_pnl") if data.get("net_pnl") is not None else 0.0
    })

df_all = pd.DataFrame(records)

# 1. Individual Signal Log Table
print("\n" + "█" * 105)
print(" 1. RECENT SHADOW SIGNALS LOG (FIRESTORE TELEMETRY VAULT)".center(105))
print("█" * 105)

display_df = df_all[["Date", "Time (IST)", "Symbol", "Decision", "Confidence", "Entry Prem", "Exit Prem", "Outcome", "Net PnL"]].copy()
display_df["Net PnL"] = display_df["Net PnL"].apply(lambda x: f"₹{x:+,.2f}" if x != 0 else "₹0.00")
print(display_df.to_markdown(index=False))

# 2. Performance Aggregation by Index
print("\n" + "█" * 105)
print(" 2. MONTH-END AGGREGATE PERFORMANCE METRICS (₹30,000 CAPITAL BASELINE)".center(105))
print("█" * 105)

summary_rows = []
for symbol in df_all["Symbol"].unique():
    sub = df_all[df_all["Symbol"] == symbol]
    resolved = sub[sub["Outcome"] != "OPEN"]
    wins = len(resolved[resolved["Net PnL"] > 0])
    total_res = len(resolved)
    win_rate = (wins / total_res * 100) if total_res > 0 else 0.0
    gross_sum = sub["Gross PnL"].sum()
    tax_sum = sub["Taxes"].sum()
    net_sum = sub["Net PnL"].sum()
    roi = (net_sum / BASE_CAPITAL) * 100
    
    summary_rows.append({
        "Instrument": symbol,
        "Total Signals": len(sub),
        "Resolved Trades": total_res,
        "Win Rate (%)": f"{win_rate:.1f}%",
        "Gross PnL": f"₹{gross_sum:+,.2f}",
        "Dhan Taxes & Fees": f"₹{tax_sum:,.2f}",
        "Net PnL": f"₹{net_sum:+,.2f}",
        "ROI on ₹30k": f"{roi:+.2f}%"
    })

# Overall Total Row
tot_signals = len(df_all)
tot_resolved = len(df_all[df_all["Outcome"] != "OPEN"])
tot_wins = len(df_all[df_all["Net PnL"] > 0])
tot_winrate = (tot_wins / tot_resolved * 100) if tot_resolved > 0 else 0.0
tot_gross = df_all["Gross PnL"].sum()
tot_taxes = df_all["Taxes"].sum()
tot_net = df_all["Net PnL"].sum()
tot_roi = (tot_net / BASE_CAPITAL) * 100

summary_rows.append({
    "Instrument": "🔥 PORTFOLIO TOTAL",
    "Total Signals": tot_signals,
    "Resolved Trades": tot_resolved,
    "Win Rate (%)": f"{tot_winrate:.1f}%",
    "Gross PnL": f"₹{tot_gross:+,.2f}",
    "Dhan Taxes & Fees": f"₹{tot_taxes:,.2f}",
    "Net PnL": f"₹{tot_net:+,.2f}",
    "ROI on ₹30k": f"{tot_roi:+.2f}%"
})

df_sum = pd.DataFrame(summary_rows)
print(df_sum.to_markdown(index=False))

print("\n" + "=" * 105)
print(f"🎯 SUMMARY: Total Net PnL = ₹{tot_net:+,.2f} ({tot_roi:+.2f}% on ₹30k capital) across {tot_signals} automated signals!")
print("=" * 105)
