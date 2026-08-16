from pydantic import BaseModel
from typing import Dict, Any, Optional, List

# --- Signal Generation ---
class SignalRequest(BaseModel):
    symbol: str
    fast: bool = False
    news_headlines: Optional[List[str]] = None
    timeframe: str = "1d"

class SignalResponse(BaseModel):
    symbol: str
    signal: str
    confidence: float
    predicted_price: float
    current_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    timestamp: str
    model_version: str
    sentiment_score: Optional[float] = None
    data_source: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None
    security_id: Optional[str] = None
    exchange_segment: Optional[str] = None

class BatchSignalsRequest(BaseModel):
    symbols: List[str]
    user_id: Optional[str] = None
    fast: bool = True

class InstrumentSignalsRequest(BaseModel):
    instruments: List[str]
    min_confidence: float = 0.75
    strategy: Optional[str] = "ai-signals"
    max_signals: int = 10

# --- Model Training ---
class TrainingRequest(BaseModel):
    symbol: str
    historical_days: int = 365
    lookahead_days: int = 5
    n_estimators: int = 100
    max_depth: int = 6
    learning_rate: float = 0.1
    use_sentiment: bool = False

class TrainingResponse(BaseModel):
    status: str
    symbol: str
    historical_days: int
    samples_used: int
    features_count: int
    model_accuracies: Dict[str, float]
    training_time_seconds: float
    data_source: str
    timestamp: str

# --- Sentiment Analysis ---
class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float
    timestamp: str

# --- Position & Portfolio Analysis ---
class PositionAnalysisRequest(BaseModel):
    symbol: str
    trading_symbol: str
    security_id: str
    position_type: str
    exchange_segment: str
    product_type: str
    buy_avg: float
    cost_price: float
    buy_qty: int
    sell_qty: int = 0
    net_qty: int
    realized_profit: float = 0.0
    unrealized_profit: float = 0.0
    expiry_date: Optional[str] = None
    option_type: Optional[str] = None
    strike_price: Optional[float] = None
    current_price: Optional[float] = None

class PositionAnalysisResponse(BaseModel):
    symbol: str
    analysis: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    ai_recommendation: Dict[str, Any]
    market_context: Dict[str, Any]
    timestamp: str

# --- Options Analytics ---
class GreeksRequest(BaseModel):
    symbol: str
    spot: float
    strike: float
    expiry: str
    volatility: float = 0.18
    option_type: str = "CE"

class OptionsStrategyRequest(BaseModel):
    strategy_type: str
    symbol: str
    spot_price: float
    expiry: str
    parameters: Dict[str, Any]

# --- Deep Learning ---
class LSTMPredictRequest(BaseModel):
    symbol: str
    recent_data: List[Dict[str, Any]]

class DQNActionRequest(BaseModel):
    symbol: str
    current_state: List[float]

# --- Admin Training ---
class TrainingRequest(BaseModel):
    symbol: str = "NIFTY"
    days: int = 730
    upload_gcs: bool = True
    gcs_bucket: str = "project-841b7f97-5ee3-4fbe-920-models"
    gcs_prefix: str = "trained_models"


class LSTMTrainingRequest(TrainingRequest):
    epochs: int = 100
    batch_size: int = 32


class DQNTrainingRequest(TrainingRequest):
    episodes: int = 200

# --- AI/Gemini Integrations ---
class GeminiSignalRequest(BaseModel):
    symbol: str
    current_price: float
    historical_data: Optional[Dict[str, Any]] = None
    technical_indicators: Optional[Dict[str, float]] = None
    news_context: Optional[str] = None

class AgentAnalysisRequest(BaseModel):
    symbol: str
    market_data: Dict[str, Any]
    analysis_type: str = "comprehensive"

class EnhancedSignalRequest(BaseModel):
    symbol: str
    current_price: float
    technical_data: Optional[Dict[str, Any]] = None
    market_context: Optional[Dict[str, Any]] = None
    news_sentiment: Optional[str] = None
    portfolio_context: Optional[Dict[str, Any]] = None

class GeminiEnhancedSignalRequest(BaseModel):
    symbol: str
    analysis_type: str = "comprehensive"
    auto_execute: bool = False
    fetch_live_data: bool = True

class MarketDataRequest(BaseModel):
    symbol: str
    exchange: str = "NSE"
    data_type: str = "quote"

class GeminiChatRequest(BaseModel):
    question: str
    context: Optional[str] = None

class FinanceAIRequest(BaseModel):
    symbol: str
    current_price: float
    technical_indicators: Optional[Dict[str, Any]] = None
    news_items: Optional[List[str]] = None
    model_type: str = "stock_analyst"

class FinanceAIOptionsStrategyRequest(BaseModel):
    index: str = "NIFTY"
    spot_price: float
    outlook: str = "NEUTRAL"
    capital: float = 100000
    risk_appetite: str = "MODERATE"

class FinanceAIRiskAnalysisRequest(BaseModel):
    positions: List[Dict[str, Any]]
    account_value: float

class AgentConsultRequest(BaseModel):
    query: str
    symbol: Optional[str] = None
