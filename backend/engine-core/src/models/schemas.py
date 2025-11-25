from pydantic import BaseModel
from typing import List, Dict

class PredictionResponse(BaseModel):
    symbol: str
    predicted_price: float
    confidence: float
    signal_type: str
    expected_return: float
    risk_score: float
    time_horizon: str
    model_version: str
    components: Dict[str, float]
    features_used: List[str]
    timestamp: str

class ModelStatus(BaseModel):
    name: str
    type: str
    trained: bool
    last_trained: str | None
    samples_seen: int
    metrics: Dict[str, float]
