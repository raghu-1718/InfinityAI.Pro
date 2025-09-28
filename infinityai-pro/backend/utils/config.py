# config.py

from dataclasses import dataclass, field
from typing import List, Dict
import os

@dataclass
class Config:
    CAPITAL: float = 11000.0
    RISK_PER_TRADE_PCT: float = 0.03
    MAX_DAILY_LOSS_PCT: float = 0.10          # stop trading after 10% loss
    MAX_DAILY_PROFIT_PCT: float = 0.25          # Target 25% profit today
    MAX_CONSECUTIVE_LOSSES: int = 3            # max losses in a row before cooldown
    COOLDOWN_AFTER_LOSSES_SEC: int = 300       # 5 minutes cooldown after consecutive losses
    CYCLE_SECONDS: int = 15                     # scan frequency

    # Scoring weights
    WEIGHT_ML: float = 0.60
    WEIGHT_RULE: float = 0.30
    WEIGHT_VOL: float = 0.10

    # Minimum score to consider a trade
    MIN_TRADE_SCORE: float = 0.45
    TRADE_LOG_CSV: str = "trade_logs/trades.csv"

    SYMBOLS: List[str] = field(default_factory=lambda: [
        # Prioritize MCX commodities for extended trading hours
        "MCX_GOLD_MINI", "MCX_SILVER_MINI", "MCX_CRUDE_MINI", "MCX_NG_MINI",
        # NSE indices as backup
        "NIFTY", "BANKNIFTY", "NIFTY_MIDCAP", "NIFTY_NEXT50", "NIFTY_FIN",
        "SENSEX", "BSE_MIDCAP", "BSE_SMALLCAP",
        "GIFTNIFTY",
        # Crypto trading pairs (CoinSwitch PRO)
        "BTCINR", "ETHINR", "BNBINR", "ADAINR", "SOLINR", "DOTINR",
        "MATICINR", "LINKINR", "AVAXINR", "LTCINR", "XRPINR", "DOGEINR"
    ])

    LOT_SIZE: Dict[str,int] = field(default_factory=lambda: {"NIFTY":50, "BANKNIFTY":25, "MCX_GOLD_MINI":100})
    MIN_OPTION_PREMIUM: float = 50.0
    TP_MULTIPLIER: float = 1.5
    MODEL_PATH: str = "models/lightgbm_small.pkl"
    BACKTEST_DATA_PATH: str = "backend/data/backtest_5m/"  # expects CSVs per symbol
    PAPER_MODE: bool = False  # ⚠️ LIVE TRADING ENABLED

    BROKER: dict = field(default_factory=lambda: {
        "provider":"DHAN",
        "client_id":"1101302170",
        "client_secret":"0c7d1fd6-53d0-41e3-9d71-f6b08077e874",
        "data_api_key":"afbecc8d",
        "data_api_secret":"0c7d1fd6-53d0-41e3-9d71-f6b08077e874",
        "access_token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NTkwNDQ0NjcsImlhdCI6MTc1ODk1ODA2NywidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vYXBpLmluZmluaXR5YWkucHJvL2RoYW4vdG9rZW4iLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.lsyGB43zvpPrHqUjlpHkgW7wko03P64NzRN-02NO-XNL-nKMyOT7d52SBZwricIEswv5IetVrZw7GBTvRtjSQg"
    })

    COINSWITCH: dict = field(default_factory=lambda: {
        "enabled": True,
        "api_key": os.getenv("COINSWITCH_API_KEY", ""),
        "api_secret": os.getenv("COINSWITCH_API_SECRET", ""),
        "base_url": "https://api-trading.coinswitch.co",
        "crypto_symbols": ["BTCINR", "ETHINR", "BNBINR", "ADAINR", "SOLINR", "DOTINR", "MATICINR"]
    })

    TRADINGVIEW: dict = field(default_factory=lambda: {"api_key": None, "enabled": True})  # TradingView integration
    PERPLEXITY: dict = field(default_factory=lambda: {"api_key": os.getenv("PERPLEXITY_API_KEY", ""), "enabled": True})  # Perplexity for market intelligence
    OPENAI: dict = field(default_factory=lambda: {"api_key": os.getenv("OPENAI_API_KEY", ""), "model": "gpt-3.5-turbo", "enabled": True})  # OpenAI for strategy narration

    COMMISSION_PER_TRADE: float = 20.0
    SLIPPAGE_PTS: float = 0.5
    RANDOM_SEED: int = 42

    # Multi-Cloud AI Configuration (Azure Primary, AWS Secondary)
    # Azure AI (Primary provider - GPU & AI)
    AZURE_AI_BASE_URL: str = os.getenv("AZURE_AI_BASE_URL", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_KEY: str = os.getenv("AZURE_OPENAI_KEY", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    AZURE_SPEECH_ENDPOINT: str = os.getenv("AZURE_SPEECH_ENDPOINT", "")
    AZURE_SPEECH_KEY: str = os.getenv("AZURE_SPEECH_KEY", "")
    AZURE_VISION_ENDPOINT: str = os.getenv("AZURE_VISION_ENDPOINT", "")
    AZURE_VISION_KEY: str = os.getenv("AZURE_VISION_KEY", "")
    AZURE_TEXT_ANALYTICS_ENDPOINT: str = os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT", "")
    AZURE_TEXT_ANALYTICS_KEY: str = os.getenv("AZURE_TEXT_ANALYTICS_KEY", "")
    AZURE_ML_ENDPOINT: str = os.getenv("AZURE_ML_ENDPOINT", "")
    AZURE_ML_KEY: str = os.getenv("AZURE_ML_KEY", "")

    # AWS AI (Secondary provider - GPU & AI)
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "infinityai-models")
    AWS_BEDROCK_MODEL_ID: str = os.getenv("AWS_BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")
    AWS_SAGEMAKER_ENDPOINT: str = os.getenv("AWS_SAGEMAKER_ENDPOINT", "")
    AWS_SAGEMAKER_SD_ENDPOINT: str = os.getenv("AWS_SAGEMAKER_SD_ENDPOINT", "")
    AWS_FRAUD_DETECTOR_ID: str = os.getenv("AWS_FRAUD_DETECTOR_ID", "")

    # Hugging Face (Local AI models)
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_MODEL_CACHE: str = os.getenv("HUGGINGFACE_MODEL_CACHE", "/tmp/huggingface")

    # Cloud Storage Configuration
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "aws")  # aws, azure
    AZURE_STORAGE_ACCOUNT: str = os.getenv("AZURE_STORAGE_ACCOUNT", "")
    AZURE_STORAGE_KEY: str = os.getenv("AZURE_STORAGE_KEY", "")
    AZURE_CONTAINER: str = os.getenv("AZURE_CONTAINER", "infinityai-models")

    # Model URLs (for cloud downloads)
    YOLO_MODEL_URL: str = os.getenv("YOLO_MODEL_URL", "")
    EMBEDDING_MODEL_URL: str = os.getenv("EMBEDDING_MODEL_URL", "")

    # Broker Configuration
    BROKER_TYPE: str = os.getenv("BROKER_TYPE", "dhan")  # dhan or coinswitch

    # Dhan Broker
    DHAN_BASE_URL: str = os.getenv("DHAN_BASE_URL", "https://api.dhan.co")
    DHAN_ACCESS_TOKEN: str = os.getenv("DHAN_ACCESS_TOKEN", "")
    DHAN_CLIENT_ID: str = os.getenv("DHAN_CLIENT_ID", "")

    # CoinSwitch PRO Broker
    COINSWITCH_BASE_URL: str = os.getenv("COINSWITCH_BASE_URL", "https://api.coinswitch.co")
    COINSWITCH_API_KEY: str = os.getenv("COINSWITCH_API_KEY", "")
    COINSWITCH_API_SECRET: str = os.getenv("COINSWITCH_API_SECRET", "")

CONFIG = Config()