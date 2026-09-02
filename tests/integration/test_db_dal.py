"""
Integration Tests for Database & Storage Layer (BigQuery & DAL)
"""
import time
import pytest

from db.schemas.bigquery_schemas import TABLE_CONFIGS
from db.migrations.migrate import run_migrations
from db.dal.bigquery_dal import bigquery_dal
from db.seeds.seed_data import run_seed_all


def test_schema_definitions():
    """Verify all 4 required tables have valid schemas, partitioning, and clustering."""
    expected_tables = ["live_ticks", "trades", "model_metadata", "backtest_runs"]
    for tbl in expected_tables:
        assert tbl in TABLE_CONFIGS, f"Missing table configuration for {tbl}"
        cfg = TABLE_CONFIGS[tbl]
        assert len(cfg["schema"]) > 0
        assert "partition_field" in cfg
        assert len(cfg["clustering"]) >= 2

    # Verify live_ticks partition & clustering
    ticks_cfg = TABLE_CONFIGS["live_ticks"]
    assert ticks_cfg["partition_field"] == "timestamp"
    assert ticks_cfg["clustering"] == ["symbol", "option_type"]

    # Verify trades partition & clustering
    trades_cfg = TABLE_CONFIGS["trades"]
    assert trades_cfg["partition_field"] == "timestamp"
    assert trades_cfg["clustering"] == ["symbol", "action"]


def test_migration_dry_run():
    """Verify migration engine dry run creates/validates table definitions."""
    results = run_migrations(dry_run=True)
    for tbl in ["live_ticks", "trades", "model_metadata", "backtest_runs"]:
        assert tbl in results
        assert results[tbl] in ["dry_run_ok", "mock_created", "created_or_exists"]


def test_dal_seeding_and_row_counts():
    """Seed sample data and verify row counts match expectations."""
    summary = run_seed_all()
    assert summary["status"] == "seeded"
    counts = summary["row_counts"]

    assert counts["live_ticks"] >= 50
    assert counts["trades"] >= 10
    assert counts["model_metadata"] >= 3
    assert counts["backtest_runs"] >= 2


def test_dal_query_latency_and_integrity():
    """Verify query latency is under 350ms and returned records match filters."""
    latencies = []
    for _ in range(5):
        t0 = time.monotonic()
        results = bigquery_dal.query_ticks("NIFTY", limit=10)
        elapsed_ms = (time.monotonic() - t0) * 1000.0
        latencies.append(elapsed_ms)

    avg_latency = sum(latencies) / len(latencies)
    # Institutional requirement: query latency under 350ms
    assert avg_latency < 350.0, f"Average query latency {avg_latency:.2f}ms exceeds 350ms threshold"

    # Verify data integrity
    assert len(results) > 0
    assert all(r["symbol"] == "NIFTY" for r in results)
    assert all(r["price"] > 0 for r in results)
