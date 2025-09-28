# services/ai/execution_service.py
"""
InfinityAI.Pro - Auto-Trade Execution Service
Interfaces with Dhan / CoinSwitch PRO for live trade execution
"""

import httpx
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import asyncio
from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class ExecutionService:
    """Auto-trade execution service for Dhan/CoinSwitch PRO"""

    def __init__(self):
        self.config = Config()
        self.client: Optional[httpx.AsyncClient] = None
        self.initialized = False
        self.broker = self.config.BROKER_TYPE  # "dhan" or "coinswitch"
        self.execution_queue = asyncio.Queue()
        self.is_executing = False

    async def initialize(self):
        """Initialize execution service"""
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
            self.initialized = True
            logger.info(f"✅ Execution Service initialized for {self.broker.upper()}")

            # Start execution worker
            asyncio.create_task(self._execution_worker())

        except Exception as e:
            logger.error(f"Failed to initialize Execution service: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    # Dhan Broker Integration
    async def dhan_place_order(self, order_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Place order via Dhan API"""
        try:
            dhan_url = f"{self.config.DHAN_BASE_URL}/v2/orders"
            headers = {
                "access-token": self.config.DHAN_ACCESS_TOKEN,
                "Content-Type": "application/json"
            }

            # Prepare Dhan order payload
            payload = {
                "dhanClientId": self.config.DHAN_CLIENT_ID,
                "transactionType": order_data.get("action", "BUY"),
                "exchangeSegment": "NSE_EQ",  # Default to NSE Equity
                "productType": "INTRADAY",  # Default to intraday
                "orderType": "MARKET",  # Default to market order
                "validity": "DAY",
                "securityId": order_data.get("security_id", ""),
                "quantity": order_data.get("quantity", 0),
                "price": order_data.get("price", 0.0),
                "triggerPrice": order_data.get("trigger_price", 0.0),
                "disclosedQuantity": 0,
                "afterMarketOrder": False,
                "boProfitValue": order_data.get("take_profit", 0.0),
                "boStopLossValue": order_data.get("stop_loss", 0.0)
            }

            # Add stop loss and take profit if provided
            if order_data.get("stop_loss"):
                payload["orderType"] = "SL"
                payload["triggerPrice"] = order_data["stop_loss"]

            async with self.client.post(dhan_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

            return {
                "order_id": result.get("orderId", ""),
                "status": "PLACED",
                "broker": "dhan",
                "order_details": payload,
                "response": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Dhan order placement error: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "broker": "dhan",
                "timestamp": datetime.now().isoformat()
            }

    async def dhan_get_order_status(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Get order status from Dhan"""
        try:
            dhan_url = f"{self.config.DHAN_BASE_URL}/v2/orders/{order_id}"
            headers = {"access-token": self.config.DHAN_ACCESS_TOKEN}

            async with self.client.get(dhan_url, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

            return {
                "order_id": order_id,
                "status": result.get("orderStatus", "UNKNOWN"),
                "filled_quantity": result.get("quantity", 0),
                "average_price": result.get("price", 0.0),
                "broker": "dhan",
                "raw_response": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Dhan order status error: {e}")
            return {"error": str(e)}

    async def dhan_cancel_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Cancel order via Dhan"""
        try:
            dhan_url = f"{self.config.DHAN_BASE_URL}/v2/orders/{order_id}"
            headers = {"access-token": self.config.DHAN_ACCESS_TOKEN}

            async with self.client.delete(dhan_url, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

            return {
                "order_id": order_id,
                "status": "CANCELLED",
                "broker": "dhan",
                "response": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Dhan order cancellation error: {e}")
            return {"error": str(e)}

    # CoinSwitch PRO Integration
    async def coinswitch_place_order(self, order_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Place order via CoinSwitch PRO API"""
        try:
            cs_url = f"{self.config.COINSWITCH_BASE_URL}/trade/order"
            headers = {
                "X-AUTH-APIKEY": self.config.COINSWITCH_API_KEY,
                "X-AUTH-SIGNATURE": self._generate_coinswitch_signature(),
                "Content-Type": "application/json"
            }

            # Prepare CoinSwitch order payload
            payload = {
                "symbol": order_data.get("symbol", ""),
                "side": order_data.get("action", "BUY").lower(),
                "type": "market",  # Default to market order
                "quantity": order_data.get("quantity", 0),
                "price": order_data.get("price", 0.0),
                "timestamp": int(datetime.now().timestamp() * 1000)
            }

            # Add stop loss if provided
            if order_data.get("stop_loss"):
                payload["type"] = "stop_loss"
                payload["stop_price"] = order_data["stop_loss"]

            async with self.client.post(cs_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

            return {
                "order_id": result.get("order_id", ""),
                "status": "PLACED",
                "broker": "coinswitch",
                "order_details": payload,
                "response": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"CoinSwitch order placement error: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "broker": "coinswitch",
                "timestamp": datetime.now().isoformat()
            }

    async def coinswitch_get_order_status(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Get order status from CoinSwitch"""
        try:
            cs_url = f"{self.config.COINSWITCH_BASE_URL}/trade/order/{order_id}"
            headers = {
                "X-AUTH-APIKEY": self.config.COINSWITCH_API_KEY,
                "X-AUTH-SIGNATURE": self._generate_coinswitch_signature()
            }

            async with self.client.get(cs_url, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

            return {
                "order_id": order_id,
                "status": result.get("status", "UNKNOWN"),
                "filled_quantity": result.get("filled_quantity", 0),
                "average_price": result.get("average_price", 0.0),
                "broker": "coinswitch",
                "raw_response": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"CoinSwitch order status error: {e}")
            return {"error": str(e)}

    async def coinswitch_cancel_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Cancel order via CoinSwitch"""
        try:
            cs_url = f"{self.config.COINSWITCH_BASE_URL}/trade/order/{order_id}"
            headers = {
                "X-AUTH-APIKEY": self.config.COINSWITCH_API_KEY,
                "X-AUTH-SIGNATURE": self._generate_coinswitch_signature()
            }

            payload = {"timestamp": int(datetime.now().timestamp() * 1000)}

            async with self.client.delete(cs_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

            return {
                "order_id": order_id,
                "status": "CANCELLED",
                "broker": "coinswitch",
                "response": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"CoinSwitch order cancellation error: {e}")
            return {"error": str(e)}

    # Unified Execution Interface
    async def execute_order(self, order_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute order with risk checks and broker routing"""
        try:
            # Pre-execution risk check
            risk_check = await self._pre_execution_risk_check(order_data)
            if not risk_check.get("approved", False):
                return {
                    "status": "REJECTED",
                    "reason": "Risk check failed",
                    "risk_details": risk_check,
                    "timestamp": datetime.now().isoformat()
                }

            # Route to appropriate broker
            if self.broker == "dhan":
                result = await self.dhan_place_order(order_data, **kwargs)
            elif self.broker == "coinswitch":
                result = await self.coinswitch_place_order(order_data, **kwargs)
            else:
                return {"error": f"Unsupported broker: {self.broker}"}

            # Log execution
            await self._log_execution(order_data, result)

            return result

        except Exception as e:
            logger.error(f"Order execution error: {e}")
            return {"error": str(e)}

    async def get_order_status(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Get order status"""
        try:
            if self.broker == "dhan":
                return await self.dhan_get_order_status(order_id, **kwargs)
            elif self.broker == "coinswitch":
                return await self.coinswitch_get_order_status(order_id, **kwargs)
            else:
                return {"error": f"Unsupported broker: {self.broker}"}

        except Exception as e:
            logger.error(f"Order status error: {e}")
            return {"error": str(e)}

    async def cancel_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Cancel order"""
        try:
            if self.broker == "dhan":
                return await self.dhan_cancel_order(order_id, **kwargs)
            elif self.broker == "coinswitch":
                return await self.coinswitch_cancel_order(order_id, **kwargs)
            else:
                return {"error": f"Unsupported broker: {self.broker}"}

        except Exception as e:
            logger.error(f"Order cancellation error: {e}")
            return {"error": str(e)}

    # Portfolio Management
    async def get_portfolio(self, **kwargs) -> Dict[str, Any]:
        """Get current portfolio"""
        try:
            if self.broker == "dhan":
                return await self._dhan_get_portfolio(**kwargs)
            elif self.broker == "coinswitch":
                return await self._coinswitch_get_portfolio(**kwargs)
            else:
                return {"error": f"Unsupported broker: {self.broker}"}

        except Exception as e:
            logger.error(f"Portfolio fetch error: {e}")
            return {"error": str(e)}

    async def get_positions(self, **kwargs) -> List[Dict[str, Any]]:
        """Get current positions"""
        try:
            portfolio = await self.get_portfolio(**kwargs)
            return portfolio.get("positions", [])

        except Exception as e:
            logger.error(f"Positions fetch error: {e}")
            return []

    # Auto-trading with Signal Integration
    async def execute_signal(self, signal: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute trade based on AI signal"""
        try:
            from .signal_service import SignalService
            from .risk_service import RiskService

            signal_service = SignalService()
            risk_service = RiskService()

            await signal_service.initialize()
            await risk_service.initialize()

            # Generate order suggestion from signal
            portfolio = await self.get_portfolio()
            order_suggestion = await signal_service.suggest_order(signal, portfolio, **kwargs)

            if order_suggestion.get("action") == "HOLD":
                return {
                    "status": "NO_ACTION",
                    "reason": order_suggestion.get("reason", "No action needed"),
                    "signal": signal,
                    "timestamp": datetime.now().isoformat()
                }

            # Execute the suggested order
            order_data = {
                "symbol": order_suggestion.get("symbol"),
                "action": order_suggestion.get("action"),
                "quantity": order_suggestion.get("quantity", 0),
                "price": order_suggestion.get("entry_price", 0),
                "stop_loss": order_suggestion.get("stop_loss", 0),
                "take_profit": order_suggestion.get("take_profit", 0)
            }

            result = await self.execute_order(order_data, **kwargs)

            return {
                "signal": signal,
                "order_suggestion": order_suggestion,
                "execution_result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Signal execution error: {e}")
            return {"error": str(e)}

    # Queue-based execution for high-frequency trading
    async def queue_order(self, order_data: Dict[str, Any], **kwargs) -> str:
        """Queue order for execution"""
        try:
            order_id = f"queue_{datetime.now().timestamp()}"
            await self.execution_queue.put({
                "id": order_id,
                "data": order_data,
                "kwargs": kwargs,
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"Order queued: {order_id}")
            return order_id

        except Exception as e:
            logger.error(f"Order queuing error: {e}")
            raise

    async def _execution_worker(self):
        """Background worker for processing queued orders"""
        while True:
            try:
                if self.execution_queue.empty():
                    await asyncio.sleep(1)
                    continue

                order_item = await self.execution_queue.get()
                order_data = order_item["data"]
                kwargs = order_item.get("kwargs", {})

                logger.info(f"Processing queued order: {order_item['id']}")

                # Execute order
                result = await self.execute_order(order_data, **kwargs)

                # Log result
                await self._log_execution(order_data, result)

                self.execution_queue.task_done()

            except Exception as e:
                logger.error(f"Execution worker error: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    # Helper methods
    async def _pre_execution_risk_check(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform pre-execution risk checks"""
        try:
            from .risk_service import RiskService

            risk_service = RiskService()
            await risk_service.initialize()

            # Get portfolio for context
            portfolio = await self.get_portfolio()

            # Assess trade risk
            risk_assessment = await risk_service.assess_risk({
                "symbol": order_data.get("symbol"),
                "action": order_data.get("action"),
                "quantity": order_data.get("quantity", 0),
                "price": order_data.get("price", 0.0),
                "portfolio_value": portfolio.get("total_value", 100000),
                "stop_loss_pct": 0.02,  # Default 2%
                "existing_positions": portfolio.get("positions", [])
            })

            return risk_assessment

        except Exception as e:
            logger.error(f"Risk check error: {e}")
            return {"approved": False, "error": str(e)}

    async def _log_execution(self, order_data: Dict[str, Any], result: Dict[str, Any]):
        """Log trade execution"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "order_data": order_data,
                "execution_result": result,
                "broker": self.broker
            }

            # Write to trade logs
            import os
            log_file = os.path.join(os.path.dirname(__file__), "../../trade_logs/executions.jsonl")

            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            logger.error(f"Execution logging error: {e}")

    def _generate_coinswitch_signature(self) -> str:
        """Generate CoinSwitch API signature"""
        # This would implement proper HMAC signature generation
        # For now, return a placeholder
        return "placeholder_signature"

    async def _dhan_get_portfolio(self, **kwargs) -> Dict[str, Any]:
        """Get portfolio from Dhan"""
        try:
            dhan_url = f"{self.config.DHAN_BASE_URL}/v2/portfolio"
            headers = {"access-token": self.config.DHAN_ACCESS_TOKEN}

            async with self.client.get(dhan_url, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

            return {
                "total_value": result.get("totalValue", 0),
                "positions": result.get("positions", []),
                "broker": "dhan",
                "raw_response": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Dhan portfolio fetch error: {e}")
            return {"error": str(e)}

    async def _coinswitch_get_portfolio(self, **kwargs) -> Dict[str, Any]:
        """Get portfolio from CoinSwitch"""
        try:
            cs_url = f"{self.config.COINSWITCH_BASE_URL}/user/balances"
            headers = {
                "X-AUTH-APIKEY": self.config.COINSWITCH_API_KEY,
                "X-AUTH-SIGNATURE": self._generate_coinswitch_signature()
            }

            async with self.client.get(cs_url, headers=headers) as resp:
                resp.raise_for_status()
                result = resp.json()

            return {
                "total_value": result.get("total_balance", 0),
                "positions": result.get("positions", []),
                "broker": "coinswitch",
                "raw_response": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"CoinSwitch portfolio fetch error: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict:
        """Check execution service health"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            # Check broker connectivity
            if self.broker == "dhan":
                health = bool(self.config.DHAN_ACCESS_TOKEN and self.config.DHAN_CLIENT_ID)
            elif self.broker == "coinswitch":
                health = bool(self.config.COINSWITCH_API_KEY)
            else:
                health = False

            return {
                "status": "healthy" if health else "configuration_error",
                "broker": self.broker,
                "queue_size": self.execution_queue.qsize(),
                "is_executing": self.is_executing
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }