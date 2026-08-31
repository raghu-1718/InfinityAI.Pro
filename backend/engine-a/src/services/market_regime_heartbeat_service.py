"""
Scheduled Market Regime & Volatility Heartbeat Service
InfinityAI.Pro - Institutional Algorithmic Trading Platform
Dispatches periodic telemetry digests (10:30, 12:00, 14:00 IST)
to ensure transparent market regime visibility during chop and consolidation phases.
"""

import os
import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

try:
    from google.cloud import firestore
except Exception:
    firestore = None

from .alert_dispatcher import ALERT_DISPATCHER

logger = logging.getLogger("InfinityAI.MarketRegimeHeartbeat")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
ENGINE_B_URL = os.getenv("ENGINE_B_URL", "https://engine-b-r2f5flt77q-el.a.run.app")
ENGINE_C_URL = os.getenv("ENGINE_C_URL", "https://engine-c-r2f5flt77q-el.a.run.app")
COLLECTION_NAME = "market_regime_heartbeats"

class MarketRegimeHeartbeatService:
    """Orchestrates scheduled intraday market regime digests"""

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        self.db = None
        if firestore:
            try:
                self.db = firestore.Client(project=project_id)
            except Exception as e:
                logger.warning(f"MarketRegimeHeartbeatService Firestore init warning: {e}")

    async def _fetch_live_market_quotes(self) -> Dict[str, float]:
        """Fetches latest spot prices and India VIX from Engine C"""
        spot_prices = {"NIFTY": 24080.0, "BANKNIFTY": 57490.0, "SENSEX": 77260.0, "INDIAVIX": 13.5}
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.get(f"{ENGINE_C_URL}/api/dhan/market/quotes")
                if resp.status_code == 200:
                    data = resp.json()

                    def extract_quotes(obj):
                        if isinstance(obj, dict):
                            sym = str(obj.get("symbol") or obj.get("trading_symbol", "")).upper()
                            ltp = float(obj.get("ltp") or obj.get("last_price", 0.0))
                            if ltp > 0:
                                if "NIFTY 50" in sym or sym == "NIFTY": spot_prices["NIFTY"] = ltp
                                elif "BANKNIFTY" in sym or sym == "BANK NIFTY": spot_prices["BANKNIFTY"] = ltp
                                elif "SENSEX" in sym: spot_prices["SENSEX"] = ltp
                                elif "INDIA VIX" in sym or "INDIAVIX" in sym: spot_prices["INDIAVIX"] = ltp
                            for v in obj.values():
                                extract_quotes(v)
                        elif isinstance(obj, list):
                            for it in obj:
                                extract_quotes(it)

                    extract_quotes(data)
        except Exception as e:
            logger.warning(f"Failed to fetch live quotes for regime heartbeat: {e}")
        return spot_prices

    async def _fetch_engine_b_regime_telemetry(self) -> Dict[str, Any]:
        """Queries Engine B for real-time model analysis and ADX telemetry with Firestore fallback"""
        adx_list = []
        vetoes = []
        consensus_signals = {}

        # 1. Primary: Direct HTTP Batch Inference call to Engine B
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(
                    f"{ENGINE_B_URL}/api/v1/signals/batch",
                    json={"symbols": ["NIFTY", "BANKNIFTY", "SENSEX"], "user_id": "raghu_primary"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    signals = data.get("signals", [])
                    for s in signals:
                        sym = s.get("symbol", "")
                        sig = s.get("signal", "HOLD")
                        consensus_signals[sym] = sig
                        analysis = s.get("analysis", {})
                        adx = float(analysis.get("adx", 20.0))
                        adx_list.append(adx)
                        veto_reason = analysis.get("veto_reason")
                        if veto_reason and veto_reason not in vetoes:
                            vetoes.append(f"{sym}: {veto_reason}")
        except Exception as e:
            logger.info(f"Engine B HTTP batch lookup skipped ({e}); querying Firestore signals cache...")

        # 2. Resilient Fallback: Query latest computed signals from Firestore
        if not adx_list and self.db:
            try:
                docs = list(self.db.collection("signals").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).stream())
                seen_syms = set()
                for doc in docs:
                    d = doc.to_dict()
                    sym = d.get("symbol", "")
                    if sym in seen_syms:
                        continue
                    seen_syms.add(sym)
                    consensus_signals[sym] = d.get("signal", "HOLD")
                    analysis = d.get("analysis", {})
                    adx = float(analysis.get("adx", 16.0))
                    adx_list.append(adx)
                    veto_reason = analysis.get("veto_reason")
                    if veto_reason and veto_reason not in vetoes:
                        vetoes.append(f"{sym}: {veto_reason}")
            except Exception as fe:
                logger.warning(f"Firestore signals fallback warning: {fe}")

        avg_adx = round(sum(adx_list) / len(adx_list), 1) if adx_list else 15.5
        return {
            "adx_avg": avg_adx,
            "active_vetoes": vetoes,
            "consensus_signals": consensus_signals
        }

    async def generate_and_dispatch_heartbeat(self) -> Dict[str, Any]:
        """Generates the real-time regime digest, persists to Firestore, and dispatches via Telegram"""
        now_utc = datetime.now(timezone.utc)
        ist_time = now_utc + timedelta(hours=5, minutes=30)
        timestamp_str = ist_time.strftime("%Y-%m-%d %H:%M:%S IST")

        # 1. Fetch live market quotes
        quotes = await self._fetch_live_market_quotes()
        nifty = quotes.get("NIFTY", 24080.0)
        banknifty = quotes.get("BANKNIFTY", 57490.0)
        sensex = quotes.get("SENSEX", 77260.0)
        vix = quotes.get("INDIAVIX", 13.5)

        # 2. Fetch Engine B telemetry
        telemetry = await self._fetch_engine_b_regime_telemetry()
        adx_avg = telemetry.get("adx_avg", 15.5)
        vetoes = telemetry.get("active_vetoes", [])

        # 3. Classify Regime & Guidance
        if vix > 22.0:
            regime = "HIGH_VOLATILITY_TURBULENCE"
            badge = "BLACK SWAN ELEVATED"
            guidance = "Elevated India VIX. Dynamic risk dampers & wide trailing profit locks engaged."
        elif adx_avg < 22.0 or len(vetoes) > 0:
            regime = "RANGEBOUND_CONSOLIDATION"
            badge = "CHOP FILTER ACTIVE"
            guidance = "Low ADX trend momentum. Option buying suppressed to preserve capital against theta decay."
        else:
            regime = "DIRECTIONAL_TREND_EXPANSION"
            badge = "MOMENTUM ACTIVE"
            guidance = "Strong directional breakout confirmed. Tri-Model ensemble actively seeking high-conviction entries."

        heartbeat_doc = {
            "heartbeat_id": f"REGIME_{ist_time.strftime('%Y%m%d_%H%M%S')}",
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_ist": timestamp_str,
            "regime": regime,
            "status_badge": badge,
            "nifty_spot": nifty,
            "banknifty_spot": banknifty,
            "sensex_spot": sensex,
            "india_vix": vix,
            "adx_avg": adx_avg,
            "active_vetoes": vetoes,
            "guidance": guidance
        }

        # 4. Commit to Firestore
        if self.db:
            try:
                self.db.collection(COLLECTION_NAME).document(heartbeat_doc["heartbeat_id"]).set(heartbeat_doc)
                logger.info(f"✅ Market Regime Heartbeat committed to Firestore: {heartbeat_doc['heartbeat_id']}")
            except Exception as e:
                logger.error(f"Failed to write regime heartbeat to Firestore: {e}")

        # 5. Dispatch Alert
        await ALERT_DISPATCHER.dispatch_market_regime_heartbeat(heartbeat_doc)
        return heartbeat_doc

MARKET_REGIME_HEARTBEAT_SERVICE = MarketRegimeHeartbeatService()
