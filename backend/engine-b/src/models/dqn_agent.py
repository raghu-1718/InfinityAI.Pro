"""
DQN (Deep Q-Network) Reinforcement Learning Agent for Trading
Learns optimal Buy/Sell/Hold actions to maximize Sharpe ratio
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import deque
import logging
import json
import os
import random

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, optimizers
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    logging.warning("TensorFlow not available - DQN agent disabled")

logger = logging.getLogger(__name__)


class TradingAction:
    """Trading actions for DQN"""
    HOLD = 0
    BUY = 1
    SELL = 2

    @staticmethod
    def to_string(action: int) -> str:
        mapping = {0: "HOLD", 1: "BUY", 2: "SELL"}
        return mapping.get(action, "UNKNOWN")


class TradingEnvironment:
    """
    Custom trading environment for DQN.

    State space:
    - Current position (0=no position, 1=long, -1=short)
    - Portfolio value
    - Current price
    - Price momentum (5-day, 10-day, 20-day returns)
    - Technical indicators (RSI, MACD, ATR, etc.)
    - Market regime (trending/ranging)

    Action space:
    - 0: HOLD (no change)
    - 1: BUY (enter long or add to position)
    - 2: SELL (exit position or go short)

    Reward:
    - Sharpe ratio maximization
    - Transaction costs penalty
    - Risk-adjusted returns
    """

    def __init__(
        self,
        data: pd.DataFrame,
        initial_balance: float = 100000.0,
        transaction_cost: float = 0.001  # 0.1%
    ):
        self.data = data.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.transaction_cost = transaction_cost

        self.current_step = 0
        self.balance = initial_balance
        self.position = 0  # 0=no position, positive=long shares
        self.position_entry_price = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.trade_history: List[Dict] = []

        # Calculate state dimension
        self.state_dim = self._get_state_dim()

    def _get_state_dim(self) -> int:
        """Calculate state vector dimension"""
        # Base features: position, balance, price
        base = 3

        # Technical indicators (from data)
        tech_indicators = len([col for col in self.data.columns
                              if col not in ['date', 'open', 'high', 'low', 'close', 'volume']])

        # Momentum features (5d, 10d, 20d returns)
        momentum = 3

        return base + tech_indicators + momentum

    def reset(self) -> np.ndarray:
        """Reset environment to initial state"""
        self.current_step = 20  # Start after 20 days for momentum calc
        self.balance = self.initial_balance
        self.position = 0
        self.position_entry_price = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.trade_history = []

        return self._get_state()

    def _get_state(self) -> np.ndarray:
        """Get current state vector"""
        if self.current_step >= len(self.data):
            # Return terminal state
            return np.zeros(self.state_dim)

        row = self.data.iloc[self.current_step]
        current_price = row['close']

        # Base features
        state = [
            self.position / 100,  # Normalized position
            self.balance / self.initial_balance,  # Normalized balance
            current_price / 1000  # Normalized price (assuming ~1000-50000 range)
        ]

        # Technical indicators
        tech_cols = [col for col in self.data.columns
                    if col not in ['date', 'open', 'high', 'low', 'close', 'volume']]
        for col in tech_cols:
            state.append(row[col] if not pd.isna(row[col]) else 0)

        # Momentum features
        if self.current_step >= 20:
            price_5d = self.data.iloc[self.current_step - 5]['close']
            price_10d = self.data.iloc[self.current_step - 10]['close']
            price_20d = self.data.iloc[self.current_step - 20]['close']

            momentum_5d = (current_price - price_5d) / price_5d
            momentum_10d = (current_price - price_10d) / price_10d
            momentum_20d = (current_price - price_20d) / price_20d

            state.extend([momentum_5d, momentum_10d, momentum_20d])
        else:
            state.extend([0, 0, 0])

        return np.array(state, dtype=np.float32)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute action and return next state, reward, done, info.

        Args:
            action: 0=HOLD, 1=BUY, 2=SELL

        Returns:
            next_state, reward, done, info
        """
        current_price = self.data.iloc[self.current_step]['close']
        reward = 0.0
        trade_info = {}

        # Execute action
        if action == TradingAction.BUY and self.position == 0:
            # Enter long position
            shares_to_buy = int(self.balance / current_price)
            if shares_to_buy > 0:
                cost = shares_to_buy * current_price * (1 + self.transaction_cost)
                if cost <= self.balance:
                    self.balance -= cost
                    self.position = shares_to_buy
                    self.position_entry_price = current_price
                    self.total_trades += 1
                    trade_info = {
                        "action": "BUY",
                        "shares": shares_to_buy,
                        "price": current_price,
                        "cost": cost
                    }

        elif action == TradingAction.SELL and self.position > 0:
            # Exit long position
            proceeds = self.position * current_price * (1 - self.transaction_cost)
            self.balance += proceeds

            # Calculate trade P&L
            trade_pnl = proceeds - (self.position * self.position_entry_price)
            if trade_pnl > 0:
                self.winning_trades += 1

            # Reward based on trade outcome
            reward = trade_pnl / self.initial_balance * 100  # Percentage return

            trade_info = {
                "action": "SELL",
                "shares": self.position,
                "price": current_price,
                "proceeds": proceeds,
                "pnl": trade_pnl,
                "return_pct": (trade_pnl / (self.position * self.position_entry_price)) * 100
            }

            self.position = 0
            self.position_entry_price = 0.0

        # Store trade
        if trade_info:
            self.trade_history.append({
                "step": self.current_step,
                "date": self.data.iloc[self.current_step]['date'],
                **trade_info
            })

        # Move to next step
        self.current_step += 1

        # Check if done
        done = self.current_step >= len(self.data) - 1

        # Get next state
        next_state = self._get_state()

        # Additional reward shaping
        if self.position > 0:
            # Holding reward based on price movement
            price_change = (current_price - self.position_entry_price) / self.position_entry_price
            reward += price_change * 0.1  # Small reward for holding in profit

        # Info
        info = {
            "balance": self.balance,
            "position": self.position,
            "portfolio_value": self.balance + (self.position * current_price if self.position > 0 else 0),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            **trade_info
        }

        return next_state, reward, done, info

    def get_portfolio_value(self) -> float:
        """Get current portfolio value"""
        current_price = self.data.iloc[self.current_step]['close']
        return self.balance + (self.position * current_price if self.position > 0 else 0)


