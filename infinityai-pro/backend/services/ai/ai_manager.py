# services/ai/ai_manager.py
"""
InfinityAI.Pro - Comprehensive AI Manager
Coordinates all AI services: LLM, STT, Vision, Embeddings, Vector Search
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class AIManager:
    """
    Central coordinator for all AI services in InfinityAI.Pro
    Provides unified interface for LLM, STT, Vision, and Embeddings
    """

    def __init__(self):
        self.services = {}
        self.initialized = False
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load AI configuration"""
        return {
            "ollama": {
                "url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
                "model": os.getenv("OLLAMA_MODEL", "llama3.2:latest"),
                "timeout": 60
            },
            "whisper": {
                "model": os.getenv("WHISPER_MODEL", "base"),
                "language": os.getenv("WHISPER_LANGUAGE", "en")
            },
            "diffusers": {
                "model": os.getenv("DIFFUSERS_MODEL", "stabilityai/stable-diffusion-2-1-base"),
                "device": "cpu"  # Force CPU to save space
            },
            "yolo": {
                "model": os.getenv("YOLO_MODEL", "yolov8n.pt"),
                "conf_threshold": 0.5
            },
            "sbert": {
                "model": os.getenv("SBERT_MODEL", "all-MiniLM-L6-v2")
            },
            "vector_db": {
                "type": os.getenv("VECTOR_DB", "chromadb"),  # weaviate, chromadb, faiss
                "url": os.getenv("VECTOR_DB_URL", "http://localhost:8000"),
                "collection": "infinity_ai_docs"
            },
            "runpod": {
                "sd_endpoint": os.getenv("RUNPOD_SD_ENDPOINT", ""),
                "yolo_endpoint": os.getenv("RUNPOD_YOLO_ENDPOINT", ""),
                "whisper_endpoint": os.getenv("RUNPOD_WHISPER_ENDPOINT", ""),
                "api_key": os.getenv("RUNPOD_API_KEY", "")
            },
            "huggingface": {
                "token": os.getenv("HF_TOKEN", ""),
                "fallback_enabled": True
            },
            "alpha_vantage": {
                "api_key": os.getenv("ALPHA_VANTAGE_API_KEY", "")
            }
        }

    def _has_cuda(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False

    async def initialize(self):
        """Initialize all AI services"""
        if self.initialized:
            return

        logger.info("Initializing InfinityAI.Pro Hybrid AI Stack...")

        try:
            # Import and initialize services
            from .llm_service import LLMService
            from .stt_service import STTService
            from .vision_service import VisionService
            from .embedding_service import EmbeddingService
            from .huggingface_client import hf_client

            # Initialize LLM (Ollama - Hetzner)
            self.services['llm'] = LLMService(self.config['ollama'])
            await self.services['llm'].initialize()

            # Initialize STT (RunPod GPU)
            self.services['stt'] = STTService(self.config['whisper'])
            await self.services['stt'].initialize()

            # Initialize Vision (RunPod GPU)
            self.services['vision'] = VisionService(self.config['yolo'], self.config['diffusers'])
            await self.services['vision'].initialize()

            # Initialize Embeddings (SBERT + Vector DB - Hetzner)
            self.services['embeddings'] = EmbeddingService(self.config['sbert'], self.config['vector_db'])
            await self.services['embeddings'].initialize()

            # Initialize Hugging Face fallback
            self.services['huggingface'] = hf_client

            # Initialize Market Data AI (Alpha Vantage)
            if self.config['alpha_vantage']['api_key']:
                from ..market_data_ai import MarketDataAI
                self.services['market_data'] = MarketDataAI(self.config['alpha_vantage']['api_key'])
                await self.services['market_data'].initialize()

            # Initialize Technical Analysis AI
            from ..ai_models import TechnicalAnalysisAI
            self.services['technical_analysis'] = TechnicalAnalysisAI()
            await self.services['technical_analysis'].initialize()

            # Initialize AI Trading Simulator
            from ..ai_trading_simulator import AITradingSimulator
            self.services['trading_simulator'] = AITradingSimulator()
            await self.services['trading_simulator'].initialize()

            self.initialized = True
            logger.info("✅ All AI services initialized successfully!")

        except Exception as e:
            logger.error(f"Failed to initialize AI services: {e}")
            raise

    async def close(self):
        """Close all AI services"""
        for service_name, service in self.services.items():
            try:
                await service.close()
            except Exception as e:
                logger.error(f"Error closing {service_name}: {e}")

    # LLM Methods
    async def chat(self, message: str, context: Optional[Dict] = None) -> Dict:
        """Generate chat response using local LLM"""
        if 'llm' not in self.services:
            raise RuntimeError("LLM service not initialized")

        return await self.services['llm'].chat(message, context)

    async def generate_strategy(self, signal_data: Dict, market_context: Dict = None) -> Dict:
        """Generate trading strategy using LLM"""
        if 'llm' not in self.services:
            raise RuntimeError("LLM service not initialized")

        return await self.services['llm'].generate_trading_strategy(signal_data, market_context)

    # STT Methods
    async def speech_to_text(self, audio_data: bytes, filename: str = None) -> Dict:
        """Convert speech to text"""
        if 'stt' not in self.services:
            raise RuntimeError("STT service not initialized")

        return await self.services['stt'].transcribe(audio_data, filename)

    # Vision Methods
    async def detect_objects(self, image_data: bytes, filename: str = None) -> Dict:
        """Detect objects in image using YOLO"""
        if 'vision' not in self.services:
            raise RuntimeError("Vision service not initialized")

        return await self.services['vision'].detect_objects(image_data, filename)

    async def generate_image(self, prompt: str, **kwargs) -> Dict:
        """Generate image from text prompt"""
        if 'vision' not in self.services:
            raise RuntimeError("Vision service not initialized")

        return await self.services['vision'].generate_image(prompt, **kwargs)

    # Embedding Methods
    async def embed_text(self, text: str, metadata: Dict = None) -> Dict:
        """Generate embeddings for text"""
        if 'embeddings' not in self.services:
            raise RuntimeError("Embeddings service not initialized")

        return await self.services['embeddings'].embed_text(text, metadata)

    async def search_similar(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar content using embeddings"""
        if 'embeddings' not in self.services:
            raise RuntimeError("Embeddings service not initialized")

        return await self.services['embeddings'].search_similar(query, limit)

    # Trading Intelligence Methods
    async def analyze_market_sentiment(self, symbol: str, news_data: List[Dict] = None) -> Dict:
        """Analyze market sentiment using LLM and embeddings"""
        try:
            # Combine LLM analysis with embedding search
            sentiment_prompt = f"Analyze the current market sentiment for {symbol}. Provide a sentiment score (-1 to 1) and key insights."

            if news_data:
                sentiment_prompt += f"\n\nRecent news: {json.dumps(news_data[:5], indent=2)}"

            llm_response = await self.chat(sentiment_prompt)

            # Search for similar market analysis
            similar_analysis = await self.search_similar(f"market sentiment {symbol}", limit=3)

            return {
                "symbol": symbol,
                "sentiment_analysis": llm_response,
                "similar_analysis": similar_analysis,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing market sentiment: {e}")
            return {"error": str(e)}

    async def generate_trade_narration(self, trade_data: Dict) -> Dict:
        """Generate AI narration for trade decisions"""
        try:
            prompt = f"""
            Narrate this trading decision in a clear, professional manner:

            Trade Details:
            {json.dumps(trade_data, indent=2)}

            Provide:
            1. Clear explanation of the trade rationale
            2. Risk assessment
            3. Expected outcome
            4. Key monitoring points
            """

            narration = await self.chat(prompt)

            return {
                "trade_data": trade_data,
                "narration": narration,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating trade narration: {e}")
            return {"error": str(e)}

    # Market Data Methods
    async def get_market_quote(self, symbol: str, exchange: str = "NSE") -> Dict:
        """Get real-time market quote"""
        if 'market_data' not in self.services:
            raise RuntimeError("Market Data AI service not initialized")

        return await self.services['market_data'].get_quote(symbol, exchange)

    async def get_historical_data(self, symbol: str, interval: str = "5min") -> pd.DataFrame:
        """Get historical market data"""
        if 'market_data' not in self.services:
            raise RuntimeError("Market Data AI service not initialized")

        return await self.services['market_data'].get_intraday_data(symbol, interval)

    # Technical Analysis Methods
    async def analyze_chart_patterns(self, chart_image: bytes, symbol: str = None) -> Dict:
        """Analyze chart for technical patterns"""
        if 'technical_analysis' not in self.services:
            raise RuntimeError("Technical Analysis AI service not initialized")

        return await self.services['technical_analysis'].analyze_chart(chart_image, symbol)

    async def start_trading_simulation(self, days: int = 30) -> Dict:
        """Start AI-powered trading simulation"""
        if 'trading_simulator' not in self.services:
            raise RuntimeError("Trading Simulator AI service not initialized")

        return await self.services['trading_simulator'].run_continuous_simulation(days)

    async def simulate_trading_day(self, symbols: List[str] = None) -> Dict:
        """Run one day of AI trading simulation"""
        if 'trading_simulator' not in self.services:
            raise RuntimeError("Trading Simulator AI service not initialized")

        return await self.services['trading_simulator'].simulate_trading_day(symbols)

    async def get_trading_performance(self) -> Dict:
        """Get trading simulation performance metrics"""
        if 'trading_simulator' not in self.services:
            raise RuntimeError("Trading Simulator AI service not initialized")

        return self.services['trading_simulator'].get_performance_summary()

    async def get_realtime_quote(self, symbol: str) -> Dict:
        """Get real-time market quote"""
        if 'trading_simulator' not in self.services:
            raise RuntimeError("Trading Simulator AI service not initialized")

        return await self.services['trading_simulator'].get_realtime_quote(symbol)

    # Health Check
    async def health_check(self) -> Dict:
        """Check health of all AI services"""
        health_status = {
            "overall": "healthy",
            "services": {},
            "timestamp": datetime.now().isoformat()
        }

        for service_name, service in self.services.items():
            try:
                health = await service.health_check()
                health_status["services"][service_name] = health
                if health.get("status") != "healthy":
                    health_status["overall"] = "degraded"
            except Exception as e:
                health_status["services"][service_name] = {"status": "error", "error": str(e)}
                health_status["overall"] = "unhealthy"

        return health_status

# Note: Global AI manager instance is created in __init__.py