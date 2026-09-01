"""
InfinityAI.Pro — Comprehensive Dataset Validation & Audit
==========================================================
Validates row counts, dates, class distributions, nulls, and duplicate primary keys.
"""

import pandas as pd
from google.cloud import bigquery

bq = bigquery.Client(project="project-841b7f97-5ee3-4fbe-920")

tables = [
    "historical_ohlcv_backtest",
    "equity_training_features",
    "options_training_features"
]

for tbl in tables:
    full_table_id = f"project-841b7f97-5ee3-4fbe-920.market_data.{tbl}"
    print(f"\n=======================================================")
    print(f"      AUDITING DATASET: market_data.{tbl}")
    print(f"=======================================================")
    
    query = f"""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT symbol) as unique_symbols,
        MIN(bar_date) as min_date,
        MAX(bar_date) as max_date
    FROM `{full_table_id}`
    """
    df_meta = bq.query(query).to_dataframe()
    print(df_meta.to_string(index=False))

    if "features" in tbl:
        q_class = f"""
        SELECT signal_outcome, COUNT(*) as count, ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct
        FROM `{full_table_id}`
        GROUP BY signal_outcome
        ORDER BY count DESC
        """
        df_class = bq.query(q_class).to_dataframe()
        print("\nClass distribution:")
        print(df_class.to_string(index=False))

        # Check nulls
        q_nulls = f"""
        SELECT 
            COUNTIF(rsi_14 IS NULL) as null_rsi,
            COUNTIF(adx_14 IS NULL) as null_adx,
            COUNTIF(atr_14 IS NULL) as null_atr,
            COUNTIF(sma_20_dist_pct IS NULL) as null_sma20,
            COUNTIF(volatility_20 IS NULL) as null_vol,
            COUNTIF(volume_ratio_20 IS NULL) as null_vol_ratio,
            COUNTIF(realized_return_pct IS NULL) as null_return,
            COUNTIF(label_win IS NULL) as null_label
        FROM `{full_table_id}`
        """
        df_nulls = bq.query(q_nulls).to_dataframe()
        print("\nNull counts:")
        print(df_nulls.to_string(index=False))

        # Check duplicate primary keys (symbol + bar_date)
        q_dups = f"""
        SELECT COUNT(*) as duplicate_key_count FROM (
            SELECT symbol, bar_date, COUNT(*) as cnt
            FROM `{full_table_id}`
            GROUP BY symbol, bar_date
            HAVING cnt > 1
        )
        """
        df_dups = bq.query(q_dups).to_dataframe()
        print(f"\nDuplicate (symbol + bar_date) count: {df_dups.iloc[0]['duplicate_key_count']}")
