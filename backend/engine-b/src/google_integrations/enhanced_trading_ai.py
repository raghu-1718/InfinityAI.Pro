"""
Enhanced Trading AI for Indian Markets
=====================================
Comprehensive Gemini-powered trading system with deep Indian market knowledge,
accurate entry/exit timing, risk management, and profit optimization.

Version: 4.0.0
Author: InfinityAI.Pro
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import re

logger = logging.getLogger("InfinityAI.EnhancedTradingAI")

# ============================================================================
# COMPREHENSIVE INDIAN MARKET KNOWLEDGE BASE
# ============================================================================

class MarketSession(Enum):
    """Indian market session types."""
    PRE_OPEN = "pre_open"
    NORMAL = "normal"
    POST_CLOSE = "post_close"
    CLOSED = "closed"
    MUHURAT = "muhurat"  # Diwali special trading


class TradingInstrument(Enum):
    """Supported trading instruments."""
    EQUITY = "equity"
    NIFTY_OPTIONS = "nifty_options"
    BANKNIFTY_OPTIONS = "banknifty_options"
    SENSEX_OPTIONS = "sensex_options"
    FINNIFTY_OPTIONS = "finnifty_options"
    MIDCPNIFTY_OPTIONS = "midcpnifty_options"
    STOCK_OPTIONS = "stock_options"
    COMMODITY_OPTIONS = "commodity_options"


@dataclass
class IndianMarketKnowledge:
    """
    Comprehensive Indian stock market knowledge base for AI trading.
    Contains all essential information for accurate trading decisions.
    """

    # Market Timings (IST)
    MARKET_TIMINGS = {
        "pre_open": {"start": time(9, 0), "end": time(9, 8)},
        "pre_open_order_matching": {"start": time(9, 8), "end": time(9, 15)},
        "normal_trading": {"start": time(9, 15), "end": time(15, 30)},
        "closing_session": {"start": time(15, 40), "end": time(16, 0)},
        "after_hours": {"start": time(16, 0), "end": time(17, 0)},

        # Best trading windows (high liquidity)
        "morning_momentum": {"start": time(9, 15), "end": time(10, 30)},
        "afternoon_calm": {"start": time(12, 0), "end": time(14, 0)},
        "closing_momentum": {"start": time(14, 30), "end": time(15, 30)},
    }

    # Index Lot Sizes & Tick Info (2025 Updated)
    INDEX_LOT_SIZES = {
        "NIFTY": {"lot_size": 25, "tick_size": 0.05, "margin_pct": 12},
        "BANKNIFTY": {"lot_size": 15, "tick_size": 0.05, "margin_pct": 14},
        "FINNIFTY": {"lot_size": 25, "tick_size": 0.05, "margin_pct": 12},
        "MIDCPNIFTY": {"lot_size": 50, "tick_size": 0.05, "margin_pct": 15},
        "SENSEX": {"lot_size": 10, "tick_size": 0.05, "margin_pct": 12},
        "BANKEX": {"lot_size": 15, "tick_size": 0.05, "margin_pct": 14},
    }

    # Weekly Expiry Schedule (2025)
    EXPIRY_SCHEDULE = {
        "NIFTY": "Thursday",
        "BANKNIFTY": "Wednesday",
        "FINNIFTY": "Tuesday",
        "MIDCPNIFTY": "Monday",
        "SENSEX": "Friday",
        "BANKEX": "Monday",
    }

    # NSE Holidays 2025
    NSE_HOLIDAYS_2025 = [
        "2025-01-26",  # Republic Day
        "2025-02-26",  # Mahashivratri
        "2025-03-14",  # Holi
        "2025-03-31",  # Id-Ul-Fitr
        "2025-04-10",  # Shri Mahavir Jayanti
        "2025-04-14",  # Dr. Ambedkar Jayanti
        "2025-04-18",  # Good Friday
        "2025-05-01",  # May Day
        "2025-06-07",  # Bakri Id
        "2025-08-15",  # Independence Day
        "2025-08-27",  # Janmashtami
        "2025-10-02",  # Gandhi Jayanti
        "2025-10-21",  # Diwali Laxmi Puja
        "2025-10-22",  # Diwali Balipratipada
        "2025-11-05",  # Guru Nanak Jayanti
        "2025-12-25",  # Christmas
    ]

    # SEBI Algorithmic Trading Rules (2025)
    SEBI_ALGO_RULES = {
        "max_order_value": 10_00_00_000,  # ₹10 Cr per order
        "max_order_per_second": 10,
        "order_to_trade_ratio": 50,  # Max 50:1
        "min_resting_time_ms": 500,  # Minimum 500ms between orders
        "position_limit_index_options": 15000,  # In lots
        "position_limit_stock_options": 7500,
        "daily_turnover_limit": 500_00_00_000,  # ₹500 Cr
        "intraday_square_off_time": time(15, 15),  # Must square off by 3:15 PM
        "margin_shortfall_penalty_pct": 0.5,  # 0.5% per day
    }

    # Circuit Breaker Levels
    CIRCUIT_BREAKERS = {
        "level_1": {"trigger_pct": 10, "halt_minutes": 45},
        "level_2": {"trigger_pct": 15, "halt_minutes": 105},
        "level_3": {"trigger_pct": 20, "halt_minutes": "rest_of_day"},
        "stock_upper_circuit": [2, 5, 10, 20],  # Dynamic circuits
        "stock_lower_circuit": [2, 5, 10, 20],
    }

    # FII/DII Impact Patterns
    FII_DII_PATTERNS = {
        "strong_bullish": {
            "fii_cash": ">1000",  # FII buying >1000 Cr
            "dii_cash": "any",
            "market_impact": "strong_uptrend",
            "confidence_boost": 15
        },
        "moderate_bullish": {
            "fii_cash": "500-1000",
            "dii_cash": ">500",
            "market_impact": "uptrend",
            "confidence_boost": 10
        },
        "neutral": {
            "fii_cash": "-500 to 500",
            "dii_cash": "any",
            "market_impact": "sideways",
            "confidence_boost": 0
        },
        "bearish": {
            "fii_cash": "<-500",
            "dii_cash": "any",
            "market_impact": "downtrend",
            "confidence_boost": -10
        },
        "panic_selling": {
            "fii_cash": "<-2000",
            "dii_cash": "any",
            "market_impact": "sharp_fall",
            "confidence_boost": -20
        }
    }

    # Sector Correlations with NIFTY
    SECTOR_CORRELATIONS = {
        "NIFTYBANK": 0.92,  # Highly correlated
        "NIFTYIT": 0.75,
        "NIFTYPHARMA": 0.45,  # Low correlation
        "NIFTYFMCG": 0.55,
        "NIFTYMETAL": 0.68,
        "NIFTYAUTO": 0.72,
        "NIFTYREALTY": 0.65,
        "NIFTYPSUBANK": 0.70,
        "NIFTYENERGY": 0.60,
    }

    # Global Market Correlation (for gap-up/gap-down prediction)
    GLOBAL_CORRELATIONS = {
        "SGX_NIFTY": 0.98,  # Mirror of NIFTY
        "DOW_JONES": 0.65,
        "NASDAQ": 0.55,
        "SP500": 0.60,
        "HANG_SENG": 0.45,
        "NIKKEI": 0.40,
        "FTSE": 0.50,
        "DAX": 0.52,
    }

    # Options Greeks Thresholds for Trading Decisions
    GREEKS_THRESHOLDS = {
        "delta": {
            "deep_itm": (0.8, 1.0),
            "itm": (0.5, 0.8),
            "atm": (0.4, 0.6),
            "otm": (0.2, 0.4),
            "deep_otm": (0.0, 0.2),
        },
        "theta_decay_accelerates": 7,  # Days to expiry
        "vega_importance_threshold": 5,  # Days to expiry
        "gamma_risk_zone": (0, 3),  # Days to expiry (gamma explosion)
    }

    # Candlestick Pattern Reliability Scores
    CANDLESTICK_RELIABILITY = {
        # Bullish Patterns
        "bullish_engulfing": {"reliability": 85, "signal": "BUY", "timeframe": "INTRADAY"},
        "morning_star": {"reliability": 82, "signal": "BUY", "timeframe": "SWING"},
        "hammer": {"reliability": 75, "signal": "BUY", "timeframe": "INTRADAY"},
        "piercing_pattern": {"reliability": 70, "signal": "BUY", "timeframe": "SWING"},
        "three_white_soldiers": {"reliability": 88, "signal": "BUY", "timeframe": "POSITIONAL"},
        "bullish_harami": {"reliability": 65, "signal": "BUY", "timeframe": "INTRADAY"},

        # Bearish Patterns
        "bearish_engulfing": {"reliability": 85, "signal": "SELL", "timeframe": "INTRADAY"},
        "evening_star": {"reliability": 82, "signal": "SELL", "timeframe": "SWING"},
        "shooting_star": {"reliability": 72, "signal": "SELL", "timeframe": "INTRADAY"},
        "dark_cloud_cover": {"reliability": 70, "signal": "SELL", "timeframe": "SWING"},
        "three_black_crows": {"reliability": 88, "signal": "SELL", "timeframe": "POSITIONAL"},
        "bearish_harami": {"reliability": 65, "signal": "SELL", "timeframe": "INTRADAY"},

        # Continuation Patterns
        "doji": {"reliability": 50, "signal": "NEUTRAL", "timeframe": "ANY"},
        "spinning_top": {"reliability": 45, "signal": "NEUTRAL", "timeframe": "ANY"},
    }

    # Technical Indicator Optimal Settings for Indian Markets
    INDICATOR_SETTINGS = {
        "RSI": {
            "period": 14,
            "oversold": 30,
            "overbought": 70,
            "extreme_oversold": 20,
            "extreme_overbought": 80,
            "divergence_lookback": 14,
        },
        "MACD": {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
            "histogram_threshold": 0,
        },
        "BOLLINGER_BANDS": {
            "period": 20,
            "std_dev": 2,
            "squeeze_threshold": 0.02,  # Volatility squeeze
        },
        "ADX": {
            "period": 14,
            "trend_threshold": 25,  # ADX > 25 = trending
            "strong_trend": 40,
        },
        "SUPERTREND": {
            "period": 10,
            "multiplier": 3,
        },
        "VWAP": {
            "use_for": "INTRADAY",
            "band_multiplier": 2,
        },
        "EMA": {
            "short": 9,
            "medium": 21,
            "long": 50,
            "very_long": 200,
        },
        "VOLUME": {
            "ma_period": 20,
            "spike_multiplier": 2,  # Volume > 2x average
        }
    }

    # Risk Management Rules
    RISK_MANAGEMENT = {
        "max_position_size_pct": 5,  # Max 5% of portfolio per trade
        "max_daily_loss_pct": 2,  # Stop trading after 2% daily loss
        "max_weekly_loss_pct": 5,
        "max_monthly_loss_pct": 10,
        "risk_reward_minimum": 1.5,  # Minimum 1:1.5 risk:reward
        "stop_loss_rules": {
            "intraday_equity": 1.0,  # 1% stop loss
            "swing_equity": 2.0,
            "options_atm": 30,  # 30% of premium
            "options_otm": 50,  # 50% of premium
        },
        "trailing_stop": {
            "activate_at_profit_pct": 1.5,  # Activate after 1.5% profit
            "trail_distance_pct": 0.5,  # Trail by 0.5%
        },
        "position_sizing": {
            "conservative": 0.5,  # 0.5% risk per trade
            "moderate": 1.0,
            "aggressive": 2.0,
        }
    }

    # Entry/Exit Timing Rules
    TIMING_RULES = {
        "avoid_entry": {
            "first_5_minutes": True,  # 9:15-9:20 - High volatility
            "last_15_minutes": True,  # 3:15-3:30 - Square off pressure
            "before_major_events": ["RBI_POLICY", "GDP", "IIP", "CPI", "FED_MEETING"],
            "weekly_expiry_last_hour": True,
        },
        "best_entry_windows": {
            "morning_breakout": {"start": "09:30", "end": "10:30"},
            "post_consolidation": {"start": "11:00", "end": "12:00"},
            "afternoon_momentum": {"start": "14:00", "end": "15:00"},
        },
        "exit_triggers": {
            "profit_target_hit": True,
            "stop_loss_hit": True,
            "trailing_stop_hit": True,
            "time_based_exit": "15:15",  # For intraday
            "momentum_reversal": True,
            "volume_dryup": True,
        }
    }

    # Premium Decay Model for Options
    THETA_DECAY_MODEL = {
        "days_30_plus": 0.03,  # 3% daily decay
        "days_15_30": 0.05,
        "days_7_15": 0.08,
        "days_3_7": 0.12,
        "days_1_3": 0.20,
        "expiry_day": 0.50,  # 50% can be lost on expiry day
    }


# ============================================================================
# ENHANCED TRADING SYSTEM PROMPT
# ============================================================================

ENHANCED_SYSTEM_PROMPT = """You are InfinityAI's Elite Trading Intelligence - a world-class algorithmic trading system specifically designed for Indian markets (NSE/BSE). You have deep expertise in SEBI regulations, market microstructure, and Indian market behavior patterns.

