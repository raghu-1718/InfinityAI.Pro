import os
import httpx
from typing import Dict, Any
from ..core.utils import setup_logger

log = setup_logger("AISignal")

# Engine B URL for real ML signal validation
ENGINE_B_URL = os.environ.get(
    "ENGINE_B_URL",
    "http://engine-b-ml-prod.asia-south1-a.c.project-841b7f97-5ee3-4fbe-920.internal:8080",
)


class AISignalModel:
    """
    Real ML Signal Validation Model.
    Calls Engine B's ML ensemble for actual confidence scoring.
    NO random values - uses real trained models (RandomForest, XGBoost, LightGBM).
    """

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        self._fallback_confidence = 0.5  # Conservative fallback if API fails

    def validate_signal(self, order: Dict[str, Any]) -> float:
        """
        Validate trading signal using Engine B's real ML models.
        Returns confidence score from 0.0 to 1.0.
        """
        try:
            # Extract symbol from order
            symbol = order.get("symbol", order.get("tradingSymbol", "NIFTY"))

            # Call Engine B's real ML signal endpoint
            response = self.client.post(
                f"{ENGINE_B_URL}/api/v1/signal",
                json={
                    "symbol": symbol,
                    "include_features": True
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                confidence = data.get("confidence", data.get("ensemble_confidence", 0.5))
                signal = data.get("signal", "NEUTRAL")

                log.info(f"✅ ML Signal Validated - Symbol: {symbol}, Signal: {signal}, Confidence: {confidence:.2f}")
                return float(confidence)
            else:
                log.warning(f"⚠️ Engine B returned status {response.status_code}, using conservative confidence")
                return self._fallback_confidence

        except httpx.TimeoutException:
            log.warning("⚠️ Engine B timeout - using conservative fallback confidence")
            return self._fallback_confidence
        except Exception as e:
            log.error(f"❌ ML Signal validation error: {e}")
            return self._fallback_confidence

    def get_full_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get full ML analysis including all model predictions."""
        try:
            response = self.client.post(
                f"{ENGINE_B_URL}/api/v1/signal",
                json={"symbol": symbol, "include_features": True}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            log.error(f"Full analysis error: {e}")

        return {"symbol": symbol, "confidence": self._fallback_confidence, "signal": "NEUTRAL"}
