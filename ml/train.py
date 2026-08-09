"""
XGBoost Training Script for InfinityAI.Pro
Trains a binary classifier to predict next candle direction
Uploads versioned model to Google Cloud Storage
"""
import os
import pandas as pd
import xgboost as xgb
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from google.cloud import storage

from features import build_features

logger = logging.getLogger(__name__)

def upload_to_gcs(local_path: str, gcs_uri: str):
    """Upload file to Google Cloud Storage"""
    try:
        client = storage.Client()
        bucket_name, blob_path = gcs_uri.replace("gs://", "").split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.upload_from_filename(local_path)
        logger.info(f"✅ Uploaded {local_path} to {gcs_uri}")
    except Exception as e:
        logger.error(f"❌ GCS upload failed: {e}")
        raise


def train_model(dataset_path: str, model_uri: str):
    """
    Train XGBoost model and upload to GCS
    
    Args:
        dataset_path: Path or GCS URI to CSV dataset  
        model_uri: GCS URI for saving model (e.g., gs://bucket/model.json)
    """
    logger.info(f"🚀 Starting training...")
    logger.info(f"Dataset: {dataset_path}")
    logger.info(f"Model output: {model_uri}")
    
    # Load data
    logger.info("📊 Loading dataset...")
    if dataset_path.startswith("gs://"):
        # Download from GCS
        client = storage.Client()
        bucket_name, blob_path = dataset_path.replace("gs://", "").split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.download_to_filename("temp_dataset.csv")
        raw = pd.read_csv("temp_dataset.csv")
    else:
        raw = pd.read_csv(dataset_path)
    
    logger.info(f"Loaded {len(raw)} rows")
    
    # Feature engineering
    logger.info("🔧 Building features...")
    data = build_features(raw)
    logger.info(f"Features after processing: {len(data)} rows, {len(data.columns)} columns")
    
    # Split data
    feature_cols = [col for col in data.columns if col != 'target']
    X = data[feature_cols]
    y = data['target']
    
    # Time series: no shuffle
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    
    logger.info(f"Train set: {len(X_train)} rows, Test set: {len(X_test)} rows")
    
    # Train XGBoost
    logger.info("🌲 Training XGBoost model...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=10
    )
    
    # Evaluate
    logger.info("📈 Evaluating model...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "n_samples": len(data),
        "trained_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Metrics: {json.dumps(metrics, indent=2)}")
    
    # Save locally
    local_model_path = "model.json"
    model.save_model(local_model_path)
    logger.info(f"Saved local model to {local_model_path}")
    
    # Save metrics locally
    local_metrics_path = "metrics.json"
    with open(local_metrics_path, 'w') as f:
        json.dumps(metrics, f, indent=2)
    
    # Upload to GCS if requested
    if model_uri.startswith("gs://"):
        upload_to_gcs(local_model_path, model_uri)
        metrics_uri = model_uri.rsplit('/', 1)[0] + "/metrics.json"
        upload_to_gcs(local_metrics_path, metrics_uri)
        logger.info("✅ Training completed and uploaded to GCS!")
    else:
        logger.info(f"Model saved locally: {local_model_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train XGBoost model for InfinityAI.Pro")
    parser.add_argument("--dataset", required=True, help="Path or GCS URI to dataset CSV")
    parser.add_argument("--output", required=True, help="Path or GCS URI for model output")
    args = parser.parse_args()
    
    train_model(args.dataset, args.output)
