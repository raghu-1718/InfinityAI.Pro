import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from dhanhq import dhanhq, DhanContext
import uvicorn
from google.cloud import secretmanager
import google.generativeai as genai

app = FastAPI(title="Iaminfinity - Engine B (AI/ML & Signals)")

# --- Secret Manager ---
def get_secret_payload(secret_id: str, version_id: str = "latest") -> str:
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "after-yesterday-473512-k3")
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error fetching secret {secret_id}: {e}")
        return ""

# --- Gemini Setup ---
def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = get_secret_payload("gemini-api-key")
    
    if api_key:
        genai.configure(api_key=api_key)
    else:
        print("Warning: Gemini API Key not found in Env or Secret Manager")

configure_gemini()

# --- Models ---
class SignalRequest(BaseModel):
    symbol: str
    fast: bool = False

class SignalResponse(BaseModel):
    symbol: str
    signal: str # BUY, SELL, HOLD
    confidence: float
    predicted_price: float
    timestamp: str
    model_version: str

# --- Bootstrap Models ---
def _bootstrap_models() -> Dict[str, Any]:
    return {"version": "core-ml-1.0", "models": ["rf_price", "xgb_price", "lgb_price"]}

MODEL_STORE = _bootstrap_models()

# --- DhanHQ Client Dependency ---
def get_dhan_client():
    client_id = os.getenv("DHAN_CLIENT_ID")
    access_token = os.getenv("DHAN_ACCESS_TOKEN")
    if not client_id or not access_token:
        raise HTTPException(status_code=500, detail="DhanHQ credentials not set.")
    dhan_context = DhanContext(client_id, access_token)
    return dhanhq(dhan_context)

# --- Health ---
@app.get("/healthz")
async def healthz():
    return {"status": "healthy", "service": "engine-b", "version": MODEL_STORE["version"]}

@app.get("/")
async def root():
    return {"service": "Iaminfinity Engine B (AI/ML)", "status": "ready"}

# --- Signal Generation Endpoint ---
@app.post("/api/v1/signal", response_model=SignalResponse)
async def generate_signal(req: SignalRequest):
    if not req.symbol:
        raise HTTPException(status_code=422, detail="symbol required")
    
    # Simulate AI computation
    await asyncio.sleep(0.05 if req.fast else 0.15)
    
    base = 100.0
    # Deterministic pseudo-prediction
    pred = round(base * (1 + ((hash(req.symbol.upper()) % 21 - 10) / 1000)), 2)
    confidence = float(min(99.0, max(50.0, 55.0 + abs(pred - base) * 10)))
    
    signal = "HOLD"
    if pred > base:
        signal = "BUY"
    elif pred < base:
        signal = "SELL"
        
    return {
        "symbol": req.symbol.upper(),
        "signal": signal,
        "confidence": confidence,
        "predicted_price": pred,
        "timestamp": datetime.utcnow().isoformat(),
        "model_version": MODEL_STORE["version"]
    }

# --- Data Endpoints (Kept for AI Context) ---
@app.get("/dhan/holdings")
def get_holdings(dhan_client: dhanhq = Depends(get_dhan_client)):
    try:
        response = dhan_client.get_holdings()
        if response.get("status") == "success":
            return response.get("data")
        else:
            raise HTTPException(502, f"DhanHQ Error: {response.get("remarks")}")
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/dhan/positions")
def get_positions(dhan_client: dhanhq = Depends(get_dhan_client)):
    try:
        response = dhan_client.get_positions()
        if response.get("status") == "success":
            return response.get("data")
        else:
            raise HTTPException(502, f"DhanHQ Error: {response.get("remarks")}")
    except Exception as e:
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
