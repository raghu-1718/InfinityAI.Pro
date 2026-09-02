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
