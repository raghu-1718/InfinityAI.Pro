from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException, File, UploadFile
from typing import Dict, List, Optional, Any
from services.chat_service import process_chat_command
import httpx
import os
import logging

# Import ai_manager after other imports to avoid circular imports
# from services.ai import ai_manager

AI_MANAGER_AVAILABLE = False  # Legacy flag; chat and core AI now use AIRouter directly

router = APIRouter()
logger = logging.getLogger(__name__)

# Multi-Cloud AI endpoints (AWS Primary, Azure Secondary)
from utils.config import CONFIG
from services.ai.router import AIRouter
from services.ai.llm_service import LLMService

# AWS SageMaker endpoints (Primary GPU provider)
AWS_SAGEMAKER_SD_ENDPOINT = CONFIG.AWS_SAGEMAKER_ENDPOINT or ""
AWS_SAGEMAKER_YOLO_ENDPOINT = CONFIG.AWS_SAGEMAKER_ENDPOINT or ""  # Same endpoint, different models
AWS_SAGEMAKER_WHISPER_ENDPOINT = CONFIG.AWS_SAGEMAKER_ENDPOINT or ""  # Same endpoint, different models

# Azure ML endpoints (Secondary GPU provider)
AZURE_ML_SD_ENDPOINT = CONFIG.AZURE_ML_ENDPOINT or ""
AZURE_ML_YOLO_ENDPOINT = CONFIG.AZURE_ML_ENDPOINT or ""
AZURE_ML_WHISPER_ENDPOINT = CONFIG.AZURE_ML_ENDPOINT or ""

# Legacy RunPod endpoints (for backward compatibility)
RUNPOD_SD_ENDPOINT = os.getenv("RUNPOD_SD_ENDPOINT", "")
RUNPOD_YOLO_ENDPOINT = os.getenv("RUNPOD_YOLO_ENDPOINT", "")
RUNPOD_WHISPER_ENDPOINT = os.getenv("RUNPOD_WHISPER_ENDPOINT", "")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")

async def proxy_to_runpod(endpoint: str, request: Request):
    """Proxy request to RunPod endpoint (legacy)"""
    if not endpoint:
        raise HTTPException(status_code=503, detail="RunPod endpoint not configured")

    try:
        # Handle different content types
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            # For file uploads (YOLO, Whisper)
            form_data = await request.form()
            files = {}
            data = {}

            for key, value in form_data.items():
                if hasattr(value, 'filename'):  # It's a file
                    files[key] = (value.filename, await value.read(), value.content_type)
                else:  # It's form data
                    data[key] = value

            headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"} if RUNPOD_API_KEY else {}

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(endpoint, files=files, data=data, headers=headers)
                return response.json()
        else:
            # For JSON requests (Stable Diffusion)
            payload = await request.json()
            headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"} if RUNPOD_API_KEY else {}

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                return response.json()
    except Exception as e:
        logger.error(f"RunPod proxy error: {e}")
        raise HTTPException(status_code=500, detail="AI service temporarily unavailable")

async def proxy_to_aws_sagemaker(endpoint: str, request: Request, model_type: str = "default"):
    """Proxy request to AWS SageMaker endpoint"""
    if not endpoint:
        raise HTTPException(status_code=503, detail="AWS SageMaker endpoint not configured")

    try:
        import boto3
        import json

        # Initialize SageMaker runtime client
        sagemaker_runtime = boto3.client(
            'sagemaker-runtime',
            region_name=CONFIG.AWS_REGION,
            aws_access_key_id=CONFIG.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=CONFIG.AWS_SECRET_ACCESS_KEY
        )

        # Handle different content types
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            # For file uploads (YOLO, Whisper)
            form_data = await request.form()
            payload = {}

            for key, value in form_data.items():
                if hasattr(value, 'filename'):  # It's a file
                    payload[key] = await value.read()
                else:  # It's form data
                    payload[key] = value

            # Convert to JSON for SageMaker
            payload_json = json.dumps(payload)
        else:
            # For JSON requests (Stable Diffusion)
            payload = await request.json()
            payload_json = json.dumps(payload)

        # Call SageMaker endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=endpoint.split('/')[-1],  # Extract endpoint name from URL
            ContentType='application/json',
            Body=payload_json
        )

        # Parse response
        result = json.loads(response['Body'].read().decode())
        return result

    except Exception as e:
        logger.error(f"AWS SageMaker proxy error: {e}")
        raise HTTPException(status_code=500, detail="AWS AI service temporarily unavailable")

