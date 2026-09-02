"""
Integration Tests for Institutional Vectorized Backtesting Engine
"""
import pytest
import pandas as pd
import numpy as np

from backtesting.vectorized_engine import VectorizedBacktester
from backtesting.walk_forward import PurgedEmbargoedWFO
from backtesting.runner import generate_synthetic_nifty_bars, execute_backtest_and_persist
from db.dal.bigquery_dal import bigquery_dal


@pytest.fixture
def sample_bars():
    """Deterministic price series fixture."""
    return generate_synthetic_nifty_bars(n_bars=250)


def test_buy_and_hold_benchmark_sanity(sample_bars):
    """Verify buy-and-hold benchmark produces sane, reproducible P&L and Sharpe outputs."""
    backtester = VectorizedBacktester(initial_capital=500000.0, slippage_pct=0.0005)
    metrics = backtester.run_buy_and_hold_benchmark(sample_bars)

    assert metrics["initial_capital"] == 500000.0
    assert metrics["final_equity"] > 0.0
    # Over 250 bars with positive drift, PnL should be positive
    assert metrics["total_pnl"] > 0
    # Sane institutional bounds on Sharpe ratio (0.5 to 3.0)
    assert 0.5 <= metrics["sharpe_ratio"] <= 3.0
    # Drawdown within 5% to 35%
    assert 5.0 <= metrics["max_drawdown_pct"] <= 35.0
    # Single buy order
    assert metrics["total_trades"] == 1


def test_slippage_and_taxes_reduce_net_pnl(sample_bars):
    """Verify that execution slippage and SEBI statutory taxes strictly reduce net P&L."""
    bt_frictionless = VectorizedBacktester(initial_capital=500000.0, slippage_pct=0.0, include_sebi_taxes=False)
    gross_metrics = bt_frictionless.run_strategy(sample_bars, signal_col="signal")

    bt_with_friction = VectorizedBacktester(initial_capital=500000.0, slippage_pct=0.001, include_sebi_taxes=True)
    net_metrics = bt_with_friction.run_strategy(sample_bars, signal_col="signal")

    assert net_metrics["total_pnl"] < gross_metrics["total_pnl"]
    assert net_metrics["sharpe_ratio"] <= gross_metrics["sharpe_ratio"]
    assert net_metrics["total_trades"] == gross_metrics["total_trades"]


def test_purged_and_embargoed_wfo_splits(sample_bars):
    """Verify WFO produces non-overlapping, strictly ordered splits with no lookahead bias."""
    wfo = PurgedEmbargoedWFO(n_splits=4, embargo_pct=0.02)
    splits = wfo.split(sample_bars)

    assert len(splits) == 4
    for train_idx, test_idx in splits:
        assert len(train_idx) > 0
        assert len(test_idx) > 0
        # Train strictly precedes test (no lookahead)
        assert train_idx[-1] < test_idx[0]

        # Verify embargo calculation
        embargo_cutoff = wfo.apply_embargo(test_idx, len(sample_bars))
        assert embargo_cutoff >= test_idx[-1]


def test_backtest_persistence_to_bigquery():
    """Verify backtest runner persists complete performance record to BigQuery schema."""
    initial_count = bigquery_dal.get_row_counts()["backtest_runs"]
    result = execute_backtest_and_persist(strategy_name="tri_model_ensemble_wfo")

    assert "run_id" in result
    assert result["run_id"].startswith("bt-")
    assert "metrics" in result
    assert result["metrics"]["sharpe_ratio"] > 0

    # Confirm BigQuery DAL recorded the new run
    final_count = bigquery_dal.get_row_counts()["backtest_runs"]
    assert final_count == initial_count + 1
