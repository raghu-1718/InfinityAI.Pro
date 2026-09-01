"""
Unified Multi-Asset Accuracy Verification & SRE Report Engine
InfinityAI.Pro - Institutional Algorithmic Trading Platform
Computes segregated and combined accuracy metrics for:
1. Equities Pipeline (Firestore `equity_signals_ledger` & BigQuery `market_data.equity_signals`)
2. Options Tri-Model Pipeline (Firestore `ai_signals_ledger`)
3. Overall Unified System Accuracy Report with manual mathematical verification.
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

from google.cloud import firestore, bigquery
from google.cloud.firestore_v1.base_query import FieldFilter

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")

def compute_equity_accuracy(db: firestore.Client, bq_client: bigquery.Client) -> Dict[str, Any]:
    """Computes full performance analytics for Equities Pipeline"""
    docs = list(db.collection("equity_signals_ledger").order_by("scan_timestamp", direction=firestore.Query.DESCENDING).stream())
    total_scanned = len(docs)
    
    open_count = 0
    target_hits = 0
    stopped_out = 0
    expired = 0
    
    total_returns_pct = 0.0
    win_returns_pct = 0.0
    loss_returns_pct = 0.0
    time_to_target_total_sec = 0
    time_to_target_count = 0

    records_sample = []

    for d in docs:
        data = d.to_dict()
        status = data.get("status", "OPEN")
        ret_pct = data.get("returns_pct")
        time_sec = data.get("time_to_target_seconds")
        buy_p = float(data.get("buy_price", 0.0))
        exit_p = float(data.get("actual_exit_price") or 0.0)

        if status == "OPEN":
            open_count += 1
        elif status == "TARGET_HIT":
            target_hits += 1
            if ret_pct is not None:
                total_returns_pct += ret_pct
                win_returns_pct += ret_pct
            if time_sec is not None and time_sec > 0:
                time_to_target_total_sec += time_sec
                time_to_target_count += 1
        elif status == "STOPPED_OUT":
            stopped_out += 1
            if ret_pct is not None:
                total_returns_pct += ret_pct
                loss_returns_pct += ret_pct
        elif status == "EXPIRED":
            expired += 1
            if ret_pct is not None:
                total_returns_pct += ret_pct

        records_sample.append({
            "signal_id": d.id,
            "symbol": data.get("symbol"),
            "buy_price": buy_p,
            "target_price": data.get("target_price"),
            "stop_loss_price": data.get("stop_loss_price"),
            "exit_price": exit_p,
            "status": status,
            "returns_pct": ret_pct,
            "time_to_target": data.get("time_to_target_str") or "N/A"
        })

    closed_count = target_hits + stopped_out + expired
    win_rate = (target_hits / closed_count * 100) if closed_count > 0 else 0.0
    loss_rate = (stopped_out / closed_count * 100) if closed_count > 0 else 0.0
    avg_return_closed = (total_returns_pct / closed_count) if closed_count > 0 else 0.0
    avg_win_return = (win_returns_pct / target_hits) if target_hits > 0 else 0.0
    avg_loss_return = (loss_returns_pct / stopped_out) if stopped_out > 0 else 0.0
    avg_time_to_target_sec = int(time_to_target_total_sec / time_to_target_count) if time_to_target_count > 0 else 0

    # BigQuery row count check
    bq_count_query = f"SELECT COUNT(*) AS total_rows FROM `{PROJECT_ID}.market_data.equity_signals`"
    try:
        bq_res = list(bq_client.query(bq_count_query).result())
        bq_rows = bq_res[0].total_rows if bq_res else 0
    except Exception:
        bq_rows = "N/A"

    return {
        "pipeline": "NSE Equities (NSE_EQ)",
        "total_scanned": total_scanned,
        "open_positions": open_count,
        "closed_positions": closed_count,
        "targets_hit": target_hits,
        "stopped_out": stopped_out,
        "expired": expired,
        "win_rate_pct": round(win_rate, 2),
        "loss_rate_pct": round(loss_rate, 2),
        "avg_return_pct": round(avg_return_closed, 2),
        "avg_win_return_pct": round(avg_win_return, 2),
        "avg_loss_return_pct": round(avg_loss_return, 2),
        "avg_time_to_target_seconds": avg_time_to_target_sec,
        "avg_time_to_target_str": f"{avg_time_to_target_sec // 60}m {avg_time_to_target_sec % 60}s" if avg_time_to_target_sec > 0 else "N/A",
        "bigquery_synced_rows": bq_rows,
        "sample_records": records_sample[:10]
    }

def compute_options_accuracy(db: firestore.Client) -> Dict[str, Any]:
    """Computes performance analytics for Options Tri-Model Pipeline"""
    docs = list(db.collection("ai_signals_ledger").order_by("timestamp_utc", direction=firestore.Query.DESCENDING).limit(100).stream())
    total_signals = len(docs)

    wins = 0
    losses = 0
    open_count = 0
    total_net_pnl = 0.0
    total_roi_pct = 0.0
    closed_roi_count = 0

    for d in docs:
        data = d.to_dict()
        status = data.get("outcome_status", "OPEN")
        net_pnl = data.get("net_pnl")
        roi = data.get("roi_pct")

        if status in ["TARGET_HIT", "PROFIT_SECURED"]:
            wins += 1
            if net_pnl is not None:
                total_net_pnl += float(net_pnl)
            if roi is not None:
                total_roi_pct += float(roi)
                closed_roi_count += 1
        elif status in ["STOP_LOSS_HIT", "DYNAMIC_AI_RISK_EXIT", "INITIAL_STOP_LOSS_HIT"]:
            losses += 1
            if net_pnl is not None:
                total_net_pnl += float(net_pnl)
            if roi is not None:
                total_roi_pct += float(roi)
                closed_roi_count += 1
        elif status == "OPEN":
            open_count += 1

    closed = wins + losses
    win_rate = (wins / closed * 100) if closed > 0 else 0.0
    avg_roi = (total_roi_pct / closed_roi_count) if closed_roi_count > 0 else 0.0

    return {
        "pipeline": "NSE/BSE Index Options (ATM Intraday)",
        "total_signals": total_signals,
        "open_positions": open_count,
        "closed_positions": closed,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(win_rate, 2),
        "total_net_pnl_inr": round(total_net_pnl, 2),
        "avg_roi_pct": round(avg_roi, 2)
    }

def print_unified_accuracy_report():
    print(f"Connecting to Firestore and BigQuery for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    bq_client = bigquery.Client(project=PROJECT_ID)

    eq_report = compute_equity_accuracy(db, bq_client)
    opt_report = compute_options_accuracy(db)

    print("\n" + "="*80)
    print("      INFINITYAI.PRO -- INSTITUTIONAL MULTI-ASSET ACCURACY REPORT")
    print("="*80)
    
    print("\n[PIPELINE 1: EQUITIES ANALYSIS & TARGET TRACKING]")
    print(f"  * Total Signals Scanned:       {eq_report['total_scanned']}")
    print(f"  * Open Live Positions:         {eq_report['open_positions']}")
    print(f"  * Resolved / Closed Trades:    {eq_report['closed_positions']}")
    print(f"  * Target Hits (Profit):        {eq_report['targets_hit']}")
    print(f"  * Stopped Out (Risk Exit):     {eq_report['stopped_out']}")
    print(f"  * Expired Signals:             {eq_report['expired']}")
    print(f"  * Win Rate (Target Hit Ratio): {eq_report['win_rate_pct']}%")
    print(f"  * Average Closed Trade Return: {eq_report['avg_return_pct']:+}%")
    print(f"  * Average Win Return:          {eq_report['avg_win_return_pct']:+}%")
    print(f"  * Average Loss Return:         {eq_report['avg_loss_return_pct']:+}%")
    print(f"  * Average Time to Target:      {eq_report['avg_time_to_target_str']}")
    print(f"  * BigQuery Mirrored Rows:      {eq_report['bigquery_synced_rows']}")

    print("\n[PIPELINE 2: INDEX OPTIONS SHADOW LEDGER]")
    print(f"  * Total Evaluated Signals:     {opt_report['total_signals']}")
    print(f"  * Open Live Positions:         {opt_report['open_positions']}")
    print(f"  * Resolved Trades:             {opt_report['closed_positions']}")
    print(f"  * Target Hits (Profit):        {opt_report['wins']}")
    print(f"  * Dynamic Risk / SL Exits:     {opt_report['losses']}")
    print(f"  * Win Rate:                    {opt_report['win_rate_pct']}%")
    print(f"  * Net Realized P&L:            Rs {opt_report['total_net_pnl_inr']:+,.2f}")
    print(f"  * Average ROI per Trade:       {opt_report['avg_roi_pct']:+}%")

    print("\n[COMBINED INSTITUTIONAL SYSTEM ACCURACY SUMMARY]")
    total_sys_signals = eq_report['total_scanned'] + opt_report['total_signals']
    total_sys_closed = eq_report['closed_positions'] + opt_report['closed_positions']
    total_sys_wins = eq_report['targets_hit'] + opt_report['wins']
    combined_win_rate = (total_sys_wins / total_sys_closed * 100) if total_sys_closed > 0 else 0.0

    print(f"  * Combined Analyzed Setups:    {total_sys_signals}")
    print(f"  * Combined Closed Trades:      {total_sys_closed}")
    print(f"  * Combined Winning Trades:     {total_sys_wins}")
    print(f"  * Unified System Win Rate:     {combined_win_rate:.2f}%")

    print("\n" + "-"*80)
    print("RAW MATHEMATICAL VERIFICATION CHECK (EQUITY SAMPLE):")
    print("-"*80)
    for idx, rec in enumerate(eq_report["sample_records"][:5]):
        b = rec['buy_price']
        e = rec['exit_price']
        calc_ret = round((e - b) / b * 100, 2) if (b > 0 and e > 0) else None
        print(f"[{idx+1:02d}] {rec['signal_id']} | {rec['symbol']:<10} | Status: {rec['status']:<11} | Buy: Rs {b:.2f} -> Exit: Rs {e:.2f} | Recorded Ret: {rec['returns_pct']}% | Manual Calc: {calc_ret}% | Time: {rec['time_to_target']}")

    print("="*80 + "\n")

if __name__ == "__main__":
    print_unified_accuracy_report()