async def proxy_to_azure_ml(endpoint: str, request: Request, model_type: str = "default"):
    """Proxy request to Azure ML endpoint"""
    if not endpoint:
        raise HTTPException(status_code=503, detail="Azure ML endpoint not configured")

    try:
        # Handle different content types
        content_type = request.headers.get("content-type", "")

        headers = {
            "Authorization": f"Bearer {CONFIG.AZURE_ML_KEY}",
            "Content-Type": "application/json"
        }

        if "multipart/form-data" in content_type:
            # For file uploads (YOLO, Whisper)
            form_data = await request.form()
            payload = {}

            for key, value in form_data.items():
                if hasattr(value, 'filename'):  # It's a file
                    # Convert file to base64 for Azure ML
                    import base64
                    file_data = await value.read()
                    payload[key] = base64.b64encode(file_data).decode('utf-8')
                else:  # It's form data
                    payload[key] = value
        else:
            # For JSON requests (Stable Diffusion)
            payload = await request.json()

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            return response.json()

    except Exception as e:
        logger.error(f"Azure ML proxy error: {e}")
        raise HTTPException(status_code=500, detail="Azure AI service temporarily unavailable")

async def proxy_to_multi_cloud_ai(request: Request, model_type: str = "sd"):
    """Multi-cloud AI proxy with failover (AWS Primary, Azure Secondary, RunPod Fallback)"""
    endpoints = {
        "sd": [
            (AWS_SAGEMAKER_SD_ENDPOINT, "aws", "sagemaker"),
            (AZURE_ML_SD_ENDPOINT, "azure", "ml"),
            (f"{RUNPOD_SD_ENDPOINT}/sdapi/v1/txt2img", "runpod", "legacy")
        ],
        "yolo": [
            (AWS_SAGEMAKER_YOLO_ENDPOINT, "aws", "sagemaker"),
            (AZURE_ML_YOLO_ENDPOINT, "azure", "ml"),
            (f"{RUNPOD_YOLO_ENDPOINT}/detect", "runpod", "legacy")
        ],
        "whisper": [
            (AWS_SAGEMAKER_WHISPER_ENDPOINT, "aws", "sagemaker"),
            (AZURE_ML_WHISPER_ENDPOINT, "azure", "ml"),
            (f"{RUNPOD_WHISPER_ENDPOINT}/transcribe", "runpod", "legacy")
        ]
    }

    for endpoint, provider, service_type in endpoints.get(model_type, []):
        if not endpoint:
            continue

        try:
            if provider == "aws" and service_type == "sagemaker":
                result = await proxy_to_aws_sagemaker(endpoint, request, model_type)
            elif provider == "azure" and service_type == "ml":
                result = await proxy_to_azure_ml(endpoint, request, model_type)
            elif provider == "runpod":
                result = await proxy_to_runpod(endpoint, request)
            else:
                continue

            # Add metadata about which provider was used
            result["_provider"] = provider
            result["_service"] = service_type
            return result

        except Exception as e:
            logger.warning(f"{provider.upper()} {service_type} failed for {model_type}: {e}")
            continue

    # All providers failed
    raise HTTPException(status_code=503, detail="All AI service providers temporarily unavailable")

@router.post("/sd")
async def stable_diffusion(request: Request):
    """Proxy to Stable Diffusion using multi-cloud AI (AWS Primary, Azure Secondary, RunPod Fallback)"""
    return await proxy_to_multi_cloud_ai(request, "sd")

@router.post("/yolo")
async def yolo_detection(request: Request):
    """Proxy to YOLO object detection using multi-cloud AI (AWS Primary, Azure Secondary, RunPod Fallback)"""
    return await proxy_to_multi_cloud_ai(request, "yolo")

@router.post("/whisper")
async def whisper_transcription(request: Request):
    """Proxy to Whisper STT using multi-cloud AI (AWS Primary, Azure Secondary, RunPod Fallback)"""
    return await proxy_to_multi_cloud_ai(request, "whisper")

