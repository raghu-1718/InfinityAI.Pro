"""
InfinityAI.Pro — Real-Time FII / DII Institutional Delta & Flow Radar
=====================================================================
Ingests and analyzes real-time institutional activity:
  • FII Net Cash Inflows / Outflows (₹ Crores)
  • DII Net Cash Inflows / Outflows (₹ Crores)
  • FII Index Futures Long vs. Short Ratio
  • Option Chain Institutional Volume Velocity

Generates:
  • Institutional Conviction Multiplier: 0.85x to 1.25x
  • Institutional Flow Regime: HEAVY_ACCUMULATION, MODERATE_BUYING, BALANCED, DUMPING
"""

import os
import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("InfinityAI.FIIDIIRadar")

class FIIDIIFlowRadar:
    """Real-Time Institutional Smart Money Tracker & Alpha Multiplier Engine"""

    def __init__(self):
        self._cached_data: Optional[Dict[str, Any]] = None
        self._cached_time: float = 0.0

    def fetch_live_institutional_flow(self) -> Dict[str, Any]:
        """
        Fetches authentic real-time institutional flow & futures positions from exchange telemetry.
        Defaults strictly to 1.0x neutral baseline if live feed is unavailable.
        """
        now_utc = datetime.now(timezone.utc)
        
        # Check cache freshness (< 15 min)
        if self._cached_data and (now_utc.timestamp() - self._cached_time < 900):
            return self._cached_data

        fii_cash_net = 0.0
        dii_cash_net = 0.0
        fii_fut_long = 0
        fii_fut_short = 0
        source = "NEUTRAL_FALLBACK"

        # 1. Attempt to query Firestore macro cache (ingested daily from NSE participant OI)
        try:
            from google.cloud import firestore
            db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920"))
            today_str = (now_utc + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d")
            doc_snap = db.collection("macro_fii_dii_flow").document(today_str).get()
            if doc_snap.exists:
                payload = doc_snap.to_dict()
                fii_cash_net = float(payload.get("fii_net_cash", 0.0))
                dii_cash_net = float(payload.get("dii_net_cash", 0.0))
                fii_fut_long = int(payload.get("fii_fut_long", 0))
                fii_fut_short = int(payload.get("fii_fut_short", 0))
                source = f"FIRESTORE_NSE_DAILY_{today_str}"
        except Exception as e:
            logger.debug(f"Firestore macro flow query note: {e}")

        # 2. Attempt to query live exchange endpoint if configured
        if source == "NEUTRAL_FALLBACK":
            try:
                exchange_feed_url = os.getenv("EXCHANGE_FLOW_URL")
                if exchange_feed_url:
                    req = urllib.request.Request(exchange_feed_url, headers={"User-Agent": "InfinityAI/4.0"})
                    with urllib.request.urlopen(req, timeout=5) as response:
                        if response.status == 200:
                            payload = json.loads(response.read().decode("utf-8"))
                            fii_cash_net = float(payload.get("fii_net_cash", 0.0))
                            dii_cash_net = float(payload.get("dii_net_cash", 0.0))
                            fii_fut_long = int(payload.get("fii_fut_long", 0))
                            fii_fut_short = int(payload.get("fii_fut_short", 0))
                            source = "LIVE_EXCHANGE_FEED"
            except Exception as e:
                logger.debug(f"Live flow query note (using neutral baseline): {e}")

        total_net_cash = fii_cash_net + dii_cash_net
        total_fut = fii_fut_long + fii_fut_short
        fii_long_ratio = round((fii_fut_long / max(total_fut, 1)) * 100.0, 2) if total_fut > 0 else 50.0
        fii_long_short_ratio = round(fii_fut_long / max(fii_fut_short, 1), 2) if fii_fut_short > 0 else 1.0

        # Calculate Institutional Multiplier (0.85x to 1.25x)
        if total_net_cash >= 1500.0 and fii_long_ratio >= 58.0:
            multiplier = 1.25
            regime = "HEAVY_INSTITUTIONAL_ACCUMULATION"
            bias = "STRONG_BULLISH"
        elif total_net_cash >= 500.0 and fii_long_ratio >= 52.0:
            multiplier = 1.10
            regime = "MODERATE_INSTITUTIONAL_BUYING"
            bias = "BULLISH"
        elif total_net_cash <= -1500.0 and fii_long_ratio <= 42.0:
            multiplier = 0.85
            regime = "HEAVY_INSTITUTIONAL_DISTRIBUTION"
            bias = "STRONG_BEARISH"
        elif total_net_cash <= -500.0 and fii_long_ratio <= 48.0:
            multiplier = 0.90
            regime = "MODERATE_INSTITUTIONAL_SELLING"
            bias = "BEARISH"
        else:
            multiplier = 1.00
            regime = "BALANCED_EQUILIBRIUM"
            bias = "NEUTRAL"

        res = {
            "timestamp": now_utc.isoformat(),
            "fii_net_crores": fii_cash_net,
            "dii_net_crores": dii_cash_net,
            "total_net_institutional_flow_cr": round(total_net_cash, 2),
            "fii_index_futures_long_contracts": fii_fut_long,
            "fii_index_futures_short_contracts": fii_fut_short,
            "fii_long_exposure_pct": fii_long_ratio,
            "fii_long_short_ratio": fii_long_short_ratio,
            "institutional_multiplier": multiplier,
            "regime": regime,
            "directional_bias": bias,
            "data_source": source
        }
        self._cached_data = res
        self._cached_time = now_utc.timestamp()
        return res

    def apply_multiplier_to_confidence(
        self,
        base_confidence: float,
        signal_type: str = "BUY_CALL"
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Adjusts raw Tri-Model confidence score based on real-time institutional flow.
        """
        flow = self.fetch_live_institutional_flow()
        mult = flow["institutional_multiplier"]
        bias = flow["directional_bias"]

        # If signal aligns with institutional direction, apply boost; if opposes, apply dampener
        is_call = "CALL" in signal_type.upper() or "BUY" in signal_type.upper()
        if is_call:
            adjusted_conf = min(base_confidence * mult, 0.98) if "BULLISH" in bias else (
                max(base_confidence * 0.90, 0.40) if "BEARISH" in bias else base_confidence
            )
        else:
            # Put Option Buying
            adjusted_conf = min(base_confidence * (2.0 - mult), 0.98) if "BEARISH" in bias else (
                max(base_confidence * 0.90, 0.40) if "BULLISH" in bias else base_confidence
            )

        return round(float(adjusted_conf), 4), flow

FII_DII_FLOW_RADAR = FIIDIIFlowRadar()
