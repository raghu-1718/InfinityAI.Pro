import pandas as pd
from google.cloud import bigquery, storage
import lightgbm as lgb
from catboost import CatBoostClassifier
import joblib

# 1. Pull the latest 30 days of tick data from BigQuery
bq_client = bigquery.Client()
query = """
    SELECT rsi_14, macd_crossover, vwap_distance, atr_volatility, signal_outcome 
    FROM `project-841b7f97-5ee3-4fbe-920.infinity_dataset.market_ticks_history`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
"""
df = bq_client.query(query).to_dataframe()

X = df[['rsi_14', 'macd_crossover', 'vwap_distance', 'atr_volatility']]
y = df['signal_outcome']

# 2. Retrain LightGBM
lgb_model = lgb.LGBMClassifier(n_estimators=100)
lgb_model.fit(X, y)
joblib.dump(lgb_model, '/tmp/lightgbm_model.pkl')

# 3. Retrain CatBoost
cat_model = CatBoostClassifier(iterations=100, verbose=0)
cat_model.fit(X, y)
cat_model.save_model('/tmp/catboost_model.cbm')

# 4. Upload fresh weights to Google Cloud Storage
storage_client = storage.Client()
bucket = storage_client.bucket('infinity-ai-models-vault')

bucket.blob('lightgbm_model.pkl').upload_from_filename('/tmp/lightgbm_model.pkl')
bucket.blob('catboost_model.cbm').upload_from_filename('/tmp/catboost_model.cbm')

print("✅ Retraining complete. New weights uploaded to GCS.")
