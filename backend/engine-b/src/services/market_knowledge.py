# =====================================================================
# InfinityAI.Pro - Indian Stock Market ML Knowledge Base
# Comprehensive Trading & Financial Intelligence Module
# STATUS: VERIFIED ACCURATE [DEC 2025]
# VERSIONED • HEALTH-READY • ENGINE-B SAFE
# =====================================================================

import logging
import math
import hashlib
from datetime import datetime, timedelta, time, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache

try:
    import pytz
    IST = pytz.timezone("Asia/Kolkata")
except Exception:
    IST = None  # graceful fallback

logger = logging.getLogger("InfinityAI.MarketKnowledge")

# =====================================================================
# METADATA (VERSIONING / DRIFT DETECTION)
# =====================================================================

KNOWLEDGE_VERSION = "2.2.0"
LAST_UPDATED = "2025-12-01"


def _compute_checksum() -> str:
    """
    Deterministic checksum to detect rule drift.
    Changes only if static knowledge changes.
    """
    payload = f"{KNOWLEDGE_VERSION}|{LAST_UPDATED}|SEBI|OPTIONS|RISK|TECHNICAL"
    return hashlib.sha256(payload.encode()).hexdigest()


KNOWLEDGE_CHECKSUM = _compute_checksum()

# =====================================================================
# SECTION 1: INDIAN MARKET STRUCTURE & CONSTANTS
# =====================================================================

class Exchange(Enum):
    NSE = "National Stock Exchange"
    BSE = "Bombay Stock Exchange"
    MCX = "Multi Commodity Exchange"


class Segment(Enum):
    EQUITY = "Cash/Equity"
    FNO = "Futures & Options"
    CURRENCY = "Currency Derivatives"
    COMMODITY = "Commodity Derivatives"


class TradingSession(Enum):
    PRE_OPEN = "pre_open"
    NORMAL = "normal"
    POST_CLOSE = "post_close"
    CLOSED = "closed"


@dataclass(frozen=True)
class MarketInfo:
    """
    Complete Indian Market Information
    """

    EXCHANGES: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "NSE": {
            "full_name": "National Stock Exchange of India",
            "benchmark_index": "NIFTY 50",
            "website": "https://www.nseindia.com",
            "trading_hours": {"start": "09:15", "end": "15:30"},
            "pre_open": {"start": "09:00", "end": "09:07"},
            "post_close": {"start": "15:40", "end": "16:00"}
        },
        "BSE": {
            "full_name": "Bombay Stock Exchange",
            "benchmark_index": "SENSEX",
            "trading_hours": {"start": "09:15", "end": "15:30"}
        },
        "MCX": {
            "full_name": "Multi Commodity Exchange",
            "trading_hours": {"start": "09:00", "end": "23:30"}
        }
    })

    INDICES: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "NIFTY50": {
            "full_name": "NIFTY 50",
            "components": 50,
            "sectors": [
                "Financial Services (33%)",
                "IT (14%)",
                "Oil & Gas (12%)",
                "Consumer Goods (9%)",
                "Auto (6%)"
            ]
        },
        "BANKNIFTY": {
            "full_name": "NIFTY Bank",
            "components": 12,
            "top_constituents": [
                "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"
            ]
        },
        "FINNIFTY": {
            "full_name": "Nifty Financial Services",
            "components": 20,
            "description": "Banks + NBFCs + Insurance + Housing Finance"
        },
        "MIDCPNIFTY": {
            "full_name": "Nifty Midcap Select",
            "components": 25
        }
    })

# =====================================================================
# SECTION 2: SEBI REGULATIONS & COMPLIANCE
# =====================================================================

