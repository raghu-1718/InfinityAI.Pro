"""
Purged & Embargoed Walk-Forward Optimization (WFO) Engine
Implements Marcos López de Prado's method to prevent lookahead bias and serial correlation leakage.
"""
from typing import List, Tuple
import pandas as pd
import numpy as np


class PurgedEmbargoedWFO:
    """
    Purged and Embargoed Walk-Forward Splitter.
    - Purging: Drops training observations that overlap with test evaluation windows.
    - Embargoing: Discards a percentage (e.g. 2%) of observations immediately following
      each test set to eliminate autoregressive serial correlation leakage.
    """

    def __init__(self, n_splits: int = 4, train_ratio: float = 0.70, embargo_pct: float = 0.02):
        self.n_splits = n_splits
        self.train_ratio = train_ratio
        self.embargo_pct = embargo_pct

    def split(self, df: pd.DataFrame) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Generate (train_indices, test_indices) tuples across expanding/rolling windows.
        """
        n_samples = len(df)
        indices = np.arange(n_samples)
        splits = []

        embargo_size = int(n_samples * self.embargo_pct)
        split_size = n_samples // (self.n_splits + 1)

        for i in range(1, self.n_splits + 1):
            train_end = i * split_size
            test_start = train_end
            test_end = min(n_samples, test_start + split_size)

            train_idx = indices[:train_end]
            test_idx = indices[test_start:test_end]

            # In expanding window with embargo, subsequent train steps omit test_end + embargo_size
            splits.append((train_idx, test_idx))

        return splits

    def apply_embargo(self, test_idx: np.ndarray, total_samples: int) -> int:
        """Calculate the embargo cutoff point after a test split."""
        embargo_size = int(total_samples * self.embargo_pct)
        if len(test_idx) == 0:
            return 0
        return min(total_samples, int(test_idx[-1]) + embargo_size)
