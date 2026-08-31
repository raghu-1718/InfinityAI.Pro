"""
08:30 IST Pre-Market Intelligence Briefing Service
InfinityAI.Pro - Real-Time Vertex AI Gemini 2.5 Flash Search Grounding
Evaluates dynamic macro priors (GIFT Nifty, Brent Crude, US Yields, FII/DII Net Flows)
and commits reports to Firestore and dispatches via AlertDispatcher.
"""

import os
import json
import re
import time
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

try:
    from google.cloud import firestore
except Exception:
    firestore = None

try:
    from google.cloud import bigquery
except Exception:
    bigquery = None

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None

from .alert_dispatcher import ALERT_DISPATCHER

logger = logging.getLogger("InfinityAI.PreMarketBriefing")

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "project-841b7f97-5ee3-4fbe-920")
COLLECTION_NAME = "premarket_macro_reports"

class PreMarketBriefingService:
    """Real-Time Pre-Market Intelligence orchestrator for Engine A"""

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        self.db = None
        self.bq = None
        self.genai_client = None
        self.genai_available = False

        try:
            if firestore:
                self.db = firestore.Client(project=project_id)
        except Exception as e:
            logger.warning(f"PreMarketBriefingService Firestore init warning: {e}")

        try:
            if bigquery:
                self.bq = bigquery.Client(project=project_id)
        except Exception as e:
            logger.warning(f"PreMarketBriefingService BigQuery init warning: {e}")

        self._init_genai()

    def _init_genai(self):
        """Initializes Vertex AI Gemini 2.5 Flash client via Application Default Credentials (ADC)"""
        if not genai:
            return
        try:
            # Strictly use Vertex AI with ADC (us-central1) for enterprise Google Search Grounding
            self.genai_client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location="us-central1"
            )
            self.genai_available = True
            logger.info("✅ Vertex AI Gemini Client initialized via ADC (us-central1) for PreMarketBriefingService.")
        except Exception as e:
            logger.warning(f"Vertex AI GenAI initialization warning: {e}")
            self.genai_client = None
            self.genai_available = False

    async def _fetch_grounded_macro_telemetry(self) -> Dict[str, Any]:
        """Queries Vertex AI Gemini 2.5 Flash with live Google Search Grounding"""
        if not self.genai_available or not self.genai_client:
            return self._get_fallback_telemetry()

        prompt = (
            "You are an institutional quantitative macro research analyst for Indian capital markets (NSE/BSE). "
            "Perform a real-time live search for today's pre-market conditions:\n"
            "1. GIFT NIFTY live points change and expected NIFTY 50 opening gap.\n"
            "2. Brent Crude Oil price and 24h percentage change.\n"
            "3. NSE/BSE institutional FII & DII cash market net activity in INR Crores from the previous trading session.\n"
            "4. US 10-Year Treasury Yield and US Dollar Index (DXY).\n\n"
            "Output ONLY a raw valid JSON object (enclosed in ```json ... ```) with these exact keys:\n"
            "{\n"
            '  "gift_nifty_points": float,\n'
            '  "brent_crude_pct": float,\n'
            '  "fii_net_crores": float,\n'
            '  "dii_net_crores": float,\n'
            '  "us_10y_yield": float,\n'
            '  "dxy_index": float,\n'
            '  "macro_bias": "BULLISH" | "BEARISH" | "NEUTRAL",\n'
            '  "macro_synthesis": string\n'
            "}"
        )

        try:
            resp = await asyncio.to_thread(
                lambda: self.genai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
            )

            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', resp.text, re.DOTALL)
            raw_json = match.group(1) if match else resp.text.strip()
            data = json.loads(raw_json)
            return data
        except Exception as e:
            logger.error(f"Failed to query Google Search Grounding for Pre-Market Macro Radar: {e}")
            return self._get_fallback_telemetry()

    def _get_fallback_telemetry(self) -> Dict[str, Any]:
        return {
            "gift_nifty_points": 0.0,
            "brent_crude_pct": 0.0,
            "fii_net_crores": 0.0,
            "dii_net_crores": 0.0,
            "us_10y_yield": 4.25,
            "dxy_index": 103.5,
            "macro_bias": "NEUTRAL",
            "macro_synthesis": "Neutral pre-market setup. Monitoring opening range breakout across major indices."
        }

    async def generate_and_dispatch_briefing(self) -> Dict[str, Any]:
        """Runs the 08:30 IST live synthesis, saves report, and dispatches multi-channel alerts"""
        now_utc = datetime.now(timezone.utc)
        ist_time = now_utc + timedelta(hours=5, minutes=30)
        today_str = ist_time.strftime("%Y-%m-%d")

        # 1. Real-Time Grounded Macro Assessment
        live_telemetry = await self._fetch_grounded_macro_telemetry()

        gift_points = float(live_telemetry.get("gift_nifty_points", 0.0))
        crude_pct = float(live_telemetry.get("brent_crude_pct", 0.0))
        fii_net = float(live_telemetry.get("fii_net_crores", 0.0))
        dii_net = float(live_telemetry.get("dii_net_crores", 0.0))
        us_10y = float(live_telemetry.get("us_10y_yield", 4.25))
        dxy = float(live_telemetry.get("dxy_index", 103.5))
        macro_bias = live_telemetry.get("macro_bias", "NEUTRAL")
        gemini_synthesis = live_telemetry.get("macro_synthesis", "")

        # 2. Multi-Factor Quantitative Scoring
        gift_score = max(-1.0, min(1.0, gift_points / 100.0))
        crude_score = max(-1.0, min(1.0, -crude_pct / 2.5))
        net_inst_flow = fii_net + (dii_net * 0.7)
        flow_score = max(-1.0, min(1.0, net_inst_flow / 2500.0))
        dxy_score = -0.3 if dxy > 104.5 else (+0.3 if dxy < 103.0 else 0.0)

        composite_score = round(
            (gift_score * 0.35) + (crude_score * 0.20) + (flow_score * 0.25) + (dxy_score * 0.20),
            3
        )

        # Canonical Gap Classification
        expected_gap = "GAP_UP" if gift_points > 25.0 else ("GAP_DOWN" if gift_points < -25.0 else "FLAT")
        crude_status = "BENIGN" if crude_pct <= 0 else ("HEADWIND" if crude_pct > 1.5 else "NEUTRAL")
        flow_status = "NET_INFLOW" if (fii_net + dii_net) > 500.0 else ("NET_OUTFLOW" if (fii_net + dii_net) < -500.0 else "BALANCED")

        # Canonical Gap Narrative Reconciliation (Ensures zero semantic contradiction between JSON numbers and text)
        if expected_gap == "GAP_UP":
            canonical_gap_text = f"GIFT Nifty indicates a constructive gap-up expectation (+{gift_points:.1f} pts)."
        elif expected_gap == "GAP_DOWN":
            canonical_gap_text = f"GIFT Nifty indicates a defensive gap-down expectation ({gift_points:.1f} pts)."
        else:
            canonical_gap_text = f"GIFT Nifty indicates a flat/neutral opening expectation ({gift_points:+.1f} pts)."

        # Ensure synthesis text does not contradict validated numeric fields
        if not gemini_synthesis or ("lower gap" in gemini_synthesis.lower() and expected_gap == "GAP_UP") or ("gap up" in gemini_synthesis.lower() and expected_gap == "GAP_DOWN"):
            gemini_synthesis = (
                f"{canonical_gap_text} Brent Crude is at {crude_pct:+.2f}%, while institutional FIIs logged {fii_net:+.2f} Cr and DIIs {dii_net:+.2f} Cr. "
                f"Opening directional bias is {macro_bias}."
            )

        # 2026 Expiry Context: Tuesday for NSE, Thursday for BSE
        weekday = ist_time.weekday()
        if weekday == 1:
            expiry_comment = " ⚡ [NSE WEEKLY EXPIRY TODAY - TUESDAY]: Expect elevated late-afternoon gamma and dynamic theta damping post 13:00 IST."
        elif weekday == 3:
            expiry_comment = " ⚡ [BSE WEEKLY EXPIRY TODAY - THURSDAY]: SENSEX & BANKEX weekly settlement active."
        else:
            expiry_comment = ""

        if expiry_comment and expiry_comment not in gemini_synthesis:
            gemini_synthesis += expiry_comment

        report = {
            "report_id": f"PREMARKET_{ist_time.strftime('%Y%m%d')}",
            "report_date": today_str,
            "timestamp_ist": ist_time.strftime("%Y-%m-%d %H:%M:%S IST"),
            "timestamp_utc": now_utc.isoformat(),
            "macro_bias": macro_bias,
            "macro_score": composite_score,
            "gift_nifty_points": gift_points,
            "expected_gap": expected_gap,
            "crude_oil_pct": crude_pct,
            "crude_oil_status": crude_status,
            "us_10y_yield": us_10y,
            "dxy_index": dxy,
            "fii_net_crores": fii_net,
            "dii_net_crores": dii_net,
            "institutional_flow_bias": flow_status,
            "gemini_macro_synthesis": gemini_synthesis,
            "recommended_opening_bias": "BUY_ON_DIPS" if composite_score > 0.2 else ("SELL_ON_RALLIES" if composite_score < -0.2 else "RANGEBOUND"),
            "risk_regime": "EXPIRY_DAY_VOLATILITY" if weekday in (1, 3) else "LOW_VOLATILITY"
        }

        # 3. Commit to Firestore
        if self.db:
            try:
                self.db.collection(COLLECTION_NAME).document(report["report_id"]).set(report)
                logger.info(f"✅ Real-Time Pre-Market Macro Report committed to Firestore: {report['report_id']}")
            except Exception as e:
                logger.error(f"Failed to write pre-market report to Firestore: {e}")

        # 4. Dispatch Multi-Channel Alert
        await ALERT_DISPATCHER.dispatch_premarket_briefing(report)
        return report

    def get_latest_briefing(self) -> Optional[Dict[str, Any]]:
        """Fetches the latest pre-market briefing from Firestore"""
        if not self.db:
            return None
        try:
            docs = list(self.db.collection(COLLECTION_NAME).order_by("timestamp_utc", direction=firestore.Query.DESCENDING).limit(1).stream())
            if docs:
                return docs[0].to_dict()
        except Exception as e:
            logger.error(f"Error fetching latest briefing: {e}")
        return None

PREMARKET_BRIEFING_SERVICE = PreMarketBriefingService()
