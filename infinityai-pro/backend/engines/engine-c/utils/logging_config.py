"""
Logging configuration for Engine C
InfinityAI.Pro Trading Platform

Structured logging with JSON formatting, context management,
and integration with monitoring systems.
"""

import logging
import logging.config
import sys
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from contextlib import contextmanager
from threading import local
import traceback

# Thread-local storage for logging context
_context = local()


class ContextualFilter(logging.Filter):
    """Logging filter that adds contextual information to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add context from thread-local storage
        context = getattr(_context, 'context', {})
        for key, value in context.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        
        # Add default context
        if not hasattr(record, 'service'):
            record.service = 'engine-c'
        
        if not hasattr(record, 'component'):
            record.component = record.name.split('.')[-1]
        
        return True


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hostname = self._get_hostname()
    
    def _get_hostname(self) -> str:
        """Get hostname for logging"""
        import socket
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Create base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, 'service', 'engine-c'),
            "component": getattr(record, 'component', 'unknown'),
            "hostname": self.hostname,
            "process_id": record.process,
            "thread_id": record.thread,
            "thread_name": record.threadName,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'message',
                'service', 'component'
            }:
                try:
                    # Only include JSON-serializable values
                    json.dumps(value)
                    extra_fields[key] = value
                except (TypeError, ValueError):
                    extra_fields[key] = str(value)
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        return json.dumps(log_entry, ensure_ascii=False)


class PlainFormatter(logging.Formatter):
    """Plain text formatter for development"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Logging format ('json' or 'plain')
        log_file: Optional log file path
        enable_console: Whether to enable console logging
    """
    
    # Clear any existing handlers
    logging.getLogger().handlers.clear()
    
    # Create formatters
    if log_format.lower() == 'json':
        formatter = JSONFormatter()
    else:
        formatter = PlainFormatter()
    
    # Create contextual filter
    contextual_filter = ContextualFilter()
    
    # Setup handlers
    handlers = []
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(contextual_filter)
        handlers.append(console_handler)
    
    # File handler
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(contextual_filter)
            handlers.append(file_handler)
        except Exception as e:
            print(f"Failed to create file handler: {e}", file=sys.stderr)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        force=True
    )
    
    # Configure specific loggers
    configure_library_loggers()
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "log_format": log_format,
            "log_file": log_file,
            "enable_console": enable_console,
            "handlers_count": len(handlers)
        }
    )


def configure_library_loggers():
    """Configure logging levels for third-party libraries"""
    
    # Kafka logging
    logging.getLogger('kafka').setLevel(logging.WARNING)
    logging.getLogger('aiokafka').setLevel(logging.WARNING)
    
    # Database logging
    logging.getLogger('asyncpg').setLevel(logging.WARNING)
    logging.getLogger('aioredis').setLevel(logging.WARNING)
    
    # HTTP client logging
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    # FastAPI/Uvicorn logging
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    logging.getLogger('uvicorn.error').setLevel(logging.INFO)
    
    # Disable noisy loggers
    logging.getLogger('asyncio').setLevel(logging.WARNING)


@contextmanager
def logging_context(**context_data):
    """
    Context manager for adding contextual information to logs
    
    Usage:
        with logging_context(trade_id="12345", symbol="AAPL"):
            logger.info("Processing trade")  # Will include trade_id and symbol
    """
    if not hasattr(_context, 'context'):
        _context.context = {}
    
    # Store previous context
    previous_context = _context.context.copy()
    
    # Add new context
    _context.context.update(context_data)
    
    try:
        yield
    finally:
        # Restore previous context
        _context.context = previous_context


def add_logging_context(**context_data):
    """
    Add contextual information to the current thread's logging context
    
    Args:
        **context_data: Key-value pairs to add to logging context
    """
    if not hasattr(_context, 'context'):
        _context.context = {}
    
    _context.context.update(context_data)


def clear_logging_context():
    """Clear all contextual information from current thread"""
    if hasattr(_context, 'context'):
        _context.context.clear()


def get_logging_context() -> Dict[str, Any]:
    """Get current logging context"""
    return getattr(_context, 'context', {}).copy()


class StructuredLogger:
    """Wrapper for structured logging with convenience methods"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._name = name
    
    def _log_structured(self, level: int, message: str, **kwargs):
        """Log with structured data"""
        extra = {}
        
        # Separate logging-specific kwargs from extra data
        logging_kwargs = {'exc_info', 'stack_info', 'stacklevel'}
        for key in logging_kwargs:
            if key in kwargs:
                extra[key] = kwargs.pop(key)
        
        # Add remaining kwargs as extra fields
        if kwargs:
            extra.update(kwargs)
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data"""
        self._log_structured(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        self._log_structured(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        self._log_structured(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        self._log_structured(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data"""
        self._log_structured(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with structured data"""
        kwargs['exc_info'] = True
        self._log_structured(logging.ERROR, message, **kwargs)
    
    def trade_event(self, event_type: str, message: str, **kwargs):
        """Log trade-specific event"""
        self._log_structured(
            logging.INFO,
            message,
            event_type=event_type,
            category="trade",
            **kwargs
        )
    
    def risk_event(self, risk_type: str, message: str, **kwargs):
        """Log risk management event"""
        self._log_structured(
            logging.WARNING,
            message,
            risk_type=risk_type,
            category="risk",
            **kwargs
        )
    
    def circuit_breaker_event(self, breaker_name: str, state: str, message: str, **kwargs):
        """Log circuit breaker event"""
        self._log_structured(
            logging.WARNING,
            message,
            breaker_name=breaker_name,
            breaker_state=state,
            category="circuit_breaker",
            **kwargs
        )
    
    def broker_event(self, action: str, message: str, **kwargs):
        """Log broker interaction event"""
        self._log_structured(
            logging.INFO,
            message,
            broker_action=action,
            category="broker",
            **kwargs
        )


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)


def log_function_call(logger: logging.Logger):
    """Decorator to log function calls with parameters and execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            # Log function entry
            logger.debug(
                f"Calling {func.__name__}",
                extra={
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                    "action": "function_entry"
                }
            )
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful completion
                logger.debug(
                    f"Completed {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "action": "function_success"
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log exception
                logger.error(
                    f"Exception in {func.__name__}: {str(e)}",
                    extra={
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                        "action": "function_error"
                    },
                    exc_info=True
                )
                
                raise
        
        return wrapper
    return decorator


def log_async_function_call(logger: logging.Logger):
    """Decorator to log async function calls with parameters and execution time"""
    def decorator(func):
        import asyncio
        import functools
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            # Log function entry
            logger.debug(
                f"Calling async {func.__name__}",
                extra={
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                    "action": "async_function_entry"
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful completion
                logger.debug(
                    f"Completed async {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "action": "async_function_success"
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log exception
                logger.error(
                    f"Exception in async {func.__name__}: {str(e)}",
                    extra={
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                        "action": "async_function_error"
                    },
                    exc_info=True
                )
                
                raise
        
        return wrapper
    return decorator


# Export commonly used functions
__all__ = [
    "setup_logging",
    "logging_context",
    "add_logging_context",
    "clear_logging_context",
    "get_logging_context",
    "StructuredLogger",
    "get_structured_logger",
    "log_function_call",
    "log_async_function_call",
    "JSONFormatter",
    "PlainFormatter",
    "ContextualFilter"
]