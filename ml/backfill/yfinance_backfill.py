import yfinance as yf
import pandas as pd
import ta
import time
from google.cloud import bigquery
import os

# Map DhanHQ symbols to yfinance symbols
# 13 -> NIFTY 50 -> ^NSEI
# 25 -> BANKNIFTY -> ^NSEBANK
# 2885 -> RELIANCE -> RELIANCE.NS
# 11536 -> TCS -> TCS.NS
SYMBOLS = [
    {"name": "NIFTY 50", "ticker": "^NSEI"},
    {"name": "BANKNIFTY", "ticker": "^NSEBANK"},
    {"name": "RELIANCE", "ticker": "RELIANCE.NS"},
    {"name": "TCS", "ticker": "TCS.NS"}
]

# Set credentials implicitly using the local GCP environment if not already set
# But since antigravity-ide has ADC (Application Default Credentials), bigquery.Client() should just work.
bq_client = bigquery.Client(project="project-841b7f97-5ee3-4fbe-920")
table_id = "project-841b7f97-5ee3-4fbe-920.infinity_dataset.market_ticks_history"

def backfill():
    print(f"Truncating {table_id}...")
    try:
        bq_client.query(f"TRUNCATE TABLE `{table_id}`").result()
        print("Truncate successful.")
    except Exception as e:
        print(f"Failed to truncate: {e}")
        try:
            bq_client.query(f"DELETE FROM `{table_id}` WHERE 1=1").result()
        except Exception as e2:
            print(f"DELETE failed: {e2}")

    all_data = []

    for sym in SYMBOLS:
        print(f"Fetching 60 days of 5-minute data for {sym['name']} ({sym['ticker']}) via yfinance...")
        try:
            # yfinance supports 60 days max for 5m interval
            df = yf.download(sym["ticker"], period="60d", interval="5m", progress=False)
        except Exception as e:
            print(f"Error fetching {sym['name']}: {e}")
            continue
            
        if df.empty:
            print(f"Failed to fetch data for {sym['name']}")
            continue
            
        print(f"Fetched {len(df)} rows for {sym['name']}. Calculating indicators...")
        
        # yfinance returns multi-level columns sometimes depending on version, let's flatten if needed
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Rename columns to lowercase
        df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        # The index is the timestamp
        df = df.reset_index()
        df = df.rename(columns={"Datetime": "timestamp", "Date": "timestamp"})
        
        # Ensure timezone is UTC for BigQuery compatibility
        if df['timestamp'].dt.tz is not None:
            df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
        else:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')

        try:
            df["rsi_14"] = ta.momentum.RSIIndicator(close=df["close"], window=14).rsi()
            macd = ta.trend.MACD(close=df["close"])
            df["macd_line"] = macd.macd()
            df["macd_signal"] = macd.macd_signal()
            df["macd_crossover"] = 0
            df.loc[df["macd_line"] > df["macd_signal"], "macd_crossover"] = 1
            df.loc[df["macd_line"] < df["macd_signal"], "macd_crossover"] = -1
            
            vwap = ta.volume.VolumeWeightedAveragePrice(
                high=df["high"], low=df["low"], close=df["close"], volume=df["volume"]
            )
            df["vwap"] = vwap.volume_weighted_average_price()
            df["vwap_distance"] = (df["close"] - df["vwap"]) / df["vwap"]
            
            atr = ta.volatility.AverageTrueRange(high=df["high"], low=df["low"], close=df["close"])
            df["atr_volatility"] = atr.average_true_range()
            
            # Future 15 min return. Since interval is 5m, we shift by -3
            df["future_close_15"] = df["close"].shift(-3)
            df["signal_outcome"] = (df["future_close_15"] > df["close"]).astype(int)
            df = df.dropna()
        except Exception as e:
            print(f"Error calculating indicators for {sym['name']}: {e}")
            continue
            
        print(f"Data cleaned. {len(df)} valid rows ready for {sym['name']}.")
        
        bq_df = df[["timestamp", "rsi_14", "macd_crossover", "vwap_distance", "atr_volatility", "signal_outcome"]]
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        try:
            job = bq_client.load_table_from_dataframe(bq_df, table_id, job_config=job_config)
            job.result()
            print(f"✅ Successfully loaded {job.output_rows} rows for {sym['name']} to BigQuery.")
        except Exception as e:
            print(f"BigQuery load failed for {sym['name']}: {e}")
            
        time.sleep(2) # rate limit buffer
        
if __name__ == "__main__":
    backfill()
