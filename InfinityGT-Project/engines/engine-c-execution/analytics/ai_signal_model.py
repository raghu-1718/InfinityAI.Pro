import random
from ..core.utils import setup_logger
log = setup_logger("AISignal")

class AISignalModel:
    def validate_signal(self, order):
        confidence = random.uniform(0.5, 1.0)
        log.info(f"Signal Confidence: {confidence:.2f}")
        return confidence
