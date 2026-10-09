"""Training module for ML models"""

from .data_fetcher import MarketDataFetcher, get_training_data

try:
    from .train_lstm import train_lstm_model
except Exception:
    train_lstm_model = None

try:
    from .train_dqn import train_dqn_agent
except Exception:
    train_dqn_agent = None

try:
    from .train_all import train_all_models
except Exception:
    train_all_models = None

__all__ = [
    'MarketDataFetcher',
    'get_training_data',
    'train_lstm_model',
    'train_dqn_agent',
    'train_all_models'
]