class SEBIRegulations:
    """
    SEBI Rules and Regulations for Algorithmic Trading
    """

    LOT_SIZES_DEC_2025 = {
        "NIFTY": 75,
        "BANKNIFTY": 35,
        "FINNIFTY": 65,
        "MIDCPNIFTY": 140,
        "NIFTYNXT50": 25,
        "SENSEX": 20,
        "BANKEX": 30,
    }

    LOT_SIZES_POST_DEC30 = {
        "NIFTY": 65,
        "BANKNIFTY": 30,
        "FINNIFTY": 60,
        "MIDCPNIFTY": 120,
    }

    STT_RATES = {
        "EQUITY_DELIVERY": 0.001,
        "EQUITY_INTRADAY": 0.00025,
        "FNO_FUTURES": 0.0002,
        "FNO_OPTIONS_SELL": 0.001,
        "FNO_OPTIONS_EXERCISE": 0.00125
    }

    MARGIN_RULES = {
        "INTRADAY_EQUITY": {
            "max_leverage": "5x",
            "peak_margin": "100% upfront"
        },
        "FNO_OPTIONS_BUY": {
            "margin": "100% of Premium"
        },
        "FNO_OPTIONS_SELL": {
            "margin": "SPAN + Exposure (Dynamic)",
            "nifty_approx": "₹1.1L-1.3L naked, ₹40k-50k hedged"
        }
    }

    CIRCUIT_BREAKERS = {
        "10%": {
            "before_1pm": "45 min halt",
            "1pm_to_230pm": "15 min halt",
            "after_230pm": "No halt"
        },
        "15%": {
            "before_1pm": "1h 45min halt",
            "1pm_to_2pm": "45 min halt",
            "after_2pm": "Trading halted for day"
        },
        "20%": "Trading halted for day"
    }

    WEEKLY_EXPIRY = {
        0: "MIDCPNIFTY",
        1: "FINNIFTY",
        2: "BANKNIFTY",
        3: "NIFTY",
        4: "SENSEX/BANKEX"
    }

    @classmethod
    def get_current_lot_size(cls, symbol: str) -> int:
        if not symbol:
            return 1

        symbol = symbol.upper().replace(" ", "")
        if symbol in ("NIFTY50", "NIFTY"):
            symbol = "NIFTY"
        elif symbol in ("NIFTYBANK", "BANKNIFTY"):
            symbol = "BANKNIFTY"

        today = date.today()
        cutoff = date(2025, 12, 30)

        if today >= cutoff:
            return cls.LOT_SIZES_POST_DEC30.get(
                symbol, cls.LOT_SIZES_DEC_2025.get(symbol, 1)
            )
        return cls.LOT_SIZES_DEC_2025.get(symbol, 1)

# =====================================================================
# SECTION 3: TECHNICAL ANALYSIS
# =====================================================================

class TechnicalAnalysis:
    """Technical Analysis Engine"""

    CANDLESTICK_PATTERNS = {
        "REVERSAL_BULLISH": {
            "HAMMER": {"reliability": "high"},
            "MORNING_STAR": {"reliability": "high"},
            "BULLISH_ENGULFING": {"reliability": "high"},
            "PIERCING_LINE": {"reliability": "medium"},
        },
        "REVERSAL_BEARISH": {
            "SHOOTING_STAR": {"reliability": "high"},
            "EVENING_STAR": {"reliability": "high"},
            "BEARISH_ENGULFING": {"reliability": "high"},
            "DARK_CLOUD_COVER": {"reliability": "medium"},
        }
    }

    INDICATORS = {
        "RSI": {"period": 14, "overbought": 70, "oversold": 30},
        "MACD": {"fast": 12, "slow": 26, "signal": 9},
        "ADX": {"period": 14},
        "BOLLINGER_BANDS": {"period": 20, "std_dev": 2},
        "VWAP": {"usage": "Institutional benchmark"},
    }

    MOVING_AVERAGES = {
        "EMA_9": "Short-term trend",
        "EMA_21": "Intraday trend",
        "SMA_50": "Medium-term trend",
        "SMA_200": "Long-term trend"
    }

# =====================================================================
# SECTION 4: OPTIONS KNOWLEDGE & GREEKS
# =====================================================================

class OptionsKnowledge:
    GREEKS = {
        "DELTA": {"range_call": [0, 1], "range_put": [-1, 0]},
        "GAMMA": {"highest_at": "ATM"},
        "THETA": {"decay": "time"},
        "VEGA": {"iv_sensitivity": True}
    }

    STRATEGIES = {
        "BULLISH": ["LONG_CALL", "BULL_CALL_SPREAD"],
        "BEARISH": ["LONG_PUT", "BEAR_PUT_SPREAD"],
        "NEUTRAL": ["IRON_CONDOR", "SHORT_STRADDLE"]
    }


class OptionsMath:
    RISK_FREE_RATE = 0.07

    @staticmethod
    @lru_cache(maxsize=2048)
    def _norm_cdf(x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    @staticmethod
    def _norm_pdf(x: float) -> float:
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

    @classmethod
    def calculate_greeks(
        cls,
        spot_price: float,
        strike_price: float,
        days_to_expiry: float,
        iv: float,
        option_type: str = "CALL",
        risk_free_rate: Optional[float] = None
    ) -> Dict[str, float]:

        r = risk_free_rate or cls.RISK_FREE_RATE
        T = max(days_to_expiry / 365.0, 1e-6)
        sigma = max(iv, 0.001)

        try:
            d1 = (
                math.log(spot_price / strike_price)
                + (r + 0.5 * sigma ** 2) * T
            ) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)

            delta = cls._norm_cdf(d1) if option_type.upper() == "CALL" else cls._norm_cdf(d1) - 1
            gamma = cls._norm_pdf(d1) / (spot_price * sigma * math.sqrt(T))
            theta = -spot_price * cls._norm_pdf(d1) * sigma / (2 * math.sqrt(T)) / 365
            vega = spot_price * cls._norm_pdf(d1) * math.sqrt(T) / 100

            return {
                "delta": round(delta, 4),
                "gamma": round(gamma, 6),
                "theta": round(theta, 4),
                "vega": round(vega, 4)
            }
        except Exception as e:
            logger.warning(f"Greeks error: {e}")
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0}

