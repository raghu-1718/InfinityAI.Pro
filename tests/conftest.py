import os
import sys
import pytest
from pathlib import Path

# Ensure project root and backend are on PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
ML_DIR = PROJECT_ROOT / "ml"
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

# Backward-compatible alias for ml_models -> ml.models
try:
    import ml.models as _ml_models
    sys.modules["ml_models"] = _ml_models
    import ml.models.feature_engineering
    sys.modules["ml_models.feature_engineering"] = ml.models.feature_engineering
    import ml.models.training_pipeline
    sys.modules["ml_models.training_pipeline"] = ml.models.training_pipeline
    import ml.models.evaluate_oos_backtest
    sys.modules["ml_models.evaluate_oos_backtest"] = ml.models.evaluate_oos_backtest
except Exception:
    pass

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["TRADING_MODE"] = "paper"
os.environ["GOOGLE_CLOUD_PROJECT"] = "project-841b7f97-5ee3-4fbe-920"
os.environ["GOOGLE_CLOUD_REGION"] = "asia-south1"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["USER_CREDENTIALS_KEY"] = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

from starlette.testclient import TestClient

@pytest.fixture(scope="session")
def client():
    """Session-scoped FastAPI TestClient."""
    from backend.src.main import app
    with TestClient(app) as c:
        yield c
