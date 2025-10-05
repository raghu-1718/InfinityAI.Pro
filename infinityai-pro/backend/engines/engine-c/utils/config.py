"""
Configuration management for Engine C
InfinityAI.Pro Trading Platform

Centralized configuration with environment variable support
and validation for all Engine C settings.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Service Configuration
    SERVICE_NAME: str = "engine-c"
    SERVICE_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # FastAPI Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 1
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://infinityai:securepassword@localhost:5432/infinityai_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_TIMEOUT: int = 30
    
    # TimescaleDB Configuration
    TIMESCALE_URL: str = "postgresql://infinityai:securepassword@localhost:5432/timeseries_db"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 10
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SCHEMA_REGISTRY_URL: str = "http://localhost:8081"
    KAFKA_GROUP_ID: str = "engine-c-execution"
    KAFKA_AUTO_OFFSET_RESET: str = "latest"
    KAFKA_BATCH_SIZE: int = 16384
    KAFKA_MAX_REQUEST_SIZE: int = 1048576
    
    # Topic Names
    SIGNALS_TOPIC: str = "infinityai.signals"
    MARKET_DATA_TOPIC: str = "infinityai.market_data"
    TRADES_TOPIC: str = "infinityai.trades"
    EXECUTION_EVENTS_TOPIC: str = "infinityai.execution_events"
    
    # Dhan Broker Configuration
    DHAN_BASE_URL: str = "https://api.dhan.co"
    DHAN_ACCESS_TOKEN: str = ""
    DHAN_CLIENT_ID: str = ""
    DHAN_TIMEOUT: int = 30
    DHAN_MAX_RETRIES: int = 5
    
    # Security Configuration
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Circuit Breaker Configuration
    BROKER_CIRCUIT_BREAKER_THRESHOLD: int = 5
    BROKER_CIRCUIT_BREAKER_TIMEOUT: int = 60
    RISK_CIRCUIT_BREAKER_THRESHOLD: int = 3
    RISK_CIRCUIT_BREAKER_TIMEOUT: int = 30
    
    # Risk Management Configuration
    DEFAULT_DAILY_MAX_LOSS: float = 10000.0
    DEFAULT_POSITION_LIMIT: float = 100000.0
    DEFAULT_MAX_POSITION_SIZE_PERCENT: float = 20.0
    DEFAULT_SYMBOL_EXPOSURE_LIMIT: float = 10.0
    DEFAULT_MARGIN_RATIO: float = 0.2
    
    # Retry and Backoff Configuration
    MAX_RETRIES: int = 5
    BASE_DELAY: float = 1.0
    MAX_DELAY: float = 30.0
    BACKOFF_MULTIPLIER: float = 2.0
    
    # Monitoring Configuration
    METRICS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    JAEGER_ENABLED: bool = True
    JAEGER_ENDPOINT: str = "http://localhost:14268/api/traces"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # Account Configuration
    DEFAULT_ACCOUNT_ID: str = "account_1"
    DEFAULT_STRATEGY_ID: str = "strategy_1"
    
    # Performance Configuration
    BATCH_PROCESSING_SIZE: int = 100
    CONCURRENT_TRADES_LIMIT: int = 10
    SIGNAL_PROCESSING_TIMEOUT: int = 5
    
    # Validation Configuration
    ENABLE_PRE_TRADE_VALIDATION: bool = True
    ENABLE_KILL_SWITCHES: bool = True
    ENABLE_CIRCUIT_BREAKERS: bool = True
    ENABLE_POSITION_LIMITS: bool = True
    ENABLE_EXPOSURE_LIMITS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @validator("KAFKA_BOOTSTRAP_SERVERS")
    def validate_kafka_servers(cls, v):
        """Validate Kafka bootstrap servers format"""
        if not v or not isinstance(v, str):
            raise ValueError("KAFKA_BOOTSTRAP_SERVERS must be a non-empty string")
        
        servers = v.split(",")
        for server in servers:
            if ":" not in server.strip():
                raise ValueError(f"Invalid Kafka server format: {server}")
        
        return v
    
    @validator("DATABASE_URL", "TIMESCALE_URL", "REDIS_URL")
    def validate_database_urls(cls, v):
        """Validate database connection URLs"""
        if not v or not isinstance(v, str):
            raise ValueError("Database URL must be a non-empty string")
        
        if not v.startswith(("postgresql://", "redis://")):
            raise ValueError("Invalid database URL format")
        
        return v
    
    @validator("DHAN_ACCESS_TOKEN")
    def validate_dhan_token(cls, v):
        """Validate Dhan access token (can be empty for development)"""
        if not isinstance(v, str):
            raise ValueError("DHAN_ACCESS_TOKEN must be a string")
        
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate logging level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        
        return v.upper()
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment setting"""
        valid_environments = ["development", "staging", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(f"ENVIRONMENT must be one of: {valid_environments}")
        
        return v.lower()
    
    @validator("DEFAULT_DAILY_MAX_LOSS", "DEFAULT_POSITION_LIMIT")
    def validate_positive_numbers(cls, v):
        """Validate positive numbers for financial limits"""
        if v <= 0:
            raise ValueError("Financial limits must be positive numbers")
        
        return v
    
    @validator("DEFAULT_MAX_POSITION_SIZE_PERCENT", "DEFAULT_SYMBOL_EXPOSURE_LIMIT")
    def validate_percentages(cls, v):
        """Validate percentage values"""
        if not (0 < v <= 100):
            raise ValueError("Percentage values must be between 0 and 100")
        
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == "development"
    
    @property
    def kafka_servers_list(self) -> List[str]:
        """Get Kafka servers as a list"""
        return [server.strip() for server in self.KAFKA_BOOTSTRAP_SERVERS.split(",")]
    
    @property
    def database_config(self) -> dict:
        """Get database connection configuration"""
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "timeout": self.DATABASE_TIMEOUT
        }
    
    @property
    def redis_config(self) -> dict:
        """Get Redis connection configuration"""
        config = {
            "url": self.REDIS_URL,
            "max_connections": self.REDIS_MAX_CONNECTIONS
        }
        
        if self.REDIS_PASSWORD:
            config["password"] = self.REDIS_PASSWORD
        
        return config
    
    @property
    def kafka_config(self) -> dict:
        """Get Kafka configuration"""
        return {
            "bootstrap_servers": self.kafka_servers_list,
            "group_id": self.KAFKA_GROUP_ID,
            "auto_offset_reset": self.KAFKA_AUTO_OFFSET_RESET,
            "batch_size": self.KAFKA_BATCH_SIZE,
            "max_request_size": self.KAFKA_MAX_REQUEST_SIZE
        }
    
    @property
    def dhan_config(self) -> dict:
        """Get Dhan broker configuration"""
        return {
            "base_url": self.DHAN_BASE_URL,
            "access_token": self.DHAN_ACCESS_TOKEN,
            "client_id": self.DHAN_CLIENT_ID,
            "timeout": self.DHAN_TIMEOUT,
            "max_retries": self.DHAN_MAX_RETRIES
        }
    
    @property
    def circuit_breaker_config(self) -> dict:
        """Get circuit breaker configuration"""
        return {
            "broker": {
                "failure_threshold": self.BROKER_CIRCUIT_BREAKER_THRESHOLD,
                "recovery_timeout": self.BROKER_CIRCUIT_BREAKER_TIMEOUT
            },
            "risk": {
                "failure_threshold": self.RISK_CIRCUIT_BREAKER_THRESHOLD,
                "recovery_timeout": self.RISK_CIRCUIT_BREAKER_TIMEOUT
            }
        }
    
    @property
    def risk_limits_config(self) -> dict:
        """Get default risk limits configuration"""
        return {
            "daily_max_loss": self.DEFAULT_DAILY_MAX_LOSS,
            "position_limit": self.DEFAULT_POSITION_LIMIT,
            "max_position_size_percent": self.DEFAULT_MAX_POSITION_SIZE_PERCENT,
            "symbol_exposure_limit": self.DEFAULT_SYMBOL_EXPOSURE_LIMIT,
            "margin_ratio": self.DEFAULT_MARGIN_RATIO
        }
    
    @property
    def retry_config(self) -> dict:
        """Get retry and backoff configuration"""
        return {
            "max_retries": self.MAX_RETRIES,
            "base_delay": self.BASE_DELAY,
            "max_delay": self.MAX_DELAY,
            "backoff_multiplier": self.BACKOFF_MULTIPLIER
        }
    
    def get_topic_config(self) -> dict:
        """Get Kafka topic configuration"""
        return {
            "signals": self.SIGNALS_TOPIC,
            "market_data": self.MARKET_DATA_TOPIC,
            "trades": self.TRADES_TOPIC,
            "execution_events": self.EXECUTION_EVENTS_TOPIC
        }


