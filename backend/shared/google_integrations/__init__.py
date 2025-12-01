# =====================================================================
# InfinityAI.Pro - Google Cloud Integrations
# =====================================================================
# This package provides unified Google Cloud service integrations:
# - GenAI SDK for Gemini model access with Vertex AI
# - Enhanced GenAI with function calling for real-time data
# - Market Data Tools for live stock data
# - News Integration for sentiment analysis
# - Cloud Logging for structured trade signal logging
# - Cloud Storage for ML model and trading history persistence
# - ADK-inspired agent architecture for trading signals
# =====================================================================

from .genai_client import GenAIClient, TradingAnalysisAgent, TradingPrompt, TradingAnalysis
from .cloud_logging import TradingLogger, LogLevel, TradingEventType
from .cloud_storage import ModelStorage, TradingHistoryStorage
from .trading_agents import (
    TradingSignalAgent,
    RiskAssessmentAgent,
    MarketAnalysisAgent,
    AgentOrchestrator,
    AgentContext,
    AgentResult,
    create_trading_workflow
)

# Enhanced GenAI with function calling
try:
    from .enhanced_genai_client import (
        EnhancedGenAIClient,
        TradingRecommendation,
        TradingSignal,
        RiskLevel,
        Timeframe,
        get_quick_signal,
        get_market_overview,
        analyze_stock,
        INFINITYAI_SYSTEM_PROMPT
    )
    HAS_ENHANCED_GENAI = True
except ImportError:
    HAS_ENHANCED_GENAI = False

# Market Data Tools
try:
    from .market_data_tools import (
        MARKET_DATA_TOOLS,
        get_stock_quote,
        get_nifty_overview,
        get_technical_indicators,
        get_market_news,
        get_option_chain_data,
        get_fii_dii_activity,
        get_economic_calendar,
        execute_paper_trade
    )
    HAS_MARKET_TOOLS = True
except ImportError:
    HAS_MARKET_TOOLS = False

# News Integration
try:
    from .news_integration import (
        NewsAggregator,
        NewsArticle,
        NewsFeed,
        get_market_news_live,
        get_symbol_news_live
    )
    HAS_NEWS = True
except ImportError:
    HAS_NEWS = False

__all__ = [
    # GenAI
    "GenAIClient",
    "TradingAnalysisAgent",
    "TradingPrompt",
    "TradingAnalysis",
    # Enhanced GenAI
    "EnhancedGenAIClient",
    "TradingRecommendation",
    "TradingSignal",
    "RiskLevel",
    "Timeframe",
    "get_quick_signal",
    "get_market_overview",
    "analyze_stock",
    "INFINITYAI_SYSTEM_PROMPT",
    "HAS_ENHANCED_GENAI",
    # Market Data Tools
    "MARKET_DATA_TOOLS",
    "get_stock_quote",
    "get_nifty_overview",
    "get_technical_indicators",
    "get_market_news",
    "get_option_chain_data",
    "get_fii_dii_activity",
    "get_economic_calendar",
    "execute_paper_trade",
    "HAS_MARKET_TOOLS",
    # News Integration
    "NewsAggregator",
    "NewsArticle",
    "NewsFeed",
    "get_market_news_live",
    "get_symbol_news_live",
    "HAS_NEWS",
    # Logging
    "TradingLogger",
    "LogLevel",
    "TradingEventType",
    # Storage
    "ModelStorage",
    "TradingHistoryStorage",
    # Agents
    "TradingSignalAgent",
    "RiskAssessmentAgent",
    "MarketAnalysisAgent",
    "AgentOrchestrator",
    "AgentContext",
    "AgentResult",
    "create_trading_workflow",
]
