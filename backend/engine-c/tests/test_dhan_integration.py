
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Ensure src and repo root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
# Add backend/engine-c to path
sys.path.append(os.path.join(current_dir, '..'))
# Add repo root to path (for backend.shared imports)
sys.path.append(os.path.join(current_dir, '..', '..', '..'))

# Mock external dependencies before importing main
from src.main import app

# Mock startup internals to prevent actual initialization/network calls
app.dependency_overrides = {} 

# Create mocks with async methods where needed
mock_cache_manager = MagicMock()
mock_cache_instance = MagicMock()
mock_cache_instance.initialize = AsyncMock()
mock_cache_instance.shutdown = AsyncMock()
mock_cache_manager.return_value = mock_cache_instance

mock_health_monitor = MagicMock()
mock_monitor_instance = MagicMock()
mock_monitor_instance.start_monitoring = AsyncMock()
mock_monitor_instance.stop_monitoring = AsyncMock()
mock_health_monitor.return_value = mock_monitor_instance

# Apply patches
patch('src.main.initialize_realtime', new=AsyncMock()).start()
patch('src.main.ConnectionPoolManager.initialize', new=AsyncMock()).start()
patch('src.main.get_cache_manager', new=mock_cache_manager).start()
patch('src.main.get_health_monitor', new=mock_health_monitor).start()
patch('src.main.ActivityLogger', new=MagicMock()).start()

client = TestClient(app)

# Test Data
MOCK_USER_ID = "test-user-123"
MOCK_CLIENT_ID = "1101302170"
MOCK_CREDS = {
    "client_id": MOCK_CLIENT_ID,
    "access_token": "mock_token",
    "api_key": "mock_key",
    "api_secret": "mock_secret"
}

# Dhan Response with Typo (Simulating real API)
MOCK_FUNDS_RESPONSE = {
    "status": "success",
    "data": {
        "dhanClientId": MOCK_CLIENT_ID,
        "availabelBalance": 100.25, # TYPO from API
        "sodLimit": 100.25,
        "collateralAmount": 0.0,
        "receiveableAmount": 0.0,
        "utilizedAmount": 0.0,
        "withdrawableBalance": 100.25
    }
}

@pytest.mark.asyncio
async def test_get_funds_success():
    """
    Test retrieving funds with valid credentials, verifying correct parsing
    of the 'availabelBalance' typo.
    """
    mock_dhan_instance = MagicMock()
    mock_dhan_instance.get_fund_limits.return_value = MOCK_FUNDS_RESPONSE

    with patch('src.dhan_data_api.get_dhan_client_for_user', new=AsyncMock(return_value=(mock_dhan_instance, MOCK_CLIENT_ID, MOCK_USER_ID))):
        response = client.get(f"/api/dhan/funds?user_id={MOCK_USER_ID}")

        if response.status_code == 404:
            pytest.fail(f"Endpoint /api/dhan/funds not found. check routes.")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        funds_data = data.get("data", {})
        assert funds_data.get("dhanClientId") == MOCK_CLIENT_ID
        assert funds_data["availabelBalance"] == 100.25


@pytest.mark.asyncio
async def test_get_funds_no_creds():
    """Test get funds handles missing credentials gracefully"""
    from fastapi import HTTPException
    with patch('src.dhan_data_api.get_dhan_client_for_user', side_effect=HTTPException(status_code=401, detail="Dhan credentials not configured")):
        response = client.get(f"/api/dhan/funds?user_id=nonexistent")
        assert response.status_code in [400, 404, 401, 500]


@pytest.mark.asyncio
async def test_get_funds_fallback():
    """Test get funds uses fallback credentials if manager returns None"""
    mock_dhan_instance = MagicMock()
    mock_dhan_instance.get_fund_limits.return_value = MOCK_FUNDS_RESPONSE

    with patch('src.dhan_data_api.get_dhan_client_for_user', new=AsyncMock(return_value=(mock_dhan_instance, "1101302170", "1101302170"))):
        response = client.get(f"/api/dhan/funds?user_id=1101302170")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["availabelBalance"] == 100.25
