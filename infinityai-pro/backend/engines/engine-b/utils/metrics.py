"""
Metrics collection for Engine C
InfinityAI.Pro Trading Platform

Redis-backed metrics collection with Prometheus-compatible output
for monitoring trade execution, performance, and system health.
"""

import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

import aioredis

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Individual metric data point"""
    name: str
    value: Union[int, float]
    timestamp: float
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp,
            'tags': self.tags
        }


@dataclass
class HistogramBucket:
    """Histogram bucket for latency measurements"""
    le: float  # Less than or equal to
    count: int = 0


class MetricsCollector:
    """Metrics collection with Redis backend"""
    
    def __init__(self, redis_client: aioredis.Redis, retention_days: int = 7):
        self.redis = redis_client
        self.retention_days = retention_days
        self.retention_seconds = retention_days * 24 * 3600
        
        # Metric prefixes
        self.counter_prefix = "metrics:counter:"
        self.gauge_prefix = "metrics:gauge:"
        self.histogram_prefix = "metrics:histogram:"
        self.summary_prefix = "metrics:summary:"
        
        # Histogram buckets for latency measurements (in milliseconds)
        self.latency_buckets = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, float('inf')]
        
        # Background task for cleanup
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task for metric cleanup"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_old_metrics())
    
    async def _cleanup_old_metrics(self):
        """Cleanup old metrics periodically"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                cutoff_time = time.time() - self.retention_seconds
                
                # Get all metric keys
                patterns = [
                    f"{self.counter_prefix}*",
                    f"{self.gauge_prefix}*", 
                    f"{self.histogram_prefix}*",
                    f"{self.summary_prefix}*"
                ]
                
                for pattern in patterns:
                    async for key in self.redis.scan_iter(match=pattern):
                        try:
                            # Check if it's a time-series key
                            if ':ts:' in key.decode():
                                # Remove old timestamp entries
                                await self.redis.zremrangebyscore(key, 0, cutoff_time)
                                
                                # Remove empty sets
                                count = await self.redis.zcard(key)
                                if count == 0:
                                    await self.redis.delete(key)
                                    
                        except Exception as e:
                            logger.warning(f"Error cleaning up metric key {key}: {e}")
                            
            except Exception as e:
                logger.error(f"Error in metrics cleanup: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def _get_metric_key(self, metric_type: str, name: str, tags: Dict[str, str] = None) -> str:
        """Generate Redis key for metric"""
        prefix = getattr(self, f"{metric_type}_prefix")
        
        if tags:
            # Sort tags for consistent keys
            tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{prefix}{name}:{tag_str}"
        
        return f"{prefix}{name}"
    
    def _get_timeseries_key(self, metric_type: str, name: str, tags: Dict[str, str] = None) -> str:
        """Generate Redis key for time series metric"""
        base_key = self._get_metric_key(metric_type, name, tags)
        return f"{base_key}:ts"
    
    async def increment(self, name: str, value: int = 1, tags: Dict[str, str] = None) -> None:
        """Increment a counter metric"""
        try:
            key = self._get_metric_key("counter", name, tags)
            ts_key = self._get_timeseries_key("counter", name, tags)
            timestamp = time.time()
            
            # Increment counter
            await self.redis.incrby(key, value)
            
            # Add to time series
            await self.redis.zadd(ts_key, {str(timestamp): value})
            
            # Set expiry
            await self.redis.expire(key, self.retention_seconds)
            await self.redis.expire(ts_key, self.retention_seconds)
            
        except Exception as e:
            logger.error(f"Error incrementing counter {name}: {e}")
    
    async def gauge(self, name: str, value: Union[int, float], tags: Dict[str, str] = None) -> None:
        """Set a gauge metric"""
        try:
            key = self._get_metric_key("gauge", name, tags)
            ts_key = self._get_timeseries_key("gauge", name, tags)
            timestamp = time.time()
            
            # Set gauge value
            await self.redis.set(key, value)
            
            # Add to time series
            await self.redis.zadd(ts_key, {str(timestamp): value})
            
            # Set expiry
            await self.redis.expire(key, self.retention_seconds)
            await self.redis.expire(ts_key, self.retention_seconds)
            
        except Exception as e:
            logger.error(f"Error setting gauge {name}: {e}")
    
    async def histogram(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record a histogram value (typically for latencies)"""
        try:
            timestamp = time.time()
            
            # Update histogram buckets
            for bucket_le in self.latency_buckets:
                if value <= bucket_le:
                    bucket_tags = (tags or {}).copy()
                    bucket_tags['le'] = str(bucket_le)
                    
                    bucket_key = self._get_metric_key("histogram", f"{name}_bucket", bucket_tags)
                    await self.redis.incrby(bucket_key, 1)
                    await self.redis.expire(bucket_key, self.retention_seconds)
            
            # Count total observations
            count_key = self._get_metric_key("histogram", f"{name}_count", tags)
            await self.redis.incrby(count_key, 1)
            await self.redis.expire(count_key, self.retention_seconds)
            
            # Sum of all observations
            sum_key = self._get_metric_key("histogram", f"{name}_sum", tags)
            await self.redis.incrbyfloat(sum_key, value)
            await self.redis.expire(sum_key, self.retention_seconds)
            
            # Add to time series
            ts_key = self._get_timeseries_key("histogram", name, tags)
            await self.redis.zadd(ts_key, {str(timestamp): value})
            await self.redis.expire(ts_key, self.retention_seconds)
            
        except Exception as e:
            logger.error(f"Error recording histogram {name}: {e}")
    
    async def timing(self, name: str, duration_ms: float, tags: Dict[str, str] = None) -> None:
        """Record timing information (convenience method for histogram)"""
        await self.histogram(name, duration_ms, tags)
    
    async def get_counter(self, name: str, tags: Dict[str, str] = None) -> int:
        """Get counter value"""
        try:
            key = self._get_metric_key("counter", name, tags)
            value = await self.redis.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"Error getting counter {name}: {e}")
            return 0
    
    async def get_gauge(self, name: str, tags: Dict[str, str] = None) -> Optional[float]:
        """Get gauge value"""
        try:
            key = self._get_metric_key("gauge", name, tags)
            value = await self.redis.get(key)
            return float(value) if value else None
        except Exception as e:
            logger.error(f"Error getting gauge {name}: {e}")
            return None
    
    async def get_histogram_stats(self, name: str, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Get histogram statistics"""
        try:
            count_key = self._get_metric_key("histogram", f"{name}_count", tags)
            sum_key = self._get_metric_key("histogram", f"{name}_sum", tags)
            
            count = await self.redis.get(count_key)
            total_sum = await self.redis.get(sum_key)
            
            count = int(count) if count else 0
            total_sum = float(total_sum) if total_sum else 0.0
            
            # Calculate average
            avg = total_sum / count if count > 0 else 0
            
            # Get percentiles from time series
            ts_key = self._get_timeseries_key("histogram", name, tags)
            values = await self.redis.zrangebyscore(ts_key, 0, time.time())
            
            percentiles = {}
            if values:
                float_values = sorted([float(v) for v in values])
                percentiles = {
                    'p50': self._percentile(float_values, 50),
                    'p90': self._percentile(float_values, 90),
                    'p95': self._percentile(float_values, 95),
                    'p99': self._percentile(float_values, 99)
                }
            
            return {
                'count': count,
                'sum': total_sum,
                'average': avg,
                **percentiles
            }
            
        except Exception as e:
            logger.error(f"Error getting histogram stats {name}: {e}")
            return {'count': 0, 'sum': 0.0, 'average': 0.0}
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values"""
        if not values:
            return 0.0
        
        k = (len(values) - 1) * percentile / 100.0
        f = int(k)
        c = k - f
        
        if f == len(values) - 1:
            return values[f]
        else:
            return values[f] * (1 - c) + values[f + 1] * c
    
    async def get_time_series(self, metric_type: str, name: str, tags: Dict[str, str] = None, 
                            start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get time series data for a metric"""
        try:
            ts_key = self._get_timeseries_key(metric_type, name, tags)
            
            start_time = start_time or (time.time() - 3600)  # Last hour by default
            end_time = end_time or time.time()
            
            # Get time series data
            data = await self.redis.zrangebyscore(ts_key, start_time, end_time, withscores=True)
            
            return [
                {
                    'timestamp': float(score),
                    'value': float(value),
                    'datetime': datetime.fromtimestamp(float(score), tz=timezone.utc).isoformat()
                }
                for value, score in data
            ]
            
        except Exception as e:
            logger.error(f"Error getting time series {name}: {e}")
            return []
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values"""
        try:
            result = {
                'counters': {},
                'gauges': {},
                'histograms': {},
                'timestamp': time.time()
            }
            
            # Get all counter keys
            async for key in self.redis.scan_iter(match=f"{self.counter_prefix}*"):
                key_str = key.decode()
                if ':ts' not in key_str:  # Skip time series keys
                    metric_name = key_str[len(self.counter_prefix):]
                    value = await self.redis.get(key)
                    result['counters'][metric_name] = int(value) if value else 0
            
            # Get all gauge keys
            async for key in self.redis.scan_iter(match=f"{self.gauge_prefix}*"):
                key_str = key.decode()
                if ':ts' not in key_str:  # Skip time series keys
                    metric_name = key_str[len(self.gauge_prefix):]
                    value = await self.redis.get(key)
                    result['gauges'][metric_name] = float(value) if value else 0.0
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all metrics: {e}")
            return {'counters': {}, 'gauges': {}, 'histograms': {}, 'timestamp': time.time()}
    
    async def get_trade_metrics(self) -> Dict[str, Any]:
        """Get trade-specific metrics"""
        try:
            now = time.time()
            hour_ago = now - 3600
            
            metrics = {
                'trades_submitted_total': await self.get_counter('trades_submitted_total'),
                'trades_rejected_total': await self.get_counter('trades_rejected_total'),
                'trades_failed_total': await self.get_counter('trades_failed_total'),
                'signals_processed_total': await self.get_counter('signals_processed_total'),
                'signal_processing_errors_total': await self.get_counter('signal_processing_errors_total'),
                'pre_trade_validations_failed': await self.get_counter('pre_trade_validations_failed'),
                'kill_switch_activations': await self.get_counter('kill_switch_activations'),
                'circuit_breaker_trips': await self.get_counter('circuit_breaker_trips'),
                'broker_api_calls_total': await self.get_counter('broker_api_calls_total'),
                'broker_api_errors_total': await self.get_counter('broker_api_errors_total'),
                
                # Current gauge values
                'active_positions': await self.get_gauge('active_positions'),
                'total_exposure': await self.get_gauge('total_exposure'),
                'available_margin': await self.get_gauge('available_margin'),
                'daily_pnl': await self.get_gauge('daily_pnl'),
                
                # Performance metrics
                'trade_execution_latency': await self.get_histogram_stats('trade_execution_latency'),
                'signal_processing_latency': await self.get_histogram_stats('signal_processing_latency'),
                'broker_api_latency': await self.get_histogram_stats('broker_api_latency'),
                
                'timestamp': now
            }
            
            # Calculate success rates
            total_trades = metrics['trades_submitted_total'] + metrics['trades_rejected_total'] + metrics['trades_failed_total']
            if total_trades > 0:
                metrics['trade_success_rate'] = metrics['trades_submitted_total'] / total_trades * 100
                metrics['trade_rejection_rate'] = metrics['trades_rejected_total'] / total_trades * 100
                metrics['trade_failure_rate'] = metrics['trades_failed_total'] / total_trades * 100
            else:
                metrics['trade_success_rate'] = 0.0
                metrics['trade_rejection_rate'] = 0.0
                metrics['trade_failure_rate'] = 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting trade metrics: {e}")
            return {}
    
    async def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        try:
            lines = []
            lines.append("# Trade Execution Engine Metrics")
            lines.append("")
            
            # Get all metrics
            all_metrics = await self.get_all_metrics()
            
            # Counters
            for name, value in all_metrics['counters'].items():
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")
                lines.append("")
            
            # Gauges
            for name, value in all_metrics['gauges'].items():
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {value}")
                lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error exporting Prometheus format: {e}")
            return "# Error exporting metrics"
    
    async def record_trade_submitted(self, symbol: str, quantity: int, price: float):
        """Record successful trade submission"""
        await self.increment('trades_submitted_total', tags={'symbol': symbol})
        await self.increment('trade_volume_shares', quantity, tags={'symbol': symbol})
        await self.gauge('last_trade_price', price, tags={'symbol': symbol})
    
    async def record_trade_rejected(self, symbol: str, reason: str):
        """Record trade rejection"""
        await self.increment('trades_rejected_total', tags={'symbol': symbol, 'reason': reason})
    
    async def record_trade_failed(self, symbol: str, error_type: str):
        """Record trade failure"""
        await self.increment('trades_failed_total', tags={'symbol': symbol, 'error_type': error_type})
    
    async def record_signal_processed(self, signal_type: str, processing_time_ms: float):
        """Record signal processing"""
        await self.increment('signals_processed_total', tags={'signal_type': signal_type})
        await self.histogram('signal_processing_latency', processing_time_ms, tags={'signal_type': signal_type})
    
    async def record_validation_failure(self, validation_type: str, reason: str):
        """Record pre-trade validation failure"""
        await self.increment('pre_trade_validations_failed', 
                           tags={'validation_type': validation_type, 'reason': reason})
    
    async def record_kill_switch_activation(self, switch_type: str):
        """Record kill switch activation"""
        await self.increment('kill_switch_activations', tags={'switch_type': switch_type})
    
    async def record_circuit_breaker_trip(self, breaker_name: str):
        """Record circuit breaker trip"""
        await self.increment('circuit_breaker_trips', tags={'breaker_name': breaker_name})
    
    async def record_broker_api_call(self, endpoint: str, duration_ms: float, status_code: int):
        """Record broker API call"""
        tags = {'endpoint': endpoint, 'status_code': str(status_code)}
        await self.increment('broker_api_calls_total', tags=tags)
        await self.histogram('broker_api_latency', duration_ms, tags=tags)
        
        if status_code >= 400:
            await self.increment('broker_api_errors_total', tags=tags)
    
    async def update_position_metrics(self, active_positions: int, total_exposure: float):
        """Update position-related metrics"""
        await self.gauge('active_positions', active_positions)
        await self.gauge('total_exposure', total_exposure)
    
    async def update_pnl_metrics(self, daily_pnl: float, total_pnl: float):
        """Update P&L metrics"""
        await self.gauge('daily_pnl', daily_pnl)
        await self.gauge('total_pnl', total_pnl)
    
    async def update_margin_metrics(self, available_margin: float, used_margin: float):
        """Update margin metrics"""
        await self.gauge('available_margin', available_margin)
        await self.gauge('used_margin', used_margin)
        
        if available_margin + used_margin > 0:
            margin_utilization = used_margin / (available_margin + used_margin) * 100
            await self.gauge('margin_utilization_percent', margin_utilization)


# Export commonly used classes
__all__ = [
    "MetricsCollector",
    "MetricPoint", 
    "HistogramBucket"
]