import os
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI(title="Iaminfinity - Engine A (Market Analytics & AI)")


class PredictRequest(BaseModel):
    symbol: str
    fast: bool = False


class GeminiRequest(BaseModel):
    prompt: str
    context: Dict[str, Any] = {}


def _bootstrap_models() -> Dict[str, Any]:
    # Lightweight synthetic bootstrap used for local runs and CI
    return {"version": "local-0.1", "models": ["rf_price", "xgb_price", "lgb_price"]}


MODEL_STORE = _bootstrap_models()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


@app.get("/healthz")
async def healthz():
    return {"status": "healthy", "service": "engine-a", "version": MODEL_STORE["version"], "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
async def root():
    return {"service": "Iaminfinity Engine A", "status": "ready", "models": MODEL_STORE["models"]}


@app.post("/api/predict")
async def predict(req: PredictRequest):
    if not req.symbol:
        raise HTTPException(status_code=422, detail="symbol required")

    # Simulate light compute; 'fast' avoids heavier operations
    await asyncio.sleep(0.05 if req.fast else 0.15)

    base = 100.0
    # deterministic pseudo-prediction to keep tests stable
    pred = round(base * (1 + ((hash(req.symbol.upper()) % 21 - 10) / 1000)), 2)
    confidence = float(min(99.0, max(50.0, 55.0 + abs(pred - base) * 10)))

    return {
        "symbol": req.symbol.upper(),
        "predicted_price": pred,
        "confidence": confidence,
        "signal_type": "BUY" if pred > base else "SELL" if pred < base else "HOLD",
        "model_version": MODEL_STORE["version"],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/ai-signals")
async def ai_signals(fast: bool = False):
    symbols = os.getenv("ENGINEB_SYMBOLS", "NIFTY,BANKNIFTY,RELIANCE,TCS").split(",")
    out = []
    for s in symbols[: (3 if fast else 10)]:
        out.append((await predict(PredictRequest(symbol=s.strip(), fast=fast))))
    return {"status": "success", "count": len(out), "signals": out}


@app.post("/api/gemini/analyze")
async def gemini_analyze(req: GeminiRequest):
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    # Unified Gemini Model
    if not api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured on the server.")

    try:
        # Using a single, unified model as requested
        model = genai.GenerativeModel('gemini-pro')
        
        # Asynchronously generate content
        response = await model.generate_content_async(prompt)
        
        analysis_text = response.text
        
        return {
            "status": "ok", 
            "analysis": analysis_text, 
            "model": "gemini-pro", 
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Log the exception for debugging
        # logger.error(f"Gemini API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred with the Gemini API: {str(e)}")
