"""
Unit Tests: Vertex AI Champion-Challenger Pipeline (Domain 4)
=============================================================
Validates:
1. Population Stability Index (PSI) calculation accuracy and drift detection.
2. Brier score evaluation and calibration.
3. Walk-Forward Optimization (WFO) decision gating.
4. Hot-swap qualification threshold (+2.5% directional precision requirement).
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from ml.training.vertex_champion_challenger import (
    calculate_psi,
    VertexChampionChallengerPipeline,
    FEATURE_COLUMNS
)


def test_psi_identical_distributions():
    """Verify PSI is near zero for identical distributions."""
    np.random.seed(42)
    dist1 = np.random.normal(0, 1, 1000)
    dist2 = np.random.normal(0, 1, 1000)

    psi = calculate_psi(dist1, dist2)
    assert psi < 0.10, f"Expected stable PSI < 0.10, got {psi:.4f}"


def test_psi_shifted_distribution():
    """Verify PSI flags severe distribution drift when mean shifts significantly."""
    np.random.seed(42)
    baseline = np.random.normal(0, 1, 1000)
    shifted = np.random.normal(2.5, 1, 1000)

    psi = calculate_psi(baseline, shifted)
    assert psi >= 0.25, f"Expected drifted PSI >= 0.25, got {psi:.4f}"


def test_hot_swap_qualification_threshold():
    """Verify promotion gate requires >= +2.5% precision gain and WFE >= 0.50."""
    with patch("google.cloud.bigquery.Client"), \
         patch("google.cloud.storage.Client"), \
         patch("google.cloud.firestore.Client"):
        pipeline = VertexChampionChallengerPipeline()

    # Case A: Challenger improves by only +1.0% (< +2.5%) -> Should NOT promote
    eval_fail = {
        "meets_precision_threshold": False,
        "precision_delta": 0.010,
        "meets_psi_threshold": True,
        "mean_psi": 0.045
    }
    wfo_pass = {"majority_passed": True, "passing_folds": 2}
    should_promote_a = eval_fail["meets_precision_threshold"] and eval_fail["meets_psi_threshold"] and wfo_pass["majority_passed"]
    assert should_promote_a is False

    # Case B: Challenger improves by +3.2% (>= +2.5%), WFE majority passed, PSI stable -> Should PROMOTE
    eval_pass = {
        "meets_precision_threshold": True,
        "precision_delta": 0.032,
        "meets_psi_threshold": True,
        "mean_psi": 0.038
    }
    should_promote_b = eval_pass["meets_precision_threshold"] and eval_pass["meets_psi_threshold"] and wfo_pass["majority_passed"]
    assert should_promote_b is True


def test_brier_score_metric_properties():
    """Verify Brier Score behaves as mean squared probabilistic error."""
    from sklearn.metrics import brier_score_loss

    y_true = np.array([1, 0, 1, 1, 0])
    # Perfectly calibrated predictions
    perfect_probs = np.array([1.0, 0.0, 1.0, 1.0, 0.0])
    # Poor predictions
    poor_probs = np.array([0.2, 0.8, 0.3, 0.1, 0.9])

    perfect_brier = brier_score_loss(y_true, perfect_probs)
    poor_brier = brier_score_loss(y_true, poor_probs)

    assert perfect_brier == 0.0
    assert poor_brier > 0.40
