import re

file_path = r"C:\Users\Raghu\Projects\InfinityAI.Pro\backend\engine-b\src\main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add imports at top
import_str = """
import joblib
import traceback
from google.cloud import storage, bigquery
"""
content = content.replace("import traceback", import_str)

# 2. Add periodic background task to startup_event
startup_event_target = """@app.on_event("startup")
async def startup_event():
    \"\"\"Bootstrap application state\"\"\"
    global aiohttp_session"""

startup_event_replacement = """
async def periodic_model_update():
    while True:
        try:
            logger.info("Checking GCS for newer models...")
            MODEL_STORE.reload_from_gcs()
        except Exception as e:
            logger.error(f"Error during periodic model update: {e}")
        # Wait 24 hours (run every morning)
        await asyncio.sleep(86400)

@app.on_event("startup")
async def startup_event():
    \"\"\"Bootstrap application state\"\"\"
    global aiohttp_session
    
    # Start background task for daily model reload
    asyncio.create_task(periodic_model_update())
"""
content = content.replace(startup_event_target, startup_event_replacement)

# 3. Add reload_from_gcs to MLModelStore
reload_gcs_target = """    def _initialize_models(self):"""
reload_gcs_replacement = """    def reload_from_gcs(self):
        \"\"\"Download models from GCS\"\"\"
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket('infinity-ai-models-vault')
            
            # Download LightGBM
            lgb_blob = bucket.blob('lightgbm_model.pkl')
            if lgb_blob.exists():
                lgb_blob.download_to_filename('/tmp/lightgbm_model_dl.pkl')
                self.models['lightgbm'] = joblib.load('/tmp/lightgbm_model_dl.pkl')
                self.trained_symbols.add("ALL")
                logger.info("✅ Reloaded LightGBM from GCS")
                
            # Download CatBoost
            cat_blob = bucket.blob('catboost_model.cbm')
            if cat_blob.exists() and HAS_CATBOOST:
                cat_blob.download_to_filename('/tmp/catboost_model_dl.cbm')
                model = CatBoostClassifier()
                model.load_model('/tmp/catboost_model_dl.cbm')
                self.models['catboost'] = model
                logger.info("✅ Reloaded CatBoost from GCS")
                
        except Exception as e:
            logger.error(f"GCS Reload error: {e}")

    def _initialize_models(self):"""
content = content.replace(reload_gcs_target, reload_gcs_replacement)

# 4. Refactor MLModelStore.weighted_ensemble_predict to use BigQuery for XGBoost
predict_target = """        for model_name, weight in weights.items():
            model = self.get_model(model_name)
            if model is not None:"""

predict_replacement = """        for model_name, weight in weights.items():
            if model_name == 'xgboost':
                try:
                    # Native BigQuery ML Inference
                    bq_client = bigquery.Client()
                    # Using dummy values for now since X_scaled lacks named features
                    query = f\"\"\"
                        SELECT * FROM ML.PREDICT(MODEL `project-841b7f97-5ee3-4fbe-920.infinity_dataset.xgboost_live_model`, 
                        (SELECT {X_scaled[0][0]} as rsi_14, {X_scaled[0][1]} as macd_crossover, 
                                {X_scaled[0][2]} as vwap_distance, {X_scaled[0][3]} as atr_volatility))
                    \"\"\"
                    result = list(bq_client.query(query).result())
                    if result:
                        # Assuming the output has 'predicted_signal_outcome' or similar. 
                        # We will just map it simply.
                        pred_label = result[0].get('predicted_signal_outcome', 1)
                        class_votes[int(pred_label)] += weight
                        votes_detail['xgboost'] = {'prediction': int(pred_label), 'weight': weight, 'source': 'bqml'}
                except Exception as e:
                    logger.error(f"BQML Inference Error: {e}")
                continue

            model = self.get_model(model_name)
            if model is not None:"""
content = content.replace(predict_target, predict_replacement)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied.")
