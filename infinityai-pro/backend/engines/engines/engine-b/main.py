"""
InfinityAI.Pro - Engine B: AI/ML GPU Training & Inference
Handles machine learning model training, inference, and GPU acceleration
"""

import asyncio
import logging
import json
import os
import pickle
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
from kafka import KafkaConsumer, KafkaProducer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="InfinityAI Engine B - AI/ML GPU", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MODEL_STORAGE_PATH = os.getenv("MODEL_STORAGE_PATH", "/app/models")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Initialize connections
redis_client = redis.from_url(REDIS_URL)
kafka_producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Ensure model directory exists
os.makedirs(MODEL_STORAGE_PATH, exist_ok=True)

class TrainingRequest(BaseModel):
    model_name: str
    training_data: List[Dict[str, Any]]
    model_type: str = "neural_network"  # neural_network, lstm, transformer
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001

class InferenceRequest(BaseModel):
    model_name: str
    input_data: List[Dict[str, Any]]

class ModelStatus(BaseModel):
    model_name: str
    status: str
    accuracy: Optional[float] = None
    training_progress: Optional[float] = None
    created_at: Optional[datetime] = None

class TradingNeuralNetwork(nn.Module):
    """Neural network for trading signal prediction"""
    
    def __init__(self, input_size: int, hidden_sizes: List[int] = [128, 64, 32], output_size: int = 3):
        super(TradingNeuralNetwork, self).__init__()
        
        layers = []
        prev_size = input_size
        
        # Hidden layers
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_size),
                nn.Dropout(0.3)
            ])
            prev_size = hidden_size
        
        # Output layer
        layers.append(nn.Linear(prev_size, output_size))
        layers.append(nn.Softmax(dim=1))
        
        self.network = nn.Sequential(*layers)
        
    def forward(self, x):
        return self.network(x)

class TradingLSTM(nn.Module):
    """LSTM network for time series trading prediction"""
    
    def __init__(self, input_size: int, hidden_size: int = 128, num_layers: int = 2, output_size: int = 3):
        super(TradingLSTM, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, output_size)
        self.softmax = nn.Softmax(dim=1)
        
    def forward(self, x):
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # LSTM forward pass
        out, _ = self.lstm(x, (h0, c0))
        
        # Use the last output
        out = self.fc(out[:, -1, :])
        out = self.softmax(out)
        
        return out

