"""
========================================================================================
INFINITYAI.PRO — INSTITUTIONAL FIRESTORE QUANTITATIVE PERFORMANCE & ACCURACY ANALYZER
========================================================================================
Deeply audits and analyzes all live production trading records stored in Cloud Firestore:
1. Index Options Tri-Model Performance (`ai_signals_ledger` - 264 records)
2. 3-Tier Dynamic Trailing Stop-Loss Efficiency & Capital Preservation
3. Tri-Model Ensemble & Vertex Gemini Sentiment Calibration
4. NSE Equities Momentum Pipeline (`equity_signals_ledger` - 114 records)
5. EOD Journal Audit Trail & Portfolio Statistics (`eod_trading_journal`)
6. Signal Engine Filter & Market Chop Veto Analysis (`signals`)

Author: Senior Institutional Quant Engineer & GCP Cloud Architect
========================================================================================
"""

import sys
import os
import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np

# UTF-8 stdout encoding for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from google.cloud import firestore

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")


class InstitutionalFirestoreAnalyzer:
    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        self.db = firestore.Client(project=project_id)

    def analyze_options_ledger(self) -> Dict[str, Any]:
        """Deep analysis of all 264 Index Options records in `ai_signals_ledger`."""
        docs = list(self.db.collection("ai_signals_ledger").stream())
        signals = [d.to_dict() for d in docs]

        total_signals = len(signals)
        resolved_signals = []
        open_signals = []

        for s in signals:
            status = str(s.get("outcome_status", "")).upper()
            if status in ["TARGET_HIT", "STOP_LOSS_HIT", "CLOSED", "PROFIT_LOCK_HIT", "BREAKEVEN_HIT", "EXPIRED"]:
                resolved_signals.append(s)
            elif status in ["OPEN", "PENDING"]:
                open_signals.append(s)
            else:
                # Check if has realized PnL
                pnl = s.get("net_pnl") or s.get("gross_pnl")
                if pnl is not None and float(pnl) != 0.0:
                    resolved_signals.append(s)
                else:
                    open_signals.append(s)

        # Metrics accumulator
        winning_trades = []
        losing_trades = []
        breakeven_trades = []
        
        gross_pnls = []
        net_pnls = []
        roi_pcts = []
        mfe_excursions = []
        mae_excursions = []

        # 3-Tier Trailing SL Tracker
        trailing_active_count = 0
        tier_1_breakeven_locks = 0
        tier_2_profit_locks = 0
        tier_3_dynamic_trails = 0
        target_reaches = 0
        stop_loss_hits = 0

        # Model Consensus Tracker
        tri_consensus_total = 0
        tri_consensus_wins = 0
        gemini_aligned_total = 0
        gemini_aligned_wins = 0
        brier_scores = []

        # Instrument & Directional Breakdown
        symbol_stats = {}
        direction_stats = {"CE": {"wins": 0, "total": 0, "net_pnl": 0.0}, "PE": {"wins": 0, "total": 0, "net_pnl": 0.0}}

        for s in resolved_signals:
            net_pnl = float(s.get("net_pnl", 0.0) or 0.0)
            gross_pnl = float(s.get("gross_pnl", 0.0) or 0.0)
            gross_pnls.append(gross_pnl)
            net_pnls.append(net_pnl)

            tb = s.get("trade_bracket", {})
            entry_prem = float(tb.get("entry_premium", 0.0) or s.get("current_mtm_premium", 0.0) or 1.0)
            exit_prem = float(s.get("exit_premium", 0.0) or s.get("highest_observed_premium", entry_prem))
            highest_prem = float(s.get("highest_observed_premium", exit_prem) or exit_prem)
            stop_prem = float(tb.get("stop_loss_premium", 0.0) or (entry_prem * 0.88))

            # MFE & MAE Excursions
            if entry_prem > 0:
                mfe = ((highest_prem - entry_prem) / entry_prem) * 100.0
                mfe_excursions.append(mfe)
                mae = ((entry_prem - stop_prem) / entry_prem) * 100.0
                mae_excursions.append(mae)
                roi = ((exit_prem - entry_prem) / entry_prem) * 100.0
                roi_pcts.append(roi)

            # Win / Loss categorization
            if net_pnl > 10.0:
                winning_trades.append(s)
            elif net_pnl < -10.0:
                losing_trades.append(s)
            else:
                breakeven_trades.append(s)

            # Trailing SL metrics
            outcome = str(s.get("outcome_status", "")).upper()
            settlement = str(s.get("settlement_type", "")).upper()
            
            if tb.get("trailing_stop_loss_active"):
                trailing_active_count += 1

            if "TARGET" in outcome or "TARGET" in settlement:
                target_reaches += 1
                tier_1_breakeven_locks += 1
                tier_2_profit_locks += 1
                tier_3_dynamic_trails += 1
            elif "STOP" in outcome or "STOP" in settlement:
                stop_loss_hits += 1
            elif "BREAKEVEN" in outcome or "BREAKEVEN" in settlement:
                tier_1_breakeven_locks += 1
            elif "PROFIT_LOCK" in outcome or "PROFIT_LOCK" in settlement:
                tier_1_breakeven_locks += 1
                tier_2_profit_locks += 1
            elif mfe >= 15.0:
                tier_1_breakeven_locks += 1
                tier_2_profit_locks += 1
                tier_3_dynamic_trails += 1
            elif mfe >= 12.0:
                tier_1_breakeven_locks += 1
                tier_2_profit_locks += 1
            elif mfe >= 8.0:
                tier_1_breakeven_locks += 1

            # Model consensus calibration
            conf = float(s.get("confidence_score", 0.5) or 0.5)
            is_win = 1 if net_pnl > 0 else 0
            brier_scores.append((conf - is_win) ** 2)

            mb = s.get("model_breakdown", {})
            cb = float(mb.get("catboost_prob", 0.5) or 0.5)
            lgb = float(mb.get("lightgbm_prob", 0.5) or 0.5)
            xgb = float(mb.get("xgboost_prob", 0.5) or 0.5)
            gemini_raw = str(mb.get("gemini_sentiment", ""))

            if (cb >= 0.6 and lgb >= 0.6 and xgb >= 0.6) or (cb <= 0.4 and lgb <= 0.4 and xgb <= 0.4):
                tri_consensus_total += 1
                if is_win:
                    tri_consensus_wins += 1

            decision = str(s.get("decision", "")).upper()
            if ("BULLISH" in gemini_raw and "CALL" in decision) or ("BEARISH" in gemini_raw and "PUT" in decision):
                gemini_aligned_total += 1
                if is_win:
                    gemini_aligned_wins += 1

            # Instrument breakdown
            sym = s.get("symbol", "NIFTY")
            if sym not in symbol_stats:
                symbol_stats[sym] = {"trades": 0, "wins": 0, "net_pnl": 0.0}
            symbol_stats[sym]["trades"] += 1
            if is_win:
                symbol_stats[sym]["wins"] += 1
            symbol_stats[sym]["net_pnl"] += net_pnl

            # Directional breakdown
            opt_type = "CE" if ("CALL" in decision or "CE" in str(tb.get("option_type", ""))) else "PE"
            direction_stats[opt_type]["total"] += 1
            if is_win:
                direction_stats[opt_type]["wins"] += 1
            direction_stats[opt_type]["net_pnl"] += net_pnl

        # Mathematical Metrics Calculation
        total_res = len(resolved_signals)
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        be_count = len(breakeven_trades)

        win_rate = (win_count / total_res * 100.0) if total_res > 0 else 0.0
        tot_gross = sum(gross_pnls)
        tot_net = sum(net_pnls)
        tot_tax = tot_gross - tot_net

        total_gains = sum(s.get("net_pnl", 0.0) for s in winning_trades)
        total_losses = abs(sum(s.get("net_pnl", 0.0) for s in losing_trades))
        profit_factor = (total_gains / total_losses) if total_losses > 0 else (999.0 if total_gains > 0 else 0.0)

        avg_win = (total_gains / win_count) if win_count > 0 else 0.0
        avg_loss = (total_losses / loss_count) if loss_count > 0 else 0.0
        payoff_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0.0

        # Mathematical Expectancy = (P_win * Avg_Win) - (P_loss * Avg_Loss)
        p_win = win_count / total_res if total_res > 0 else 0.0
        p_loss = loss_count / total_res if total_res > 0 else 0.0
        expectancy_inr = (p_win * avg_win) - (p_loss * avg_loss)

        # Sharpe & Sortino Ratios of returns
        std_returns = float(np.std(net_pnls)) if len(net_pnls) > 1 else 1.0
        mean_pnl = float(np.mean(net_pnls)) if net_pnls else 0.0
        downside_returns = [p for p in net_pnls if p < 0]
        std_downside = float(np.std(downside_returns)) if len(downside_returns) > 1 else 1.0

        sharpe = (mean_pnl / std_returns * math.sqrt(252)) if std_returns > 0 else 0.0
        sortino = (mean_pnl / std_downside * math.sqrt(252)) if std_downside > 0 else 0.0

        # Capital Preservation by 3-Tier Trailing SL:
        # Avoided full -12% stop loss when shifting to BE at +8% or locking +6% at +12%
        saved_capital_inr = (tier_1_breakeven_locks - target_reaches) * (avg_loss * 0.75)

        return {
            "total_records": total_signals,
            "resolved_count": total_res,
            "open_count": len(open_signals),
            "win_count": win_count,
            "loss_count": loss_count,
            "breakeven_count": be_count,
            "win_rate_pct": round(win_rate, 2),
            "gross_pnl_inr": round(tot_gross, 2),
            "statutory_taxes_brokerage_inr": round(tot_tax, 2),
            "net_pnl_inr": round(tot_net, 2),
            "profit_factor": round(profit_factor, 2),
            "payoff_ratio": round(payoff_ratio, 2),
            "avg_win_inr": round(avg_win, 2),
            "avg_loss_inr": round(avg_loss, 2),
            "expectancy_per_trade_inr": round(expectancy_inr, 2),
            "largest_win_inr": round(max(net_pnls), 2) if net_pnls else 0.0,
            "largest_loss_inr": round(min(net_pnls), 2) if net_pnls else 0.0,
            "sharpe_ratio_est": round(sharpe, 2),
            "sortino_ratio_est": round(sortino, 2),
            "avg_mfe_pct": round(float(np.mean(mfe_excursions)), 2) if mfe_excursions else 0.0,
            "avg_mae_pct": round(float(np.mean(mae_excursions)), 2) if mae_excursions else 0.0,
            # Trailing Stop-Loss Metrics
            "trailing_stop_active_signals": trailing_active_count,
            "tier_1_breakeven_locks": tier_1_breakeven_locks,
            "tier_2_profit_locks": tier_2_profit_locks,
            "tier_3_dynamic_trails": tier_3_dynamic_trails,
            "target_hits": target_reaches,
            "full_stop_loss_hits": stop_loss_hits,
            "capital_saved_by_trailing_sl_inr": round(max(0.0, saved_capital_inr), 2),
            # AI Calibration
            "brier_score_calibration": round(float(np.mean(brier_scores)), 4) if brier_scores else 0.0,
            "tri_model_consensus_win_rate": round((tri_consensus_wins / tri_consensus_total * 100.0) if tri_consensus_total else 0.0, 2),
            "tri_model_consensus_count": tri_consensus_total,
            "gemini_aligned_win_rate": round((gemini_aligned_wins / gemini_aligned_total * 100.0) if gemini_aligned_total else 0.0, 2),
            "gemini_aligned_count": gemini_aligned_total,
            "symbol_stats": symbol_stats,
            "direction_stats": direction_stats,
        }

    def analyze_equity_ledger(self) -> Dict[str, Any]:
        """Deep analysis of all 114 Equity Momentum records in `equity_signals_ledger`."""
        docs = list(self.db.collection("equity_signals_ledger").stream())
        signals = [d.to_dict() for d in docs]

        total_scanned = len(signals)
        target_hits = 0
        stopped_out = 0
        open_positions = 0
        returns: List[float] = []
        win_returns: List[float] = []
        loss_returns: List[float] = []
        time_to_targets: List[int] = []
        sector_breakdown = {}

        for s in signals:
            st = str(s.get("status", "OPEN")).upper()
            ret = s.get("returns_pct")
            sec = s.get("time_to_target_seconds")
            am = s.get("analysis_method", {})
            sector = am.get("sector", "Diversified")

            if sector not in sector_breakdown:
                sector_breakdown[sector] = {"trades": 0, "wins": 0, "returns": []}
            sector_breakdown[sector]["trades"] += 1

            if st == "TARGET_HIT":
                target_hits += 1
                sector_breakdown[sector]["wins"] += 1
                if ret is not None:
                    returns.append(float(ret))
                    win_returns.append(float(ret))
                    sector_breakdown[sector]["returns"].append(float(ret))
                if sec is not None and float(sec) > 0:
                    time_to_targets.append(int(sec))
            elif st == "STOPPED_OUT":
                stopped_out += 1
                if ret is not None:
                    returns.append(float(ret))
                    loss_returns.append(float(ret))
                    sector_breakdown[sector]["returns"].append(float(ret))
            else:
                open_positions += 1

        resolved = target_hits + stopped_out
        win_rate = (target_hits / resolved * 100.0) if resolved > 0 else 0.0
        profit_factor = (
            (sum(win_returns) / abs(sum(loss_returns)))
            if loss_returns and sum(loss_returns) != 0
            else (999.0 if win_returns else 0.0)
        )

        return {
            "total_scanned": total_scanned,
            "resolved_count": resolved,
            "open_positions": open_positions,
            "target_hits": target_hits,
            "stopped_out": stopped_out,
            "win_rate_pct": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "avg_return_pct": round(float(np.mean(returns)), 2) if returns else 0.0,
            "avg_win_pct": round(float(np.mean(win_returns)), 2) if win_returns else 0.0,
            "avg_loss_pct": round(float(np.mean(loss_returns)), 2) if loss_returns else 0.0,
            "max_gain_pct": round(max(returns), 2) if returns else 0.0,
            "max_drawdown_pct": round(min(returns), 2) if returns else 0.0,
            "avg_time_to_target_sec": int(np.mean(time_to_targets)) if time_to_targets else 0,
            "sector_breakdown": sector_breakdown,
        }

    def analyze_eod_journals(self) -> Dict[str, Any]:
        """Analysis of official daily institutional EOD journals in `eod_trading_journal`."""
        docs = list(self.db.collection("eod_trading_journal").stream())
        journals = [d.to_dict() for d in docs]

        daily_metrics = []
        for j in journals:
            m = j.get("metrics")
            if m:
                daily_metrics.append(m)

        if not daily_metrics:
            return {"total_journals": len(journals), "note": "Journals exist in legacy format"}

        avg_roi = float(np.mean([m.get("net_roi_pct", 0.0) for m in daily_metrics]))
        avg_sharpe = float(np.mean([m.get("sharpe_ratio", 0.0) for m in daily_metrics]))
        avg_sortino = float(np.mean([m.get("sortino_ratio", 0.0) for m in daily_metrics]))
        avg_pf = float(np.mean([m.get("profit_factor", 0.0) for m in daily_metrics]))
        avg_win_rate = float(np.mean([m.get("win_rate_pct", 0.0) for m in daily_metrics]))

        return {
            "total_journals": len(journals),
            "analyzed_sessions": len(daily_metrics),
            "avg_daily_roi_pct": round(avg_roi, 2),
            "avg_sharpe_ratio": round(avg_sharpe, 2),
            "avg_sortino_ratio": round(avg_sortino, 2),
            "avg_profit_factor": round(avg_pf, 2),
            "avg_win_rate_pct": round(avg_win_rate, 2),
            "latest_session": daily_metrics[-1] if daily_metrics else None,
        }

    def analyze_chop_filter_vetoes(self, limit: int = 500) -> Dict[str, Any]:
        """Analyzes chop filter and momentum vetoes from recent signals."""
        docs = list(self.db.collection("signals").order_by("stored_at", direction=firestore.Query.DESCENDING).limit(limit).stream())
        signals = [d.to_dict() for d in docs]

        veto_count = 0
        veto_reasons = {}
        actionable_signals = 0

        for s in signals:
            analysis = s.get("analysis", {})
            if analysis.get("veto_active"):
                veto_count += 1
                reason = analysis.get("veto_reason", "Chop Filter Active")
                # Normalize reason
                if "ADX < 25" in reason:
                    norm_reason = "ADX < 25 Consolidating / Theta Decay Risk"
                elif "RSI" in reason:
                    norm_reason = "RSI Overbought/Oversold Filter"
                elif "MACD" in reason:
                    norm_reason = "MACD Momentum Counter-Trend"
                else:
                    norm_reason = reason[:45]
                veto_reasons[norm_reason] = veto_reasons.get(norm_reason, 0) + 1
            else:
                actionable_signals += 1

        veto_rate = (veto_count / len(signals) * 100.0) if signals else 0.0

        return {
            "sample_size": len(signals),
            "veto_count": veto_count,
            "actionable_signals": actionable_signals,
            "veto_rate_pct": round(veto_rate, 2),
            "veto_reasons": veto_reasons,
        }


