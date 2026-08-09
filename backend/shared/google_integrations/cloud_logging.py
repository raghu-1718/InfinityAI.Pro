"""
InfinityAI.Pro - Google Cloud Logging Integration
==================================================
Structured logging for trading signals, ML predictions, and system events.
Uses official google-cloud-logging SDK for centralized log management.

Based on: https://github.com/googleapis/python-logging
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from functools import wraps
import asyncio
import time

# Google Cloud Logging
try:
    from google.cloud import logging as cloud_logging
    from google.cloud.logging_v2 import StructLog
    HAS_CLOUD_LOGGING = True
except ImportError:
    HAS_CLOUD_LOGGING = False
    cloud_logging = None

logger = logging.getLogger("InfinityAI.CloudLogging")


class LogLevel(Enum):
    """Log severity levels aligned with Cloud Logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TradingEventType(Enum):
    """Types of trading events for structured logging."""
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_EXECUTED = "signal_executed"
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    RISK_ALERT = "risk_alert"
    ML_PREDICTION = "ml_prediction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    MARKET_DATA = "market_data"
    PORTFOLIO_UPDATE = "portfolio_update"
    ERROR = "error"
    SYSTEM = "system"


@dataclass
class TradingLogEntry:
    """Structured log entry for trading events."""
    event_type: TradingEventType
    symbol: Optional[str] = None
    signal: Optional[str] = None
    confidence: Optional[float] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    order_id: Optional[str] = None
    risk_level: Optional[str] = None
    model_name: Optional[str] = None
    prediction: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        data = {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
        }

        # Add optional fields if present
        if self.symbol:
            data["symbol"] = self.symbol
        if self.signal:
            data["signal"] = self.signal
        if self.confidence is not None:
            data["confidence"] = self.confidence
        if self.price is not None:
            data["price"] = self.price
        if self.quantity is not None:
            data["quantity"] = self.quantity
        if self.order_id:
            data["order_id"] = self.order_id
        if self.risk_level:
            data["risk_level"] = self.risk_level
        if self.model_name:
            data["model_name"] = self.model_name
        if self.prediction:
            data["prediction"] = self.prediction
        if self.latency_ms is not None:
            data["latency_ms"] = self.latency_ms
        if self.metadata:
            data["metadata"] = self.metadata

        return data


