import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx
import uvicorn

app = FastAPI(title="Iaminfinity - Engine A (Orchestration & Auth)")

# --- Models ---
class OrchestrateRequest(BaseModel):
    symbol: str
    qty: Optional[float] = 1.0
    strategy: Optional[str] = None

# --- Config ---
ENGINE_B_URL = os.getenv("ENGINE_B_URL", "http://engine-core:8080") # Default to service name
ENGINE_C_URL = os.getenv("ENGINE_C_URL", "http://engine-execution:8080")

# --- Health & Root ---
@app.get("/healthz")
async def healthz():
    return {"status": "healthy", "service": "engine-a-orchestrator"}

@app.get("/")
async def root():
    return {"service": "Iaminfinity Engine A (Orchestration)", "status": "ready"}

# --- Orchestration Endpoint ---
@app.post("/orchestrate")
async def orchestrate(req: OrchestrateRequest, bg: BackgroundTasks):
    if not ENGINE_B_URL or not ENGINE_C_URL:
        raise HTTPException(500, "ENGINE_B_URL or ENGINE_C_URL not configured.")

    # 1. Get Signal from Engine-B (AI/ML)
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # Call Engine B for signal
            b_resp = await client.post(f"{ENGINE_B_URL}/api/v1/signal", json={"symbol": req.symbol})
            b_resp.raise_for_status()
            signal_data = b_resp.json()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Engine-B (AI) error: {e}")

    signal = signal_data.get("signal", "HOLD").upper()
    if signal == "HOLD":
        return {"signal": signal_data, "execution": "skipped_hold_signal"}

    # 2. Prepare Execution Payload
    # Map symbol to Security ID (Simple mapping for demo)
    security_id_map = {
        "RELIANCE": "1333", 
        "TCS": "2968",
        "HDFCBANK": "1394",
        "NIFTY": "13",
        "BANKNIFTY": "25"
    }
    security_id = security_id_map.get(req.symbol.upper(), "1333") # Default to Reliance if not found

    exec_payload = {
        "transaction_type": signal,
        "exchange_segment": "NSE_EQ",
        "product_type": "INTRADAY",
        "order_type": "MARKET",
        "validity": "DAY",
        "security_id": security_id,
        "quantity": int(req.qty) if req.qty else 1,
        "price": 0.0
    }

    # 3. Schedule Execution with Engine-C
    async def send_exec():
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                c_resp = await client.post(f"{ENGINE_C_URL}/api/dhan/place-order", json=exec_payload)
                c_resp.raise_for_status()
                print(f"Execution sent: {c_resp.json()}")
            except Exception as e:
                print(f"Error sending execution request: {e}")

    bg.add_task(send_exec)
    return {"signal": signal_data, "execution_payload": exec_payload, "status": "execution_scheduled"}

# --- DhanHQ OAuth Logic ---
@app.get("/api/auth/dhan/login")
async def dhan_login():
    client_id = os.getenv("DHAN_CLIENT_ID")
    redirect_uri = os.getenv("DHAN_REDIRECT_URI", "https://infinityai.pro/api/auth/dhan/callback")
    if not client_id:
        raise HTTPException(500, "DHAN_CLIENT_ID not set")
    
    login_url = f"https://dhan.co/login?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    return RedirectResponse(login_url)

@app.get("/api/auth/dhan/callback")
async def dhan_callback(code: str):
    return {"status": "received", "code": code, "message": "Token exchange logic to be implemented"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