@router.post("/start-simulation")
async def start_trading_simulation(days: int = 30):
    """Start AI-powered trading simulation (router placeholder)."""
    try:
        # Placeholder until full simulation service is ported; return an ack
        return {"status": "started", "days": days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.post("/simulate-day")
async def simulate_trading_day(symbols: List[str] = None):
    """Run one day of AI trading simulation (router placeholder)."""
    try:
        symbols = symbols or []
        return {"status": "simulated", "symbols": symbols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Day simulation failed: {str(e)}")

@router.get("/performance")
async def get_trading_performance():
    """Get trading simulation performance metrics (router placeholder)."""
    try:
        return {"status": "ok", "equity_curve": [], "note": "simulation service not yet ported"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance fetch failed: {str(e)}")

@router.get("/realtime-quote/{symbol}")
async def get_realtime_market_quote(symbol: str):
    """Get real-time market quote (placeholder)."""
    try:
        return {"symbol": symbol, "price": None, "note": "market data not yet ported"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quote fetch failed: {str(e)}")

@router.get("/historical/{symbol}")
async def get_historical_data(symbol: str, interval: str = "5min"):
    """Get historical market data (placeholder)."""
    try:
        return {"symbol": symbol, "interval": interval, "data": [], "note": "historical service not yet ported"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get historical data: {str(e)}")

@router.post("/analyze-chart")
async def analyze_chart(file: UploadFile = File(...), symbol: str = None):
    """Analyze chart image for technical patterns via vision router."""
    try:
        image_bytes = await file.read()
        async with AIRouter() as router:
            result = await router.analyze_image(image_bytes, symbol=symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart analysis failed: {str(e)}")

@router.post("/analyze-price-data")
async def analyze_price_data(price_data: Dict, symbol: str):
    """Analyze price data for technical indicators using signal router."""
    try:
        market_data = {"symbol": symbol, "price_data": price_data}
        async with AIRouter() as router:
            result = await router.generate_signal(market_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price analysis failed: {str(e)}")

@router.get("/crypto/quote/{symbol}")
async def get_crypto_quote(symbol: str):
    """Get real-time crypto quote from CoinSwitch"""
    if not AI_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Manager service temporarily unavailable")
    try:
        result = await ai_manager.get_crypto_quote(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto quote fetch failed: {str(e)}")

@router.get("/crypto/historical/{symbol}")
async def get_crypto_historical_data(symbol: str, interval: str = "5min"):
    """Get historical crypto market data"""
    if not AI_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Manager service temporarily unavailable")
    try:
        data = await ai_manager.get_crypto_historical_data(symbol, interval)
        if data is not None and not data.empty:
            return data.to_dict('records')
        return {"error": "No crypto data available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get crypto historical data: {str(e)}")

@router.get("/crypto/ticker/{symbol}")
async def get_crypto_ticker(symbol: str):
    """Get crypto ticker data from CoinSwitch"""
    if not AI_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Manager service temporarily unavailable")
    try:
        if 'crypto_market_data' not in ai_manager.services:
            raise HTTPException(status_code=503, detail="Crypto market data service not available")

        result = ai_manager.services['crypto_market_data'].get_ticker(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto ticker fetch failed: {str(e)}")

@router.get("/crypto/depth/{symbol}")
async def get_crypto_depth(symbol: str, limit: int = 50):
    """Get crypto order book depth from CoinSwitch"""
    if not AI_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Manager service temporarily unavailable")
    try:
        if 'crypto_market_data' not in ai_manager.services:
            raise HTTPException(status_code=503, detail="Crypto market data service not available")

        result = ai_manager.services['crypto_market_data'].get_depth(symbol, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto depth fetch failed: {str(e)}")

@router.get("/crypto/portfolio")
async def get_crypto_portfolio():
    """Get crypto portfolio from CoinSwitch"""
    if not AI_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Manager service temporarily unavailable")
    try:
        if 'crypto_market_data' not in ai_manager.services:
            raise HTTPException(status_code=503, detail="Crypto market data service not available")

        result = ai_manager.services['crypto_market_data'].get_portfolio()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto portfolio fetch failed: {str(e)}")

@router.get("/crypto/orders")
async def get_crypto_orders(symbol: Optional[str] = None):
    """Get crypto open orders from CoinSwitch"""
    if not AI_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Manager service temporarily unavailable")
    try:
        if 'crypto_market_data' not in ai_manager.services:
            raise HTTPException(status_code=503, detail="Crypto market data service not available")

        result = ai_manager.services['crypto_market_data'].get_open_orders(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto orders fetch failed: {str(e)}")

# AI Service Endpoints using AI Router
@router.post("/llm/chat")
async def llm_chat(request: Dict[str, Any]):
    """Chat with AI using multi-cloud router (Gemini/Perplexity/Azure/AWS)."""
    try:
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        async with AIRouter() as router:
            response = await router.ask_llm(message)

        # We don’t know the exact provider here without deeper tracing; reflect configured primary
        return {
            "response": response,
            "primary": CONFIG.PRIMARY_AI_SERVICE,
        }
    except Exception as e:
        logger.error(f"LLM chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI chat failed: {str(e)}")

@router.post("/llm/chat/ensemble")
async def llm_chat_ensemble(request: Dict[str, Any]):
    """Query multiple providers in parallel and synthesize a consensus response."""
    try:
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        async with AIRouter() as router:
            result = await router.ask_llm_ensemble(message, summarize=True)

        return result
    except Exception as e:
        logger.error(f"LLM ensemble chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI ensemble chat failed: {str(e)}")

@router.get("/health")
async def ai_health():
    """Report AI provider configuration and basic readiness."""
    try:
        providers = {
            "gemini": {
                "configured": bool(CONFIG.GEMINI_API_KEY),
                "model": CONFIG.GEMINI_MODEL,
            },
            "perplexity": {
                "configured": bool(CONFIG.PERPLEXITY_API_KEY or CONFIG.VERCEL_AI_GATEWAY_URL),
                "gateway": bool(CONFIG.VERCEL_AI_GATEWAY_URL),
                "model": getattr(CONFIG, "AI_GATEWAY_MODEL", ""),
            },
            "azure": {
                "configured": bool(CONFIG.AZURE_OPENAI_KEY and CONFIG.AZURE_OPENAI_ENDPOINT),
                "deployment": CONFIG.AZURE_OPENAI_DEPLOYMENT,
                "api_version": getattr(CONFIG, "AZURE_OPENAI_API_VERSION", ""),
            },
            "aws": {
                "configured": bool(CONFIG.AWS_ACCESS_KEY_ID and CONFIG.AWS_SECRET_ACCESS_KEY),
                "region": CONFIG.AWS_REGION,
                "model": CONFIG.AWS_BEDROCK_MODEL_ID,
            },
        }
        return {
            "status": "ok",
            "primary": CONFIG.PRIMARY_AI_SERVICE,
            "providers": providers,
        }
    except Exception as e:
        logger.error(f"AI health error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers/test")
async def ai_providers_test():
    """Attempt a tiny prompt against each configured provider and report status."""
    results = {}
    svc = LLMService()
    await svc.initialize()
    prompt = "Reply with OK."
    try:
        # Gemini
        if CONFIG.GEMINI_API_KEY:
            try:
                text = await svc.gemini_ask(prompt)
                results["gemini"] = {"ok": True, "len": len(text)}
            except Exception as e:
                results["gemini"] = {"ok": False, "error": str(e)}
        # Perplexity/Gateway
        if CONFIG.PERPLEXITY_API_KEY or CONFIG.VERCEL_AI_GATEWAY_URL:
            try:
                text = await svc.perplexity_ask(prompt)
                results["perplexity"] = {"ok": True, "len": len(text)}
            except Exception as e:
                results["perplexity"] = {"ok": False, "error": str(e)}
        # Azure
        if CONFIG.AZURE_OPENAI_KEY and CONFIG.AZURE_OPENAI_ENDPOINT:
            try:
                text = await svc.azure_ask(prompt)
                results["azure"] = {"ok": True, "len": len(text)}
            except Exception as e:
                results["azure"] = {"ok": False, "error": str(e)}
        # AWS
        if CONFIG.AWS_ACCESS_KEY_ID and CONFIG.AWS_SECRET_ACCESS_KEY:
            try:
                text = await svc.aws_ask(prompt)
                results["aws"] = {"ok": True, "len": len(text)}
            except Exception as e:
                results["aws"] = {"ok": False, "error": str(e)}
        return {"status": "done", "results": results}
    finally:
        await svc.close()

@router.post("/sentiment/analyze")
async def sentiment_analysis(request: Dict[str, Any]):
    """Analyze sentiment of text using AI Router."""
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        async with AIRouter() as router:
            result = await router.analyze_sentiment(text)

        return {
            "sentiment": result.get("sentiment", "neutral"),
            "confidence": result.get("confidence", 0.5),
            "text": text
        }
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

@router.post("/signal/generate")
async def signal_generation(request: Dict[str, Any]):
    """Generate trading signals using AI Router."""
    try:
        symbol = request.get("symbol", "")
        price_data = request.get("price_data", {})

        if not symbol or not price_data:
            raise HTTPException(status_code=400, detail="Symbol and price_data are required")

        market_data = {"symbol": symbol, "price_data": price_data}

        async with AIRouter() as router:
            result = await router.generate_signal(market_data)

        return {
            "signal": result.get("signal", "HOLD"),
            "score": result.get("score", 0.5),
            "symbol": symbol,
            "analysis": result.get("analysis", "")
        }
    except Exception as e:
        logger.error(f"Signal generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Signal generation failed: {str(e)}")

@router.post("/risk/assess")
async def risk_assessment(request: Dict[str, Any]):
    """Assess trading risk using AI Router."""
    try:
        symbol = request.get("symbol", "")
        action = request.get("action", "")
        quantity = request.get("quantity", 0)
        price = request.get("price", 0)

        if not all([symbol, action, quantity, price]):
            raise HTTPException(status_code=400, detail="Symbol, action, quantity, and price are required")

        trade_data = {
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": price
        }

        async with AIRouter() as router:
            result = await router.assess_risk(trade_data)

        return {
            "risk_score": result.get("risk_score", 0.5),
            "approved": result.get("approved", False),
            "reasoning": result.get("reasoning", ""),
            "symbol": symbol
        }
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")
