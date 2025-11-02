import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure local imports work when executed by Vercel runtime
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from routers import webhook_router  # noqa: E402

app = FastAPI(
    title="InfinityAI Edge API",
    description="Handles webhooks and other lightweight edge tasks.",
    version="1.0.0",
)

# --- CORS ---
origins = [
    os.environ.get("FRONTEND_VERCEL_URL", "http://localhost:5173"),
    "https://infinityai.pro",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(webhook_router.router, prefix="/api")


# --- Health Check ---
@app.get("/api/health", tags=["Health"]) 
async def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}
