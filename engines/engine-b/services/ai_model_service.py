import numpy as np, pandas as pd
from datetime import datetime
from dataclasses import asdict
from typing import Dict, List
from core.utils import utc_now
from services.data_connector import DataConnector
from services.feature_pipeline import extract_snapshot_features, BASIC_FEATURES
from services.sentiment_service import SentimentService
from services.model_zoo import ModelZoo
from services.ensemble_service import weighted_ensemble
from services.strategy_engine import compute_risk_return
from models.domain import AISignal

import logging, os, yaml
logger = logging.getLogger("ai_model_service")

class AIModelService:
    def __init__(self, settings_path: str = "config/settings.yaml"):
        with open(settings_path, "r") as f:
            self.cfg = yaml.safe_load(f)
        self.connector = DataConnector(base_url=os.getenv("ENGINE_A_URL", self.cfg["engine_a"]["base_url"]))
        self.sentiment = SentimentService(enabled=self.cfg["models"]["enable_transformers_sentiment"])
        self.mz = ModelZoo()
        self.weights = self.cfg["models"]["ensemble"]["weights"]
        self.features = BASIC_FEATURES
        self._bootstrap_models()

    def _bootstrap_models(self):
        N = 800
        rng = np.random.default_rng(42)
        X = rng.normal(0, 1, size=(N, len(self.features)))
        X = np.abs(X) * np.array([100,1e4,50,100,100,105,95,0,0.01,0.05,1.0])[None,:]
        y = X[:,0] * (1.0 + rng.normal(0, 0.02, size=N))
        self.mz.train_tabular(X, y)
        logger.info("✅ ModelZoo tabular models bootstrapped with synthetic data")

    async def predict_symbol(self, symbol: str) -> AISignal:
        snap = await self.connector.fetch_snapshot(symbol)
        news = await self.connector.fetch_news(5)
        curr_price = float(snap.get("price") or snap.get("last_price") or 100.0)
        news_sent = self.sentiment.score_news(news)
        X = extract_snapshot_features(snap)
        comp = self.mz.predict_tabular(X)
        sentiment_tilt = curr_price * 0.002 * news_sent
        for k in comp:
            comp[k] = comp[k] + sentiment_tilt
        ens_price = weighted_ensemble(comp, self.weights)
        stop, target, exp_ret = compute_risk_return(curr_price, ens_price, atr=None,
                                                    stop_mult=self.cfg["models"]["risk"]["stop_atr_mult"],
                                                    rr_target=self.cfg["models"]["risk"]["target_rr"])
        delta = (ens_price - curr_price) / curr_price
        abs_delta = abs(delta)
        confidence = float(min(95.0, max(55.0, (abs_delta * 100 * 2) + 55.0)))
        if delta > 0.015:
            signal = "BUY"
        elif delta < -0.015:
            signal = "SELL"
        else:
            signal = "HOLD"
        return AISignal(
            symbol=symbol,
            predicted_price=float(round(ens_price, 2)),
            confidence=round(confidence, 2),
            signal_type=signal,
            expected_return=float(round(delta, 4)),
            risk_score=float(min(1.0, abs_delta * 15.0)),
            time_horizon="4H",
            model_version=self.cfg["service"]["version"],
            features_used=self.features,
            components={k: float(round(v, 4)) for k, v in comp.items()},
            timestamp=utc_now()
        )

    async def batch_signals(self, symbols: List[str]) -> List[AISignal]:
        out = []
        for s in symbols:
            try:
                out.append(await self.predict_symbol(s))
            except Exception as e:
                logger.error(f"Signal error {s}: {e}")
        return out
