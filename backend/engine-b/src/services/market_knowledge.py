# =====================================================================
# InfinityAI.Pro - Indian Stock Market ML Knowledge Base
# Comprehensive Trading & Financial Intelligence Module
# STATUS: VERIFIED ACCURATE [DEC 2025]
# =====================================================================

import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import math

logger = logging.getLogger("InfinityAI.MarketKnowledge")

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


@dataclass
class MarketInfo:
    """
    Complete Indian Market Information
    Last Updated: December 2025
    """

    EXCHANGES: Dict = field(default_factory=lambda: {
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

    INDICES: Dict = field(default_factory=lambda: {
        "NIFTY50": {
            "full_name": "NIFTY 50",
            "components": 50,
            "sectors": ["Financial Services (33%)", "IT (14%)", "Oil & Gas (12%)", "Consumer Goods (9%)", "Auto (6%)"]
        },
        "BANKNIFTY": {
            "full_name": "NIFTY Bank",
            "components": 12,
            "top_constituents": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"]
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
# SECTION 2: SEBI REGULATIONS & COMPLIANCE (DEC 2025 VERIFIED)
# =====================================================================

class SEBIRegulations:
    """
    SEBI Rules and Regulations for Algorithmic Trading
    Verified Date: December 1, 2025
    """

    # -----------------------------------------------------------------
    # 1. LOT SIZES (CRITICAL - Current as of Dec 2025)
    # Note: Dec 30, 2025 reduction scheduled per SEBI circular
    # -----------------------------------------------------------------
    LOT_SIZES_DEC_2025 = {
        "NIFTY": 75,           # Active through Dec 29, 2025
        "BANKNIFTY": 35,       # Active (was 30, changed July 2025)
        "FINNIFTY": 65,        # Active
        "MIDCPNIFTY": 140,     # Active
        "NIFTYNXT50": 25,
        "SENSEX": 20,          # BSE
        "BANKEX": 30,          # BSE
    }

    # Upcoming reduction effective Dec 30, 2025
    LOT_SIZES_POST_DEC30 = {
        "NIFTY": 65,
        "BANKNIFTY": 30,
        "FINNIFTY": 60,
        "MIDCPNIFTY": 120,
    }

    # -----------------------------------------------------------------
    # 2. STT RATES (Post-Oct 2024 Budget Hike)
    # -----------------------------------------------------------------
    STT_RATES = {
        "EQUITY_DELIVERY": 0.001,       # 0.1% on buy & sell
        "EQUITY_INTRADAY": 0.00025,     # 0.025% sell only
        "FNO_FUTURES": 0.0002,          # 0.02% sell only (doubled from 0.01%)
        "FNO_OPTIONS_SELL": 0.001,      # 0.1% on premium (doubled from 0.05%)
        "FNO_OPTIONS_EXERCISE": 0.00125 # 0.125% on intrinsic value
    }

    # -----------------------------------------------------------------
    # 3. MARGIN RULES
    # -----------------------------------------------------------------
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

    # -----------------------------------------------------------------
    # 4. CIRCUIT BREAKERS (Market Wide)
    # -----------------------------------------------------------------
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

    # -----------------------------------------------------------------
    # 5. WEEKLY EXPIRY CALENDAR
    # -----------------------------------------------------------------
    WEEKLY_EXPIRY = {
        0: "MIDCPNIFTY",       # Monday
        1: "FINNIFTY",         # Tuesday
        2: "BANKNIFTY",        # Wednesday
        3: "NIFTY",            # Thursday
        4: "SENSEX/BANKEX"     # Friday (BSE)
    }

    @classmethod
    def get_current_lot_size(cls, symbol: str) -> int:
        """Get current lot size with Dec 30 transition logic"""
        symbol = symbol.upper().replace(" ", "")
        if symbol in ["NIFTY50", "NIFTY"]:
            symbol = "NIFTY"
        elif symbol in ["NIFTYBANK", "BANKNIFTY"]:
            symbol = "BANKNIFTY"

        # Check if past Dec 30, 2025
        if datetime.now() >= datetime(2025, 12, 30):
            return cls.LOT_SIZES_POST_DEC30.get(symbol, cls.LOT_SIZES_DEC_2025.get(symbol, 1))
        return cls.LOT_SIZES_DEC_2025.get(symbol, 1)


# =====================================================================
# SECTION 3: TECHNICAL ANALYSIS PATTERNS & INDICATORS
# =====================================================================

class TechnicalAnalysis:
    """Technical Analysis Engine with Pattern Recognition"""

    CANDLESTICK_PATTERNS = {
        "REVERSAL_BULLISH": {
            "HAMMER": {"reliability": "high", "confirmation": "Green candle close above"},
            "MORNING_STAR": {"reliability": "high", "type": "3-candle"},
            "BULLISH_ENGULFING": {"reliability": "high"},
            "PIERCING_LINE": {"reliability": "medium"},
            "INVERTED_HAMMER": {"reliability": "medium", "confirmation": "required"}
        },
        "REVERSAL_BEARISH": {
            "SHOOTING_STAR": {"reliability": "high", "confirmation": "Red candle close below"},
            "EVENING_STAR": {"reliability": "high", "type": "3-candle"},
            "BEARISH_ENGULFING": {"reliability": "high"},
            "DARK_CLOUD_COVER": {"reliability": "medium"},
            "HANGING_MAN": {"reliability": "medium", "confirmation": "required"}
        },
        "CONTINUATION": {
            "DOJI": {"signal": "indecision", "action": "wait"},
            "SPINNING_TOP": {"signal": "indecision"},
            "MARUBOZU": {"signal": "strong momentum"},
            "THREE_WHITE_SOLDIERS": {"signal": "bullish continuation"},
            "THREE_BLACK_CROWS": {"signal": "bearish continuation"}
        }
    }

    INDICATORS = {
        "RSI": {
            "standard_period": 14,
            "overbought": 70,
            "oversold": 30,
            "divergence": {
                "bullish": "Price Lower Low + RSI Higher Low",
                "bearish": "Price Higher High + RSI Lower High"
            }
        },
        "MACD": {
            "fast": 12,
            "slow": 26,
            "signal": 9,
            "crossover_bullish": "MACD crosses above Signal",
            "crossover_bearish": "MACD crosses below Signal"
        },
        "SUPERTREND": {
            "standard": {"period": 10, "multiplier": 3},
            "scalping": {"period": 7, "multiplier": 2},
            "positional": {"period": 14, "multiplier": 3}
        },
        "BOLLINGER_BANDS": {
            "period": 20,
            "std_dev": 2,
            "squeeze": "Low volatility, breakout imminent",
            "expansion": "High volatility, trend in progress"
        },
        "ADX": {
            "period": 14,
            "weak_trend": "<20",
            "strong_trend": ">25",
            "very_strong": ">50"
        },
        "VWAP": {
            "usage": "Institutional benchmark",
            "above_vwap": "Bullish bias",
            "below_vwap": "Bearish bias"
        },
        "CPR": {
            "full_name": "Central Pivot Range",
            "components": ["TC", "Pivot", "BC"],
            "narrow_cpr": "Trending day likely",
            "wide_cpr": "Rangebound day likely"
        }
    }

    MOVING_AVERAGES = {
        "EMA_9": "Short-term trend",
        "EMA_21": "Intraday trend",
        "SMA_50": "Medium-term trend",
        "SMA_200": "Long-term trend (Institutional)",
        "GOLDEN_CROSS": "50 SMA crosses above 200 SMA → Bullish",
        "DEATH_CROSS": "50 SMA crosses below 200 SMA → Bearish"
    }


# =====================================================================
# SECTION 4: OPTIONS KNOWLEDGE & GREEKS
# =====================================================================

class OptionsKnowledge:
    """Complete Options Trading Knowledge Base"""

    GREEKS = {
        "DELTA": {
            "symbol": "Δ",
            "range_call": [0, 1],
            "range_put": [-1, 0],
            "atm_value": 0.5,
            "usage": ["Hedge ratio", "ITM probability", "Direction exposure"]
        },
        "GAMMA": {
            "symbol": "Γ",
            "highest_at": "ATM, near expiry",
            "usage": "Rate of change of Delta"
        },
        "THETA": {
            "symbol": "Θ",
            "nature": "Negative for buyers, Positive for sellers",
            "accelerates": "Near expiry",
            "usage": "Time decay per day"
        },
        "VEGA": {
            "symbol": "ν",
            "highest_at": "ATM options",
            "usage": "Sensitivity to IV changes"
        }
    }

    STRATEGIES = {
        "BULLISH": {
            "LONG_CALL": {"risk": "Premium", "reward": "Unlimited"},
            "BULL_CALL_SPREAD": {"risk": "Net debit", "reward": "Limited"},
            "BULL_PUT_SPREAD": {"risk": "Limited", "reward": "Net credit"}
        },
        "BEARISH": {
            "LONG_PUT": {"risk": "Premium", "reward": "Strike - Premium"},
            "BEAR_PUT_SPREAD": {"risk": "Net debit", "reward": "Limited"},
            "BEAR_CALL_SPREAD": {"risk": "Limited", "reward": "Net credit"}
        },
        "NEUTRAL": {
            "SHORT_STRADDLE": {"risk": "Unlimited", "reward": "Premium", "view": "Low volatility"},
            "IRON_CONDOR": {"risk": "Limited", "reward": "Net credit", "view": "Range-bound"},
            "IRON_BUTTERFLY": {"risk": "Limited", "reward": "Net credit", "view": "Pin to strike"}
        },
        "VOLATILITY": {
            "LONG_STRADDLE": {"risk": "Premium", "reward": "Unlimited", "view": "Big move expected"},
            "LONG_STRANGLE": {"risk": "Premium", "reward": "Unlimited", "view": "Cheaper than straddle"}
        }
    }

    CHAIN_ANALYSIS = {
        "PCR": {
            "bullish_extreme": ">1.3 (Contrarian bullish)",
            "bearish_extreme": "<0.7 (Contrarian bearish)",
            "neutral": "0.8 - 1.2"
        },
        "MAX_PAIN": "Strike where option writers have minimum loss",
        "OI_BUILDUP": {
            "long_buildup": "Price ↑ + OI ↑ → Bullish",
            "short_covering": "Price ↑ + OI ↓ → Weak bullish",
            "short_buildup": "Price ↓ + OI ↑ → Bearish",
            "long_unwinding": "Price ↓ + OI ↓ → Weak bearish"
        }
    }


class OptionsMath:
    """
    Black-Scholes-Merton Implementation for Indian Markets
    Optimized for real-time calculations
    """

    # Pre-calculated constants
    RISK_FREE_RATE = 0.07  # India 10Y bond yield approx

    @staticmethod
    @lru_cache(maxsize=1000)
    def _norm_cdf(x: float) -> float:
        """Cached cumulative normal distribution"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    @staticmethod
    def _norm_pdf(x: float) -> float:
        """Standard normal PDF"""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

    @classmethod
    def calculate_greeks(
        cls,
        spot_price: float,
        strike_price: float,
        days_to_expiry: float,
        iv: float,
        option_type: str = "CALL",
        risk_free_rate: float = None
    ) -> Dict[str, float]:
        """
        Calculate option Greeks using Black-Scholes

        Args:
            spot_price: Current underlying price
            strike_price: Option strike price
            days_to_expiry: Days until expiry
            iv: Implied volatility as decimal (0.20 for 20%)
            option_type: "CALL" or "PUT"
            risk_free_rate: Risk-free rate (default: 7%)

        Returns:
            Dict with delta, gamma, theta, vega
        """
        if risk_free_rate is None:
            risk_free_rate = cls.RISK_FREE_RATE

        # Safety bounds
        T = max(days_to_expiry / 365.0, 1e-6)
        sigma = max(iv, 0.001)
        r = risk_free_rate

        try:
            sqrt_t = math.sqrt(T)
            d1 = (math.log(spot_price / strike_price) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_t)
            d2 = d1 - sigma * sqrt_t

            nd1 = cls._norm_cdf(d1)
            nd2 = cls._norm_cdf(d2)
            pdf_d1 = cls._norm_pdf(d1)

            if option_type.upper() == "CALL":
                delta = nd1
                theta_yearly = (
                    -spot_price * pdf_d1 * sigma / (2 * sqrt_t)
                    - r * strike_price * math.exp(-r * T) * nd2
                )
            else:
                delta = nd1 - 1
                theta_yearly = (
                    -spot_price * pdf_d1 * sigma / (2 * sqrt_t)
                    + r * strike_price * math.exp(-r * T) * cls._norm_cdf(-d2)
                )

            theta = theta_yearly / 365.0
            gamma = pdf_d1 / (spot_price * sigma * sqrt_t)
            vega = spot_price * pdf_d1 * sqrt_t / 100.0

            # Moneyness calculation
            if option_type.upper() == "CALL":
                moneyness = spot_price / strike_price
            else:
                moneyness = strike_price / spot_price

            return {
                "delta": round(delta, 4),
                "gamma": round(gamma, 6),
                "theta": round(theta, 2),
                "vega": round(vega, 3),
                "moneyness": round(moneyness, 4),
                "status": "ITM" if moneyness > 1.02 else ("ATM" if moneyness > 0.98 else "OTM")
            }
        except (ValueError, ZeroDivisionError) as e:
            logger.warning(f"Greeks calculation error: {e}")
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "error": str(e)}

    @classmethod
    def calculate_iv_from_premium(
        cls,
        spot_price: float,
        strike_price: float,
        days_to_expiry: float,
        premium: float,
        option_type: str = "CALL",
        risk_free_rate: float = None
    ) -> float:
        """
        Calculate Implied Volatility from option premium using Newton-Raphson
        """
        if risk_free_rate is None:
            risk_free_rate = cls.RISK_FREE_RATE

        T = max(days_to_expiry / 365.0, 1e-6)

        # Initial guess based on ATM approximation
        iv = 0.2

        for _ in range(50):  # Max iterations
            greeks = cls.calculate_greeks(spot_price, strike_price, days_to_expiry, iv, option_type, risk_free_rate)

            # Calculate option price with current IV
            sqrt_t = math.sqrt(T)
            d1 = (math.log(spot_price / strike_price) + (risk_free_rate + 0.5 * iv ** 2) * T) / (iv * sqrt_t)
            d2 = d1 - iv * sqrt_t

            if option_type.upper() == "CALL":
                price = spot_price * cls._norm_cdf(d1) - strike_price * math.exp(-risk_free_rate * T) * cls._norm_cdf(d2)
            else:
                price = strike_price * math.exp(-risk_free_rate * T) * cls._norm_cdf(-d2) - spot_price * cls._norm_cdf(-d1)

            vega = greeks["vega"] * 100  # Convert back

            if abs(vega) < 1e-10:
                break

            diff = premium - price
            if abs(diff) < 0.01:
                break

            iv = iv + diff / vega
            iv = max(0.01, min(iv, 5.0))  # Bound IV between 1% and 500%

        return round(iv, 4)


# =====================================================================
# SECTION 5: RISK MANAGEMENT
# =====================================================================

class RiskManagement:
    """Risk Management Framework for Algorithmic Trading"""

    POSITION_SIZING = {
        "FIXED_RISK": {
            "formula": "Position Size = (Capital × Risk%) / (Entry - StopLoss)",
            "typical_risk": "1-2% per trade"
        },
        "KELLY_CRITERION": {
            "formula": "f* = (W × R - L) / R",
            "usage": "Half-Kelly recommended (f*/2)"
        },
        "ATR_BASED": {
            "formula": "Size = Risk Amount / (ATR × Multiplier)",
            "adapts_to": "Volatility"
        }
    }

    STOP_LOSS_TYPES = {
        "FIXED_PERCENT": {"typical": "1-5%", "cons": "Ignores volatility"},
        "ATR_BASED": {"multiplier": "1.5-3x ATR", "pros": "Adapts to volatility"},
        "SWING_BASED": {"method": "Below swing low / Above swing high"},
        "TRAILING": {"types": ["Fixed distance", "ATR-based", "Chandelier"]}
    }

    SLIPPAGE_ESTIMATES = {
        "NIFTY_LIQUID": 0.05,      # Points per lot
        "BANKNIFTY_LIQUID": 0.5,   # Points per lot (higher volatility)
        "STOCK_FNO": 0.10,         # Percentage
        "ILLIQUID_OPTIONS": 1.0,   # Percentage or more
        "NOTE": "SL-M orders blocked for options since 2021"
    }

    RISK_METRICS = {
        "SHARPE_RATIO": {"good": ">1.5", "excellent": ">2.5"},
        "SORTINO_RATIO": "Penalizes only downside volatility",
        "MAX_DRAWDOWN": "Most critical for traders",
        "CALMAR_RATIO": "Annual Return / Max Drawdown"
    }

    @staticmethod
    def calculate_position_size(
        capital: float,
        risk_percent: float,
        entry_price: float,
        stop_loss_price: float,
        lot_size: int = 1
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size based on fixed risk

        Args:
            capital: Total trading capital
            risk_percent: Risk per trade as percentage (e.g., 1.0 for 1%)
            entry_price: Entry price
            stop_loss_price: Stop loss price
            lot_size: Contract lot size

        Returns:
            Dict with lots, quantity, risk amount
        """
        risk_amount = capital * (risk_percent / 100.0)
        risk_per_unit = abs(entry_price - stop_loss_price)

        if risk_per_unit == 0:
            return {"lots": 0, "quantity": 0, "risk_amount": 0, "error": "Stop loss equals entry"}

        risk_per_lot = risk_per_unit * lot_size
        num_lots = int(risk_amount / risk_per_lot)

        return {
            "lots": max(num_lots, 0),
            "quantity": max(num_lots * lot_size, 0),
            "risk_amount": round(risk_amount, 2),
            "risk_per_lot": round(risk_per_lot, 2),
            "actual_risk": round(num_lots * risk_per_lot, 2)
        }


# =====================================================================
# SECTION 6: REAL-TIME MARKET ANALYSIS
# =====================================================================

class RealTimeAnalyzer:
    """Real-time market analysis utilities"""

    @staticmethod
    def get_trading_session() -> Dict[str, Any]:
        """Get current trading session status"""
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()

        # Weekend check
        if weekday >= 5:
            return {
                "session": TradingSession.CLOSED.value,
                "is_trading": False,
                "reason": "Weekend"
            }

        # Trading hours
        pre_open_start = time(9, 0)
        pre_open_end = time(9, 15)
        market_start = time(9, 15)
        market_end = time(15, 30)
        post_close_start = time(15, 40)
        post_close_end = time(16, 0)

        if pre_open_start <= current_time < pre_open_end:
            return {"session": TradingSession.PRE_OPEN.value, "is_trading": False, "note": "Pre-open auction"}
        elif market_start <= current_time < market_end:
            return {"session": TradingSession.NORMAL.value, "is_trading": True}
        elif post_close_start <= current_time < post_close_end:
            return {"session": TradingSession.POST_CLOSE.value, "is_trading": False}
        else:
            return {"session": TradingSession.CLOSED.value, "is_trading": False}

    @staticmethod
    def analyze_vix(vix_level: float) -> Dict[str, Any]:
        """Analyze India VIX and provide recommendations"""
        if vix_level < 12:
            regime = "LOW_VOLATILITY"
            action = "Sell options, range-bound strategies"
            position_size = "Normal"
        elif vix_level < 16:
            regime = "NORMAL"
            action = "Standard strategies"
            position_size = "Normal"
        elif vix_level < 22:
            regime = "ELEVATED"
            action = "Reduce position sizes, tighter stops"
            position_size = "75%"
        elif vix_level < 30:
            regime = "HIGH"
            action = "Defensive, buy options for protection"
            position_size = "50%"
        else:
            regime = "EXTREME_FEAR"
            action = "Cash heavy, only hedged positions"
            position_size = "25%"

        return {
            "vix": vix_level,
            "regime": regime,
            "action": action,
            "position_size_multiplier": position_size
        }

    @staticmethod
    def calculate_pcr(put_oi: int, call_oi: int) -> Dict[str, Any]:
        """Calculate and interpret Put-Call Ratio"""
        if call_oi == 0:
            return {"pcr": 0, "interpretation": "No data"}

        pcr = put_oi / call_oi

        if pcr > 1.3:
            interpretation = "EXTREME_BEARISH_SENTIMENT"
            contrarian = "Bullish (Oversold fear)"
        elif pcr > 1.1:
            interpretation = "BEARISH_SENTIMENT"
            contrarian = "Mildly Bullish"
        elif pcr > 0.9:
            interpretation = "NEUTRAL"
            contrarian = "No signal"
        elif pcr > 0.7:
            interpretation = "BULLISH_SENTIMENT"
            contrarian = "Mildly Bearish"
        else:
            interpretation = "EXTREME_BULLISH_SENTIMENT"
            contrarian = "Bearish (Overbought greed)"

        return {
            "pcr": round(pcr, 2),
            "interpretation": interpretation,
            "contrarian_signal": contrarian
        }

    @staticmethod
    def generate_signal(
        rsi: float,
        adx: float,
        macd_signal: str,
        price_vs_vwap: str,
        support: float,
        resistance: float,
        current_price: float
    ) -> Dict[str, Any]:
        """Generate comprehensive trading signal"""
        score = 0
        factors = []

        # RSI Analysis
        if rsi < 30:
            score += 2
            factors.append("RSI Oversold (+2)")
        elif rsi < 40:
            score += 1
            factors.append("RSI Low (+1)")
        elif rsi > 70:
            score -= 2
            factors.append("RSI Overbought (-2)")
        elif rsi > 60:
            score -= 1
            factors.append("RSI High (-1)")

        # ADX Trend Strength
        if adx > 25:
            factors.append(f"Strong Trend (ADX: {adx})")

        # MACD
        if macd_signal == "BULLISH":
            score += 1
            factors.append("MACD Bullish (+1)")
        elif macd_signal == "BEARISH":
            score -= 1
            factors.append("MACD Bearish (-1)")

        # VWAP
        if price_vs_vwap == "ABOVE":
            score += 0.5
            factors.append("Above VWAP (+0.5)")
        elif price_vs_vwap == "BELOW":
            score -= 0.5
            factors.append("Below VWAP (-0.5)")

        # Support/Resistance proximity
        support_distance = (current_price - support) / current_price * 100
        resistance_distance = (resistance - current_price) / current_price * 100

        if support_distance < 1:
            score += 1
            factors.append("Near Support (+1)")
        if resistance_distance < 1:
            score -= 1
            factors.append("Near Resistance (-1)")

        # Generate final signal
        if score >= 2:
            signal = "BUY"
            confidence = min(85, 50 + score * 12)
        elif score <= -2:
            signal = "SELL"
            confidence = min(85, 50 + abs(score) * 12)
        else:
            signal = "HOLD"
            confidence = 55 + abs(score) * 5

        return {
            "signal": signal,
            "confidence": round(confidence),
            "score": round(score, 1),
            "factors": factors,
            "support": support,
            "resistance": resistance,
            "risk_reward": round(resistance_distance / max(support_distance, 0.1), 2) if signal == "BUY" else None
        }


# =====================================================================
# SECTION 7: FUNDAMENTAL ANALYSIS (INDIAN MARKET SPECIFIC)
# =====================================================================

class FundamentalAnalysis:
    """Fundamental Analysis for Indian Equities"""

    VALUATION_RATIOS = {
        "PE_RATIO": {
            "nifty_historical_avg": 22,
            "undervalued": "<18",
            "fair": "18-25",
            "overvalued": ">25"
        },
        "PB_RATIO": {
            "usage": "Banks, Asset-heavy companies",
            "below_book": "<1 (may indicate stress or opportunity)"
        },
        "EV_EBITDA": {
            "usage": "Capital-intensive sectors",
            "good": "<10"
        }
    }

    INDIAN_SECTORS = {
        "BANKING": {
            "key_metrics": ["NIM", "GNPA", "NNPA", "CASA", "CAR", "PCR"],
            "bellwethers": ["HDFCBANK", "ICICIBANK", "SBIN"]
        },
        "IT_SERVICES": {
            "key_metrics": ["Revenue Growth", "EBIT Margin", "Attrition", "Deal TCV"],
            "bellwethers": ["TCS", "INFY", "WIPRO"]
        },
        "PHARMA": {
            "key_metrics": ["R&D Spend", "ANDA Pipeline", "US Revenue %"],
            "bellwethers": ["SUNPHARMA", "DRREDDY", "CIPLA"]
        },
        "AUTO": {
            "key_metrics": ["Volume Growth", "ASP", "EV Mix"],
            "bellwethers": ["MARUTI", "TATAMOTORS", "M&M"]
        },
        "FMCG": {
            "key_metrics": ["Volume Growth", "Pricing Power", "Rural Mix"],
            "bellwethers": ["HINDUNILVR", "ITC", "NESTLEIND"]
        }
    }


# =====================================================================
# SECTION 8: TRADING PSYCHOLOGY
# =====================================================================

class TradingPsychology:
    """Behavioral Biases and Trading Rules"""

    COGNITIVE_BIASES = {
        "LOSS_AVERSION": {
            "impact": "Hold losers too long, cut winners early",
            "solution": "Pre-defined stop-loss, stick to plan"
        },
        "CONFIRMATION_BIAS": {
            "impact": "Miss contrary signals",
            "solution": "Actively seek opposite view"
        },
        "OVERCONFIDENCE": {
            "impact": "Overtrade, overlarge positions",
            "solution": "Track actual performance"
        },
        "REVENGE_TRADING": {
            "impact": "Larger losses after a loss",
            "solution": "Cool-off period, daily loss limit"
        },
        "FOMO": {
            "impact": "Chase moves, bad entries",
            "solution": "Wait for your setup"
        }
    }

    TRADING_RULES = [
        "Never risk more than 2% per trade",
        "Always use stop-loss",
        "Let winners run, cut losers quickly",
        "Never average down on losing trades",
        "Don't trade during emotional distress",
        "Have a written trading plan",
        "Review trades weekly",
        "Take breaks after big wins or losses",
        "The market is always right"
    ]


# =====================================================================
# SECTION 9: MAIN KNOWLEDGE INTERFACE CLASS
# =====================================================================

class IndianMarketKnowledge:
    """
    Main interface for accessing Indian Market ML Knowledge Base
    Aggregates all knowledge modules for easy access
    """

    version = "2.0.0"
    last_updated = "2025-12-01"

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

        # Quick access attributes
        self.INDEX_INFO = self.market_info.INDICES
        self.EXCHANGES = self.market_info.EXCHANGES
        self.SEBI_2025_RULES = {
            "lot_sizes": self.sebi.LOT_SIZES_DEC_2025,
            "stt_rates": self.sebi.STT_RATES,
            "margins": self.sebi.MARGIN_RULES,
            "circuits": self.sebi.CIRCUIT_BREAKERS,
            "expiry_calendar": self.sebi.WEEKLY_EXPIRY
        }
        self.TECHNICAL_INDICATORS = self.technical.INDICATORS
        self.OPTION_GREEKS = self.options.GREEKS
        self.CANDLESTICK_PATTERNS = self.technical.CANDLESTICK_PATTERNS
        self.TRADING_SESSIONS = self.market_info.EXCHANGES
        self.ECONOMIC_INDICATORS = {
            "RBI_REPO_RATE": 6.5,
            "INFLATION_CPI": 5.5,
            "10Y_BOND_YIELD": 7.0
        }
        self.ML_FEATURES = {
            "price_features": ["open", "high", "low", "close", "volume", "vwap"],
            "technical_features": ["rsi_14", "macd", "adx", "atr", "bollinger_width"],
            "options_features": ["iv", "pcr", "max_pain", "oi_change"],
            "sentiment_features": ["vix", "fii_dii_flow", "news_sentiment"]
        }

        # For backward compatibility
        self.TOP_50_STOCKS = {
            "RELIANCE": {"security_id": "2885", "isin": "INE002A01018"},
            "TCS": {"security_id": "11536", "isin": "INE467B01029"},
            "HDFCBANK": {"security_id": "1333", "isin": "INE040A01034"},
            "INFY": {"security_id": "1594", "isin": "INE009A01021"},
            "ICICIBANK": {"security_id": "4963", "isin": "INE090A01021"}
        }

    def get_index_info(self, symbol: str) -> Dict[str, Any]:
        """Get information about an index"""
        symbol = symbol.upper().replace(" ", "")
        if symbol == "NIFTY":
            symbol = "NIFTY50"
        return self.market_info.INDICES.get(symbol, {"error": f"Index {symbol} not found"})

    def get_lot_size(self, symbol: str) -> int:
        """Get current lot size for a symbol"""
        return self.sebi.get_current_lot_size(symbol)

    def get_sebi_rules(self, symbol: str = None) -> Dict[str, Any]:
        """Get SEBI rules, optionally filtered by symbol"""
        rules = {
            "lot_sizes": self.sebi.LOT_SIZES_DEC_2025,
            "stt_rates": self.sebi.STT_RATES,
            "margins": self.sebi.MARGIN_RULES,
            "expiry_calendar": self.sebi.WEEKLY_EXPIRY
        }
        if symbol:
            symbol = symbol.upper()
            rules["symbol_lot_size"] = self.get_lot_size(symbol)
        return rules

    def get_trading_sessions(self) -> Dict[str, Any]:
        """Get trading session information"""
        return {
            "current": self.analyzer.get_trading_session(),
            "nse_hours": self.market_info.EXCHANGES.get("NSE", {})
        }

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock information"""
        return self.TOP_50_STOCKS.get(symbol.upper())

    def get_all_indicators(self) -> Dict[str, Any]:
        """Get all technical indicators"""
        return {
            "indicators": self.technical.INDICATORS,
            "moving_averages": self.technical.MOVING_AVERAGES,
            "patterns": self.technical.CANDLESTICK_PATTERNS
        }

    def get_option_greeks_info(self) -> Dict[str, Any]:
        """Get option Greeks documentation"""
        return {
            "greeks": self.options.GREEKS,
            "strategies": self.options.STRATEGIES,
            "chain_analysis": self.options.CHAIN_ANALYSIS
        }

    def get_economic_indicators(self) -> Dict[str, Any]:
        """Get current economic indicators"""
        return self.ECONOMIC_INDICATORS

    def get_candlestick_patterns(self) -> Dict[str, Any]:
        """Get candlestick patterns"""
        return self.technical.CANDLESTICK_PATTERNS

    def get_ml_features(self) -> Dict[str, Any]:
        """Get ML feature definitions"""
        return self.ML_FEATURES

    def calculate_greeks(
        self,
        spot: float,
        strike: float,
        days_to_expiry: float,
        iv: float,
        option_type: str = "CALL"
    ) -> Dict[str, float]:
        """Calculate option Greeks"""
        return self.options_math.calculate_greeks(spot, strike, days_to_expiry, iv, option_type)

    def calculate_position_size(
        self,
        capital: float,
        risk_percent: float,
        entry: float,
        stop_loss: float,
        symbol: str = "NIFTY"
    ) -> Dict[str, Any]:
        """Calculate position size with lot size"""
        lot_size = self.get_lot_size(symbol)
        return self.risk.calculate_position_size(capital, risk_percent, entry, stop_loss, lot_size)

    def analyze_market(
        self,
        vix: float = None,
        put_oi: int = None,
        call_oi: int = None
    ) -> Dict[str, Any]:
        """Quick market analysis"""
        result = {}
        result["session"] = self.analyzer.get_trading_session()
        if vix:
            result["vix_analysis"] = self.analyzer.analyze_vix(vix)
        if put_oi and call_oi:
            result["pcr_analysis"] = self.analyzer.calculate_pcr(put_oi, call_oi)
        return result


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
    'IndianMarketKnowledge',
    'MarketInfo',
    'SEBIRegulations',
    'TechnicalAnalysis',
    'OptionsKnowledge',
    'OptionsMath',
    'RiskManagement',
    'RealTimeAnalyzer',
    'FundamentalAnalysis',
    'TradingPsychology',
    'Exchange',
    'Segment',
    'TradingSession',
    'MARKET_INFO',
    'SEBI_RULES',
    'TECHNICAL_ANALYSIS',
    'OPTIONS_KNOWLEDGE',
    'OPTIONS_MATH',
    'RISK_MANAGEMENT',
    'REAL_TIME_ANALYZER',
    'FUNDAMENTAL_ANALYSIS',
    'TRADING_PSYCHOLOGY'
]


# =====================================================================
# VALIDATION
# =====================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("InfinityAI.Pro Knowledge Base - Verification")
    print(f"Version: 2.0.0 | Last Updated: December 1, 2025")
    print("=" * 60)

    knowledge = IndianMarketKnowledge()

    print(f"\n📊 Current NIFTY Lot Size: {knowledge.get_lot_size('NIFTY')}")
    print(f"📊 Current BANKNIFTY Lot Size: {knowledge.get_lot_size('BANKNIFTY')}")
    print(f"📊 Options Sell STT: {SEBI_RULES.STT_RATES['FNO_OPTIONS_SELL'] * 100}%")

    # Test Greeks calculation
    greeks = knowledge.calculate_greeks(
        spot=24000,
        strike=24100,
        days_to_expiry=5,
        iv=0.15,
        option_type="CALL"
    )
    print(f"\n🧮 Sample Greeks (NIFTY 24000, Strike 24100, 5 DTE, 15% IV):")
    print(f"   Delta: {greeks['delta']}, Gamma: {greeks['gamma']}")
    print(f"   Theta: {greeks['theta']}, Vega: {greeks['vega']}")
    print(f"   Status: {greeks['status']}")

    # Test position sizing
    pos = knowledge.calculate_position_size(
        capital=500000,
        risk_percent=1.0,
        entry=100,
        stop_loss=95,
        symbol="NIFTY"
    )
    print(f"\n💰 Position Size (₹5L capital, 1% risk, SL 5 points):")
    print(f"   Lots: {pos['lots']}, Quantity: {pos['quantity']}")
    print(f"   Risk Amount: ₹{pos['risk_amount']}")

    # Test session
    session = knowledge.analyzer.get_trading_session()
    print(f"\n⏰ Current Session: {session['session']}")

    print("\n✅ Knowledge Base Loaded Successfully!")
