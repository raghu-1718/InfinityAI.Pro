"""
Master Training Script
Runs both LSTM and DQN training sequentially
"""

import os
import sys
import logging
import argparse
from datetime import datetime
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from training.train_lstm import train_lstm_model
from training.train_dqn import train_dqn_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def upload_to_gcs(local_dir: str, bucket_name: str, gcs_prefix: str):
    """Upload trained models to Google Cloud Storage"""
    try:
        from google.cloud import storage

        logger.info(f"\nUploading models to GCS...")
        logger.info(f"  Bucket: {bucket_name}")
        logger.info(f"  Prefix: {gcs_prefix}")

        client = storage.Client()
        bucket = client.bucket(bucket_name)

        uploaded_files = []

        for root, dirs, files in os.walk(local_dir):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, local_dir)
                gcs_path = f"{gcs_prefix}/{relative_path}"

                blob = bucket.blob(gcs_path)
                blob.upload_from_filename(local_path)

                uploaded_files.append(gcs_path)
                logger.info(f"  ✓ Uploaded: {gcs_path}")

        logger.info(f"✓ Uploaded {len(uploaded_files)} files to GCS")

        return uploaded_files

    except Exception as e:
        logger.warning(f"GCS upload failed: {e}")
        logger.info("Models saved locally only")
        return []


def train_all_models(
    symbol: str = "NIFTY",
    days: int = 730,
    lstm_epochs: int = 100,
    dqn_episodes: int = 200,
    model_dir: str = "/app/models",
    upload_gcs: bool = False,
    gcs_bucket: str = "galvanic-pulsar-482815-h0-models",
    gcs_prefix: str = "trained_models"
):
    """
    Train both LSTM and DQN models.

    Args:
        symbol: Stock symbol
        days: Historical days
        lstm_epochs: LSTM training epochs
        dqn_episodes: DQN training episodes
        model_dir: Local model directory
        upload_gcs: Whether to upload to GCS
        gcs_bucket: GCS bucket name
        gcs_prefix: GCS path prefix
    """
    start_time = datetime.now()

    logger.info("=" * 100)
    logger.info(" INFINITYAI.PRO - MODEL TRAINING PIPELINE ".center(100, "="))
    logger.info("=" * 100)
    logger.info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Symbol: {symbol}")
    logger.info(f"Historical data: {days} days")
    logger.info(f"LSTM epochs: {lstm_epochs}")
    logger.info(f"DQN episodes: {dqn_episodes}")
    logger.info("=" * 100)

    results = {}

    try:
        # Train LSTM
        logger.info("\n" + "█" * 100)
        logger.info(" STEP 1: LSTM PRICE FORECASTER ".center(100, "█"))
        logger.info("█" * 100)

        lstm_results = train_lstm_model(
            symbol=symbol,
            days=days,
            lookback_days=60,
            forecast_days=30,
            epochs=lstm_epochs,
            batch_size=32,
            validation_split=0.2,
            model_dir=os.path.join(model_dir, "lstm")
        )

        results["lstm"] = lstm_results
        logger.info("\n✅ LSTM training completed successfully!")

    except Exception as e:
        logger.error(f"\n❌ LSTM training failed: {e}")
        results["lstm"] = {"error": str(e)}

    try:
        # Train DQN
        logger.info("\n" + "█" * 100)
        logger.info(" STEP 2: DQN TRADING AGENT ".center(100, "█"))
        logger.info("█" * 100)

        dqn_results = train_dqn_agent(
            symbol=symbol,
            days=days,
            episodes=dqn_episodes,
            update_target_every=10,
            initial_epsilon=1.0,
            epsilon_decay=0.995,
            epsilon_min=0.01,
            gamma=0.95,
            learning_rate=0.001,
            batch_size=32,
            memory_size=10000,
            model_dir=os.path.join(model_dir, "dqn")
        )

        results["dqn"] = dqn_results
        logger.info("\n✅ DQN training completed successfully!")

    except Exception as e:
        logger.error(f"\n❌ DQN training failed: {e}")
        results["dqn"] = {"error": str(e)}

    # Upload to GCS
    if upload_gcs:
        try:
            logger.info("\n" + "=" * 100)
            logger.info(" STEP 3: UPLOAD TO GOOGLE CLOUD STORAGE ".center(100, "="))
            logger.info("=" * 100)

            uploaded_files = upload_to_gcs(model_dir, gcs_bucket, gcs_prefix)
            results["gcs_uploaded_files"] = uploaded_files

        except Exception as e:
            logger.error(f"❌ GCS upload failed: {e}")
            results["gcs_upload_error"] = str(e)

    # Save combined results
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    results["metadata"] = {
        "symbol": symbol,
        "historical_days": days,
        "started_at": start_time.isoformat(),
        "completed_at": end_time.isoformat(),
        "duration_seconds": duration,
        "duration_minutes": round(duration / 60, 2)
    }

    results_file = os.path.join(model_dir, f"{symbol}_complete_training_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Final summary
    logger.info("\n" + "=" * 100)
    logger.info(" TRAINING COMPLETE ".center(100, "="))
    logger.info("=" * 100)
    logger.info(f"Total duration: {duration / 60:.1f} minutes")
    logger.info(f"Results saved to: {results_file}")

    if "error" not in results.get("lstm", {}):
        logger.info("\n✅ LSTM Model:")
        logger.info(f"   - Epochs: {results['lstm']['epochs_trained']}")
        logger.info(f"   - Final loss: {results['lstm']['final_loss']:.6f}")
        logger.info(f"   - MAE: {results['lstm']['final_mae']:.4f}")

    if "error" not in results.get("dqn", {}):
        logger.info("\n✅ DQN Agent:")
        logger.info(f"   - Episodes: {results['dqn']['episodes']}")
        logger.info(f"   - Avg reward: {results['dqn']['avg_reward']:.2f}")
        logger.info(f"   - Win rate: {results['dqn']['avg_win_rate']:.1f}%")
        logger.info(f"   - Portfolio return: {results['dqn']['total_return_pct']:.2f}%")

    if upload_gcs and "gcs_uploaded_files" in results:
        logger.info(f"\n✅ GCS Upload: {len(results['gcs_uploaded_files'])} files uploaded")

    logger.info("=" * 100)
    logger.info("\n🎉 All training complete! Models are ready for deployment.")

    return results


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(description='Train all ML models')

    parser.add_argument('--symbol', type=str, default='NIFTY', help='Stock symbol')
    parser.add_argument('--days', type=int, default=730, help='Historical days')
    parser.add_argument('--lstm-epochs', type=int, default=100, help='LSTM epochs')
    parser.add_argument('--dqn-episodes', type=int, default=200, help='DQN episodes')
    parser.add_argument('--model-dir', type=str, default='/app/models', help='Model directory')
    parser.add_argument('--upload-gcs', action='store_true', help='Upload to GCS')
    parser.add_argument('--gcs-bucket', type=str, default='galvanic-pulsar-482815-h0-models', help='GCS bucket')
    parser.add_argument('--gcs-prefix', type=str, default='trained_models', help='GCS prefix')

    args = parser.parse_args()

    train_all_models(
        symbol=args.symbol,
        days=args.days,
        lstm_epochs=args.lstm_epochs,
        dqn_episodes=args.dqn_episodes,
        model_dir=args.model_dir,
        upload_gcs=args.upload_gcs,
        gcs_bucket=args.gcs_bucket,
        gcs_prefix=args.gcs_prefix
    )


if __name__ == '__main__':
    main()
