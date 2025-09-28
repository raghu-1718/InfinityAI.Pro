"""
AI Failover Router Service
Handles multi-cloud AI provider failover: RunPod → Azure → AWS
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import aiohttp
from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class AIRouter:
    """
    Multi-cloud AI router with automatic failover
    Priority: Azure (primary) → AWS (secondary)
    """

    def __init__(self):
        self.config = Config()
        self.providers = ["azure", "aws"]  # Removed RunPod
        self.timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
        self.session = None
        self.health_cache = {}  # Cache provider health status
        self.cache_ttl = timedelta(minutes=5)  # Health cache TTL

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _check_provider_health(self, provider: str) -> bool:
        """Check if a provider is healthy"""
        cache_key = f"{provider}_health"
        now = datetime.now()

        # Check cache first
        if cache_key in self.health_cache:
            cached_time, is_healthy = self.health_cache[cache_key]
            if now - cached_time < self.cache_ttl:
                return is_healthy

        # Perform health check
        try:
            if provider == "azure":
                # Check Azure health via OpenAI endpoint
                async with self.session.get(f"{self.config.AZURE_OPENAI_ENDPOINT}/openai/models?api-version=2023-05-15",
                                          headers={"api-key": self.config.AZURE_OPENAI_KEY}) as resp:
                    is_healthy = resp.status == 200
            elif provider == "aws":
                # Check AWS health via Bedrock
                import boto3
                bedrock = boto3.client(
                    'bedrock',
                    region_name=self.config.AWS_REGION,
                    aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY
                )
                # Simple health check - list models
                response = bedrock.list_foundation_models()
                is_healthy = bool(response.get('modelSummaries'))
            else:
                is_healthy = False

            # Cache result
            self.health_cache[cache_key] = (now, is_healthy)
            return is_healthy

        except Exception as e:
            logger.warning(f"Health check failed for {provider}: {e}")
            self.health_cache[cache_key] = (now, False)
            return False

    async def _route_request(self, service_type: str, method: str, **kwargs) -> Any:
        """
        Route request through providers with failover
        service_type: 'llm', 'speech', 'vision', 'diffusion'
        method: method name to call
        """
        errors = []

        for provider in self.providers:
            try:
                # Check provider health first
                if not await self._check_provider_health(provider):
                    logger.info(f"Skipping unhealthy provider: {provider}")
                    continue

                # Import the appropriate service module
                if service_type == "llm":
                    from .llm_service import LLMService
                    service = LLMService()
                elif service_type == "speech":
                    from .speech_service import SpeechService
                    service = SpeechService()
                elif service_type == "vision":
                    from .vision_service import VisionService
                    service = VisionService()
                elif service_type == "diffusion":
                    from .diffusion_service import DiffusionService
                    service = DiffusionService()
                elif service_type == "sentiment":
                    from .sentiment_service import SentimentService
                    service = SentimentService()
                elif service_type == "risk":
                    from .risk_service import RiskService
                    service = RiskService()
                elif service_type == "signal":
                    from .signal_service import SignalService
                    service = SignalService()
                else:
                    raise ValueError(f"Unknown service type: {service_type}")

                # Call the method on the service - try Azure first, then AWS
                method_func = getattr(service, f"azure_{method}")
                result = await method_func(**kwargs)

                logger.info(f"Successfully routed {service_type}.{method} via {provider}")
                return result

            except Exception as e:
                error_msg = f"[{provider.upper()}] {service_type}.{method} failed: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue

        # All providers failed
        final_error = f"All AI providers failed for {service_type}.{method}. Errors: {'; '.join(errors)}"
        logger.error(final_error)
        raise Exception(final_error)

    # LLM Methods
    async def ask_llm(self, prompt: str, **kwargs) -> str:
        """Route LLM request with failover"""
        return await self._route_request("llm", "ask", prompt=prompt, **kwargs)

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Route text generation with failover"""
        return await self._route_request("llm", "generate", prompt=prompt, **kwargs)

    # Speech Methods
    async def transcribe_audio(self, audio_data: bytes, **kwargs) -> str:
        """Route speech-to-text with failover"""
        return await self._route_request("speech", "transcribe", audio_data=audio_data, **kwargs)

    async def synthesize_speech(self, text: str, **kwargs) -> bytes:
        """Route text-to-speech with failover"""
        return await self._route_request("speech", "synthesize", text=text, **kwargs)

    # Vision Methods
    async def analyze_image(self, image_data: bytes, **kwargs) -> Dict[str, Any]:
        """Route image analysis with failover"""
        return await self._route_request("vision", "analyze", image_data=image_data, **kwargs)

    async def detect_objects(self, image_data: bytes, **kwargs) -> List[Dict[str, Any]]:
        """Route object detection with failover"""
        return await self._route_request("vision", "detect", image_data=image_data, **kwargs)

    # Sentiment Methods
    async def analyze_sentiment(self, text: str, **kwargs) -> Dict[str, Any]:
        """Route sentiment analysis with failover"""
        return await self._route_request("sentiment", "analyze", text=text, **kwargs)

    async def get_market_sentiment(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Route market sentiment analysis with failover"""
        return await self._route_request("sentiment", "market", symbol=symbol, **kwargs)

    # Risk Methods
    async def assess_risk(self, trade_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Route risk assessment with failover"""
        return await self._route_request("risk", "assess", trade_data=trade_data, **kwargs)

    async def check_compliance(self, trade_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Route compliance check with failover"""
        return await self._route_request("risk", "compliance", trade_data=trade_data, **kwargs)

    # Signal Methods
    async def generate_signal(self, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Route signal generation with failover"""
        return await self._route_request("signal", "generate", market_data=market_data, **kwargs)

    async def suggest_order(self, signal: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Route order suggestion with failover"""
        return await self._route_request("signal", "suggest", signal=signal, **kwargs)

    # Execution Methods
    async def execute_order(self, order_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Route order execution"""
        # Execution doesn't use failover - uses configured broker
        try:
            from .execution_service import ExecutionService
            execution = ExecutionService()
            await execution.initialize()
            result = await execution.execute_order(order_data, **kwargs)
            await execution.close()
            return result
        except Exception as e:
            logger.error(f"Execution routing error: {e}")
            raise

    async def get_portfolio(self, **kwargs) -> Dict[str, Any]:
        """Route portfolio fetch"""
        try:
            from .execution_service import ExecutionService
            execution = ExecutionService()
            await execution.initialize()
            result = await execution.get_portfolio(**kwargs)
            await execution.close()
            return result
        except Exception as e:
            logger.error(f"Portfolio routing error: {e}")
            raise