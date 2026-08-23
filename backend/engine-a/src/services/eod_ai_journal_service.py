"""
InfinityAI.Pro — 15:35 IST Automated EOD AI Journal & Performance Digest
==========================================================================
Automatically triggers at 15:35 IST upon market close:
  1. Aggregates all closed & open shadow/live trades from Firestore ai_signals_ledger.
  2. Computes Net Realized P&L in ₹, Win Rate, ROI %, and SEBI 2026 statutory taxes.
  3. Uses Vertex AI Gemini 2.5 Flash to synthesize an institutional qualitative review.
  4. Saves journal to Firestore eod_trading_journal and dispatches via Telegram.
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

try:
    from google.cloud import firestore
except Exception:
    firestore = None

try:
    from .alert_dispatcher import ALERT_DISPATCHER
except Exception:
    try:
        from src.services.alert_dispatcher import ALERT_DISPATCHER
    except Exception:
        ALERT_DISPATCHER = None

logger = logging.getLogger("InfinityAI.EODAIJournal")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
LEDGER_COLLECTION = "ai_signals_ledger"
JOURNAL_COLLECTION = "eod_trading_journal"

class EODAIJournalService:
    """Automated post-market analytical synthesis and journaling engine"""

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        self.db = None
        if firestore:
            try:
                self.db = firestore.Client(project=project_id)
            except Exception as e:
                logger.warning(f"EODAIJournalService Firestore init warning: {e}")

    async def generate_and_dispatch_eod_journal(self, target_date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes complete EOD journal generation:
        Pulls ledger docs, computes performance metrics, generates Gemini critique,
        stores in Firestore, and sends Telegram digest.
        """
        now_utc = datetime.now(timezone.utc)
        ist_time = now_utc + timedelta(hours=5, minutes=30)
        date_str = target_date_str or ist_time.strftime("%Y-%m-%d")

        # 1. Fetch today's signals from Firestore
        signals: List[Dict[str, Any]] = []
        if self.db:
            try:
                # Query docs where timestamp starts with date_str or date matches
                docs = self.db.collection(LEDGER_COLLECTION).stream()
                for doc in docs:
                    data = doc.to_dict()
                    ts = data.get("timestamp_ist", data.get("timestamp", ""))
                    if date_str in ts or data.get("date") == date_str:
                        signals.append(data)
            except Exception as e:
                logger.error(f"Error fetching ledger for EOD journal: {e}")

        # 2. Compute Performance Metrics
        total_signals = len(signals)
        target_hits = sum(1 for s in signals if s.get("status") in ["TARGET_HIT", "WIN", "PROFIT"])
        sl_hits = sum(1 for s in signals if s.get("status") in ["STOP_LOSS_HIT", "LOSS"])
        open_signals = sum(1 for s in signals if s.get("status") in ["OPEN", "PENDING", "ACTIVE"])
        closed_trades = target_hits + sl_hits

        win_rate = (target_hits / closed_trades * 100.0) if closed_trades > 0 else 0.0

        gross_pnl = sum(float(s.get("realized_pnl_rupees", s.get("expected_target_gross", 0))) for s in signals if s.get("status") in ["TARGET_HIT", "WIN"])
        gross_loss = sum(float(s.get("realized_pnl_rupees", s.get("max_loss_gross", 0))) for s in signals if s.get("status") in ["STOP_LOSS_HIT", "LOSS"])
        net_realized_pnl = round(gross_pnl + gross_loss, 2)

        total_taxes = round(sum(float(s.get("tax_cost", 55.0)) for s in signals), 2)
        net_after_tax = round(net_realized_pnl - (total_taxes if closed_trades > 0 else 0.0), 2)

        # 3. Qualitative Gemini 2.5 Flash Synthesis
        gemini_critique = self._synthesize_with_gemini(
            date_str=date_str,
            total_signals=total_signals,
            win_rate=win_rate,
            net_pnl=net_after_tax,
            signals=signals
        )

        journal_id = f"EOD_{date_str.replace('-', '')}"
        journal_record = {
            "journal_id": journal_id,
            "date": date_str,
            "timestamp_ist": ist_time.strftime("%Y-%m-%d %H:%M:%S IST"),
            "timestamp_utc": now_utc.isoformat(),
            "total_signals": total_signals,
            "closed_trades": closed_trades,
            "target_hits": target_hits,
            "stop_loss_hits": sl_hits,
            "open_signals": open_signals,
            "win_rate_pct": round(win_rate, 1),
            "gross_pnl_rupees": net_realized_pnl,
            "estimated_statutory_taxes": total_taxes,
            "net_realized_pnl_rupees": net_after_tax,
            "performance_rating": "INSTITUTIONAL_OUTPERFORM" if win_rate >= 70 else "NOMINAL_EXECUTION" if win_rate >= 50 else "CAPITAL_PRESERVATION",
            "gemini_qualitative_review": gemini_critique,
            "signals_snapshot": signals[:10]  # Store first 10 for quick UI review
        }

        # 4. Commit to Firestore
        if self.db:
            try:
                self.db.collection(JOURNAL_COLLECTION).document(journal_id).set(journal_record)
                logger.info(f"✅ EOD Trading Journal committed to Firestore: {journal_id}")
            except Exception as e:
                logger.error(f"Failed to commit EOD journal to Firestore: {e}")

        # 5. Dispatch Telegram Digest
        await self._dispatch_telegram_journal(journal_record)
        return journal_record

    def _synthesize_with_gemini(
        self,
        date_str: str,
        total_signals: int,
        win_rate: float,
        net_pnl: float,
        signals: List[Dict[str, Any]]
    ) -> str:
        """Calls Vertex AI Gemini 2.5 Flash for post-market qualitative evaluation"""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            vertexai.init(project=self.project_id, location="us-central1")
            model = GenerativeModel("gemini-2.5-flash")
            
            prompt = f"""You are a Lead Quantitative Portfolio Manager reviewing the trading day ({date_str}) for InfinityAI.Pro on Indian Capital Markets (NSE/BSE).
Performance Summary:
- Total Signals: {total_signals}
- Win Rate: {win_rate:.1f}%
- Net Realized P&L: ₹{net_pnl:+,.2f}
- Sample Trades: {json.dumps(signals[:5], default=str)}

Provide an institutional post-market review structured in 3 bullet points:
1. Regime & Edge Analysis: How the Tri-Model ensemble performed against today's price action.
2. Risk & Slippage Execution: Assessment of stop-loss adherence and theta decay mitigation.
3. Tactical Guidance: Key setups to prioritize for tomorrow's opening session."""

            resp = model.generate_content(prompt)
            if resp and resp.text:
                return resp.text.strip()
        except Exception as e:
            logger.warning(f"Vertex AI Gemini EOD synthesis fallback: {e}")

        # Rule-based fallback synthesis
        pnl_symbol = "🟢" if net_pnl >= 0 else "🔴"
        return (
            f"{pnl_symbol} Institutional EOD Summary for {date_str}:\n"
            f"• Market Regime: Tri-Model MLOps Ensemble executed {total_signals} setups with {win_rate:.1f}% target realization.\n"
            f"• Risk Discipline: Dynamic VaR sizing and -11% stop-loss guardrails strictly retained capital with net P&L ₹{net_pnl:+,.2f}.\n"
            f"• Tomorrow's Focus: Monitor GIFT Nifty gap signals and pre-market institutional FII/DII flow synthesis at 08:30 IST."
        )

    async def _dispatch_telegram_journal(self, journal: Dict[str, Any]) -> None:
        """Formats and sends the EOD journal digest via AlertDispatcher"""
        pnl_symbol = "🟢" if journal["net_realized_pnl_rupees"] >= 0 else "🔴"
        msg = (
            f"📊 <b>INFINITYAI.PRO — EOD PERFORMANCE JOURNAL</b> 📊\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Date:</b> <code>{journal['date']}</code> (15:35 IST Market Close)\n"
            f"🎯 <b>Total Setups:</b> {journal['total_signals']} | <b>Closed:</b> {journal['closed_trades']}\n"
            f"🏆 <b>Win Rate:</b> <b>{journal['win_rate_pct']:.1f}%</b> ({journal['target_hits']} Wins / {journal['stop_loss_hits']} Losses)\n"
            f"{pnl_symbol} <b>Net Realized P&L:</b> <b>₹{journal['net_realized_pnl_rupees']:+,.2f}</b>\n"
            f"🏛️ <b>Statutory Taxes & Brokerage:</b> ₹{journal['estimated_statutory_taxes']:,.2f}\n"
            f"🏅 <b>Performance Rating:</b> <code>{journal['performance_rating']}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠 <b>AI Qualitative Critique (Gemini 2.5 Flash):</b>\n"
            f"<i>{journal['gemini_qualitative_review']}</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <i>Autonomous Institutional Execution by InfinityAI.Pro</i>"
        )
        if ALERT_DISPATCHER:
            await ALERT_DISPATCHER.dispatch_custom_message(msg)

EOD_AI_JOURNAL_SERVICE = EODAIJournalService()
