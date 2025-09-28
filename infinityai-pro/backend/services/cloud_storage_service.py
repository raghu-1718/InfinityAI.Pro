# services/cloud_storage_service.py
"""
Cloud Storage Service for InfinityAI.Pro
Provides high-level interface for multi-cloud storage operations
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.storage import get_storage, MultiCloudStorage
from utils.config import CONFIG
from utils.logger import get_logger

logger = get_logger("cloud_storage_service")

class CloudStorageService:
    """High-level cloud storage service"""

    def __init__(self):
        self.storage: Optional[MultiCloudStorage] = None
        self.initialized = False
        self.stats = {
            "uploads": 0,
            "downloads": 0,
            "deletions": 0,
            "errors": 0,
            "total_bytes_uploaded": 0,
            "total_bytes_downloaded": 0
        }

    async def initialize(self) -> bool:
        """Initialize the cloud storage service"""
        try:
            if not self.initialized:
                self.storage = get_storage()
                self.initialized = True
                logger.info("✅ Cloud storage service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize cloud storage service: {e}")
            return False

    async def connect(self) -> bool:
        """Test connection to storage providers"""
        if not self.initialized:
            await self.initialize()

        try:
            health = await self.storage.health_check()
            logger.info(f"Storage health check: {health}")
            return health["providers"][CONFIG.STORAGE_PROVIDER]["status"] == "healthy"
        except Exception as e:
            logger.error(f"Storage connection test failed: {e}")
            return False

    async def upload_model(self, model_path: str, model_name: str) -> Optional[str]:
        """Upload ML model to cloud storage"""
        try:
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return None

            # Generate key for model storage
            key = f"models/{model_name}"

            # Upload file
            result = await self.storage.upload_file(model_path, key)
            self.stats["uploads"] += 1
            self.stats["total_bytes_uploaded"] += os.path.getsize(model_path)

            logger.info(f"Uploaded model {model_name} to cloud storage")
            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Model upload failed: {e}")
            return None

    async def download_model(self, model_name: str, local_path: str) -> bool:
        """Download ML model from cloud storage"""
        try:
            key = f"models/{model_name}"

            # Check if file exists
            if not await self.storage.file_exists(key):
                logger.warning(f"Model {model_name} not found in cloud storage")
                return False

            # Download file
            success = await self.storage.download_file(key, local_path)
            if success:
                self.stats["downloads"] += 1
                self.stats["total_bytes_downloaded"] += os.path.getsize(local_path)
                logger.info(f"Downloaded model {model_name} from cloud storage")
            else:
                self.stats["errors"] += 1

            return success

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Model download failed: {e}")
            return False

    async def upload_trading_data(self, data_path: str, symbol: str, data_type: str = "historical") -> Optional[str]:
        """Upload trading data to cloud storage"""
        try:
            if not os.path.exists(data_path):
                logger.error(f"Data file not found: {data_path}")
                return None

            # Generate key for data storage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"trading_data/{data_type}/{symbol}/{timestamp}_{os.path.basename(data_path)}"

            # Upload file
            result = await self.storage.upload_file(data_path, key)
            self.stats["uploads"] += 1
            self.stats["total_bytes_uploaded"] += os.path.getsize(data_path)

            logger.info(f"Uploaded trading data for {symbol} to cloud storage")
            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Trading data upload failed: {e}")
            return None

    async def upload_chart_image(self, image_path: str, symbol: str, analysis_id: str) -> Optional[str]:
        """Upload chart analysis image to cloud storage"""
        try:
            if not os.path.exists(image_path):
                logger.error(f"Chart image not found: {image_path}")
                return None

            # Generate key for chart storage
            key = f"charts/{symbol}/{analysis_id}_{os.path.basename(image_path)}"

            # Upload file
            result = await self.storage.upload_file(image_path, key)
            self.stats["uploads"] += 1
            self.stats["total_bytes_uploaded"] += os.path.getsize(image_path)

            logger.info(f"Uploaded chart for {symbol} to cloud storage")
            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Chart upload failed: {e}")
            return None

    async def get_model_url(self, model_name: str, expires: int = 3600) -> Optional[str]:
        """Get signed URL for model access"""
        try:
            key = f"models/{model_name}"
            if not await self.storage.file_exists(key):
                return None

            return await self.storage.get_file_url(key, expires)

        except Exception as e:
            logger.error(f"Failed to get model URL: {e}")
            return None

    async def cleanup_old_files(self, days_old: int = 30) -> int:
        """Clean up old files from cloud storage (placeholder - would need listing capability)"""
        # This would require implementing list_files functionality in storage providers
        # For now, return 0 as placeholder
        logger.info(f"Cleanup of files older than {days_old} days not yet implemented")
        return 0

    async def replicate_to_secondary(self, key: str) -> bool:
        """Replicate file to secondary storage provider for redundancy"""
        try:
            primary = CONFIG.STORAGE_PROVIDER
            secondary = "azure" if primary == "aws" else "aws"

            success = await self.storage.replicate_file(key, primary, secondary)
            if success:
                logger.info(f"Replicated {key} to secondary storage")
            return success

        except Exception as e:
            logger.error(f"Replication failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get storage service statistics"""
        return {
            "initialized": self.initialized,
            "primary_provider": CONFIG.STORAGE_PROVIDER,
            "stats": self.stats.copy(),
            "health": "healthy" if self.initialized else "not_initialized"
        }

    async def backup_database(self, db_path: str) -> Optional[str]:
        """Backup database to cloud storage"""
        try:
            if not os.path.exists(db_path):
                logger.error(f"Database file not found: {db_path}")
                return None

            # Generate backup key
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"backups/database/{timestamp}_chroma_backup.db"

            # Upload backup
            result = await self.storage.upload_file(db_path, key)
            self.stats["uploads"] += 1
            self.stats["total_bytes_uploaded"] += os.path.getsize(db_path)

            logger.info("Database backup uploaded to cloud storage")
            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Database backup failed: {e}")
            return None

    async def backup_models(self, models_dir: str) -> List[str]:
        """Backup all models to cloud storage"""
        uploaded = []
        try:
            if not os.path.exists(models_dir):
                logger.warning(f"Models directory not found: {models_dir}")
                return uploaded

            for filename in os.listdir(models_dir):
                if filename.endswith(('.pkl', '.h5', '.pt', '.onnx')):
                    model_path = os.path.join(models_dir, filename)
                    result = await self.upload_model(model_path, filename)
                    if result:
                        uploaded.append(filename)

            logger.info(f"Backed up {len(uploaded)} models to cloud storage")
            return uploaded

        except Exception as e:
            logger.error(f"Models backup failed: {e}")
            return uploaded

# Global instance
cloud_storage_service = CloudStorageService()