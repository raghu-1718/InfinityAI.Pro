"""
Abstract Base Adapter for Market Data Ingestion
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List

class BaseMarketDataAdapter(ABC):
    @abstractmethod
    def load_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Returns standard OHLCV dataframe with DatetimeIndex in IST"""
        pass
