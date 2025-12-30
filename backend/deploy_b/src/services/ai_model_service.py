import os
import yaml
import logging
import numpy as np
from typing import Dict, List
from datetime import datetime

from core.utils import utc_now
from src.services.data_connector import DataConnector
from src.services.feature_pipeline import extract_snapshot_features, BASIC_FEATURES
from src.services.sentiment_service import SentimentService
from src.services.model_zoo import ModelZoo
from src.services.ensemble_service import weighted_ensemble
from src.services.strategy_engine import compute_risk_return
from models.domain import AISignal

logger = logging.getLogger("engine_b.ai_model_service")


class AIModelService:
    """
    Core AI inference service for Engine B.

    Responsibilities:
    - Fetch snapshot + news
    - Extract features
    - Run ensemble prediction
    - Apply sentiment tilt
    - Compute risk-adjusted signal
    """

    def __init__(self, settings_path: str = "config/settings.yaml"):
        self.cfg = self._load_config(settings_path)

        self.connector = DataConnector(
            base_url=os.getenv(
                "ENGINE_A_URL",
                self.cfg["engine_a"]["base_url"]
            )
        )

        self.sentiment = SentimentService(
            enabled=self.cfg["models"]["enable_transformers_sentiment"]
        )

        self.mz = ModelZoo()
        self.weights = self.cfg["models"]["ensemble"]["weights"]
        self.features = BASIC_FEATURES

        # self._bootstrap_models()  # Removed synthetic bootstrapping

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    async def predict_symbol(self, symbol: str, fast: bool = False) -> AISignal:
        """
        Predict a single symbol.

        fast=True:
          - skips news sentiment
          - minimizes I/O
          - lower latency
        """
        symbol = symbol.upper()

        snap = await self.connector.fetch_snapshot(symbol)
        if not snap:
            logger.warning(f"No snapshot data for {symbol}")

        news = [] if fast else await self.connector.fetch_news(5)

        # --- Price extraction (defensive) ---
        curr_price = float(
            snap.get("price")
            or snap.get("last_price")
            or snap.get("close")
            or 100.0
        )

        # --- Sentiment ---
        news_sent = 0.0 if fast else self.sentiment.score_news(news)
        news_sent = float(max(-1.0, min(1.0, news_sent)))

        # --- Feature extraction ---
        X = extract_snapshot_features(snap)
        if X.shape[0] != len(self.features):
            logger.warning(
                f"Feature mismatch for {symbol}: "
                f"{X.shape[0]} vs {len(self.features)}"
            )

        # --- Model predictions ---
        components = self.mz.predict_tabular(X)

        # Sentiment tilt (small, bounded)
        sentiment_tilt = curr_price * 0.002 * news_sent
        for k in components:
            components[k] += sentiment_tilt

        ens_price = weighted_ensemble(components, self.weights)

        stop, target, exp_ret = compute_risk_return(
            curr_price,
            ens_price,
            atr=None,
            stop_mult=self.cfg["models"]["risk"]["stop_atr_mult"],
            rr_target=self.cfg["models"]["risk"]["target_rr"],
        )

        delta = (ens_price - curr_price) / curr_price
        abs_delta = abs(delta)

        confidence = float(
            min(95.0, max(55.0, (abs_delta * 100 * 2) + 55.0))
        )

        if delta > 0.015:
            signal = "BUY"
        elif delta < -0.015:
            signal = "SELL"
        else:
            signal = "HOLD"

        return AISignal(
            symbol=symbol,
            predicted_price=round(float(ens_price), 2),
            confidence=round(confidence, 2),
            signal_type=signal,
            expected_return=round(float(delta), 4),
            risk_score=min(1.0, abs_delta * 15.0),
            time_horizon="4H",
            model_version=self.cfg["service"]["version"],
            features_used=self.features,
            components={k: round(float(v), 4) for k, v in components.items()},
            timestamp=utc_now(),
        )

    async def batch_signals(
        self,
        symbols: List[str],
        fast: bool = False
    ) -> List[AISignal]:
        results: List[AISignal] = []

        for symbol in symbols:
            try:
                results.append(
                    await self.predict_symbol(symbol, fast=fast)
                )
            except Exception as e:
                logger.error(
                    f"Batch signal failed for {symbol}: {e}",
                    exc_info=True
                )

        return results
