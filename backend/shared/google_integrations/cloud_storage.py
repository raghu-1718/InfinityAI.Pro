"""
InfinityAI.Pro - Google Cloud Storage Integration
==================================================
Cloud Storage for ML model persistence and trading history storage.
Uses official google-cloud-storage SDK.

Based on: https://github.com/googleapis/nodejs-storage (Python equivalent)
"""

import os
import json
import gzip
import pickle
import logging
from typing import Dict, Any, Optional, List, BinaryIO, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import io

# Google Cloud Storage
try:
    from google.cloud import storage
    HAS_GCS = True
except ImportError:
    HAS_GCS = False
    storage = None

logger = logging.getLogger("InfinityAI.CloudStorage")


@dataclass
class ModelMetadata:
    """Metadata for stored ML models."""
    model_name: str
    version: str
    model_type: str  # xgboost, lightgbm, catboost, sklearn
    symbol: Optional[str] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    training_date: datetime = field(default_factory=datetime.utcnow)
    features: List[str] = field(default_factory=list)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_name": self.model_name,
            "version": self.version,
            "model_type": self.model_type,
            "symbol": self.symbol,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "training_date": self.training_date.isoformat(),
            "features": self.features,
            "hyperparameters": self.hyperparameters
        }


@dataclass
class TradeRecord:
    """Record of a trade for history storage."""
    trade_id: str
    symbol: str
    signal: str  # BUY, SELL
    quantity: int
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: datetime = field(default_factory=datetime.utcnow)
    exit_time: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    status: str = "OPEN"  # OPEN, CLOSED, CANCELLED
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "signal": self.signal,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "model_used": self.model_used,
            "confidence": self.confidence,
            "stop_loss": self.stop_loss,
            "target_price": self.target_price,
            "status": self.status,
            "metadata": self.metadata
        }


