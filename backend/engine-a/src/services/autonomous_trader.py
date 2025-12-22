import asyncio
import logging
import os
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.services.risk_manager import RiskManager

logger = logging.getLogger(__name__)

# Constants
ENGINE_B_URL = os.environ.get("ENGINE_B_URL", "https://engine-b-429140669077.us-central1.run.app")
ENGINE_C_URL = os.environ.get("ENGINE_C_URL", "https://engine-c-429140669077.us-central1.run.app")

class AutonomousTrader:
    """
    Centralized Authority for Autonomous Trading.
    Located in Engine A (Orchestrator).
    Responsible for:
    1. Fetching Signals (from Engine B)
    2. Risk Validation (Engine A Authority)
    3. Trade Approval/Rejection
    4. Execution Command (to Engine C)
    """

    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
        self.is_active = False
        self.task = None
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.config = {
            "min_confidence": 0.75,
            "poll_interval": 10,  # seconds
            "max_risk_per_trade": 0.02, # 2%
            "capital": 100000.0, # Virtual capital for sizing
            "stop_loss_pct": 0.02
        }
        logger.info("✅ AutonomousTrader initialized in Engine A")

    async def start(self):
        """Start the autonomous trading loop"""
        if self.is_active:
            logger.warning("AutonomousTrader already running")
            return
        
        self.is_active = True
        self.task = asyncio.create_task(self._trading_loop())
        logger.info("🚀 AutonomousTrader Loop Started")

    async def stop(self):
        """Stop the autonomous trading loop"""
        logger.info("🛑 Stopping AutonomousTrader...")
        self.is_active = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        await self.http_client.aclose()
        logger.info("✅ AutonomousTrader Stopped")

    async def _trading_loop(self):
        """Main loop: Signal -> Risk -> Execution"""
        while self.is_active:
            try:
                # 1. Fetch Signals from Engine B
                signals = await self._fetch_signals()
                
                for signal in signals:
                    if not self.is_active: break
                    
                    # 2. Process & Risk Check
                    await self._process_signal(signal)
                
                await asyncio.sleep(self.config["poll_interval"])

            except Exception as e:
                logger.error(f"Error in AutonomousTrader loop: {e}")
                await asyncio.sleep(10) # Backoff on error

    async def _fetch_signals(self) -> List[Dict]:
        """Call Engine B to get AI Signals"""
        try:
            # Using the batch signal endpoint verified in Engine B
            url = f"{ENGINE_B_URL}/api/v1/signals/batch" 
            payload = {
                "symbols": ["NIFTY", "BANKNIFTY", "RELIANCE", "HDFCBANK", "INFY", "TCS"], # Default watchlist
                "fast": True
            }
            
            resp = await self.http_client.post(url, json=payload)
            if resp.status_code == 200:
                # Engine B returns list of SignalResponse objects directly for batch
                return resp.json()
            else:
                logger.warning(f"Engine B Signal Fetch Failed: {resp.status_code} - {resp.text}")
                return []
        except Exception as e:
            logger.error(f"Signal API Error: {e}")
            return []

    async def _process_signal(self, signal: Dict):
        """Authorize and Execute a potential trade"""
        symbol = signal.get("symbol")
        confidence = signal.get("confidence", 0)
        signal_type = signal.get("signal", "HOLD") # BUY/SELL
        
        if signal_type == "HOLD":
            return

        logger.info(f"🔎 Analyzing Signal: {signal_type} {symbol} ({confidence:.1%})")

        # ---------------------------------------------------------
        # RISK GATE (MANDATORY)
        # ---------------------------------------------------------
        # Calculate Position Size
        pos_size_res = self.risk_manager.optimize_position_size(
            capital=self.config["capital"],
            risk_per_trade=self.config["max_risk_per_trade"],
            stop_loss_pct=self.config["stop_loss_pct"]
        )
        safe_quantity = int(pos_size_res.get("optimal_position_size", 0) / (signal.get("current_price") or 1000))
        if safe_quantity <= 0:
            logger.warning(f"❌ Trade Rejected: Position size 0 for {symbol}")
            return
        
        # Risk Score
        risk_res = self.risk_manager.score_risk(
            position_size=pos_size_res.get("risk_amount", 0),
            volatility=0.02, # Should come from signal/market data
            max_drawdown=0.05 # Should come from portfolio state
        )
        
        if risk_res.get("recommendation") != "PROCEED":
             logger.warning(f"❌ Trade Rejected by Risk Manager: {symbol} - {risk_res['risk_level']}")
             return

        # ---------------------------------------------------------
        # EXECUTION AUTHORITY
        # ---------------------------------------------------------
        logger.info(f"✅ Trade APPROVED: {signal_type} {safe_quantity} {symbol}. Sending to Execution Engine.")
        await self._execute_trade(symbol, signal_type, safe_quantity, signal)

    async def _execute_trade(self, symbol: str, side: str, qty: int, signal_data: Dict):
        """Send explicit command to Engine C"""
        try:
            # Mapping schema to Engine C's OrderRequest
            sec_id = signal_data.get("security_id", "0")
            segment = signal_data.get("exchange_segment", "NSE_EQ")
            
            payload = {
                "transaction_type": side.upper(), # BUY/SELL
                "exchange_segment": segment, 
                "product_type": "INTRADAY",
                "order_type": "MARKET",
                "validity": "DAY",
                "security_id": sec_id,
                "quantity": qty,
                "price": 0
            }
            
            url = f"{ENGINE_C_URL}/api/dhan/place-order"
            resp = await self.http_client.post(url, json=payload)
            
            if resp.status_code == 200:
                logger.info(f"🎉 Execution Success: {resp.json()}")
            else:
                logger.error(f"❌ Execution Failed: {resp.text}")

        except Exception as e:
            logger.error(f"Execution API Error: {e}")

