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
    gift_nifty_points: Optional[float] = None   # e.g. +75.0 points or None if unavailable
    expected_gap: Optional[str] = "UNAVAILABLE" # "GAP_UP", "GAP_DOWN", "FLAT", "UNAVAILABLE"
    crude_oil_pct: Optional[float] = None
    crude_oil_status: Optional[str] = "UNAVAILABLE"
    us_10y_yield: Optional[float] = None
    dxy_index: Optional[float] = None
    fii_net_crores: Optional[float] = None
    dii_net_crores: Optional[float] = None
    institutional_flow_bias: str = "BALANCED" # "NET_INFLOW", "NET_OUTFLOW", "BALANCED"
    gemini_macro_synthesis: str = ""
    recommended_opening_bias: str = "RANGEBOUND / SHORT_STRADDLES_IRON_CONDORS"
    risk_regime: str = "LOW_VOLATILITY"       # "LOW_VOLATILITY", "HIGH_VOLATILITY", "EVENT_RISK"


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
                "You are an institutional quantitative macro research analyst for Indian capital markets (NSE/BSE).\n"
                "CRITICAL SYSTEM INSTRUCTION: Never invent or estimate spot prices from training memory if a feed returns only percentage change; print SPOT_UNAVAILABLE instead.\n\n"
                "Search real-time live Indian and global financial market data for today across verified sources "
                "(Moneycontrol, The Economic Times, Livemint, Reuters, Bloomberg, NSE India, BSE India, and RBI) and extract BOTH raw spot values and percentage changes:\n"
                "1. GIFT NIFTY live futures spot price (or SPOT_UNAVAILABLE), live points change, and estimated market opening gap for NIFTY 50.\n"
                "2. Brent Crude Oil live spot price in USD (or SPOT_UNAVAILABLE) and percentage change.\n"
                "3. FII and DII cash market net flow from the latest session in INR Crores.\n"
                "4. US 10-Year Treasury Yield raw yield and US Dollar Index (DXY) spot value.\n"
                "5. Top breaking domestic/global market catalysts, corporate earnings surprises, or central bank news.\n\n"
                "Output ONLY a raw valid JSON object (enclosed in ```json ... ```) with exact keys:\n"
                "{\n"
                '  "gift_nifty_spot": float | "SPOT_UNAVAILABLE",\n'
                '  "gift_nifty_points": float,\n'
                '  "brent_crude_spot": float | "SPOT_UNAVAILABLE",\n'
                '  "brent_crude_pct": float,\n'
                '  "fii_net_crores": float,\n'
                '  "dii_net_crores": float,\n'
                '  "us_10y_yield": float,\n'
                '  "dxy_index": float,\n'
                '  "macro_bias": "BULLISH" | "BEARISH" | "NEUTRAL",\n'
                '  "macro_score": float between -1.0 and +1.0,\n'
                '  "macro_synthesis": string summarizing key catalysts,\n'
                '  "top_sources": list of string website domains used\n'
                "}"
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
            data = json.loads(raw)
            logger.info(f"🌐 [PreMarketMacroRadar] Live search telemetry grounded via Vertex AI: {data.get('macro_bias')} (Score: {data.get('macro_score')})")
            return data
        except Exception as e:
            logger.warning(f"Live search grounding fallback in PreMarketMacroRadar: {e}")
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

        gift_nifty_gap = gift_nifty_gap if gift_nifty_gap is not None else (float(live_data["gift_nifty_points"]) if "gift_nifty_points" in live_data else None)
        crude_oil_pct = crude_oil_pct if crude_oil_pct is not None else (float(live_data["brent_crude_pct"]) if "brent_crude_pct" in live_data else None)
        us_10y_yield = us_10y_yield if us_10y_yield is not None else (float(live_data["us_10y_yield"]) if "us_10y_yield" in live_data else None)
        dxy_index = dxy_index if dxy_index is not None else (float(live_data["dxy_index"]) if "dxy_index" in live_data else None)
        fii_net_crores = fii_net_crores if fii_net_crores is not None else (float(live_data["fii_net_crores"]) if "fii_net_crores" in live_data else None)
        dii_net_crores = dii_net_crores if dii_net_crores is not None else (float(live_data["dii_net_crores"]) if "dii_net_crores" in live_data else None)

        # 1. Quantitative Factor Scoring
        gift_score = max(-1.0, min(1.0, gift_nifty_gap / 100.0)) if gift_nifty_gap is not None else 0.0
        crude_score = max(-1.0, min(1.0, -crude_oil_pct / 2.5)) if crude_oil_pct is not None else 0.0

        if fii_net_crores is not None and dii_net_crores is not None:
            net_inst_flow = fii_net_crores + (dii_net_crores * 0.7)
            flow_score = max(-1.0, min(1.0, net_inst_flow / 2500.0))
            flow_status = "NET_INFLOW" if (fii_net_crores + dii_net_crores) > 500.0 else ("NET_OUTFLOW" if (fii_net_crores + dii_net_crores) < -500.0 else "BALANCED")
        else:
            flow_score = 0.0
            flow_status = "BALANCED"

        if dxy_index is not None:
            dxy_score = -0.3 if dxy_index > 104.5 else (+0.3 if dxy_index < 103.0 else 0.0)
        else:
            dxy_score = 0.0

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

        expected_gap = ("GAP_UP" if gift_nifty_gap > 35.0 else ("GAP_DOWN" if gift_nifty_gap < -35.0 else "FLAT")) if gift_nifty_gap is not None else "UNAVAILABLE"
        crude_status = ("BENIGN" if crude_oil_pct < 0 else ("HEADWIND" if crude_oil_pct > 1.5 else "NEUTRAL")) if crude_oil_pct is not None else "UNAVAILABLE"
        risk_regime = "HIGH_VOLATILITY" if ((gift_nifty_gap and abs(gift_nifty_gap) > 120.0) or (crude_oil_pct and abs(crude_oil_pct) > 3.0)) else "LOW_VOLATILITY"

        # 2. Vertex AI Gemini 2.5 Synthesis
        gemini_text = ""
        gap_desc = f"{gift_nifty_gap:+.1f} pts" if gift_nifty_gap is not None else "N/A"
        crude_desc = f"{crude_oil_pct:+.2f}%" if crude_oil_pct is not None else "N/A"
        fii_desc = f"₹{fii_net_crores:+.1f} Cr" if fii_net_crores is not None else "N/A"
        dii_desc = f"₹{dii_net_crores:+.1f} Cr" if dii_net_crores is not None else "N/A"
        yield_desc = f"{us_10y_yield:.2f}%" if us_10y_yield is not None else "N/A"
        dxy_desc = f"{dxy_index:.1f}" if dxy_index is not None else "N/A"

        if self.vertex_available and self.genai_client:
            prompt = (
                f"Analyze Indian pre-market conditions for {report_date}: "
                f"GIFT NIFTY gap: {gap_desc}, Crude Oil (Brent): {crude_desc}, "
                f"US 10Y Yield: {yield_desc}, DXY: {dxy_desc}, "
                f"FII Net: {fii_desc}, DII Net: {dii_desc}. "
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
                        f"Macro regime stands {bias} with institutional liquidity rated {flow_status}. "
                        f"Opening structure indicates {expected_gap.lower()} setup with {crude_status.lower()} crude oil environment."
                    )
                    break
        else:
            gemini_text = (
                f"Macro regime indicates {bias} opening conditions with institutional liquidity rated {flow_status}. "
                f"Underlying market breadth supports {open_bias.lower()} positioning."
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
