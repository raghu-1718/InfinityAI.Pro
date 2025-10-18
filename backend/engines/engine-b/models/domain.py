from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

@dataclass
class AISignal:
    symbol: str
    predicted_price: float
    confidence: float
    signal_type: str
    expected_return: float
    risk_score: float
    time_horizon: str
    model_version: str
    features_used: List[str]
    components: Dict[str, float]
    timestamp: datetime
