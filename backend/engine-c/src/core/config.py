"""
Configuration for Engine-C
Per-user credentials stored in Firestore; platform defaults from environment
"""
import os
from dotenv import load_dotenv

load_dotenv()


def require_env(var_name: str, example: str = "", optional: bool = False):
    """Get environment variable with optional fallback"""
    value = os.getenv(var_name)
    if value is None or value == "":
        if optional:
            return ""
        msg = f"[FATAL] Required environment variable '{var_name}' is missing."
        if example:
            msg += f" Example: {example}"
        raise RuntimeError(msg)
    return value


class Config:
    """
    Platform-wide configuration
    
    NOTE: User-specific DhanHQ credentials are stored in Firestore.
    These environment variables are OPTIONAL platform defaults only.
    All trading operations use per-user credentials from Firestore via UserCredentialsManager.
    """
    DHAN_API_BASE = os.getenv("DHAN_API_BASE", "https://api.dhan.co/v2")
    WEBSOCKET_URL = os.getenv("DHAN_WEBSOCKET_URL", "wss://stream.dhan.co")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Platform defaults (optional - not used for trading)
    # All trading uses per-user Firestore credentials
    DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "")
    CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "")
    DHAN_API_KEY = os.getenv("DHAN_API_KEY", "")
    DHAN_API_SECRET = os.getenv("DHAN_API_SECRET", "")
