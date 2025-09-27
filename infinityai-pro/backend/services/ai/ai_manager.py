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
            # Check disk space first
            import shutil
            total, used, free = shutil.disk_usage('/')
            free_gb = free / (1024**3)

            # Import and initialize services
            from .llm_service import LLMService
            from .stt_service import STTService
            from .vision_service import VisionService
            from .embedding_service import EmbeddingService
            from .huggingface_client import hf_client

            # Initialize LLM (Ollama - Hetzner) - lightweight
            try:
                self.services['llm'] = LLMService(self.config['ollama'])
                await self.services['llm'].initialize()
                logger.info("✅ LLM service initialized")
            except Exception as e:
                logger.warning(f"LLM service failed: {e}")

            # Initialize STT (RunPod GPU) - lightweight
            try:
                self.services['stt'] = STTService(self.config['whisper'])
                await self.services['stt'].initialize()
                logger.info("✅ STT service initialized")
            except Exception as e:
                logger.warning(f"STT service failed: {e}")

            # Initialize Vision (RunPod GPU) - check disk space
            if free_gb > 1.0:  # Need at least 1GB for vision models
                try:
                    self.services['vision'] = VisionService(self.config['yolo'], self.config['diffusers'])
                    await self.services['vision'].initialize()
                    logger.info("✅ Vision service initialized")
                except Exception as e:
                    logger.warning(f"Vision service failed: {e}")
            else:
                logger.warning(f"Skipping Vision service - insufficient disk space ({free_gb:.1f}GB free)")

            # Initialize Embeddings (SBERT + Vector DB) - check disk space
            if free_gb > 2.0:  # Need at least 2GB for embeddings
                try:
                    self.services['embeddings'] = EmbeddingService(self.config['sbert'], self.config['vector_db'])
                    await self.services['embeddings'].initialize()
                    logger.info("✅ Embeddings service initialized")
                except Exception as e:
                    logger.warning(f"Embeddings service failed: {e}")
            else:
                logger.warning(f"Skipping Embeddings service - insufficient disk space ({free_gb:.1f}GB free)")

            # Initialize Hugging Face fallback - always available
            self.services['huggingface'] = hf_client
            await self.services['huggingface'].initialize()
            logger.info("✅ HuggingFace fallback initialized")

            # Initialize Market Data AI (Alpha Vantage + CoinSwitch) - lightweight
            if self.config['alpha_vantage']['api_key']:
                try:
                    from ..market_data_ai import MarketDataAI
                    self.services['market_data'] = MarketDataAI(self.config['alpha_vantage']['api_key'])
                    await self.services['market_data'].initialize()
                    logger.info("✅ Market Data AI initialized")
                except Exception as e:
                    logger.warning(f"Market Data AI failed: {e}")

            # Initialize CoinSwitch Crypto Market Data - lightweight
            if self.config.get('coinswitch', {}).get('enabled', False):
                try:
                    from ..broker_coinswitch import CoinSwitchAdapter
                    coinswitch_config = self.config.get('coinswitch', {})
                    if coinswitch_config.get('api_key') and coinswitch_config.get('api_secret'):
                        self.services['crypto_market_data'] = CoinSwitchAdapter(
                            api_key=coinswitch_config['api_key'],
                            api_secret=coinswitch_config['api_secret'],
                            base_url=coinswitch_config.get('base_url', 'https://api-trading.coinswitch.co')
                        )
                        logger.info("✅ CoinSwitch crypto market data initialized")
                except Exception as e:
                    logger.warning(f"CoinSwitch initialization failed: {e}")

            # Initialize Technical Analysis AI - lightweight
            try:
                from ..ai_models import TechnicalAnalysisAI
                self.services['technical_analysis'] = TechnicalAnalysisAI()
                await self.services['technical_analysis'].initialize()
                logger.info("✅ Technical Analysis AI initialized")
            except Exception as e:
                logger.warning(f"Technical Analysis AI failed: {e}")

            # Initialize AI Trading Simulator - lightweight
            try:
                from ..ai_trading_simulator import AITradingSimulator
                self.services['trading_simulator'] = AITradingSimulator()
                await self.services['trading_simulator'].initialize()
                logger.info("✅ AI Trading Simulator initialized")
            except Exception as e:
                logger.warning(f"AI Trading Simulator failed: {e}")

            self.initialized = True
            logger.info("✅ AI services initialization completed!")

        except Exception as e:
            logger.error(f"Failed to initialize AI services: {e}")
            # Don't raise exception - allow partial initialization
            self.initialized = True

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

    async def get_crypto_quote(self, symbol: str) -> Dict:
        """Get real-time crypto quote from CoinSwitch"""
        if 'crypto_market_data' not in self.services:
            raise RuntimeError("Crypto market data service not initialized")

        return await self.services['crypto_market_data'].get_quote_async(symbol)

    async def get_historical_data(self, symbol: str, interval: str = "5min") -> pd.DataFrame:
        """Get historical market data (supports both traditional and crypto)"""
        # Check if this is a crypto symbol
        is_crypto = symbol in self.config.get('coinswitch', {}).get('crypto_symbols', []) or symbol.endswith('INR')

        if is_crypto and 'crypto_market_data' in self.services:
            return await self.get_crypto_historical_data(symbol, interval)
        elif 'market_data' in self.services:
            return await self.services['market_data'].get_intraday_data(symbol, interval)
        else:
            raise RuntimeError("No market data service available for symbol type")
        """Get historical crypto data"""
        try:
            # For now, return simulated data since CoinSwitch may not have extensive historical data
            # In production, you might want to use additional data sources
            logger.warning(f"Crypto historical data for {symbol} - using simulated data")
            return await self._generate_crypto_historical_data(symbol, interval)
        except Exception as e:
            logger.error(f"Error getting crypto historical data: {e}")
            return pd.DataFrame()

    async def _generate_crypto_historical_data(self, symbol: str, interval: str = "5min", periods: int = 200) -> pd.DataFrame:
        """Generate realistic crypto historical data for backtesting"""
        try:
            # Get current price from CoinSwitch
            current_quote = await self.get_crypto_quote(symbol)
            base_price = current_quote.get('last_price', 100000)  # Default fallback

            # Generate price series with crypto volatility
            np.random.seed(hash(symbol) % 2**32)
            returns = np.random.normal(0.0002, 0.01, periods)  # Higher volatility for crypto
            prices = base_price * np.exp(np.cumsum(returns))

            # Create timestamps
            now = pd.Timestamp.now()
            if interval == "5min":
                timestamps = [now - pd.Timedelta(minutes=5*i) for i in range(periods)][::-1]
            else:
                # Default to 5min intervals
                timestamps = [now - pd.Timedelta(minutes=5*i) for i in range(periods)][::-1]

            # Create OHLCV data
            high_mult = 1 + np.abs(np.random.normal(0, 0.005, periods))
            low_mult = 1 - np.abs(np.random.normal(0, 0.005, periods))

            candles = []
            for i, (timestamp, price) in enumerate(zip(timestamps, prices)):
                high = price * high_mult[i]
                low = price * low_mult[i]
                open_price = price * (1 + np.random.normal(0, 0.002))
                close = price
                volume = np.random.randint(100, 10000)  # Crypto volumes

                candles.append({
                    "datetime": timestamp,
                    "open": open_price,
                    "high": max(open_price, high),
                    "low": min(open_price, low),
                    "close": close,
                    "volume": volume
                })

            df = pd.DataFrame(candles)
            df.set_index("datetime", inplace=True)

            # Add technical indicators
            df = featurize(df.reset_index())
            df.set_index("datetime", inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error generating crypto historical data: {e}")
            return pd.DataFrame()

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