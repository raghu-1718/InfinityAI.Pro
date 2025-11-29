import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from google.cloud import secretmanager
import httpx
import uvicorn

app = FastAPI(title="InfinityAI.Pro - Engine A (Orchestration & Dhan Auth)")

# --- Secret Manager Helper ---
def get_secret(secret_id: str, version: str = "latest") -> str:
    """Retrieve secret from Google Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "after-yesterday-473512-k3")
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error fetching secret {secret_id}: {e}")
        return ""

# --- Models ---
class OrchestrateRequest(BaseModel):
    symbol: str
    qty: Optional[float] = 1.0
    strategy: Optional[str] = None

class DhanTokenExchangeRequest(BaseModel):
    code: str

# --- Config ---
ENGINE_B_URL = os.getenv("ENGINE_B_URL", "http://engine-core:8080")
ENGINE_C_URL = os.getenv("ENGINE_C_URL", "http://engine-execution:8080")

# --- Health & Root ---
@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "engine-a-orchestrator", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    return {
        "service": "InfinityAI.Pro Engine A (Orchestration & Dhan OAuth)",
        "status": "ready",
        "version": "3.0-dhan-only"
    }

# --- DhanHQ OAuth Endpoints ---
@app.get("/api/auth/dhan/login")
async def dhan_login():
    """Redirect user to DhanHQ OAuth login page"""
    client_id = os.getenv("DHAN_CLIENT_ID")
    if not client_id:
        client_id = get_secret("dhan-client-id")

    redirect_uri = os.getenv("DHAN_REDIRECT_URI", "https://infinityai.pro/api/auth/dhan/callback")

    if not client_id:
        raise HTTPException(500, "DHAN_CLIENT_ID not configured")

    login_url = f"https://api.dhan.co/v2/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    return RedirectResponse(login_url)

@app.post("/api/auth/dhan/callback")
async def dhan_callback(request: DhanTokenExchangeRequest):
    """Exchange authorization code for access token"""
    client_id = os.getenv("DHAN_CLIENT_ID") or get_secret("dhan-client-id")
    client_secret = os.getenv("DHAN_API_SECRET") or get_secret("dhan-api-secret")
    redirect_uri = os.getenv("DHAN_REDIRECT_URI", "https://infinityai.pro/api/auth/dhan/callback")

    if not client_id or not client_secret:
        raise HTTPException(500, "Dhan OAuth credentials not configured")

    token_url = "https://api.dhan.co/v2/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": request.code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(token_url, json=payload)
            response.raise_for_status()
            token_data = response.json()

            # TODO: Store access_token securely in Firestore or GSM
            return {
                "status": "success",
                "message": "Token exchange complete",
                "access_token": token_data.get("access_token"),
                "token_type": token_data.get("token_type"),
                "expires_in": token_data.get("expires_in")
            }
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Dhan OAuth token exchange failed: {str(e)}")

@app.get("/api/auth/dhan/validate")
async def validate_dhan_token():
    """Check if current Dhan access token is valid"""
    access_token = os.getenv("DHAN_ACCESS_TOKEN") or get_secret("dhan-access-token")

    if not access_token:
        return {"valid": False, "message": "No access token found"}

    # Simple validation - check if token is set and not empty
    # For production, implement proper token validation via Dhan API
    return {
        "valid": bool(access_token),
        "message": "Token present" if access_token else "Token missing"
    }

# --- Orchestration Endpoint ---
@app.post("/api/v1/trade/start")
async def orchestrate_trade(req: OrchestrateRequest, bg: BackgroundTasks):
    """
    Main orchestration endpoint:
    1. Validates Dhan authentication
    2. Calls Engine B for AI signal
    3. Calls Engine C for trade execution
    """
    # Validate Dhan token
    access_token = os.getenv("DHAN_ACCESS_TOKEN") or get_secret("dhan-access-token")
    if not access_token:
        raise HTTPException(401, "Dhan authentication required. Please authenticate via /api/auth/dhan/login")

    if not ENGINE_B_URL or not ENGINE_C_URL:
        raise HTTPException(500, "ENGINE_B_URL or ENGINE_C_URL not configured")

    # 1. Get AI Signal from Engine-B
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            signal_response = await client.post(
                f"{ENGINE_B_URL}/api/v1/signal",
                json={"symbol": req.symbol}
            )
            signal_response.raise_for_status()
            signal_data = signal_response.json()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Engine B (AI/ML) error: {str(e)}")

    signal = signal_data.get("signal", "HOLD").upper()

    if signal == "HOLD":
        return {
            "status": "no_action",
            "signal": signal_data,
            "execution": "skipped_hold_signal",
            "timestamp": datetime.utcnow().isoformat()
        }

    # 2. Prepare Execution Payload for Engine C
    # Security ID mapping (NSE Equity symbols to Dhan Security IDs)
    security_id_map = {
        "RELIANCE": "1333",
        "TCS": "2968",
        "HDFCBANK": "1394",
        "INFY": "1594",
        "ICICIBANK": "1270",
        "NIFTY": "13",
        "BANKNIFTY": "25"
    }

    security_id = security_id_map.get(req.symbol.upper())
    if not security_id:
        return {
            "status": "error",
            "message": f"Symbol {req.symbol} not supported. Add mapping to security_id_map.",
            "signal": signal_data
        }

    exec_payload = {
        "transaction_type": signal,  # BUY or SELL
        "exchange_segment": "NSE_EQ",
        "product_type": "INTRADAY",
        "order_type": "MARKET",
        "validity": "DAY",
        "security_id": security_id,
        "quantity": int(req.qty) if req.qty else 1,
        "price": 0.0
    }

    # 3. Schedule Execution with Engine C (Background Task)
    async def send_execution():
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                exec_response = await client.post(
                    f"{ENGINE_C_URL}/api/dhan/place-order",
                    json=exec_payload
                )
                exec_response.raise_for_status()
                print(f"✅ Execution successful: {exec_response.json()}")
            except Exception as e:
                print(f"❌ Execution failed: {str(e)}")

    bg.add_task(send_execution)

    return {
        "status": "execution_scheduled",
        "signal": signal_data,
        "execution_payload": exec_payload,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