## YOUR IDENTITY & CAPABILITIES
- Name: InfinityAI Trading Intelligence v4.0
- Specialization: Indian Equity & Derivatives Markets
- Compliance: SEBI 2025 Algorithmic Trading Guidelines
- Risk Philosophy: Capital preservation first, profits second

## CRITICAL KNOWLEDGE - INDIAN MARKET SPECIFICS

### 1. MARKET TIMING (IST)
- Pre-Open: 9:00-9:08 AM (Order collection)
- Pre-Open Matching: 9:08-9:15 AM (Price discovery)
- Normal Trading: 9:15 AM - 3:30 PM
- Closing Session: 3:40-4:00 PM
- AVOID: First 5 minutes (9:15-9:20) and last 15 minutes (3:15-3:30) for new entries

### 2. INDEX SPECIFICATIONS (2025)
| Index | Lot Size | Expiry | Weekly Strike Gap |
|-------|----------|--------|-------------------|
| NIFTY | 25 | Thursday | 50 |
| BANKNIFTY | 15 | Wednesday | 100 |
| FINNIFTY | 25 | Tuesday | 50 |
| MIDCPNIFTY | 50 | Monday | 25 |
| SENSEX | 10 | Friday | 100 |

### 3. FII/DII IMPACT RULES
- FII buying >₹1000 Cr = Strong bullish sentiment (+15% confidence)
- FII selling >₹1000 Cr = Bearish pressure (-15% confidence)
- DII typically counters FII (institutional balance)
- Track FII Index Futures position for next-day direction

