"""
Audit logging utility for Engine C
InfinityAI.Pro Trading Platform

Comprehensive audit trail logging for trade execution, risk management,
and regulatory compliance with structured data storage.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import uuid

import asyncpg

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    TRADE_SUBMITTED = "TRADE_SUBMITTED"
    TRADE_EXECUTED = "TRADE_EXECUTED"
    TRADE_REJECTED = "TRADE_REJECTED"
    TRADE_FAILED = "TRADE_FAILED"
    TRADE_CANCELLED = "TRADE_CANCELLED"
    
    RISK_VALIDATION = "RISK_VALIDATION"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    KILL_SWITCH_ACTIVATED = "KILL_SWITCH_ACTIVATED"
    KILL_SWITCH_DEACTIVATED = "KILL_SWITCH_DEACTIVATED"
    
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    CIRCUIT_BREAKER_CLOSED = "CIRCUIT_BREAKER_CLOSED"
    
    POSITION_UPDATED = "POSITION_UPDATED"
    MARGIN_CALL = "MARGIN_CALL"
    
    SYSTEM_START = "SYSTEM_START"
    SYSTEM_STOP = "SYSTEM_STOP"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    USER_ACTION = "USER_ACTION"
    
    COMPLIANCE_CHECK = "COMPLIANCE_CHECK"
    REGULATORY_REPORT = "REGULATORY_REPORT"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class AuditEvent:
    """Structured audit event"""
    event_id: str
    event_type: AuditEventType
    timestamp: float
    severity: AuditSeverity
    source: str
    message: str
    data: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    ip_address: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'severity': self.severity.value,
            'source': self.source,
            'message': self.message,
            'data': self.data,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'correlation_id': self.correlation_id,
            'ip_address': self.ip_address,
            'datetime': datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat()
        }


class AuditLogger:
    """Audit logging service with database persistence"""
    
    def __init__(self, postgres_pool: asyncpg.Pool, service_name: str = "engine-c"):
        self.postgres_pool = postgres_pool
        self.service_name = service_name
        self._buffer = []
        self._buffer_lock = asyncio.Lock()
        self._flush_task = None
        self._should_stop = False
        
        # Configuration
        self.buffer_size = 100
        self.flush_interval = 10  # seconds
        
        # Start background flush task
        self._start_flush_task()
    
    def _start_flush_task(self):
        """Start background task to flush audit events"""
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._background_flush())
    
    async def _background_flush(self):
        """Background task to periodically flush buffered events"""
        while not self._should_stop:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_buffer()
            except Exception as e:
                logger.error(f"Error in audit flush task: {e}")
    
    async def log_event(self,
                       event_type: AuditEventType,
                       message: str,
                       data: Dict[str, Any] = None,
                       severity: AuditSeverity = AuditSeverity.INFO,
                       user_id: str = None,
                       session_id: str = None,
                       correlation_id: str = None,
                       ip_address: str = None) -> str:
        """
        Log an audit event
        
        Returns:
            event_id: Unique identifier for the logged event
        """
        
        event_id = str(uuid.uuid4())
        
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=time.time(),
            severity=severity,
            source=self.service_name,
            message=message,
            data=data or {},
            user_id=user_id,
            session_id=session_id,
            correlation_id=correlation_id,
            ip_address=ip_address
        )
        
        # Add to buffer
        async with self._buffer_lock:
            self._buffer.append(event)
            
            # Flush if buffer is full
            if len(self._buffer) >= self.buffer_size:
                await self._flush_buffer()
        
        # Log to standard logger as well
        log_level = self._get_log_level(severity)
        logger.log(
            log_level,
            f"AUDIT: {message}",
            extra={
                'event_id': event_id,
                'event_type': event_type.value,
                'audit_data': data
            }
        )
        
        return event_id
    
    def _get_log_level(self, severity: AuditSeverity) -> int:
        """Convert audit severity to logging level"""
        mapping = {
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL
        }
        return mapping.get(severity, logging.INFO)
    
    async def _flush_buffer(self):
        """Flush buffered events to database"""
        async with self._buffer_lock:
            if not self._buffer:
                return
            
            events_to_flush = self._buffer.copy()
            self._buffer.clear()
        
        try:
            await self._store_events(events_to_flush)
            logger.debug(f"Flushed {len(events_to_flush)} audit events to database")
            
        except Exception as e:
            logger.error(f"Failed to flush audit events: {e}")
            
            # Put events back in buffer
            async with self._buffer_lock:
                self._buffer.extend(events_to_flush)
    
    async def _store_events(self, events: List[AuditEvent]):
        """Store events in database"""
        if not events:
            return
        
        async with self.postgres_pool.acquire() as conn:
            # Prepare batch insert
            query = """
                INSERT INTO audit_logs (
                    event_id, event_type, timestamp, severity, source, message,
                    data, user_id, session_id, correlation_id, ip_address, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
            """
            
            batch_data = []
            for event in events:
                batch_data.append((
                    event.event_id,
                    event.event_type.value,
                    event.timestamp,
                    event.severity.value,
                    event.source,
                    event.message,
                    json.dumps(event.data) if event.data else None,
                    event.user_id,
                    event.session_id,
                    event.correlation_id,
                    event.ip_address
                ))
            
            await conn.executemany(query, batch_data)
    
    async def force_flush(self):
        """Force flush all buffered events"""
        await self._flush_buffer()
    
    async def shutdown(self):
        """Shutdown audit logger and flush remaining events"""
        self._should_stop = True
        
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        await self._flush_buffer()
        logger.info("Audit logger shutdown completed")
    
    # Convenience methods for common audit events
    
    async def log_trade_submitted(self, trade_data: Dict[str, Any], user_id: str = None):
        """Log trade submission"""
        return await self.log_event(
            AuditEventType.TRADE_SUBMITTED,
            f"Trade submitted for {trade_data.get('symbol', 'unknown')} - {trade_data.get('quantity', 0)} shares",
            data=trade_data,
            user_id=user_id
        )
    
    async def log_trade_executed(self, trade_data: Dict[str, Any], execution_data: Dict[str, Any]):
        """Log trade execution"""
        return await self.log_event(
            AuditEventType.TRADE_EXECUTED,
            f"Trade executed: {trade_data.get('symbol', 'unknown')} - {execution_data.get('filled_quantity', 0)} @ {execution_data.get('fill_price', 0)}",
            data={**trade_data, **execution_data}
        )
    
    async def log_trade_rejected(self, trade_data: Dict[str, Any], rejection_reason: str):
        """Log trade rejection"""
        return await self.log_event(
            AuditEventType.TRADE_REJECTED,
            f"Trade rejected for {trade_data.get('symbol', 'unknown')}: {rejection_reason}",
            data={**trade_data, 'rejection_reason': rejection_reason},
            severity=AuditSeverity.WARNING
        )
    
    async def log_trade_failed(self, trade_data: Dict[str, Any], error: str):
        """Log trade failure"""
        return await self.log_event(
            AuditEventType.TRADE_FAILED,
            f"Trade failed for {trade_data.get('symbol', 'unknown')}: {error}",
            data={**trade_data, 'error': error},
            severity=AuditSeverity.ERROR
        )
    
    async def log_risk_validation(self, validation_type: str, result: bool, details: Dict[str, Any]):
        """Log risk validation"""
        severity = AuditSeverity.INFO if result else AuditSeverity.WARNING
        return await self.log_event(
            AuditEventType.RISK_VALIDATION,
            f"Risk validation ({validation_type}): {'PASSED' if result else 'FAILED'}",
            data={
                'validation_type': validation_type,
                'result': result,
                **details
            },
            severity=severity
        )
    
    async def log_limit_exceeded(self, limit_type: str, current_value: float, limit_value: float, details: Dict[str, Any] = None):
        """Log limit exceeded"""
        return await self.log_event(
            AuditEventType.LIMIT_EXCEEDED,
            f"Limit exceeded: {limit_type} - Current: {current_value}, Limit: {limit_value}",
            data={
                'limit_type': limit_type,
                'current_value': current_value,
                'limit_value': limit_value,
                **(details or {})
            },
            severity=AuditSeverity.WARNING
        )
    
    async def log_kill_switch(self, switch_type: str, action: str, reason: str, user_id: str = None):
        """Log kill switch activation/deactivation"""
        event_type = AuditEventType.KILL_SWITCH_ACTIVATED if action == 'activated' else AuditEventType.KILL_SWITCH_DEACTIVATED
        severity = AuditSeverity.CRITICAL if action == 'activated' else AuditSeverity.INFO
        
        return await self.log_event(
            event_type,
            f"Kill switch {action}: {switch_type} - {reason}",
            data={
                'switch_type': switch_type,
                'action': action,
                'reason': reason
            },
            severity=severity,
            user_id=user_id
        )
    
    async def log_circuit_breaker(self, breaker_name: str, state: str, details: Dict[str, Any] = None):
        """Log circuit breaker state change"""
        event_type = AuditEventType.CIRCUIT_BREAKER_OPEN if state == 'OPEN' else AuditEventType.CIRCUIT_BREAKER_CLOSED
        severity = AuditSeverity.WARNING if state == 'OPEN' else AuditSeverity.INFO
        
        return await self.log_event(
            event_type,
            f"Circuit breaker {breaker_name} state changed to {state}",
            data={
                'breaker_name': breaker_name,
                'state': state,
                **(details or {})
            },
            severity=severity
        )
    
    async def log_position_update(self, account_id: str, symbol: str, position_data: Dict[str, Any]):
        """Log position update"""
        return await self.log_event(
            AuditEventType.POSITION_UPDATED,
            f"Position updated for {account_id} - {symbol}",
            data={
                'account_id': account_id,
                'symbol': symbol,
                **position_data
            }
        )
    
    async def log_system_event(self, event: str, details: Dict[str, Any] = None):
        """Log system events"""
        event_mapping = {
            'start': AuditEventType.SYSTEM_START,
            'stop': AuditEventType.SYSTEM_STOP,
            'error': AuditEventType.SYSTEM_ERROR
        }
        
        event_type = event_mapping.get(event, AuditEventType.SYSTEM_ERROR)
        severity = AuditSeverity.ERROR if event == 'error' else AuditSeverity.INFO
        
        return await self.log_event(
            event_type,
            f"System event: {event}",
            data=details or {},
            severity=severity
        )
    
    async def log_configuration_change(self, setting: str, old_value: Any, new_value: Any, user_id: str = None):
        """Log configuration changes"""
        return await self.log_event(
            AuditEventType.CONFIGURATION_CHANGE,
            f"Configuration changed: {setting} from {old_value} to {new_value}",
            data={
                'setting': setting,
                'old_value': str(old_value),
                'new_value': str(new_value)
            },
            user_id=user_id
        )
    
    async def log_user_action(self, action: str, details: Dict[str, Any], user_id: str, ip_address: str = None):
        """Log user actions"""
        return await self.log_event(
            AuditEventType.USER_ACTION,
            f"User action: {action}",
            data={
                'action': action,
                **details
            },
            user_id=user_id,
            ip_address=ip_address
        )
    
    async def log_compliance_check(self, check_type: str, result: bool, details: Dict[str, Any]):
        """Log compliance checks"""
        return await self.log_event(
            AuditEventType.COMPLIANCE_CHECK,
            f"Compliance check ({check_type}): {'PASSED' if result else 'FAILED'}",
            data={
                'check_type': check_type,
                'result': result,
                **details
            },
            severity=AuditSeverity.WARNING if not result else AuditSeverity.INFO
        )
    
    async def search_events(self,
                          event_types: List[AuditEventType] = None,
                          start_time: float = None,
                          end_time: float = None,
                          user_id: str = None,
                          correlation_id: str = None,
                          severity: AuditSeverity = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Search audit events with filters"""
        
        query_parts = ["SELECT * FROM audit_logs WHERE 1=1"]
        params = []
        param_counter = 1
        
        # Build dynamic query
        if event_types:
            event_type_values = [et.value for et in event_types]
            query_parts.append(f"AND event_type = ANY(${param_counter})")
            params.append(event_type_values)
            param_counter += 1
        
        if start_time:
            query_parts.append(f"AND timestamp >= ${param_counter}")
            params.append(start_time)
            param_counter += 1
        
        if end_time:
            query_parts.append(f"AND timestamp <= ${param_counter}")
            params.append(end_time)
            param_counter += 1
        
        if user_id:
            query_parts.append(f"AND user_id = ${param_counter}")
            params.append(user_id)
            param_counter += 1
        
        if correlation_id:
            query_parts.append(f"AND correlation_id = ${param_counter}")
            params.append(correlation_id)
            param_counter += 1
        
        if severity:
            query_parts.append(f"AND severity = ${param_counter}")
            params.append(severity.value)
            param_counter += 1
        
        query_parts.append(f"ORDER BY timestamp DESC LIMIT ${param_counter}")
        params.append(limit)
        
        query = " ".join(query_parts)
        
        try:
            async with self.postgres_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                
                return [
                    {
                        **dict(row),
                        'data': json.loads(row['data']) if row['data'] else {}
                    }
                    for row in rows
                ]
        
        except Exception as e:
            logger.error(f"Error searching audit events: {e}")
            return []
    
    async def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get specific audit event by ID"""
        try:
            async with self.postgres_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM audit_logs WHERE event_id = $1",
                    event_id
                )
                
                if row:
                    return {
                        **dict(row),
                        'data': json.loads(row['data']) if row['data'] else {}
                    }
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting audit event {event_id}: {e}")
            return None
    
    async def get_statistics(self, start_time: float = None, end_time: float = None) -> Dict[str, Any]:
        """Get audit statistics"""
        try:
            query_parts = [
                """
                SELECT 
                    event_type,
                    severity,
                    COUNT(*) as count
                FROM audit_logs 
                WHERE 1=1
                """
            ]
            params = []
            param_counter = 1
            
            if start_time:
                query_parts.append(f"AND timestamp >= ${param_counter}")
                params.append(start_time)
                param_counter += 1
            
            if end_time:
                query_parts.append(f"AND timestamp <= ${param_counter}")
                params.append(end_time)
                param_counter += 1
            
            query_parts.append("GROUP BY event_type, severity ORDER BY count DESC")
            query = " ".join(query_parts)
            
            async with self.postgres_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                
                stats = {
                    'total_events': 0,
                    'by_type': {},
                    'by_severity': {},
                    'period': {
                        'start_time': start_time,
                        'end_time': end_time
                    }
                }
                
                for row in rows:
                    count = row['count']
                    event_type = row['event_type']
                    severity = row['severity']
                    
                    stats['total_events'] += count
                    
                    if event_type not in stats['by_type']:
                        stats['by_type'][event_type] = 0
                    stats['by_type'][event_type] += count
                    
                    if severity not in stats['by_severity']:
                        stats['by_severity'][severity] = 0
                    stats['by_severity'][severity] += count
                
                return stats
        
        except Exception as e:
            logger.error(f"Error getting audit statistics: {e}")
            return {
                'total_events': 0,
                'by_type': {},
                'by_severity': {},
                'error': str(e)
            }


# Export commonly used classes and functions
__all__ = [
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity"
]