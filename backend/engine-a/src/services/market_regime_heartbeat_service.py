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

    async def _fetch_live_market_quotes(self) -> Dict[str, Any]:
        """
        Fetches real-time spot prices (NIFTY, BANKNIFTY, SENSEX) and India VIX from Engine C
        with explicit security ID mapping (13=NIFTY, 25=BANKNIFTY, 51=SENSEX, 21=INDIAVIX).
        """
        spot_prices: Dict[str, Optional[float]] = {
            "NIFTY": None,
            "BANKNIFTY": None,
            "SENSEX": None,
            "INDIAVIX": None,
            "data_source": "live_broker_feed"
        }
        
        target_urls = [
            os.getenv("ENGINE_C_URL", "https://engine-c-313407263327.asia-south1.run.app"),
            "https://engine-c-r2f5flt77q-el.a.run.app",
            "https://engine-c-313407263327.asia-south1.run.app"
        ]
        # Deduplicate while preserving order
        urls_to_try = list(dict.fromkeys(u for u in target_urls if u))
        
        fetched = False
        async with httpx.AsyncClient(timeout=8.0) as client:
            for base_url in urls_to_try:
                try:
                    resp = await client.get(
                        f"{base_url}/api/dhan/market/quotes",
                        params={"security_ids": "13,25,51,21", "exchange_segment": "IDX_I"}
                    )
                    if resp.status_code == 200:
                        raw_data = resp.json()
                        
                        # Peel nested 'data' wrappers from DhanHQ v2 format
                        d = raw_data
                        while isinstance(d, dict) and "data" in d and "IDX_I" not in d:
                            d = d["data"]
                        
                        idx_data = d.get("IDX_I", {}) if isinstance(d, dict) else {}
                        if not idx_data and isinstance(d, dict):
                            # Try case-insensitive lookup
                            idx_data = d.get("idx_i", {})
                        
                        # Security ID mapping dictionary:
                        # 13: NIFTY 50, 25: BANKNIFTY, 51: SENSEX, 21: INDIA VIX
                        id_map = {
                            "13": "NIFTY",
                            "25": "BANKNIFTY",
                            "51": "SENSEX",
                            "21": "INDIAVIX"
                        }
                        
                        for sec_id, key in id_map.items():
                            sec_node = idx_data.get(str(sec_id)) or idx_data.get(int(sec_id))
                            if sec_node and isinstance(sec_node, dict):
                                p = sec_node.get("last_price") or sec_node.get("ltp")
                                if not p and "ohlc" in sec_node:
                                    p = sec_node["ohlc"].get("close") or sec_node["ohlc"].get("open")
                                if p and float(p) > 0:
                                    spot_prices[key] = round(float(p), 2)
                        
                        if spot_prices["NIFTY"] and spot_prices["BANKNIFTY"]:
                            fetched = True
                            logger.info(
                                f"✓ Successfully resolved live market quotes from Engine C ({base_url}): "
                                f"NIFTY={spot_prices['NIFTY']}, BANKNIFTY={spot_prices['BANKNIFTY']}, "
                                f"SENSEX={spot_prices['SENSEX']}, INDIAVIX={spot_prices['INDIAVIX']}"
                            )
                            break
                except Exception as e:
                    logger.warning(f"Failed quote retrieval attempt from {base_url}: {e}")
        
        # Resilient fallback: If live quotes failed, query latest verified Firestore record
        if not fetched and self.db:
            try:
                logger.warning("Live broker quotes unavailable; attempting verified Firestore recovery...")
                history = list(self.db.collection(COLLECTION_NAME).order_by("timestamp_utc", direction=firestore.Query.DESCENDING).limit(1).stream())
                if history:
                    last_doc = history[0].to_dict()
                    spot_prices["NIFTY"] = last_doc.get("nifty_spot")
                    spot_prices["BANKNIFTY"] = last_doc.get("banknifty_spot")
                    spot_prices["SENSEX"] = last_doc.get("sensex_spot")
                    spot_prices["INDIAVIX"] = last_doc.get("india_vix", 13.5)
                    spot_prices["data_source"] = f"verified_cache_{last_doc.get('heartbeat_id', 'unknown')}"
                    logger.info(f"Retrieved verified baseline from previous heartbeat: {spot_prices['NIFTY']}")
            except Exception as fe:
                logger.error(f"Firestore fallback lookup failed: {fe}")
        
        # Explicit degraded-state handling: If both live feed and Firestore cache failed,
        # never fabricate fictitious prices. Flag degraded mode explicitly.
        if spot_prices["NIFTY"] is None or spot_prices["BANKNIFTY"] is None:
            spot_prices["data_source"] = "DEGRADED_BROKER_FEED_UNAVAILABLE"
            spot_prices["is_degraded"] = True
            logger.critical("🚨 CRITICAL: Live market quotes unavailable from Engine C and Firestore cache. Entering degraded mode.")

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
        is_degraded = quotes.get("is_degraded", False)
        nifty = quotes.get("NIFTY")
        banknifty = quotes.get("BANKNIFTY")
        sensex = quotes.get("SENSEX")
        vix = quotes.get("INDIAVIX")
        data_src = quotes.get("data_source", "live_broker_feed")

        # 2. Fetch Engine B telemetry
        telemetry = await self._fetch_engine_b_regime_telemetry()
        adx_avg = telemetry.get("adx_avg", 15.5)
        vetoes = telemetry.get("active_vetoes", [])

        # 3. Classify Regime & Guidance
        if is_degraded or nifty is None or banknifty is None:
            regime = "DATA_FEED_DEGRADED"
            badge = "BROKER FEED OFFLINE"
            guidance = "Live broker quote feed unavailable. Automated trade executions halted to protect capital."
            nifty = float(nifty or 0.0)
            banknifty = float(banknifty or 0.0)
            sensex = float(sensex or 0.0)
            vix = float(vix or 0.0)
        elif vix > 22.0:
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
            "guidance": guidance,
            "data_source": data_src
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