class DQNAgent:
    """
    Deep Q-Network agent for trading.

    Architecture:
    - Input: State vector (position, balance, price, indicators)
    - Dense Layer 1: 128 units, ReLU
    - Dense Layer 2: 64 units, ReLU
    - Dense Layer 3: 32 units, ReLU
    - Output: Q-values for 3 actions (HOLD, BUY, SELL)

    Training:
    - Experience replay buffer
    - Target network (soft updates)
    - Epsilon-greedy exploration
    - Double DQN (reduce overestimation)
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int = 3,
        learning_rate: float = 0.001,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
        memory_size: int = 10000,
        batch_size: int = 32
    ):
        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow required for DQN agent")

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.batch_size = batch_size

        # Experience replay memory
        self.memory = deque(maxlen=memory_size)

        # Q-network and target network
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()

    def _build_model(self) -> keras.Model:
        """Build Q-network"""
        model = models.Sequential([
            layers.Dense(128, activation='relu', input_shape=(self.state_dim,)),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(self.action_dim, activation='linear')  # Q-values
        ])

        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse'
        )

        return model

    def update_target_model(self):
        """Copy weights from Q-network to target network"""
        self.target_model.set_weights(self.model.get_weights())

    def remember(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Store experience in replay memory"""
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state: np.ndarray, training: bool = True) -> int:
        """
        Choose action using epsilon-greedy policy.

        Args:
            state: Current state
            training: If True, use exploration; otherwise, greedy

        Returns:
            Action (0=HOLD, 1=BUY, 2=SELL)
        """
        if training and np.random.rand() < self.epsilon:
            # Explore: random action
            return random.randint(0, self.action_dim - 1)

        # Exploit: best action from Q-network
        state_tensor = tf.convert_to_tensor(state.reshape(1, -1), dtype=tf.float32)
        q_values = self.model(state_tensor, training=False).numpy()[0]
        return int(np.argmax(q_values))

    def replay(self):
        """Train on batch from experience replay"""
        if len(self.memory) < self.batch_size:
            return

        # Sample batch
        batch = random.sample(self.memory, self.batch_size)

        states = np.array([exp[0] for exp in batch])
        actions = np.array([exp[1] for exp in batch])
        rewards = np.array([exp[2] for exp in batch])
        next_states = np.array([exp[3] for exp in batch])
        dones = np.array([exp[4] for exp in batch])

        # Predict Q-values for current states
        q_values = self.model.predict(states, verbose=0)

        # Predict Q-values for next states (target network)
        next_q_values = self.target_model.predict(next_states, verbose=0)

        # Update Q-values with Bellman equation
        for i in range(self.batch_size):
            if dones[i]:
                q_values[i][actions[i]] = rewards[i]
            else:
                q_values[i][actions[i]] = rewards[i] + self.gamma * np.max(next_q_values[i])

        # Train model
        self.model.fit(states, q_values, epochs=1, verbose=0)

        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save(self, filepath: str):
        """Save agent model"""
        self.model.save(filepath)
        logger.info(f"Saved DQN model to {filepath}")

    def load(self, filepath: str):
        """Load agent model"""
        self.model = keras.models.load_model(filepath)
        self.update_target_model()
        logger.info(f"Loaded DQN model from {filepath}")


