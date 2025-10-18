import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DHAN_API_BASE = os.getenv("DHAN_API_BASE", "https://api.dhan.co/v2")
    DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
    CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
    WEBSOCKET_URL = os.getenv("DHAN_WEBSOCKET_URL", "wss://stream.dhan.co")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
