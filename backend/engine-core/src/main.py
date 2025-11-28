import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
import httpx
from typing import Optional, Dict, Any, List
from dhanhq import dhanhq

# --- Pydantic Models ---
class OrchestrateRequest(BaseModel):
    symbol: str
    qty: Optional[float] = 1.0
    strategy: Optional[str] = None

class MarketDataResponse(BaseModel):
    symbol: str
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class NewsArticle(BaseModel):
    title: str | None
    source: str | None
    url: str | None
    publishedAt: str | None

class NewsResponse(BaseModel):
    query: str
    count: int
    articles: List[NewsArticle]

# --- FastAPI App Initialisation ---
app = FastAPI(
    title="Iaminfinity - Engine B (Core Orchestration & Data)",
    version="1.1.0"
)

# --- DhanHQ API Client Dependency ---
def get_dhan_client():
    client_id = os.getenv("DHAN_CLIENT_ID")
    access_token = os.getenv("DHAN_ACCESS_TOKEN")
    if not client_id or not access_token:
        raise HTTPException(status_code=500, detail="DhanHQ credentials not set.")
    return dhanhq(client_id, access_token)

# --- Core Endpoints ---
@app.get("/")
async def root():
    return {
        "service": "Iaminfinity Engine B",
        "version": "1.1.0",
        "status": "operational",
        "description": "Core Orchestration & Data Aggregation Engine",
        "capabilities": [
            "Workflow Orchestration",
            "Real-time Market Data via DhanHQ",
            "Live Data Subscriptions",
            "Multi-Engine Coordination",
            "News & Sentiment Analysis"
        ],
        "endpoints": {
            "orchestrate": "/orchestrate - Coordinate AI predictions and trade execution",
            "subscribe": "/dhan/subscribe-live-data - Subscribe to live market data feeds",
            "docs": "/docs - Interactive API documentation"
        }
    }

@app.get("/healthz")
async def healthz():
    return {"status": "healthy", "service": "engine-b"}

@app.post("/orchestrate")
async def orchestrate(req: OrchestrateRequest, bg: BackgroundTasks):
    engine_b_url = os.getenv("ENGINE_B_URL")
    engine_c_url = os.getenv("ENGINE_C_URL")
    if not engine_b_url or not engine_c_url:
        raise HTTPException(500, "ENGINE_B_URL or ENGINE_C_URL not configured.")

    # 1. Get Signal from Engine-B
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            b_resp = await client.post(f"{engine_b_url}/api/predict", json={"symbol": req.symbol})
            b_resp.raise_for_status()
            signal = b_resp.json()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Engine-B error: {e}")

    # 2. Prepare and Schedule Execution with Engine-C
    # This now needs to map to the new, more detailed model of engine-execution
    # We need to get the security_id for the symbol. For now, we hardcode it.
    # In a real system, you would have a symbol mapping service.
    security_id_map = {
        "RELIANCE": "1333", 
        "TCS": "2968",
        "HDFCBANK": "1394"
    }
    security_id = security_id_map.get(req.symbol.upper())
    if not security_id:
        raise HTTPException(404, f"Security ID for symbol {req.symbol} not found.")

    side = signal.get("signal", "HOLD").upper()
    if side == "HOLD":
        return {"signal": signal, "execution": "skipped_hold_signal"}

    exec_payload = {
        "transaction_type": side,
        "exchange_segment": "NSE_EQ",
        "product_type": "INTRADAY",
        "order_type": "MARKET",
        "validity": "DAY",
        "security_id": security_id,
        "quantity": int(req.qty) if req.qty else 1,
    }

    async def send_exec():
        try:
            c_resp = await client.post(f"{engine_c_url}/api/dhan/place-order", json=exec_payload)
            c_resp.raise_for_status()
        except Exception as e:
            print(f"Error sending execution request: {e}") # Replace with proper logging
            pass

    bg.add_task(send_exec)
    return {"signal": signal, "execution_payload": exec_payload, "status": "execution_scheduled"}


# --- Data Provider Endpoints ---

@app.post("/dhan/subscribe-live-data")
def subscribe_live_data(instruments: List[tuple[str, str]], dhan_client: dhanhq = Depends(get_dhan_client)):
    """
    Subscribes to real-time market data feed for a list of instruments.
    Each instrument is a tuple of (exchange_segment, security_id).
    Example: [("NSE_EQ", "1333")] for Reliance.
    """
    print(f"Subscribing to instruments: {instruments}")

    # Define the callback function to handle incoming ticks
    def on_tick(tick_data):
        # In a real application, you would push this data to a message queue (e.g., Kafka, Redis Pub/Sub)
        # or a time-series database for consumption by engine-core.
        print(f"Received Tick: {tick_data}")

    try:
        # The DhanHQ SDK handles the websocket connection and subscription in the background
        dhan_client.subscribe_on_tick(instruments, on_tick)
        return {"status": "success", "message": f"Successfully subscribed to {len(instruments)} instruments."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to subscribe to live data: {str(e)}")