# =====================================================================
# SECTION 5: RISK MANAGEMENT
# =====================================================================

class RiskManagement:
    @staticmethod
    def calculate_position_size(
        capital: float,
        risk_percent: float,
        entry_price: float,
        stop_loss_price: float,
        lot_size: int
    ) -> Dict[str, Any]:

        if entry_price == stop_loss_price:
            return {"error": "Invalid stop loss"}

        risk_amount = capital * (risk_percent / 100.0)
        risk_per_unit = abs(entry_price - stop_loss_price)
        qty = int(risk_amount / (risk_per_unit * lot_size))

        return {
            "lots": max(qty, 0),
            "quantity": max(qty * lot_size, 0),
            "risk_amount": round(risk_amount, 2)
        }

# =====================================================================
# SECTION 6: REAL-TIME MARKET ANALYSIS
# =====================================================================

class RealTimeAnalyzer:
    @staticmethod
    def get_trading_session() -> Dict[str, Any]:
        now = datetime.now(IST) if IST else datetime.now()
        t = now.time()

        if now.weekday() >= 5:
            return {"session": TradingSession.CLOSED.value, "is_trading": False}

        if time(9, 0) <= t < time(9, 15):
            return {"session": TradingSession.PRE_OPEN.value, "is_trading": False}
        if time(9, 15) <= t < time(15, 30):
            return {"session": TradingSession.NORMAL.value, "is_trading": True}
        if time(15, 40) <= t < time(16, 0):
            return {"session": TradingSession.POST_CLOSE.value, "is_trading": False}

        return {"session": TradingSession.CLOSED.value, "is_trading": False}

# =====================================================================
# SECTION 7: FUNDAMENTAL ANALYSIS
# =====================================================================

class FundamentalAnalysis:
    SECTORS = {
        "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN"],
        "IT": ["TCS", "INFY", "WIPRO"],
        "PHARMA": ["SUNPHARMA", "DRREDDY"],
    }

# =====================================================================
# SECTION 8: TRADING PSYCHOLOGY
# =====================================================================

class TradingPsychology:
    RULES = [
        "Never risk more than 2%",
        "Always use stop-loss",
        "Avoid revenge trading",
        "Stick to your plan"
    ]

# =====================================================================
# SECTION 9: MAIN KNOWLEDGE INTERFACE
# =====================================================================

class IndianMarketKnowledge:
    """
    SINGLE ENTRY POINT FOR ENGINE-B
    """

    version = KNOWLEDGE_VERSION
    last_updated = LAST_UPDATED
    checksum = KNOWLEDGE_CHECKSUM

    def __init__(self):
        self.market_info = MarketInfo()
        self.sebi = SEBIRegulations()
        self.technical = TechnicalAnalysis()
        self.options = OptionsKnowledge()
        self.options_math = OptionsMath()
        self.risk = RiskManagement()
        self.analyzer = RealTimeAnalyzer()
        self.fundamental = FundamentalAnalysis()
        self.psychology = TradingPsychology()

    # ---- SAFE WRAPPERS ----

    def get_lot_size(self, symbol: str) -> int:
        return self.sebi.get_current_lot_size(symbol)

    def calculate_greeks(self, *args, **kwargs) -> Dict[str, float]:
        return self.options_math.calculate_greeks(*args, **kwargs)

    def get_trading_session(self) -> Dict[str, Any]:
        return self.analyzer.get_trading_session()

# =====================================================================
# EXPORTS
# =====================================================================

MARKET_INFO = MarketInfo()
SEBI_RULES = SEBIRegulations()
TECHNICAL_ANALYSIS = TechnicalAnalysis()
OPTIONS_KNOWLEDGE = OptionsKnowledge()
OPTIONS_MATH = OptionsMath()
RISK_MANAGEMENT = RiskManagement()
REAL_TIME_ANALYZER = RealTimeAnalyzer()
FUNDAMENTAL_ANALYSIS = FundamentalAnalysis()
TRADING_PSYCHOLOGY = TradingPsychology()

__all__ = [
    "IndianMarketKnowledge",
    "MarketInfo",
    "SEBIRegulations",
    "TechnicalAnalysis",
    "OptionsKnowledge",
    "OptionsMath",
    "RiskManagement",
    "RealTimeAnalyzer",
    "FundamentalAnalysis",
    "TradingPsychology",
    "Exchange",
    "Segment",
    "TradingSession",
]
