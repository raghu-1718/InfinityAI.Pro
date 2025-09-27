# Entry point for FastAPI application
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.trading import router as trading_router
from api.options import router as options_router
from api.ai import router as ai_router
from api.user import router as user_router
from services.ai import ai_manager
import asyncio
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    try:
        logger.info("Initializing AI Manager...")
        await ai_manager.initialize()
        logger.info("AI Manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI Manager: {e}")
        # Don't crash the app, just log the error
        pass

    yield

    # Shutdown
    try:
        await ai_manager.close()
        logger.info("AI Manager closed successfully")
    except Exception as e:
        logger.error(f"Error closing AI Manager: {e}")

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:3002", 
        "http://127.0.0.1:3002",
        "https://infinityai.pro",
        "https://api.infinityai.pro",
        "https://infinityai-frontend.onrender.com"
    ],  # Allow React dev server and production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trading_router, prefix="/trading")
app.include_router(options_router, prefix="/options")
app.include_router(ai_router, prefix="/ai")
app.include_router(user_router, prefix="/user")

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "InfinityAI.Pro Backend"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "InfinityAI.Pro Trading API", "version": "1.0.0", "status": "running"}

if __name__ == "__main__":
	import uvicorn
	import os
	port = int(os.getenv("PORT", 8000))
	uvicorn.run(app, host="0.0.0.0", port=port)