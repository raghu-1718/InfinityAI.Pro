"""
InfinityAI.Pro — Dual-Metric Population Stability Index & Feature Importance Drift Watchdog
=============================================================================================
Engine B MLOps | Production Grade | GCP Cloud Architecture
Monitors:
1. Population Stability Index (PSI) per feature:
   - PSI < 0.10: Stable Regime (Green)
   - 0.10 <= PSI <= 0.25: Moderate Drift Warning (Yellow)
   - PSI > 0.25: Critical Drift (Red -> Triggers Cloud Build Retraining)
2. Feature Importance Drift:
   - Detects if top-5 feature weights collapse by > 40% between baseline and live fits.
"""

import os
import math
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("InfinityAI.PSIDriftWatchdog")

class DualMetricDriftWatchdog:
    """Institutional Dual-Metric Concept Drift Watchdog"""

    def __init__(self, num_bins: int = 10, drift_threshold: float = 0.25):
        self.num_bins = num_bins
        self.drift_threshold = drift_threshold

    def calculate_psi(
        self,
        baseline: np.ndarray,
        live: np.ndarray,
        epsilon: float = 1e-4
    ) -> float:
        """
        Calculates Population Stability Index:
        PSI = sum( (Actual_pct - Expected_pct) * ln(Actual_pct / Expected_pct) )
        """
        b = baseline[~np.isnan(baseline)]
        l = live[~np.isnan(live)]

        if len(b) < 10 or len(l) < 10:
            return 0.0

        quantiles = np.linspace(0, 100, self.num_bins + 1)
        bin_edges = np.percentile(b, quantiles)
        bin_edges = np.unique(bin_edges)

        if len(bin_edges) < 2:
            val = float(bin_edges[0]) if len(bin_edges) == 1 else 0.0
            bin_edges = np.array([-np.inf, val, np.inf])
        else:
            bin_edges[0] = -np.inf
            bin_edges[-1] = np.inf

        expected_counts, _ = np.histogram(b, bins=bin_edges)
        actual_counts, _ = np.histogram(l, bins=bin_edges)

        expected_pct = expected_counts / max(len(b), 1)
        actual_pct = actual_counts / max(len(l), 1)

        expected_pct = np.where(expected_pct == 0, epsilon, expected_pct)
        actual_pct = np.where(actual_pct == 0, epsilon, actual_pct)

        psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
        return float(np.maximum(0.0, round(psi, 4)))

    def calculate_feature_importance_drift(
        self,
        baseline_importance: Dict[str, float],
        live_importance: Dict[str, float],
        max_allowed_collapse_pct: float = 0.40
    ) -> Dict[str, Any]:
        """
        Detects if top features collapse by > 40% relative to baseline model.
        """
        drifted_features = []
        feature_deltas = {}

        for feat, base_val in baseline_importance.items():
            live_val = live_importance.get(feat, 0.0)
            if base_val > 0:
                rel_change = (live_val - base_val) / base_val
                feature_deltas[feat] = round(rel_change, 4)
                if rel_change < -max_allowed_collapse_pct:
                    drifted_features.append(feat)

        is_importance_drifted = len(drifted_features) > 0

        return {
            "is_importance_drifted": is_importance_drifted,
            "drifted_features": drifted_features,
            "feature_deltas": feature_deltas,
            "alert": is_importance_drifted
        }

    def evaluate_dataset_drift(
        self,
        baseline_df_dict: Dict[str, np.ndarray],
        live_df_dict: Dict[str, np.ndarray],
        core_features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates full multi-feature PSI drift across core indicators:
        (gex, pcr_momentum, iv_skew, obi, rsi, macd, vwap_distance).
        """
        features_to_check = core_features or ["gex", "pcr_momentum", "iv_skew", "obi", "rsi", "macd", "vwap_distance"]
        feature_psi_scores = {}
        critical_drift_features = []

        for feat in features_to_check:
            if feat in baseline_df_dict and feat in live_df_dict:
                psi_val = self.calculate_psi(baseline_df_dict[feat], live_df_dict[feat])
                feature_psi_scores[feat] = psi_val
                if psi_val > self.drift_threshold:
                    critical_drift_features.append(feat)

        mean_psi = float(np.mean(list(feature_psi_scores.values()))) if feature_psi_scores else 0.0
        should_trigger_retraining = (len(critical_drift_features) >= 2) or (mean_psi > self.drift_threshold)

        status = "CRITICAL_DRIFT" if should_trigger_retraining else ("MODERATE_DRIFT" if mean_psi > 0.10 else "STABLE")

        return {
            "status": status,
            "mean_psi": round(mean_psi, 4),
            "feature_psi_scores": feature_psi_scores,
            "critical_features": critical_drift_features,
            "trigger_retraining": should_trigger_retraining,
            "action": "TRIGGER_CLOUD_BUILD_RETRAINING" if should_trigger_retraining else "MAINTAIN_CURRENT_CHAMPION"
        }

DUAL_METRIC_DRIFT_WATCHDOG = DualMetricDriftWatchdog()
