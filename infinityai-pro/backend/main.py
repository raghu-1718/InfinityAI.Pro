"""
InfinityAI.Pro - Advanced AI Trading Platform
GPU-accelerated multi-cloud trading system
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import logging
import asyncio
from contextlib import asynccontextmanager

# Import all API routers
from api.advanced_analysis import router as analysis_router
from api.health import router as health_router
from api.market_data import router as market_router
from api.orders import router as orders_router
from api.risk import router as risk_router
from api.websocket import router as ws_router

# Import services
from services.advanced_ai_engine import advanced_ai_engine
from services.market_data_manager import market_data_manager
from services.live_trader import live_trader
from services.websocket_manager import websocket_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    
    # Startup
    logger.info("🚀 Starting InfinityAI.Pro Advanced Trading Platform")
    
    try:
        # Initialize services
        await market_data_manager.initialize()
        await live_trader.initialize_components()
        
        logger.info("✅ All services initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("🛑 Shutting down InfinityAI.Pro")
        
        try:
            await advanced_ai_engine.close()
            await market_data_manager.close()
            await websocket_manager.close_all_connections()
            
            logger.info("✅ Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="InfinityAI.Pro - Advanced AI Trading Platform",
    description="GPU-accelerated multi-cloud AI trading system with real-time analysis",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://infinityai.pro-frontend.s3-website-us-east-1.amazonaws.com",
        "https://infinityai.pro",
        "https://www.infinityai.pro"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Import all routers
from api.dual_engine_analysis import router as dual_engine_router
from api.chatbot_api import router as chatbot_router
from api.ultra_ai_api import router as ultra_ai_router
from api.dhan_api import router as dhan_router
from api.ai_realtime_analysis import router as ai_analysis_router

# Include all routers
app.include_router(analysis_router)
app.include_router(dual_engine_router)
app.include_router(chatbot_router)
app.include_router(ultra_ai_router)
app.include_router(dhan_router)
app.include_router(ai_analysis_router)
app.include_router(health_router)
app.include_router(market_router)
app.include_router(orders_router)
app.include_router(risk_router)
app.include_router(ws_router)

# Mount static files for React frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint - serve React app
@app.get("/")
async def root():
    """Root endpoint - serve React app"""
    try:
        return FileResponse('static/index.html')
    except FileNotFoundError:
        # Fallback API info if React app not found
        return {
            "platform": "InfinityAI.Pro",
            "version": "2.0.0",
            "description": "Advanced AI Trading Platform with GPU Acceleration",
            "status": "🚀 Ready for Advanced Trading",
            "message": "React frontend not found. API endpoints are working."
        }

# WebSocket endpoint for real-time communication
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    
    await websocket_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Process message (could be trading commands, analysis requests, etc.)
            response = await process_websocket_message(data, user_id)
            
            # Send response back
            await websocket_manager.send_personal_message(response, user_id)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected for user: {user_id}")

async def process_websocket_message(message: str, user_id: str) -> str:
    """Process incoming WebSocket messages"""
    
    try:
        import json
        data = json.loads(message)
        
        message_type = data.get('type', 'unknown')
        
        if message_type == 'analysis_request':
            # Run quick analysis
            result = await advanced_ai_engine.analyze_market_comprehensive(
                market_data=data.get('market_data', {}),
                analysis_type='quick'
            )
            return json.dumps({
                'type': 'analysis_result',
                'data': result,
                'timestamp': str(asyncio.get_event_loop().time())
            })
            
        elif message_type == 'market_data_request':
            # Get real-time market data
            symbol = data.get('symbol', 'NIFTY')
            quote = await market_data_manager.get_real_time_quote(symbol)
            return json.dumps({
                'type': 'market_data',
                'symbol': symbol,
                'data': quote,
                'timestamp': str(asyncio.get_event_loop().time())
            })
            
        else:
            return json.dumps({
                'type': 'error',
                'message': f'Unknown message type: {message_type}'
            })
            
    except Exception as e:
        logger.error(f"WebSocket message processing error: {e}")
        return json.dumps({
            'type': 'error',
            'message': str(e)
        })

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "platform": "InfinityAI.Pro",
        "version": "2.0.0",
        "gpu_enabled": True,
        "services": {
            "ai_engine": "operational",
            "market_data": "operational",
            "live_trader": "operational",
            "websocket": "operational"
        }
    }

# Catch-all route for React SPA (only for frontend routes)
@app.get("/{catchall:path}")
async def serve_react_app(request: Request, catchall: str):
    """Serve React app for frontend routes only"""
    # Exclude all API routes and special FastAPI paths
    excluded_paths = [
        'api/', 'docs', 'openapi.json', 'redoc', 'health', 'ws/',
        'ai/', 'dhan/', 'static/'
    ]
    
    # Check if this is an excluded route
    for excluded in excluded_paths:
        if catchall.startswith(excluded):
            # Let FastAPI handle 404 naturally
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")
    
    # Serve the React app's index.html for all other routes (frontend routes)
    try:
        return FileResponse('static/index.html')
    except FileNotFoundError:
        return {"message": "React app not found. Run the frontend build first."}

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )