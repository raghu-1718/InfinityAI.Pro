import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from .order_manager import order_manager, Order, OrderStatus, OrderType
from .position_manager import position_manager
from .risk_manager import risk_manager
from ..broker.adapter_factory import get_adapter
from ...shared.utils.logger import get_logger

logger = get_logger("execution_engine")

class ExecutionEngine:
    def __init__(self):
        self.running = False
        self.broker_adapters: Dict[str, Any] = {}
        self.execution_queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.order_status_tasks: Dict[str, asyncio.Task] = {}
        
        # Register callbacks
        order_manager.add_order_callback(self._on_order_event)
        position_manager.add_position_callback(self._on_position_event)
        risk_manager.add_risk_callback(self._on_risk_event)
        
    async def start(self, num_workers: int = 3):
        """Start the execution engine"""
        if self.running:
            return
            
        self.running = True
        logger.info(f"Starting execution engine with {num_workers} workers")
        
        # Start worker tasks
        for i in range(num_workers):
            worker = asyncio.create_task(self._execution_worker(f"worker-{i}"))
            self.workers.append(worker)
            
        # Start monitoring tasks
        asyncio.create_task(self._risk_monitoring_loop())
        asyncio.create_task(self._order_status_monitoring_loop())
        
    async def stop(self):
        """Stop the execution engine"""
        if not self.running:
            return
            
        self.running = False
        logger.info("Stopping execution engine")
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
            
        # Cancel order status tasks
        for task in self.order_status_tasks.values():
            task.cancel()
            
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
    async def submit_order(self, order: Order) -> str:
        """Submit an order for execution"""
        # Validate with risk manager
        is_valid, reason = await risk_manager.validate_order(order)
        if not is_valid:
            logger.warning(f"Order rejected by risk manager: {reason}")
            await order_manager.update_order_status(order.id, OrderStatus.REJECTED)
            raise ValueError(f"Risk check failed: {reason}")
            
        # Create order in order manager
        order_id = await order_manager.create_order(order)
        
        # Queue for execution
        await self.execution_queue.put(order_id)
        
        logger.info(f"Submitted order {order_id} for execution")
        return order_id
        
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        order = order_manager.get_order(order_id)
        if not order:
            return False
            
        # Try to cancel with broker first
        if order.broker_order_id:
            try:
                adapter = self._get_broker_adapter(order.user_id)
                if adapter and hasattr(adapter, 'cancel_order'):
                    await adapter.cancel_order(order.broker_order_id)
            except Exception as e:
                logger.error(f"Failed to cancel order with broker: {e}")
                
        # Update order status
        return await order_manager.cancel_order(order_id)
        
    async def _execution_worker(self, worker_name: str):
        """Worker task for processing order executions"""
        logger.info(f"Started execution worker: {worker_name}")
        
        while self.running:
            try:
                # Get order from queue with timeout
                order_id = await asyncio.wait_for(
                    self.execution_queue.get(), timeout=1.0
                )
                
                await self._execute_order(order_id)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in execution worker {worker_name}: {e}")
                
        logger.info(f"Stopped execution worker: {worker_name}")
        
    async def _execute_order(self, order_id: str):
        """Execute a single order"""
        order = order_manager.get_order(order_id)
        if not order:
            logger.error(f"Order {order_id} not found for execution")
            return
            
        try:
            # Get broker adapter
            adapter = self._get_broker_adapter(order.user_id)
            if not adapter:
                raise Exception("No broker adapter available")
                
            # Update order status to submitted
            await order_manager.update_order_status(order_id, OrderStatus.SUBMITTED)
            
            # Execute with broker
            result = await self._execute_with_broker(adapter, order)
            
            if result.get("status") == "success":
                broker_order_id = result.get("broker_order_id")
                await order_manager.update_order_status(
                    order_id, OrderStatus.SUBMITTED, broker_order_id=broker_order_id
                )
                
                # Start monitoring order status
                if broker_order_id:
                    task = asyncio.create_task(
                        self._monitor_order_status(order_id, broker_order_id, adapter)
                    )
                    self.order_status_tasks[order_id] = task
                    
            else:
                await order_manager.update_order_status(order_id, OrderStatus.REJECTED)
                logger.error(f"Order execution failed: {result.get('message')}")
                
        except Exception as e:
            logger.error(f"Failed to execute order {order_id}: {e}")
            await order_manager.update_order_status(order_id, OrderStatus.REJECTED)
            
    async def _execute_with_broker(self, adapter, order: Order) -> Dict[str, Any]:
        """Execute order with broker adapter"""
        # Convert order to broker format
        broker_order = {
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "order_type": order.order_type.value,
            "price": order.price,
            "stop_price": order.stop_price,
            "user_id": order.user_id
        }
        
        # Execute with adapter
        if hasattr(adapter, 'execute_order_async'):
            return await adapter.execute_order_async(broker_order)
        else:
            # Fallback to sync execution
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, adapter.execute_trade, broker_order, {})
            
    async def _monitor_order_status(self, order_id: str, broker_order_id: str, adapter):
        """Monitor order status with broker"""
        try:
            while self.running:
                # Check order status with broker
                if hasattr(adapter, 'get_order_status'):
                    status_info = await adapter.get_order_status(broker_order_id)
                    
                    if status_info:
                        await self._process_order_status_update(order_id, status_info)
                        
                        # Stop monitoring if order is complete
                        if status_info.get("status") in ["FILLED", "CANCELLED", "REJECTED"]:
                            break
                            
                await asyncio.sleep(1)  # Check every second
                
        except Exception as e:
            logger.error(f"Error monitoring order status for {order_id}: {e}")
        finally:
            # Clean up task reference
            if order_id in self.order_status_tasks:
                del self.order_status_tasks[order_id]
                
    async def _process_order_status_update(self, order_id: str, status_info: Dict[str, Any]):
        """Process order status update from broker"""
        broker_status = status_info.get("status", "")
        filled_qty = status_info.get("filled_quantity", 0)
        fill_price = status_info.get("fill_price", 0.0)
        
        # Map broker status to internal status
        status_mapping = {
            "NEW": OrderStatus.SUBMITTED,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "CANCELLED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
            "EXPIRED": OrderStatus.EXPIRED
        }
        
        internal_status = status_mapping.get(broker_status, OrderStatus.SUBMITTED)
        
        # Update order status
        await order_manager.update_order_status(
            order_id, internal_status, filled_qty=filled_qty, fill_price=fill_price
        )
        
        # Update position if filled
        if filled_qty > 0:
            order = order_manager.get_order(order_id)
            if order:
                await position_manager.update_position(
                    order.user_id, order.symbol, filled_qty, fill_price, order.side
                )
                
    def _get_broker_adapter(self, user_id: str):
        """Get broker adapter for user"""
        # This would typically get user credentials and create adapter
        # For now, return a cached adapter or create new one
        if user_id not in self.broker_adapters:
            try:
                from ....core.user_manager import get_user_credentials
                creds = get_user_credentials(user_id)
                if creds:
                    adapter = get_adapter(creds["broker"])
                    self.broker_adapters[user_id] = adapter
                    return adapter
            except Exception as e:
                logger.error(f"Failed to get broker adapter for {user_id}: {e}")
                return None
                
        return self.broker_adapters.get(user_id)
        
    async def _risk_monitoring_loop(self):
        """Continuous risk monitoring loop"""
        while self.running:
            try:
                # Get all users with active positions
                user_ids = set()
                for position_key in position_manager.positions.keys():
                    user_id = position_key.split(":")[0]
                    user_ids.add(user_id)
                    
                # Monitor each user
                for user_id in user_ids:
                    await risk_manager.monitor_positions(user_id)
                    
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in risk monitoring loop: {e}")
                await asyncio.sleep(10)
                
    async def _order_status_monitoring_loop(self):
        """Monitor for stale orders that need status updates"""
        while self.running:
            try:
                # Check for orders that haven't been updated recently
                pending_orders = order_manager.get_pending_orders()
                
                for order in pending_orders:
                    # If order is older than 30 seconds and still pending, check status
                    age = datetime.now() - order.created_at
                    if age.total_seconds() > 30 and order.broker_order_id:
                        if order.id not in self.order_status_tasks:
                            adapter = self._get_broker_adapter(order.user_id)
                            if adapter:
                                task = asyncio.create_task(
                                    self._monitor_order_status(order.id, order.broker_order_id, adapter)
                                )
                                self.order_status_tasks[order.id] = task
                                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in order status monitoring loop: {e}")
                await asyncio.sleep(30)
                
    async def _on_order_event(self, order: Order, event_type: str):
        """Handle order events"""
        logger.info(f"Order event: {event_type} for order {order.id}")
        
    async def _on_position_event(self, position, event_type: str):
        """Handle position events"""
        logger.info(f"Position event: {event_type} for {position.symbol}")
        
    async def _on_risk_event(self, data, event_type: str):
        """Handle risk events"""
        logger.warning(f"Risk event: {event_type}")

# Global execution engine instance
execution_engine = ExecutionEngine()