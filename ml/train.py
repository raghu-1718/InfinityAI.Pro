"""
XGBoost Training Script for InfinityAI.Pro
Trains a binary classifier to predict next candle direction
Uploads versioned model to Google Cloud Storage
"""
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
    
import os
# OpenTelemetry setup
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Initialize OpenTelemetry Tracing
resource = Resource(attributes={SERVICE_NAME: "ml-train"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)
otlp_exporter = OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317"), insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

def upload_to_gcs(local_path: str, gcs_uri: str):
    with tracer.start_as_current_span("upload_to_gcs"):
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
    with tracer.start_as_current_span("train_model"):
        """
        Train XGBoost model and upload to GCS
        """
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
    
    logger.info(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples")
    
    # Train XGBoost
    logger.info("🤖 Training XGBoost...")
    model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='binary:logistic',
        eval_metric='logloss',
        n_jobs=-1,
        random_state=42,
        use_label_encoder=False
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50
    )
    
    # Evaluate
    logger.info("📊 Evaluating model...")
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
    }
    
    logger.info(f"✅ Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"✅ Precision: {metrics['precision']:.4f}")
    logger.info(f"✅ Recall: {metrics['recall']:.4f}")
    logger.info(f"✅ F1 Score: {metrics['f1_score']:.4f}")
    
    # Save model locally
    model_filename = "model.json"
    model.save_model(model_filename)
    logger.info(f"💾 Model saved to {model_filename}")
    
    # Create metadata
    metadata = {
        "trained_at": datetime.utcnow().isoformat(),
        "dataset_rows": len(raw),
        "features_used": len(data),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_columns": feature_cols,
        "metrics": metrics,
        "model_params": model.get_params()
    }
    
    metadata_filename = "metadata.json"
    with open(metadata_filename, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"📄 Metadata saved to {metadata_filename}")
    
    # Upload to GCS
    logger.info("☁️ Uploading to GCS...")
    upload_to_gcs(model_filename, model_uri)
    
    # Upload metadata
    metadata_uri = model_uri.replace(".json", "_metadata.json")
    upload_to_gcs(metadata_filename, metadata_uri)
    
    # Also upload as "latest" for easy loading
    latest_uri = model_uri.rsplit("/", 1)[0] + "/latest.json"
    upload_to_gcs(model_filename, latest_uri)
    logger.info(f"✅ Also uploaded as {latest_uri}")
    
    logger.info("🎉 Training complete!")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train XGBoost model for InfinityAI.Pro")
    parser.add_argument("--dataset", required=True, help="Path or GCS URI to training dataset CSV")
    parser.add_argument("--model_uri", required=True, help="GCS URI for output model (e.g., gs://bucket/model.json)")
    
    args = parser.parse_args()
    
    try:
        metadata = train_model(args.dataset, args.model_uri)
        logger.info(f"Final metrics: {json.dumps(metadata['metrics'], indent=2)}")
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        raise