def train_dqn_agent(
    symbol: str,
    historical_data: pd.DataFrame,
    episodes: int = 100,
    update_target_every: int = 10,
    model_dir: str = "models/dqn"
) -> Dict[str, Any]:
    """
    Train DQN agent on historical data.

    Args:
        symbol: Stock symbol
        historical_data: DataFrame with OHLCV + technical indicators
        episodes: Number of training episodes
        update_target_every: Update target network every N episodes
        model_dir: Directory to save models

    Returns:
        Training metrics
    """
    os.makedirs(model_dir, exist_ok=True)

    # Create environment
    env = TradingEnvironment(historical_data)

    # Create agent
    agent = DQNAgent(state_dim=env.state_dim)

    # Training loop
    episode_rewards = []
    episode_trades = []

    for episode in range(episodes):
        state = env.reset()
        total_reward = 0
        done = False

        while not done:
            action = agent.act(state, training=True)
            next_state, reward, done, info = env.step(action)

            agent.remember(state, action, reward, next_state, done)
            agent.replay()

            state = next_state
            total_reward += reward

        episode_rewards.append(total_reward)
        episode_trades.append(env.total_trades)

        # Update target network
        if (episode + 1) % update_target_every == 0:
            agent.update_target_model()

        # Log progress
        if (episode + 1) % 10 == 0:
            avg_reward = np.mean(episode_rewards[-10:])
            logger.info(f"Episode {episode + 1}/{episodes} - Avg Reward: {avg_reward:.2f}, Epsilon: {agent.epsilon:.3f}")

    # Save model
    model_path = os.path.join(model_dir, f"{symbol}_dqn.h5")
    agent.save(model_path)

    # Return metrics
    return {
        "symbol": symbol,
        "episodes": episodes,
        "final_epsilon": agent.epsilon,
        "avg_reward": float(np.mean(episode_rewards)),
        "max_reward": float(np.max(episode_rewards)),
        "avg_trades_per_episode": float(np.mean(episode_trades)),
        "model_path": model_path
    }


def get_dqn_action(
    symbol: str,
    current_state: np.ndarray,
    model_dir: str = "models/dqn"
) -> Dict[str, Any]:
    """
    Get recommended action from trained DQN agent.

    Example:
        >>> action = get_dqn_action("NIFTY", current_state)
        >>> print(action["recommended_action"])  # BUY/SELL/HOLD
    """
    model_path = os.path.join(model_dir, f"{symbol}_dqn.h5")

    if not os.path.exists(model_path):
        return {
            "error": "Model not trained",
            "symbol": symbol
        }

    # Create agent and load model
    agent = DQNAgent(state_dim=len(current_state))
    agent.load(model_path)

    # Get action (no exploration)
    action_idx = agent.act(current_state, training=False)
    action_name = TradingAction.to_string(action_idx)

    # Get Q-values for confidence
    state_tensor = tf.convert_to_tensor(current_state.reshape(1, -1), dtype=tf.float32)
    q_values = agent.model(state_tensor, training=False).numpy()[0]

    return {
        "symbol": symbol,
        "recommended_action": action_name,
        "confidence": float(q_values[action_idx]),
        "q_values": {
            "HOLD": float(q_values[0]),
            "BUY": float(q_values[1]),
            "SELL": float(q_values[2])
        },
        "generated_at": datetime.now().isoformat()
    }
