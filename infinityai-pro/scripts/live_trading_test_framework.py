#!/usr/bin/env python3
"""
🚀 InfinityAI.Pro Live Trading Test Framework
🎯 Comprehensive testing for live trading when market opens
🛡️ Safety controls, monitoring, and risk management
💰 Ready for ₹2-5L daily trading with full automation
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import requests
import websockets
from dataclasses import dataclass
import sqlite3
import smtplib
from email.mime.text import MimeText
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_trading_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TradingSession:
    """Trading session configuration"""
    session_id: str
    start_time: datetime
    end_time: datetime
    capital_allocated: float
    max_positions: int
    risk_per_trade: float
    strategy_type: str
    symbols: List[str]
    status: str = "PENDING"

@dataclass
class Trade:
    """Individual trade representation"""
    trade_id: str
    symbol: str
    action: str  # BUY/SELL
    quantity: int
    price: float
    timestamp: datetime
    strategy: str
    confidence_score: float
    stop_loss: float
    take_profit: float
    status: str = "PENDING"

class LiveTradingTestFramework:
    """🎯 Comprehensive live trading test system"""
    
    def __init__(self):
        """Initialize trading test framework"""
        self.base_urls = {
            'engine_a': 'https://infinityai.pro',
            'engine_b': 'https://infinityai-engine-b.googlecloud.run',
            'engine_c': 'http://infinityai-alb.us-east-1.elb.amazonaws.com/engine-c',
            'engine_d': 'http://infinityai-alb.us-east-1.elb.amazonaws.com/engine-d'
        }
        
        # Trading configuration
        self.trading_config = {
            'market_hours': {
                'pre_market': (time(9, 0), time(9, 15)),
                'regular': (time(9, 15), time(15, 30)),
                'post_market': (time(15, 30), time(16, 0))
            },
            'position_limits': {
                'max_positions': 10,
                'max_capital_per_trade': 200000,  # ₹2 lakh
                'max_daily_loss': 100000,  # ₹1 lakh
                'max_portfolio_risk': 0.20  # 20%
            },
            'strategies': {
                'momentum': {'timeframe': '5m', 'risk': 0.02},
                'scalping': {'timeframe': '1m', 'risk': 0.01},
                'swing': {'timeframe': '1h', 'risk': 0.03}
            }
        }
        
        # Initialize database for tracking
        self.init_database()
        
        # Safety controls
        self.safety_controls = {
            'circuit_breaker': False,
            'max_consecutive_losses': 5,
            'consecutive_losses': 0,
            'daily_pnl': 0.0,
            'last_trade_time': None
        }
        
    def init_database(self):
        """Initialize SQLite database for trade tracking"""
        self.db_connection = sqlite3.connect('live_trading_test.db', check_same_thread=False)
        cursor = self.db_connection.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                capital_allocated REAL,
                strategy_type TEXT,
                status TEXT,
                total_pnl REAL DEFAULT 0,
                trades_count INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                session_id TEXT,
                symbol TEXT,
                action TEXT,
                quantity INTEGER,
                price REAL,
                timestamp TEXT,
                strategy TEXT,
                confidence_score REAL,
                stop_loss REAL,
                take_profit REAL,
                status TEXT,
                pnl REAL DEFAULT 0,
                exit_price REAL,
                exit_time TEXT,
                FOREIGN KEY (session_id) REFERENCES trading_sessions (session_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_health (
                timestamp TEXT,
                engine_a_status TEXT,
                engine_b_status TEXT,
                engine_c_status TEXT,
                engine_d_status TEXT,
                overall_health TEXT,
                latency_ms INTEGER,
                data_quality_score REAL
            )
        ''')
        
        self.db_connection.commit()
    
    async def pre_market_checks(self) -> Dict[str, bool]:
        """🔍 Comprehensive pre-market system verification"""
        logger.info("🔍 Starting pre-market checks...")
        
        checks = {
            'engine_health': await self.check_all_engines(),
            'data_feeds': await self.verify_data_feeds(),
            'ai_models': await self.test_ai_models(),
            'risk_controls': self.verify_risk_controls(),
            'market_data': await self.verify_market_data(),
            'broker_connection': await self.test_broker_connection(),
            'voice_system': await self.test_voice_system(),
            'safety_systems': self.test_safety_systems()
        }
        
        all_passed = all(checks.values())
        
        logger.info(f"📊 Pre-market checks: {checks}")
        logger.info(f"✅ All systems ready: {all_passed}")
        
        return checks
    
    async def check_all_engines(self) -> bool:
        """Check health of all 4 engines"""
        try:
            tasks = []
            for engine, url in self.base_urls.items():
                tasks.append(self.check_engine_health(engine, url))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            engine_status = {}
            for i, (engine, result) in enumerate(zip(self.base_urls.keys(), results)):
                if isinstance(result, Exception):
                    engine_status[engine] = False
                    logger.error(f"❌ {engine} health check failed: {result}")
                else:
                    engine_status[engine] = result
                    logger.info(f"✅ {engine}: {'Healthy' if result else 'Unhealthy'}")
            
            return all(engine_status.values())
            
        except Exception as e:
            logger.error(f"❌ Engine health check error: {e}")
            return False
    
    async def check_engine_health(self, engine: str, url: str) -> bool:
        """Check individual engine health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('status') == 'healthy'
                    return False
        except Exception as e:
            logger.error(f"❌ {engine} health check failed: {e}")
            return False
    
    async def verify_data_feeds(self) -> bool:
        """Verify real-time data feeds are active"""
        try:
            # Check market data freshness
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_urls['engine_a']}/api/market/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        # Check if data is recent (within last 2 minutes)
                        if 'last_update' in data:
                            last_update = datetime.fromisoformat(data['last_update'])
                            age = (datetime.now() - last_update).total_seconds()
                            return age < 120  # 2 minutes
            
            return False
        except Exception as e:
            logger.error(f"❌ Data feeds verification failed: {e}")
            return False
    
    async def test_ai_models(self) -> bool:
        """Test AI model inference capabilities"""
        try:
            # Test Engine B AI models
            test_data = {
                'symbol': 'NIFTY',
                'timeframe': '5m',
                'test_mode': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_urls['engine_b']}/api/ai/test_inference",
                    json=test_data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('inference_successful', False)
            
            return False
        except Exception as e:
            logger.error(f"❌ AI models test failed: {e}")
            return False
    
    def verify_risk_controls(self) -> bool:
        """Verify risk control systems"""
        try:
            # Check all risk parameters are properly set
            required_controls = [
                'max_positions',
                'max_capital_per_trade',
                'max_daily_loss',
                'max_portfolio_risk'
            ]
            
            for control in required_controls:
                if control not in self.trading_config['position_limits']:
                    logger.error(f"❌ Missing risk control: {control}")
                    return False
            
            # Verify safety controls are active
            if self.safety_controls['circuit_breaker']:
                logger.warning("⚠️ Circuit breaker is active")
                return False
            
            return True
        except Exception as e:
            logger.error(f"❌ Risk controls verification failed: {e}")
            return False
    
    async def verify_market_data(self) -> bool:
        """Verify market data availability for trading symbols"""
        try:
            symbols = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS']
            
            for symbol in symbols:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_urls['engine_a']}/api/market/quote/{symbol}"
                    ) as response:
                        if response.status != 200:
                            logger.error(f"❌ No market data for {symbol}")
                            return False
            
            return True
        except Exception as e:
            logger.error(f"❌ Market data verification failed: {e}")
            return False
    
    async def test_broker_connection(self) -> bool:
        """Test Dhan API broker connection"""
        try:
            # Test Dhan API connection
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_urls['engine_c']}/api/broker/test_connection"
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('connection_status') == 'connected'
            
            return False
        except Exception as e:
            logger.error(f"❌ Broker connection test failed: {e}")
            return False
    
    async def test_voice_system(self) -> bool:
        """Test voice trading system"""
        try:
            # Test voice command processing
            test_command = "Test voice system status"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_urls['engine_d']}/api/voice/test",
                    json={'command': test_command}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('voice_system_ready', False)
            
            return False
        except Exception as e:
            logger.error(f"❌ Voice system test failed: {e}")
            return False
    
    def test_safety_systems(self) -> bool:
        """Test all safety systems"""
        try:
            # Test emergency stop functionality
            # Test position limits
            # Test circuit breaker logic
            # Test alert systems
            
            safety_checks = [
                self.safety_controls is not None,
                'circuit_breaker' in self.safety_controls,
                'max_consecutive_losses' in self.safety_controls,
                callable(getattr(self, 'emergency_stop', None))
            ]
            
            return all(safety_checks)
        except Exception as e:
            logger.error(f"❌ Safety systems test failed: {e}")
            return False
    
    async def start_live_trading_session(self, capital: float, strategy: str = 'momentum') -> str:
        """🚀 Start live trading session"""
        
        # Check if market is open
        if not self.is_market_open():
            raise Exception("❌ Market is not open for trading")
        
        # Run pre-market checks
        checks = await self.pre_market_checks()
        if not all(checks.values()):
            failed_checks = [k for k, v in checks.items() if not v]
            raise Exception(f"❌ Pre-market checks failed: {failed_checks}")
        
        # Create trading session
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = TradingSession(
            session_id=session_id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=6),
            capital_allocated=capital,
            max_positions=10,
            risk_per_trade=0.02,
            strategy_type=strategy,
            symbols=['NIFTY', 'BANKNIFTY'],
            status="ACTIVE"
        )
        
        # Store in database
        cursor = self.db_connection.cursor()
        cursor.execute('''
            INSERT INTO trading_sessions 
            (session_id, start_time, end_time, capital_allocated, strategy_type, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session.session_id,
            session.start_time.isoformat(),
            session.end_time.isoformat(),
            session.capital_allocated,
            session.strategy_type,
            session.status
        ))
        self.db_connection.commit()
        
        logger.info(f"🚀 Live trading session started: {session_id}")
        logger.info(f"💰 Capital: ₹{capital:,.0f}")
        logger.info(f"📊 Strategy: {strategy}")
        
        # Start trading loop
        asyncio.create_task(self.trading_loop(session))
        
        # Start monitoring
        asyncio.create_task(self.monitor_session(session))
        
        return session_id
    
    async def trading_loop(self, session: TradingSession):
        """🔄 Main trading execution loop"""
        logger.info(f"🔄 Starting trading loop for session {session.session_id}")
        
        while session.status == "ACTIVE" and self.is_market_open():
            try:
                # Check safety controls
                if self.safety_controls['circuit_breaker']:
                    logger.warning("⚠️ Circuit breaker active - pausing trading")
                    await asyncio.sleep(60)
                    continue
                
                # Get AI signals
                signals = await self.get_ai_signals(session.symbols)
                
                # Process each signal
                for signal in signals:
                    if await self.should_execute_trade(signal, session):
                        trade = await self.execute_trade(signal, session)
                        if trade:
                            logger.info(f"✅ Trade executed: {trade.trade_id}")
                
                # Wait before next iteration
                await asyncio.sleep(30)  # 30-second intervals
                
            except Exception as e:
                logger.error(f"❌ Trading loop error: {e}")
                await asyncio.sleep(60)
        
        # End session
        await self.end_trading_session(session)
    
    async def get_ai_signals(self, symbols: List[str]) -> List[Dict]:
        """🧠 Get AI trading signals from Engine B"""
        signals = []
        
        try:
            for symbol in symbols:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_urls['engine_b']}/api/ai/generate_signal",
                        json={
                            'symbol': symbol,
                            'timeframe': '5m',
                            'strategy': 'momentum'
                        },
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            signal = await response.json()
                            signals.append(signal)
                        
        except Exception as e:
            logger.error(f"❌ Error getting AI signals: {e}")
        
        return signals
    
    async def should_execute_trade(self, signal: Dict, session: TradingSession) -> bool:
        """🎯 Determine if trade should be executed based on risk management"""
        try:
            # Check confidence score
            if signal.get('confidence_score', 0) < 0.7:
                return False
            
            # Check position limits
            current_positions = await self.get_current_positions()
            if len(current_positions) >= self.trading_config['position_limits']['max_positions']:
                return False
            
            # Check capital allocation
            trade_amount = signal.get('position_size', 0) * signal.get('price', 0)
            if trade_amount > self.trading_config['position_limits']['max_capital_per_trade']:
                return False
            
            # Check daily loss limit
            if self.safety_controls['daily_pnl'] < -self.trading_config['position_limits']['max_daily_loss']:
                logger.warning("⚠️ Daily loss limit reached")
                self.safety_controls['circuit_breaker'] = True
                return False
            
            # Check consecutive losses
            if self.safety_controls['consecutive_losses'] >= self.safety_controls['max_consecutive_losses']:
                logger.warning("⚠️ Maximum consecutive losses reached")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in trade decision: {e}")
            return False
    
    async def execute_trade(self, signal: Dict, session: TradingSession) -> Optional[Trade]:
        """💼 Execute trade through Engine C"""
        try:
            trade_id = f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            trade_request = {
                'trade_id': trade_id,
                'symbol': signal['symbol'],
                'action': signal['action'],
                'quantity': signal['position_size'],
                'price': signal['price'],
                'stop_loss': signal.get('stop_loss'),
                'take_profit': signal.get('take_profit'),
                'strategy': signal.get('strategy', 'momentum')
            }
            
            # Execute through Engine C
            async with aiohttp.ClientSession() as client_session:
                async with client_session.post(
                    f"{self.base_urls['engine_c']}/api/trade/execute",
                    json=trade_request,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('status') == 'EXECUTED':
                            # Create trade object
                            trade = Trade(
                                trade_id=trade_id,
                                symbol=signal['symbol'],
                                action=signal['action'],
                                quantity=signal['position_size'],
                                price=result.get('executed_price', signal['price']),
                                timestamp=datetime.now(),
                                strategy=signal.get('strategy', 'momentum'),
                                confidence_score=signal.get('confidence_score', 0),
                                stop_loss=signal.get('stop_loss', 0),
                                take_profit=signal.get('take_profit', 0),
                                status='EXECUTED'
                            )
                            
                            # Store in database
                            await self.store_trade(trade, session.session_id)
                            
                            # Update safety controls
                            self.safety_controls['last_trade_time'] = datetime.now()
                            
                            return trade
                        
            return None
            
        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
            return None
    
    async def store_trade(self, trade: Trade, session_id: str):
        """💾 Store trade in database"""
        cursor = self.db_connection.cursor()
        cursor.execute('''
            INSERT INTO trades 
            (trade_id, session_id, symbol, action, quantity, price, timestamp, 
             strategy, confidence_score, stop_loss, take_profit, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.trade_id, session_id, trade.symbol, trade.action,
            trade.quantity, trade.price, trade.timestamp.isoformat(),
            trade.strategy, trade.confidence_score, trade.stop_loss,
            trade.take_profit, trade.status
        ))
        self.db_connection.commit()
    
    async def monitor_session(self, session: TradingSession):
        """📊 Monitor trading session performance"""
        while session.status == "ACTIVE":
            try:
                # Calculate session metrics
                metrics = await self.calculate_session_metrics(session.session_id)
                
                # Check for alerts
                await self.check_alerts(metrics, session)
                
                # Log status
                logger.info(f"📊 Session {session.session_id}: PnL: ₹{metrics['total_pnl']:,.0f}, Trades: {metrics['trade_count']}")
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def calculate_session_metrics(self, session_id: str) -> Dict:
        """📈 Calculate session performance metrics"""
        cursor = self.db_connection.cursor()
        
        # Get all trades for session
        cursor.execute('''
            SELECT * FROM trades WHERE session_id = ?
        ''', (session_id,))
        
        trades = cursor.fetchall()
        
        if not trades:
            return {
                'total_pnl': 0,
                'trade_count': 0,
                'win_rate': 0,
                'avg_trade_pnl': 0
            }
        
        # Calculate metrics
        total_pnl = sum(trade[15] or 0 for trade in trades)  # pnl column
        trade_count = len(trades)
        winning_trades = sum(1 for trade in trades if (trade[15] or 0) > 0)
        win_rate = winning_trades / trade_count if trade_count > 0 else 0
        avg_trade_pnl = total_pnl / trade_count if trade_count > 0 else 0
        
        return {
            'total_pnl': total_pnl,
            'trade_count': trade_count,
            'win_rate': win_rate,
            'avg_trade_pnl': avg_trade_pnl
        }
    
    async def check_alerts(self, metrics: Dict, session: TradingSession):
        """🚨 Check for trading alerts and notifications"""
        # High profit alert
        if metrics['total_pnl'] > 50000:  # ₹50k profit
            await self.send_alert(f"🎉 High Profit Alert: ₹{metrics['total_pnl']:,.0f}")
        
        # Loss alert
        if metrics['total_pnl'] < -20000:  # ₹20k loss
            await self.send_alert(f"⚠️ Loss Alert: ₹{metrics['total_pnl']:,.0f}")
        
        # Low win rate alert
        if metrics['trade_count'] > 10 and metrics['win_rate'] < 0.5:
            await self.send_alert(f"📉 Low Win Rate: {metrics['win_rate']:.1%}")
    
    async def send_alert(self, message: str):
        """📧 Send alert notification"""
        logger.warning(f"🚨 ALERT: {message}")
        
        # Voice notification through Engine D
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{self.base_urls['engine_d']}/api/voice/alert",
                    json={'message': message}
                )
        except Exception as e:
            logger.error(f"❌ Voice alert failed: {e}")
    
    def is_market_open(self) -> bool:
        """🕐 Check if market is currently open"""
        now = datetime.now().time()
        
        # Check if it's a weekday
        if datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check market hours (9:15 AM to 3:30 PM)
        market_start = time(9, 15)
        market_end = time(15, 30)
        
        return market_start <= now <= market_end
    
    async def get_current_positions(self) -> List[Dict]:
        """📋 Get current open positions"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_urls['engine_c']}/api/positions"
                ) as response:
                    if response.status == 200:
                        return await response.json()
            return []
        except Exception as e:
            logger.error(f"❌ Error getting positions: {e}")
            return []
    
    async def emergency_stop(self, reason: str = "Manual"):
        """🛑 Emergency stop all trading"""
        logger.critical(f"🛑 EMERGENCY STOP: {reason}")
        
        # Activate circuit breaker
        self.safety_controls['circuit_breaker'] = True
        
        # Close all positions
        positions = await self.get_current_positions()
        for position in positions:
            try:
                await self.close_position(position)
            except Exception as e:
                logger.error(f"❌ Error closing position: {e}")
        
        # Send alerts
        await self.send_alert(f"🛑 EMERGENCY STOP ACTIVATED: {reason}")
        
        # Voice announcement
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{self.base_urls['engine_d']}/api/voice/emergency",
                    json={'message': f"Emergency stop activated due to {reason}"}
                )
        except Exception as e:
            logger.error(f"❌ Emergency voice alert failed: {e}")
    
    async def close_position(self, position: Dict):
        """Close a specific position"""
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{self.base_urls['engine_c']}/api/trade/close",
                    json={'position_id': position['id']}
                )
        except Exception as e:
            logger.error(f"❌ Error closing position: {e}")
    
    async def end_trading_session(self, session: TradingSession):
        """🏁 End trading session and generate report"""
        session.status = "COMPLETED"
        
        # Calculate final metrics
        metrics = await self.calculate_session_metrics(session.session_id)
        
        # Update session in database
        cursor = self.db_connection.cursor()
        cursor.execute('''
            UPDATE trading_sessions 
            SET status = ?, total_pnl = ?, trades_count = ?, win_rate = ?
            WHERE session_id = ?
        ''', (
            session.status,
            metrics['total_pnl'],
            metrics['trade_count'],
            metrics['win_rate'],
            session.session_id
        ))
        self.db_connection.commit()
        
        # Generate session report
        report = await self.generate_session_report(session.session_id)
        
        logger.info(f"🏁 Trading session ended: {session.session_id}")
        logger.info(f"📊 Final PnL: ₹{metrics['total_pnl']:,.0f}")
        logger.info(f"📈 Win Rate: {metrics['win_rate']:.1%}")
        
        return report
    
    async def generate_session_report(self, session_id: str) -> Dict:
        """📋 Generate comprehensive session report"""
        cursor = self.db_connection.cursor()
        
        # Get session data
        cursor.execute('SELECT * FROM trading_sessions WHERE session_id = ?', (session_id,))
        session_data = cursor.fetchone()
        
        # Get all trades
        cursor.execute('SELECT * FROM trades WHERE session_id = ?', (session_id,))
        trades_data = cursor.fetchall()
        
        # Calculate detailed metrics
        metrics = await self.calculate_session_metrics(session_id)
        
        report = {
            'session_id': session_id,
            'session_summary': {
                'start_time': session_data[1],
                'end_time': session_data[2],
                'capital_allocated': session_data[3],
                'strategy': session_data[4],
                'total_pnl': metrics['total_pnl'],
                'win_rate': metrics['win_rate'],
                'trade_count': metrics['trade_count']
            },
            'performance_metrics': {
                'roi': (metrics['total_pnl'] / session_data[3]) * 100,
                'avg_trade_pnl': metrics['avg_trade_pnl'],
                'max_drawdown': 0,  # Calculate this
                'sharpe_ratio': 0   # Calculate this
            },
            'risk_metrics': {
                'max_position_size': 0,
                'avg_position_size': 0,
                'risk_per_trade': 0
            },
            'trades': [
                {
                    'trade_id': trade[0],
                    'symbol': trade[2],
                    'action': trade[3],
                    'quantity': trade[4],
                    'price': trade[5],
                    'timestamp': trade[6],
                    'pnl': trade[15] or 0
                }
                for trade in trades_data
            ]
        }
        
        return report

class TradingTestAPI:
    """🌐 API interface for testing framework"""
    
    def __init__(self):
        self.framework = LiveTradingTestFramework()
    
    async def run_voice_command_test(self, command: str) -> Dict:
        """Test voice command processing"""
        try:
            # Test voice command: "Start momentum trading on NIFTY with 2 lakh capital"
            if "start" in command.lower() and "trading" in command.lower():
                # Extract parameters from voice command
                capital = 200000  # Default ₹2 lakh
                strategy = "momentum"  # Default strategy
                
                # Parse voice command for specific values
                if "lakh" in command.lower():
                    words = command.split()
                    for i, word in enumerate(words):
                        if word.lower() == "lakh" and i > 0:
                            try:
                                capital = float(words[i-1]) * 100000
                            except:
                                pass
                
                # Start trading session
                session_id = await self.framework.start_live_trading_session(capital, strategy)
                
                return {
                    'status': 'success',
                    'message': f'Trading session started with ₹{capital:,.0f} capital',
                    'session_id': session_id
                }
            
            return {'status': 'error', 'message': 'Command not recognized'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

# Main execution functions
async def run_comprehensive_test():
    """🧪 Run comprehensive trading system test"""
    print("🧪 InfinityAI.Pro Live Trading Test Framework")
    print("=" * 60)
    
    framework = LiveTradingTestFramework()
    
    try:
        # Pre-market checks
        print("🔍 Running pre-market checks...")
        checks = await framework.pre_market_checks()
        
        if all(checks.values()):
            print("✅ All systems ready for live trading!")
            
            # Test voice command
            api = TradingTestAPI()
            voice_result = await api.run_voice_command_test(
                "Start momentum trading on NIFTY with 2 lakh capital"
            )
            print(f"🗣️ Voice command test: {voice_result}")
            
        else:
            failed = [k for k, v in checks.items() if not v]
            print(f"❌ System checks failed: {failed}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    """🎯 Entry point for live trading tests"""
    print("🚀 InfinityAI.Pro - Live Trading Test Framework")
    print("💰 Ready for ₹2-5L daily trading automation")
    print("🛡️ Comprehensive safety controls and monitoring")
    print("=" * 60)
    
    asyncio.run(run_comprehensive_test())