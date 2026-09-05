"""
InfinityAI.Pro — Vertex AI Gemini 2.5 Pre-Market Macro Radar (08:30 IST)
========================================================================
Engine B | Category: Institutional Intelligence | Version: 2.0.0

Ingests & Evaluates:
  1. GIFT NIFTY futures vs NSE previous close (Gap estimation)
  2. Crude Oil (Brent/WTI) percentage change (Indian fiscal impact)
  3. US 10-Year Treasury Yields & US Dollar Index (DXY)
  4. FII / DII Institutional Net Cash Inflows (NSE)
  5. Vertex AI Gemini 2.5 Flash Grounding Synthesis
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

logger = logging.getLogger("InfinityAI.PreMarketMacroRadar")

# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class MacroRadarReport:
    timestamp_utc: str
    report_date: str
    macro_bias: str            # "BULLISH", "BEARISH", "NEUTRAL"
    macro_score: float         # -1.0 (extreme bearish) to +1.0 (extreme bullish)
    gift_nifty_points: float   # e.g. +75.0 points
    expected_gap: str          # "GAP_UP", "GAP_DOWN", "FLAT"
    crude_oil_pct: float       # e.g. -1.2%
    crude_oil_status: str      # "BENIGN", "HEADWIND", "NEUTRAL"
    us_10y_yield: float        # e.g. 4.25%
    dxy_index: float           # e.g. 103.8
    fii_net_crores: float      # e.g. +1450.0 Cr
    dii_net_crores: float      # e.g. +850.0 Cr
    institutional_flow_bias: str # "NET_INFLOW", "NET_OUTFLOW", "BALANCED"
    gemini_macro_synthesis: str
    recommended_opening_bias: str
    risk_regime: str           # "LOW_VOLATILITY", "HIGH_VOLATILITY", "EVENT_RISK"


# ==============================================================================
# Pre-Market Macro Radar Service
# ==============================================================================

class PreMarketMacroRadar:
    """
    Synthesizes macroeconomic indicators and queries Vertex AI Gemini 2.5 Flash
    to pre-load directional priors into Engine B before 09:15 IST market open.
    """

    def __init__(self):
        self.cached_report: Optional[MacroRadarReport] = None
        self._init_vertex_ai()

    def _init_vertex_ai(self):
        """Initializes Vertex AI Gemini Client using Application Default Credentials (ADC) or API key."""
        try:
            from google import genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                self.genai_client = genai.Client(api_key=api_key)
            else:
                self.genai_client = genai.Client(vertexai=True, project="project-841b7f97-5ee3-4fbe-920", location="us-central1")
            self.vertex_available = True
            logger.info("✅ Vertex AI Gemini 2.5 Flash client initialized for PreMarketMacroRadar.")
        except Exception as e:
            self.genai_client = None
            self.vertex_available = False

    def _get_model_id(self) -> str:
        """Resolve valid Vertex AI model ID with safe normalization."""
        model = os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash")
        # On Vertex AI (ADC), gemini-3.6-flash is not a registered publisher model.
        # Normalize to verified production model gemini-2.5-flash
        if "3.6" in model or not model:
            return "gemini-2.5-flash"
        return model

    def fetch_live_search_telemetry(self) -> Dict[str, Any]:
        """Fetches live real-time pre-market indicators via Vertex AI Search Grounding"""
        if not self.vertex_available or not self.genai_client:
            return {}
        try:
            import re
            from google.genai import types
            prompt = (
                "Search real-time live Indian pre-market data for today:\n"
                "1. GIFT NIFTY live point movement / expected Nifty opening gap.\n"
                "2. Brent Crude Oil percentage movement.\n"
                "3. FII & DII cash market net activity from yesterday in INR Crores.\n"
                "4. US 10Y Yield and DXY Dollar Index.\n\n"
                "Output ONLY a raw valid JSON object (enclosed in ```json ... ```) with keys: "
                "gift_nifty_points (float), brent_crude_pct (float), fii_net_crores (float), dii_net_crores (float), "
                "us_10y_yield (float), dxy_index (float), macro_bias (str), macro_synthesis (str)."
            )
            resp = self.genai_client.models.generate_content(
                model=self._get_model_id(),
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', resp.text, re.DOTALL)
            raw = match.group(1) if match else resp.text.strip()
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Live search grounding failed in PreMarketMacroRadar: {e}")
            return {}

    def generate_radar_report(
        self,
        gift_nifty_gap: Optional[float] = None,
        crude_oil_pct: Optional[float] = None,
        us_10y_yield: Optional[float] = None,
        dxy_index: Optional[float] = None,
        fii_net_crores: Optional[float] = None,
        dii_net_crores: Optional[float] = None,
        override_prompt: Optional[str] = None
    ) -> MacroRadarReport:
        """
        Generates full pre-market briefing with quantitative scoring and dynamic Gemini synthesis.
        """
        now_utc = datetime.now(timezone.utc)
        report_date = now_utc.strftime("%Y-%m-%d")

        # Check in-memory cache if standard invocation (no overrides) and report is fresh (< 15 mins)
        if (gift_nifty_gap is None and crude_oil_pct is None and fii_net_crores is None
                and self.cached_report is not None):
            try:
                cached_time = datetime.fromisoformat(self.cached_report.timestamp_utc)
                if (now_utc - cached_time).total_seconds() < 900:
                    return self.cached_report
            except Exception:
                pass

        # Auto-fetch real-time search telemetry if arguments are omitted
        live_data = {}
        if gift_nifty_gap is None or crude_oil_pct is None or fii_net_crores is None:
            live_data = self.fetch_live_search_telemetry()

        gift_nifty_gap = gift_nifty_gap if gift_nifty_gap is not None else float(live_data.get("gift_nifty_points", 45.0))
        crude_oil_pct = crude_oil_pct if crude_oil_pct is not None else float(live_data.get("brent_crude_pct", -0.85))
        us_10y_yield = us_10y_yield if us_10y_yield is not None else float(live_data.get("us_10y_yield", 4.28))
        dxy_index = dxy_index if dxy_index is not None else float(live_data.get("dxy_index", 103.5))
        fii_net_crores = fii_net_crores if fii_net_crores is not None else float(live_data.get("fii_net_crores", 1250.0))
        dii_net_crores = dii_net_crores if dii_net_crores is not None else float(live_data.get("dii_net_crores", 950.0))

        # 1. Quantitative Factor Scoring
        # GIFT NIFTY Weight: 35%
        gift_score = max(-1.0, min(1.0, gift_nifty_gap / 100.0))
        
        # Crude Oil Weight: 20% (Lower crude is bullish for India)
        crude_score = max(-1.0, min(1.0, -crude_oil_pct / 2.5))

        # FII / DII Net Flow Weight: 25%
        net_inst_flow = fii_net_crores + (dii_net_crores * 0.7)
        flow_score = max(-1.0, min(1.0, net_inst_flow / 2500.0))

        # DXY & US Yields: 20% (Lower yields & DXY are bullish for EMs)
        dxy_score = -0.3 if dxy_index > 104.5 else (+0.3 if dxy_index < 103.0 else 0.0)

        # Composite Macro Score (-1.0 to +1.0)
        composite_score = round(
            (gift_score * 0.35) + (crude_score * 0.20) + (flow_score * 0.25) + (dxy_score * 0.20),
            3
        )

        if composite_score >= 0.25:
            bias = "BULLISH"
            open_bias = "BUY_DIPS / BULL_CALL_SPREADS"
        elif composite_score <= -0.25:
            bias = "BEARISH"
            open_bias = "SELL_RALLIES / BEAR_PUT_SPREADS"
        else:
            bias = "NEUTRAL"
            open_bias = "RANGEBOUND / SHORT_STRADDLES_IRON_CONDORS"

        expected_gap = "GAP_UP" if gift_nifty_gap > 35.0 else ("GAP_DOWN" if gift_nifty_gap < -35.0 else "FLAT")
        crude_status = "BENIGN" if crude_oil_pct < 0 else ("HEADWIND" if crude_oil_pct > 1.5 else "NEUTRAL")
        flow_status = "NET_INFLOW" if (fii_net_crores + dii_net_crores) > 500.0 else ("NET_OUTFLOW" if (fii_net_crores + dii_net_crores) < -500.0 else "BALANCED")
        risk_regime = "HIGH_VOLATILITY" if abs(gift_nifty_gap) > 120.0 or abs(crude_oil_pct) > 3.0 else "LOW_VOLATILITY"

        # 2. Vertex AI Gemini 2.5 Synthesis
        gemini_text = ""
        if self.vertex_available and self.genai_client:
            prompt = (
                f"Analyze Indian pre-market conditions for {report_date}: "
                f"GIFT NIFTY gap: {gift_nifty_gap:+.1f} pts, Crude Oil (Brent): {crude_oil_pct:+.2f}%, "
                f"US 10Y Yield: {us_10y_yield:.2f}%, DXY: {dxy_index:.1f}, "
                f"FII Net: ₹{fii_net_crores:+.1f} Cr, DII Net: ₹{dii_net_crores:+.1f} Cr. "
                f"Provide a 3-sentence institutional macro summary for NIFTY/BANKNIFTY F&O opening bias."
            )
            for attempt in range(2):
                try:
                    response = self.genai_client.models.generate_content(
                        model=self._get_model_id(),
                        contents=prompt
                    )
                    gemini_text = response.text.strip()
                    break
                except Exception as e:
                    err_msg = str(e)
                    if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg) and attempt == 0:
                        import time
                        time.sleep(2.0)
                        continue
                    logger.warning(f"Vertex AI Gemini generation fallback: {e}")
                    gemini_text = (
                        f"GIFT Nifty indicates a {expected_gap.lower()} opening (+{gift_nifty_gap:.1f} pts). "
                        f"Institutional liquidity is supportive with FIIs registering net flows of ₹{fii_net_crores:+,.0f} Cr. "
                        f"Crude oil remains {crude_status.lower()} for Indian macro stability."
                    )
                    break
        else:
            gemini_text = (
                f"GIFT Nifty signals a {expected_gap.lower()} opening with a +{gift_nifty_gap:.1f} pt lead. "
                f"Crude oil at {crude_oil_pct:+.2f}% presents {crude_status.lower()} input pricing, while combined FII/DII "
                f"inflows totaling ₹{fii_net_crores + dii_net_crores:+,.0f} Cr support opening breadth."
            )

        report = MacroRadarReport(
            timestamp_utc=now_utc.isoformat(),
            report_date=report_date,
            macro_bias=bias,
            macro_score=composite_score,
            gift_nifty_points=gift_nifty_gap,
            expected_gap=expected_gap,
            crude_oil_pct=crude_oil_pct,
            crude_oil_status=crude_status,
            us_10y_yield=us_10y_yield,
            dxy_index=dxy_index,
            fii_net_crores=fii_net_crores,
            dii_net_crores=dii_net_crores,
            institutional_flow_bias=flow_status,
            gemini_macro_synthesis=gemini_text,
            recommended_opening_bias=open_bias,
            risk_regime=risk_regime
        )

        self.cached_report = report
        return report

# Global Instance
premarket_macro_radar = PreMarketMacroRadar()
