"""
InfinityAI.Pro — Institutional Tri-Model MLOps Training Pipeline
Pure Index F&O Engine: Trains CatBoost, LightGBM, XGBoost, and RandomForest on Real Indian Index Data.
Supports: NIFTY, BANKNIFTY, SENSEX, FINNIFTY, MIDCPNIFTY.
Integrates BigQuery Options Data (PCR & OI) with local VM Parquet caching.
Saves and publishes trained model weights to gs://infinity-ai-models-vault/.
"""

import os
import sys
import logging
import argparse
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

# Ensure path includes engine-b src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ML Frameworks
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, log_loss

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

try:
    from google.cloud import storage, bigquery
    HAS_GCS = True
    HAS_BIGQUERY = True
except ImportError:
    HAS_GCS = False
    HAS_BIGQUERY = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("InfinityAI.TriModelTrainer")

# Pure Indian Index Master Mapping for DhanHQ API v2
INDEX_MASTER_MAP = {
    "NIFTY": ("13", "IDX_I"),
    "NIFTY50": ("13", "IDX_I"),
    "BANKNIFTY": ("25", "IDX_I"),
    "SENSEX": ("51", "IDX_I"),
    "BSESN": ("51", "IDX_I"),
    "FINNIFTY": ("27", "IDX_I"),
    "MIDCPNIFTY": ("442", "IDX_I")
}

# BigQuery Project ID
BIGQUERY_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")


def fetch_options_features_from_bigquery(symbol: str) -> pd.DataFrame:
    """
    Fetches BigQuery options ticks, aggregating locally via .parquet cache for VM efficiency.
    Prevents massive egress costs by hitting BQ only once every 24 hours per symbol.
    """
    if not HAS_BIGQUERY:
        logger.warning("BigQuery SDK not installed. Skipping options features.")
        return pd.DataFrame()

    cache_dir = os.path.join(os.path.dirname(__file__), 'local_cache')
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"options_data_{symbol}.parquet")

    # 1. VM Local Cache Check (Valid for 24 hours)
    if os.path.exists(cache_file):
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - file_mod_time < timedelta(hours=24):
            logger.info(f"Loading options data for {symbol} from local VM cache: {cache_file}")
            return pd.read_parquet(cache_file)

    # 2. Fetch from BigQuery if cache missing or expired
    logger.info(f"Cache missed/expired. Fetching {symbol} options data from BigQuery...")
    try:
        client = bigquery.Client(project=BIGQUERY_PROJECT_ID)
        # Pull only required fields to keep memory footprint low
        query = f"""
            SELECT timestamp, option_type, open_interest
            FROM `{BIGQUERY_PROJECT_ID}.market_data.options_ticks`
            WHERE underlying = '{symbol}'
            ORDER BY timestamp ASC
        """
        df = client.query(query).to_dataframe()

        if not df.empty:
            df.to_parquet(cache_file)
            logger.info(f"✅ Saved {symbol} options data to local VM cache: {cache_file}")
        else:
            logger.warning(f"BigQuery returned 0 rows for {symbol} options ticks.")

        return df
    except Exception as e:
        logger.error(f"BigQuery options fetch failed: {e}")
        return pd.DataFrame()


