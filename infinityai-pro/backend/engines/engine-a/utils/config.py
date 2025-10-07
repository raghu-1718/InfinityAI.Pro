"""
Configuration management for Engine A
InfinityAI.Pro Trading Platform

Centralized configuration with environment variable support
and validation for all Engine A settings.
"""

import os
from typing import Optional, List
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Service Configuration
    SERVICE_NAME: str = "engine-a"
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
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 10
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_GROUP_ID: str = "engine-a"
    KAFKA_AUTO_OFFSET_RESET: str = "latest"
    
    # Dhan Broker Configuration
    DHAN_ACCESS_TOKEN: str = ""
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
        
    @field_validator("KAFKA_BOOTSTRAP_SERVERS")
    @classmethod
    def validate_kafka_servers(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("KAFKA_BOOTSTRAP_SERVERS must be a non-empty string")
        return v


@lru_cache()
def get_settings() -> Settings:
    env = os.getenv("INFINITYAI_ENV", "development").lower()
    return Settings()


def get_environment_info() -> dict:
    settings = get_settings()
    return {
        "service_name": settings.SERVICE_NAME,
        "service_version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "log_level": settings.LOG_LEVEL,
        "is_production": settings.ENVIRONMENT == "production",
    }
