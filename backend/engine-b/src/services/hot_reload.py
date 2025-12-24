"""
Background Model Hot-Reload Service
Periodically checks GCS for new models and reloads atomically
"""
import asyncio
import logging
from src.services.model_loader import fetch_latest_model
from src.services.model_registry import MODEL_REGISTRY

logger = logging.getLogger(__name__)

# Check every 5 minutes
CHECK_INTERVAL = 300


async def model_hot_reload_loop():
    """
    Background task that checks GCS for new models
    Reloads atomically without interrupting inference
    """
    logger.info("🔁 Model hot-reload service started")
    
    # Initial load
    try:
        model, version, updated = fetch_latest_model()
        MODEL_REGISTRY.update(model, version)
    except Exception as e:
        logger.error(f"❌ Initial model load failed: {e}")
        logger.warning("⚠️ Engine B starting without XGBoost model - will use fallback")
    
    # Periodic reload loop
    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL)
            
            logger.info(f"🔍 Hot-reload poll tick @ {asyncio.get_event_loop().time()}")
            
            model, version, updated = fetch_latest_model()
            
            # Check if version changed
            current_version = MODEL_REGISTRY.model_version
            
            if current_version != version:
                logger.info(f"🆕 New model detected: {version}")
                MODEL_REGISTRY.update(model, version)
                logger.info(f"✅ Model hot-reloaded successfully")
            else:
                logger.info(f"✓ Model up to date: {version}")
                
        except Exception as e:
            logger.error(f"⚠️ Hot-reload check failed: {e}")
            logger.exception("Full traceback:")
            # Don't crash - keep existing model
            continue


def get_model_for_inference():
    """
    Get current model for inference
    Returns: (model, version) or (None, None) if not loaded
    """
    model, version = MODEL_REGISTRY.get()
    
    if model is None:
        logger.warning("⚠️ No XGBoost model loaded - using fallback")
    
    return model, version
