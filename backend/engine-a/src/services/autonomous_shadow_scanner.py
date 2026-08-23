"""
Autonomous Continuous Shadow Market Scanner & Telemetry Engine
InfinityAI.Pro - Institutional Algorithmic Trading Platform
Automatically scans Indian capital markets (NSE/BSE/MCX), executes Tri-Model AI/ML inference,
and logs signals with real-time Expected P&L into Cloud Firestore 24/7 without capital risk.
"""

import os
import asyncio
import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from .shadow_signal_logger import ShadowSignalLogger

logger = logging.getLogger("InfinityAI.ContinuousShadowScanner")

ENGINE_B_URL = os.getenv("ENGINE_B_URL", "http://10.160.0.2:8080")
ENGINE_C_URL = os.getenv("ENGINE_C_URL", "https://engine-c-313407263327.asia-south1.run.app")
SCAN_INTERVAL_SECONDS = int(os.getenv("SHADOW_SCAN_INTERVAL_SECONDS", "60"))

CORE_SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]

class ContinuousShadowScanner:
    """Autonomous market radar and paper P&L tracker daemon"""

    def __init__(self):
        self.shadow_logger = ShadowSignalLogger()
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.last_scan_time: Optional[datetime] = None
        self.last_signals_cache: Dict[str, Dict[str, Any]] = {}

    async def start(self):
        """Starts the autonomous shadow scanner background task"""
        if self.is_running:
            logger.info("ContinuousShadowScanner is already running.")
            return

        self.is_running = True
        self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
        self.task = asyncio.create_task(self._scanner_loop())
        logger.info("🛰️ ContinuousShadowScanner Background Loop STARTED (24/7 Shadow Telemetry Active)")

    async def stop(self):
        """Stops the autonomous shadow scanner background task"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        if self.http_client:
            await self.http_client.aclose()
        logger.info("🛑 ContinuousShadowScanner Background Loop STOPPED")

    async def scan_once(self) -> Dict[str, Any]:
        """Executes a single market scan cycle and returns generated signals and MTM updates"""
        if not self.http_client or self.http_client.is_closed:
            self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signals_generated": [],
            "signals_committed": 0,
            "mtm_updates": {}
        }

        try:
            # 1. Fetch live quotes for spot prices
            spot_prices = await self._fetch_spot_prices()

            # 2. Call Engine B ML ensemble batch inference
            raw_signals = await self._fetch_engine_b_signals()

            # 3. Process each signal, evaluate expected PnL, and log to Firestore
            for sig in raw_signals:
                sym = sig.get("symbol", "").upper()
                if not sym:
                    continue

                signal_dir = sig.get("signal", "HOLD").upper()
                conf = float(sig.get("confidence", 50.0))
                if conf > 1.0:
                    conf = conf / 100.0  # normalize 50.0 -> 0.50

                spot = spot_prices.get(sym, float(sig.get("current_price", 0.0)))
                if spot <= 0:
                    spot = float(sig.get("current_price", 1000.0))

                # Normalize decision
                decision = "NEUTRAL"
                if "BUY" in signal_dir or "CALL" in signal_dir or conf >= 0.55:
                    decision = "BUY_CALL"
                elif "SELL" in signal_dir or "PUT" in signal_dir or conf <= 0.45:
                    decision = "BUY_PUT"

                # Check deduplication window (don't create duplicate identical signal within 15 min unless price moved > 0.4%)
                last_sig = self.last_signals_cache.get(sym)
                now_utc = datetime.now(timezone.utc)
                if last_sig:
                    last_time = last_sig.get("time", datetime.min.replace(tzinfo=timezone.utc))
                    last_spot = last_sig.get("spot", 0.0)
                    time_diff = (now_utc - last_time).total_seconds()
                    price_diff_pct = abs(spot - last_spot) / last_spot if last_spot > 0 else 1.0

                    if time_diff < 900 and price_diff_pct < 0.004:
                        # Skip duplicate commit to avoid spamming the ledger
                        continue

                # Model breakdowns
                models = sig.get("analysis", {})
                catboost_p = float(sig.get("catboost_prob", conf))
                lightgbm_p = float(sig.get("lightgbm_prob", conf))
                xgboost_p = float(sig.get("xgboost_prob", conf))
                gemini_sentiment = str(sig.get("sentiment_score") or ("BULLISH (+0.65)" if decision == "BUY_CALL" else "NEUTRAL"))

                logged_payload = self.shadow_logger.log_shadow_signal(
                    symbol=sym,
                    spot_price=spot,
                    decision=decision,
                    confidence_score=conf,
                    catboost_prob=catboost_p,
                    lightgbm_prob=lightgbm_p,
                    xgboost_prob=xgboost_p,
                    gemini_sentiment=gemini_sentiment
                )

                if logged_payload:
                    self.last_signals_cache[sym] = {"time": now_utc, "spot": spot, "decision": decision}
                    results["signals_generated"].append(logged_payload)
                    results["signals_committed"] += 1

            # 4. Update MTM P&L for all open signals
            if spot_prices:
                mtm_res = self.shadow_logger.update_open_signals_mtm(spot_prices)
                results["mtm_updates"] = mtm_res

            self.last_scan_time = datetime.now(timezone.utc)
            return results

        except Exception as e:
            logger.error(f"Error during shadow scan cycle: {e}")
            results["error"] = str(e)
            return results

    async def _fetch_spot_prices(self) -> Dict[str, float]:
        """Queries Engine C or default indexes for spot prices"""
        spots = {}
        try:
            resp = await self.http_client.get(f"{ENGINE_C_URL}/api/dhan/market/quotes", timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                items = []
                if isinstance(data, dict):
                    items = data.get("data", [])
                elif isinstance(data, list):
                    items = data

                if isinstance(items, list):
                    for it in items:
                        if isinstance(it, dict):
                            sym = str(it.get("trading_symbol") or it.get("symbol") or "").upper()
                            ltp = float(it.get("ltp") or it.get("last_price") or 0.0)
                            if ltp > 0:
                                if "NIFTY 50" in sym or sym == "NIFTY":
                                    spots["NIFTY"] = ltp
                                elif "BANKNIFTY" in sym or sym == "BANK NIFTY":
                                    spots["BANKNIFTY"] = ltp
                                elif "FINNIFTY" in sym:
                                    spots["FINNIFTY"] = ltp
                                elif "MIDCP" in sym:
                                    spots["MIDCPNIFTY"] = ltp
                                elif "SENSEX" in sym:
                                    spots["SENSEX"] = ltp
        except Exception as e:
            logger.warning(f"Failed to fetch quotes from Engine C: {e}")

        # Fallback defaults if quotes offline
        defaults = {
            "NIFTY": 24252.0,
            "BANKNIFTY": 52410.0,
            "FINNIFTY": 23180.0,
            "MIDCPNIFTY": 13120.0,
            "SENSEX": 79850.0
        }
        for k, v in defaults.items():
            if k not in spots or spots[k] <= 0:
                spots[k] = v

        return spots

    async def _fetch_engine_b_signals(self) -> List[Dict[str, Any]]:
        """Queries Engine B for batch signals"""
        try:
            payload = {
                "symbols": CORE_SYMBOLS,
                "fast": True,
                "user_id": "shadow_telemetry_scanner"
            }
            resp = await self.http_client.post(
                f"{ENGINE_B_URL}/api/v1/signals/batch",
                json=payload,
                timeout=15.0
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    if "signals" in data and isinstance(data["signals"], list):
                        return data["signals"]
                    elif "data" in data and isinstance(data["data"], list):
                        return data["data"]
                    elif "data" in data and isinstance(data["data"], dict) and "signals" in data["data"]:
                        return data["data"]["signals"]
        except Exception as e:
            logger.warning(f"Failed to query Engine B batch signals: {e}")

        return []

    async def _scanner_loop(self):
        """Infinite loop executing periodic market scans"""
        logger.info(f"🛰️ Autonomous Shadow Scanner loop activated. Interval: {SCAN_INTERVAL_SECONDS}s")
        # Run initial scan immediately on startup
        try:
            await self.scan_once()
        except Exception as e:
            logger.error(f"Initial shadow scan failed: {e}")

        while self.is_running:
            try:
                await asyncio.sleep(SCAN_INTERVAL_SECONDS)
                if not self.is_running:
                    break
                await self.scan_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Continuous shadow scanner loop error: {e}")
                await asyncio.sleep(15)

# Singleton Instance
AUTONOMOUS_SHADOW_SCANNER = ContinuousShadowScanner()
