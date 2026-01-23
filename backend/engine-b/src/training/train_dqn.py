"""
DQN Agent Training Script
Trains Deep Q-Network agent for trading on historical data
"""

import os
import sys
import logging
from datetime import datetime
import argparse
import json
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.dqn_agent import DQNAgent, TradingEnvironment, TradingAction
from training.data_fetcher import get_training_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train_dqn_agent(
    symbol: str = "NIFTY",
    days: int = 730,
    episodes: int = 200,
    update_target_every: int = 10,
    initial_epsilon: float = 1.0,
    epsilon_decay: float = 0.995,
    epsilon_min: float = 0.01,
    gamma: float = 0.95,
    learning_rate: float = 0.001,
    batch_size: int = 32,
    memory_size: int = 10000,
    model_dir: str = "/app/models/dqn"
):
    """
    Train DQN agent for trading.

    Args:
        symbol: Stock symbol to train on
        days: Number of historical days to fetch
        episodes: Number of training episodes
        update_target_every: Update target network every N episodes
        initial_epsilon: Initial exploration rate
        epsilon_decay: Epsilon decay rate
        epsilon_min: Minimum epsilon
        gamma: Discount factor
        learning_rate: Learning rate
        batch_size: Replay batch size
        memory_size: Replay buffer size
        model_dir: Directory to save models

    Returns:
        Training results dictionary
    """
    logger.info("=" * 80)
    logger.info(f"DQN AGENT TRAINING - {symbol}")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  Symbol: {symbol}")
    logger.info(f"  Historical days: {days}")
    logger.info(f"  Episodes: {episodes}")
    logger.info(f"  Update target every: {update_target_every}")
    logger.info(f"  Epsilon: {initial_epsilon} → {epsilon_min} (decay: {epsilon_decay})")
    logger.info(f"  Gamma (discount): {gamma}")
    logger.info(f"  Learning rate: {learning_rate}")
    logger.info(f"  Batch size: {batch_size}")
    logger.info(f"  Memory size: {memory_size}")
    logger.info(f"  Model directory: {model_dir}")
    logger.info("=" * 80)

    try:
        # Step 1: Fetch and prepare training data
        logger.info("\n[1/5] Fetching historical data...")
        training_data = get_training_data(symbol, days=days)
        logger.info(f"✓ Loaded {len(training_data)} samples with {len(training_data.columns)} features")

        # Step 2: Initialize trading environment
        logger.info("\n[2/5] Initializing trading environment...")
        env = TradingEnvironment(
            data=training_data,
            initial_balance=100000.0,
            transaction_cost=0.001
        )
        logger.info(f"✓ Environment initialized (state_dim={env.state_dim})")

        # Step 3: Initialize DQN agent
        logger.info("\n[3/5] Initializing DQN agent...")
        agent = DQNAgent(
            state_dim=env.state_dim,
            action_dim=3,
            learning_rate=learning_rate,
            gamma=gamma,
            epsilon=initial_epsilon,
            epsilon_decay=epsilon_decay,
            epsilon_min=epsilon_min,
            memory_size=memory_size,
            batch_size=batch_size
        )
        logger.info("✓ Agent initialized")

        # Step 4: Training loop
        logger.info(f"\n[4/5] Training DQN agent for {episodes} episodes...")
        logger.info("This may take 10-30 minutes depending on hardware...")
        logger.info("=" * 80)

        episode_rewards = []
        episode_trades = []
        episode_portfolio_values = []
        episode_win_rates = []

        best_reward = -np.inf
        best_episode = 0

        for episode in range(episodes):
            state = env.reset()
            total_reward = 0
            done = False
            steps = 0

            while not done:
                # Select action
                action = agent.act(state, training=True)

                # Execute action
                next_state, reward, done, info = env.step(action)

                # Store experience
                agent.remember(state, action, reward, next_state, done)

                # Train agent
                agent.replay()

                state = next_state
                total_reward += reward
                steps += 1

            # Episode complete
            final_portfolio_value = env.get_portfolio_value()
            win_rate = (env.winning_trades / env.total_trades * 100) if env.total_trades > 0 else 0

            episode_rewards.append(total_reward)
            episode_trades.append(env.total_trades)
            episode_portfolio_values.append(final_portfolio_value)
            episode_win_rates.append(win_rate)

            # Track best episode
            if total_reward > best_reward:
                best_reward = total_reward
                best_episode = episode + 1

            # Update target network
            if (episode + 1) % update_target_every == 0:
                agent.update_target_model()
                logger.info(f"  ↻ Target network updated")

            # Log progress
            if (episode + 1) % 10 == 0 or episode == 0:
                avg_reward = np.mean(episode_rewards[-10:])
                avg_trades = np.mean(episode_trades[-10:])
                avg_portfolio = np.mean(episode_portfolio_values[-10:])
                avg_win_rate = np.mean(episode_win_rates[-10:])

                logger.info(
                    f"Episode {episode + 1:3d}/{episodes} | "
                    f"Reward: {total_reward:8.2f} (avg: {avg_reward:8.2f}) | "
                    f"Trades: {env.total_trades:3d} (avg: {avg_trades:.1f}) | "
                    f"Win%: {win_rate:5.1f}% (avg: {avg_win_rate:.1f}%) | "
                    f"Portfolio: ₹{final_portfolio_value:,.0f} (avg: ₹{avg_portfolio:,.0f}) | "
                    f"ε: {agent.epsilon:.3f}"
                )

        logger.info("=" * 80)
        logger.info("✓ Training completed!")

        # Step 5: Save model and results
        logger.info("\n[5/5] Saving model and results...")
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, f"{symbol}_dqn.h5")
        agent.save(model_path)
        logger.info(f"✓ Model saved to {model_path}")

        # Calculate final metrics
        total_return = (episode_portfolio_values[-1] - 100000) / 100000 * 100
        avg_reward = float(np.mean(episode_rewards))
        max_reward = float(np.max(episode_rewards))
        min_reward = float(np.min(episode_rewards))
        avg_trades = float(np.mean(episode_trades))
        avg_win_rate = float(np.mean(episode_win_rates))
        final_portfolio = float(episode_portfolio_values[-1])

        training_results = {
            "symbol": symbol,
            "episodes": episodes,
            "final_epsilon": float(agent.epsilon),
            "avg_reward": avg_reward,
            "max_reward": max_reward,
            "min_reward": min_reward,
            "best_episode": best_episode,
            "avg_trades_per_episode": avg_trades,
            "avg_win_rate": avg_win_rate,
            "final_portfolio_value": final_portfolio,
            "total_return_pct": float(total_return),
            "model_path": model_path,
            "trained_at": datetime.now().isoformat()
        }

        # Save results
        results_file = os.path.join(model_dir, f"{symbol}_training_results.json")
        with open(results_file, 'w') as f:
            json.dump(training_results, f, indent=2)

        logger.info(f"✓ Results saved to {results_file}")

        # Display final metrics
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING RESULTS:")
        logger.info("=" * 80)
        logger.info(f"  Episodes: {episodes}")
        logger.info(f"  Best episode: {best_episode} (reward: {best_reward:.2f})")
        logger.info(f"  Average reward: {avg_reward:.2f}")
        logger.info(f"  Max reward: {max_reward:.2f}")
        logger.info(f"  Min reward: {min_reward:.2f}")
        logger.info(f"  Average trades/episode: {avg_trades:.1f}")
        logger.info(f"  Average win rate: {avg_win_rate:.1f}%")
        logger.info(f"  Final portfolio value: ₹{final_portfolio:,.0f}")
        logger.info(f"  Total return: {total_return:.2f}%")
        logger.info(f"  Final epsilon: {agent.epsilon:.4f}")
        logger.info("=" * 80)

        # Test agent
        logger.info("\n[Testing trained agent...]")
        state = env.reset()
        test_action = agent.act(state, training=False)
        action_name = TradingAction.to_string(test_action)
        logger.info(f"✓ Test action: {action_name}")

        logger.info("\n🎉 DQN training completed successfully!")

        return training_results

    except Exception as e:
        logger.error(f"\n❌ Training failed: {str(e)}", exc_info=True)
        raise


