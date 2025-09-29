# Minimal main.py for Railway deployment
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2025-09-28T08:50:00Z"}

@app.get("/healthz")
async def healthz_check():
    """Health check endpoint for Railway"""
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