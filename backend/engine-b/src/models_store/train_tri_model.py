"""
InfinityAI.Pro — Institutional Tri-Model MLOps Training Pipeline
Trains CatBoost, LightGBM, XGBoost, and RandomForest on Real Indian Capital Market Data.
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
    from google.cloud import storage
    HAS_GCS = True
except ImportError:
    HAS_GCS = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("InfinityAI.TriModelTrainer")


def calculate_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """Engineer institutional technical features on OHLCV dataset"""
    data = df.copy()
    close = data['close']
    high = data['high']
    low = data['low']
    vol = data['volume']

    # 1. Price Momentum & Returns
    data['ret_1d'] = close.pct_change(1)
    data['ret_3d'] = close.pct_change(3)
    data['ret_5d'] = close.pct_change(5)
    data['ret_10d'] = close.pct_change(10)
    data['ret_20d'] = close.pct_change(20)

    # 2. Moving Averages
    data['ema_9'] = close.ewm(span=9, adjust=False).mean()
    data['ema_21'] = close.ewm(span=21, adjust=False).mean()
    data['ema_50'] = close.ewm(span=50, adjust=False).mean()
    data['ema_200'] = close.ewm(span=200, adjust=False).mean()

    data['dist_ema_9'] = (close - data['ema_9']) / data['ema_9']
    data['dist_ema_21'] = (close - data['ema_21']) / data['ema_21']
    data['dist_ema_50'] = (close - data['ema_50']) / data['ema_50']
    data['ema_cross'] = (data['ema_9'] - data['ema_21']) / close

    # 3. RSI (14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    data['rsi'] = 100 - (100 / (1 + rs))

    # 4. MACD (12, 26, 9)
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    data['macd'] = macd / close
    data['macd_signal'] = signal / close
    data['macd_hist'] = (macd - signal) / close

    # 5. Bollinger Bands (20, 2)
    sma_20 = close.rolling(window=20).mean()
    std_20 = close.rolling(window=20).std()
    bb_upper = sma_20 + 2 * std_20
    bb_lower = sma_20 - 2 * std_20
    data['bb_pct'] = (close - bb_lower) / ((bb_upper - bb_lower) + 1e-9)
    data['bb_width'] = (bb_upper - bb_lower) / sma_20

    # 6. ATR & Volatility
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()
    data['atr_pct'] = atr / close

    # 7. Volume dynamics
    vol_ma20 = vol.rolling(window=20).mean()
    data['vol_ratio'] = vol / (vol_ma20 + 1e-9)
    data['obv'] = (np.sign(close.diff()) * vol).fillna(0).cumsum()
    data['obv_slope'] = data['obv'].pct_change(5)

    # 8. Target Label Generation (Future 3-day return)
    # 0 = SELL (down > 0.6%), 1 = HOLD (-0.6% to +0.6%), 2 = BUY (up > 0.6%)
    fwd_ret = close.shift(-3) / close - 1.0
    threshold = 0.006

    data['target'] = 1  # Default HOLD
    data.loc[fwd_ret > threshold, 'target'] = 2   # BUY
    data.loc[fwd_ret < -threshold, 'target'] = 0  # SELL

    # Drop NaNs
    feature_cols = [
        'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d',
        'dist_ema_9', 'dist_ema_21', 'dist_ema_50', 'ema_cross',
        'rsi', 'macd', 'macd_signal', 'macd_hist',
        'bb_pct', 'bb_width', 'atr_pct', 'vol_ratio', 'obv_slope'
    ]

    clean_df = data.dropna(subset=feature_cols + ['target']).copy()
    return clean_df, feature_cols


def fetch_training_data(symbol: str = "NIFTY", days: int = 730) -> pd.DataFrame:
    """Fetch training data from DhanHQ via Engine-C proxy with fallback to Yahoo"""
    import requests
    engine_c_url = os.getenv("ENGINE_C_URL", "https://engine-c-r2f5flt77q-el.a.run.app")
    
    sec_id_map = {
        "NIFTY": ("13", "IDX_I", "INDEX"),
        "BANKNIFTY": ("25", "IDX_I", "INDEX"),
        "SENSEX": ("51", "IDX_I", "INDEX"),
        "RELIANCE": ("2885", "NSE_EQ", "EQUITY"),
        "TCS": ("11536", "NSE_EQ", "EQUITY"),
        "INFY": ("1594", "NSE_EQ", "EQUITY"),
        "HDFCBANK": ("1333", "NSE_EQ", "EQUITY")
    }

    sec_info = sec_id_map.get(symbol.upper(), ("13", "IDX_I", "INDEX"))
    sec_id, exchange_seg, inst_type = sec_info
    
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"📡 Fetching {days} days of training data for {symbol} (SecID: {sec_id}, Segment: {exchange_seg})...")
    
    # Try DhanHQ via Engine-C Proxy
    try:
        r = requests.get(
            f"{engine_c_url}/api/dhan/market/historical",
            params={
                "security_id": sec_id,
                "exchange_segment": exchange_seg,
                "instrument_type": inst_type,
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
                    logger.info(f"✅ Successfully fetched {len(df)} candles from DhanHQ API v2 for {symbol}")
                    return df
    except Exception as e:
        logger.warning(f"Engine-C DhanHQ proxy fetch failed: {e}")

    # Fallback to yfinance
    try:
        import yfinance as yf
        ticker_map = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN", "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "INFY": "INFY.NS", "HDFCBANK": "HDFCBANK.NS"}
        ticker = ticker_map.get(symbol.upper(), f"{symbol}.NS")
        data = yf.download(ticker, period=f"{days}d", interval="1d", progress=False)
        if not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            df = pd.DataFrame({
                'open': data['Open'].values,
                'high': data['High'].values,
                'low': data['Low'].values,
                'close': data['Close'].values,
                'volume': data['Volume'].values
            })
            logger.info(f"✅ Fetched {len(df)} candles from Yahoo Finance for {symbol}")
            return df
    except Exception as e:
        logger.error(f"Yahoo fallback failed: {e}")

    raise ValueError(f"Unable to fetch historical training data for {symbol}")


def train_tri_model_ensemble(
    symbol: str = "NIFTY",
    days: int = 730,
    save_dir: str = "/tmp/models",
    upload_gcs: bool = True,
    gcs_bucket: str = "infinity-ai-models-vault"
) -> Dict[str, Any]:
    """Train Tri-Model Ensemble (XGBoost, LightGBM, CatBoost, RandomForest) on real dataset"""
    os.makedirs(save_dir, exist_ok=True)
    
    # 1. Fetch Data
    raw_df = fetch_training_data(symbol=symbol, days=days)
    
    # 2. Engineer Features
    clean_df, feature_cols = calculate_features(raw_df)
    X = clean_df[feature_cols].values
    y = clean_df['target'].values.astype(int)

    # 3. Train / Validation Split (Time-Series Split 80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logger.info(f"📊 Training Set: {len(X_train)} samples | Test Set: {len(X_test)} samples | Features: {len(feature_cols)}")

    results = {}
    models = {}

    # --- A. XGBoost Classifier ---
    logger.info("🌲 Training XGBoost Classifier...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.03,
        objective='multi:softprob',
        eval_metric='mlogloss',
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(X_train_scaled, y_train)
    xgb_preds = xgb_model.predict(X_test_scaled)
    xgb_proba = xgb_model.predict_proba(X_test_scaled)
    models['xgboost'] = xgb_model
    results['xgboost'] = {
        'accuracy': float(accuracy_score(y_test, xgb_preds)),
        'f1_score': float(f1_score(y_test, xgb_preds, average='weighted', zero_division=0)),
        'log_loss': float(log_loss(y_test, xgb_proba))
    }
    logger.info(f"  ✓ XGBoost Accuracy: {results['xgboost']['accuracy']*100:.2f}% | F1: {results['xgboost']['f1_score']:.4f}")

    # --- B. LightGBM Classifier ---
    logger.info("⚡ Training LightGBM Classifier...")
    lgb_model = lgb.LGBMClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.03,
        random_state=42,
        verbose=-1,
        n_jobs=-1
    )
    lgb_model.fit(X_train_scaled, y_train)
    lgb_preds = lgb_model.predict(X_test_scaled)
    lgb_proba = lgb_model.predict_proba(X_test_scaled)
    models['lightgbm'] = lgb_model
    results['lightgbm'] = {
        'accuracy': float(accuracy_score(y_test, lgb_preds)),
        'f1_score': float(f1_score(y_test, lgb_preds, average='weighted', zero_division=0)),
        'log_loss': float(log_loss(y_test, lgb_proba))
    }
    logger.info(f"  ✓ LightGBM Accuracy: {results['lightgbm']['accuracy']*100:.2f}% | F1: {results['lightgbm']['f1_score']:.4f}")

    # --- C. CatBoost Classifier ---
    if HAS_CATBOOST:
        logger.info("🐱 Training CatBoost Classifier...")
        cat_model = CatBoostClassifier(
            iterations=150,
            depth=5,
            learning_rate=0.03,
            random_state=42,
            verbose=False
        )
        cat_model.fit(X_train_scaled, y_train)
        cat_preds = cat_model.predict(X_test_scaled)
        cat_proba = cat_model.predict_proba(X_test_scaled)
        models['catboost'] = cat_model
        results['catboost'] = {
            'accuracy': float(accuracy_score(y_test, cat_preds)),
            'f1_score': float(f1_score(y_test, cat_preds, average='weighted', zero_division=0)),
            'log_loss': float(log_loss(y_test, cat_proba))
        }
        logger.info(f"  ✓ CatBoost Accuracy: {results['catboost']['accuracy']*100:.2f}% | F1: {results['catboost']['f1_score']:.4f}")

    # --- D. Random Forest Classifier ---
    logger.info("🌳 Training Random Forest Classifier...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train_scaled, y_train)
    rf_preds = rf_model.predict(X_test_scaled)
    rf_proba = rf_model.predict_proba(X_test_scaled)
    models['random_forest'] = rf_model
    results['random_forest'] = {
        'accuracy': float(accuracy_score(y_test, rf_preds)),
        'f1_score': float(f1_score(y_test, rf_preds, average='weighted', zero_division=0)),
        'log_loss': float(log_loss(y_test, rf_proba))
    }
    logger.info(f"  ✓ RandomForest Accuracy: {results['random_forest']['accuracy']*100:.2f}% | F1: {results['random_forest']['f1_score']:.4f}")

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
    ensemble_loss = float(log_loss(y_test, ensemble_proba))

    results['ensemble'] = {
        'accuracy': ensemble_acc,
        'f1_score': ensemble_f1,
        'log_loss': ensemble_loss,
        'weights': weights
    }
    logger.info(f"🏆 TRI-MODEL ENSEMBLE Accuracy: {ensemble_acc*100:.2f}% | F1: {ensemble_f1:.4f} | LogLoss: {ensemble_loss:.4f}")

    # --- 4. Serialize Model Artifacts ---
    logger.info("\n💾 Saving Model Artifacts locally...")
    lgb_path = os.path.join(save_dir, "lightgbm_model.pkl")
    joblib.dump(lgb_model, lgb_path)

    rf_path = os.path.join(save_dir, "random_forest_model.pkl")
    joblib.dump(rf_model, rf_path)

    scaler_path = os.path.join(save_dir, "scaler.pkl")
    joblib.dump(scaler, scaler_path)

    xgb_path = os.path.join(save_dir, "xgboost_model.json")
    xgb_model.save_model(xgb_path)

    if HAS_CATBOOST:
        cat_path = os.path.join(save_dir, "catboost_model.cbm")
        cat_model.save_model(cat_path)

    # --- 5. Publish Artifacts to GCS Model Vault ---
    if upload_gcs and HAS_GCS:
        try:
            logger.info(f"☁️ Uploading model artifacts to gs://{gcs_bucket}/...")
            client = storage.Client()
            bucket = client.bucket(gcs_bucket)
            
            for file_name in ["lightgbm_model.pkl", "random_forest_model.pkl", "scaler.pkl", "xgboost_model.json"]:
                p = os.path.join(save_dir, file_name)
                if os.path.exists(p):
                    blob = bucket.blob(file_name)
                    blob.upload_from_filename(p)
                    logger.info(f"  ✓ Uploaded: gs://{gcs_bucket}/{file_name}")

            if HAS_CATBOOST and os.path.exists(os.path.join(save_dir, "catboost_model.cbm")):
                blob = bucket.blob("catboost_model.cbm")
                blob.upload_from_filename(os.path.join(save_dir, "catboost_model.cbm"))
                logger.info(f"  ✓ Uploaded: gs://{gcs_bucket}/catboost_model.cbm")

            results['gcs_uploaded'] = True
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
    parser = argparse.ArgumentParser(description="Train Tri-Model ML Ensemble on Real Market Data")
    parser.add_argument("--symbol", type=str, default="NIFTY", help="Symbol to train on (e.g. NIFTY, BANKNIFTY, RELIANCE)")
    parser.add_argument("--days", type=int, default=730, help="Historical training lookback in days")
    parser.add_argument("--upload-gcs", action="store_true", default=True, help="Upload models to GCS vault")
    args = parser.parse_args()

    res = train_tri_model_ensemble(symbol=args.symbol, days=args.days, upload_gcs=args.upload_gcs)
    print("\n=== Training Results ===")
    import json
    print(json.dumps(res, indent=2))
