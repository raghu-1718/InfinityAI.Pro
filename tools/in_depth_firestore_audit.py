"""
In-Depth Firestore Ledger & Telemetry Analytics Script
InfinityAI.Pro - Institutional System Health, Signal & Performance Audit
"""
import os
import sys
import json
from datetime import datetime, timezone
from google.cloud import firestore

def main():
    project_id = "project-841b7f97-5ee3-4fbe-920"
    db = firestore.Client(project=project_id)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "collections": {},
        "summary": {}
    }

    # 1. AI Signals Ledger
    print("Fetching 'ai_signals_ledger'...")
    signals_docs = list(db.collection("ai_signals_ledger").stream())
    signals_list = [d.to_dict() for d in signals_docs]
    report["collections"]["ai_signals_ledger_count"] = len(signals_list)

    total_signals = len(signals_list)
    resolved_signals = [s for s in signals_list if s.get("outcome_status") not in [None, "OPEN", "PENDING"]]
    open_signals = [s for s in signals_list if s.get("outcome_status") in [None, "OPEN", "PENDING"]]
    winning_signals = [s for s in resolved_signals if float(s.get("net_pnl", 0.0)) > 0]
    losing_signals = [s for s in resolved_signals if float(s.get("net_pnl", 0.0)) <= 0]

    total_net_pnl = sum(float(s.get("net_pnl", 0.0)) for s in resolved_signals)
    total_gross_pnl = sum(float(s.get("gross_pnl", 0.0)) for s in resolved_signals)
    win_rate = (len(winning_signals) / len(resolved_signals) * 100) if resolved_signals else 0.0

    # Decision Breakdown
    call_signals = [s for s in signals_list if "CALL" in s.get("decision", "").upper()]
    put_signals = [s for s in signals_list if "PUT" in s.get("decision", "").upper()]

    report["summary"]["signals"] = {
        "total_generated": total_signals,
        "open_count": len(open_signals),
        "resolved_count": len(resolved_signals),
        "winning_count": len(winning_signals),
        "losing_count": len(losing_signals),
        "win_rate_pct": round(win_rate, 2),
        "total_gross_pnl": round(total_gross_pnl, 2),
        "total_net_pnl": round(total_net_pnl, 2),
        "call_signals_count": len(call_signals),
        "put_signals_count": len(put_signals),
        "recent_5_signals": signals_list[:5]
    }

    # 2. Real-time Macro Stream
    print("Fetching 'realtime_macro_stream'...")
    macro_docs = list(db.collection("realtime_macro_stream").stream())
    report["collections"]["realtime_macro_stream"] = [d.to_dict() for d in macro_docs]

    # 3. EOD Trading Journal
    print("Fetching 'eod_trading_journal'...")
    eod_docs = list(db.collection("eod_trading_journal").stream())
    report["collections"]["eod_trading_journal"] = [d.to_dict() for d in eod_docs]

    # 4. Circuit Breaker State
    print("Fetching 'circuit_breaker' & 'circuit_breaker_state'...")
    cb_docs = list(db.collection("circuit_breaker").stream()) + list(db.collection("circuit_breaker_state").stream())
    report["collections"]["circuit_breaker"] = [d.to_dict() for d in cb_docs]

    # 5. Premarket Macro Reports
    print("Fetching 'premarket_macro_reports'...")
    pm_docs = list(db.collection("premarket_macro_reports").stream())
    report["collections"]["premarket_macro_reports"] = [d.to_dict() for d in pm_docs]

    # 6. Model Retraining Runs & Metadata
    print("Fetching 'model_retraining_runs' & 'model_metadata'...")
    retrain_docs = list(db.collection("model_retraining_runs").stream())
    model_meta_docs = list(db.collection("model_metadata").stream())
    report["collections"]["model_retraining_runs"] = [d.to_dict() for d in retrain_docs]
    report["collections"]["model_metadata"] = [d.to_dict() for d in model_meta_docs]

    # 7. Options Volatility Surface
    print("Fetching 'options_volatility_surface'...")
    iv_docs = list(db.collection("options_volatility_surface").stream())
    report["collections"]["options_volatility_surface_count"] = len(iv_docs)
    report["collections"]["options_volatility_surface_sample"] = [d.to_dict() for d in iv_docs[:3]]

    # 8. User Credentials & Sessions
    print("Fetching 'user_credentials' & 'trading_sessions'...")
    user_cred_docs = list(db.collection("user_credentials").stream())
    session_docs = list(db.collection("trading_sessions").stream())
    report["collections"]["user_credentials_count"] = len(user_cred_docs)
    report["collections"]["trading_sessions_count"] = len(session_docs)

    # Save to JSON file
    out_path = os.path.join(os.path.dirname(__file__), "firestore_audit_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n[OK] Firestore Audit Saved to {out_path}")
    print(f"Total Signals: {total_signals} | Resolved: {len(resolved_signals)} | Win Rate: {win_rate:.1f}% | Net PnL: INR {total_net_pnl:+,.2f}")
    if report["collections"]["realtime_macro_stream"]:
        print(f"Active Macro Bias: {report['collections']['realtime_macro_stream'][0].get('regime_status')} (Scalar: {report['collections']['realtime_macro_stream'][0].get('sentiment_scalar')})")


if __name__ == "__main__":
    main()
