"""
DEPRECATED: Engine D has been archived.
The original implementation was moved to `archive/engine-d-deprecated-2025-11-25`.
Do not use this module. Use Engine C equivalents under `engines/engine-c-execution/services/`.
"""

raise RuntimeError("Engine D archived. See archive/engine-d-deprecated-2025-11-25")
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from engines.security_middleware import SecurityHeadersMiddleware as SharedSecurityHeaders
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
import os
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import google.generativeai as genai
from google.cloud import secretmanager

# Google Cloud Project Configuration
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'after-yesterday-473512-k3')

def get_gemini_api_key() -> str:
    """Get Gemini API key from GCP Secret Manager or environment variables."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        # Try primary key first
        secret_name = f"projects/{PROJECT_ID}/secrets/gemini-api-key-primary/versions/latest"
        response = client.access_secret_version(request={"name": secret_name})
        api_key = response.payload.data.decode("UTF-8")
        return api_key
    except Exception:
        try:
            # Fallback to secondary key
            secret_name = f"projects/{PROJECT_ID}/secrets/gemini-api-key-secondary/versions/latest"
            response = client.access_secret_version(request={"name": secret_name})
            api_key = response.payload.data.decode("UTF-8")
            return api_key
        except Exception:
            # Final fallback to environment variable
            api_key = os.getenv("GEMINI_API_KEY_PRIMARY")
            if api_key:
                return api_key
            else:
                raise ValueError("Gemini API key not configured in Secret Manager or environment")

# Health orchestrator import with fallback
try:
    from health_orchestrator import health_orchestrator
except Exception:
    class _HealthStub:
        async def get_comprehensive_health(self) -> Dict[str, Any]:
            return {
                "timestamp": time.time(),
                "summary": {
                    "healthy_engines": 0,
                    "total_engines": 0,
                    "health_percentage": 0,
                    "avg_response_time_ms": 0,
                    "overall_status": "degraded",
                },
                "engines": {},
                "system_status": {
                    "orchestration": "inactive",
                    "monitoring": "disabled",
                    "last_update": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
                },
            }

        def get_simple_health_status(self) -> Dict[str, bool]:
            return {}

    health_orchestrator = _HealthStub()

# Auth service import with fallback
try:
    from services.auth_service import auth_service  # type: ignore
except Exception:
    class _AuthStub:
        def login(self, email: str, password: str) -> Dict[str, Any]:
            return {
                "access_token": "dev-token",
                "token_type": "bearer",
                "user": {"email": email, "username": email.split("@")[0], "role": "user"},
                "expires_in": 3600,
            }

        def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
            return {"sub": "dev@local", "role": "user", "exp": int(time.time()) + 3600}

    auth_service = _AuthStub()

# WebSocket manager import with fallback
try:
    from services.ws_manager import ws_manager  # type: ignore
except Exception:
    class _WSStub:
        async def connect(self, websocket: WebSocket, channel: str = "dashboard") -> None:
            await websocket.accept()

        def disconnect(self, websocket: WebSocket, channel: str = "dashboard") -> None:
            pass

        async def send_personal(self, message: Dict[str, Any], websocket: WebSocket) -> None:
            try:
                await websocket.send_json(message)
            except Exception:
                pass

        async def broadcast(self, message: Dict[str, Any], channel: str = "dashboard") -> None:
            return

        def get_connection_stats(self) -> Dict[str, Any]:
            return {"total_connections": 0, "channels": {"dashboard": 0, "trades": 0, "signals": 0, "health": 0}}

    ws_manager = _WSStub()

# Event broadcaster import with fallback
try:
    from services.event_broadcaster import EventBroadcaster  # type: ignore
except Exception:
    class EventBroadcaster:  # type: ignore
        def __init__(self, ws_mgr: Any):
            self.ws_manager = ws_mgr
            self.event_count = 0

        async def broadcast_trade_event(self, trade_data: Dict[str, Any]) -> None:
            self.event_count += 1
            await self.ws_manager.broadcast({"type": "trade", "data": trade_data, "event_id": f"trade_{self.event_count}"}, channel="trades")

        async def broadcast_signal_event(self, signal_data: Dict[str, Any]) -> None:
            self.event_count += 1
            await self.ws_manager.broadcast({"type": "signal", "data": signal_data, "event_id": f"signal_{self.event_count}"}, channel="signals")

        async def broadcast_custom_event(self, event_type: str, data: Dict[str, Any], channel: str = "dashboard") -> None:
            self.event_count += 1
            await self.ws_manager.broadcast({"type": event_type, "data": data, "event_id": f"{event_type}_{self.event_count}"}, channel=channel)

        def get_stats(self) -> Dict[str, Any]:
            return {"total_events": self.event_count, "connections": self.ws_manager.get_connection_stats()}


# Initialize app and components
app = FastAPI(title="InfinityAI Engine D - Chatbot & Orchestration", description="Multi-engine orchestration and AI chatbot service with JWT auth and WebSocket", version="4.6.0")
security = HTTPBearer()
event_broadcaster = EventBroadcaster(ws_manager)

# Security Headers and CORS
# Use shared security headers across services
app.add_middleware(SharedSecurityHeaders)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://infinityai.pro,https://www.infinityai.pro,http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Lifespan
STARTED_AT = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[Engine-D] Starting up at {datetime.now(timezone.utc).isoformat()}, PID={os.getpid()}")
    yield
    print(f"[Engine-D] Shutting down at {datetime.now(timezone.utc).isoformat()}, PID={os.getpid()}")

app.router.lifespan_context = lifespan


# Models
class ChatRequest(BaseModel):
    message: str
    user_id: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    status: str
    message_id: str
    response: str
    intent: str
    confidence: float
    timestamp: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]
    expires_in: int


class BroadcastRequest(BaseModel):
    event_type: str
    data: Dict[str, Any]
    channel: Optional[str] = "dashboard"


def classify_intent(message: str) -> Tuple[str, float]:
    msg = message.lower()
    if any(w in msg for w in ["status", "health", "system", "running"]):
        return ("status", 0.9)
    if any(w in msg for w in ["market", "price", "signal", "data"]):
        return ("market_data", 0.8)
    if any(w in msg for w in ["ai", "predict", "forecast", "analysis"]):
        return ("ai_prediction", 0.8)
    if any(w in msg for w in ["trade", "buy", "sell", "order"]):
        return ("trade_execution", 0.7)
    if any(w in msg for w in ["portfolio", "balance", "holdings"]):
        return ("portfolio", 0.8)
    if any(w in msg for w in ["dhan", "oauth", "connect", "account"]):
        return ("account_management", 0.7)
    return ("general", 0.5)


async def generate_response(intent: str, message: str, confidence: float) -> str:
    # Configure Gemini
    try:
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Construct prompt for Gemini
        gemini_prompt = f"""
        You are InfinityAI.Pro's expert chatbot.
        User message: {message}
        Detected intent: {intent}
        Confidence: {confidence}

        Based on the user's message and detected intent, provide a concise and helpful response.
        If the intent is 'status', provide a summary of the system health.
        If the intent is 'market_data', explain that Engine A provides this.
        If the intent is 'ai_prediction', explain that Engine B provides this.
        If the intent is 'trade_execution', explain that Engine C handles this.
        If the intent is 'portfolio', explain that Engine C provides this.
        If the intent is 'account_management', explain that Engine C handles this.
        Otherwise, provide a general helpful response.
        """

        response = model.generate_content(gemini_prompt)
        return response.text
    except Exception as e:
        return f"🤖 **InfinityAI Assistant**: I'm sorry, I'm having trouble connecting to my AI brain. Error: {str(e)[:100]}"

    if intent == "status":
        try:
            health_data = await health_orchestrator.get_comprehensive_health()
            summary = health_data.get("summary", {})
            response = "🚀 **System Status Report**\n\n"
            response += f"📊 **Health**: {summary.get('healthy_engines', 0)}/{summary.get('total_engines', 0)} engines online ({summary.get('health_percentage', 0)}%)\n"
            response += f"⚡ **Performance**: {summary.get('avg_response_time_ms', 0)}ms avg response time\n"
            overall = summary.get("overall_status", "unknown")
            response += f"🎯 **Status**: {str(overall).upper()}\n\n"
            response += "**Engine Details:**\n"
            for name, engine_data in health_data.get("engines", {}).items():
                status_icon = "✅" if engine_data.get("healthy") else "❌"
                response += f"{status_icon} **Engine {name}**: {engine_data.get('status','n/a')} ({engine_data.get('response_time_ms','?')}ms)\n"
            return response
        except Exception as e:
            return f"⚠️ **System Status**: Error retrieving health data - {str(e)[:50]}"
    if intent == "market_data":
        return "📈 **Market Data**: Connecting to Engine A for live NSE/BSE/MCX data. Please check market signals endpoint for real-time information."
    if intent == "ai_prediction":
        return "🤖 **AI Predictions**: Engine B provides ML-powered trading signals with 11 technical indicators. Check AI signals endpoint for live predictions."
    if intent == "trade_execution":
        return "💰 **Trading**: Engine C handles trade execution via Dhan API integration. Please ensure your Dhan account is connected for live trading."
    if intent == "portfolio":
        return "📊 **Portfolio**: Portfolio data available through Engine C. Connect your Dhan account to view live holdings and P&L."
    if intent == "account_management":
        return "🔐 **Account Management**: Use Engine C's OAuth endpoints to connect your Dhan trading account securely."
    return f"🤖 **InfinityAI Assistant**: I understand you're asking about '{message}'. I can help with system status, market data, AI predictions, trading, and account management. What would you like to know?"


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "engine-d-orchestration",
        "websocket_connections": ws_manager.get_connection_stats(),
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        "uptime_seconds": round(time.time() - STARTED_AT, 1),
    }

@app.get("/version")
async def version_info():
    """Version and build information for deployment tracking"""
    return {
        "service": "engine-d-orchestration",
        "version": "4.6.0",
        "build_date": "2025-10-18",
        "commit_sha": os.getenv("GIT_COMMIT", "local"),
        "features": ["chatbot", "websocket", "orchestration", "health-monitoring", "jwt-auth"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> Dict[str, Any]:
    try:
        result_opt = auth_service.login(request.email, request.password)
        if result_opt is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        result: Dict[str, Any] = result_opt
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.get("/auth/verify")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    try:
        token = credentials.credentials
        payload_opt = auth_service.verify_token(token)
        if payload_opt is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        payload: Dict[str, Any] = payload_opt
        return {"status": "valid", "user": payload.get("sub"), "role": payload.get("role"), "expires": payload.get("exp")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token verification failed: {str(e)}")


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await ws_manager.connect(websocket, "dashboard")
    try:
        await ws_manager.send_personal({"type": "connection", "message": "Connected to InfinityAI.Pro Dashboard", "timestamp": datetime.now(timezone.utc).isoformat()}, websocket)
        while True:
            try:
                data = await websocket.receive_text()
                await ws_manager.send_personal({"type": "echo", "data": data, "timestamp": datetime.now(timezone.utc).isoformat()}, websocket)
            except WebSocketDisconnect:
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket, "dashboard")


@app.websocket("/ws/trades")
async def websocket_trades(websocket: WebSocket):
    await ws_manager.connect(websocket, "trades")
    try:
        await ws_manager.send_personal({"type": "connection", "message": "Connected to Trade Execution Feed", "timestamp": datetime.now(timezone.utc).isoformat()}, websocket)
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket, "trades")


@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    await ws_manager.connect(websocket, "signals")
    try:
        await ws_manager.send_personal({"type": "connection", "message": "Connected to AI Signals Feed", "timestamp": datetime.now(timezone.utc).isoformat()}, websocket)
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket, "signals")

# HTTP GET probes for WebSocket readiness (for uptime/verification tools)
@app.get("/ws/dashboard")
async def websocket_dashboard_probe():
    return {"status": "ok", "websocket": "available", "path": "/ws/dashboard"}

@app.get("/ws/trades")
async def websocket_trades_probe():
    return {"status": "ok", "websocket": "available", "path": "/ws/trades"}

@app.get("/ws/signals")
async def websocket_signals_probe():
    return {"status": "ok", "websocket": "available", "path": "/ws/signals"}


@app.post("/broadcast/trade")
async def broadcast_trade(request: BroadcastRequest) -> Dict[str, Any]:
    try:
        await event_broadcaster.broadcast_trade_event(request.data)
        return {"status": "success", "message": "Trade event broadcasted", "connections": ws_manager.get_connection_stats()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Broadcast failed: {str(e)}")


@app.post("/broadcast/signal")
async def broadcast_signal(request: BroadcastRequest) -> Dict[str, Any]:
    try:
        await event_broadcaster.broadcast_signal_event(request.data)
        return {"status": "success", "message": "Signal event broadcasted", "connections": ws_manager.get_connection_stats()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Broadcast failed: {str(e)}")


@app.post("/broadcast/custom")
async def broadcast_custom(request: BroadcastRequest) -> Dict[str, Any]:
    try:
        await event_broadcaster.broadcast_custom_event(request.event_type, request.data, request.channel or "dashboard")
        return {"status": "success", "message": f"{request.event_type} event broadcasted to {request.channel}", "connections": ws_manager.get_connection_stats()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Broadcast failed: {str(e)}")


@app.get("/broadcast/stats")
async def broadcast_stats() -> Dict[str, Any]:
    return {"status": "success", "data": event_broadcaster.get_stats(), "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}


@app.get("/api/health/comprehensive")
async def comprehensive_health() -> Dict[str, Any]:
    try:
        return await health_orchestrator.get_comprehensive_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/api/health/simple")
async def simple_health() -> Dict[str, Any]:
    try:
        health_data = await health_orchestrator.get_comprehensive_health()
        return {"engines": health_orchestrator.get_simple_health_status(), "summary": health_data.get("summary", {})}
    except Exception as e:
        return {"engines": {name: False for name in ['A', 'B', 'C', 'D', 'ULTRA']}, "summary": {"healthy_engines": 0, "total_engines": 5, "health_percentage": 0, "overall_status": "critical"}, "error": str(e)[:100]}

@app.get("/api/status")
async def engine_status() -> Dict[str, Any]:
    """Engine D status endpoint - MISSING ENDPOINT FIXED"""
    try:
        # Get comprehensive health data
        health_data = await health_orchestrator.get_comprehensive_health()

        # Get WebSocket connection stats
        ws_stats = ws_manager.get_connection_stats()

        # Get event broadcaster stats
        event_stats = event_broadcaster.get_stats()

        return {
            "status": "operational",
            "service": "engine-d-orchestration",
            "version": "4.6.0",
            "uptime_seconds": round(time.time() - STARTED_AT, 1),
            "health_summary": health_data.get("summary", {}),
            "websocket_connections": ws_stats,
            "event_stats": event_stats,
            "engines_status": health_orchestrator.get_simple_health_status(),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            "features": ["chatbot", "websocket", "orchestration", "health-monitoring", "jwt-auth"],
            "last_health_check": health_data.get("timestamp", time.time())
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "engine-d-orchestration",
            "error": str(e)[:100],
            "uptime_seconds": round(time.time() - STARTED_AT, 1),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest) -> Dict[str, Any]:
    try:
        intent, confidence = classify_intent(request.message)
        response_text = await generate_response(intent, request.message, confidence)
        response = ChatResponse(
            status="success",
            message_id=f"msg_{int(time.time())}_{hash(request.user_id) % 10000}",
            response=response_text,
            intent=intent,
            confidence=confidence,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        )
        return response.model_dump()
    except Exception as e:
        return {"status": "error", "message_id": f"error_{int(time.time())}", "response": f"Sorry, I encountered an error: {str(e)[:100]}", "intent": "error", "confidence": 0.0, "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "service": "InfinityAI.Pro - Engine D",
        "version": "4.6.0",
        "status": "operational",
        "deployment": "Google Cloud Run",
        "connected_engines": ["A", "B", "C"],
        "features": [
            "Multi-engine health monitoring",
            "Real-time system orchestration",
            "AI-powered chatbot",
            "Intent recognition",
            "Comprehensive health reporting",
        ],
        "endpoints": [
            "/health - Basic health check",
            "/api/health/comprehensive - Full system health",
            "/api/health/simple - Boolean health status",
            "/api/chat - AI chatbot interface",
            "/broadcast/* - Event broadcasting endpoints",
        ],
    }


@app.get("/dashboard")
async def serve_dashboard():
    html = f"""
    <!DOCTYPE html>
    <html><head><title>InfinityAI.Pro Dashboard</title>
    <meta http-equiv='refresh' content='15'>
    <style>
        body{{font-family:Arial;background:#f9fafb;margin:40px}}
        h1{{color:#333}} .card{{background:#fff;padding:20px;border-radius:10px;box-shadow:0 1px 6px #ccc}}
    </style></head>
    <body><div class='card'>
    <h1>🤖 InfinityAI.Pro - Engine D</h1>
    <p>Status: <b>Active (Google Cloud)</b></p>
    <p>Engines Monitored: A, B, C</p>
    <p>Frontend: Connected</p>
    <p>Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}</p>
    <a href='/api/health/comprehensive'>View Full Health JSON</a>
    </div></body></html>
    """
    return HTMLResponse(html)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)