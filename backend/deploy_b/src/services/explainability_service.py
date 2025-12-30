# =====================================================================
# InfinityAI.Pro - Explainability Service
# Model-agnostic SHAP-based explainability layer
# STATUS: PRODUCTION-READY
# =====================================================================

import os
import json
import logging
from typing import Dict, Any, List

import numpy as np
import joblib

try:
    import shap
    _SHAP_AVAILABLE = True
except Exception:
    _SHAP_AVAILABLE = False

from lightgbm import LGBMRegressor

logger = logging.getLogger("InfinityAI.ExplainabilityService")


class ExplainabilityService:
    """
    Provides feature-level explanations for ML predictions using SHAP.

    Design goals:
    - Safe for production (no crashes if SHAP missing)
    - Model-agnostic (tree-based focus)
    - Deterministic output shape
    - Compatible with Engine-B inference pipeline
    """

    def __init__(
        self,
        model_path: str,
        scaler_path: str,
        features_path: str,
        model_type: str = "tree"
    ):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.features_path = features_path
        self.model_type = model_type

        self.model = None
        self.scaler = None
        self.features: List[str] = []
        self.explainer = None

        self._load_artifacts()
        self._init_explainer()

    # -----------------------------------------------------------------
    # Artifact loading
    # -----------------------------------------------------------------

    def _load_artifacts(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        if not os.path.exists(self.scaler_path):
            raise FileNotFoundError(f"Scaler not found: {self.scaler_path}")
        if not os.path.exists(self.features_path):
            raise FileNotFoundError(f"Features file not found: {self.features_path}")

        self.model = joblib.load(self.model_path)
        self.scaler = joblib.load(self.scaler_path)

        with open(self.features_path, "r") as f:
            self.features = json.load(f)

        if not isinstance(self.features, list):
            raise ValueError("features.json must be a list of feature names")

        logger.info(
            "Explainability artifacts loaded | "
            f"features={len(self.features)} | model={type(self.model).__name__}"
        )

    # -----------------------------------------------------------------
    # SHAP explainer initialization
    # -----------------------------------------------------------------

    def _init_explainer(self):
        if not _SHAP_AVAILABLE:
            logger.warning("SHAP not available — explainability disabled")
            return

        try:
            if self.model_type == "tree":
                self.explainer = shap.TreeExplainer(self.model)
            else:
                self.explainer = shap.Explainer(self.model)

            logger.info("SHAP explainer initialized successfully")

        except Exception as e:
            logger.exception(f"Failed to initialize SHAP explainer: {e}")
            self.explainer = None

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def explain(self, X: np.ndarray) -> Dict[str, float]:
        """
        Generate per-feature importance for a single prediction.

        Returns:
            {
                "feature_name": importance_score,
                ...
            }
        """

        if self.explainer is None:
            return self._fallback_explanation(X)

        if X.ndim != 2 or X.shape[0] != 1:
            raise ValueError("Explain expects X with shape (1, n_features)")

        try:
            X_scaled = self.scaler.transform(X)
            shap_values = self.explainer(X_scaled)

            values = shap_values.values
            if values.ndim == 3:
                values = values[0]

            importance = np.abs(values[0])

            result = {
                self.features[i]: float(round(importance[i], 6))
                for i in range(min(len(self.features), len(importance)))
            }

            return result

        except Exception as e:
            logger.exception(f"Explainability failed: {e}")
            return self._fallback_explanation(X)

    # -----------------------------------------------------------------
    # Health & metadata
    # -----------------------------------------------------------------

    def health(self) -> Dict[str, Any]:
        """
        Health status for /health/models and /health/knowledge
        """
        return {
            "service": "ExplainabilityService",
            "shap_available": _SHAP_AVAILABLE,
            "explainer_initialized": self.explainer is not None,
            "model_loaded": self.model is not None,
            "scaler_loaded": self.scaler is not None,
            "feature_count": len(self.features),
            "model_type": type(self.model).__name__,
        }

    # -----------------------------------------------------------------
    # Fallback logic
    # -----------------------------------------------------------------

    def _fallback_explanation(self, X: np.ndarray) -> Dict[str, float]:
        """
        Safe fallback when SHAP is unavailable.
        Returns uniform small weights so API never breaks.
        """
        logger.warning("Using fallback explainability (uniform weights)")

        weight = round(1.0 / max(len(self.features), 1), 6)
        return {f: weight for f in self.features}
