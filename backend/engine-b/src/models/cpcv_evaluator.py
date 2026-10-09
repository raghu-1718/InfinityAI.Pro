"""
InfinityAI.Pro — Combinatorial Purged Cross-Validation (CPCV) Engine
====================================================================
Implements institutional non-leaking financial cross-validation (Advances in Financial Machine Learning):
1. Purging: Discards training observations whose label evaluation window overlaps with test observations.
2. Embargoing: Enforces a strict post-test buffer (e.g. 24h / N bars) to kill autoregressive serial correlation.
3. Out-of-sample metric aggregation: Sharpe, Sortino, and Brier accuracy score.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any, Generator, Optional

class CombinatorialPurgedCV:
    """Institutional Purged and Embargoed Cross-Validation Splitter"""

    def __init__(
        self,
        n_splits: int = 5,
        embargo_pct: float = 0.02,  # 2% post-test embargo (~1 day in a 50-day window)
        holding_bars: int = 30
    ):
        self.n_splits = n_splits
        self.embargo_pct = embargo_pct
        self.holding_bars = holding_bars

    def split(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        groups: Optional[np.ndarray] = None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Yields (train_indices, test_indices) with strict purging and embargoing.
        """
        n_samples = len(X)
        indices = np.arange(n_samples)
        embargo_bars = max(1, int(n_samples * self.embargo_pct))
        
        fold_size = n_samples // self.n_splits

        for fold in range(self.n_splits):
            test_start = fold * fold_size
            test_end = n_samples if fold == self.n_splits - 1 else (fold + 1) * fold_size
            
            test_idx = indices[test_start:test_end]
            
            # ── 1. Purging: Remove training bars whose holding window intersects test interval ──
            # Any bar i < test_start where (i + holding_bars) >= test_start must be purged
            purge_left = max(0, test_start - self.holding_bars)
            
            # ── 2. Embargoing: Remove training bars immediately following test interval ──
            embargo_right = min(n_samples, test_end + embargo_bars)
            
            # Valid training ranges are: [0, purge_left) and [embargo_right, n_samples)
            train_mask = (indices < purge_left) | (indices >= embargo_right)
            train_idx = indices[train_mask]
            
            if len(train_idx) > 0 and len(test_idx) > 0:
                yield train_idx, test_idx

    @staticmethod
    def evaluate_cpcv_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray,
        returns: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Computes institutional out-of-sample metrics:
        - Brier Score (lower is better, calibrated probabilities)
        - Sharpe Ratio (annualized return / volatility)
        - Sortino Ratio (annualized return / downside volatility)
        """
        n = len(y_true)
        if n == 0:
            return {"brier_score": 1.0, "sharpe_ratio": 0.0, "sortino_ratio": 0.0}

        # Multi-class Brier Score: sum((proba_k - y_k)^2) / n
        n_classes = y_proba.shape[1] if y_proba.ndim > 1 else 3
        y_one_hot = np.zeros((n, n_classes))
        for i, val in enumerate(y_true):
            if 0 <= val < n_classes:
                y_one_hot[i, val] = 1.0

        brier = float(np.mean(np.sum((y_proba - y_one_hot) ** 2, axis=1)))

        # Return simulation based on model decisions (2=BUY long, 0=SELL short, 1=HOLD flat)
        if returns is None or len(returns) != n:
            # Proxy returns if not passed directly
            proxy_ret = np.where(y_true == 2, 0.0075, np.where(y_true == 0, -0.0075, 0.0))
        else:
            proxy_ret = returns

        trade_signals = np.where(y_pred == 2, 1.0, np.where(y_pred == 0, -1.0, 0.0))
        strategy_rets = trade_signals * proxy_ret

        mean_ret = np.mean(strategy_rets)
        std_ret = np.std(strategy_rets)
        downside_std = np.std(strategy_rets[strategy_rets < 0])

        # Annualized Sharpe (assuming 252 trading days)
        sharpe = float((mean_ret / (std_ret + 1e-6)) * np.sqrt(252)) if std_ret > 0 else 0.0
        sortino = float((mean_ret / (downside_std + 1e-6)) * np.sqrt(252)) if downside_std > 0 else 0.0

        return {
            "brier_score": round(brier, 4),
            "sharpe_ratio": round(sharpe, 4),
            "sortino_ratio": round(sortino, 4)
        }