class ModelStorage:
    """
    Cloud Storage integration for ML model persistence.

    Features:
    - Store and retrieve ML models (XGBoost, LightGBM, CatBoost, sklearn)
    - Version control for models
    - Model metadata and metrics storage
    - Compressed storage for efficiency
    - Local caching for performance
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        project_id: Optional[str] = None,
        models_prefix: str = "models/",
        local_cache_dir: str = "/tmp/infinityai_models"
    ):
        """
        Initialize model storage.

        Args:
            bucket_name: GCS bucket name
            project_id: Cloud project ID
            models_prefix: Prefix for model objects in bucket
            local_cache_dir: Local directory for model caching
        """
        self.bucket_name = bucket_name or os.getenv("GCS_MODELS_BUCKET", "infinityai-models")
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.models_prefix = models_prefix
        self.local_cache_dir = Path(local_cache_dir)

        self._client = None
        self._bucket = None
        self._initialized = False

        # Create local cache directory
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)

        if HAS_GCS:
            self._initialize()
        else:
            logger.warning("google-cloud-storage not installed. Using local storage only.")

    def _initialize(self):
        """Initialize GCS client."""
        try:
            self._client = storage.Client(project=self.project_id)
            self._bucket = self._client.bucket(self.bucket_name)

            # Create bucket if it doesn't exist
            if not self._bucket.exists():
                self._bucket = self._client.create_bucket(
                    self.bucket_name,
                    location="asia-south1"
                )
                logger.info(f"✅ Created GCS bucket: {self.bucket_name}")

            self._initialized = True
            logger.info(f"✅ Model storage initialized: gs://{self.bucket_name}")
        except Exception as e:
            logger.warning(f"⚠️ GCS initialization failed: {e}. Using local storage.")
            self._initialized = False

    def save_model(
        self,
        model: Any,
        metadata: ModelMetadata,
        compress: bool = True
    ) -> str:
        """
        Save an ML model to Cloud Storage.

        Args:
            model: The model object to save
            metadata: Model metadata
            compress: Whether to compress the model

        Returns:
            Storage path of the saved model
        """
        # Generate storage path
        model_path = f"{self.models_prefix}{metadata.model_name}/{metadata.version}/"
        model_file = f"{metadata.model_type}_model"

        if compress:
            model_file += ".pkl.gz"
        else:
            model_file += ".pkl"

        full_path = model_path + model_file

        # Serialize model
        model_bytes = pickle.dumps(model)

        if compress:
            model_bytes = gzip.compress(model_bytes)

        # Save to GCS
        if self._initialized and self._bucket:
            try:
                blob = self._bucket.blob(full_path)
                blob.upload_from_string(
                    model_bytes,
                    content_type="application/octet-stream"
                )

                # Save metadata
                metadata_blob = self._bucket.blob(model_path + "metadata.json")
                metadata_blob.upload_from_string(
                    json.dumps(metadata.to_dict()),
                    content_type="application/json"
                )

                logger.info(f"✅ Model saved to gs://{self.bucket_name}/{full_path}")
            except Exception as e:
                logger.error(f"❌ Failed to save model to GCS: {e}")

        # Also save locally as cache
        local_path = self.local_cache_dir / metadata.model_name / metadata.version
        local_path.mkdir(parents=True, exist_ok=True)

        with open(local_path / model_file, "wb") as f:
            f.write(model_bytes)

        with open(local_path / "metadata.json", "w") as f:
            json.dump(metadata.to_dict(), f)

        return f"gs://{self.bucket_name}/{full_path}" if self._initialized else str(local_path / model_file)

    def load_model(
        self,
        model_name: str,
        version: str = "latest",
        model_type: str = "xgboost"
    ) -> tuple[Any, Optional[ModelMetadata]]:
        """
        Load a model from Cloud Storage.

        Args:
            model_name: Name of the model
            version: Model version (or "latest")
            model_type: Type of model

        Returns:
            Tuple of (model, metadata)
        """
        if version == "latest":
            version = self._get_latest_version(model_name)
            if not version:
                raise ValueError(f"No versions found for model: {model_name}")

        # Try loading from GCS first
        if self._initialized and self._bucket:
            try:
                model_path = f"{self.models_prefix}{model_name}/{version}/"

                # Check for compressed model
                for ext in [".pkl.gz", ".pkl"]:
                    model_file = f"{model_type}_model{ext}"
                    blob = self._bucket.blob(model_path + model_file)

                    if blob.exists():
                        model_bytes = blob.download_as_bytes()

                        if ext == ".pkl.gz":
                            model_bytes = gzip.decompress(model_bytes)

                        model = pickle.loads(model_bytes)

                        # Load metadata
                        metadata = None
                        metadata_blob = self._bucket.blob(model_path + "metadata.json")
                        if metadata_blob.exists():
                            metadata_dict = json.loads(metadata_blob.download_as_string())
                            metadata = ModelMetadata(**metadata_dict)

                        logger.info(f"✅ Model loaded from GCS: {model_name}/{version}")
                        return model, metadata

            except Exception as e:
                logger.warning(f"⚠️ Failed to load from GCS: {e}. Trying local cache.")

        # Fallback to local cache
        local_path = self.local_cache_dir / model_name / version

        for ext in [".pkl.gz", ".pkl"]:
            model_file = local_path / f"{model_type}_model{ext}"

            if model_file.exists():
                with open(model_file, "rb") as f:
                    model_bytes = f.read()

                if ext == ".pkl.gz":
                    model_bytes = gzip.decompress(model_bytes)

                model = pickle.loads(model_bytes)

                # Load metadata
                metadata = None
                metadata_file = local_path / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        metadata_dict = json.load(f)
                    metadata = ModelMetadata(**metadata_dict)

                logger.info(f"✅ Model loaded from local cache: {model_name}/{version}")
                return model, metadata

        raise FileNotFoundError(f"Model not found: {model_name}/{version}")

    def _get_latest_version(self, model_name: str) -> Optional[str]:
        """Get the latest version of a model."""
        versions = self.list_versions(model_name)
        if versions:
            # Sort versions (assuming semantic versioning)
            versions.sort(reverse=True)
            return versions[0]
        return None

    def list_versions(self, model_name: str) -> List[str]:
        """List all versions of a model."""
        versions = []

        # Check GCS
        if self._initialized and self._bucket:
            try:
                prefix = f"{self.models_prefix}{model_name}/"
                blobs = self._bucket.list_blobs(prefix=prefix, delimiter="/")

                for page in blobs.pages:
                    for prefix in page.prefixes:
                        version = prefix.split("/")[-2]
                        if version:
                            versions.append(version)
            except Exception as e:
                logger.warning(f"⚠️ Failed to list GCS versions: {e}")

        # Also check local cache
        local_path = self.local_cache_dir / model_name
        if local_path.exists():
            for version_dir in local_path.iterdir():
                if version_dir.is_dir() and version_dir.name not in versions:
                    versions.append(version_dir.name)

        return versions

    def delete_model(self, model_name: str, version: str):
        """Delete a model version."""
        if self._initialized and self._bucket:
            try:
                prefix = f"{self.models_prefix}{model_name}/{version}/"
                blobs = self._bucket.list_blobs(prefix=prefix)
                for blob in blobs:
                    blob.delete()
                logger.info(f"✅ Deleted model from GCS: {model_name}/{version}")
            except Exception as e:
                logger.error(f"❌ Failed to delete from GCS: {e}")

        # Delete from local cache
        local_path = self.local_cache_dir / model_name / version
        if local_path.exists():
            import shutil
            shutil.rmtree(local_path)
            logger.info(f"✅ Deleted model from local cache: {model_name}/{version}")


class TradingHistoryStorage:
    """
    Cloud Storage for trading history persistence.

    Features:
    - Store and retrieve trade records
    - Daily/monthly aggregation
    - Performance analytics storage
    - Compressed JSON storage
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        project_id: Optional[str] = None,
        history_prefix: str = "trading_history/"
    ):
        """
        Initialize trading history storage.

        Args:
            bucket_name: GCS bucket name
            project_id: Cloud project ID
            history_prefix: Prefix for history objects
        """
        self.bucket_name = bucket_name or os.getenv("GCS_HISTORY_BUCKET", "infinityai-history")
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.history_prefix = history_prefix

        self._client = None
        self._bucket = None
        self._initialized = False

        if HAS_GCS:
            self._initialize()

    def _initialize(self):
        """Initialize GCS client."""
        try:
            self._client = storage.Client(project=self.project_id)
            self._bucket = self._client.bucket(self.bucket_name)

            if not self._bucket.exists():
                self._bucket = self._client.create_bucket(
                    self.bucket_name,
                    location="asia-south1"
                )

            self._initialized = True
            logger.info(f"✅ Trading history storage initialized: gs://{self.bucket_name}")
        except Exception as e:
            logger.warning(f"⚠️ GCS initialization failed: {e}")
            self._initialized = False

    def save_trade(self, trade: TradeRecord) -> bool:
        """
        Save a trade record.

        Args:
            trade: Trade record to save

        Returns:
            Success status
        """
        # Generate path based on date
        date_str = trade.entry_time.strftime("%Y/%m/%d")
        file_path = f"{self.history_prefix}{date_str}/{trade.trade_id}.json"

        trade_data = trade.to_dict()

        if self._initialized and self._bucket:
            try:
                blob = self._bucket.blob(file_path)
                blob.upload_from_string(
                    json.dumps(trade_data),
                    content_type="application/json"
                )
                logger.debug(f"Trade saved to GCS: {trade.trade_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to save trade: {e}")
                return False

        return False

    def get_trades_by_date(
        self,
        date: datetime,
        symbol: Optional[str] = None
    ) -> List[TradeRecord]:
        """
        Get trades for a specific date.

        Args:
            date: Date to query
            symbol: Optional symbol filter

        Returns:
            List of trade records
        """
        trades = []
        date_str = date.strftime("%Y/%m/%d")
        prefix = f"{self.history_prefix}{date_str}/"

        if self._initialized and self._bucket:
            try:
                blobs = self._bucket.list_blobs(prefix=prefix)

                for blob in blobs:
                    if blob.name.endswith(".json"):
                        data = json.loads(blob.download_as_string())

                        if symbol is None or data.get("symbol") == symbol:
                            trades.append(TradeRecord(**data))
            except Exception as e:
                logger.error(f"Failed to get trades: {e}")

        return trades

    def get_trades_by_range(
        self,
        start_date: datetime,
        end_date: datetime,
        symbol: Optional[str] = None
    ) -> List[TradeRecord]:
        """
        Get trades for a date range.

        Args:
            start_date: Start date
            end_date: End date
            symbol: Optional symbol filter

        Returns:
            List of trade records
        """
        trades = []
        current = start_date

        while current <= end_date:
            daily_trades = self.get_trades_by_date(current, symbol)
            trades.extend(daily_trades)
            current += timedelta(days=1)

        return trades

    def save_daily_summary(
        self,
        date: datetime,
        summary: Dict[str, Any]
    ):
        """
        Save daily trading summary.

        Args:
            date: Summary date
            summary: Summary data
        """
        date_str = date.strftime("%Y/%m/%d")
        file_path = f"{self.history_prefix}{date_str}/summary.json"

        if self._initialized and self._bucket:
            try:
                blob = self._bucket.blob(file_path)
                blob.upload_from_string(
                    json.dumps(summary),
                    content_type="application/json"
                )
                logger.info(f"Daily summary saved: {date_str}")
            except Exception as e:
                logger.error(f"Failed to save summary: {e}")

    def get_performance_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics for a period.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Performance metrics
        """
        trades = self.get_trades_by_range(start_date, end_date)

        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl": 0
            }

        closed_trades = [t for t in trades if t.status == "CLOSED" and t.pnl is not None]

        if not closed_trades:
            return {
                "total_trades": len(trades),
                "closed_trades": 0,
                "open_trades": len(trades),
                "win_rate": 0,
                "total_pnl": 0
            }

        wins = len([t for t in closed_trades if t.pnl > 0])
        total_pnl = sum(t.pnl for t in closed_trades)

        return {
            "total_trades": len(trades),
            "closed_trades": len(closed_trades),
            "open_trades": len(trades) - len(closed_trades),
            "wins": wins,
            "losses": len(closed_trades) - wins,
            "win_rate": wins / len(closed_trades) * 100,
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / len(closed_trades),
            "best_trade": max(t.pnl for t in closed_trades),
            "worst_trade": min(t.pnl for t in closed_trades)
        }