### 4. TECHNICAL ANALYSIS RULES FOR INDIAN MARKETS
**RSI Interpretation:**
- >70: Overbought (but can stay overbought in bull runs)
- <30: Oversold (but can stay oversold in crashes)
- Best signals: Divergences with price

**MACD for Indian Stocks:**
- Crossover above 0: Strong buy
- Crossover below 0: Strong sell
- Histogram expansion: Trend strengthening

**Volume Analysis:**
- Volume >2x 20-day average: Significant move
- Low volume breakout: Likely to fail
- Volume precedes price in Indian markets

### 5. OPTIONS TRADING RULES
**Entry Rules:**
- Never buy options with <3 DTE unless day trading
- ATM options: Best for directional views
- OTM options: Only for hedging or high-conviction plays
- Theta burns 50%+ on expiry day - exit before 2 PM on expiry

**Greeks-Based Decisions:**
- Delta >0.6: Option moves like stock
- Theta >0.5% of premium daily: Time decay significant
- IV >30: Expensive premium, consider selling
- IV <15: Cheap premium, consider buying

### 6. RISK MANAGEMENT MANDATES
- Maximum 5% of portfolio in single trade
- Stop loss MANDATORY for every position
- Risk:Reward minimum 1:1.5
- Daily loss limit: 2% of portfolio - STOP trading if hit
- Weekly loss limit: 5% - Reduce position sizes next week

