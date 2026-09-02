"""
BigQuery Table Schemas, Partitioning, and Clustering Definitions
"""
from typing import Dict, List, Any
from google.cloud import bigquery

DATASET_NAME = "market_data"

LIVE_TICKS_SCHEMA = [
    bigquery.SchemaField("tick_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("price", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("volume", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("strike_price", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("option_type", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("open_interest", "INT64", mode="NULLABLE"),
    bigquery.SchemaField("implied_volatility", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("correlation_id", "STRING", mode="NULLABLE"),
]

TRADES_SCHEMA = [
    bigquery.SchemaField("trade_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("correlation_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("action", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("quantity", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("price", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("order_type", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("gross_value", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("statutory_taxes", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("net_pnl", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("strategy", "STRING", mode="NULLABLE"),
]

MODEL_METADATA_SCHEMA = [
    bigquery.SchemaField("model_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("model_name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("version", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("algorithm", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("weights_json", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("val_loss", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("sharpe_ratio", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("gcs_artifact_uri", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("registered_at", "TIMESTAMP", mode="REQUIRED"),
]

BACKTEST_RUNS_SCHEMA = [
    bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("strategy", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("start_date", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("end_date", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("initial_capital", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("total_pnl", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("total_return_pct", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("sharpe_ratio", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("deflated_sharpe_ratio", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("probabilistic_sharpe_ratio", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("max_drawdown", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("win_rate", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("total_trades", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("metrics_json", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
]

TABLE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "live_ticks": {
        "schema": LIVE_TICKS_SCHEMA,
        "partition_field": "timestamp",
        "partition_type": bigquery.TimePartitioningType.DAY,
        "clustering": ["symbol", "option_type"]
    },
    "trades": {
        "schema": TRADES_SCHEMA,
        "partition_field": "timestamp",
        "partition_type": bigquery.TimePartitioningType.DAY,
        "clustering": ["symbol", "action"]
    },
    "model_metadata": {
        "schema": MODEL_METADATA_SCHEMA,
        "partition_field": "registered_at",
        "partition_type": bigquery.TimePartitioningType.MONTH,
        "clustering": ["model_name", "version"]
    },
    "backtest_runs": {
        "schema": BACKTEST_RUNS_SCHEMA,
        "partition_field": "created_at",
        "partition_type": bigquery.TimePartitioningType.DAY,
        "clustering": ["strategy", "symbol"]
    }
}