def main():
    """Command-line interface for DQN training"""
    parser = argparse.ArgumentParser(description='Train DQN trading agent')

    parser.add_argument(
        '--symbol',
        type=str,
        default='NIFTY',
        help='Stock symbol to train on (default: NIFTY)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=730,
        help='Number of historical days to fetch (default: 730)'
    )
    parser.add_argument(
        '--episodes',
        type=int,
        default=200,
        help='Number of training episodes (default: 200)'
    )
    parser.add_argument(
        '--update-target',
        type=int,
        default=10,
        help='Update target network every N episodes (default: 10)'
    )
    parser.add_argument(
        '--epsilon',
        type=float,
        default=1.0,
        help='Initial epsilon (default: 1.0)'
    )
    parser.add_argument(
        '--epsilon-decay',
        type=float,
        default=0.995,
        help='Epsilon decay rate (default: 0.995)'
    )
    parser.add_argument(
        '--epsilon-min',
        type=float,
        default=0.01,
        help='Minimum epsilon (default: 0.01)'
    )
    parser.add_argument(
        '--gamma',
        type=float,
        default=0.95,
        help='Discount factor (default: 0.95)'
    )
    parser.add_argument(
        '--learning-rate',
        type=float,
        default=0.001,
        help='Learning rate (default: 0.001)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Replay batch size (default: 32)'
    )
    parser.add_argument(
        '--memory-size',
        type=int,
        default=10000,
        help='Replay buffer size (default: 10000)'
    )
    parser.add_argument(
        '--model-dir',
        type=str,
        default='/app/models/dqn',
        help='Directory to save models (default: /app/models/dqn)'
    )

    args = parser.parse_args()

    # Train agent
    train_dqn_agent(
        symbol=args.symbol,
        days=args.days,
        episodes=args.episodes,
        update_target_every=args.update_target,
        initial_epsilon=args.epsilon,
        epsilon_decay=args.epsilon_decay,
        epsilon_min=args.epsilon_min,
        gamma=args.gamma,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        memory_size=args.memory_size,
        model_dir=args.model_dir
    )


if __name__ == '__main__':
    main()
