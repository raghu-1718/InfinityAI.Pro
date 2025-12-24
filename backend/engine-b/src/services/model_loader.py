"""
GCS Model Loader with Hot-Reload Support
Fetches latest XGBoost model from Cloud Storage
"""
import logging
from google.cloud import storage
from typing import Tuple, Any
from io import BytesIO

logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = "gen-lang-client-0779271931-ml-models"
MODEL_PREFIX = "xgb/"


def fetch_latest_model() -> Tuple[Any, str, Any]:
    """
    Fetch latest XGBoost model from GCS
    
    Returns:
        (model, version, updated_timestamp)
    """
    try:
        import xgboost as xgb
        
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        
        # List all models in prefix
        blobs = list(bucket.list_blobs(prefix=MODEL_PREFIX))
        
        logger.info(f"📂 GCS objects found in {MODEL_PREFIX}: {[b.name for b in blobs[:10]]}")
        
        if not blobs:
            raise FileNotFoundError(f"No models found in gs://{BUCKET_NAME}/{MODEL_PREFIX}")
        
        # Get latest by update time
        latest_blob = sorted(blobs, key=lambda b: b.updated, reverse=True)[0]
        
        logger.info(f"📥 Downloading model: {latest_blob.name}")
        
        # Download model bytes
        model_bytes = latest_blob.download_as_bytes()
        
        # Load XGBoost model
        booster = xgb.Booster()
        booster.load_model(BytesIO(model_bytes))
        
        version = latest_blob.name
        updated = latest_blob.updated
        
        logger.info(f"✅ Model loaded: {version} (updated: {updated})")
        
        return booster, version, updated
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch model from GCS: {e}")
        raise


def fetch_specific_model(version: str) -> Any:
    """
    Fetch a specific model version from GCS
    Used for rollback scenarios
    """
    try:
        import xgboost as xgb
        
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(version)
        
        if not blob.exists():
            raise FileNotFoundError(f"Model version not found: {version}")
        
        model_bytes = blob.download_as_bytes()
        booster = xgb.Booster()
        booster.load_model(BytesIO(model_bytes))
        
        logger.info(f"✅ Loaded specific model: {version}")
        return booster
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch model {version}: {e}")
        raise
