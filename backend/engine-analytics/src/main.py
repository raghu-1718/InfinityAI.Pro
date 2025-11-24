from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys, os
# Ensure package imports resolve when running as a module or from root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Shared security middleware lives under engine-core; import explicitly
try:
    from backend.engine_core.src.core.security_middleware import SecurityHeadersMiddleware as SharedSecurityHeaders
except Exception:
    # Fallback to legacy name if present
    from engines.security_middleware import SecurityHeadersMiddleware as SharedSecurityHeaders
import uvicorn, os, yaml, asyncio, time
from datetime import datetime
from dataclasses import asdict
import numpy as np

app = FastAPI(
    title="InfinityAI Engine B",
    description="Advanced AI/ML intelligence for Indian markets",
    version="4.6.0"
)

# Use shared security middleware for consistent headers across services
app.add_middleware(SharedSecurityHeaders)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://infinityai.pro,https://www.infinityai.pro,http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Global services - lazily initialized
CFG_PATH = "config/settings.yaml"
CFG = None
ai = None
explain_svc = None
gemini_model = None
gemini_api_key = None

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
            from .services.ai_model_service import AIModelService
            ai = AIModelService(settings_path=CFG_PATH)
        except Exception:
            pass  # Will be initialized on first use
    if explain_svc is None:
        try:
            from .services.explainability_service import ExplainabilityService
            explain_svc = ExplainabilityService(
                model_path="models_store/lightgbm_model.pkl",
                scaler_path="models_store/scaler.pkl",
                features_path="models_store/ta_features.json"
            )
        except Exception:
            pass  # Will be initialized on first use

def get_gemini_model():
    """Lazily initialize and cache the Gemini model and API key to avoid per-request overhead."""
    global gemini_model, gemini_api_key
    if gemini_model is not None:
        return gemini_model
    try:
        import google.generativeai as genai
        import os
        from google.cloud import secretmanager

        # Fetch and cache API key once
        if not gemini_api_key:
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "infinity-ai-5ec7c")
            api_key_local = None
            # Try primary key first, then secondary, then env
            try:
                secret_name = f"projects/{project_id}/secrets/gemini-api-key-primary/versions/latest"
                response = client.access_secret_version(request={"name": secret_name})
                api_key_local = response.payload.data.decode("UTF-8")
            except Exception:
                try:
                    secret_name = f"projects/{project_id}/secrets/gemini-api-key-secondary/versions/latest"
                    response = client.access_secret_version(request={"name": secret_name})
                    api_key_local = response.payload.data.decode("UTF-8")
                except Exception:
                    api_key_local = os.getenv("GEMINI_API_KEY_PRIMARY")

            if not api_key_local:
                raise HTTPException(status_code=503, detail="Gemini API key not configured in Secret Manager or environment")
            gemini_api_key = api_key_local

        # Configure and cache the model
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        return gemini_model
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Gemini API library not installed. Please install: pip install google-generativeai"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini model initialization failed: {e}")



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
async def ai_signals(fast: bool = False):
    """
    Generate AI signals.
    - fast=true: limit symbols (<=3), skip sentiment, and apply per-symbol timeouts for responsiveness.
    """
    init_services()
    if not ai or not CFG:
        raise HTTPException(status_code=503, detail="Services not initialized")

    all_symbols = (
        CFG.get("markets", {}).get("NSE_INDICES", [])
        + CFG.get("markets", {}).get("NSE_STOCKS", [])
        + CFG.get("markets", {}).get("MCX_COMMODITIES", [])
    )
    # Default fallbacks if config is empty
    if not all_symbols:
        all_symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS"]

    if fast:
        # Keep it tiny for health checks
        symbols = all_symbols[:3]
        # Run predictions concurrently with per-symbol timeout to avoid tail latency
        tasks = []
        for s in symbols:
            tasks.append(asyncio.wait_for(ai.predict_symbol(s, fast=True), timeout=3))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        sigs = [r for r in results if not isinstance(r, Exception)]
    else:
        # Standard path (top 10)
        symbols = all_symbols[:10]
        sigs = await ai.batch_signals(symbols, fast=False)

    return {
        "status": "success",
        "count": len(sigs),
        "symbols_considered": symbols,
        "fast": fast,
        "signals": [{**asdict(s), "timestamp": s.timestamp.isoformat()} for s in sigs],
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/api/ai-signals/fast")
async def ai_signals_fast():
    """Convenience alias to generate fast AI signals without query params."""
    return await ai_signals(fast=True)

@app.post("/api/predict/{symbol}")
async def predict_symbol(symbol: str):
    init_services()
    if not ai:
        raise HTTPException(status_code=503, detail="AI service not initialized")
    try:
        # Basic symbol validation: uppercase letters, digits, dot, underscore, hyphen, length <= 20
        import re
        if not re.match(r"^[A-Za-z0-9._-]{1,20}$", symbol or ""):
            raise HTTPException(status_code=422, detail="Invalid symbol format")
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

@app.post("/api/gemini/analyze")
async def gemini_analyze(request_data: dict):
    """
    Gemini AI Analysis Endpoint

    Processes prompts using Google's Gemini API for portfolio analysis,
    market insights, and trading recommendations.
    """
    try:
        # Reuse cached Gemini model to minimize cold latency
        model = get_gemini_model()

        # Extract request data
        prompt = request_data.get("prompt", "")
        context = request_data.get("context", {})
        user_id = request_data.get("userId", "anonymous")

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        # Enhanced prompt with context for trading analysis
        enhanced_prompt = f"""
You are InfinityAI.Pro's expert trading analyst specializing in Indian markets (NSE/BSE/MCX).

User Context: {user_id}
Additional Context: {context}

Analysis Request:
{prompt}

Please provide:
1. Clear, actionable insights
2. Risk assessment for Indian markets
3. Specific recommendations with rationale
4. Market timing considerations
5. Risk management suggestions

Focus on NSE/BSE stocks and MCX commodities. Consider current Indian market conditions.
"""

        # Generate response with bounded output and hard timeout to avoid request hanging
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

        def _call_gemini():
            return model.generate_content(
                enhanced_prompt,
                generation_config={
                    "max_output_tokens": 256,
                    "temperature": 0.7,
                    "top_p": 0.9,
                },
            )

        timeout_seconds = int(os.getenv("GEMINI_ANALYZE_TIMEOUT", "8"))
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_call_gemini)
            try:
                response = fut.result(timeout=timeout_seconds)
                return {
                    "status": "success",
                    "analysis": response.text,
                    "model": "gemini-1.5-flash",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_used": bool(context),
                }
            except FuturesTimeout:
                raise HTTPException(status_code=503, detail="Gemini backend timeout. Please retry.")

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Gemini API library not installed. Please install: pip install google-generativeai"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini analysis failed: {str(e)}"
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)