"""
InfinityAI.Pro — Bayesian Ensemble Weight Client (Engine A)
============================================================
Engine A | Production Grade | Version: 3.0.0

High-speed consumer of Bayesian online weights from Firestore with local in-memory
cache and instant fallback to baseline priors.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

try:
    from google.cloud import firestore
except Exception:
    firestore = None

logger = logging.getLogger("InfinityAI.BayesianEnsembleClient")

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "project-841b7f97-5ee3-4fbe-920")
METADATA_COLLECTION = "model_metadata"
METADATA_DOC = "bayesian_ensemble_weights"

DEFAULT_WEIGHTS = {
    "catboost": 0.40,
    "lightgbm": 0.35,
    "xgboost": 0.25
}

class BayesianEnsembleClient:
    """Client for retrieving and caching active Bayesian weights in Engine A"""

    def __init__(self, project_id: str = PROJECT_ID, cache_ttl_seconds: int = 180):
        self.project_id = project_id
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cached_weights = DEFAULT_WEIGHTS.copy()
        self._last_fetch_time: Optional[datetime] = None
        self.db = None

        if firestore:
            try:
                self.db = firestore.Client(project=self.project_id)
            except Exception as e:
                logger.debug(f"Firestore Bayesian client init notice: {e}")

    def get_active_weights(self) -> Dict[str, float]:
        """
        Retrieves active Bayesian weights with fast local TTL caching (3 minutes).
        """
        now = datetime.now(timezone.utc)
        if self._last_fetch_time:
            age = (now - self._last_fetch_time).total_seconds()
            if age < self.cache_ttl_seconds:
                return self._cached_weights

        # Fetch from Firestore
        if self.db:
            try:
                doc = self.db.collection(METADATA_COLLECTION).document(METADATA_DOC).get()
                if doc.exists:
                    data = doc.to_dict()
                    w = data.get("weights")
                    if w and isinstance(w, dict):
                        self._cached_weights = {k: float(v) for k, v in w.items()}
                        self._last_fetch_time = now
                        return self._cached_weights
            except Exception as e:
                logger.debug(f"Bayesian weights cache fetch fallback: {e}")

        return self._cached_weights

    def calculate_bayesian_consensus(
        self,
        catboost_prob: float,
        lightgbm_prob: float,
        xgboost_prob: float
    ) -> Dict[str, Any]:
        """
        Calculates consensus probability weighted by active Bayesian online weights.
        """
        weights = self.get_active_weights()
        w_cat = weights.get("catboost", 0.40)
        w_lgb = weights.get("lightgbm", 0.35)
        w_xgb = weights.get("xgboost", 0.25)

        total_weight = w_cat + w_lgb + w_xgb
        consensus_prob = ((catboost_prob * w_cat) + (lightgbm_prob * w_lgb) + (xgboost_prob * w_xgb)) / total_weight

        champion = max(weights, key=weights.get)

        return {
            "consensus_probability": round(float(consensus_prob), 4),
            "applied_weights": {
                "catboost": round(w_cat, 4),
                "lightgbm": round(w_lgb, 4),
                "xgboost": round(w_xgb, 4)
            },
            "champion_model": champion
        }

BAYESIAN_CLIENT = BayesianEnsembleClient()
