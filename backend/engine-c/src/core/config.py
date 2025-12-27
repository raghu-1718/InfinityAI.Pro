import os
from dotenv import load_dotenv

load_dotenv()


def require_env(var_name: str, example: str = ""):
    value = os.getenv(var_name)
    if value is None or value == "":
        msg = f"[FATAL] Required environment variable '{var_name}' is missing."
        if example:
            msg += f" Example: {example}"
        raise RuntimeError(msg)
    return value

class Config:
    DHAN_API_BASE = os.getenv("DHAN_API_BASE", "https://api.dhan.co/v2")
    DHAN_ACCESS_TOKEN = require_env("DHAN_ACCESS_TOKEN", "your-dhan-access-token")
    CLIENT_ID = require_env("DHAN_CLIENT_ID", "your-dhan-client-id")
    WEBSOCKET_URL = os.getenv("DHAN_WEBSOCKET_URL", "wss://stream.dhan.co")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
