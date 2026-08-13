import asyncio
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import ta
import time
from google.cloud import bigquery

# Add src to python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from src.user_credentials import UserCredentialsManager
from src.dhan_client_wrapper import create_dhan_client

async def main():
    print("Initializing UserCredentialsManager...")
    creds_manager = UserCredentialsManager()
    
    user_id = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
    print(f"Fetching credentials for {user_id}...")
    creds_response = await creds_manager.get_user_credentials(user_id)
    
    if not creds_response or not creds_response.get("dhan_access_token"):
        print("Failed to get credentials.")
        return
        
    client_id = creds_response.get("dhan_client_id")
    access_token = creds_response.get("dhan_access_token")
    
    print("Creating DhanHQ Client...")
    dhan = create_dhan_client(client_id, access_token)
    
    # 30 days up to yesterday
    to_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d")
    
    # A representative list of "EVERYTHING" core instruments to avoid hitting DhanHQ rate limits too hard
    # 13 = NIFTY 50, 25 = BANKNIFTY, 2885 = RELIANCE, 11536 = TCS
    symbols = [
        {"id": "13", "segment": "IDX_I", "type": "INDEX"},
        {"id": "25", "segment": "IDX_I", "type": "INDEX"},
        {"id": "2885", "segment": "NSE_EQ", "type": "EQUITY"},
        {"id": "11536", "segment": "NSE_EQ", "type": "EQUITY"}
    ]
    
    bq_client = bigquery.Client()
    table_id = "project-841b7f97-5ee3-4fbe-920.infinity_dataset.market_ticks_history"
    
    # 1. Truncate Table Once
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

    for sym in symbols:
        print(f"Fetching data for {sym['id']} from {from_date} to {to_date}...")
        try:
            resp = dhan.intraday_minute_data(
                security_id=sym["id"],
                exchange_segment=sym["segment"],
                instrument_type=sym["type"],
                from_date=from_date,
                to_date=to_date
            )
        except Exception as e:
            print(f"Error fetching {sym['id']}: {e}")
            continue
            
        if not resp or resp.get("status") == "failure" or not resp.get("data"):
            print(f"Failed to fetch data for {sym['id']}: {resp}")
            continue
            
        raw_data = resp["data"]
        if "start_Time" in raw_data:
            df = pd.DataFrame({
                "timestamp": pd.to_datetime(raw_data["start_Time"]),
                "open": raw_data["open"],
                "high": raw_data["high"],
                "low": raw_data["low"],
                "close": raw_data["close"],
                "volume": raw_data["volume"]
            })
            # Ensure it's explicitly a datetime object, not float
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
        else:
            df = pd.DataFrame(raw_data)
            
        print(f"Fetched {len(df)} rows for {sym['id']}. Calculating indicators...")
        if len(df) == 0:
            continue
            
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp")
            
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
            
            df["future_close_15"] = df["close"].shift(-15)
            df["signal_outcome"] = (df["future_close_15"] > df["close"]).astype(int)
            df = df.dropna()
        except Exception as e:
            print(f"Error calculating indicators for {sym['id']}: {e}")
            continue
            
        print(f"Data cleaned. {len(df)} valid rows ready for {sym['id']}.")
        
        bq_df = df[["timestamp", "rsi_14", "macd_crossover", "vwap_distance", "atr_volatility", "signal_outcome"]].copy()
        
        # Ensure timestamp is explicitly datetime64[ns]
        bq_df["timestamp"] = pd.to_datetime(bq_df["timestamp"], unit='s', origin='unix')
        print("Data types before load:")
        print(bq_df.dtypes)
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        try:
            job = bq_client.load_table_from_dataframe(bq_df, table_id, job_config=job_config)
            job.result()
            print(f"✅ Successfully loaded {job.output_rows} rows for {sym['id']} to BigQuery.")
        except Exception as e:
            print(f"BigQuery load failed for {sym['id']}: {e}")
            
        time.sleep(2) # rate limit buffer

if __name__ == "__main__":
    asyncio.run(main())
