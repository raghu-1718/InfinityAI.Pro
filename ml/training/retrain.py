import os
import sys
import logging
import tempfile
import hashlib
from datetime import datetime
import pandas as pd
import numpy as np
from google.cloud import bigquery, storage
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss, f1_score
from sklearn.ensemble import RandomForestClassifier
import lightgbm as lgb
from catboost import CatBoostClassifier
import xgboost as xgb
import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("InfinityAI.RetrainingPipeline")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
BUCKET_NAME = "infinity-ai-models-vault"
TMP_DIR = tempfile.gettempdir()

def compute_hashes(filepath: str):
    """Compute MD5 (hex and base64) and SHA256 of a local file."""
    import base64
    md5_obj = hashlib.md5()
    sha256_obj = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            md5_obj.update(chunk)
            sha256_obj.update(chunk)
    md5_hex = md5_obj.hexdigest()
    md5_b64 = base64.b64encode(md5_obj.digest()).decode("utf-8")
    sha256_hex = sha256_obj.hexdigest()
    return md5_hex, md5_b64, sha256_hex

# 1. Pull live ticks streamed by Engine C from market_data.live_ticks
logger.info("📡 Ingesting live tick dataset from BigQuery (market_data.live_ticks)...")
bq_client = bigquery.Client(project=PROJECT_ID)

query_live = f"""
    SELECT 
        SAFE_CAST(JSON_VALUE(data, '$.rsi_14') AS FLOAT64) AS rsi_14,
        SAFE_CAST(JSON_VALUE(data, '$.macd_crossover') AS FLOAT64) AS macd_crossover,
        SAFE_CAST(JSON_VALUE(data, '$.vwap_distance') AS FLOAT64) AS vwap_distance,
        SAFE_CAST(JSON_VALUE(data, '$.atr_volatility') AS FLOAT64) AS atr_volatility,
        IF(SAFE_CAST(JSON_VALUE(data, '$.change_pct') AS FLOAT64) > 0, 1, 0) AS signal_outcome
    FROM `{PROJECT_ID}.market_data.live_ticks`
    WHERE JSON_VALUE(data, '$.rsi_14') IS NOT NULL
      AND publish_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    ORDER BY publish_time DESC
    LIMIT 50000
"""

df_live = pd.DataFrame()
try:
    df_live = bq_client.query(query_live).to_dataframe()
    logger.info(f"✅ Ingested {len(df_live):,} live market ticks from market_data.live_ticks")
except Exception as e:
    logger.warning(f"Notice querying live_ticks: {e}")

# 2. Augment with historical tick baseline from infinity_dataset.market_ticks_history
logger.info("📡 Ingesting historical ticks archive (infinity_dataset.market_ticks_history)...")
query_hist = f"""
    SELECT 
        rsi_14, 
        macd_crossover, 
        vwap_distance, 
        atr_volatility, 
        signal_outcome 
    FROM `{PROJECT_ID}.infinity_dataset.market_ticks_history`
    WHERE signal_outcome IS NOT NULL
    ORDER BY timestamp DESC
    LIMIT 50000
"""

df_hist = pd.DataFrame()
try:
    df_hist = bq_client.query(query_hist).to_dataframe()
    logger.info(f"✅ Ingested {len(df_hist):,} historical records from market_ticks_history")
except Exception as e:
    logger.warning(f"Notice querying market_ticks_history: {e}")

# 3. Combine datasets
if not df_live.empty and not df_hist.empty:
    df = pd.concat([df_live, df_hist], ignore_index=True)
elif not df_live.empty:
    df = df_live
else:
    df = df_hist

df = df.dropna()
logger.info(f"📊 Combined Training Corpus: {len(df):,} valid samples with feature complete vectors")

feature_cols = ['rsi_14', 'macd_crossover', 'vwap_distance', 'atr_volatility']
X = np.asarray(df[feature_cols].astype(float))
y = np.asarray(df['signal_outcome'].astype(int))

# 80/20 Stratified Train/Validation Split for out-of-sample metrics
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
logger.info(f"📐 Train Samples: {len(X_train):,} | Out-of-Sample Validation Samples: {len(X_val):,}")

# Standard scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
scaler_path = os.path.join(TMP_DIR, 'scaler.pkl')
joblib.dump(scaler, scaler_path)

# 4. Retrain LightGBM
logger.info("🌲 Retraining LightGBM Classifier...")
lgb_model = lgb.LGBMClassifier(n_estimators=100, max_depth=6, random_state=42, verbose=-1)
lgb_model.fit(X_train_scaled, y_train)
lgb_preds = lgb_model.predict(X_val_scaled)
lgb_proba = lgb_model.predict_proba(X_val_scaled)
lgb_acc = accuracy_score(y_val, lgb_preds)
lgb_loss = log_loss(y_val, lgb_proba)
logger.info(f"   -> LightGBM Val Accuracy: {lgb_acc:.4f} | Log Loss: {lgb_loss:.4f} | F1: {f1_score(y_val, lgb_preds, average='weighted'):.4f}")
lgb_path = os.path.join(TMP_DIR, 'lightgbm_model.pkl')
joblib.dump(lgb_model, lgb_path)

