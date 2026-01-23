"""
LSTM Model Training Script
Trains LSTM price forecaster on historical NIFTY data
"""

import os
import sys
import logging
from datetime import datetime
import argparse
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.lstm_model import LSTMPriceForecaster
from training.data_fetcher import get_training_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train_lstm_model(
    symbol: str = "NIFTY",
    days: int = 730,
    lookback_days: int = 60,
    forecast_days: int = 30,
    epochs: int = 100,
    batch_size: int = 32,
    validation_split: float = 0.2,
    model_dir: str = "/app/models/lstm"
):
    """
    Train LSTM model for stock price forecasting.

    Args:
        symbol: Stock symbol to train on
        days: Number of historical days to fetch
        lookback_days: Number of days to use for prediction
        forecast_days: Number of days to forecast
        epochs: Maximum training epochs
        batch_size: Training batch size
        validation_split: Validation data split
        model_dir: Directory to save trained models

    Returns:
        Training results dictionary
    """
    logger.info("=" * 80)
    logger.info(f"LSTM TRAINING - {symbol}")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  Symbol: {symbol}")
    logger.info(f"  Historical days: {days}")
    logger.info(f"  Lookback window: {lookback_days} days")
    logger.info(f"  Forecast horizon: {forecast_days} days")
    logger.info(f"  Max epochs: {epochs}")
    logger.info(f"  Batch size: {batch_size}")
    logger.info(f"  Validation split: {validation_split}")
    logger.info(f"  Model directory: {model_dir}")
    logger.info("=" * 80)

    try:
        # Step 1: Fetch and prepare training data
        logger.info("\n[1/4] Fetching historical data...")
        training_data = get_training_data(symbol, days=days)
        logger.info(f"✓ Loaded {len(training_data)} samples with {len(training_data.columns)} features")

        # Step 2: Initialize LSTM model
        logger.info("\n[2/4] Initializing LSTM model...")
        forecaster = LSTMPriceForecaster(
            symbol=symbol,
            lookback_days=lookback_days,
            forecast_days=forecast_days,
            model_dir=model_dir
        )
        logger.info("✓ Model initialized")

        # Step 3: Train model
        logger.info(f"\n[3/4] Training LSTM model...")
        logger.info(f"This may take 5-15 minutes depending on hardware...")

        training_results = forecaster.train(
            historical_data=training_data,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            early_stop_patience=10
        )

        logger.info("✓ Training completed!")

        # Step 4: Display results
        logger.info("\n[4/4] Training Results:")
        logger.info("=" * 80)
        logger.info(f"  Epochs trained: {training_results['epochs_trained']}")
        logger.info(f"  Best epoch: {training_results['best_epoch']}")
        logger.info(f"  Final training loss: {training_results['final_loss']:.6f}")
        logger.info(f"  Final validation loss: {training_results['final_val_loss']:.6f}")
        logger.info(f"  Final MAE: {training_results['final_mae']:.4f}")
        logger.info(f"  Final validation MAE: {training_results['final_val_mae']:.4f}")
        logger.info(f"  Training samples: {training_results['training_samples']}")
        logger.info("=" * 80)

        # Step 5: Test prediction
        logger.info("\n[5/5] Testing prediction...")
        recent_data = training_data.tail(lookback_days + 10).copy()
        test_forecast = forecaster.predict(recent_data)

        logger.info(f"✓ Prediction successful!")
        logger.info(f"  Current price: ₹{test_forecast['current_price']}")
        logger.info(f"  Predicted price (30 days): ₹{test_forecast['predicted_price_30d']}")
        logger.info(f"  Expected change: ₹{test_forecast['price_change']} ({test_forecast['price_change_pct']:.2f}%)")

        # Save results to JSON
        results_file = os.path.join(model_dir, f"{symbol}_training_results.json")
        with open(results_file, 'w') as f:
            json.dump({
                **training_results,
                "trained_at": datetime.now().isoformat(),
                "test_forecast": test_forecast
            }, f, indent=2)

        logger.info(f"\n✓ Results saved to {results_file}")
        logger.info(f"✓ Model saved to {model_dir}/{symbol}.h5")
        logger.info("\n🎉 LSTM training completed successfully!")

        return training_results

    except Exception as e:
        logger.error(f"\n❌ Training failed: {str(e)}", exc_info=True)
        raise


def main():
    """Command-line interface for LSTM training"""
    parser = argparse.ArgumentParser(description='Train LSTM price forecasting model')

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
        '--lookback',
        type=int,
        default=60,
        help='Lookback window in days (default: 60)'
    )
    parser.add_argument(
        '--forecast',
        type=int,
        default=30,
        help='Forecast horizon in days (default: 30)'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='Maximum training epochs (default: 100)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Training batch size (default: 32)'
    )
    parser.add_argument(
        '--validation-split',
        type=float,
        default=0.2,
        help='Validation split ratio (default: 0.2)'
    )
    parser.add_argument(
        '--model-dir',
        type=str,
        default='/app/models/lstm',
        help='Directory to save models (default: /app/models/lstm)'
    )

    args = parser.parse_args()

    # Train model
    train_lstm_model(
        symbol=args.symbol,
        days=args.days,
        lookback_days=args.lookback,
        forecast_days=args.forecast,
        epochs=args.epochs,
        batch_size=args.batch_size,
        validation_split=args.validation_split,
        model_dir=args.model_dir
    )


if __name__ == '__main__':
    main()
