# services/ai/__init__.py
"""
InfinityAI.Pro - AI Services Package
Comprehensive AI stack: LLM, STT, Vision, Embeddings
"""

from .ai_manager import AIManager
from .llm_service import LLMService
from .stt_service import STTService
from .vision_service import VisionService
from .embedding_service import EmbeddingService

# Create global AI manager instance
ai_manager = AIManager()

__all__ = [
    'ai_manager',
    'AIManager',
    'LLMService',
    'STTService',
    'VisionService',
    'EmbeddingService'
]