# app/main.py - FastAPI application for InfinityAI.Pro
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import Dict, List, Optional
from pydantic import BaseModel
import asyncio

# Import AI services
try:
    from services.ai import ai_manager
    AI_AVAILABLE = True
except ImportError:
    print("⚠️  AI services not available - running without AI features")
    AI_AVAILABLE = False
    ai_manager = None

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict] = None

class ImageGenerationRequest(BaseModel):
    prompt: str
    steps: Optional[int] = 20
    guidance_scale: Optional[float] = 7.5
    height: Optional[int] = 512
    width: Optional[int] = 512

class EmbeddingRequest(BaseModel):
    text: str
    metadata: Optional[Dict] = None

class TradingSignalRequest(BaseModel):
    symbol: str
    direction: str
    score: float
    ml_prob: Optional[float] = 0.0
    rule_score: Optional[float] = 0.0

# FastAPI app
app = FastAPI(
    title="InfinityAI.Pro API",
    description="Comprehensive AI stack for trading intelligence",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global AI manager
ai_initialized = False

@app.on_event("startup")
async def startup_event():
    """Initialize AI services on startup"""
    global ai_initialized
    if not AI_AVAILABLE:
        print("ℹ️  AI services not available - trading features will work without AI")
        return

    try:
        await ai_manager.initialize()
        ai_initialized = True
        print("✅ AI services initialized")
    except Exception as e:
        print(f"❌ Failed to initialize AI services: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Close AI services on shutdown"""
    if AI_AVAILABLE and ai_manager:
        await ai_manager.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "InfinityAI.Pro AI Stack API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not AI_AVAILABLE:
        return {"status": "healthy", "ai_services": "not_available", "trading": "available"}

    if not ai_initialized:
        return {"status": "initializing", "ai_services": "not_ready"}

    try:
        health = await ai_manager.health_check()
        return {
            "status": "healthy" if health.get("overall") == "healthy" else "degraded",
            "ai_services": health
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Chat endpoints
@app.post("/ai/chat")
async def chat(request: ChatRequest):
    """Chat with AI assistant"""
    if not AI_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI services not available")

    try:
        response = await ai_manager.chat(request.message, request.context)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/trading/strategy")
async def generate_trading_strategy(request: TradingSignalRequest):
    """Generate AI-powered trading strategy"""
    try:
        signal_data = {
            "symbol": request.symbol,
            "direction": request.direction,
            "score": request.score,
            "ml_prob": request.ml_prob,
            "rule_score": request.rule_score
        }

        strategy = await ai_manager.generate_strategy(signal_data)
        return {"strategy": strategy}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/market/sentiment")
async def analyze_market_sentiment(symbol: str):
    """Analyze market sentiment for a symbol"""
    try:
        analysis = await ai_manager.analyze_market_sentiment(symbol)
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/trade/narrate")
async def narrate_trade(trade_data: Dict):
    """Generate AI narration for trade decisions"""
    try:
        narration = await ai_manager.generate_trade_narration(trade_data)
        return {"narration": narration}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Speech endpoints
@app.post("/ai/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """Convert speech to text"""
    try:
        audio_data = await file.read()
        result = await ai_manager.speech_to_text(audio_data, file.filename)
        return {"transcription": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vision endpoints
@app.post("/ai/vision/detect")
async def detect_objects(file: UploadFile = File(...)):
    """Detect objects in image"""
    try:
        image_data = await file.read()
        result = await ai_manager.detect_objects(image_data, file.filename)
        return {"detection": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/vision/generate")
async def generate_image(request: ImageGenerationRequest):
    """Generate image from text prompt"""
    try:
        result = await ai_manager.generate_image(
            request.prompt,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            height=request.height,
            width=request.width
        )
        return {"image": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/vision/analyze")
async def analyze_image(file: UploadFile = File(...), analysis_type: str = "general"):
    """Comprehensive image analysis"""
    try:
        image_data = await file.read()
        result = await ai_manager.analyze_image(image_data, analysis_type)
        return {"analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Embedding endpoints
@app.post("/ai/embed")
async def embed_text(request: EmbeddingRequest):
    """Generate embeddings for text"""
    try:
        result = await ai_manager.embed_text(request.text, request.metadata)
        return {"embedding": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/search")
async def search_similar(query: str, limit: int = 5):
    """Search for similar content"""
    try:
        results = await ai_manager.search_similar(query, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Trading Intelligence endpoints
@app.get("/ai/market/overview")
async def get_market_overview():
    """Get comprehensive market overview"""
    try:
        overview = await ai_manager.chat(
            "Provide a comprehensive market overview including key trends, sentiment analysis, and trading implications for commodities and equities."
        )
        return {"overview": overview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/portfolio/analyze")
async def analyze_portfolio(portfolio_data: Dict):
    """Analyze portfolio with AI insights"""
    try:
        analysis = await ai_manager.chat(
            f"Analyze this trading portfolio and provide insights: {portfolio_data}"
        )
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )