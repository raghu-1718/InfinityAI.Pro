import os

def env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)

# Global, cross-workload configuration getters
class Settings:
    # Telegram
    TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN")

    # Dhan (global token or per-user via store/DB)
    DHAN_DEFAULT_CLIENT_ID = env("DHAN_CLIENT_ID")  # optional default
    DHAN_ACCESS_TOKEN = env("DHAN_ACCESS_TOKEN")    # rotate safely

    # Angel (optional)
    ANGEL_API_KEY = env("ANGEL_API_KEY")
    ANGEL_ACCESS_TOKEN = env("ANGEL_ACCESS_TOKEN")
    ANGEL_LOCAL_IP = env("ANGEL_LOCAL_IP")
    ANGEL_PUBLIC_IP = env("ANGEL_PUBLIC_IP")
    ANGEL_MAC_ADDRESS = env("ANGEL_MAC_ADDRESS")

    # Paths
    USER_STORE_PATH = env("USER_STORE_PATH", "config/user_store.json")
    LOGS_DIR = env("LOGS_DIR", "logs")

settings = Settings()
