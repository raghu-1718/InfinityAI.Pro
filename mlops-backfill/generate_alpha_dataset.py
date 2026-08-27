import yfinance as yf
import pandas as pd
import numpy as np
import ta
from google.cloud import bigquery

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
DATASET_ID = "infinity_dataset"
TABLE_ID = "market_ticks_history"
ALPHA_TABLE_ID = "market_ticks_history_alpha"

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
    {"name": "KOTAKBANK", "ticker": "KOTAKBANK.NS"},
    {"name": "BHARTIARTL", "ticker": "BHARTIARTL.NS"},
    {"name": "BAJFINANCE", "ticker": "BAJFINANCE.NS"}
]

def generate_alpha_dataset():
    print(f"=== 1. Generating Enriched Alpha Dataset for {len(SYMBOLS)} symbols ===")
    all_dfs = []

    for sym in SYMBOLS:
        print(f"Fetching 60d 5m candles for {sym['name']} ({sym['ticker']})...")
        df = yf.download(sym["ticker"], period="60d", interval="5m", progress=False)
        if df.empty or len(df) < 500:
            print(f"  Warning: Insufficient data for {sym['name']}")
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        df = df.reset_index()
        df = df.rename(columns={"Datetime": "timestamp", "Date": "timestamp"})
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        # Ensure UTC timezone
        if df['timestamp'].dt.tz is not None:
            df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
        else:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')

        # 1. EMAs & Trend Alignment
        df["ema_20"] = ta.trend.EMAIndicator(close=df["close"], window=20).ema_indicator()
        df["ema_50"] = ta.trend.EMAIndicator(close=df["close"], window=50).ema_indicator()
        df["trend_aligned"] = 0
        df.loc[(df["close"] > df["ema_50"]) & (df["ema_20"] > df["ema_50"]), "trend_aligned"] = 1  # Bullish
        df.loc[(df["close"] < df["ema_50"]) & (df["ema_20"] < df["ema_50"]), "trend_aligned"] = -1 # Bearish

        # 2. Oscillators & Indicators
        df["rsi_14"] = ta.momentum.RSIIndicator(close=df["close"], window=14).rsi()
        macd = ta.trend.MACD(close=df["close"])
        df["macd_line"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_hist"] = macd.macd_diff()
        df["macd_crossover"] = 0
        df.loc[df["macd_line"] > df["macd_signal"], "macd_crossover"] = 1
        df.loc[df["macd_line"] < df["macd_signal"], "macd_crossover"] = -1

        # 3. Volatility & Regimes
        atr = ta.volatility.AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=14)
        df["atr_volatility"] = atr.average_true_range()
        df["atr_ratio"] = df["atr_volatility"] / df["close"]
        adx = ta.trend.ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=14)
        df["adx_14"] = adx.adx()
        df["adx_slope"] = df["adx_14"].diff(3)

        bb = ta.volatility.BollingerBands(close=df["close"], window=20, window_dev=2)
        df["bollinger_bandwidth"] = (bb.bollinger_hband() - bb.bollinger_lband()) / (bb.bollinger_mavg() + 1e-6)
        df["bb_pct"] = (df["close"] - bb.bollinger_lband()) / (bb.bollinger_hband() - bb.bollinger_lband() + 1e-6)

        # 4. VWAP
        if "volume" in df.columns and (df["volume"] > 0).any():
            vwap = ta.volume.VolumeWeightedAveragePrice(
                high=df["high"], low=df["low"], close=df["close"], volume=df["volume"]
            )
            df["vwap"] = vwap.volume_weighted_average_price()
        else:
            df["vwap"] = (df["high"] + df["low"] + df["close"]) / 3.0
        df["vwap_distance"] = (df["close"] - df["vwap"]) / df["vwap"]

        # 5. Price Action & Momentum
        df["return_15m_past"] = df["close"].pct_change(3)
        df["return_5m_past"] = df["close"].pct_change(1)

        # 6. Triple Barrier Dynamic ATR Target Labeling over next 12 candles (60 mins max):
        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values
        atrs = df["atr_volatility"].values

        n = len(df)
        labels = np.ones(n, dtype=int) # Default 1 (HOLD)
        horizon = 12

        for i in range(n - horizon):
            entry_price = closes[i]
            vol = atrs[i]
            if np.isnan(vol) or vol <= 0:
                continue

            upper_barrier = entry_price + (1.2 * vol)
            lower_barrier = entry_price - (1.0 * vol)

            hit = 1
            for h in range(1, horizon + 1):
                cur_high = highs[i + h]
                cur_low = lows[i + h]

                upper_hit = cur_high >= upper_barrier
                lower_hit = cur_low <= lower_barrier

                if upper_hit and not lower_hit:
                    hit = 2 # BUY
                    break
                elif lower_hit and not upper_hit:
                    hit = 0 # SELL
                    break
                elif upper_hit and lower_hit:
                    hit = 2 if closes[i + h] > entry_price else 0
                    break
            labels[i] = hit

        df["signal_outcome"] = labels

        # Chronological Time-Ordered Split flag (75% Train = False, 25% Out-Of-Time Test = True)
        split_idx = int(len(df) * 0.75)
        df["is_test"] = False
        df.iloc[split_idx:, df.columns.get_loc("is_test")] = True

        feature_cols = [
            "timestamp", "signal_outcome", "is_test",
            "rsi_14", "macd_line", "macd_signal", "macd_hist", "macd_crossover",
            "vwap_distance", "atr_volatility", "atr_ratio", "adx_14", "adx_slope",
            "bollinger_bandwidth", "bb_pct", "return_15m_past", "return_5m_past", "trend_aligned"
        ]

        clean_df = df.dropna(subset=feature_cols).copy()
        print(f"  • {sym['name']}: {len(clean_df):,} valid rows | Classes: {clean_df['signal_outcome'].value_counts().to_dict()}")
        all_dfs.append(clean_df[feature_cols])

    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df["timestamp"] = pd.to_datetime(combined_df["timestamp"])
    combined_df["signal_outcome"] = combined_df["signal_outcome"].astype(int)
    combined_df["macd_crossover"] = combined_df["macd_crossover"].astype(int)
    combined_df["trend_aligned"] = combined_df["trend_aligned"].astype(int)
    combined_df["is_test"] = combined_df["is_test"].astype(bool)

    print("\n=== 2. Enriched Dataset Quality Summary ===")
    print(f"Total Rows: {len(combined_df):,}")
    print(f"Train Rows: {(~combined_df['is_test']).sum():,} | Test Rows: {combined_df['is_test'].sum():,}")
    print("\nClass Value Counts:")
    print(combined_df["signal_outcome"].value_counts())
    print("\nClass Percentages (%):")
    print(combined_df["signal_outcome"].value_counts(normalize=True) * 100)

    bq_client = bigquery.Client(project=PROJECT_ID, location="asia-south1")
    
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("signal_outcome", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("is_test", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("rsi_14", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("macd_line", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("macd_signal", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("macd_hist", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("macd_crossover", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("vwap_distance", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("atr_volatility", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("atr_ratio", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("adx_14", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("adx_slope", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("bollinger_bandwidth", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("bb_pct", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("return_15m_past", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("return_5m_past", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("trend_aligned", "INT64", mode="NULLABLE"),
    ]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE"
    )

    alpha_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{ALPHA_TABLE_ID}"
    print(f"\n=== 3. Uploading to Alpha Table: {alpha_table_ref} ===")
    job_alpha = bq_client.load_table_from_dataframe(combined_df, alpha_table_ref, job_config=job_config)
    job_alpha.result()
    print(f"[SUCCESS] Loaded {job_alpha.output_rows:,} rows into {alpha_table_ref}")

    prod_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    print(f"\n=== 4. Updating Production Table: {prod_table_ref} ===")
    job_prod = bq_client.load_table_from_dataframe(combined_df, prod_table_ref, job_config=job_config)
    job_prod.result()
    print(f"[SUCCESS] Updated {job_prod.output_rows:,} rows in {prod_table_ref}")

if __name__ == "__main__":
    generate_alpha_dataset()
