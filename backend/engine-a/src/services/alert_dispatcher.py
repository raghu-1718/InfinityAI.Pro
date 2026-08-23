"""
Multi-Channel Alert Dispatcher (Telegram & WhatsApp)
InfinityAI.Pro - Institutional Algorithmic Trading Platform
Asynchronously dispatches real-time AI signal alerts, trade brackets,
trailing stop transitions, and 08:30 IST Pre-Market Macro Briefings.
"""

import os
import asyncio
import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("InfinityAI.AlertDispatcher")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_TO_NUMBER = os.getenv("WHATSAPP_TO_NUMBER", "")
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")

class AlertDispatcher:
    """Multi-channel async notifications dispatcher for Telegram & WhatsApp"""

    def __init__(self):
        self.telegram_enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        self.whatsapp_enabled = bool(WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_TO_NUMBER)
        self.webhook_enabled = bool(ALERT_WEBHOOK_URL)
        if self.telegram_enabled:
            logger.info("✅ Telegram Alert Channel: ENABLED")
        if self.whatsapp_enabled:
            logger.info("✅ WhatsApp Alert Channel: ENABLED")

    async def dispatch_signal_alert(self, signal_payload: Dict[str, Any]):
        """Dispatches a newly generated high-conviction AI trading signal"""
        try:
            sym = signal_payload.get("symbol", "NIFTY")
            decision = signal_payload.get("decision", "BUY_CALL")
            conf = float(signal_payload.get("confidence_score", 0.65)) * 100
            spot = float(signal_payload.get("spot_price", 0.0))
            bracket = signal_payload.get("trade_bracket", {})
            exp_pnl = signal_payload.get("expected_pnl", {})
            models = signal_payload.get("model_breakdown", {})

            contract = bracket.get("contract", f"{sym} ATM Options")
            lot_size = bracket.get("lot_size", 65)
            entry_prem = float(bracket.get("entry_premium", 100.0))
            target_prem = float(bracket.get("target_premium", entry_prem * 1.15))
            stop_prem = float(bracket.get("stop_loss_premium", entry_prem * 0.89))
            exp_net = float(exp_pnl.get("expected_profit_target_net", (target_prem - entry_prem) * lot_size - 55))
            max_risk = float(exp_pnl.get("max_loss_stop_loss_net", (stop_prem - entry_prem) * lot_size - 55))
            gemini_sent = models.get("gemini_sentiment", "NEUTRAL")
            time_ist = signal_payload.get("timestamp_ist", "")

            emoji = "🟢 🎯" if "CALL" in decision or "BUY" in decision else "🔴 🎯"
            tg_text = (
                f"{emoji} *INFINITY AI INSTITUTIONAL SIGNAL*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 *Contract:* `{contract}`\n"
                f"🧭 *Decision:* *{decision}* (AI Consensus: `{conf:.1f}%`)\n"
                f"📍 *Underlying Spot:* `₹{spot:,.2f}`\n"
                f"⏱ *Timestamp:* `{time_ist}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 *Trade Bracket (1 Lot = {lot_size}):*\n"
                f"• *ATM Entry Premium:* `₹{entry_prem:.2f}`\n"
                f"• *Target (+15%):* `₹{target_prem:.2f}` (*Exp Net:* `+₹{exp_net:,.2f}`)\n"
                f"• *Stop Loss (-11%):* `₹{stop_prem:.2f}` (*Max Risk:* `₹{max_risk:,.2f}`)\n"
                f"• *Trailing SL Invariants:* `+8% -> BE | +12% -> +6% Lock`\n"
                f"• *Gemini Macro Bias:* `{gemini_sent}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🛡️ _Auto-logged to Firestore Ledger & Live MTM Tracker_"
            )

            await self._send_telegram(tg_text)
            await self._send_whatsapp(tg_text.replace("*", "").replace("`", ""))
            await self._send_webhook({"event": "SIGNAL_GENERATED", "data": signal_payload})
        except Exception as e:
            logger.warning(f"Error dispatching signal alert: {e}")

    def _format_outcome_text(self, outcome_data: Dict[str, Any]) -> str:
        sig_id = outcome_data.get("signal_id", "")
        sym = outcome_data.get("symbol", "NIFTY")
        status = outcome_data.get("outcome_status", "RESOLVED")
        exit_prem = float(outcome_data.get("exit_premium", 0.0))
        gross_pnl = float(outcome_data.get("gross_pnl", 0.0))
        net_pnl = float(outcome_data.get("net_pnl", 0.0))
        resolved_at = outcome_data.get("resolved_at", "Just now")
        bracket = outcome_data.get("trade_bracket", {})
        entry_prem = float(bracket.get("entry_premium", 100.0))
        lot_size = bracket.get("lot_size", 65)
        contract = bracket.get("contract", f"{sym} ATM Options")
        tax_cost = float(outcome_data.get("estimated_tax_brokerage", 55.0))
        roi_pct = (net_pnl / (entry_prem * lot_size) * 100) if (entry_prem * lot_size) > 0 else 0.0

        if status == "TARGET_HIT" or net_pnl > 0:
            header = "🟢 🎉 *INFINITY AI — PROFIT TARGET ACHIEVED (+15%)*"
            result_badge = f"🏆 *PROFIT: +₹{net_pnl:,.2f}* (`+{roi_pct:.1f}% ROI`)"
        elif status == "STOP_LOSS_HIT":
            header = "🔴 🛡️ *INFINITY AI — STOP LOSS TRIGGERED (-11%)*"
            result_badge = f"⚠️ *LOSS: -₹{abs(net_pnl):,.2f}* (`{roi_pct:.1f}% ROI`)"
        else:
            header = "⏰ 📋 *INFINITY AI — EOD 15:15 INTRADAY AUTO SQUARE-OFF*"
            pnl_badge = f"+₹{net_pnl:,.2f}" if net_pnl >= 0 else f"-₹{abs(net_pnl):,.2f}"
            result_badge = f"📊 *NET RESULT: {pnl_badge}* (`{roi_pct:+.1f}% ROI`)"

        return (
            f"{header}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Contract:* `{contract}`\n"
            f"🏷️ *Signal ID:* `{sig_id}`\n"
            f"💰 *Entry Premium:* `₹{entry_prem:.2f}` ➔ *Exit:* `₹{exit_prem:.2f}`\n"
            f"💵 *Trade Outcome:* {result_badge}\n"
            f"🧾 *Gross P&L:* `₹{gross_pnl:+,.2f}` | *Statutory Taxes:* `₹{tax_cost:.2f}`\n"
            f"⏱️ *Resolution Time:* `{resolved_at}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ _Trade closed & committed to Institutional Performance Ledger_"
        )

    async def dispatch_outcome_alert(self, outcome_data: Dict[str, Any]):
        """Dispatches an alert when an open trade reaches Target, Stop Loss, or EOD Exit"""
        try:
            tg_text = self._format_outcome_text(outcome_data)
            await self._send_telegram(tg_text)
            await self._send_whatsapp(tg_text.replace("*", "").replace("`", ""))
            await self._send_webhook({"event": "OUTCOME_RESOLVED", "data": outcome_data})
        except Exception as e:
            logger.warning(f"Error dispatching outcome alert: {e}")

    def dispatch_outcome_sync(self, outcome_data: Dict[str, Any]):
        """Thread-safe synchronous fallback for dispatching outcome alerts"""
        try:
            tg_text = self._format_outcome_text(outcome_data)
            self._send_telegram_sync(tg_text)
        except Exception as e:
            logger.warning(f"Sync outcome dispatch error: {e}")

    def _send_telegram_sync(self, text: str):
        if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
            return
        import urllib.request, json
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
        except Exception as e:
            logger.warning(f"Sync Telegram dispatch failed: {e}")

    async def dispatch_premarket_briefing(self, report: Dict[str, Any]):
        """Dispatches the 08:30 IST Pre-Market Intelligence Briefing"""
        try:
            date_str = report.get("report_date", "Today")
            bias = report.get("macro_bias", "NEUTRAL")
            gap = report.get("expected_gap", "FLAT")
            gift_pts = report.get("gift_nifty_points", 0.0)
            crude_pct = report.get("crude_oil_pct", 0.0)
            fii = report.get("fii_net_crores", 0.0)
            dii = report.get("dii_net_crores", 0.0)
            synthesis = report.get("gemini_macro_synthesis", "")

            tg_text = (
                f"☕ *INFINITY AI PRE-MARKET MACRO RADAR (08:30 IST)*\n"
                f"📅 *Date:* `{date_str}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🧭 *Opening Directional Bias:* *{bias}* ({gap})\n"
                f"📈 *GIFT NIFTY Delta:* `{gift_pts:+.1f} pts`\n"
                f"🛢️ *Brent Crude Oil:* `{crude_pct:+.2f}%`\n"
                f"🏦 *Institutional Cash Flow:*\n"
                f"   • *FII Net:* `₹{fii:+,.0f} Cr`\n"
                f"   • *DII Net:* `₹{dii:+,.0f} Cr`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🧠 *Vertex AI Gemini Macro Synthesis:*\n"
                f"{synthesis}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚀 _Engine B models pre-loaded. Ready for 09:15 IST Market Open._"
            )

            await self._send_telegram(tg_text)
            await self._send_whatsapp(tg_text.replace("*", "").replace("`", ""))
            await self._send_webhook({"event": "PREMARKET_BRIEFING", "data": report})
        except Exception as e:
            logger.warning(f"Error dispatching premarket briefing: {e}")

    async def _send_telegram(self, text: str):
        if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.warning(f"Telegram dispatch failed: {e}")

    async def _send_whatsapp(self, text: str):
        if not (WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_TO_NUMBER):
            return
        url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "messaging_product": "whatsapp",
            "to": WHATSAPP_TO_NUMBER,
            "type": "text",
            "text": {"body": text}
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload, headers=headers)
        except Exception as e:
            logger.warning(f"WhatsApp dispatch failed: {e}")

    async def _send_webhook(self, payload: Dict[str, Any]):
        if not ALERT_WEBHOOK_URL:
            return
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(ALERT_WEBHOOK_URL, json=payload)
        except Exception as e:
            logger.warning(f"Webhook dispatch failed: {e}")

    async def dispatch_custom_message(self, html_or_md_text: str):
        """Dispatches an arbitrary formatted message (EOD Journal, Circuit Breakers, etc.)"""
        try:
            await self._send_telegram_html(html_or_md_text)
            await self._send_whatsapp(html_or_md_text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "").replace("<i>", "").replace("</i>", ""))
        except Exception as e:
            logger.warning(f"Custom message dispatch failed: {e}")

    async def _send_telegram_html(self, text: str):
        if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            # Fallback to plain text or Markdown if HTML parse fails
            try:
                payload["parse_mode"] = "Markdown"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(url, json=payload)
            except Exception:
                logger.warning(f"Telegram HTML dispatch failed: {e}")

ALERT_DISPATCHER = AlertDispatcher()
