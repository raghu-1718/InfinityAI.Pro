"""
InfinityAI.Pro — Population Stability Index (PSI) Concept Drift Watchdog
========================================================================
Engine B | Production Grade | Version: 3.0.0

Monitors real-time streaming feature distributions against baseline historical
distributions to detect statistical concept drift and market regime shifts.

  PSI < 0.10  -> STABLE_REGIME (Green: Full Position Sizing 1.0x)
  PSI 0.10-0.20 -> MODERATE_DRIFT (Yellow: Model Warning, Position Sizing 0.75x)
  PSI > 0.20  -> CRITICAL_DRIFT (Red: Auto-Retraining Triggered, Risk Sizing 0.50x)
"""

import os
import math
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np

try:
    from google.cloud import firestore
except Exception:
    firestore = None

logger = logging.getLogger("InfinityAI.PSIDriftWatchdog")

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "project-841b7f97-5ee3-4fbe-920")
DRIFT_DOC_COLLECTION = "model_metadata"
DRIFT_DOC_ID = "concept_drift_telemetry"

class PSIDriftWatchdog:
    """Institutional Concept Drift Monitor using Population Stability Index"""

    def __init__(self, num_bins: int = 10, project_id: str = PROJECT_ID):
        self.num_bins = num_bins
        self.project_id = project_id
        self.db = None

        if firestore:
            try:
                self.db = firestore.Client(project=self.project_id)
            except Exception as e:
                logger.debug(f"Firestore drift watchdog init notice: {e}")

    def compute_feature_psi(
        self,
        expected_array: np.ndarray,  # Historical Baseline (e.g. from BigQuery Golden Dataset)
        actual_array: np.ndarray,    # Live Streaming Window (e.g. recent 300 ticks)
        epsilon: float = 1e-4
    ) -> float:
        """
        Calculates the Population Stability Index for a single continuous feature:
        PSI = sum( (Actual_pct - Expected_pct) * ln(Actual_pct / Expected_pct) )
        """
        if len(expected_array) < 10 or len(actual_array) < 10:
            return 0.0

        # Create quantile bin edges based on expected historical distribution
        quantiles = np.linspace(0, 100, self.num_bins + 1)
        bin_edges = np.percentile(expected_array, quantiles)
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf
        bin_edges = np.unique(bin_edges) # Remove duplicates if zero variance

        if len(bin_edges) <= 2:
            return 0.0

        # Calculate frequency distribution
        expected_counts, _ = np.histogram(expected_array, bins=bin_edges)
        actual_counts, _ = np.histogram(actual_array, bins=bin_edges)

        expected_pct = (expected_counts / len(expected_array)) + epsilon
        actual_pct = (actual_counts / len(actual_array)) + epsilon

        # Normalize
        expected_pct /= np.sum(expected_pct)
        actual_pct /= np.sum(actual_pct)

        # PSI Summation
        psi_value = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
        return float(max(0.0, psi_value))

    def evaluate_multi_feature_drift(
        self,
        baseline_df_dict: Dict[str, np.ndarray],
        live_df_dict: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """
        Evaluates PSI across all 8 features and computes Aggregate Drift Score.
        """
        feature_psis = {}
        for feature_name, expected_vals in baseline_df_dict.items():
            if feature_name in live_df_dict:
                psi = self.compute_feature_psi(expected_vals, live_df_dict[feature_name])
                feature_psis[feature_name] = round(psi, 4)

        avg_psi = float(np.mean(list(feature_psis.values()))) if feature_psis else 0.0
        max_psi = float(np.max(list(feature_psis.values()))) if feature_psis else 0.0
        max_feature = max(feature_psis, key=feature_psis.get) if feature_psis else "none"

        if avg_psi < 0.10:
            regime_status = "STABLE_NO_DRIFT"
            risk_sizing_multiplier = 1.00
            retrain_required = False
        elif avg_psi <= 0.20:
            regime_status = "MODERATE_DRIFT_WARNING"
            risk_sizing_multiplier = 0.75
            retrain_required = False
        else:
            regime_status = "CRITICAL_CONCEPT_DRIFT_ACTION_REQUIRED"
            risk_sizing_multiplier = 0.50
            retrain_required = True

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "aggregate_psi": round(avg_psi, 4),
            "max_feature_psi": round(max_psi, 4),
            "most_drifted_feature": max_feature,
            "regime_status": regime_status,
            "risk_sizing_multiplier": risk_sizing_multiplier,
            "retrain_required": retrain_required,
            "feature_breakdown": feature_psis
        }

        self._persist_drift_telemetry(result)
        return result

    def _persist_drift_telemetry(self, payload: Dict[str, Any]) -> None:
        """Persists drift status to Firestore for Engine A & Dashboard consumption"""
        if not self.db:
            return
        try:
            self.db.collection(DRIFT_DOC_COLLECTION).document(DRIFT_DOC_ID).set(payload)
        except Exception as e:
            logger.debug(f"Error persisting drift telemetry: {e}")

PSI_DRIFT_WATCHDOG = PSIDriftWatchdog()
