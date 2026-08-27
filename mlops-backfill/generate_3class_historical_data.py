import yfinance as yf
import pandas as pd
import numpy as np
import ta
import time
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
DATASET_ID = "infinity_dataset"
CANDIDATE_TABLE = "market_ticks_history_3class_v2"
PROD_TABLE = "market_ticks_history"

SYMBOLS = [
    {"name": "NIFTYBEES", "ticker": "NIFTYBEES.NS"},
    {"name": "BANKBEES", "ticker": "BANKBEES.NS"},
    {"name": "RELIANCE", "ticker": "RELIANCE.NS"},
    {"name": "HDFCBANK", "ticker": "HDFCBANK.NS"},
    {"name": "ICICIBANK", "ticker": "ICICIBANK.NS"},
    {"name": "INFY", "ticker": "INFY.NS"},
    {"name": "TCS", "ticker": "TCS.NS"},
    {"name": "ITC", "ticker": "ITC.NS"},
    {"name": "LT", "ticker": "LT.NS"},
    {"name": "SBIN", "ticker": "SBIN.NS"},
    {"name": "AXISBANK", "ticker": "AXISBANK.NS"},
    {"name": "KOTAKBANK", "ticker": "KOTAKBANK.NS"}
]

def generate_3class_dataset():
    print(f"=== 1. Generating 3-Class Historical Dataset for {len(SYMBOLS)} symbols ===")
    all_dfs = []

    for sym in SYMBOLS:
        print(f"Fetching 60d 5m candles for {sym['name']} ({sym['ticker']})...")
        df = yf.download(sym["ticker"], period="60d", interval="5m", progress=False)
        if df.empty:
            print(f"  Warning: No data for {sym['name']}")
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        df = df.reset_index()
        df = df.rename(columns={"Datetime": "timestamp", "Date": "timestamp"})
        
        # Ensure UTC timezone
        if df['timestamp'].dt.tz is not None:
            df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
        else:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            
        # 1. RSI (14)
        df["rsi_14"] = ta.momentum.RSIIndicator(close=df["close"], window=14).rsi()
        
        # 2. MACD Crossover (-1, 0, 1)
        macd = ta.trend.MACD(close=df["close"])
        df["macd_line"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_crossover"] = 0
        df.loc[df["macd_line"] > df["macd_signal"], "macd_crossover"] = 1
        df.loc[df["macd_line"] < df["macd_signal"], "macd_crossover"] = -1
        
        # 3. VWAP & Distance
        if "volume" in df.columns and (df["volume"] > 0).any():
            vwap = ta.volume.VolumeWeightedAveragePrice(
                high=df["high"], low=df["low"], close=df["close"], volume=df["volume"]
            )
            df["vwap"] = vwap.volume_weighted_average_price()
        else:
            df["vwap"] = (df["high"] + df["low"] + df["close"]) / 3.0
        
        df["vwap_distance"] = (df["close"] - df["vwap"]) / df["vwap"]
        
        # 4. ATR Volatility
        atr = ta.volatility.AverageTrueRange(high=df["high"], low=df["low"], close=df["close"])
        df["atr_volatility"] = atr.average_true_range()
        
        # 5. 3-Class Target Generation
        # Forward 15-min return (3 x 5m candles)
        df["future_close_15"] = df["close"].shift(-3)
        df["fwd_ret"] = (df["future_close_15"] - df["close"]) / df["close"]
        
        # 0 = SELL (fwd_ret <= -0.20%), 1 = HOLD (-0.20% < fwd_ret < +0.20%), 2 = BUY (fwd_ret >= +0.20%)
        df["signal_outcome"] = 1 # default HOLD
        df.loc[df["fwd_ret"] >= 0.0020, "signal_outcome"] = 2 # BUY
        df.loc[df["fwd_ret"] <= -0.0020, "signal_outcome"] = 0 # SELL
        
        df = df.dropna(subset=["timestamp", "rsi_14", "macd_crossover", "vwap_distance", "atr_volatility", "signal_outcome"])
        print(f"  • {sym['name']}: {len(df):,} valid rows | Class distribution: {df['signal_outcome'].value_counts().to_dict()}")
        all_dfs.append(df[["timestamp", "rsi_14", "macd_crossover", "vwap_distance", "atr_volatility", "signal_outcome"]])

    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df["timestamp"] = pd.to_datetime(combined_df["timestamp"])
    combined_df["signal_outcome"] = combined_df["signal_outcome"].astype(int)
    combined_df["macd_crossover"] = combined_df["macd_crossover"].astype(int)
    
    print("\n=== 2. Dataset Quality Checks ===")
    print(f"Total Rows: {len(combined_df):,}")
    print("Null Counts:\n", combined_df.isnull().sum())
    print("\nClass Value Counts:")
    print(combined_df["signal_outcome"].value_counts())
    print("\nClass Percentages (%):")
    print(combined_df["signal_outcome"].value_counts(normalize=True) * 100)
    
    # 3. Write to BigQuery candidate table
    bq_client = bigquery.Client(project=PROJECT_ID, location="asia-south1")
    candidate_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{CANDIDATE_TABLE}"
    
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("rsi_14", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("macd_crossover", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("vwap_distance", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("atr_volatility", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("signal_outcome", "INT64", mode="NULLABLE"),
    ]
    
    print(f"\n=== 3. Uploading to BigQuery Candidate Table: {candidate_table_ref} ===")
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE"
    )
    
    job = bq_client.load_table_from_dataframe(combined_df, candidate_table_ref, job_config=job_config)
    job.result()
    print(f"[SUCCESS] Successfully loaded {job.output_rows:,} rows into {candidate_table_ref}")
    
    # Also overwrite the production table with this 3-class dataset so both are synchronized
    prod_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{PROD_TABLE}"
    print(f"\n=== 4. Updating Production Table: {prod_table_ref} ===")
    job_prod = bq_client.load_table_from_dataframe(combined_df, prod_table_ref, job_config=job_config)
    job_prod.result()
    print(f"[SUCCESS] Successfully updated {job_prod.output_rows:,} rows in {prod_table_ref}")

if __name__ == "__main__":
    generate_3class_dataset()
