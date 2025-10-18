
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn, os, yaml, asyncio, time
from datetime import datetime
from dataclasses import asdict
import numpy as np
# Lazy imports - imported inside init_services() to avoid module-level import failures
# from services.ai_model_service import AIModelService
# from services.sentiment_service import SentimentService
# from services.explainability_service import ExplainabilityService
# from models.schemas import PredictionResponse, ModelStatus

app = FastAPI(
    title="InfinityAI Engine B",
    description="Advanced AI/ML intelligence for Indian markets",
    version="4.6.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

# Global services - lazily initialized
CFG_PATH = "config/settings.yaml"
CFG = None
ai = None
explain_svc = None

def init_services():
    """Initialize services lazily to avoid blocking container startup"""
    global CFG, ai, explain_svc
    if CFG is None:
        try:
            with open(CFG_PATH, "r") as f:
                CFG = yaml.safe_load(f)
        except Exception:
            CFG = {"service": {"version": "4.6.0"}, "markets": {"NSE_INDICES": [], "NSE_STOCKS": [], "MCX_COMMODITIES": []}}
    
    if ai is None:
        try:
            from services.ai_model_service import AIModelService
            ai = AIModelService(settings_path=CFG_PATH)
        except Exception:
            pass  # Will be initialized on first use
    
    if explain_svc is None:
        try:
            from services.explainability_service import ExplainabilityService
            explain_svc = ExplainabilityService(
                model_path="models_store/lightgbm_model.pkl",
                scaler_path="models_store/scaler.pkl",
                features_path="models_store/ta_features.json"
            )
        except Exception:
            pass  # Will be initialized on first use

@app.get("/")
async def root():
    init_services()
    models_list = list(ai.mz.models.keys()) if ai else []
    version = CFG.get("service", {}).get("version", "4.6.0") if CFG else "4.6.0"
    return {
        "service": "Engine B - AI/ML Intelligence",
        "version": version,
        "status": "operational",
        "models": models_list,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health():
    start = time.time()
    latency_ms = int((time.time() - start) * 1000)
    return {
        "status": "healthy",
        "service": "engine-b",
        "latency_ms": latency_ms,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/version")
async def version_info():
    """Version and build information for deployment tracking"""
    return {
        "service": "engine-b-ai-ml",
        "version": "4.6.0",
        "build_date": "2025-10-18",
        "commit_sha": os.getenv("GIT_COMMIT", "local"),
        "features": ["ai-predictions", "sentiment-analysis", "explainability", "market-intelligence"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/explain/{symbol}")
async def explain_symbol(symbol: str):
    init_services()
    if not ai or not explain_svc:
        raise HTTPException(status_code=503, detail="Services not initialized")
    try:
        snap = await ai.connector.fetch_snapshot(symbol.upper())
        X = ai.features if hasattr(ai, "features") else []
        features = snap if snap else {}
        arr = ai.mz.models["lgb_price"].predict(np.array([list(features.values())])) if features else np.zeros((1, len(X)))
        shap_importance = explain_svc.explain(np.array([list(features.values())]))
        return {"status": "success", "feature_importance": shap_importance, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explainability failed: {e}")

@app.get("/api/ai-signals")
async def ai_signals():
    init_services()
    if not ai or not CFG:
        raise HTTPException(status_code=503, detail="Services not initialized")
    symbols = (CFG.get("markets", {}).get("NSE_INDICES", []) + CFG.get("markets", {}).get("NSE_STOCKS", []) + CFG.get("markets", {}).get("MCX_COMMODITIES", []))[:10]
    try:
        sigs = await ai.batch_signals(symbols)
        return {
            "status": "success",
            "count": len(sigs),
            "signals": [{**asdict(s), "timestamp": s.timestamp.isoformat()} for s in sigs],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict/{symbol}")
async def predict_symbol(symbol: str):
    init_services()
    if not ai:
        raise HTTPException(status_code=503, detail="AI service not initialized")
    try:
        s = await ai.predict_symbol(symbol.upper())
        return {"status":"success", "signal": {**asdict(s), "timestamp": s.timestamp.isoformat()}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

@app.post("/api/batch-predict")
async def batch_predict(symbols: list[str]):
    init_services()
    if not ai:
        raise HTTPException(status_code=503, detail="AI service not initialized")
    try:
        sigs = await ai.batch_signals([s.upper() for s in symbols[:10]])
        return {
            "status": "success",
            "signals": [{**asdict(s), "timestamp": s.timestamp.isoformat()} for s in sigs],
            "count": len(sigs),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {e}")

@app.get("/api/sentiment/{symbol}")
async def get_sentiment(symbol: str):
    init_services()
    if not ai:
        raise HTTPException(status_code=503, detail="AI service not initialized")
    try:
        news = await ai.connector.fetch_news(5)
        score = ai.sentiment.score_news(news)
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "sentiment_score": score,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {e}")

@app.get("/api/models/status")
async def model_status():
    init_services()
    if not ai:
        return {"status": "services_not_initialized", "models": []}
    m = ai.mz
    return {
        "status": "success",
        "models": [
            {
                "name": k,
                "type": type(v).__name__,
                "trained": bool(m.fitted.get(k, False)),
                "last_trained": m.last_trained.get(k).isoformat() if m.last_trained.get(k) else None,
                "samples_seen": 0,
                "metrics": m.metrics.get(k, {})
            } for k, v in m.models.items()
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)