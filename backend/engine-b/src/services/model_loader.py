"""
GCS Model Loader with Hot-Reload Support
Fetches latest XGBoost model from Cloud Storage
"""
import logging
from google.cloud import storage
from typing import Tuple, Any
from io import BytesIO

logger = logging.getLogger(__name__)

import os

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "dev-project")
if not os.getenv("GOOGLE_CLOUD_PROJECT"):
    # In non-production or testing environments, use a default bucket name.
    logger.warning("GOOGLE_CLOUD_PROJECT not set; using default project ID 'dev-project' for model bucket.")
    # BUCKET_NAME will be constructed with this fallback.


BUCKET_NAME = os.getenv("GCS_MODELS_BUCKET", "infinity-ai-models-vault")
MODEL_PREFIX = os.getenv("MODEL_PREFIX", "xgb/")


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