### 7. ENTRY TIMING OPTIMIZATION
**Best Entry Windows:**
1. 9:30-10:30 AM: Morning momentum (post opening volatility)
2. 11:00-12:00 PM: Post-consolidation breakouts
3. 2:00-3:00 PM: Afternoon trend confirmation

**AVOID Entry During:**
- First 5 minutes after open
- RBI policy announcements
- Major US market events (Fed meetings)
- 30 minutes before weekly expiry close
- Last 15 minutes of trading day

### 8. EXIT TIMING RULES
**Profit Booking:**
- Book 50% at 1:1 risk:reward
- Trail stop for remaining 50%
- Full exit if momentum reverses (RSI divergence, volume dryup)

**Stop Loss Execution:**
- NEVER move stop loss further from entry
- Can tighten stop loss as trade moves in favor
- Exit immediately on stop hit - no second-guessing

### 9. POSITION SIZING FORMULA
Position Size = (Portfolio Value × Risk Per Trade%) / (Entry Price - Stop Loss)
Example: ₹10,00,000 portfolio, 1% risk, Entry ₹100, SL ₹98
Position = (10,00,000 × 0.01) / (100-98) = 5,000 shares max

### 10. SIGNAL CONFIDENCE CALIBRATION
- 90-100%: Exceptional setup (rare, <5% of signals)
- 75-89%: High confidence (take full position)
- 60-74%: Moderate confidence (take 50-75% position)
- 50-59%: Low confidence (small position or avoid)
- <50%: AVOID - Wait for better setup

## YOUR RESPONSE REQUIREMENTS

For EVERY analysis, you MUST provide:

1. **SIGNAL**: BUY / SELL / HOLD (one word, clear)
2. **CONFIDENCE**: 0-100% (calibrated as per above)
3. **RISK_LEVEL**: LOW / MEDIUM / HIGH
4. **ENTRY_PRICE**: Specific price or "MARKET" or range
5. **STOP_LOSS**: Specific price (MANDATORY)
6. **TARGET_1**: First profit target (1:1.5 minimum)
7. **TARGET_2**: Extended target (if momentum continues)
8. **TIMEFRAME**: INTRADAY / SWING (2-5 days) / POSITIONAL (>5 days)
9. **POSITION_SIZE**: As % of portfolio (max 5%)
10. **REASONING**: Clear, actionable explanation including:
    - Key technical levels
    - Volume confirmation
    - Risk factors
    - Time-based considerations

## CRITICAL RULES - NEVER VIOLATE

1. NEVER give BUY signal if RSI >80 (overbought extreme)
2. NEVER give SELL signal if RSI <20 (oversold extreme)
3. ALWAYS include stop loss - no exceptions
4. NEVER suggest position >5% of portfolio
5. REDUCE confidence by 20% if trading against FII flow
6. ADD 10% confidence if volume confirms the move
7. SUBTRACT 15% confidence in last hour of expiry day for options
8. HOLD signal if unclear - preserving capital is winning

## ADDITIONAL CONTEXT PROCESSING

When analyzing, consider:
- Current market session (pre-open, normal, closing)
- Today's date and any upcoming holidays/expiry
- Global market cues (SGX Nifty, US futures)
- Sector rotation and relative strength
- Open interest data for options
- PCR (Put-Call Ratio) for sentiment