class AIModelService:
    """Handles AI model training, inference, and management"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.training_tasks = {}
        self.load_existing_models()
        
    def load_existing_models(self):
        """Load existing trained models from storage"""
        try:
            for filename in os.listdir(MODEL_STORAGE_PATH):
                if filename.endswith('.pth'):
                    model_name = filename.replace('.pth', '')
                    logger.info(f"Found existing model: {model_name}")
        except Exception as e:
            logger.error(f"Error loading existing models: {e}")
    
    def prepare_data(self, training_data: List[Dict[str, Any]]) -> tuple:
        """Prepare and preprocess training data"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(training_data)
            
            # Feature columns (everything except target)
            feature_columns = [col for col in df.columns if col not in ['target', 'signal', 'action']]
            
            # Determine target column
            target_col = 'target' if 'target' in df.columns else 'signal' if 'signal' in df.columns else 'action'
            
            if target_col not in df.columns:
                raise ValueError("No target column found in training data")
            
            X = df[feature_columns].fillna(0)
            y = df[target_col]
            
            # Encode labels if they're strings
            if y.dtype == 'object':
                label_encoder = LabelEncoder()
                y = label_encoder.fit_transform(y)
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Convert to tensors
            X_tensor = torch.FloatTensor(X_scaled)
            y_tensor = torch.LongTensor(y)
            
            return X_tensor, y_tensor, scaler, feature_columns
            
        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            raise HTTPException(status_code=400, detail=f"Data preparation failed: {e}")
    
    async def train_model(self, request: TrainingRequest) -> Dict:
        """Train a new AI model"""
        try:
            logger.info(f"Starting training for model: {request.model_name}")
            
            # Prepare data
            X_tensor, y_tensor, scaler, feature_columns = self.prepare_data(request.training_data)
            
            # Move to GPU if available
            X_tensor = X_tensor.to(DEVICE)
            y_tensor = y_tensor.to(DEVICE)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_tensor, y_tensor, test_size=0.2, random_state=42
            )
            
            # Create model based on type
            input_size = X_tensor.shape[1]
            output_size = len(torch.unique(y_tensor))
            
            if request.model_type == "lstm":
                # Reshape for LSTM (batch_size, sequence_length, input_size)
                X_train = X_train.unsqueeze(1)
                X_test = X_test.unsqueeze(1)
                model = TradingLSTM(input_size, output_size=output_size).to(DEVICE)
            else:
                model = TradingNeuralNetwork(input_size, output_size=output_size).to(DEVICE)
            
            # Loss and optimizer
            criterion = nn.CrossEntropyLoss()
            optimizer = optim.Adam(model.parameters(), lr=request.learning_rate)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=10)
            
            # Training loop
            model.train()
            train_dataset = TensorDataset(X_train, y_train)
            train_loader = DataLoader(train_dataset, batch_size=request.batch_size, shuffle=True)
            
            training_losses = []
            
            for epoch in range(request.epochs):
                epoch_loss = 0.0
                for batch_X, batch_y in train_loader:
                    optimizer.zero_grad()
                    outputs = model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
                    epoch_loss += loss.item()
                
                avg_loss = epoch_loss / len(train_loader)
                training_losses.append(avg_loss)
                scheduler.step(avg_loss)
                
                # Update training progress
                progress = ((epoch + 1) / request.epochs) * 100
                self.training_tasks[request.model_name] = {
                    "status": "training",
                    "progress": progress,
                    "current_loss": avg_loss,
                    "epoch": epoch + 1
                }
                
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch + 1}/{request.epochs}, Loss: {avg_loss:.4f}")
            
            # Evaluate model
            model.eval()
            with torch.no_grad():
                test_outputs = model(X_test)
                _, predicted = torch.max(test_outputs.data, 1)
                accuracy = (predicted == y_test).sum().item() / y_test.size(0)
            
            # Save model and scaler
            model_path = os.path.join(MODEL_STORAGE_PATH, f"{request.model_name}.pth")
            scaler_path = os.path.join(MODEL_STORAGE_PATH, f"{request.model_name}_scaler.pkl")
            
            torch.save({
                'model_state_dict': model.state_dict(),
                'model_type': request.model_type,
                'input_size': input_size,
                'output_size': output_size,
                'feature_columns': feature_columns,
                'accuracy': accuracy,
                'training_losses': training_losses
            }, model_path)
            
            joblib.dump(scaler, scaler_path)
            
            # Store in memory
            self.models[request.model_name] = model
            self.scalers[request.model_name] = scaler
            
            # Update training status
            self.training_tasks[request.model_name] = {
                "status": "completed",
                "progress": 100.0,
                "accuracy": accuracy,
                "final_loss": training_losses[-1] if training_losses else 0
            }
            
            # Send training completion message to Kafka
            kafka_producer.send("model_training", {
                "model_name": request.model_name,
                "status": "completed",
                "accuracy": accuracy,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            logger.info(f"Training completed for {request.model_name} with accuracy: {accuracy:.4f}")
            
            return {
                "status": "success",
                "model_name": request.model_name,
                "accuracy": accuracy,
                "training_losses": training_losses[-10:],  # Last 10 losses
                "epochs_trained": request.epochs,
                "device_used": str(DEVICE)
            }
            
        except Exception as e:
            logger.error(f"Training failed for {request.model_name}: {e}")
            self.training_tasks[request.model_name] = {
                "status": "failed",
                "error": str(e)
            }
            raise HTTPException(status_code=500, detail=f"Training failed: {e}")
    
    async def run_inference(self, request: InferenceRequest) -> Dict:
        """Run inference on trained model"""
        try:
            model_name = request.model_name
            
            # Load model if not in memory
            if model_name not in self.models:
                await self.load_model(model_name)
            
            if model_name not in self.models:
                raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
            
            model = self.models[model_name]
            scaler = self.scalers[model_name]
            
            # Prepare input data
            df = pd.DataFrame(request.input_data)
            X_scaled = scaler.transform(df.fillna(0))
            X_tensor = torch.FloatTensor(X_scaled).to(DEVICE)
            
            # Handle LSTM input shape
            model_path = os.path.join(MODEL_STORAGE_PATH, f"{model_name}.pth")
            checkpoint = torch.load(model_path, map_location=DEVICE)
            
            if checkpoint.get('model_type') == 'lstm':
                X_tensor = X_tensor.unsqueeze(1)
            
            # Run inference
            model.eval()
            with torch.no_grad():
                outputs = model(X_tensor)
                probabilities = outputs.cpu().numpy()
                predictions = torch.argmax(outputs, dim=1).cpu().numpy()
            
            # Convert predictions to trading signals
            signal_map = {0: "SELL", 1: "HOLD", 2: "BUY"}
            signals = [signal_map.get(pred, "HOLD") for pred in predictions]
            
            results = []
            for i, (signal, probs) in enumerate(zip(signals, probabilities)):
                results.append({
                    "index": i,
                    "signal": signal,
                    "confidence": float(np.max(probs)),
                    "probabilities": {
                        "sell": float(probs[0]),
                        "hold": float(probs[1]),
                        "buy": float(probs[2])
                    }
                })
            
            # Send inference results to Kafka
            kafka_producer.send("inference_results", {
                "model_name": model_name,
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            logger.info(f"Inference completed for {model_name}: {len(results)} predictions")
            
            return {
                "status": "success",
                "model_name": model_name,
                "predictions": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Inference failed for {request.model_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Inference failed: {e}")
    
    async def load_model(self, model_name: str):
        """Load model from storage"""
        try:
            model_path = os.path.join(MODEL_STORAGE_PATH, f"{model_name}.pth")
            scaler_path = os.path.join(MODEL_STORAGE_PATH, f"{model_name}_scaler.pkl")
            
            if not os.path.exists(model_path):
                return False
            
            # Load checkpoint
            checkpoint = torch.load(model_path, map_location=DEVICE)
            
            # Recreate model
            input_size = checkpoint['input_size']
            output_size = checkpoint['output_size']
            model_type = checkpoint.get('model_type', 'neural_network')
            
            if model_type == 'lstm':
                model = TradingLSTM(input_size, output_size=output_size).to(DEVICE)
            else:
                model = TradingNeuralNetwork(input_size, output_size=output_size).to(DEVICE)
            
            model.load_state_dict(checkpoint['model_state_dict'])
            
            # Load scaler
            scaler = joblib.load(scaler_path)
            
            self.models[model_name] = model
            self.scalers[model_name] = scaler
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return False

# Initialize AI service
ai_service = AIModelService()

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    gpu_info = {
        "available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "current_device": str(DEVICE)
    }
    
    if torch.cuda.is_available():
        gpu_info["gpu_name"] = torch.cuda.get_device_name(0)
        gpu_info["gpu_memory"] = torch.cuda.get_device_properties(0).total_memory
    
    return {
        "status": "healthy",
        "service": "Engine B - AI/ML GPU",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "gpu_info": gpu_info
    }

@app.post("/models/train")
async def train_model(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Train a new AI model"""
    # Run training in background
    background_tasks.add_task(ai_service.train_model, request)
    
    return {
        "status": "training_started",
        "model_name": request.model_name,
        "message": "Training started in background",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/models/inference")
async def run_inference(request: InferenceRequest):
    """Run inference on a trained model"""
    return await ai_service.run_inference(request)

@app.get("/models/{model_name}/status")
async def get_model_status(model_name: str):
    """Get training/inference status of a model"""
    try:
        # Check if model exists in training tasks
        if model_name in ai_service.training_tasks:
            training_info = ai_service.training_tasks[model_name]
            return {
                "model_name": model_name,
                "status": training_info.get("status", "unknown"),
                "progress": training_info.get("progress", 0),
                "accuracy": training_info.get("accuracy"),
                "current_loss": training_info.get("current_loss"),
                "epoch": training_info.get("epoch"),
                "error": training_info.get("error")
            }
        
        # Check if model exists in storage
        model_path = os.path.join(MODEL_STORAGE_PATH, f"{model_name}.pth")
        if os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location='cpu')
            return {
                "model_name": model_name,
                "status": "trained",
                "accuracy": checkpoint.get("accuracy", 0),
                "model_type": checkpoint.get("model_type", "unknown"),
                "available": True
            }
        
        return {
            "model_name": model_name,
            "status": "not_found",
            "available": False
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models():
    """List all available models"""
    try:
        models = []
        
        # Get models from storage
        for filename in os.listdir(MODEL_STORAGE_PATH):
            if filename.endswith('.pth'):
                model_name = filename.replace('.pth', '')
                try:
                    checkpoint = torch.load(os.path.join(MODEL_STORAGE_PATH, filename), map_location='cpu')
                    models.append({
                        "name": model_name,
                        "type": checkpoint.get("model_type", "unknown"),
                        "accuracy": checkpoint.get("accuracy", 0),
                        "status": "available",
                        "loaded": model_name in ai_service.models
                    })
                except:
                    models.append({
                        "name": model_name,
                        "status": "corrupted",
                        "loaded": False
                    })
        
        return {
            "models": models,
            "total_count": len(models),
            "loaded_count": len(ai_service.models)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gpu/status")
async def get_gpu_status():
    """Get detailed GPU status and utilization"""
    try:
        if not torch.cuda.is_available():
            return {"gpu_available": False, "message": "CUDA not available"}
        
        gpu_status = {
            "gpu_available": True,
            "device_count": torch.cuda.device_count(),
            "current_device": torch.cuda.current_device(),
            "devices": []
        }
        
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            memory_allocated = torch.cuda.memory_allocated(i) / 1024**3  # GB
            memory_cached = torch.cuda.memory_reserved(i) / 1024**3  # GB
            memory_total = props.total_memory / 1024**3  # GB
            
            gpu_status["devices"].append({
                "id": i,
                "name": props.name,
                "total_memory_gb": round(memory_total, 2),
                "allocated_memory_gb": round(memory_allocated, 2),
                "cached_memory_gb": round(memory_cached, 2),
                "utilization_percent": round((memory_allocated / memory_total) * 100, 2),
                "compute_capability": f"{props.major}.{props.minor}"
            })
        
        return gpu_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
