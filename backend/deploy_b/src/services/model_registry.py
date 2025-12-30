"""
Model Registry with Thread-Safe Hot-Reload Support
Enables zero-downtime model updates in Engine B
"""
import threading
from datetime import datetime
from typing import Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Thread-safe registry for XGBoost models
    Supports atomic model swapping for hot-reload
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self.model: Optional[Any] = None
        self.model_version: Optional[str] = None
        self.loaded_at: Optional[datetime] = None
        self.load_count: int = 0
    
    def update(self, model: Any, version: str):
        """
        Atomically update the model
        Thread-safe for concurrent inference requests
        """
        with self._lock:
            old_version = self.model_version
            self.model = model
            self.model_version = version
            self.loaded_at = datetime.utcnow()
            self.load_count += 1
            
            if old_version:
                logger.info(f"🔁 Model hot-reloaded: {old_version} → {version}")
            else:
                logger.info(f"✅ Initial model loaded: {version}")
    
    def get(self) -> Tuple[Optional[Any], Optional[str]]:
        """
        Get current model (thread-safe)
        Returns: (model, version)
        """
        with self._lock:
            return self.model, self.model_version
    
    def get_metadata(self) -> dict:
        """Get model metadata for health checks"""
        with self._lock:
            return {
                "model_version": self.model_version,
                "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
                "load_count": self.load_count,
                "is_loaded": self.model is not None
            }


# Global singleton instance
MODEL_REGISTRY = ModelRegistry()
