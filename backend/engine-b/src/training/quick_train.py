"""
Quick local training script for testing
Trains models with smaller datasets for fast iteration
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from training.train_all import train_all_models

if __name__ == '__main__':
    print("\n🚀 Starting quick training (small dataset for testing)...\n")

    train_all_models(
        symbol="NIFTY",
        days=365,  # 1 year instead of 2
        lstm_epochs=20,  # Reduced from 100
        dqn_episodes=50,  # Reduced from 200
        model_dir="./models_local",  # Local directory
        upload_gcs=False  # Don't upload during testing
    )

    print("\n✅ Quick training complete! Check ./models_local/ for results.\n")
