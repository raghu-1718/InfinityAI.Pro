"""
Create a baseline XGBoost model for Phase-6A verification
This is a minimal model to test hot-reload functionality
"""
import os
import json
import pandas as pd
import numpy as np
import xgboost as xgb
from datetime import datetime, timezone
from google.cloud import storage

# Sample training data (minimal for testing)
np.random.seed(42)
n_samples = 1000

# Create synthetic OHLCV-like features
data = {
    'rsi_14': np.random.uniform(30, 70, n_samples),
    'ema_10': np.random.uniform(100, 200, n_samples),
    'ema_20': np.random.uniform(100, 200, n_samples),
    'ema_50': np.random.uniform(100, 200, n_samples),
    'macd': np.random.uniform(-2, 2, n_samples),
    'atr': np.random.uniform(1, 5, n_samples),
    'return_1': np.random.uniform(-0.05, 0.05, n_samples),
    'return_5': np.random.uniform(-0.1, 0.1, n_samples),
    'volume_ratio': np.random.uniform(0.5, 2.0, n_samples),
    'volatility_20': np.random.uniform(0.01, 0.05, n_samples)
}

df = pd.DataFrame(data)

# Binary target: 1 for up, 0 for down
y = (df['return_1'] > 0).astype(int)
X = df.drop(columns=[])

# Split
split_idx = int(len(X) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

# Train baseline XGBoost
print("Training baseline XGBoost model...")
model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='binary:logistic',
    random_state=42,
    use_label_encoder=False,
    eval_metric='logloss'
)

model.fit(X_train, y_train)

# Evaluate
from sklearn.metrics import accuracy_score, precision_score, recall_score
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)

print(f"✅ Model trained - Accuracy: {accuracy:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}")

# Save model
model_filename = "model.json"
model.save_model(model_filename)
print(f"💾 Model saved to {model_filename}")

# Create metadata
metadata = {
    "model_name": "xgboost_baseline",
    "model_version": "v1.0.0",
    "trained_at": datetime.now(timezone.utc).isoformat(),
    "features": list(X.columns),
    "data_window": "2024-01-01 to 2024-12-23 (synthetic)",
    "metrics": {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall)
    },
    "params": model.get_params(),
    "n_samples_train": len(X_train),
    "n_samples_test": len(X_test)
}

metadata_filename = "metadata.json"
with open(metadata_filename, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"📄 Metadata saved to {metadata_filename}")

# Upload to GCS
print("\n☁️ Uploading to Google Cloud Storage...")
bucket_name = "gen-lang-client-0779271931-ml-models"
model_path = "xgb/xgboost_baseline/v1.0.0"

try:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # Upload model
    model_blob = bucket.blob(f"{model_path}/model.json")
    model_blob.upload_from_filename(model_filename)
    print(f"✅ Uploaded: gs://{bucket_name}/{model_path}/model.json")
    
    # Upload metadata
    metadata_blob = bucket.blob(f"{model_path}/metadata.json")
    metadata_blob.upload_from_filename(metadata_filename)
    print(f"✅ Uploaded: gs://{bucket_name}/{model_path}/metadata.json")
    
    # Also upload as "latest" for easy discovery
    latest_model_blob = bucket.blob("xgb/latest.json")
    latest_model_blob.upload_from_filename(model_filename)
    print(f"✅ Uploaded: gs://{bucket_name}/xgb/latest.json")
    
    print("\n🎉 Model upload complete!")
    print(f"\nModel location: gs://{bucket_name}/{model_path}/")
    print("\nHot-reload will detect this model within 5 minutes.")
    
except Exception as e:
    print(f"❌ Upload failed: {e}")
    print("Make sure you have GCS credentials configured.")
