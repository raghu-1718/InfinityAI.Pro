# live_trader.py
import asyncio, time, math, random, logging
import pandas as pd
import numpy as np
import aiohttp
import json
import csv
import os
from datetime import datetime
from typing import Dict, Any
from utils.config import CONFIG
from services.model_train import featurize
from utils.logger import get_logger

logger = logging.getLogger(__name__)

def write_trade_log(row:Dict[str,Any]):
    header = ["timestamp","symbol","signal","score","ml_prob","rule_score","vol_factor","premium","contracts","cost","sl","tp","outcome","pnl","equity_after"]
    os.makedirs(os.path.dirname(CONFIG.TRADE_LOG_CSV), exist_ok=True)
    file_exists = os.path.exists(CONFIG.TRADE_LOG_CSV)
    with open(CONFIG.TRADE_LOG_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

class WSFetcher:
    def __init__(self, url:str, subscribe_payload:dict, message_callback, reconnect_delay=2.0):
        self.url = url
        self.sub_payload = subscribe_payload
        self.cb = message_callback
        self.reconnect_delay = reconnect_delay
        self.keep_running = True
        self.session = None
        self.ws = None

    async def connect(self):
        headers = {
            "access-token": CONFIG.BROKER['access_token'],
            "X-Client-Id": CONFIG.BROKER['client_id']
        }
        while self.keep_running:
            try:
                async with aiohttp.ClientSession(headers=headers) as session:
                    self.session = session
                    async with session.ws_connect(self.url) as ws:
                        self.ws = ws
                        # send subscription
                        if self.sub_payload:
                            await ws.send_json(self.sub_payload)
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                # user callback handles ticks
                                await self.cb(data)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
            except Exception as e:
                print("WS error", e, "reconnecting in", self.reconnect_delay)
                await asyncio.sleep(self.reconnect_delay)

    def stop(self):
        self.keep_running = False

class RealTimeFetcher:
    def __init__(self, adapter=None):
        self.adapter = adapter
        self.candles = {}  # symbol -> list of candles
        self.current_candle = {}  # symbol -> current 5m candle
        self.task = None

    async def start(self):
        if self.adapter:
            # Start periodic market data fetching instead of WebSocket
            self.task = asyncio.create_task(self._periodic_market_data_fetch())
            logger.info("Started periodic market data fetching")
        else:
            logger.info("No adapter, using fallback data")

    async def _periodic_market_data_fetch(self):
        """Fetch market data periodically for all symbols using TradingView + Dhan fallback"""
        logger.info("Starting periodic market data fetch...")
        while True:
            try:
                for symbol in CONFIG.SYMBOLS:  # Scan all symbols, not just first 2
                    try:
                        # Try TradingView first
                        tv_provider = None
                        quote = None

                        try:
                            from services.tradingview_provider import TradingViewProvider
                            tv_provider = TradingViewProvider()
                            await tv_provider.initialize()
                            quote = await tv_provider.get_quote(symbol)
                        except Exception as e:
                            logger.warning(f"TradingView fetch failed for {symbol}: {e}")

                        # Fallback to Dhan API if TradingView failed
                        if not quote and self.adapter:
                            quote = await self.adapter.get_quote_async(symbol)

                        if quote and quote.get('last_price', 0) > 0:
                            # Convert to tick format expected by on_tick
                            tick_data = {
                                "symbol": symbol,
                                "ltp": quote.get("last_price", 0),
                                "volume": quote.get("volume", 0),
                                "timestamp": pd.Timestamp.now().isoformat()
                            }
                            await self.on_tick(tick_data)
                            logger.debug(f"Updated {symbol}: ₹{quote.get('last_price', 0):.2f}")
                        else:
                            logger.warning(f"No valid quote data received for {symbol} from any source")

                    except Exception as e:
                        logger.error(f"Failed to fetch quote for {symbol}: {e}")

                    finally:
                        # Clean up TradingView session
                        if 'tv_provider' in locals() and tv_provider:
                            await tv_provider.close()

                # Wait before next fetch - more frequent now
                await asyncio.sleep(10)  # Fetch every 10 seconds for better data

            except Exception as e:
                logger.error(f"Error in periodic market data fetch: {e}")
                await asyncio.sleep(30)  # Wait longer on error

    def stop(self):
        if self.task:
            self.task.cancel()

    async def on_tick(self, data):
        # Assume data: {"symbol": "NIFTY", "ltp": 24000.5, "volume": 1000, "timestamp": "2023-09-26T10:00:00Z"}
        symbol = data.get("symbol", "NIFTY")
        price = data.get("ltp", 0)
        vol = data.get("volume", 0)
        ts_str = data.get("timestamp", "")
        if not ts_str:
            ts = pd.Timestamp.now()
        else:
            ts = pd.to_datetime(ts_str)
        
        # Round to 5m interval
        interval = pd.Timedelta(minutes=5)
        candle_start = ts.floor(interval)
        
        if symbol not in self.current_candle:
            self.current_candle[symbol] = {
                "datetime": candle_start,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": vol
            }
        else:
            candle = self.current_candle[symbol]
            if candle["datetime"] != candle_start:
                # New candle, save previous
                if symbol not in self.candles:
                    self.candles[symbol] = []
                self.candles[symbol].append(candle)
                # Keep last 200
                if len(self.candles[symbol]) > 200:
                    self.candles[symbol].pop(0)
                # Start new
                self.current_candle[symbol] = {
                    "datetime": candle_start,
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": vol
                }
            else:
                # Update current
                candle["high"] = max(candle["high"], price)
                candle["low"] = min(candle["low"], price)
                candle["close"] = price
                candle["volume"] += vol

    async def get_candles(self, symbol, timeframe="5m", length=200):
        if symbol not in self.candles:
            # Generate realistic synthetic data with technical indicators
            await self._generate_realistic_data(symbol, length)
            
        # Get from real-time or generated data
        candles = self.candles[symbol][-length:] if len(self.candles[symbol]) >= length else self.candles[symbol]
        if self.current_candle.get(symbol):
            candles = candles + [self.current_candle[symbol]]
        df = pd.DataFrame(candles)
        df.set_index("datetime", inplace=True)
        return df
    
    async def _generate_realistic_data(self, symbol, length=200):
        """Generate realistic market data with technical indicators"""
        # Base prices for different symbols
        base_prices = {
            "NIFTY": 24000,
            "BANKNIFTY": 51000,
            "NIFTY_MIDCAP": 12000,
            "NIFTY_NEXT50": 70000,
            "NIFTY_FIN": 22000,
            "SENSEX": 79000,
            "BSE_MIDCAP": 28000,
            "BSE_SMALLCAP": 15000,
            "MCX_GOLD_MINI": 72000,
            "MCX_SILVER_MINI": 89000,
            "MCX_CRUDE_MINI": 5800,
            "MCX_NG_MINI": 220,
            "GIFTNIFTY": 24000
        }
        
        base_price = base_prices.get(symbol, 24000)
        
        # Generate price series with realistic volatility
        now = pd.Timestamp.now()
        dates = [now - pd.Timedelta(minutes=5*i) for i in range(length)][::-1]
        
        # Create price movements with trends and volatility
        np.random.seed(hash(symbol) % 2**32)  # Deterministic seed per symbol
        returns = np.random.normal(0.0001, 0.005, length)  # Small drift, 0.5% vol
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Create OHLCV data
        high_mult = 1 + np.abs(np.random.normal(0, 0.003, length))
        low_mult = 1 - np.abs(np.random.normal(0, 0.003, length))
        
        candles = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            high = price * high_mult[i]
            low = price * low_mult[i]
            open_price = price * (1 + np.random.normal(0, 0.001))
            close = price
            volume = np.random.randint(1000, 10000)
            
            candles.append({
                "datetime": date,
                "open": open_price,
                "high": max(open_price, high),
                "low": min(open_price, low),
                "close": close,
                "volume": volume
            })
        
        # Apply technical indicators
        df = pd.DataFrame(candles)
        df = featurize(df)  # This adds MACD, RSI, ATR, VWAP, etc.
        
        # Store as list of dicts
        self.candles[symbol] = df.to_dict('records')

class LiveTrader:
    def __init__(self):
        self.equity = CONFIG.CAPITAL
        self.start_equity = CONFIG.CAPITAL
        self.trades_today = 0
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.last_loss_time = None
        self.open_trade = None
        
        # Performance monitoring
        self.performance_stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'ai_signals_correct': 0,
            'ai_signals_total': 0,
            'ai_accuracy': 0.0
        }
        
        # Initialize broker first (even in paper mode for market data)
        self.broker = None
        self.fetcher = None
        self.model = None
        self.sentiment_analyzer = None
        
        # Load ML model for better signals
        try:
            import pickle
            with open(CONFIG.MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            print("Loaded ML model for enhanced signals")
        except Exception as e:
            print(f"No ML model loaded: {e}")

    async def initialize_components(self):
        """Initialize broker and market data fetcher"""
        try:
            self.broker = await self.get_real_broker()
            logger.info("Broker initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize broker: {e}. Using fallback mode.")
            self.broker = None
        
        # Initialize fetcher with broker for market data (or None if broker failed)
        self.fetcher = RealTimeFetcher(adapter=self.broker)

        # Initialize sentiment analyzer for AI-enhanced signals
        try:
            from services.sentiment_analyzer import SentimentAnalyzer
            self.sentiment_analyzer = SentimentAnalyzer()
            await self.sentiment_analyzer.initialize_clients()
            logger.info("Sentiment analyzer initialized with Perplexity and OpenAI")
        except Exception as e:
            logger.warning(f"Failed to initialize sentiment analyzer: {e}. Using basic signals.")
            self.sentiment_analyzer = None

    async def get_market_data(self, symbol):
        return await self.fetcher.get_candles(symbol, "5m", 200)

    async def get_real_broker(self):
        # Always return broker for market data access, but only place real orders if not PAPER_MODE
        try:
            from services.broker_dhan import DhanAdapter
            broker = DhanAdapter(
                client_id=CONFIG.BROKER['client_id'],
                access_token=CONFIG.BROKER['access_token'],
                data_api_key=CONFIG.BROKER.get('data_api_key'),
                api_secret=CONFIG.BROKER.get('data_api_secret')
            )
            return broker
        except Exception as e:
            logger.error(f"Failed to create Dhan broker: {e}")
            raise

    def daily_loss_pct(self):
        return (self.start_equity - self.equity) / max(self.start_equity, 1.0)

    def daily_profit_pct(self):
        return (self.equity - self.start_equity) / max(self.start_equity, 1.0)

    def compute_features_row(self, df):
        df2 = featurize(df.reset_index())
        return df2

    def rule_based_score(self, last_row:pd.Series):
        macd = last_row["MACD"]
        price = last_row["close"]
        vwap = last_row["VWAP"]
        rsi = last_row["RSI"]
        bull = 0.0
        if macd > 0 and price > vwap and 40 <= rsi <= 70:
            bull = 1.0
        elif macd > 0 and price > vwap and 35 <= rsi <= 80:
            bull = 0.7
        elif macd > 0:
            bull = 0.4
        bear = 0.0
        if macd < 0 and price < vwap and 30 <= rsi <= 60:
            bear = 1.0
        elif macd < 0 and price < vwap and 25 <= rsi <= 65:
            bear = 0.7
        elif macd < 0:
            bear = 0.4
        if bull >= bear and bull > 0:
            return {"direction": "BUY", "rule_score": bull}
        elif bear > bull:
            return {"direction": "SELL", "rule_score": bear}
        else:
            return {"direction": "HOLD", "rule_score": 0.0}

    def volatility_factor(self, last_row:pd.Series):
        atr = last_row.get("ATR", 0.0)
        # Ensure ATR is a numeric value
        if hasattr(atr, 'timestamp'):  # Check if it's a Timestamp
            atr = 0.0
        elif not isinstance(atr, (int, float)):
            try:
                atr = float(atr)
            except (ValueError, TypeError):
                atr = 0.0
        
        price = last_row.get("close", 1.0)
        if hasattr(price, 'timestamp'):  # Check if it's a Timestamp
            price = 1.0
        elif not isinstance(price, (int, float)):
            try:
                price = float(price)
            except (ValueError, TypeError):
                price = 1.0
                
        val = (atr / max(price, 1.0)) * 100.0
        val_norm = min(val / 5.0, 1.0)
        return float(val_norm)

    def compute_contracts(self, premium, vol_factor):
        risk_amount = self.equity * CONFIG.RISK_PER_TRADE_PCT
        stop_per_contract = premium * 0.6
        if stop_per_contract <= 0:
            return 0
        raw_contracts = math.floor(risk_amount / stop_per_contract)
        adj = max(0.3, 1.0 - vol_factor)
        contracts = max(0, int(math.floor(raw_contracts * adj)))
        contracts = min(contracts, 3)
        return contracts

    async def evaluate_symbol(self, symbol):
        try:
            df = await self.get_market_data(symbol)
            if df is None or df.empty:
                return None
            
            # Ensure dataframe is properly formatted
            df = df.reset_index()  # Reset index to avoid datetime index issues
            last_row = df.iloc[-1]
            
            # Ensure we have the required columns
            required_cols = ["close", "MACD", "VWAP", "RSI", "ATR"]
            if not all(col in last_row.index for col in required_cols):
                logger.warning(f"Missing required columns for {symbol}. Available: {list(last_row.index)}")
                return None
            
            features = self.compute_features_row(df)
            if features is None or features.empty:
                return None
            
            # Ensure features dataframe is also properly formatted
            features = features.reset_index(drop=True)
            last_row = features.iloc[-1]  # Use featurized data for analysis
            
            # Ensure we have the required columns
            required_cols = ["close", "MACD", "VWAP", "RSI", "ATR"]
            if not all(col in last_row.index for col in required_cols):
                logger.warning(f"Missing required columns for {symbol}. Available: {list(last_row.index)}")
                return None
            
            last_feat = features[["MACD","RSI","SMA_5","SMA_20","ret1"]].iloc[-1]  # Features for ML model
            ml_prob = self.model.predict_proba(last_feat.values.reshape(1, -1))[0][1]
            rule_res = self.rule_based_score(last_row)
            vol_factor = self.volatility_factor(last_row)
            total_score = (CONFIG.WEIGHT_ML * ml_prob) + (CONFIG.WEIGHT_RULE * rule_res["rule_score"]) + (CONFIG.WEIGHT_VOL * vol_factor)
            if total_score < CONFIG.MIN_TRADE_SCORE:
                return None
            premium = last_row["close"]
            contracts = self.compute_contracts(premium, vol_factor)
            if contracts <= 0:
                return None
            return {
                "symbol": symbol,
                "direction": rule_res["direction"],
                "score": total_score,
                "ml_prob": ml_prob,
                "rule_score": rule_res["rule_score"],
                "vol_factor": vol_factor,
                "premium": premium,
                "contracts": contracts,
                "last_row": last_row
            }
        except Exception as e:
            logger.error(f"Error evaluating {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def pick_best_candidate(self):
        candidates = []
        for symbol in CONFIG.SYMBOLS:
            cand = await self.evaluate_symbol(symbol)
            if cand:
                candidates.append(cand)
        
        if not candidates:
            return None

        # Enhance candidates with AI and sentiment analysis
        enhanced_candidates = []
        for candidate in candidates:
            if self.sentiment_analyzer:
                try:
                    enhanced = await self.sentiment_analyzer.enhance_signal(candidate)
                    enhanced_candidates.append(enhanced)
                    logger.info(f"Enhanced {candidate['symbol']}: {enhanced.recommendation}")
                except Exception as e:
                    logger.warning(f"Failed to enhance signal for {candidate['symbol']}: {e}")
                    # Fallback to original candidate
                    enhanced_candidates.append(candidate)
            else:
                enhanced_candidates.append(candidate)
        
        # Select best enhanced candidate
        if enhanced_candidates and isinstance(enhanced_candidates[0], dict):
            # Original format - use basic selection
            best = max(enhanced_candidates, key=lambda x: x["score"])
        else:
            # Enhanced format - use final_score
            best = max(enhanced_candidates, key=lambda x: x.final_score if hasattr(x, 'final_score') else x.get('score', 0))
            if hasattr(best, 'recommendation'):
                logger.info(f"AI-Enhanced selection: {best.recommendation}")
        
        # Return in original format for compatibility
        if hasattr(best, 'original_signal'):
            return best.original_signal
        else:
            return best

    async def generate_signal(self):
        return await self.pick_best_candidate()

    async def execute_trade(self, candidate):
        logger.info(f"Executing trade: {candidate['symbol']} {candidate['direction']} {candidate['contracts']} contracts")
        
        if not self.broker:
            self.broker = await self.get_real_broker()
        
        symbol = f"{candidate['symbol']}_OPT"  # Assuming options trading
        action = candidate["direction"]
        contracts = candidate["contracts"]
        premium = candidate["premium"]
        cost = contracts * premium
        
        if cost > self.equity * 0.1:  # Cap at 10%
            contracts = int((self.equity * 0.1) / premium)
            logger.info(f"Reduced contracts to {contracts} due to cost limit")
        
        if contracts <= 0:
            logger.warning("Insufficient funds for trade")
            return False
        
        if CONFIG.PAPER_MODE:
            # Paper mode - simulate trade execution
            logger.info(f"PAPER MODE: Would execute {action} {contracts} contracts of {symbol} at ₹{premium}")
            self.open_trade = {
                "symbol": symbol,
                "action": action,
                "contracts": contracts,
                "entry_premium": premium,
                "entry_price": candidate["last_row"]["close"],
                "tp": premium * 0.1,  # 10% profit target
                "sl": premium * 0.03,  # 3% stop loss
                "order_id": f"paper_{datetime.now().timestamp()}",
                "entry_time": datetime.now()
            }
            self.equity -= cost if action == "BUY" else 0
            self.trades_today += 1
            logger.info(f"Simulated trade: {self.open_trade}")
            # Log trade
            self.log_trade(self.open_trade, "ENTRY")
            return True
        else:
            # Live mode - place real order
            logger.info("Live mode: Placing real order...")
            # For indices, use futures contracts instead of options
            if symbol.endswith("_OPT"):
                # Convert to futures symbol (remove _OPT and use current month)
                base_symbol = symbol.replace("_OPT", "")
                
                # Special handling for MCX commodities
                if base_symbol.startswith("MCX_"):
                    # For MCX, use the base symbol directly (no expiry conversion needed)
                    futures_symbol = base_symbol
                    logger.info(f"Using MCX commodity: {futures_symbol}")
                else:
                    # For NSE indices, add expiry
                    current_month = datetime.now().strftime("%b").upper()
                    current_year = datetime.now().strftime("%y")
                    futures_symbol = f"{base_symbol}-{current_month}{current_year}-FUT"
                    logger.info(f"Converted {symbol} to futures: {futures_symbol}")
            else:
                futures_symbol = symbol
            
            strategy = {
                "action": action,
                "symbol": futures_symbol,
                "quantity": contracts
            }
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, self.broker.execute_trade, strategy, {})
            if res.get("status") == "success":
                self.open_trade = {
                    "symbol": futures_symbol,
                    "action": action,
                    "contracts": contracts,
                    "entry_premium": premium,
                    "entry_price": candidate["last_row"]["close"],
                    "tp": premium * 0.1,  # 10% profit target
                    "sl": premium * 0.03,  # 3% stop loss
                    "order_id": res.get("order_details", {}).get("orderId", "unknown"),
                    "entry_time": datetime.now()
                }
                self.equity -= cost if action == "BUY" else 0
                self.trades_today += 1
                logger.info(f"Executed live trade: {self.open_trade}")
                # Log trade
                self.log_trade(self.open_trade, "ENTRY")
                return True
            else:
                logger.error(f"Order failed: {res}")
                return False

    async def close_trade(self, reason="EXIT"):
        if not self.open_trade:
            return False
        # Simulate exit for now (in paper mode or if no real monitoring)
        exit_premium = self.open_trade["entry_premium"] * 1.05  # Simulate 5% gain
        pnl = (exit_premium - self.open_trade["entry_premium"]) * self.open_trade["contracts"] if self.open_trade["action"] == "BUY" else (self.open_trade["entry_premium"] - exit_premium) * self.open_trade["contracts"]
        self.equity += self.open_trade["entry_premium"] * self.open_trade["contracts"] + pnl
        self.daily_pnl += pnl
        
        # Update performance statistics
        trade_result = {
            'pnl': pnl,
            'symbol': self.open_trade['symbol'],
            'reason': reason
        }
        self.update_performance_stats(trade_result)
        
        logger.info(f"Closed trade: PnL ₹{pnl:.2f}, New equity: ₹{self.equity:.2f}")
        # Log trade
        self.log_trade(self.open_trade, reason, pnl=pnl)
        self.open_trade = None
        return True

    async def monitor_trade(self):
        if not self.open_trade:
            return
        # Simplified monitoring - in real implementation, check real-time prices
        # For now, simulate based on time or random (paper mode)
        if CONFIG.PAPER_MODE:
            # Simulate exit conditions
            if random.random() < 0.1:  # 10% chance per check
                pnl = (random.uniform(-0.5, 0.5) * self.open_trade["entry_premium"]) * self.open_trade["contracts"]
                if pnl > 0:
                    await self.close_trade("PROFIT")
                    self.consecutive_losses = 0
                else:
                    await self.close_trade("LOSS")
                    self.consecutive_losses += 1
                    self.last_loss_time = time.time()
        else:
            # Real monitoring would check current market prices and SL/TP
            pass

    def update_performance_stats(self, trade_result):
        """Update performance statistics after each trade"""
        self.performance_stats['total_trades'] += 1
        
        pnl = trade_result.get('pnl', 0.0)
        self.performance_stats['total_pnl'] += pnl
        
        if pnl > 0:
            self.performance_stats['winning_trades'] += 1
            self.performance_stats['avg_win'] = (
                (self.performance_stats['avg_win'] * (self.performance_stats['winning_trades'] - 1)) + pnl
            ) / self.performance_stats['winning_trades']
        elif pnl < 0:
            self.performance_stats['losing_trades'] += 1
            self.performance_stats['avg_loss'] = (
                (self.performance_stats['avg_loss'] * (self.performance_stats['losing_trades'] - 1)) + abs(pnl)
            ) / self.performance_stats['losing_trades']
        
        # Calculate derived metrics
        total_trades = self.performance_stats['total_trades']
        winning_trades = self.performance_stats['winning_trades']
        
        if total_trades > 0:
            self.performance_stats['win_rate'] = winning_trades / total_trades
            
        if self.performance_stats['avg_loss'] > 0:
            self.performance_stats['profit_factor'] = (
                self.performance_stats['avg_win'] * self.performance_stats['win_rate']
            ) / (self.performance_stats['avg_loss'] * (1 - self.performance_stats['win_rate']))
    
    def display_performance_stats(self):
        """Display current performance statistics"""
        stats = self.performance_stats
        print("\n📊 PERFORMANCE STATISTICS")
        print("=" * 40)
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Winning Trades: {stats['winning_trades']}")
        print(f"Losing Trades: {stats['losing_trades']}")
        print(f"Win Rate: {stats['win_rate']*100:.1f}%")
        print(f"Average Win: ₹{stats['avg_win']:.2f}")
        print(f"Average Loss: ₹{stats['avg_loss']:.2f}")
        print(f"Profit Factor: {stats['profit_factor']:.2f}")
        print(f"Total P&L: ₹{stats['total_pnl']:.2f}")
        print(f"AI Signal Accuracy: {stats['ai_accuracy']*100:.1f}%")
        print(f"Current Equity: ₹{self.equity:.2f}")
        print(f"Daily P&L: ₹{self.daily_pnl:.2f}")
        print("=" * 40)
        
        # Display AI insights if available
        if self.sentiment_analyzer:
            print("\n🤖 AI MARKET INTELLIGENCE")
            print("-" * 30)
            try:
                # Get market overview (this would be async in real implementation)
                asyncio.create_task(self._display_market_overview())
                print("📈 Market intelligence analysis in progress...")
            except Exception as e:
                print(f"AI insights unavailable: {e}")
        
        # Strategy optimization suggestions
        self._provide_strategy_recommendations()
    
    def _provide_strategy_recommendations(self):
        """Provide strategy optimization recommendations based on performance"""
        stats = self.performance_stats
        
        print("\n🎯 STRATEGY OPTIMIZATION RECOMMENDATIONS")
        print("-" * 45)
        
        if stats['total_trades'] < 5:
            print("📈 Need more trades for meaningful analysis")
            return
            
        # Win rate analysis
        if stats['win_rate'] < 0.4:
            print("⚠️  Low win rate - consider stricter entry criteria")
            print("   💡 Increase MIN_TRADE_SCORE in config")
        elif stats['win_rate'] > 0.6:
            print("✅ Good win rate - maintain current strategy")
        
        # Profit factor analysis
        if stats['profit_factor'] < 1.5:
            print("⚠️  Low profit factor - losses outweigh wins")
            print("   💡 Consider reducing position sizes or tightening stops")
        elif stats['profit_factor'] > 2.0:
            print("✅ Excellent profit factor - consider increasing position sizes")
        
        # Risk management
        if stats['avg_loss'] > stats['avg_win'] * 2:
            print("⚠️  Losses too large relative to wins")
            print("   💡 Consider reducing stop loss percentage")
        
        # AI accuracy
        if stats['ai_accuracy'] < 0.5:
            print("🤖 AI accuracy needs improvement")
            print("   💡 Consider retraining model or adjusting features")
        
        # Market timing
        print("📊 Market Analysis:")
        print("   • NSE: 9:15 AM - 3:30 PM IST")
        print("   • MCX: 9:00 AM - 11:30 PM IST")
        print("   • Best MCX hours: 9 AM - 11 AM, 5 PM - 9 PM")
        
        # Capital efficiency
        capital_efficiency = (stats['total_pnl'] / self.start_equity) * 100
        print(f"💰 Capital Efficiency: {capital_efficiency:.1f}%")
        
        if capital_efficiency > 5:
            print("✅ Good capital utilization")
        else:
            print("⚠️  Consider optimizing position sizing")

    async def _display_market_overview(self):
        """Display AI market overview"""
        try:
            if self.sentiment_analyzer:
                overview = await self.sentiment_analyzer.get_market_overview()
                print(f"🌍 Market Sentiment: {overview.get('market_sentiment', 'unknown')}")
                print(f"⚠️  Risk Assessment: {overview.get('risk_assessment', 'unknown')}")
                
                developments = overview.get('key_developments', [])
                if developments:
                    print("📰 Key Developments:")
                    for dev in developments[:3]:
                        print(f"   • {dev}")
                
                implications = overview.get('trading_implications', [])
                if implications:
                    print("💡 Trading Implications:")
                    for imp in implications[:2]:
                        print(f"   • {imp}")
        except Exception as e:
            logger.error(f"Error displaying market overview: {e}")

    async def run(self):
        logger.info("Starting advanced AI options trader with risk management...")
        await self.initialize_components()
        await self.fetcher.start()
        try:
            while True:
                # Risk checks
                if self.daily_loss_pct() >= CONFIG.MAX_DAILY_LOSS_PCT:
                    logger.warning("Daily loss limit reached. Stopping for the day.")
                    break
                if self.daily_profit_pct() >= CONFIG.MAX_DAILY_PROFIT_PCT:
                    logger.info("Daily profit target reached. Stopping for the day.")
                    break
                if self.consecutive_losses >= CONFIG.MAX_CONSECUTIVE_LOSSES:
                    if time.time() - self.last_loss_time < CONFIG.COOLDOWN_AFTER_LOSSES_SEC:
                        logger.info("In cooldown after consecutive losses.")
                        await asyncio.sleep(300)  # Wait 5 minutes
                        continue
                    else:
                        self.consecutive_losses = 0  # Reset after cooldown

                if not self.open_trade:
                    candidate = await self.generate_signal()
                    if candidate:
                        logger.info(f"Attempting to execute trade for {candidate['symbol']}")
                        success = await self.execute_trade(candidate)
                        if success:
                            logger.info(f"Entered trade for {candidate['symbol']} {candidate['direction']}")
                else:
                    # Monitor and potentially close trade
                    await self.monitor_trade()
                    # For now, simulate closing after some time
                    if self.open_trade and (datetime.now() - self.open_trade["entry_time"]).seconds > 300:  # 5 minutes
                        await self.close_trade("TIMEOUT")

                await asyncio.sleep(CONFIG.CYCLE_SECONDS)  # Scan every 15 seconds
        finally:
            if self.open_trade:
                await self.close_trade("SHUTDOWN")
            self.fetcher.stop()
            if self.sentiment_analyzer:
                await self.sentiment_analyzer.close_clients()
            logger.info(f"Trader stopped. Final equity: ₹{self.equity:.2f}, Daily PnL: ₹{self.daily_pnl:.2f}")
            self.display_performance_stats()

    def log_trade(self, trade_data, outcome, pnl=0.0):
        """Log trade to CSV file"""
        row = {
            "timestamp": datetime.now().isoformat(),
            "symbol": trade_data["symbol"],
            "signal": trade_data["action"],
            "score": 0.0,  # Not available in trade data
            "ml_prob": 0.0,  # Not available in trade data
            "rule_score": 0.0,  # Not available in trade data
            "vol_factor": 0.0,  # Not available in trade data
            "premium": trade_data["entry_premium"],
            "contracts": trade_data["contracts"],
            "cost": trade_data["entry_premium"] * trade_data["contracts"],
            "sl": trade_data["sl"],
            "tp": trade_data["tp"],
            "outcome": outcome,
            "pnl": pnl,
            "equity_after": self.equity
        }
        write_trade_log(row)

if __name__ == "__main__":
    trader = LiveTrader()
    asyncio.run(trader.run())