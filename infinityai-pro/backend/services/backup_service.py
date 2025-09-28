# services/backup_service.py
"""
Automated backup service for InfinityAI.Pro
Backs up ChromaDB, models, and trading data to cloud storage
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from services.cloud_storage_service import cloud_storage_service
from utils.logger import get_logger

logger = get_logger("backup_service")

class BackupService:
    """Automated backup service"""

    def __init__(self):
        self.running = False
        self.backup_interval_hours = 24  # Daily backups
        self.retention_days = 30  # Keep backups for 30 days
        self.stats = {
            "last_backup": None,
            "total_backups": 0,
            "failed_backups": 0,
            "bytes_backed_up": 0
        }

    async def start(self):
        """Start the backup service"""
        if self.running:
            return

        self.running = True
        logger.info("Starting automated backup service")

        # Run initial backup
        await self.perform_backup()

        # Schedule regular backups
        asyncio.create_task(self._backup_loop())

    async def stop(self):
        """Stop the backup service"""
        self.running = False
        logger.info("Backup service stopped")

    async def _backup_loop(self):
        """Main backup loop"""
        while self.running:
            try:
                # Wait for next backup interval
                await asyncio.sleep(self.backup_interval_hours * 3600)

                if self.running:  # Check again after sleep
                    await self.perform_backup()

            except Exception as e:
                logger.error(f"Error in backup loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry

    async def perform_backup(self) -> Dict[str, Any]:
        """Perform a complete backup"""
        start_time = datetime.now()
        logger.info("Starting automated backup")

        results = {
            "timestamp": start_time.isoformat(),
            "success": False,
            "components": {},
            "errors": []
        }

        try:
            # Initialize cloud storage
            await cloud_storage_service.initialize()

            # Backup ChromaDB
            chroma_result = await self._backup_chromadb()
            results["components"]["chromadb"] = chroma_result

            # Backup models
            models_result = await self._backup_models()
            results["components"]["models"] = models_result

            # Backup trading data
            trading_result = await self._backup_trading_data()
            results["components"]["trading_data"] = trading_result

            # Cleanup old backups
            cleanup_result = await self._cleanup_old_backups()
            results["components"]["cleanup"] = cleanup_result

            results["success"] = all([
                chroma_result.get("success", False),
                models_result.get("success", False),
                trading_result.get("success", False)
            ])

            # Update stats
            self.stats["last_backup"] = start_time.isoformat()
            self.stats["total_backups"] += 1

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Backup completed in {duration:.1f}s - Success: {results['success']}")

        except Exception as e:
            results["errors"].append(str(e))
            self.stats["failed_backups"] += 1
            logger.error(f"Backup failed: {e}")

        return results

    async def _backup_chromadb(self) -> Dict[str, Any]:
        """Backup ChromaDB database"""
        try:
            db_path = "chroma_db/chroma.sqlite3"

            if not os.path.exists(db_path):
                return {"success": False, "error": "ChromaDB database not found"}

            result = await cloud_storage_service.backup_database(db_path)

            if result:
                return {
                    "success": True,
                    "url": result,
                    "size_bytes": os.path.getsize(db_path)
                }
            else:
                return {"success": False, "error": "Backup upload failed"}

        except Exception as e:
            logger.error(f"ChromaDB backup error: {e}")
            return {"success": False, "error": str(e)}

    async def _backup_models(self) -> Dict[str, Any]:
        """Backup ML models"""
        try:
            models_dir = "models"

            if not os.path.exists(models_dir):
                return {"success": False, "error": "Models directory not found"}

            uploaded_models = await cloud_storage_service.backup_models(models_dir)

            return {
                "success": True,
                "uploaded_count": len(uploaded_models),
                "models": uploaded_models
            }

        except Exception as e:
            logger.error(f"Models backup error: {e}")
            return {"success": False, "error": str(e)}

    async def _backup_trading_data(self) -> Dict[str, Any]:
        """Backup trading data files"""
        try:
            data_dir = "data/backtest_5m"
            uploaded_files = []

            if not os.path.exists(data_dir):
                return {"success": False, "error": "Trading data directory not found"}

            for filename in os.listdir(data_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(data_dir, filename)
                    symbol = filename.replace('.csv', '')

                    result = await cloud_storage_service.upload_trading_data(
                        file_path, symbol, "backtest_5m"
                    )

                    if result:
                        uploaded_files.append({
                            "symbol": symbol,
                            "filename": filename,
                            "url": result
                        })

            return {
                "success": True,
                "uploaded_count": len(uploaded_files),
                "files": uploaded_files
            }

        except Exception as e:
            logger.error(f"Trading data backup error: {e}")
            return {"success": False, "error": str(e)}

    async def _cleanup_old_backups(self) -> Dict[str, Any]:
        """Clean up old backup files"""
        try:
            # This would need to be implemented in cloud_storage_service
            # For now, return placeholder
            deleted_count = await cloud_storage_service.cleanup_old_files(self.retention_days)

            return {
                "success": True,
                "deleted_count": deleted_count,
                "retention_days": self.retention_days
            }

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return {"success": False, "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Get backup service statistics"""
        return {
            "running": self.running,
            "backup_interval_hours": self.backup_interval_hours,
            "retention_days": self.retention_days,
            "stats": self.stats.copy()
        }

    async def manual_backup(self, components: List[str] = None) -> Dict[str, Any]:
        """Perform manual backup of specific components"""
        if components is None:
            components = ["chromadb", "models", "trading_data"]

        results = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "errors": []
        }

        try:
            await cloud_storage_service.initialize()

            if "chromadb" in components:
                results["components"]["chromadb"] = await self._backup_chromadb()

            if "models" in components:
                results["components"]["models"] = await self._backup_models()

            if "trading_data" in components:
                results["components"]["trading_data"] = await self._backup_trading_data()

            results["success"] = all([
                comp.get("success", False)
                for comp in results["components"].values()
            ])

        except Exception as e:
            results["errors"].append(str(e))
            results["success"] = False

        return results

# Global instance
backup_service = BackupService()