def run_full_analysis():
    print("========================================================================================")
    print("🚀 RUNNING INSTITUTIONAL DATA ANALYSIS OVER PRODUCTION FIRESTORE RECORDS...")
    print("========================================================================================")

    analyzer = InstitutionalFirestoreAnalyzer()

    # 1. Options Tri-Model Analysis
    print("  [1/4] Auditing `ai_signals_ledger` (264 Options Contracts)...")
    options_audit = analyzer.analyze_options_ledger()

    # 2. Equity Momentum Analysis
    print("  [2/4] Auditing `equity_signals_ledger` (114 Equity Momentum Signals)...")
    equity_audit = analyzer.analyze_equity_ledger()

    # 3. EOD Journals Audit
    print("  [3/4] Auditing `eod_trading_journal` (Daily Audited Performance Logs)...")
    journal_audit = analyzer.analyze_eod_journals()

    # 4. Chop Veto Analysis
    print("  [4/4] Auditing `signals` (Chop Filter & Anti-Whipsaw Veto Engine)...")
    veto_audit = analyzer.analyze_chop_filter_vetoes(limit=500)

    # Compile Consolidated Report
    report = {
        "analysis_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "gcp_project_id": PROJECT_ID,
        "options_tri_model_audit": options_audit,
        "equity_momentum_audit": equity_audit,
        "eod_journals_audit": journal_audit,
        "chop_veto_audit": veto_audit,
    }

    # Save to disk
    out_path = os.path.join(os.path.dirname(__file__), "..", "firestore_performance_analysis_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Analysis complete! Report saved to {out_path}")
    return report


if __name__ == "__main__":
    rep = run_full_analysis()
    print("\n" + json.dumps(rep, indent=2))
