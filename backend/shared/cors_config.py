"""
CORS Configuration with Environment-Gating for Production Safety

This module provides environment-aware CORS origin configuration
to prevent localhost URLs from leaking into production deployments.

Usage:
    from backend.shared.cors_config import ALLOWED_ORIGINS
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
"""

import os
from typing import List
import logging

logger = logging.getLogger(__name__)


def get_allowed_origins() -> List[str]:
    """
    Get allowed CORS origins based on environment.
    
    DEVELOPMENT: Allows localhost for local testing
    PRODUCTION: Only allows whitelisted production domains
    
    Returns:
        List of allowed origin URLs
    """
    
    environment = os.getenv("ENVIRONMENT", "production").lower()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "galvanic-pulsar-482815-h0")
    
    # Base production origins (ALWAYS included)
    production_origins = [
        "https://infinityai.pro",
        "https://www.infinityai.pro",
        "https://app.infinityai.pro",
        f"https://{project_id}.web.app",
        f"https://{project_id}.firebaseapp.com",
    ]
    
    # Development-only origins (NEVER in production)
    development_only = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ]
    
    if environment == "development":
        logger.info("🔓 CORS: Development mode - allowing localhost origins")
        return production_origins + development_only
    else:
        logger.info("🔒 CORS: Production mode - localhost origins BLOCKED")
        return production_origins


# Export for use in engines
ALLOWED_ORIGINS = get_allowed_origins()

# Log configuration on module import
logger.info(f"✅ CORS allowed origins: {ALLOWED_ORIGINS}")
