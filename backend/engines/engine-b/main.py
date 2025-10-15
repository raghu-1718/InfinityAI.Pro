from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import time
import random
import numpy as np
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import asyncio
from datetime import datetime, timedelta

app = FastAPI(
    title="InfinityAI Engine B - AI Predictions",
    description="Machine learning predictions, sentiment analysis, and trading recommendations",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prediction models
PREDICTION_MODELS = {
    "lstm": "Long Short-Term Memory Neural Network",
    "transformer": "Transformer-based Time Series Model",
    "random_forest": "Random Forest Regression",
    "svm": "Support Vector Machine",
    "ensemble": "Ensemble of Multiple Models"
}

# Market sentiment sources
SENTIMENT_SOURCES = ["twitter", "news", "economic_indicators", "technical_analysis"]

class PredictionRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    model: str = "ensemble"
    confidence_threshold: float = 0.7

class AISignal(BaseModel):
    symbol: str
    prediction_type: str
    direction: str
    confidence: float
    price_target: float
    stop_loss: float
    timeframe: str
    model_used: str
    features_analyzed: List[str]
    timestamp: str

def generate_ai_prediction(symbol: str, model: str = "ensemble") -> Dict[str, Any]:
    """Generate AI-based trading predictions"""
    
    # Simulate AI model processing time
    processing_time = random.uniform(0.1, 0.5)
    
    # Base price for calculations
    base_price = random.uniform(100, 5000)
    
    # Generate confidence score
    confidence = random.uniform(0.6, 0.95)
    
    # Determine prediction direction based on "AI analysis"
    market_conditions = random.choice(["bullish", "bearish", "neutral"])
    if market_conditions == "bullish":
        direction = "BUY"
        price_target = base_price * random.uniform(1.02, 1.08)
        stop_loss = base_price * random.uniform(0.95, 0.98)
    elif market_conditions == "bearish":
        direction = "SELL"
        price_target = base_price * random.uniform(0.92, 0.98)
        stop_loss = base_price * random.uniform(1.02, 1.05)
    else:
        direction = "HOLD"
        price_target = base_price * random.uniform(0.99, 1.01)
        stop_loss = base_price * random.uniform(0.97, 1.03)
    
    # Features analyzed by AI
    features = [
        "price_momentum",
        "volume_profile", 
        "market_sentiment",
        "technical_indicators",
        "volatility_patterns",
        "correlation_analysis",
        "news_sentiment",
        "macro_economic_factors"
    ]
    
    selected_features = random.sample(features, random.randint(4, 7))
    
    return {
        "symbol": symbol,
        "prediction_type": "price_direction",
        "direction": direction,
        "confidence": round(confidence, 3),
        "price_target": round(price_target, 2),
        "current_price": round(base_price, 2),
        "stop_loss": round(stop_loss, 2),
        "timeframe": "1h",
        "model_used": model,
        "features_analyzed": selected_features,
        "market_conditions": market_conditions,
        "processing_time_ms": round(processing_time * 1000, 2),
        "risk_reward_ratio": round(abs(price_target - base_price) / abs(stop_loss - base_price), 2),
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }

def generate_sentiment_analysis(symbol: str) -> Dict[str, Any]:
    """Generate market sentiment analysis"""
    
    sentiment_scores = {
        "twitter": random.uniform(-1, 1),
        "news": random.uniform(-1, 1), 
        "economic_indicators": random.uniform(-1, 1),
        "technical_analysis": random.uniform(-1, 1)
    }
    
    # Overall sentiment
    overall_sentiment = np.mean(list(sentiment_scores.values()))
    
    if overall_sentiment > 0.2:
        sentiment_label = "POSITIVE"
    elif overall_sentiment < -0.2:
        sentiment_label = "NEGATIVE"
    else:
        sentiment_label = "NEUTRAL"
    
    return {
        "symbol": symbol,
        "overall_sentiment": round(overall_sentiment, 3),
        "sentiment_label": sentiment_label,
        "confidence": random.uniform(0.7, 0.95),
        "sources": sentiment_scores,
        "key_drivers": random.sample([
            "earnings_report", "market_volatility", "sector_rotation", 
            "regulatory_news", "technical_breakout", "volume_spike"
        ], 3),
        "sentiment_trend": random.choice(["improving", "deteriorating", "stable"]),
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "engine-b-ai-predictions",
        "version": "2.0.0",
        "ai_models": len(PREDICTION_MODELS),
        "sentiment_sources": len(SENTIMENT_SOURCES),
        "capabilities": "ML predictions, sentiment analysis",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        "uptime": "running"
    }

@app.post("/api/predict")
async def generate_prediction(request: PredictionRequest):
    """Generate AI trading prediction for a symbol"""
    try:
        if request.model not in PREDICTION_MODELS:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not supported")
        
        # Simulate AI processing
        await asyncio.sleep(random.uniform(0.2, 0.8))
        
        prediction = generate_ai_prediction(request.symbol, request.model)
        
        # Filter by confidence threshold
        if prediction["confidence"] < request.confidence_threshold:
            prediction["direction"] = "HOLD"
            prediction["note"] = f"Low confidence ({prediction['confidence']:.3f} < {request.confidence_threshold})"
        
        return {
            "status": "success",
            "prediction": prediction,
            "model_info": {
                "name": request.model,
                "description": PREDICTION_MODELS[request.model]
            },
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/api/signals")
async def get_ai_signals():
    """Get AI trading signals for multiple symbols"""
    try:
        symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY"]
        signals = []
        
        for symbol in symbols:
            prediction = generate_ai_prediction(symbol)
            sentiment = generate_sentiment_analysis(symbol)
            
            # Combine prediction and sentiment
            signal = {
                "symbol": symbol,
                "prediction": prediction,
                "sentiment": sentiment,
                "combined_score": round((prediction["confidence"] + abs(sentiment["overall_sentiment"])) / 2, 3),
                "recommendation": prediction["direction"]
            }
            signals.append(signal)
        
        return {
            "status": "success",
            "signals": signals,
            "count": len(signals),
            "models_used": list(PREDICTION_MODELS.keys()),
            "analysis_type": "AI + Sentiment",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate AI signals: {str(e)}")

@app.get("/api/sentiment/{symbol}")
async def get_sentiment_analysis(symbol: str):
    """Get sentiment analysis for a specific symbol"""
    try:
        sentiment = generate_sentiment_analysis(symbol.upper())
        
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "sentiment": sentiment,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

@app.get("/api/models")
async def get_available_models():
    """Get information about available AI models"""
    return {
        "status": "success",
        "models": [
            {
                "name": name,
                "description": desc,
                "accuracy": random.uniform(0.75, 0.92),
                "training_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                "supported_timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"]
            }
            for name, desc in PREDICTION_MODELS.items()
        ],
        "count": len(PREDICTION_MODELS),
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }

@app.post("/api/batch-predict")
async def batch_predictions(symbols: List[str], model: str = "ensemble"):
    """Generate predictions for multiple symbols"""
    try:
        if model not in PREDICTION_MODELS:
            raise HTTPException(status_code=400, detail=f"Model {model} not supported")
        
        predictions = []
        for symbol in symbols[:10]:  # Limit to 10 symbols
            await asyncio.sleep(0.1)  # Simulate processing
            prediction = generate_ai_prediction(symbol, model)
            predictions.append(prediction)
        
        return {
            "status": "success",
            "predictions": predictions,
            "count": len(predictions),
            "model_used": model,
            "processing_time": "batch_optimized",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "InfinityAI Engine B - AI Predictions",
        "version": "2.0.0",
        "status": "operational",
        "description": "Machine learning predictions, sentiment analysis, and trading recommendations",
        "features": [
            "Multi-model AI predictions",
            "Real-time sentiment analysis",
            "Risk-reward calculations", 
            "Confidence-based filtering",
            "Batch processing support"
        ],
        "endpoints": [
            "/health - Service health check",
            "/api/predict - Generate single prediction", 
            "/api/signals - Get AI signals for multiple symbols",
            "/api/sentiment/{symbol} - Get sentiment analysis",
            "/api/models - Get available AI models",
            "/api/batch-predict - Batch predictions"
        ],
        "ai_models": len(PREDICTION_MODELS),
        "sentiment_sources": SENTIMENT_SOURCES
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)