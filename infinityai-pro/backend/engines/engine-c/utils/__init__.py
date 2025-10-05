"""
Utils package for Engine C
InfinityAI.Pro Trading Platform

Utilities and helper modules for trade execution engine including:
- Configuration management
- Logging setup
- Metrics collection
- Circuit breakers
- Exponential backoff
- Audit logging
- Encryption and secure vault
"""

from .config import get_settings, get_environment_info
from .logging_config import setup_logging, get_structured_logger, logging_context
from .metrics import MetricsCollector
from .circuit_breaker import CircuitBreaker, get_circuit_breaker
from .backoff import ExponentialBackoff, broker_api_backoff
from .audit import AuditLogger, AuditEventType, AuditSeverity
from .encryption import SecureVault, get_secret_manager, setup_vault_from_env

__version__ = "1.0.0"

__all__ = [
    # Configuration
    "get_settings",
    "get_environment_info",
    
    # Logging
    "setup_logging",
    "get_structured_logger", 
    "logging_context",
    
    # Metrics
    "MetricsCollector",
    
    # Circuit Breakers
    "CircuitBreaker",
    "get_circuit_breaker",
    
    # Backoff and Retry
    "ExponentialBackoff",
    "broker_api_backoff",
    
    # Audit Logging
    "AuditLogger",
    "AuditEventType",
    "AuditSeverity",
    
    # Encryption
    "SecureVault",
    "get_secret_manager",
    "setup_vault_from_env"
]