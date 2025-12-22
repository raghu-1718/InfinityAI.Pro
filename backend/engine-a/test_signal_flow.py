import asyncio
import logging
import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from services.autonomous_trader import AutonomousTrader
from services.risk_manager import RiskManager

# Mock logging
logging.basicConfig(level=logging.INFO)

class TestSignalFlow(unittest.TestCase):
    def setUp(self):
        # Mock Risk Manager
        self.risk_manager = MagicMock(spec=RiskManager)
        self.risk_manager.optimize_position_size.return_value = {
            "optimal_position_size": 100000.0,
            "risk_amount": 2000.0
        }
        self.risk_manager.score_risk.return_value = {"recommendation": "PROCEED", "risk_level": "LOW"}
        
        # Init Trader
        self.trader = AutonomousTrader(self.risk_manager)
        
        # Mock HTTP client
        self.trader.http_client = AsyncMock()

    async def async_test_flow(self):
        # 1. Setup Mock Engine B Response (Batch Signals)
        # Matches Engine B's SignalResponse structure
        signal_response = [
            {
                "symbol": "NIFTY",
                "signal": "BUY",
                "confidence": 85.0,
                "predicted_price": 24000.0,
                "current_price": 23800.0,
                "timestamp": "2024-01-01T10:00:00Z",
                "model_version": "v3.6-ml",
                "security_id": "13",
                "exchange_segment": "IDX_I"
            },
            {
                "symbol": "RELIANCE",
                "signal": "HOLD",
                "confidence": 50.0,
                "predicted_price": 2500.0,
                "current_price": 2500.0,
                "timestamp": "2024-01-01T10:00:00Z",
                "model_version": "v3.6-ml",
                "security_id": "1333",
                "exchange_segment": "NSE_EQ"
            },
            {
                "symbol": "TCS",
                "signal": "BUY",  # Valid signal but HIGH RISK
                "confidence": 80.0,
                "predicted_price": 4000.0,
                "current_price": 3800.0,
                "timestamp": "2024-01-01T10:00:00Z",
                "model_version": "v3.6-ml",
                "security_id": "2968",
                "exchange_segment": "NSE_EQ"
            }
        ]
        
        # Configure Risk Manager Side Effects
        # 1. NIFTY -> PROCEED
        # 2. TCS -> REVIEW (REJECT)
        self.risk_manager.score_risk.side_effect = [
            {"recommendation": "PROCEED", "risk_level": "LOW"},
            {"recommendation": "REVIEW", "risk_level": "HIGH", "components": {"volatility": 0.9}}
        ]

        # Mock POST to Engine B
        mock_b_resp = MagicMock()
        mock_b_resp.status_code = 200
        mock_b_resp.json.return_value = signal_response
        
        # Mock POST to Engine C (Execution)
        mock_c_resp = MagicMock()
        mock_c_resp.status_code = 200
        mock_c_resp.json.return_value = {"status": "success", "order_id": "123"}
        
        # Configure side_effects based on URL
        async def post_side_effect(url, json=None):
            if "engine-b" in url and "signals/batch" in url:
                print(f"Verified call to Engine B: {url}")
                # Verify payload
                assert "symbols" in json
                assert json["fast"] is True
                return mock_b_resp
            elif "engine-c" in url and "place-order" in url:
                print(f"Verified call to Engine C: {url}")
                # Verify payload
                print(f"Execution Payload: {json}")
                # Should ONLY call for NIFTY (ID 13)
                if json["security_id"] == "2968":
                    raise AssertionError("❌ CRITICAL: Engine C called for High Risk Trade (TCS)!")
                
                assert json["security_id"] == "13"
                assert json["exchange_segment"] == "IDX_I"
                assert json["transaction_type"] == "BUY"
                return mock_c_resp
            return MagicMock(status_code=404)

        self.trader.http_client.post.side_effect = post_side_effect

        # 2. Run _fetch_signals
        signals = await self.trader._fetch_signals()
        print(f"Signals Fetched: {len(signals)}")
        assert len(signals) == 3
        
        # 3. Process Signals
        print("Processing signals...")
        for signal in signals:
            await self.trader._process_signal(signal)
            
        # 4. Verify Assertions
        # Should execute NIFTY (BUY)
        # Skip RELIANCE (HOLD)
        # Reject TCS (High Risk)
        # Check call count: 1 fetch + 1 execution (Nifty) = 2 calls
        assert self.trader.http_client.post.call_count == 2
        print("[SUCCESS] Signal Flow & Risk Gate Verification Passed")

    def test_run_async(self):
        asyncio.run(self.async_test_flow())

if __name__ == "__main__":
    unittest.main()
