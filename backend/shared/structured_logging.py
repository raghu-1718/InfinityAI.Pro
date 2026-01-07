"""
Structured Logging Module for InfinityAI.Pro
=============================================

Provides production-grade structured logging with trace ID propagation,
context preservation, and Cloud Logging integration.

Project: galvanic-pulsar-482815-h0
Usage:
    from shared.structured_logging import get_logger, set_trace_context

    logger = get_logger(__name__)
    set_trace_context(trace_id="abc123", user_id="user456")
    logger.info("Trading signal received", signal="BUY", confidence=0.92)
"""

import json
import os
import sys
import logging
import uuid
from typing import Any, Dict, Optional
from datetime import datetime
from contextvars import ContextVar

# Context variables for correlation tracking
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
service_name_var: ContextVar[Optional[str]] = ContextVar("service_name", default=None)

# Global service name (set on module initialization)
_SERVICE_NAME = os.getenv("SERVICE_NAME", "infinityai-service")
_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "galvanic-pulsar-482815-h0")
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")


def set_trace_context(
    trace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    service_name: Optional[str] = None
) -> None:
    """
    Set correlation IDs for request tracing.

    Args:
        trace_id: Global trace ID for end-to-end tracking
        user_id: User ID associated with the request
        request_id: Unique request ID
        service_name: Service name (defaults to SERVICE_NAME env var)
    """
    if trace_id:
        trace_id_var.set(trace_id)
    if user_id:
        user_id_var.set(user_id)
    if request_id:
        request_id_var.set(request_id)
    if service_name:
        service_name_var.set(service_name)


def get_trace_context() -> Dict[str, Optional[str]]:
    """Get current trace context."""
    return {
        "trace_id": trace_id_var.get(),
        "user_id": user_id_var.get(),
        "request_id": request_id_var.get(),
        "service_name": service_name_var.get() or _SERVICE_NAME
    }


def clear_trace_context() -> None:
    """Clear all context variables (useful for testing)."""
    trace_id_var.set(None)
    user_id_var.set(None)
    request_id_var.set(None)
    service_name_var.set(None)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs compatible with
    Google Cloud Logging.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": service_name_var.get() or _SERVICE_NAME,
            "project_id": _PROJECT_ID,
            "environment": _ENVIRONMENT,
        }

        # Add trace context
        trace_id = trace_id_var.get()
        if trace_id:
            log_entry["trace_id"] = trace_id
            # Google Cloud format for integration
            log_entry["logging.googleapis.com/trace"] = f"projects/{_PROJECT_ID}/traces/{trace_id}"

        if user_id := user_id_var.get():
            log_entry["user_id"] = user_id

        if request_id := request_id_var.get():
            log_entry["request_id"] = request_id

        # Add custom fields from extra dict
        if hasattr(record, "custom_fields"):
            log_entry.update(record.custom_fields)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }

        # Add source location
        log_entry["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName
        }

        return json.dumps(log_entry)


class StructuredLogger(logging.LoggerAdapter):
    """
    Custom logger adapter that supports structured logging with custom fields.

    Usage:
        logger = get_logger(__name__)
        logger.info("Order placed", symbol="NIFTY50", quantity=100, price=20500.0)
    """

    def process(
        self,
        msg: str,
        kwargs: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """Process log message and extract custom fields."""
        custom_fields = {}

        # Extract custom fields from kwargs
        for key in list(kwargs.keys()):
            if key not in ("exc_info", "stack_info", "stacklevel", "extra"):
                custom_fields[key] = kwargs.pop(key)

        # Add custom fields to extra
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        kwargs["extra"]["custom_fields"] = custom_fields
        return msg, kwargs

    def info(self, msg: str, **kwargs):
        """Log info level with custom fields."""
        self.logger.info(msg, **kwargs)

    def debug(self, msg: str, **kwargs):
        """Log debug level with custom fields."""
        self.logger.debug(msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        """Log warning level with custom fields."""
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs):
        """Log error level with custom fields."""
        self.logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        """Log critical level with custom fields."""
        self.logger.critical(msg, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        StructuredLogger instance configured for structured logging
    """
    logger = logging.getLogger(name)

    # Configure if not already configured
    if not logger.handlers:
        # Set level
        log_level = os.getenv("LOG_LEVEL", "INFO")
        logger.setLevel(getattr(logging, log_level))

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level))

        # Set structured formatter
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False

    # Return adapter for custom fields support
    return StructuredLogger(logger, {})


class TraceContextFilter(logging.Filter):
    """Logging filter that adds trace context to all records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add trace context to record."""
        record.trace_id = trace_id_var.get() or ""
        record.user_id = user_id_var.get() or ""
        record.request_id = request_id_var.get() or ""
        return True


# Example usage and initialization
if __name__ == "__main__":
    # Initialize logging
    os.environ["SERVICE_NAME"] = "engine-a"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["ENVIRONMENT"] = "development"

    # Get logger
    logger = get_logger(__name__)

    # Set trace context
    set_trace_context(
        trace_id="trace-" + str(uuid.uuid4())[:8],
        user_id="user-123",
        request_id="req-" + str(uuid.uuid4())[:8]
    )

    # Log with custom fields
    print("=== Structured Logging Example ===\n")

    logger.info("Application started", version="1.0.0", region="us-central1")

    logger.debug(
        "Processing trade signal",
        symbol="NIFTY50",
        signal="BUY",
        confidence=0.92,
        timestamp="2026-01-06T12:00:00Z"
    )

    logger.warning(
        "High volatility detected",
        symbol="BANKNIFTY",
        volatility_pct=8.5,
        threshold_pct=5.0
    )

    try:
        # Simulate error
        1 / 0
    except ZeroDivisionError as e:
        logger.error(
            "Failed to calculate signal confidence",
            symbol="FINNIFTY",
            operation="divide",
            exc_info=True
        )

    print("\n✅ Structured logging framework ready for production")

    # Print trace context
    context = get_trace_context()
    print(f"\nTrace Context: {json.dumps(context, indent=2)}")