def calculate_features(df_ohlcv: pd.DataFrame, df_options: Optional[pd.DataFrame] = None) -> Tuple[pd.DataFrame, list]:
    """Engineer institutional technical features on Index OHLCV dataset + Options Flow."""
    data = df_ohlcv.copy()

    # Extract robust date index for merging
    if 'date' not in data.columns:
        if 'Date' in data.columns:
            data['date'] = pd.to_datetime(data['Date']).dt.date
        elif data.index.name == 'Date':
            data['date'] = pd.to_datetime(data.index).date
        else:
            try:
                data['date'] = pd.to_datetime(data.index).date
            except Exception as e:
                logger.warning(f"Could not infer date index: {e}")

    feature_cols = []

    # =========================================================
    # 1. INTEGRATE OPTIONS FLOW DATA (PCR & OPEN INTEREST)
    # =========================================================
    if df_options is not None and not df_options.empty:
        logger.info("Aggregating options data to calculate PCR and Total OI momentum...")

        # Convert timestamp to daily date
        df_options['date'] = pd.to_datetime(df_options['timestamp']).dt.date

        # Aggregate Total PE and CE Open Interest per day
        oi_daily = df_options.groupby(['date', 'option_type'])['open_interest'].sum().unstack()

        if 'CE' in oi_daily.columns and 'PE' in oi_daily.columns:
            oi_daily = oi_daily[['CE', 'PE']].rename(columns={'CE': 'Total_CE_OI', 'PE': 'Total_PE_OI'})

            # Calculate Put-Call Ratio (PCR) - handling division by zero
            oi_daily['PCR'] = oi_daily['Total_PE_OI'] / oi_daily['Total_CE_OI'].replace(0, np.nan)

            # Preserve original index to prevent time-series corruption during merge
            orig_index = data.index

            # Merge options features back into the main OHLCV dataframe
            data = data.merge(oi_daily, on='date', how='left')

            # RESTORE original index
            data.index = orig_index

            # Clean up missing data using Forward Fill
            data[['Total_CE_OI', 'Total_PE_OI']] = data[['Total_CE_OI', 'Total_PE_OI']].ffill().fillna(0)
            data['PCR'] = data['PCR'].ffill().fillna(1.0) # Neutral PCR baseline

            feature_cols.extend(['Total_CE_OI', 'Total_PE_OI', 'PCR'])
            logger.info("✅ Successfully merged PCR and OI features.")

    # =========================================================
    # 2. STANDARD OHLCV TECHNICAL INDICATORS
    # =========================================================
    # MUST define these AFTER the merge so they reference the aligned dataframe
    close = data['close']
    high = data['high']
    low = data['low']
    vol = data['volume'] if 'volume' in data.columns else pd.Series(1000, index=data.index)

    # Price Momentum & Returns
    data['ret_1d'] = close.pct_change(1, fill_method=None)
    data['ret_3d'] = close.pct_change(3, fill_method=None)
    data['ret_5d'] = close.pct_change(5, fill_method=None)
    data['ret_10d'] = close.pct_change(10, fill_method=None)
    data['ret_20d'] = close.pct_change(20, fill_method=None)

    # Moving Averages
    data['ema_9'] = close.ewm(span=9, adjust=False).mean()
    data['ema_21'] = close.ewm(span=21, adjust=False).mean()
    data['ema_50'] = close.ewm(span=50, adjust=False).mean()
    data['ema_200'] = close.ewm(span=200, adjust=False).mean()

    data['dist_ema_9'] = (close - data['ema_9']) / data['ema_9']
    data['dist_ema_21'] = (close - data['ema_21']) / data['ema_21']
    data['dist_ema_50'] = (close - data['ema_50']) / data['ema_50']
    data['ema_cross'] = (data['ema_9'] - data['ema_21']) / close

    # RSI (14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    data['rsi'] = 100 - (100 / (1 + rs))

    # MACD (12, 26, 9)
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    data['macd'] = macd / close
    data['macd_signal'] = signal / close
    data['macd_hist'] = (macd - signal) / close

    # Bollinger Bands (20, 2)
    sma_20 = close.rolling(window=20).mean()
    std_20 = close.rolling(window=20).std()
    bb_upper = sma_20 + 2 * std_20
    bb_lower = sma_20 - 2 * std_20
    data['bb_pct'] = (close - bb_lower) / ((bb_upper - bb_lower) + 1e-9)
    data['bb_width'] = (bb_upper - bb_lower) / sma_20

    # ATR & Volatility
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()
    data['atr_pct'] = atr / close

    # Volume dynamics
    vol_ma20 = vol.rolling(window=20).mean()
    data['vol_ratio'] = vol / (vol_ma20 + 1e-9)
    data['obv'] = (np.sign(close.diff()) * vol).fillna(0).cumsum()
    data['obv_slope'] = data['obv'].pct_change(periods=5, fill_method=None)

    # =========================================================
    # 3. TARGET LABEL GENERATION (Future 3-day return)
    # =========================================================
    # 0 = SELL (down > 0.5%), 1 = HOLD (-0.5% to +0.5%), 2 = BUY (up > 0.5%)
    fwd_ret = close.shift(-3) / close - 1.0
    threshold = 0.005

    data['target'] = 1  # Default HOLD
    data.loc[fwd_ret > threshold, 'target'] = 2   # BUY
    data.loc[fwd_ret < -threshold, 'target'] = 0  # SELL

    # Register standard features
    feature_cols.extend([
        'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d',
        'dist_ema_9', 'dist_ema_21', 'dist_ema_50', 'ema_cross',
        'rsi', 'macd', 'macd_signal', 'macd_hist',
        'bb_pct', 'bb_width', 'atr_pct', 'vol_ratio', 'obv_slope'
    ])

    clean_df = data.dropna(subset=feature_cols + ['target']).copy()
    return clean_df, feature_cols


