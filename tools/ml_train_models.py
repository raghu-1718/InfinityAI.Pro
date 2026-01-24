"""
ML Model Training Pipeline for InfinityAI.Pro
Trains XGBoost, LightGBM, CatBoost, and Random Forest models for Indian market symbols
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from google.cloud import storage
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import json

# Configuration
PROJECT_ID = 'galvanic-pulsar-482815-h0'
GCS_BUCKET = 'galvanic-pulsar-482815-h0-ml-models'
SYMBOLS = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX', 'GOLD', 'CRUDEOIL']
MODELS = ['xgboost', 'lightgbm', 'catboost', 'randomforest']

# Feature columns (excluding target and metadata)
FEATURE_COLS = [
    'sma_20', 'sma_50', 'ema_12', 'ema_26', 'macd', 'macd_signal', 'macd_diff',
    'rsi', 'bb_high', 'bb_mid', 'bb_low', 'bb_width', 'atr',
    'stoch_k', 'stoch_d', 'volume_sma', 'volume_ratio', 'returns',
    'log_returns', 'volatility_20'
]

TARGET_COL = 'Close'


def download_from_gcs(symbol):
    """Load training data from local files (already downloaded)"""
    print(f"\n[INFO] Loading data for {symbol}...")
    
    local_path = f'ml_data_local/{symbol}_3y_daily.csv'
    
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Data file not found: {local_path}")
    
    print(f"[OK] Loading from {local_path}")
    
    df = pd.read_csv(local_path)
    # Rename timestamp to Date for consistency
    if 'timestamp' in df.columns:
        df['Date'] = pd.to_datetime(df['timestamp'])
    return df


def prepare_features(df):
    """Prepare features and target for training"""
    print(f"[INFO] Preparing features...")
    
    # Drop rows with NaN values
    df_clean = df.dropna()
    
    # Ensure all feature columns exist
    missing_cols = [col for col in FEATURE_COLS if col not in df_clean.columns]
    if missing_cols:
        print(f"[WARN] Missing columns: {missing_cols}")
        available_features = [col for col in FEATURE_COLS if col in df_clean.columns]
    else:
        available_features = FEATURE_COLS
    
    X = df_clean[available_features]
    y = df_clean[TARGET_COL]
    
    print(f"[OK] Features shape: {X.shape}, Target shape: {y.shape}")
    return X, y, available_features


def train_xgboost(X_train, y_train, X_test, y_test):
    """Train XGBoost model"""
    print("[INFO] Training XGBoost model...")
    
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    metrics = calculate_metrics(y_test, y_pred)
    print(f"[OK] XGBoost - RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, R²: {metrics['r2']:.4f}")
    
    return model, metrics


def train_lightgbm(X_train, y_train, X_test, y_test):
    """Train LightGBM model"""
    print("[INFO] Training LightGBM model...")
    
    model = lgb.LGBMRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    metrics = calculate_metrics(y_test, y_pred)
    print(f"[OK] LightGBM - RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, R²: {metrics['r2']:.4f}")
    
    return model, metrics


def train_catboost(X_train, y_train, X_test, y_test):
    """Train CatBoost model"""
    print("[INFO] Training CatBoost model...")
    
    model = CatBoostRegressor(
        iterations=100,
        depth=6,
        learning_rate=0.1,
        random_state=42,
        verbose=False
    )
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    metrics = calculate_metrics(y_test, y_pred)
    print(f"[OK] CatBoost - RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, R²: {metrics['r2']:.4f}")
    
    return model, metrics


def train_randomforest(X_train, y_train, X_test, y_test):
    """Train Random Forest model"""
    print("[INFO] Training Random Forest model...")
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    metrics = calculate_metrics(y_test, y_pred)
    print(f"[OK] Random Forest - RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, R²: {metrics['r2']:.4f}")
    
    return model, metrics


def calculate_metrics(y_true, y_pred):
    """Calculate evaluation metrics"""
    return {
        'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
        'mae': mean_absolute_error(y_true, y_pred),
        'r2': r2_score(y_true, y_pred)
    }


def save_model_locally(model, symbol, model_type, metrics, feature_cols):
    """Save model and metadata locally"""
    os.makedirs('trained_models', exist_ok=True)
    
    # Save model
    model_filename = f'trained_models/{symbol}_{model_type}_model.pkl'
    joblib.dump(model, model_filename)
    
    # Save metadata
    metadata = {
        'symbol': symbol,
        'model_type': model_type,
        'trained_at': datetime.now().isoformat(),
        'metrics': metrics,
        'feature_columns': feature_cols,
        'model_file': model_filename
    }
    
    metadata_filename = f'trained_models/{symbol}_{model_type}_metadata.json'
    with open(metadata_filename, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"[OK] Saved {model_type} model to {model_filename}")
    return model_filename, metadata_filename


def upload_to_gcs(local_path, gcs_path):
    """Upload file to GCS using gcloud CLI"""
    import subprocess
    
    gcs_full_path = f'gs://{GCS_BUCKET}/{gcs_path}'
    cmd = ['gcloud', 'storage', 'cp', local_path, gcs_full_path]
    
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    
    if result.returncode == 0:
        print(f"[OK] Uploaded {local_path} to {gcs_full_path}")
    else:
        print(f"[WARN] Failed to upload {local_path}: {result.stderr}")



def train_all_models_for_symbol(symbol):
    """Train all model types for a given symbol"""
    print(f"\n{'='*60}")
    print(f"Training models for {symbol}")
    print(f"{'='*60}")
    
    # Download data
    df = download_from_gcs(symbol)
    
    # Prepare features
    X, y, feature_cols = prepare_features(df)
    
    # Split data (80/20 train/test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )
    
    print(f"[INFO] Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    results = {}
    
    # Train XGBoost
    xgb_model, xgb_metrics = train_xgboost(X_train, y_train, X_test, y_test)
    model_file, meta_file = save_model_locally(xgb_model, symbol, 'xgboost', xgb_metrics, feature_cols)
    upload_to_gcs(model_file, f'models/{symbol}/xgboost_model.pkl')
    upload_to_gcs(meta_file, f'models/{symbol}/xgboost_metadata.json')
    results['xgboost'] = xgb_metrics
    
    # Train LightGBM
    lgb_model, lgb_metrics = train_lightgbm(X_train, y_train, X_test, y_test)
    model_file, meta_file = save_model_locally(lgb_model, symbol, 'lightgbm', lgb_metrics, feature_cols)
    upload_to_gcs(model_file, f'models/{symbol}/lightgbm_model.pkl')
    upload_to_gcs(meta_file, f'models/{symbol}/lightgbm_metadata.json')
    results['lightgbm'] = lgb_metrics
    
    # Train CatBoost
    cat_model, cat_metrics = train_catboost(X_train, y_train, X_test, y_test)
    model_file, meta_file = save_model_locally(cat_model, symbol, 'catboost', cat_metrics, feature_cols)
    upload_to_gcs(model_file, f'models/{symbol}/catboost_model.pkl')
    upload_to_gcs(meta_file, f'models/{symbol}/catboost_metadata.json')
    results['catboost'] = cat_metrics
    
    # Train Random Forest
    rf_model, rf_metrics = train_randomforest(X_train, y_train, X_test, y_test)
    model_file, meta_file = save_model_locally(rf_model, symbol, 'randomforest', rf_metrics, feature_cols)
    upload_to_gcs(model_file, f'models/{symbol}/randomforest_model.pkl')
    upload_to_gcs(meta_file, f'models/{symbol}/randomforest_metadata.json')
    results['randomforest'] = rf_metrics
    
    return results


def main():
    """Main training pipeline"""
    print("="*60)
    print("ML Model Training Pipeline - InfinityAI.Pro")
    print("="*60)
    
    all_results = {}
    
    for symbol in SYMBOLS:
        try:
            results = train_all_models_for_symbol(symbol)
            all_results[symbol] = results
        except Exception as e:
            print(f"[ERROR] Failed to train models for {symbol}: {e}")
            all_results[symbol] = {'error': str(e)}
    
    # Save summary
    os.makedirs('trained_models', exist_ok=True)
    summary_file = 'trained_models/training_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    upload_to_gcs(summary_file, 'models/training_summary.json')
    
    print("\n" + "="*60)
    print("Training Complete!")
    print("="*60)
    print(f"\nSummary saved to {summary_file}")
    
    # Print best models
    print("\n[BEST MODELS BY SYMBOL]")
    for symbol, results in all_results.items():
        if 'error' not in results:
            best_model = max(results.items(), key=lambda x: x[1]['r2'])
            print(f"{symbol}: {best_model[0]} (R²: {best_model[1]['r2']:.4f})")


if __name__ == '__main__':
    main()