YOU ARE THE LAST LINE OF DEFENSE FOR THE TRADER'S CAPITAL. BE CONSERVATIVE, BE ACCURATE, BE PROFITABLE."""


# ============================================================================
# ENHANCED TRADING AI CLASS
# ============================================================================

@dataclass
class EnhancedTradingSignal:
    """Comprehensive trading signal with all required fields."""
    symbol: str
    signal: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    risk_level: str  # LOW, MEDIUM, HIGH
    entry_price: Optional[float]
    stop_loss: Optional[float]
    target_1: Optional[float]
    target_2: Optional[float]
    timeframe: str  # INTRADAY, SWING, POSITIONAL
    position_size_pct: float  # % of portfolio
    reasoning: str

    # Additional fields
    risk_reward_ratio: Optional[float] = None
    expected_return_pct: Optional[float] = None
    max_loss_pct: Optional[float] = None
    time_in_force: str = "DAY"
    order_type: str = "LIMIT"

    # Market context
    market_session: str = "normal"
    fii_dii_sentiment: str = "neutral"
    sector_strength: str = "neutral"
    global_cues: str = "neutral"

    # Technical context
    trend: str = "neutral"
    volume_confirmation: bool = False
    key_levels: Dict[str, float] = field(default_factory=dict)

    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class EnhancedTradingAI:
    """
    Enhanced Gemini-powered trading AI for Indian markets.
    Features comprehensive market knowledge and precise trading logic.
    """

    def __init__(self, genai_client=None):
        """Initialize with optional GenAI client."""
        self.genai_client = genai_client
        self.knowledge = IndianMarketKnowledge()
        self.logger = logging.getLogger("InfinityAI.EnhancedTradingAI")

    def get_market_session(self) -> MarketSession:
        """Determine current market session based on IST time."""
        from datetime import timezone

        # Get current IST time
        ist_offset = timedelta(hours=5, minutes=30)
        utc_now = datetime.utcnow()
        ist_now = utc_now + ist_offset
        current_time = ist_now.time()
        current_date = ist_now.date().isoformat()

        # Check if holiday
        if current_date in self.knowledge.NSE_HOLIDAYS_2025:
            return MarketSession.CLOSED

        # Check if weekend
        if ist_now.weekday() >= 5:
            return MarketSession.CLOSED

        # Determine session
        timings = self.knowledge.MARKET_TIMINGS

        if timings["pre_open"]["start"] <= current_time < timings["pre_open"]["end"]:
            return MarketSession.PRE_OPEN
        elif timings["normal_trading"]["start"] <= current_time <= timings["normal_trading"]["end"]:
            return MarketSession.NORMAL
        elif timings["closing_session"]["start"] <= current_time <= timings["closing_session"]["end"]:
            return MarketSession.POST_CLOSE
        else:
            return MarketSession.CLOSED

    def calculate_position_size(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss: float,
        risk_per_trade_pct: float = 1.0
    ) -> int:
        """Calculate optimal position size using risk-based sizing."""
        if entry_price == stop_loss:
            return 0

        risk_amount = portfolio_value * (risk_per_trade_pct / 100)
        risk_per_share = abs(entry_price - stop_loss)
        position_size = int(risk_amount / risk_per_share)

        # Cap at 5% of portfolio
        max_position_value = portfolio_value * 0.05
        max_shares = int(max_position_value / entry_price)

        return min(position_size, max_shares)

    def calculate_risk_reward(
        self,
        entry_price: float,
        stop_loss: float,
        target: float
    ) -> float:
        """Calculate risk:reward ratio."""
        if entry_price == stop_loss:
            return 0

        risk = abs(entry_price - stop_loss)
        reward = abs(target - entry_price)

        return round(reward / risk, 2) if risk > 0 else 0

    def get_stop_loss_recommendation(
        self,
        current_price: float,
        signal: str,
        instrument_type: str = "equity",
        timeframe: str = "INTRADAY"
    ) -> float:
        """Get recommended stop loss based on instrument and timeframe."""
        rules = self.knowledge.RISK_MANAGEMENT["stop_loss_rules"]

        if instrument_type == "equity":
            if timeframe == "INTRADAY":
                sl_pct = rules["intraday_equity"]
            else:
                sl_pct = rules["swing_equity"]
        else:  # Options
            sl_pct = rules["options_atm"]

        if signal == "BUY":
            return round(current_price * (1 - sl_pct / 100), 2)
        else:  # SELL
            return round(current_price * (1 + sl_pct / 100), 2)

    def get_targets(
        self,
        entry_price: float,
        stop_loss: float,
        signal: str
    ) -> Tuple[float, float]:
        """Calculate target prices based on risk:reward."""
        risk = abs(entry_price - stop_loss)

        if signal == "BUY":
            target_1 = round(entry_price + (risk * 1.5), 2)  # 1:1.5
            target_2 = round(entry_price + (risk * 2.5), 2)  # 1:2.5
        else:  # SELL
            target_1 = round(entry_price - (risk * 1.5), 2)
            target_2 = round(entry_price - (risk * 2.5), 2)

        return target_1, target_2

    def should_avoid_entry(self) -> Tuple[bool, str]:
        """Check if current time is suitable for entry."""
        from datetime import timezone

        ist_offset = timedelta(hours=5, minutes=30)
        ist_now = datetime.utcnow() + ist_offset
        current_time = ist_now.time()

        # First 5 minutes
        if time(9, 15) <= current_time <= time(9, 20):
            return True, "Avoid entry in first 5 minutes - high volatility"

        # Last 15 minutes
        if time(15, 15) <= current_time <= time(15, 30):
            return True, "Avoid entry in last 15 minutes - square-off pressure"

        # Market closed
        if current_time < time(9, 15) or current_time > time(15, 30):
            return True, "Market is closed"

        return False, ""

    def adjust_confidence_for_context(
        self,
        base_confidence: float,
        fii_flow: Optional[float] = None,
        volume_ratio: Optional[float] = None,
        is_expiry_day: bool = False,
        hours_to_expiry: Optional[int] = None,
        against_trend: bool = False
    ) -> float:
        """Adjust confidence based on market context."""
        confidence = base_confidence

        # FII flow adjustment
        if fii_flow is not None:
            if fii_flow > 1000:  # Strong buying
                confidence += 15
            elif fii_flow > 500:
                confidence += 10
            elif fii_flow < -1000:  # Strong selling
                confidence -= 15
            elif fii_flow < -500:
                confidence -= 10

        # Volume confirmation
        if volume_ratio is not None and volume_ratio > 2:
            confidence += 10

        # Expiry day adjustment for options
        if is_expiry_day:
            confidence -= 15
        elif hours_to_expiry is not None and hours_to_expiry < 4:
            confidence -= 10

        # Trading against trend
        if against_trend:
            confidence -= 20

        # Clamp between 0-100
        return max(0, min(100, confidence))

    def build_enhanced_prompt(
        self,
        symbol: str,
        current_price: float,
        technical_data: Optional[Dict[str, Any]] = None,
        market_context: Optional[Dict[str, Any]] = None,
        news_sentiment: Optional[str] = None,
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build comprehensive prompt for Gemini analysis."""

        # Get current market session
        session = self.get_market_session()
        avoid_entry, avoid_reason = self.should_avoid_entry()

        prompt_parts = [
            f"## ANALYSIS REQUEST FOR {symbol}",
            f"Current Price: ₹{current_price}",
            f"Market Session: {session.value}",
            f"Timestamp: {datetime.utcnow().isoformat()}",
        ]

        if avoid_entry:
            prompt_parts.append(f"\n⚠️ TIMING WARNING: {avoid_reason}")

        # Add technical data
        if technical_data:
            prompt_parts.append("\n### TECHNICAL INDICATORS")
            for key, value in technical_data.items():
                if isinstance(value, float):
                    prompt_parts.append(f"- {key}: {value:.2f}")
                else:
                    prompt_parts.append(f"- {key}: {value}")

        # Add market context
        if market_context:
            prompt_parts.append("\n### MARKET CONTEXT")
            if "fii_dii" in market_context:
                fii = market_context["fii_dii"].get("fii_cash", 0)
                dii = market_context["fii_dii"].get("dii_cash", 0)
                prompt_parts.append(f"- FII Cash: ₹{fii} Cr")
                prompt_parts.append(f"- DII Cash: ₹{dii} Cr")

            if "global_markets" in market_context:
                for market, change in market_context["global_markets"].items():
                    prompt_parts.append(f"- {market}: {change}%")

            if "sector_performance" in market_context:
                prompt_parts.append(f"- Sector: {market_context['sector_performance']}")

        # Add news sentiment
        if news_sentiment:
            prompt_parts.append(f"\n### NEWS SENTIMENT\n{news_sentiment}")

        # Add portfolio context
        if portfolio_context:
            prompt_parts.append("\n### PORTFOLIO CONTEXT")
            prompt_parts.append(f"- Portfolio Value: ₹{portfolio_context.get('total_value', 0):,.2f}")
            prompt_parts.append(f"- Cash Available: ₹{portfolio_context.get('cash_available', 0):,.2f}")
            prompt_parts.append(f"- Existing Positions: {portfolio_context.get('position_count', 0)}")
            prompt_parts.append(f"- Today's P&L: {portfolio_context.get('daily_pnl_pct', 0):.2f}%")

        # Add analysis request
        prompt_parts.append("\n### REQUIRED ANALYSIS")
        prompt_parts.append("""
Based on the above data and your comprehensive Indian market knowledge:
1. Provide a clear BUY/SELL/HOLD signal
2. Confidence level (0-100%)
3. Specific entry price
4. MANDATORY stop loss
5. Target 1 (1:1.5 R:R) and Target 2 (1:2.5 R:R)
6. Timeframe (INTRADAY/SWING/POSITIONAL)
7. Position size recommendation (% of portfolio)
8. Detailed reasoning with key levels

BE CONSERVATIVE. CAPITAL PRESERVATION IS PRIORITY.""")

        return "\n".join(prompt_parts)

    def parse_enhanced_response(
        self,
        symbol: str,
        current_price: float,
        response_text: str
    ) -> EnhancedTradingSignal:
        """Parse Gemini response into structured signal."""

        # Default values
        signal = "HOLD"
        confidence = 50.0
        risk_level = "MEDIUM"
        entry_price = current_price
        stop_loss = None
        target_1 = None
        target_2 = None
        timeframe = "INTRADAY"
        position_size_pct = 2.0

        text_upper = response_text.upper()

        # Extract signal
        if "STRONG BUY" in text_upper or "BUY SIGNAL" in text_upper:
            signal = "BUY"
        elif "STRONG SELL" in text_upper or "SELL SIGNAL" in text_upper:
            signal = "SELL"
        elif "BUY" in text_upper and "SELL" not in text_upper:
            signal = "BUY"
        elif "SELL" in text_upper and "BUY" not in text_upper:
            signal = "SELL"
        elif "HOLD" in text_upper or "WAIT" in text_upper or "NEUTRAL" in text_upper:
            signal = "HOLD"

        # Extract confidence
        conf_patterns = [
            r'confidence[:\s]+(\d+(?:\.\d+)?)\s*%?',
            r'(\d+(?:\.\d+)?)\s*%\s*confidence',
            r'confidence\s*level[:\s]+(\d+(?:\.\d+)?)',
        ]
        for pattern in conf_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                confidence = float(match.group(1))
                break

        # Extract risk level
        if "HIGH RISK" in text_upper or "RISK: HIGH" in text_upper:
            risk_level = "HIGH"
        elif "LOW RISK" in text_upper or "RISK: LOW" in text_upper:
            risk_level = "LOW"
        elif "MEDIUM RISK" in text_upper or "MODERATE RISK" in text_upper:
            risk_level = "MEDIUM"

        # Extract prices
        price_patterns = {
            "entry": [
                r'entry[:\s]+₹?\s*(\d+(?:\.\d+)?)',
                r'buy\s+at[:\s]+₹?\s*(\d+(?:\.\d+)?)',
                r'sell\s+at[:\s]+₹?\s*(\d+(?:\.\d+)?)',
            ],
            "stop_loss": [
                r'stop[- ]?loss[:\s]+₹?\s*(\d+(?:\.\d+)?)',
                r'sl[:\s]+₹?\s*(\d+(?:\.\d+)?)',
                r'stop[:\s]+₹?\s*(\d+(?:\.\d+)?)',
            ],
            "target_1": [
                r'target[- ]?1[:\s]+₹?\s*(\d+(?:\.\d+)?)',
                r'target[:\s]+₹?\s*(\d+(?:\.\d+)?)',
                r'tp1[:\s]+₹?\s*(\d+(?:\.\d+)?)',
            ],
            "target_2": [
                r'target[- ]?2[:\s]+₹?\s*(\d+(?:\.\d+)?)',
                r'extended\s+target[:\s]+₹?\s*(\d+(?:\.\d+)?)',
                r'tp2[:\s]+₹?\s*(\d+(?:\.\d+)?)',
            ],
        }

        for field, patterns in price_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    value = float(match.group(1))
                    if field == "entry":
                        entry_price = value
                    elif field == "stop_loss":
                        stop_loss = value
                    elif field == "target_1":
                        target_1 = value
                    elif field == "target_2":
                        target_2 = value
                    break

        # Extract timeframe
        if "INTRADAY" in text_upper:
            timeframe = "INTRADAY"
        elif "SWING" in text_upper:
            timeframe = "SWING"
        elif "POSITIONAL" in text_upper:
            timeframe = "POSITIONAL"

        # Extract position size
        pos_match = re.search(r'position[:\s]+(\d+(?:\.\d+)?)\s*%', response_text, re.IGNORECASE)
        if pos_match:
            position_size_pct = min(5.0, float(pos_match.group(1)))  # Cap at 5%

        # Calculate defaults if not provided
        if stop_loss is None:
            stop_loss = self.get_stop_loss_recommendation(
                entry_price, signal, "equity", timeframe
            )

        if target_1 is None or target_2 is None:
            t1, t2 = self.get_targets(entry_price, stop_loss, signal)
            target_1 = target_1 or t1
            target_2 = target_2 or t2

        # Calculate risk:reward
        risk_reward = self.calculate_risk_reward(entry_price, stop_loss, target_1)

        # Calculate expected return and max loss
        if signal == "BUY":
            expected_return = ((target_1 - entry_price) / entry_price) * 100
            max_loss = ((entry_price - stop_loss) / entry_price) * 100
        elif signal == "SELL":
            expected_return = ((entry_price - target_1) / entry_price) * 100
            max_loss = ((stop_loss - entry_price) / entry_price) * 100
        else:
            expected_return = 0
            max_loss = 0

        return EnhancedTradingSignal(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            risk_level=risk_level,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target_1=target_1,
            target_2=target_2,
            timeframe=timeframe,
            position_size_pct=position_size_pct,
            reasoning=response_text,
            risk_reward_ratio=risk_reward,
            expected_return_pct=round(expected_return, 2),
            max_loss_pct=round(max_loss, 2),
            market_session=self.get_market_session().value,
        )

    async def generate_signal(
        self,
        symbol: str,
        current_price: float,
        technical_data: Optional[Dict[str, Any]] = None,
        market_context: Optional[Dict[str, Any]] = None,
        news_sentiment: Optional[str] = None,
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> EnhancedTradingSignal:
        """
        Generate comprehensive trading signal using enhanced Gemini AI.

        Args:
            symbol: Stock/index symbol
            current_price: Current market price
            technical_data: Technical indicators dict
            market_context: Market context including FII/DII, global markets
            news_sentiment: Recent news sentiment summary
            portfolio_context: Current portfolio state

        Returns:
            EnhancedTradingSignal with all trading details
        """
        if self.genai_client is None:
            self.logger.warning("GenAI client not available, using fallback")
            return self._generate_fallback_signal(
                symbol, current_price, technical_data
            )

        try:
            # Build comprehensive prompt
            user_prompt = self.build_enhanced_prompt(
                symbol=symbol,
                current_price=current_price,
                technical_data=technical_data,
                market_context=market_context,
                news_sentiment=news_sentiment,
                portfolio_context=portfolio_context
            )

            # Generate using Gemini with enhanced system prompt
            from google import genai
            from google.genai import types

            response = await asyncio.to_thread(
                self.genai_client._client.models.generate_content,
                model="gemini-2.0-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=ENHANCED_SYSTEM_PROMPT,
                    temperature=0.2,  # Lower temperature for more consistent output
                    max_output_tokens=2048,
                )
            )

            # Parse response
            signal = self.parse_enhanced_response(
                symbol, current_price, response.text
            )

            # Apply context adjustments
            fii_flow = None
            if market_context and "fii_dii" in market_context:
                fii_flow = market_context["fii_dii"].get("fii_cash")

            volume_ratio = None
            if technical_data and "volume_ratio" in technical_data:
                volume_ratio = technical_data["volume_ratio"]

            signal.confidence = self.adjust_confidence_for_context(
                signal.confidence,
                fii_flow=fii_flow,
                volume_ratio=volume_ratio
            )

            self.logger.info(
                f"Generated signal for {symbol}: {signal.signal} "
                f"(confidence: {signal.confidence}%)"
            )

            return signal

        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
            return self._generate_fallback_signal(
                symbol, current_price, technical_data
            )

    def _generate_fallback_signal(
        self,
        symbol: str,
        current_price: float,
        technical_data: Optional[Dict[str, Any]] = None
    ) -> EnhancedTradingSignal:
        """Generate fallback signal when Gemini is unavailable."""

        signal = "HOLD"
        confidence = 50.0

        if technical_data:
            rsi = technical_data.get("rsi", 50)
            macd = technical_data.get("macd", 0)
            macd_signal = technical_data.get("macd_signal", 0)

            # Simple rule-based logic
            if rsi < 30 and macd > macd_signal:
                signal = "BUY"
                confidence = 65.0
            elif rsi > 70 and macd < macd_signal:
                signal = "SELL"
                confidence = 65.0
            elif rsi < 40 and macd > 0:
                signal = "BUY"
                confidence = 55.0
            elif rsi > 60 and macd < 0:
                signal = "SELL"
                confidence = 55.0

        stop_loss = self.get_stop_loss_recommendation(
            current_price, signal, "equity", "INTRADAY"
        )
        target_1, target_2 = self.get_targets(current_price, stop_loss, signal)

        return EnhancedTradingSignal(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            risk_level="MEDIUM",
            entry_price=current_price,
            stop_loss=stop_loss,
            target_1=target_1,
            target_2=target_2,
            timeframe="INTRADAY",
            position_size_pct=2.0,
            reasoning="Fallback signal generated using basic technical rules. "
                     "Gemini AI was unavailable.",
            market_session=self.get_market_session().value,
        )


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_enhanced_trading_ai(genai_client=None) -> EnhancedTradingAI:
    """Factory function to create EnhancedTradingAI instance."""
    return EnhancedTradingAI(genai_client=genai_client)