def fetch_index_training_data(symbol: str = "NIFTY", days: int = 730) -> pd.DataFrame:
    """Fetch institutional index data from DhanHQ via Engine-C proxy with Yahoo fallback"""
    import requests
    engine_c_url = os.getenv("ENGINE_C_URL", "https://engine-c-r2f5flt77q-el.a.run.app")

    sec_id, exchange_seg = INDEX_MASTER_MAP.get(symbol.upper(), ("13", "IDX_I"))
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"📡 Fetching {days} days of Index data for {symbol}...")

    # Primary: DhanHQ via Engine-C Proxy
    try:
        r = requests.get(
            f"{engine_c_url}/api/dhan/market/historical",
            params={
                "security_id": sec_id,
                "exchange_segment": exchange_seg,
                "instrument_type": "INDEX",
                "from_date": from_date,
                "to_date": to_date,
                "interval": "daily",
                "user_id": "raghu_primary"
            },
            timeout=20
        )
        if r.status_code == 200:
            c_json = r.json()
            raw_d = c_json.get('data', {})
            candle_d = raw_d.get('data', raw_d) if isinstance(raw_d, dict) else raw_d
            if isinstance(candle_d, dict) and 'close' in candle_d:
                df = pd.DataFrame(candle_d)
                col_map = {'start_Time': 'Date', 'timestamp': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
                df.rename(columns=col_map, inplace=True)
                df.columns = [c.lower() for c in df.columns]
                if len(df) >= 50:
                    logger.info(f"✅ Fetched {len(df)} candles from DhanHQ API v2")
                    return df
    except Exception as e:
        logger.warning(f"Engine-C DhanHQ proxy failed: {e}")

    # Fallback: Yahoo Finance Index Tickers
    try:
        import yfinance as yf
        ticker_map = {
            "NIFTY": "^NSEI", "NIFTY50": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "SENSEX": "^BSESN", "BSESN": "^BSESN",
            "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
            "MIDCPNIFTY": "^NSEMDCP50"
        }
        ticker = ticker_map.get(symbol.upper(), "^NSEI")
        data = yf.download(ticker, period=f"{days}d", interval="1d", progress=False)
        if not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            df = pd.DataFrame({
                'open': data['Open'].values,
                'high': data['High'].values,
                'low': data['Low'].values,
                'close': data['Close'].values,
                'volume': data['Volume'].values if 'Volume' in data.columns else np.zeros(len(data))
            })
            # Ensure index holds date
            df.index = data.index
            logger.info(f"✅ Fetched {len(df)} candles from Yahoo Finance fallback")
            return df
    except Exception as e:
        logger.error(f"Yahoo index fallback failed: {e}")

    raise ValueError(f"Unable to fetch index historical training data for {symbol}")


def train_tri_model_ensemble(
    symbol: str = "NIFTY",
    days: int = 730,
    save_dir: str = "/tmp/models",
    upload_gcs: bool = True,
    gcs_bucket: str = "infinity-ai-models-vault"
) -> Dict[str, Any]:
    """Train Tri-Model Ensemble on Index dataset + BQ Options Data"""
    os.makedirs(save_dir, exist_ok=True)

    # 1. Fetch OHLCV Price Data
    raw_df = fetch_index_training_data(symbol=symbol, days=days)

    # 2. Fetch Options Data from BigQuery / VM Cache
    options_df = fetch_options_features_from_bigquery(symbol=symbol)

    # 3. Engineer Features & Merge
    clean_df, feature_cols = calculate_features(raw_df, options_df)

    X = clean_df[feature_cols].values
    y = clean_df['target'].values.astype(int)

    # 4. Train / Validation Split (80/20 Time-Series Split)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logger.info(f"📊 {symbol} Training Set: {len(X_train)} samples | Test Set: {len(X_test)} samples | Features: {len(feature_cols)}")

    results = {}
    models = {}

    # --- A. XGBoost Classifier ---
    logger.info("🌲 Training XGBoost Classifier...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=150, max_depth=5, learning_rate=0.03,
        objective='multi:softprob', eval_metric='mlogloss',
        random_state=42, n_jobs=-1
    )
    xgb_model.fit(X_train_scaled, y_train)
    xgb_preds = xgb_model.predict(X_test_scaled)
    xgb_proba = xgb_model.predict_proba(X_test_scaled)
    models['xgboost'] = xgb_model
    results['xgboost'] = {
        'accuracy': float(accuracy_score(y_test, xgb_preds)),
        'f1_score': float(f1_score(y_test, xgb_preds, average='weighted', zero_division=0)),
        'log_loss': float(log_loss(y_test, xgb_proba, labels=[0, 1, 2]))
    }

    # --- B. LightGBM Classifier ---
    logger.info("⚡ Training LightGBM Classifier...")
    lgb_model = lgb.LGBMClassifier(
        n_estimators=150, max_depth=5, learning_rate=0.03,
        random_state=42, verbose=-1, n_jobs=-1
    )
    lgb_model.fit(X_train_scaled, y_train)
    lgb_preds = lgb_model.predict(X_test_scaled)
    lgb_proba = lgb_model.predict_proba(X_test_scaled)
    models['lightgbm'] = lgb_model
    results['lightgbm'] = {
        'accuracy': float(accuracy_score(y_test, lgb_preds)),
        'f1_score': float(f1_score(y_test, lgb_preds, average='weighted', zero_division=0)),
        'log_loss': float(log_loss(y_test, lgb_proba, labels=[0, 1, 2]))
    }

    # --- C. CatBoost Classifier ---
    if HAS_CATBOOST:
        logger.info("🐱 Training CatBoost Classifier...")
        cat_model = CatBoostClassifier(
            iterations=150, depth=5, learning_rate=0.03,
            random_state=42, verbose=False
        )
        cat_model.fit(X_train_scaled, y_train)
        cat_preds = cat_model.predict(X_test_scaled)
        cat_proba = cat_model.predict_proba(X_test_scaled)
        models['catboost'] = cat_model
        results['catboost'] = {
            'accuracy': float(accuracy_score(y_test, cat_preds)),
            'f1_score': float(f1_score(y_test, cat_preds, average='weighted', zero_division=0)),
            'log_loss': float(log_loss(y_test, cat_proba, labels=[0, 1, 2]))
        }

    # --- D. Random Forest Classifier ---
    logger.info("🌳 Training Random Forest Classifier...")
    rf_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
    rf_model.fit(X_train_scaled, y_train)
    rf_preds = rf_model.predict(X_test_scaled)
    rf_proba = rf_model.predict_proba(X_test_scaled)
    models['random_forest'] = rf_model
    results['random_forest'] = {
        'accuracy': float(accuracy_score(y_test, rf_preds)),
        'f1_score': float(f1_score(y_test, rf_preds, average='weighted', zero_division=0)),
        'log_loss': float(log_loss(y_test, rf_proba, labels=[0, 1, 2]))
    }

    # --- E. Weighted Ensemble Evaluation ---
    weights = {'xgboost': 0.40, 'lightgbm': 0.30, 'catboost': 0.15, 'random_forest': 0.15}
    ensemble_proba = (
        weights['xgboost'] * xgb_proba +
        weights['lightgbm'] * lgb_proba +
        (weights['catboost'] * cat_proba if HAS_CATBOOST else 0) +
        weights['random_forest'] * rf_proba
    )
    ensemble_preds = np.argmax(ensemble_proba, axis=1)
    ensemble_acc = float(accuracy_score(y_test, ensemble_preds))
    ensemble_f1 = float(f1_score(y_test, ensemble_preds, average='weighted', zero_division=0))

    results['ensemble'] = {
        'accuracy': ensemble_acc,
        'f1_score': ensemble_f1,
        'log_loss': float(log_loss(y_test, ensemble_proba, labels=[0, 1, 2])),
        'weights': weights
    }
    logger.info(f"🏆 Index {symbol} TRI-MODEL ENSEMBLE Accuracy: {ensemble_acc*100:.2f}% | F1: {ensemble_f1:.4f}")

    # --- 5. Serialize Model Artifacts ---
    logger.info("💾 Saving Model Artifacts locally...")
    joblib.dump(lgb_model, os.path.join(save_dir, "lightgbm_model.pkl"))
    joblib.dump(rf_model, os.path.join(save_dir, "random_forest_model.pkl"))
    joblib.dump(scaler, os.path.join(save_dir, "scaler.pkl"))
    xgb_model.save_model(os.path.join(save_dir, "xgboost_model.json"))

    if HAS_CATBOOST:
        cat_model.save_model(os.path.join(save_dir, "catboost_model.cbm"))

    # --- 6. Publish Artifacts to GCS Model Vault ---
    if upload_gcs and HAS_GCS:
        try:
            logger.info(f"☁️ Uploading model artifacts to gs://{gcs_bucket}/...")
            client = storage.Client()
            bucket = client.bucket(gcs_bucket)

            for file_name in ["lightgbm_model.pkl", "random_forest_model.pkl", "scaler.pkl", "xgboost_model.json"]:
                p = os.path.join(save_dir, file_name)
                if os.path.exists(p):
                    bucket.blob(file_name).upload_from_filename(p)

            if HAS_CATBOOST and os.path.exists(os.path.join(save_dir, "catboost_model.cbm")):
                bucket.blob("catboost_model.cbm").upload_from_filename(os.path.join(save_dir, "catboost_model.cbm"))

            results['gcs_uploaded'] = True
            logger.info(f"✅ Successfully published all {symbol} index models to gs://{gcs_bucket}/")
        except Exception as e:
            logger.warning(f"GCS Upload Notice: {e}")
            results['gcs_uploaded'] = False

    return {
        "status": "success",
        "symbol": symbol,
        "samples_trained": len(X_train),
        "samples_tested": len(X_test),
        "features_count": len(feature_cols),
        "features": feature_cols,
        "metrics": results,
        "trained_at": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Tri-Model ML Ensemble on Real Indian Index Data")
    parser.add_argument("--symbol", type=str, default="NIFTY", help="Index symbol: NIFTY, BANKNIFTY, SENSEX, FINNIFTY")
    parser.add_argument("--days", type=int, default=730, help="Historical lookback days")
    parser.add_argument("--upload-gcs", action="store_true", default=True, help="Upload to GCS Vault")
    args = parser.parse_args()

    res = train_tri_model_ensemble(symbol=args.symbol, days=args.days, upload_gcs=args.upload_gcs)
    import json
    print(json.dumps(res, indent=2))

# Sort values and set index
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data = data.sort_values('date').set_index('date')

    # Core Technical Indicators
    data['returns'] = data['close'].pct_change()
    data['log_returns'] = np.log1p(data['returns'])
    data['sma_5'] = data['close'].rolling(5).mean()
    data['sma_20'] = data['close'].rolling(20).mean()
    data['ema_12'] = data['close'].ewm(span=12, adjust=False).mean()
    data['ema_26'] = data['close'].ewm(span=26, adjust=False).mean()

    # MACD
    data['macd'] = data['ema_12'] - data['ema_26']
    data['macd_signal'] = data['macd'].ewm(span=9, adjust=False).mean()

    # RSI (14)
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    data['rsi'] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    roll_mean = data['close'].rolling(20).mean()
    roll_std = data['close'].rolling(20).std()
    data['bb_upper'] = roll_mean + (roll_std * 2)
    data['bb_lower'] = roll_mean - (roll_std * 2)
    data['bb_width'] = (data['bb_upper'] - data['bb_lower']) / (roll_mean + 1e-9)

    # Volatility
    data['volatility_10'] = data['returns'].rolling(10).std()
    data['volatility_30'] = data['returns'].rolling(30).std()

    # Integrate Options Features (PCR, OI) if available
    if df_options is not None and not df_options.empty:
        logger.info("🔗 Merging Options-derived features (PCR, OI) into training dataset...")
        if 'date' in df_options.columns:
            df_options['date'] = pd.to_datetime(df_options['date'])
            df_options = df_options.set_index('date')

        # Merge on date index
        data = data.join(df_options, how='left')

        # Fill missing options metrics with forward-fill or defaults
        options_cols = ['pcr', 'total_ce_oi', 'total_pe_oi', 'avg_iv']
        for col in options_cols:
            if col in data.columns:
                data[col] = data[col].fillna(method='ffill').fillna(1.0 if 'pcr' in col else 0.0)

    # Define Target Variable (1 if next day close > current close, else 0)
    data['target'] = (data['close'].shift(-1) > data['close']).astype(int)

    # Drop rows with NaN resulting from rolling windows/shifts
    data = data.dropna()

    # Feature columns list
    feature_cols = [
        'returns', 'log_returns', 'sma_5', 'sma_20', 'ema_12', 'ema_26',
        'macd', 'macd_signal', 'rsi', 'bb_width', 'volatility_10', 'volatility_30'
    ]

    # Add options features to training features if present
    for col in ['pcr', 'total_ce_oi', 'total_pe_oi', 'avg_iv']:
        if col in data.columns:
            feature_cols.append(col)

    return data, feature_cols
