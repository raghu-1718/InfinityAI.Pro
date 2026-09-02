"""
InfinityAI.Pro Unified Backend Service Entrypoint
FastAPI application orchestrating Market Ingestion, AI Inference, Backtesting, and Portfolio State.
"""
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.middleware import CorrelationIdMiddleware, is_market_open_ist
from backend.src.routers import market, inference, backtest, portfolio

app = FastAPI(
    title="InfinityAI.Pro Unified Analytics & Trading Platform",
    description="Institutional-grade algorithmic trading and analytics engine for Indian Capital Markets.",
    version="2.5.0-PROD",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. Mount Idempotency & Tracing Middleware
app.add_middleware(CorrelationIdMiddleware)

# 2. Mount Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-correlation-id"]
)

# 3. Mount Microservice Routers
app.include_router(market.router)
app.include_router(inference.router)
app.include_router(backtest.router)
app.include_router(portfolio.router)


@app.get("/health", tags=["System Telemetry"])
async def health_check():
    """System health check and market operational status."""
    return {
        "status": "healthy",
        "service": "infinityai-backend",
        "version": "2.5.0-PROD",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "trading_mode": os.getenv("TRADING_MODE", "paper"),
        "market_status": "OPEN" if is_market_open_ist() else "CLOSED",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready", tags=["System Telemetry"])
async def readiness_check():
    """Kubernetes / Cloud Run readiness probe."""
    return {"status": "ready", "ready": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.src.main:app", host="0.0.0.0", port=8000, reload=True)