class DevelopmentSettings(Settings):
    """Development environment settings"""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # Use test database for development
    DATABASE_URL: str = "postgresql://infinityai:securepassword@localhost:5432/infinityai_test_db"
    
    # Relaxed limits for development
    DEFAULT_DAILY_MAX_LOSS: float = 1000.0
    DEFAULT_POSITION_LIMIT: float = 10000.0
    
    # Shorter timeouts for faster feedback
    DHAN_TIMEOUT: int = 10
    SIGNAL_PROCESSING_TIMEOUT: int = 2


class ProductionSettings(Settings):
    """Production environment settings"""
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Stricter circuit breaker settings
    BROKER_CIRCUIT_BREAKER_THRESHOLD: int = 3
    BROKER_CIRCUIT_BREAKER_TIMEOUT: int = 120
    
    # Conservative risk limits
    DEFAULT_MAX_POSITION_SIZE_PERCENT: float = 10.0
    DEFAULT_SYMBOL_EXPOSURE_LIMIT: float = 5.0
    
    # Longer timeouts for stability
    DHAN_TIMEOUT: int = 60
    DATABASE_TIMEOUT: int = 60


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    Environment variable INFINITYAI_ENV determines the settings class to use.
    """
    env = os.getenv("INFINITYAI_ENV", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "development":
        return DevelopmentSettings()
    else:
        return Settings()


def get_environment_info() -> dict:
    """Get environment information for debugging"""
    settings = get_settings()
    
    return {
        "service_name": settings.SERVICE_NAME,
        "service_version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "log_level": settings.LOG_LEVEL,
        "is_production": settings.is_production,
        "is_development": settings.is_development,
        "kafka_servers": len(settings.kafka_servers_list),
        "database_configured": bool(settings.DATABASE_URL),
        "redis_configured": bool(settings.REDIS_URL),
        "dhan_configured": bool(settings.DHAN_ACCESS_TOKEN),
        "monitoring_enabled": settings.METRICS_ENABLED
    }


# Export commonly used settings
__all__ = [
    "Settings",
    "DevelopmentSettings", 
    "ProductionSettings",
    "get_settings",
    "get_environment_info"
]