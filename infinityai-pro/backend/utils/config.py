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
        "GIFTNIFTY"
    ])

    LOT_SIZE: Dict[str,int] = field(default_factory=lambda: {"NIFTY":50, "BANKNIFTY":25, "MCX_GOLD_MINI":100})
    MIN_OPTION_PREMIUM: float = 50.0
    TP_MULTIPLIER: float = 1.5
    MODEL_PATH: str = "models/lightgbm_small.pkl"
    BACKTEST_DATA_PATH: str = "data/backtest_5m/"  # expects CSVs per symbol
    PAPER_MODE: bool = False  # ⚠️ LIVE TRADING ENABLED

    BROKER: dict = field(default_factory=lambda: {
        "provider":"DHAN",
        "client_id":"1101302170",
        "client_secret":"0c7d1fd6-53d0-41e3-9d71-f6b08077e874",
        "data_api_key":"afbecc8d",
        "data_api_secret":"0c7d1fd6-53d0-41e3-9d71-f6b08077e874",
        "access_token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NTg5NTQ4MDYsImlhdCI6MTc1ODg2ODQwNiwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vaW5maW5pdHlhaS5wcm8vYXBpL2RoYW4vY2FsbGJhY2siLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.AkNcjigwjCHj6aM1itcLWgpt3Ivkmbqw2apcEDE--mKoNh5cvIXpPm4k8OYgql5-4dEDP23jQL-HAnM-cSYkfw"
    })

    TRADINGVIEW: dict = field(default_factory=lambda: {"api_key": None, "enabled": True})  # TradingView integration
    PERPLEXITY: dict = field(default_factory=lambda: {"api_key": os.getenv("PERPLEXITY_API_KEY", ""), "enabled": True})  # Perplexity for market intelligence
    OPENAI: dict = field(default_factory=lambda: {"api_key": os.getenv("OPENAI_API_KEY", ""), "model": "gpt-3.5-turbo", "enabled": True})  # OpenAI for strategy narration

    COMMISSION_PER_TRADE: float = 20.0
    SLIPPAGE_PTS: float = 0.5
    RANDOM_SEED: int = 42

CONFIG = Config()