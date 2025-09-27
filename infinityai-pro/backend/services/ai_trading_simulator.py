# ai_trading_simulator.py
"""
AI-Powered Trading Simulator with Real-Time Data and ML Optimization
Combines market data fetching, trade simulation, and reinforcement learning
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pickle
import os
import json
from collections import deque

from services.market_data_ai import MarketDataAI
from services.paper_bot import PaperBot
from services.model_train import featurize
from utils.config import CONFIG

logger = logging.getLogger(__name__)

class AITradingSimulator:
    """
    Advanced AI trading simulator that:
    1. Fetches real-time market data
    2. Simulates trades with current ML models
    3. Learns from results using reinforcement learning
    4. Continuously optimizes trading strategies
    """

    def __init__(self, config=CONFIG):
        self.config = config
        self.market_data = None
        self.paper_bot = None
        self.initialized = False

        # RL components
        self.state_size = 15  # Technical indicators + market data
        self.action_size = 3  # BUY, SELL, HOLD
        self.memory = deque(maxlen=10000)
        self.gamma = 0.95  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001

        # Performance tracking
        self.episode_rewards = []
        self.portfolio_values = []
        self.win_rate_history = []
        self.sharpe_ratio_history = []

        # Model paths
        self.rl_model_path = os.path.join(self.config.MODEL_DIR, 'rl_trading_model.pkl')
        self.performance_log_path = os.path.join(self.config.MODEL_DIR, 'simulation_performance.json')

        # Ensure directories exist
        os.makedirs(self.config.MODEL_DIR, exist_ok=True)
        os.makedirs(self.config.BACKTEST_DATA_PATH, exist_ok=True)

    async def initialize(self):
        """Initialize all components"""
        if self.initialized:
            return

        logger.info("🚀 Initializing AI Trading Simulator...")

        # Initialize market data service
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "BD03X0M5F86UW8PP")
        self.market_data = MarketDataAI(api_key)
        await self.market_data.initialize()

        # Initialize paper trading bot
        self.paper_bot = PaperBot(self.config)

        # Load existing RL model if available
        self.load_rl_model()

        self.initialized = True
        logger.info("✅ AI Trading Simulator initialized")

    async def close(self):
        """Clean up resources"""
        if self.market_data:
            await self.market_data.close()

    def get_state(self, symbol: str, df: pd.DataFrame) -> np.ndarray:
        """Extract state representation from market data"""
        try:
            # Get latest data point
            latest = df.iloc[-1]

            # Technical indicators
            macd = latest.get('MACD', 0)
            rsi = latest.get('RSI', 50)
            sma_5 = latest.get('SMA_5', latest.get('close', 0))
            sma_20 = latest.get('SMA_20', latest.get('close', 0))
            ema_12 = latest.get('EMA_12', latest.get('close', 0))
            ema_26 = latest.get('EMA_26', latest.get('close', 0))
            atr = latest.get('ATR', 1)
            vwap = latest.get('VWAP', latest.get('close', 0))

            # Price action
            close = latest.get('close', 0)
            high = latest.get('high', 0)
            low = latest.get('low', 0)
            volume = latest.get('volume', 1000)

            # Returns
            ret_1d = df['close'].pct_change().iloc[-1] if len(df) > 1 else 0
            ret_5d = df['close'].pct_change(5).iloc[-1] if len(df) > 5 else 0

            # Volatility
            vol_20d = df['close'].pct_change().rolling(20).std().iloc[-1] if len(df) > 20 else 0.02

            state = np.array([
                macd, rsi, sma_5, sma_20, ema_12, ema_26,
                atr, vwap, close, high, low, volume,
                ret_1d, ret_5d, vol_20d
            ])

            # Normalize state
            state = (state - np.mean(state)) / (np.std(state) + 1e-8)

            return state

        except Exception as e:
            logger.error(f"Error getting state for {symbol}: {e}")
            return np.zeros(self.state_size)

    def choose_action(self, state: np.ndarray) -> int:
        """Choose action using epsilon-greedy policy"""
        if np.random.rand() <= self.epsilon:
            return np.random.choice(self.action_size)  # Explore
        else:
            # Exploit - use ML model prediction
            if hasattr(self, 'rl_model') and self.rl_model is not None:
                try:
                    state_reshaped = state.reshape(1, -1)
                    if hasattr(self.rl_model, 'predict_proba'):
                        probs = self.rl_model.predict_proba(state_reshaped)[0]
                        return np.argmax(probs)
                    else:
                        pred = self.rl_model.predict(state_reshaped)[0]
                        return int(pred)
                except Exception as e:
                    logger.warning(f"RL model prediction failed: {e}")

            return np.random.choice(self.action_size)  # Fallback to random

    def remember(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        """Store experience in memory"""
        self.memory.append((state, action, reward, next_state, done))

    def calculate_reward(self, action: int, pnl: float, market_return: float) -> float:
        """Calculate reward based on trading performance"""
        base_reward = pnl * 100  # Scale PnL

        # Bonus for beating market
        if pnl > market_return:
            base_reward += 10

        # Penalty for wrong direction vs market
        if (action == 0 and market_return < 0) or (action == 1 and market_return > 0):
            base_reward -= 5

        # Penalty for holding during volatile periods
        if action == 2 and abs(market_return) > 0.02:  # 2% daily move
            base_reward -= 2

        return base_reward

    async def simulate_trading_day(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Run one day of AI-powered trading simulation"""
        if symbols is None:
            symbols = self.config.SYMBOLS

        total_pnl = 0
        trades_executed = 0
        episode_reward = 0

        logger.info(f"🤖 Starting AI trading simulation for {len(symbols)} symbols")

        for symbol in symbols:
            try:
                # Fetch real-time data
                df = await self.market_data.get_intraday_data(symbol, "5min")
                if df is None or len(df) < 50:
                    logger.warning(f"Insufficient data for {symbol}")
                    continue

                # Featurize data
                df_feat = featurize(df.reset_index())

                # Get current state
                state = self.get_state(symbol, df_feat)

                # Choose action
                action = self.choose_action(state)

                # Execute trade simulation
                if action == 0:  # BUY
                    signal = "BUY"
                elif action == 1:  # SELL
                    signal = "SELL"
                else:  # HOLD
                    signal = "HOLD"

                # Simulate trade using paper bot logic
                if signal != "HOLD":
                    # Get premium estimate
                    premium = max(10.0, df_feat.iloc[-1]['close'] * 0.0006)

                    # Position sizing
                    risk_amount = self.paper_bot.equity * self.config.RISK_PER_TRADE_PCT
                    stop_loss_amount = premium * 0.6
                    contracts = int(max(1, risk_amount / (stop_loss_amount + 1e-9)))

                    cost = contracts * premium
                    if cost <= self.paper_bot.equity * 0.3:
                        # Simulate trade outcome
                        market_return = df_feat['close'].pct_change().iloc[-1] if len(df_feat) > 1 else 0
                        pnl = np.random.choice([1, -1], p=[0.55, 0.45]) * cost * np.random.uniform(0.2, 1.5)

                        # Update paper bot equity
                        self.paper_bot.equity = self.paper_bot.equity - cost + cost + pnl

                        total_pnl += pnl
                        trades_executed += 1

                        # Calculate reward
                        reward = self.calculate_reward(action, pnl/cost, market_return)
                        episode_reward += reward

                        # Get next state for learning
                        next_state = self.get_state(symbol, df_feat)

                        # Store experience
                        self.remember(state, action, reward, next_state, False)

                        logger.info(".2f"
            except Exception as e:
                logger.error(f"Error simulating {symbol}: {e}")
                continue

        # Update performance metrics
        self.portfolio_values.append(self.paper_bot.equity)
        self.episode_rewards.append(episode_reward)

        # Calculate win rate (simplified)
        if trades_executed > 0:
            win_rate = len([r for r in self.episode_rewards[-10:] if r > 0]) / min(10, len(self.episode_rewards))
            self.win_rate_history.append(win_rate)

        # Calculate Sharpe ratio (simplified)
        if len(self.portfolio_values) > 10:
            returns = pd.Series(self.portfolio_values).pct_change().dropna()
            if len(returns) > 0 and returns.std() > 0:
                sharpe = returns.mean() / returns.std() * np.sqrt(252)  # Annualized
                self.sharpe_ratio_history.append(sharpe)

        # Decay exploration rate
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        # Save performance data
        self.save_performance_data()

        result = {
            "total_pnl": total_pnl,
            "trades_executed": trades_executed,
            "equity": self.paper_bot.equity,
            "episode_reward": episode_reward,
            "epsilon": self.epsilon,
            "win_rate": self.win_rate_history[-1] if self.win_rate_history else 0,
            "sharpe_ratio": self.sharpe_ratio_history[-1] if self.sharpe_ratio_history else 0
        }

        logger.info(f"📊 Simulation complete: PnL: ₹{total_pnl:.2f}, Equity: ₹{self.paper_bot.equity:.2f}, Trades: {trades_executed}")
        return result

    def train_rl_model(self, batch_size: int = 32):
        """Train RL model on accumulated experiences"""
        if len(self.memory) < batch_size:
            return

        # Sample batch from memory
        batch = np.random.choice(len(self.memory), batch_size, replace=False)
        states, actions, rewards, next_states, dones = [], [], [], [], []

        for idx in batch:
            state, action, reward, next_state, done = self.memory[idx]
            states.append(state)
            actions.append(action)
            rewards.append(reward)
            next_states.append(next_state)
            dones.append(done)

        states = np.array(states)
        next_states = np.array(next_states)

        # Simple Q-learning update (simplified RL)
        # In a real implementation, you'd use a proper RL framework like Stable Baselines

        # For now, we'll use the existing ML training approach
        # Convert experiences to supervised learning format
        X = states
        y = actions  # Simplified: predict best action

        # Add some noise to prevent overfitting
        y = y + np.random.normal(0, 0.1, size=y.shape)

        # Train/update model
        try:
            if not hasattr(self, 'rl_model') or self.rl_model is None:
                # Initialize simple model
                from sklearn.ensemble import RandomForestClassifier
                self.rl_model = RandomForestClassifier(n_estimators=100, random_state=42)

            # Fit on recent experiences
            recent_states = np.array([exp[0] for exp in list(self.memory)[-1000:]])
            recent_actions = np.array([exp[1] for exp in list(self.memory)[-1000:]])

            if len(recent_states) >= 10:
                self.rl_model.fit(recent_states, recent_actions)
                self.save_rl_model()

                logger.info("🧠 RL model updated with recent experiences")

        except Exception as e:
            logger.error(f"Error training RL model: {e}")

    async def run_continuous_simulation(self, days: int = 30, train_interval: int = 5):
        """Run continuous simulation with periodic training"""
        logger.info(f"🚀 Starting continuous AI trading simulation for {days} days")

        for day in range(days):
            try:
                # Run daily simulation
                result = await self.simulate_trading_day()

                # Train model periodically
                if (day + 1) % train_interval == 0:
                    self.train_rl_model()
                    logger.info(f"📈 Model training completed (Day {day + 1})")

                # Log progress
                if (day + 1) % 10 == 0:
                    self.log_progress(day + 1)

                # Small delay between days
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in simulation day {day + 1}: {e}")
                continue

        logger.info("🎯 Continuous simulation completed!")
        return self.get_performance_summary()

    def log_progress(self, day: int):
        """Log simulation progress"""
        if not self.episode_rewards:
            return

        recent_rewards = self.episode_rewards[-10:]
        avg_reward = np.mean(recent_rewards)
        win_rate = np.mean(self.win_rate_history[-10:]) if self.win_rate_history else 0

        logger.info(f"📊 Day {day}: Avg Reward: {avg_reward:.2f}, Win Rate: {win_rate:.2%}, "
                   f"Equity: ₹{self.paper_bot.equity:.2f}, Epsilon: {self.epsilon:.3f}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.episode_rewards:
            return {"error": "No simulation data available"}

        total_return = (self.paper_bot.equity - self.config.CAPITAL) / self.config.CAPITAL
        total_trades = len([r for r in self.episode_rewards if r != 0])

        return {
            "total_return_pct": total_return * 100,
            "final_equity": self.paper_bot.equity,
            "total_trades": total_trades,
            "avg_reward_per_episode": np.mean(self.episode_rewards),
            "best_episode_reward": max(self.episode_rewards),
            "worst_episode_reward": min(self.episode_rewards),
            "win_rate": np.mean(self.win_rate_history) if self.win_rate_history else 0,
            "sharpe_ratio": np.mean(self.sharpe_ratio_history) if self.sharpe_ratio_history else 0,
            "total_episodes": len(self.episode_rewards),
            "final_epsilon": self.epsilon,
            "model_trained": hasattr(self, 'rl_model') and self.rl_model is not None
        }

    def save_rl_model(self):
        """Save RL model to disk"""
        try:
            with open(self.rl_model_path, 'wb') as f:
                pickle.dump(self.rl_model, f)
            logger.info(f"💾 RL model saved to {self.rl_model_path}")
        except Exception as e:
            logger.error(f"Error saving RL model: {e}")

    def load_rl_model(self):
        """Load RL model from disk"""
        try:
            if os.path.exists(self.rl_model_path):
                with open(self.rl_model_path, 'rb') as f:
                    self.rl_model = pickle.load(f)
                logger.info(f"📂 RL model loaded from {self.rl_model_path}")
            else:
                self.rl_model = None
                logger.info("📝 No existing RL model found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading RL model: {e}")
            self.rl_model = None

    def save_performance_data(self):
        """Save performance metrics to JSON"""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "portfolio_values": self.portfolio_values[-100:],  # Last 100 values
                "episode_rewards": self.episode_rewards[-100:],
                "win_rate_history": self.win_rate_history[-50:],
                "sharpe_ratio_history": self.sharpe_ratio_history[-50:],
                "current_equity": self.paper_bot.equity if self.paper_bot else 0
            }

            with open(self.performance_log_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving performance data: {e}")

    async def get_realtime_quote(self, symbol: str) -> Dict:
        """Get real-time quote for monitoring"""
        if not self.market_data:
            return {"error": "Market data service not initialized"}

        return await self.market_data.get_quote(symbol)

    async def health_check(self) -> Dict:
        """Health check for AI trading simulator"""
        return {
            "status": "healthy" if self.initialized else "unhealthy",
            "service": "ai_trading_simulator",
            "market_data": self.market_data.health_check() if self.market_data else {"status": "not_initialized"},
            "paper_bot_equity": self.paper_bot.equity if self.paper_bot else 0,
            "rl_model_loaded": hasattr(self, 'rl_model') and self.rl_model is not None,
            "memory_size": len(self.memory),
            "epsilon": self.epsilon
        }


# Global AI trading simulator instance
ai_trading_simulator = AITradingSimulator()


async def main():
    """Main function for testing the AI trading simulator"""
    simulator = AITradingSimulator()

    try:
        await simulator.initialize()

        # Run a short simulation
        result = await simulator.simulate_trading_day(["AAPL", "GOOGL"])
        print("Simulation result:", result)

        # Get performance summary
        summary = simulator.get_performance_summary()
        print("Performance summary:", summary)

    finally:
        await simulator.close()


if __name__ == "__main__":
    asyncio.run(main())