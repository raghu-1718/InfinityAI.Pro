"""
Configuration for Engine-C
Per-user credentials stored in Supabase; platform defaults from environment
"""
import os
from dotenv import load_dotenv

load_dotenv()


def require_env(var_name: str, example: str = "", optional: bool = False) -> str:
    """Get environment variable with optional fallback. For GOOGLE_CLOUD_PROJECT, provide a default for testing."""
    value = os.getenv(var_name)
    if value is None or value == "":
        if var_name == "GOOGLE_CLOUD_PROJECT":
            default = "dev-project"
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️ {var_name} not set; using default '{default}' for testing.")
            return default
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

    NOTE: User-specific DhanHQ credentials are stored in Supabase.
    These environment variables are OPTIONAL platform defaults only.
    All trading operations use per-user credentials from Supabase via UserCredentialsManager.
    """
    DHAN_API_BASE = os.getenv("DHAN_API_BASE", "https://api.dhan.co/v2")
    WEBSOCKET_URL = os.getenv("DHAN_WEBSOCKET_URL", "wss://stream.dhan.co")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Platform defaults (optional - not used for trading)
    # All trading uses per-user Supabase credentials
    DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "")
    CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "")
    DHAN_API_KEY = os.getenv("DHAN_API_KEY", "")
    DHAN_API_SECRET = os.getenv("DHAN_API_SECRET", "")
