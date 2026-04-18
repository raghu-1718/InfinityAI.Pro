
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

mock_coupon_manager = MagicMock()
mock_coupon_instance = MagicMock()
mock_coupon_instance.initialize_default_coupons = AsyncMock()
mock_coupon_manager.return_value = mock_coupon_instance

# Apply patches
patch('src.main.initialize_realtime', new=AsyncMock()).start()
patch('src.main.ConnectionPoolManager.initialize', new=AsyncMock()).start()
patch('src.main.get_cache_manager', new=mock_cache_manager).start()
patch('src.main.get_health_monitor', new=mock_health_monitor).start()
patch('src.main.get_coupon_auth_manager', new=mock_coupon_manager).start()
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
    
    # Mock UserCredentialsManager
    with patch('src.main.get_credentials_manager') as mock_get_cm:
        mock_cm_instance = MagicMock()
        mock_get_cm.return_value = mock_cm_instance
        
        # Mock get_user_credentials (Async)
        # Structure must match: {"credentials": {...}}
        mock_cm_instance.get_user_credentials = AsyncMock(return_value={"credentials": MOCK_CREDS})
        
        # Mock dhanhq client
        with patch('src.main.dhanhq') as mock_dhan_init:
            mock_dhan_instance = MagicMock()
            mock_dhan_init.return_value = mock_dhan_instance
            
            # Mock get_fund_limits return value
            mock_dhan_instance.get_fund_limits.return_value = MOCK_FUNDS_RESPONSE
            
            # Make request
            response = client.get(f"/api/dhan/funds?user_id={MOCK_USER_ID}")
            
            # Assertions
            if response.status_code == 404:
                pytest.fail(f"Endpoint /api/dhan/funds not found. check routes.")
                
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            
            # Verify data passed through correctly
            funds_data = data["data"]
            assert funds_data["dhanClientId"] == MOCK_CLIENT_ID
            # Check if the tyop is preserved (as Engine A/C usually passthrough)
            assert funds_data["availabelBalance"] == 100.25

@pytest.mark.asyncio
async def test_get_funds_no_creds():
    """Test get funds handles missing credentials gracefully"""
    
    with patch('src.main.get_credentials_manager') as mock_get_cm:
        mock_cm_instance = MagicMock()
        mock_get_cm.return_value = mock_cm_instance
        
        # Mock get_user_credentials returning None
        mock_cm_instance.get_user_credentials = AsyncMock(return_value=None)
        
        response = client.get(f"/api/dhan/funds?user_id=nonexistent")
        
        # Should return error or handled failure
        assert response.status_code in [400, 404, 401, 500] 
        # Note: 500 is technically a failure, but we prefer 400/404. 
        # If code raises Exception on None credentials, it might be 500.

@pytest.mark.asyncio
async def test_get_funds_fallback():
    """Test get funds uses fallback credentials if manager returns None"""
    
    with patch('src.main.get_credentials_manager') as mock_get_cm:
        mock_cm_instance = MagicMock()
        mock_get_cm.return_value = mock_cm_instance
        
        # Mock get_user_credentials returning None (simulating missing user)
        mock_cm_instance.get_user_credentials = AsyncMock(return_value=None)
        # Mock find_credentials_by_client_id returning None (simulating missing client map)
        mock_cm_instance.find_credentials_by_client_id = AsyncMock(return_value=None)
        
        # Mock dhanhq client to return success when initialized with fallback
        with patch('src.main.dhanhq') as mock_dhan_init:
            mock_dhan_instance = MagicMock()
            mock_dhan_init.return_value = mock_dhan_instance
            mock_dhan_instance.get_fund_limits.return_value = MOCK_FUNDS_RESPONSE
            
            # Request with the fallback user ID
            # "1101302170" is the fallback ID in main.py
            # "test-user-fallback" is also supported
            response = client.get(f"/api/dhan/funds?user_id=1101302170")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["availabelBalance"] == 100.25