# 5. Retrain CatBoost
logger.info("🐱 Retraining CatBoost Classifier...")
cat_model = CatBoostClassifier(iterations=100, depth=6, verbose=0, random_seed=42)
cat_model.fit(X_train_scaled, y_train)
cat_preds = cat_model.predict(X_val_scaled)
cat_proba = cat_model.predict_proba(X_val_scaled)
cat_acc = accuracy_score(y_val, cat_preds)
cat_loss = log_loss(y_val, cat_proba)
logger.info(f"   -> CatBoost Val Accuracy: {cat_acc:.4f} | Log Loss: {cat_loss:.4f} | F1: {f1_score(y_val, cat_preds, average='weighted'):.4f}")
cat_path = os.path.join(TMP_DIR, 'catboost_model.cbm')
cat_model.save_model(cat_path)

# 6. Retrain XGBoost (40% Weight Driver)
logger.info("🚀 Retraining XGBoost Classifier (xgboost_model.json)...")
xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.05, random_state=42)
xgb_model.fit(X_train_scaled, y_train)
xgb_preds = xgb_model.predict(X_val_scaled)
xgb_proba = xgb_model.predict_proba(X_val_scaled)
xgb_acc = accuracy_score(y_val, xgb_preds)
xgb_loss = log_loss(y_val, xgb_proba)
logger.info(f"   -> XGBoost Val Accuracy: {xgb_acc:.4f} | Log Loss: {xgb_loss:.4f} | F1: {f1_score(y_val, xgb_preds, average='weighted'):.4f}")
xgb_path = os.path.join(TMP_DIR, 'xgboost_model.json')
xgb_model.save_model(xgb_path)

# 7. Retrain Random Forest (15% Weight Driver)
logger.info("🌳 Retraining Random Forest Classifier...")
rf_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
rf_model.fit(X_train_scaled, y_train)
rf_preds = rf_model.predict(X_val_scaled)
rf_proba = rf_model.predict_proba(X_val_scaled)
rf_acc = accuracy_score(y_val, rf_preds)
rf_loss = log_loss(y_val, rf_proba)
logger.info(f"   -> Random Forest Val Accuracy: {rf_acc:.4f} | Log Loss: {rf_loss:.4f} | F1: {f1_score(y_val, rf_preds, average='weighted'):.4f}")
rf_path = os.path.join(TMP_DIR, 'random_forest_model.pkl')
joblib.dump(rf_model, rf_path)

# 8. Blended Ensemble Evaluation
ens_proba = (xgb_proba * 0.40) + (lgb_proba * 0.30) + (cat_proba * 0.20) + (rf_proba * 0.10)
ens_preds = np.argmax(ens_proba, axis=1)
ens_acc = accuracy_score(y_val, ens_preds)
ens_loss = log_loss(y_val, ens_proba)
logger.info(f"🏆 TRI-MODEL + RF ENSEMBLE OUT-OF-SAMPLE VALIDATION ACCURACY: {ens_acc:.4f} | Log Loss: {ens_loss:.4f}")

# 9. Verify Hashes & Upload fresh weights to Google Cloud Storage Vault
logger.info(f"☁️ Uploading fresh institutional weights to gs://{BUCKET_NAME}/...")
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

date_str = datetime.utcnow().strftime("%Y%m%d")

artifacts = [
    ('lightgbm_model.pkl', lgb_path),
    ('catboost_model.cbm', cat_path),
    ('xgboost_model.json', xgb_path),
    ('random_forest_model.pkl', rf_path),
    ('scaler.pkl', scaler_path)
]

print("\n" + "=" * 90)
print(f"{'ARTIFACT':<25} | {'SIZE (BYTES)':<12} | {'MD5 (HEX)':<32} | {'MD5 (B64)':<24}")
print("-" * 90)

for gcs_name, local_path in artifacts:
    md5_hex, md5_b64, sha256_hex = compute_hashes(local_path)
    size = os.path.getsize(local_path)
    print(f"{gcs_name:<25} | {size:<12,} | {md5_hex:<32} | {md5_b64:<24}")

    # Root latest model
    blob_root = bucket.blob(gcs_name)
    blob_root.upload_from_filename(local_path)
    # Dated archive
    blob_archive = bucket.blob(f"retrained/{date_str}/{gcs_name}")
    blob_archive.upload_from_filename(local_path)
    logger.info(f"   -> Uploaded: gs://{BUCKET_NAME}/{gcs_name} (Size: {size:,} bytes | MD5: {md5_b64})")

print("=" * 90 + "\n")

logger.info("✅ Institutional Tri-Model MLOps Retraining successfully completed!")