class TradingLogger:
    """
    Cloud Logging integration for InfinityAI.Pro trading platform.

    Features:
    - Structured logging for trading events
    - ML prediction logging with metrics
    - Trade execution audit trail
    - Performance metrics (latency, throughput)
    - SEBI compliance logging
    - Integration with Cloud Monitoring
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        log_name: str = "infinityai-trading",
        enable_cloud_logging: bool = True,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the trading logger.

        Args:
            project_id: Cloud project ID
            log_name: Name for the Cloud Logging log
            enable_cloud_logging: Whether to enable Cloud Logging
            labels: Default labels to add to all log entries
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.log_name = log_name
        self.enable_cloud_logging = enable_cloud_logging and HAS_CLOUD_LOGGING
        self.labels = labels or {}

        # Add default labels
        self.labels.update({
            "service": "infinityai-pro",
            "environment": os.getenv("ENVIRONMENT", "production"),
            "version": os.getenv("APP_VERSION", "3.6")
        })

        self._client = None
        self._cloud_logger = None
        self._local_logger = logging.getLogger("InfinityAI.Trading")

        self._initialize()

    def _initialize(self):
        """Initialize Cloud Logging client."""
        if self.enable_cloud_logging:
            try:
                self._client = cloud_logging.Client(project=self.project_id)
                self._cloud_logger = self._client.logger(self.log_name)

                # Also setup Python logging integration
                self._client.setup_logging(log_level=logging.INFO)

                logger.info(f"✅ Cloud Logging initialized: {self.log_name}")
            except Exception as e:
                logger.warning(f"⚠️ Cloud Logging initialization failed: {e}")
                self.enable_cloud_logging = False
        else:
            logger.info("📝 Using local logging (Cloud Logging disabled)")

    def log_signal(
        self,
        symbol: str,
        signal: str,
        confidence: float,
        model_name: str = "ensemble",
        risk_level: str = "MEDIUM",
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        target_price: Optional[float] = None,
        latency_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a trading signal generation event.

        Args:
            symbol: Stock symbol
            signal: Signal type (BUY/SELL/HOLD)
            confidence: Signal confidence (0-100)
            model_name: ML model that generated the signal
            risk_level: Risk assessment level
            entry_price: Suggested entry price
            stop_loss: Suggested stop loss
            target_price: Suggested target price
            latency_ms: Signal generation latency
            metadata: Additional metadata
        """
        entry = TradingLogEntry(
            event_type=TradingEventType.SIGNAL_GENERATED,
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            model_name=model_name,
            risk_level=risk_level,
            price=entry_price,
            latency_ms=latency_ms,
            metadata={
                **(metadata or {}),
                "stop_loss": stop_loss,
                "target_price": target_price
            }
        )

        self._log(entry, LogLevel.INFO)

    def log_order(
        self,
        symbol: str,
        order_id: str,
        event_type: TradingEventType,
        signal: str,
        quantity: int,
        price: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log an order-related event.

        Args:
            symbol: Stock symbol
            order_id: Broker order ID
            event_type: Type of order event
            signal: BUY/SELL
            quantity: Number of shares
            price: Order price
            metadata: Additional metadata
        """
        entry = TradingLogEntry(
            event_type=event_type,
            symbol=symbol,
            order_id=order_id,
            signal=signal,
            quantity=quantity,
            price=price,
            metadata=metadata or {}
        )

        self._log(entry, LogLevel.INFO)

    def log_ml_prediction(
        self,
        model_name: str,
        symbol: str,
        prediction: Dict[str, Any],
        latency_ms: float,
        features_used: Optional[List[str]] = None,
        model_version: Optional[str] = None
    ):
        """
        Log an ML model prediction.

        Args:
            model_name: Name of the ML model
            symbol: Stock symbol
            prediction: Prediction results
            latency_ms: Inference latency
            features_used: List of features used
            model_version: Model version string
        """
        entry = TradingLogEntry(
            event_type=TradingEventType.ML_PREDICTION,
            symbol=symbol,
            model_name=model_name,
            prediction=prediction,
            latency_ms=latency_ms,
            metadata={
                "features_used": features_used or [],
                "model_version": model_version or "latest"
            }
        )

        self._log(entry, LogLevel.INFO)

    def log_risk_alert(
        self,
        symbol: str,
        risk_level: str,
        alert_type: str,
        message: str,
        current_value: Optional[float] = None,
        threshold: Optional[float] = None
    ):
        """
        Log a risk alert.

        Args:
            symbol: Stock symbol
            risk_level: Alert severity
            alert_type: Type of risk alert
            message: Alert message
            current_value: Current metric value
            threshold: Threshold that was breached
        """
        entry = TradingLogEntry(
            event_type=TradingEventType.RISK_ALERT,
            symbol=symbol,
            risk_level=risk_level,
            metadata={
                "alert_type": alert_type,
                "message": message,
                "current_value": current_value,
                "threshold": threshold
            }
        )

        level = LogLevel.WARNING if risk_level in ["MEDIUM", "HIGH"] else LogLevel.ERROR
        self._log(entry, level)

    def log_sentiment(
        self,
        symbol: str,
        sentiment: str,
        score: float,
        source: str = "news",
        key_factors: Optional[List[str]] = None
    ):
        """
        Log sentiment analysis results.

        Args:
            symbol: Stock symbol
            sentiment: Sentiment label (BULLISH/BEARISH/NEUTRAL)
            score: Sentiment score (-1 to 1)
            source: Data source (news, social, etc.)
            key_factors: Key factors affecting sentiment
        """
        entry = TradingLogEntry(
            event_type=TradingEventType.SENTIMENT_ANALYSIS,
            symbol=symbol,
            prediction={"sentiment": sentiment, "score": score},
            metadata={
                "source": source,
                "key_factors": key_factors or []
            }
        )

        self._log(entry, LogLevel.INFO)

    def log_error(
        self,
        error_type: str,
        message: str,
        symbol: Optional[str] = None,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log an error event.

        Args:
            error_type: Type of error
            message: Error message
            symbol: Related stock symbol (if applicable)
            stack_trace: Stack trace
            metadata: Additional context
        """
        entry = TradingLogEntry(
            event_type=TradingEventType.ERROR,
            symbol=symbol,
            metadata={
                "error_type": error_type,
                "message": message,
                "stack_trace": stack_trace,
                **(metadata or {})
            }
        )

        self._log(entry, LogLevel.ERROR)

    def _log(self, entry: TradingLogEntry, level: LogLevel):
        """
        Internal method to log an entry.

        Args:
            entry: Log entry to record
            level: Log severity level
        """
        log_data = entry.to_dict()
        log_data["labels"] = self.labels

        # Log to Cloud Logging if available
        if self.enable_cloud_logging and self._cloud_logger:
            try:
                severity = level.value
                self._cloud_logger.log_struct(
                    log_data,
                    severity=severity,
                    labels=self.labels
                )
            except Exception as e:
                self._local_logger.warning(f"Cloud logging failed: {e}")

        # Always log locally as backup
        log_message = json.dumps(log_data, default=str)
        if level == LogLevel.DEBUG:
            self._local_logger.debug(log_message)
        elif level == LogLevel.INFO:
            self._local_logger.info(log_message)
        elif level == LogLevel.WARNING:
            self._local_logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self._local_logger.error(log_message)
        elif level == LogLevel.CRITICAL:
            self._local_logger.critical(log_message)


def log_execution_time(logger_instance: Optional[TradingLogger] = None):
    """
    Decorator to log function execution time.

    Args:
        logger_instance: TradingLogger instance to use
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                latency_ms = (time.perf_counter() - start_time) * 1000

                if logger_instance:
                    logger_instance._log(
                        TradingLogEntry(
                            event_type=TradingEventType.SYSTEM,
                            latency_ms=latency_ms,
                            metadata={
                                "function": func.__name__,
                                "success": True
                            }
                        ),
                        LogLevel.DEBUG
                    )

                return result
            except Exception as e:
                latency_ms = (time.perf_counter() - start_time) * 1000

                if logger_instance:
                    logger_instance.log_error(
                        error_type="function_error",
                        message=str(e),
                        metadata={
                            "function": func.__name__,
                            "latency_ms": latency_ms
                        }
                    )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                latency_ms = (time.perf_counter() - start_time) * 1000

                if logger_instance:
                    logger_instance._log(
                        TradingLogEntry(
                            event_type=TradingEventType.SYSTEM,
                            latency_ms=latency_ms,
                            metadata={
                                "function": func.__name__,
                                "success": True
                            }
                        ),
                        LogLevel.DEBUG
                    )

                return result
            except Exception as e:
                latency_ms = (time.perf_counter() - start_time) * 1000

                if logger_instance:
                    logger_instance.log_error(
                        error_type="function_error",
                        message=str(e),
                        metadata={
                            "function": func.__name__,
                            "latency_ms": latency_ms
                        }
                    )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
