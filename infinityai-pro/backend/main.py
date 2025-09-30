# Entry point for FastAPI application
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

# Import existing API routers
from api.trading import router as trading_router
from api.options import router as options_router
from api.ai import router as ai_router
from api.user import router as user_router
from api.storage import router as storage_router
from api.keys import router as keys_router

# Import new authentication and broker management
from app.auth import router as auth_router
from app.brokers import router as brokers_router
from app.database import init_db_pool, close_db_pool, create_tables, get_database_health
from app.crypto import get_crypto_health

# Import existing services
from services.cache.redis_service import health_check as redis_health_check
from services.security.azure_keyvault import initialize_key_vault, health_check as keyvault_health_check
from services.database.connection_pool import initialize_database as init_existing_db, health_check as existing_db_health_check
from services.market_data.fallback_service import get_status as market_data_status

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    try:
        logger.info("🚀 Initializing InfinityAI.Pro services...")
        
        # Initialize PostgreSQL database pool for auth/broker management
        logger.info("Initializing PostgreSQL database pool...")
        await init_db_pool()
        
        # Create database tables if they don't exist
        logger.info("Creating database tables...")
        await create_tables()
        
        # Initialize Azure Key Vault
        logger.info("Initializing Azure Key Vault...")
        await initialize_key_vault()
        
        # Initialize existing database services
        logger.info("Initializing existing database services...")
        await init_existing_db()
        
        # Temporarily disable AI manager initialization for testing
        # await ai_manager.initialize()
        logger.info("AI Manager initialization skipped for testing")
        
        logger.info("✅ All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Don't crash the app, just log the error
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

    yield

    # Shutdown
    try:
        logger.info("🔄 Shutting down services...")
        
        # Close PostgreSQL database pool
        await close_db_pool()
        
        # await ai_manager.close()
        logger.info("✅ All services shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

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
        "https://www.infinityai.pro",
        "https://api.infinityai.pro",
        "https://infinityai-frontend.onrender.com",
        "https://frontend-38jexw06p-infinityaipro.vercel.app",
        "https://*.vercel.app",
        "https://infinityaipro.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include existing API routers
app.include_router(trading_router, prefix="/trading")
app.include_router(options_router, prefix="/options")
app.include_router(ai_router, prefix="/ai")
app.include_router(user_router, prefix="/user")
app.include_router(storage_router, prefix="/storage")
app.include_router(keys_router, prefix="/keys")

# Include new authentication and broker management routers
app.include_router(auth_router)
app.include_router(brokers_router)

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {}
    }
    
    # Check PostgreSQL database (new auth/broker system)
    try:
        pg_status = await get_database_health()
        health_status["services"]["postgresql"] = pg_status
    except Exception as e:
        health_status["services"]["postgresql"] = {"status": "error", "error": str(e)}
    
    # Check cryptography system
    try:
        crypto_status = get_crypto_health()
        health_status["services"]["cryptography"] = crypto_status
    except Exception as e:
        health_status["services"]["cryptography"] = {"status": "error", "error": str(e)}
    
    # Check Redis cache
    try:
        redis_status = await redis_health_check()
        health_status["services"]["redis"] = redis_status
    except Exception as e:
        health_status["services"]["redis"] = {"status": "error", "error": str(e)}
    
    # Check Azure Key Vault
    try:
        vault_status = await keyvault_health_check()
        health_status["services"]["keyvault"] = vault_status
    except Exception as e:
        health_status["services"]["keyvault"] = {"status": "error", "error": str(e)}
    
    # Check existing database (Cassandra)
    try:
        existing_db_status = await existing_db_health_check()
        health_status["services"]["cassandra"] = existing_db_status
    except Exception as e:
        health_status["services"]["cassandra"] = {"status": "error", "error": str(e)}
    
    # Check Market Data providers
    try:
        market_status = get_status()
        health_status["services"]["market_data"] = {"status": "healthy", "providers": market_status}
    except Exception as e:
        health_status["services"]["market_data"] = {"status": "error", "error": str(e)}
    
    # Determine overall status
    service_statuses = []
    for service in health_status["services"].values():
        if isinstance(service, dict):
            service_statuses.append(service.get("status"))
    
    if any(status == "unhealthy" for status in service_statuses):
        health_status["status"] = "degraded"
    elif any(status == "error" for status in service_statuses):
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/healthz")
async def healthz_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "timestamp": "2025-09-28T08:50:00Z"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "InfinityAI.Pro Trading API", "version": "1.0.0", "status": "running"}

if __name__ == "__main__":
	import uvicorn
	import os
	port = int(os.getenv("PORT", 8000))
	uvicorn.run(app, host="0.0.0.0", port=port)