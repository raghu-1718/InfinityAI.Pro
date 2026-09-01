"""
InfinityAI.Pro — Historical Signal Labeling & Feature Engineering Engine
========================================================================
Processes raw historical OHLCV bars from `market_data.historical_ohlcv_backtest`,
computes institutional quantitative features, simulates forward-looking trade outcomes
(WIN / LOSS / EXPIRED, realized returns, duration), and populates independent BigQuery
feature stores:
  1. `market_data.equity_training_features`
  2. `market_data.options_training_features`
"""

import os
import sys
import math
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SignalLabelingEngine")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
EQUITY_FEATURES_TABLE = f"{PROJECT_ID}.market_data.equity_training_features"
OPTIONS_FEATURES_TABLE = f"{PROJECT_ID}.market_data.options_training_features"

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Computes standard Wilder's RSI."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)

def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Computes Average True Range (ATR)."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr.fillna(tr.mean())

def compute_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Computes directional ADX."""
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0.0
    minus_dm[minus_dm > 0] = 0.0

    tr = compute_atr(high, low, close, period=period)
    plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / (tr + 1e-9))
    minus_di = 100 * (minus_dm.abs().ewm(alpha=1/period).mean() / (tr + 1e-9))
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)) * 100
    adx = dx.ewm(alpha=1/period).mean()
    return adx.fillna(25.0)

def engineer_features_and_labels(df_raw: pd.DataFrame, asset_class: str = "EQUITY") -> pd.DataFrame:
    """
    Computes rolling quantitative features and simulates forward-looking trade brackets.
    """
    labeled_rows = []

    for sym, group in df_raw.groupby("symbol"):
        grp = group.sort_values("bar_date").reset_index(drop=True).copy()
        if len(grp) < 25:
            continue

        c = grp["close"]
        h = grp["high"]
        l = grp["low"]
        o = grp["open"]
        v = grp["volume"]

        # 1. Technical Indicators
        grp["rsi_14"] = compute_rsi(c, 14)
        grp["atr_14"] = compute_atr(h, l, c, 14)
        grp["adx_14"] = compute_adx(h, l, c, 14)
        grp["sma_20"] = c.rolling(20).mean().fillna(c)
        grp["sma_50"] = c.rolling(50).mean().fillna(c)
        grp["sma_200"] = c.rolling(200).mean().fillna(c)

        grp["sma_20_dist_pct"] = ((c - grp["sma_20"]) / grp["sma_20"] * 100).fillna(0.0)
        grp["sma_50_dist_pct"] = ((c - grp["sma_50"]) / grp["sma_50"] * 100).fillna(0.0)
        grp["range_pct"] = ((h - l) / (l + 1e-9) * 100).fillna(1.0)
        grp["intraday_return_pct"] = ((c - o) / (o + 1e-9) * 100).fillna(0.0)
        grp["volatility_20"] = c.pct_change().rolling(20).std().fillna(0.01) * 100
        grp["volume_ratio_20"] = (v / (v.rolling(20).mean() + 1e-9)).fillna(1.0)

        # Forward Trade Simulation
        max_horizon = 5 if asset_class == "EQUITY" else 3

        for i in range(len(grp) - max_horizon):
            row = grp.iloc[i]
            entry_price = float(row["close"])
            range_p = float(row["range_pct"])

            # Bracket formulation matching production scanner
            if asset_class == "EQUITY":
                target_pct = float(max(2.5, min(4.8, 2.5 + (range_p * 0.5))))
                stop_loss_pct = float(max(1.4, min(2.4, target_pct / 1.8)))
            else: # OPTIONS INDEX UNDERLYING
                target_pct = float(max(1.0, min(3.0, 1.2 + (range_p * 0.4))))
                stop_loss_pct = float(max(0.6, min(1.8, target_pct / 1.6)))

            target_price = entry_price * (1.0 + target_pct / 100.0)
            stop_loss_price = entry_price * (1.0 - stop_loss_pct / 100.0)

            outcome = "EXPIRED"
            realized_ret = 0.0
            holding_days = max_horizon
            exit_price = entry_price
            label_win = 0

            # Forward lookahead over holding horizon
            for step in range(1, max_horizon + 1):
                fwd_bar = grp.iloc[i + step]
                fwd_high = float(fwd_bar["high"])
                fwd_low = float(fwd_bar["low"])
                fwd_close = float(fwd_bar["close"])

                hit_target = fwd_high >= target_price
                hit_sl = fwd_low <= stop_loss_price

                if hit_target and not hit_sl:
                    outcome = "WIN" if asset_class == "EQUITY" else "TARGET_HIT"
                    label_win = 1
                    realized_ret = target_pct
                    holding_days = step
                    exit_price = target_price
                    break
                elif hit_sl and not hit_target:
                    outcome = "LOSS" if asset_class == "EQUITY" else "STOPPED_OUT"
                    label_win = 0
                    realized_ret = -stop_loss_pct
                    holding_days = step
                    exit_price = stop_loss_price
                    break
                elif hit_target and hit_sl:
                    # Conservative assumption: worst-case stop loss hits first
                    outcome = "LOSS" if asset_class == "EQUITY" else "STOPPED_OUT"
                    label_win = 0
                    realized_ret = -stop_loss_pct
                    holding_days = step
                    exit_price = stop_loss_price
                    break

            if outcome == "EXPIRED":
                final_close = float(grp.iloc[i + max_horizon]["close"])
                realized_ret = round(((final_close - entry_price) / entry_price) * 100, 2)
                exit_price = final_close
                label_win = 1 if realized_ret > 0.5 else 0

            labeled_rows.append({
                "signal_id": f"BOOTSTRAP_{asset_class}_{sym}_{str(row['bar_date']).replace('-', '')}",
                "symbol": sym,
                "security_id": str(row["security_id"]),
                "bar_date": row["bar_date"],
                "entry_price": round(entry_price, 2),
                "target_price": round(target_price, 2),
                "stop_loss_price": round(stop_loss_price, 2),
                "target_pct": round(target_pct, 2),
                "stop_loss_pct": round(stop_loss_pct, 2),
                "exit_price": round(exit_price, 2),
                "realized_return_pct": round(realized_ret, 2),
                "holding_days": int(holding_days),
                "signal_outcome": outcome,
                "label_win": int(label_win),
                # Engineered Features
                "rsi_14": round(float(row["rsi_14"]), 2),
                "adx_14": round(float(row["adx_14"]), 2),
                "atr_14": round(float(row["atr_14"]), 2),
                "range_pct": round(float(row["range_pct"]), 2),
                "intraday_return_pct": round(float(row["intraday_return_pct"]), 2),
                "sma_20_dist_pct": round(float(row["sma_20_dist_pct"]), 2),
                "sma_50_dist_pct": round(float(row["sma_50_dist_pct"]), 2),
                "volatility_20": round(float(row["volatility_20"]), 2),
                "volume_ratio_20": round(float(row["volume_ratio_20"]), 2),
                "is_live_trade": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })

    return pd.DataFrame(labeled_rows)

def ensure_feature_tables(bq_client: bigquery.Client):
    """Ensures feature tables exist with appropriate schemas."""
    schema = [
        bigquery.SchemaField("signal_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("security_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("bar_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("entry_price", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("target_price", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("stop_loss_price", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("target_pct", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("stop_loss_pct", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("exit_price", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("realized_return_pct", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("holding_days", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("signal_outcome", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("label_win", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("rsi_14", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("adx_14", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("atr_14", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("range_pct", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("intraday_return_pct", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("sma_20_dist_pct", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("sma_50_dist_pct", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("volatility_20", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("volume_ratio_20", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("is_live_trade", "BOOLEAN", mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]

    for table_id in [EQUITY_FEATURES_TABLE, OPTIONS_FEATURES_TABLE]:
        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="bar_date"
        )
        table.clustering_fields = ["symbol", "signal_outcome"]
        bq_client.create_table(table, exists_ok=True)
        logger.info(f"✅ BigQuery feature table verified: {table_id}")

def run_labeling_pipeline():
    """Extracts raw bars, engineers features, and populates both feature stores."""
    bq_client = bigquery.Client(project=PROJECT_ID)
    ensure_feature_tables(bq_client)

    raw_query = f"""
    SELECT * 
    FROM `{PROJECT_ID}.market_data.historical_ohlcv_backtest`
    ORDER BY symbol, bar_date ASC
    """
    logger.info("📥 Pulling raw historical bars from BigQuery...")
    df_raw = bq_client.query(raw_query).to_dataframe()
    logger.info(f"   • Loaded {len(df_raw):,} raw bars across {df_raw['symbol'].nunique()} instruments.")

    # 1. Equities
    df_eq_raw = df_raw[df_raw["instrument_type"] == "EQUITY"].copy()
    logger.info(f"⚙️ Engineering features and labels for Equities ({len(df_eq_raw):,} bars)...")
    df_eq_features = engineer_features_and_labels(df_eq_raw, asset_class="EQUITY")
    logger.info(f"   • Generated {len(df_eq_features):,} labeled Equity samples. (Win rate: {df_eq_features['label_win'].mean()*100:.1f}%)")

    # 2. Options (Indices)
    df_opt_raw = df_raw[df_raw["instrument_type"] == "INDEX"].copy()
    logger.info(f"⚙️ Engineering features and labels for Options/Indices ({len(df_opt_raw):,} bars)...")
    df_opt_features = engineer_features_and_labels(df_opt_raw, asset_class="OPTIONS")
    logger.info(f"   • Generated {len(df_opt_features):,} labeled Options samples. (Win rate: {df_opt_features['label_win'].mean()*100:.1f}%)")

    # Load into BigQuery
    for df, target_table in [(df_eq_features, EQUITY_FEATURES_TABLE), (df_opt_features, OPTIONS_FEATURES_TABLE)]:
        df["bar_date"] = pd.to_datetime(df["bar_date"]).dt.date
        df["created_at"] = pd.to_datetime(df["created_at"])
        job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
        load_job = bq_client.load_table_from_dataframe(df, target_table, job_config=job_config)
        load_job.result()
        logger.info(f"💾 Ingested {len(df):,} rows into {target_table}.")

    logger.info("🎉 Signal Labeling Pipeline Completed Successfully!")
    return len(df_eq_features), len(df_opt_features)

if __name__ == "__main__":
    run_labeling_pipeline()
