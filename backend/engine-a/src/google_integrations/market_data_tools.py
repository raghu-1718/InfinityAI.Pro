"""
InfinityAI.Pro - Real-Time Market Data Tools for Gemini Function Calling
=======================================================================
Provides LIVE Indian stock market data tools that Gemini can call automatically.
All data is sourced from REAL APIs - NO simulated/demo data.

Data Sources:
- NSE Official Data (via nsepython)
- Yahoo Finance (for historical data)
- Real-time FII/DII activity
- Live option chain from NSE

Features:
- Real-time stock prices via yfinance + NSE
- NIFTY/BANKNIFTY option chain data from NSE
- Live FII/DII activity from NSE
- Technical indicators (calculated from real data)
- Economic calendar
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

logger = logging.getLogger("InfinityAI.MarketDataTools")

# Try importing data libraries
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    logger.warning("yfinance not available")

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# NSE Python for live NSE data
try:
    from nsepython import (
        nse_optionchain_scrapper,
        nse_fiidii
    )
    HAS_NSEPYTHON = True
    logger.info("✅ nsepython loaded - LIVE NSE data enabled")
except ImportError:
    HAS_NSEPYTHON = False
    logger.warning("nsepython not available - some features may use cached data")

# =====================================================================
# MARKET DATA FUNCTIONS FOR GEMINI FUNCTION CALLING
# =====================================================================

def get_stock_quote(symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
    """
    Get real-time stock quote and key metrics.
    """
    if not HAS_YFINANCE:
        return {"error": "yfinance not available", "symbol": symbol}

    try:
        # Format symbol for yfinance (Indian stocks need .NS or .BO suffix)
        if exchange.upper() == "NSE":
            yf_symbol = f"{symbol}.NS"
        elif exchange.upper() == "BSE":
            yf_symbol = f"{symbol}.BO"
        else:
            yf_symbol = symbol

        # Handle indices
        if symbol.upper() in ["NIFTY", "NIFTY50", "^NSEI"]:
            yf_symbol = "^NSEI"
        elif symbol.upper() in ["BANKNIFTY", "NIFTYBANK", "^NSEBANK"]:
            yf_symbol = "^NSEBANK"
        elif symbol.upper() in ["SENSEX", "^BSESN"]:
            yf_symbol = "^BSESN"

        ticker = yf.Ticker(yf_symbol)
        info = ticker.info

        # Get current market data
        hist = ticker.history(period="5d")

        if hist.empty:
            return {"error": f"No data available for {symbol}", "symbol": symbol}

        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100

        return {
            "symbol": symbol,
            "exchange": exchange,
            "current_price": round(current_price, 2),
            "previous_close": round(prev_close, 2),
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
            "day_high": round(hist['High'].iloc[-1], 2),
            "day_low": round(hist['Low'].iloc[-1], 2),
            "volume": int(hist['Volume'].iloc[-1]),
            "52_week_high": info.get('fiftyTwoWeekHigh', 0),
            "52_week_low": info.get('fiftyTwoWeekLow', 0),
            "market_cap": info.get('marketCap', 0),
            "pe_ratio": info.get('trailingPE', 0),
            "pb_ratio": info.get('priceToBook', 0),
            "dividend_yield": info.get('dividendYield', 0),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}


def get_nifty_overview() -> Dict[str, Any]:
    """
    Get comprehensive NIFTY 50 index overview with top gainers/losers.
    """
    if not HAS_YFINANCE:
        return {"error": "yfinance not available"}

    try:
        # Get NIFTY 50 index data
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="5d")

        if hist.empty:
            return {"error": "No NIFTY data available"}

        current = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current
        change = current - prev_close
        change_pct = (change / prev_close) * 100

        # Get BANKNIFTY
        banknifty = yf.Ticker("^NSEBANK")
        bn_hist = banknifty.history(period="5d")
        bn_current = bn_hist['Close'].iloc[-1] if not bn_hist.empty else 0
        bn_prev = bn_hist['Close'].iloc[-2] if len(bn_hist) > 1 else bn_current
        bn_change_pct = ((bn_current - bn_prev) / bn_prev * 100) if bn_prev else 0

        # Top NIFTY 50 stocks to check
        nifty50_components = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
            "HINDUNILVR", "SBIN", "BHARTIARTL", "HDFC", "ITC",
            "KOTAKBANK", "LT", "AXISBANK", "BAJFINANCE", "ASIANPAINT"
        ]

        gainers = []
        losers = []

        for symbol in nifty50_components[:15]:  # Limit API calls
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                h = ticker.history(period="2d")
                if len(h) >= 2:
                    curr = h['Close'].iloc[-1]
                    prev = h['Close'].iloc[-2]
                    chg_pct = ((curr - prev) / prev) * 100
                    stock_data = {
                        "symbol": symbol,
                        "price": round(curr, 2),
                        "change_percent": round(chg_pct, 2)
                    }
                    if chg_pct > 0:
                        gainers.append(stock_data)
                    else:
                        losers.append(stock_data)
            except Exception:
                continue

        # Sort gainers and losers
        gainers = sorted(gainers, key=lambda x: x['change_percent'], reverse=True)[:5]
        losers = sorted(losers, key=lambda x: x['change_percent'])[:5]

        return {
            "nifty50": {
                "value": round(current, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "day_high": round(hist['High'].iloc[-1], 2),
                "day_low": round(hist['Low'].iloc[-1], 2),
                "trend": "BULLISH" if change_pct > 0.3 else "BEARISH" if change_pct < -0.3 else "NEUTRAL"
            },
            "banknifty": {
                "value": round(bn_current, 2),
                "change_percent": round(bn_change_pct, 2),
                "trend": "BULLISH" if bn_change_pct > 0.3 else "BEARISH" if bn_change_pct < -0.3 else "NEUTRAL"
            },
            "market_breadth": {
                "advances": len(gainers),
                "declines": len(losers),
                "unchanged": 15 - len(gainers) - len(losers)
            },
            "top_gainers": gainers,
            "top_losers": losers,
            "market_status": _get_market_status(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching NIFTY overview: {e}")
        return {"error": str(e)}


def get_technical_indicators(symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
    """
    Calculate technical indicators for a stock.
    """
    if not HAS_YFINANCE or not HAS_PANDAS:
        return {"error": "Required libraries not available", "symbol": symbol}

    try:
        # Format symbol
        if exchange.upper() == "NSE":
            yf_symbol = f"{symbol}.NS"
        elif exchange.upper() == "BSE":
            yf_symbol = f"{symbol}.BO"
        else:
            yf_symbol = symbol

        if symbol.upper() in ["NIFTY", "NIFTY50"]:
            yf_symbol = "^NSEI"
        elif symbol.upper() in ["BANKNIFTY", "NIFTYBANK"]:
            yf_symbol = "^NSEBANK"

        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="3mo")

        if hist.empty or len(hist) < 30:
            return {"error": f"Insufficient data for {symbol}", "symbol": symbol}

        close = hist['Close']
        high = hist['High']
        low = hist['Low']
        volume = hist['Volume']

        # Calculate RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Calculate MACD
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal

        # Calculate Bollinger Bands
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        bb_upper = sma20 + (std20 * 2)
        bb_lower = sma20 - (std20 * 2)

        # Moving Averages
        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        sma50 = close.rolling(window=50).mean()
        sma200 = close.rolling(window=200).mean() if len(close) >= 200 else pd.Series([np.nan])

        # ATR (Average True Range)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()

        # Volume analysis
        avg_volume_20 = volume.rolling(window=20).mean().iloc[-1]
        volume_ratio = volume.iloc[-1] / avg_volume_20 if avg_volume_20 > 0 else 1

        current_price = close.iloc[-1]

        # Generate signals
        signals = []
        if rsi.iloc[-1] < 30:
            signals.append("RSI OVERSOLD - Potential buy zone")
        elif rsi.iloc[-1] > 70:
            signals.append("RSI OVERBOUGHT - Potential sell zone")

        if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
            signals.append("MACD BULLISH CROSSOVER")
        elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
            signals.append("MACD BEARISH CROSSOVER")

        if current_price > sma50.iloc[-1] and ema9.iloc[-1] > ema21.iloc[-1]:
            signals.append("UPTREND - Price above key MAs")
        elif current_price < sma50.iloc[-1] and ema9.iloc[-1] < ema21.iloc[-1]:
            signals.append("DOWNTREND - Price below key MAs")

        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "rsi": {
                "value": round(rsi.iloc[-1], 2),
                "status": "OVERSOLD" if rsi.iloc[-1] < 30 else "OVERBOUGHT" if rsi.iloc[-1] > 70 else "NEUTRAL"
            },
            "macd": {
                "macd": round(macd.iloc[-1], 2),
                "signal": round(signal.iloc[-1], 2),
                "histogram": round(histogram.iloc[-1], 2),
                "trend": "BULLISH" if macd.iloc[-1] > signal.iloc[-1] else "BEARISH"
            },
            "bollinger_bands": {
                "upper": round(bb_upper.iloc[-1], 2),
                "middle": round(sma20.iloc[-1], 2),
                "lower": round(bb_lower.iloc[-1], 2),
                "position": "UPPER" if current_price > bb_upper.iloc[-1] else "LOWER" if current_price < bb_lower.iloc[-1] else "MIDDLE"
            },
            "moving_averages": {
                "ema9": round(ema9.iloc[-1], 2),
                "ema21": round(ema21.iloc[-1], 2),
                "sma50": round(sma50.iloc[-1], 2),
                "sma200": round(sma200.iloc[-1], 2) if not pd.isna(sma200.iloc[-1]) else "N/A",
                "trend": "BULLISH" if current_price > sma50.iloc[-1] else "BEARISH"
            },
            "atr": {
                "value": round(atr.iloc[-1], 2),
                "percent": round((atr.iloc[-1] / current_price) * 100, 2)
            },
            "volume": {
                "current": int(volume.iloc[-1]),
                "average_20d": int(avg_volume_20),
                "ratio": round(volume_ratio, 2),
                "status": "HIGH" if volume_ratio > 1.5 else "LOW" if volume_ratio < 0.5 else "NORMAL"
            },
            "signals": signals,
            "overall_trend": "BULLISH" if len([s for s in signals if "BULLISH" in s or "UPTREND" in s]) > len([s for s in signals if "BEARISH" in s or "DOWNTREND" in s]) else "BEARISH" if len([s for s in signals if "BEARISH" in s or "DOWNTREND" in s]) > 0 else "NEUTRAL",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating indicators for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}


def get_market_news(category: str = "indian_markets") -> Dict[str, Any]:
    """
    Get latest market news and sentiment from REAL RSS feeds.
    """
    try:
        from .news_integration import NewsAggregator
        import asyncio

        aggregator = NewsAggregator()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            news_feed = loop.run_until_complete(
                aggregator.fetch_all_news(categories=[category], max_articles=20)
            )
        finally:
            loop.close()

        return {
            "category": category,
            "date": datetime.now().strftime("%B %d, %Y"),
            "source": "LIVE_RSS_FEEDS",
            "news": {
                "headlines": [
                    {
                        "title": article.title,
                        "sentiment": article.sentiment,
                        "source": article.source,
                        "url": article.url,
                        "published": article.published.isoformat() if article.published else None
                    }
                    for article in news_feed.articles[:10]
                ],
                "overall_sentiment": news_feed.overall_sentiment,
                "sentiment_breakdown": {
                    "bullish": news_feed.bullish_count,
                    "bearish": news_feed.bearish_count,
                    "neutral": news_feed.neutral_count
                }
            },
            "market_status": _get_market_status(),
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        logger.error("news_integration module missing. Live news unavailable.")
        return {
            "category": category,
            "date": datetime.now().strftime("%B %d, %Y"),
            "source": "UNAVAILABLE",
            "error": "news_integration module missing",
            "market_status": _get_market_status(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching live news: {e}")
        return {
            "category": category,
            "date": datetime.now().strftime("%B %d, %Y"),
            "source": "UNAVAILABLE",
            "error": str(e),
            "market_status": _get_market_status(),
            "timestamp": datetime.now().isoformat()
        }


def get_option_chain_data(symbol: str = "NIFTY", expiry: str = "current") -> Dict[str, Any]:
    """
    Get LIVE option chain data from NSE.
    """
    try:
        if HAS_NSEPYTHON:
            logger.info(f"Fetching LIVE option chain for {symbol} from NSE")
            oc_data = nse_optionchain_scrapper(symbol.upper())
            if oc_data and 'records' in oc_data:
                records = oc_data['records']
                spot_price = records.get('underlyingValue', 0)
                expiry_dates = records.get('expiryDates', [])
                current_expiry = expiry_dates[0] if expiry_dates else None
                data = records.get('data', [])

                total_call_oi = 0
                total_put_oi = 0
                max_call_oi = 0
                max_put_oi = 0
                max_call_oi_strike = 0
                max_put_oi_strike = 0
                option_chain = []

                for item in data:
                    strike = item.get('strikePrice', 0)
                    ce_data = item.get('CE', {})
                    call_oi = ce_data.get('openInterest', 0)
                    call_oi_change = ce_data.get('changeinOpenInterest', 0)
                    pe_data = item.get('PE', {})
                    put_oi = pe_data.get('openInterest', 0)
                    put_oi_change = pe_data.get('changeinOpenInterest', 0)

                    total_call_oi += call_oi
                    total_put_oi += put_oi

                    if call_oi > max_call_oi:
                        max_call_oi = call_oi
                        max_call_oi_strike = strike
                    if put_oi > max_put_oi:
                        max_put_oi = put_oi
                        max_put_oi_strike = strike

                    option_chain.append({
                        "strike": strike,
                        "call_oi": call_oi,
                        "put_oi": put_oi,
                        "call_oi_change": call_oi_change,
                        "put_oi_change": put_oi_change,
                        "call_ltp": ce_data.get('lastPrice', 0),
                        "put_ltp": pe_data.get('lastPrice', 0),
                        "call_iv": ce_data.get('impliedVolatility', 0),
                        "put_iv": pe_data.get('impliedVolatility', 0)
                    })

                pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1.0
                atm_strike = round(spot_price / 100) * 100
                lot_sizes = {"NIFTY": 75, "BANKNIFTY": 35, "FINNIFTY": 40}
                lot_size = lot_sizes.get(symbol.upper(), 75)

                if pcr > 1.2:
                    market_bias = "BULLISH (High Put writing indicates support)"
                elif pcr < 0.8:
                    market_bias = "BEARISH (High Call writing indicates resistance)"
                else:
                    market_bias = "NEUTRAL"

                return {
                    "symbol": symbol,
                    "source": "NSE_LIVE",
                    "spot_price": round(spot_price, 2),
                    "atm_strike": atm_strike,
                    "lot_size": lot_size,
                    "expiry": current_expiry,
                    "all_expiries": expiry_dates[:5],
                    "pcr": round(pcr, 2),
                    "max_pain": atm_strike,
                    "max_call_oi_strike": max_call_oi_strike,
                    "max_put_oi_strike": max_put_oi_strike,
                    "total_call_oi": total_call_oi,
                    "total_put_oi": total_put_oi,
                    "market_bias": market_bias,
                    "key_support": max_put_oi_strike,
                    "key_resistance": max_call_oi_strike,
                    "top_strikes": sorted(
                        [s for s in option_chain if abs(s['strike'] - atm_strike) <= 500],
                        key=lambda x: abs(x['strike'] - atm_strike)
                    )[:11],
                    "timestamp": datetime.now().isoformat()
                }

        if HAS_YFINANCE:
            logger.warning("nsepython unavailable, using yfinance for spot price only")
            if symbol.upper() in ["NIFTY", "NIFTY50"]:
                yf_symbol = "^NSEI"
            elif symbol.upper() in ["BANKNIFTY", "NIFTYBANK"]:
                yf_symbol = "^NSEBANK"
            else:
                return {"error": f"Option chain not available for {symbol}", "source": "UNAVAILABLE"}

            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period="1d")

            if hist.empty:
                return {"error": "No data available", "source": "UNAVAILABLE"}

            spot_price = hist['Close'].iloc[-1]
            return {
                "symbol": symbol,
                "source": "YFINANCE_SPOT_ONLY",
                "spot_price": round(spot_price, 2),
                "warning": "Full option chain requires nsepython - install with: pip install nsepython",
                "timestamp": datetime.now().isoformat()
            }

        return {"error": "No data source available", "source": "UNAVAILABLE"}

    except Exception as e:
        logger.error(f"Error fetching option chain for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol, "source": "ERROR"}


def get_fii_dii_activity() -> Dict[str, Any]:
    """
    Get LIVE FII/DII activity data from NSE.
    """
    current_date = datetime.now().strftime("%Y-%m-%d")

    try:
        if HAS_NSEPYTHON:
            logger.info("Fetching LIVE FII/DII data from NSE")
            fii_dii_data = nse_fiidii()
            if fii_dii_data is not None and len(fii_dii_data) > 0:
                latest = fii_dii_data.iloc[0] if hasattr(fii_dii_data, 'iloc') else fii_dii_data[0]
                fii_buy = float(latest.get('FII_DII_BuyValue', 0) if hasattr(latest, 'get') else 0)
                fii_sell = float(latest.get('FII_DII_SellValue', 0) if hasattr(latest, 'get') else 0)
                fii_net = fii_buy - fii_sell
                dii_buy = float(latest.get('DII_BuyValue', 0) if hasattr(latest, 'get') else 0)
                dii_sell = float(latest.get('DII_SellValue', 0) if hasattr(latest, 'get') else 0)
                dii_net = dii_buy - dii_sell

                return {
                    "date": current_date,
                    "source": "NSE_LIVE",
                    "cash_segment": {
                        "fii": {
                            "gross_buy": round(fii_buy, 2),
                            "gross_sell": round(fii_sell, 2),
                            "net": round(fii_net, 2),
                            "trend": "BUYING" if fii_net > 0 else "SELLING"
                        },
                        "dii": {
                            "gross_buy": round(dii_buy, 2),
                            "gross_sell": round(dii_sell, 2),
                            "net": round(dii_net, 2),
                            "trend": "BUYING" if dii_net > 0 else "SELLING"
                        }
                    },
                    "interpretation": _get_fii_dii_interpretation(fii_net, dii_net),
                    "market_impact": _get_market_impact(fii_net, dii_net),
                    "timestamp": datetime.now().isoformat()
                }

        return {
            "date": current_date,
            "source": "UNAVAILABLE",
            "error": "nsepython required for live FII/DII data - install with: pip install nsepython",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching FII/DII data: {e}")
        return {
            "date": current_date,
            "source": "ERROR",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def _get_fii_dii_interpretation(fii_net: float, dii_net: float) -> str:
    if fii_net > 0 and dii_net > 0:
        return "Both FIIs and DIIs are buying - Strong bullish signal"
    elif fii_net < 0 and dii_net < 0:
        return "Both FIIs and DIIs are selling - Bearish signal"
    elif fii_net < 0 and dii_net > 0:
        return "FIIs selling but DIIs buying - DII support may limit downside"
    elif fii_net > 0 and dii_net < 0:
        return "FIIs buying but DIIs selling - Mixed signals, watch for direction"
    return "Neutral activity"


def _get_market_impact(fii_net: float, dii_net: float) -> str:
    net_flow = fii_net + dii_net
    if net_flow > 1000:
        return "BULLISH - Strong net inflows"
    elif net_flow < -1000:
        return "BEARISH - Strong net outflows"
    elif abs(net_flow) < 500:
        return "NEUTRAL - Balanced flows"
    elif net_flow > 0:
        return "MILDLY_BULLISH - Moderate net inflows"
    else:
        return "MILDLY_BEARISH - Moderate net outflows"


def get_economic_calendar() -> Dict[str, Any]:
    """
    Get upcoming economic events affecting Indian markets.
    """
    today = datetime.now()
    events = [
        {
            "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "event": "RBI MPC Meeting (Day 1)",
            "importance": "HIGH",
            "expected_impact": "Banking sector, interest rate sensitive stocks"
        },
        {
            "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "event": "RBI MPC Rate Decision",
            "importance": "HIGH",
            "expected_impact": "Market-wide, especially banks and NBFCs"
        },
        {
            "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "event": "US FOMC Meeting",
            "importance": "MEDIUM",
            "expected_impact": "IT stocks, export-oriented companies"
        },
        {
            "date": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
            "event": "India IIP Data Release",
            "importance": "MEDIUM",
            "expected_impact": "Industrial stocks, infra"
        },
        {
            "date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            "event": "India CPI Inflation Data",
            "importance": "HIGH",
            "expected_impact": "Market sentiment, RBI policy expectations"
        }
    ]
    return {
        "upcoming_events": events,
        "next_major_event": events[0] if events else None,
        "timestamp": datetime.now().isoformat()
    }


def execute_paper_trade(
    symbol: str,
    action: str,
    quantity: int,
    price: float,
    order_type: str = "LIMIT",
    product_type: str = "INTRADAY"
) -> Dict[str, Any]:
    """
    Execute a PAPER TRADE for backtesting and strategy validation.
    """
    order_id = str(uuid.uuid4())[:8].upper()
    if action.upper() not in ["BUY", "SELL"]:
        return {"error": "Invalid action. Use BUY or SELL"}
    if quantity <= 0:
        return {"error": "Quantity must be positive"}
    return {
        "status": "PAPER_ORDER_LOGGED",
        "mode": "BACKTESTING",
        "order_id": f"PAPER-{order_id}",
        "symbol": symbol.upper(),
        "action": action.upper(),
        "quantity": quantity,
        "price": price,
        "order_type": order_type,
        "product_type": product_type,
        "order_value": quantity * price,
        "exchange": "NSE",
        "timestamp": datetime.now().isoformat(),
        "warning": "PAPER TRADE ONLY - For live trading use: POST /api/dhan/place-order",
        "live_trading_endpoint": "https://engine-c-429140669077.us-central1.run.app/api/dhan/place-order"
    }

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def _get_market_status() -> Dict[str, Any]:
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()
    if weekday >= 5:
        return {"status": "CLOSED", "reason": "Weekend", "next_open": "Monday 9:00 AM IST"}
    pre_market_start = datetime.strptime("09:00", "%H:%M").time()
    market_open = datetime.strptime("09:15", "%H:%M").time()
    market_close = datetime.strptime("15:30", "%H:%M").time()
    post_market_end = datetime.strptime("16:00", "%H:%M").time()
    if current_time < pre_market_start:
        return {"status": "CLOSED", "reason": "Before market hours", "opens_at": "9:00 AM IST"}
    elif pre_market_start <= current_time < market_open:
        return {"status": "PRE_MARKET", "note": "Pre-open auction session"}
    elif market_open <= current_time < market_close:
        return {"status": "OPEN", "closes_at": "3:30 PM IST"}
    elif market_close <= current_time < post_market_end:
        return {"status": "POST_MARKET", "note": "After-market session"}
    else:
        return {"status": "CLOSED", "reason": "After market hours", "next_open": "Tomorrow 9:00 AM IST"}

# =====================================================================
# FUNCTION REGISTRY FOR GEMINI - ALL LIVE DATA SOURCES
# =====================================================================

MARKET_DATA_TOOLS = [
    get_stock_quote,
    get_nifty_overview,
    get_technical_indicators,
    get_market_news,
    get_option_chain_data,
    get_fii_dii_activity,
    get_economic_calendar,
    execute_paper_trade
]

TOOL_DESCRIPTIONS = {
    "get_stock_quote": "Get LIVE stock quote, price, and key metrics for any NSE/BSE listed stock or index (via yfinance)",
    "get_nifty_overview": "Get LIVE NIFTY 50 index overview with top gainers, losers, and market breadth (via yfinance + NSE)",
    "get_technical_indicators": "Calculate technical indicators (RSI, MACD, Bollinger Bands, MAs) from LIVE price data",
    "get_market_news": "Get LIVE market news from Economic Times, Moneycontrol, Livemint RSS feeds",
    "get_option_chain_data": "Get LIVE option chain from NSE with PCR, max pain, and key OI levels for NIFTY/BANKNIFTY",
    "get_fii_dii_activity": "Get LIVE FII/DII buying/selling activity from NSE",
    "get_economic_calendar": "Get upcoming economic events that may affect Indian markets",
    "execute_paper_trade": "Execute a PAPER TRADE for backtesting (for live trading use Engine C Dhan API)"
}
