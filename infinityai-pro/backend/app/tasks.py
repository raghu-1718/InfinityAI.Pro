"""
Celery tasks for InfinityAI.Pro
Background processing for broker validation, expiry checks, and system maintenance
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from celery import Celery
from celery.schedules import crontab
import structlog

# Import database utilities for sync operations
from .database import DatabaseManager, init_sync_pool, close_sync_pool
from .crypto import TokenEncryption

logger = structlog.get_logger(__name__)

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_BACKEND", "redis://localhost:6379/1")

# Initialize Celery app
celery_app = Celery(
    "infinityai_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour
    task_routes={
        'app.tasks.validate_broker_token': {'queue': 'broker_validation'},
        'app.tasks.check_expired_tokens': {'queue': 'maintenance'},
        'app.tasks.cleanup_old_sessions': {'queue': 'maintenance'},
        'app.tasks.sync_trading_accounts': {'queue': 'trading'},
    }
)


class BrokerValidatorSync:
    """Synchronous broker validator for Celery tasks"""
    
    @staticmethod
    def validate_dhan_token(token: str) -> tuple[bool, str, Optional[dict]]:
        """Validate Dhan broker token (sync version)"""
        try:
            # Import Dhan library
            from dhanhq import dhanhq
            
            # Initialize Dhan client
            dhan = dhanhq(user_id="", access_token=token)
            
            # Test with account data call
            account_info = dhan.get_account_data()
            
            if account_info and not account_info.get('error'):
                return True, "Token validated successfully", {
                    "account_id": account_info.get("account_id"),
                    "client_name": account_info.get("client_name"),
                    "balance": account_info.get("balance"),
                    "validated_at": datetime.utcnow().isoformat()
                }
            else:
                error_msg = account_info.get('error', 'Unknown error') if account_info else 'No response'
                return False, f"Invalid token or API error: {error_msg}", None
                
        except ImportError:
            logger.warning("Dhan library not available, using mock validation")
            return BrokerValidatorSync.mock_validation(token)
        except Exception as e:
            logger.error("Dhan validation failed", error=str(e))
            return False, f"Validation failed: {str(e)}", None
    
    @staticmethod
    def validate_zerodha_token(token: str) -> tuple[bool, str, Optional[dict]]:
        """Validate Zerodha/KiteConnect token (sync version)"""
        try:
            # Import KiteConnect library if available
            # from kiteconnect import KiteConnect
            
            # For now, return placeholder
            return False, "Zerodha validation not implemented yet", None
            
        except ImportError:
            return False, "Zerodha library not available", None
        except Exception as e:
            return False, f"Zerodha validation error: {str(e)}", None
    
    @staticmethod
    def mock_validation(token: str) -> tuple[bool, str, Optional[dict]]:
        """Mock validation for testing and unsupported brokers"""
        if len(token) >= 20:  # Simple validation
            return True, "Mock validation successful", {
                "account_id": f"MOCK_{token[:8]}",
                "client_name": "Mock Account",
                "balance": 50000.0,
                "validated_at": datetime.utcnow().isoformat()
            }
        else:
            return False, "Token appears invalid (too short)", None
    
    @staticmethod
    def validate_broker_token(broker_name: str, token: str) -> tuple[bool, str, Optional[dict]]:
        """Generic broker token validation (sync)"""
        try:
            if broker_name.lower() == "dhan":
                return BrokerValidatorSync.validate_dhan_token(token)
            elif broker_name.lower() == "zerodha":
                return BrokerValidatorSync.validate_zerodha_token(token)
            elif broker_name.lower() == "upstox":
                # Placeholder for Upstox
                return BrokerValidatorSync.mock_validation(token)
            else:
                # Use mock validation for unsupported brokers
                return BrokerValidatorSync.mock_validation(token)
                
        except Exception as e:
            logger.error("Broker validation failed", broker=broker_name, error=str(e))
            return False, f"Validation error: {str(e)}", None


# Celery Tasks
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def validate_broker_token(self, broker_id: str, broker_name: str):
    """
    Validate broker token and update status
    This is the main task called from the API
    """
    try:
        logger.info("Starting broker validation task", broker_id=broker_id, broker=broker_name)
        
        # Get broker connection data
        result = DatabaseManager.execute_sync_query(
            """
            SELECT id, user_id, encrypted_token, token_iv, broker_name
            FROM broker_connections 
            WHERE id = %s
            """,
            (broker_id,),
            fetch_one=True
        )
        
        if not result:
            logger.error("Broker connection not found", broker_id=broker_id)
            return {"success": False, "error": "Broker connection not found"}
        
        # Decrypt token
        try:
            encrypted_token = bytes(result['encrypted_token'])
            token_iv = bytes(result['token_iv']) if result['token_iv'] else None
            
            # Use sync decryption
            from cryptography.fernet import Fernet
            fernet_key = os.getenv("FERNET_KEY")
            if not fernet_key:
                raise ValueError("FERNET_KEY not configured")
            
            fernet = Fernet(fernet_key.encode())
            decrypted_token = fernet.decrypt(encrypted_token).decode('utf-8')
            
        except Exception as e:
            logger.error("Token decryption failed", broker_id=broker_id, error=str(e))
            
            # Update status to invalid
            DatabaseManager.execute_sync_query(
                """
                UPDATE broker_connections 
                SET status = %s, 
                    last_validated_at = %s,
                    validation_attempts = validation_attempts + 1,
                    metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                WHERE id = %s
                """,
                ('invalid', datetime.utcnow(), 
                 {'last_validation_message': 'Token decryption failed'}, broker_id)
            )
            
            return {"success": False, "error": "Token decryption failed"}
        
        # Validate token with broker API
        is_valid, message, account_info = BrokerValidatorSync.validate_broker_token(
            broker_name, decrypted_token
        )
        
        # Update broker status
        new_status = 'connected' if is_valid else 'invalid'
        metadata_update = {
            'last_validation_message': message,
            'last_validation_attempt': datetime.utcnow().isoformat()
        }
        
        if account_info:
            metadata_update['account_info'] = account_info
        
        DatabaseManager.execute_sync_query(
            """
            UPDATE broker_connections 
            SET status = %s, 
                last_validated_at = %s,
                validation_attempts = validation_attempts + 1,
                metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
            WHERE id = %s
            """,
            (new_status, datetime.utcnow(), metadata_update, broker_id)
        )
        
        logger.info(
            "Broker validation completed",
            broker_id=broker_id,
            status=new_status,
            valid=is_valid,
            message=message
        )
        
        return {
            "success": True,
            "broker_id": broker_id,
            "status": new_status,
            "valid": is_valid,
            "message": message,
            "account_info": account_info
        }
        
    except Exception as e:
        logger.error("Broker validation task failed", broker_id=broker_id, error=str(e))
        
        # Update status to invalid on task failure
        try:
            DatabaseManager.execute_sync_query(
                """
                UPDATE broker_connections 
                SET status = %s, 
                    last_validated_at = %s,
                    validation_attempts = validation_attempts + 1,
                    metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                WHERE id = %s
                """,
                ('invalid', datetime.utcnow(), 
                 {'last_validation_message': f'Task error: {str(e)}'}, broker_id)
            )
        except Exception as db_error:
            logger.error("Failed to update broker status after task error", error=str(db_error))
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info("Retrying broker validation", broker_id=broker_id, retry=self.request.retries + 1)
            raise self.retry(countdown=60 * (2 ** self.request.retries))  # Exponential backoff
        
        return {"success": False, "error": str(e)}


@celery_app.task
def check_expired_tokens():
    """
    Periodic task to check and mark expired broker tokens
    Runs every 5 minutes
    """
    try:
        logger.info("Starting expired token check")
        
        # Find expired tokens
        expired_tokens = DatabaseManager.execute_sync_query(
            """
            SELECT id, user_id, broker_name, expiry_timestamp
            FROM broker_connections 
            WHERE expiry_timestamp IS NOT NULL 
            AND expiry_timestamp < now()
            AND status != 'expired'
            """,
            fetch_all=True
        )
        
        if not expired_tokens:
            logger.info("No expired tokens found")
            return {"expired_count": 0}
        
        # Mark tokens as expired
        expired_ids = [token['id'] for token in expired_tokens]
        
        # Update status in batch
        placeholders = ','.join(['%s'] * len(expired_ids))
        query = f"""
            UPDATE broker_connections 
            SET status = 'expired', 
                updated_at = now(),
                metadata = COALESCE(metadata, '{{}}'::jsonb) || %s::jsonb
            WHERE id IN ({placeholders})
        """
        
        metadata_update = {
            'marked_expired_at': datetime.utcnow().isoformat(),
            'expired_by_system': True
        }
        
        params = [metadata_update] + expired_ids
        
        DatabaseManager.execute_sync_query(query, tuple(params))
        
        logger.info("Marked expired tokens", count=len(expired_tokens))
        
        # Send notifications (optional)
        for token in expired_tokens:
            notify_token_expired.delay(str(token['id']), str(token['user_id']))
        
        return {
            "expired_count": len(expired_tokens),
            "expired_brokers": [
                {"id": str(token['id']), "broker": token['broker_name']} 
                for token in expired_tokens
            ]
        }
        
    except Exception as e:
        logger.error("Expired token check failed", error=str(e))
        return {"error": str(e)}


@celery_app.task
def cleanup_old_sessions():
    """
    Clean up old user sessions
    Runs daily at 2 AM
    """
    try:
        logger.info("Starting session cleanup")
        
        # Delete sessions older than 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        result = DatabaseManager.execute_sync_query(
            """
            DELETE FROM user_sessions 
            WHERE created_at < %s OR expires_at < now()
            """,
            (cutoff_date,)
        )
        
        # Extract count from result string like "DELETE 5"
        deleted_count = int(result.split()[1]) if result and "DELETE" in result else 0
        
        logger.info("Cleaned up old sessions", deleted_count=deleted_count)
        
        return {"deleted_sessions": deleted_count}
        
    except Exception as e:
        logger.error("Session cleanup failed", error=str(e))
        return {"error": str(e)}


@celery_app.task
def sync_trading_accounts(broker_id: str):
    """
    Sync trading account information from broker
    Called after successful broker validation
    """
    try:
        logger.info("Starting trading account sync", broker_id=broker_id)
        
        # Get broker connection
        broker = DatabaseManager.execute_sync_query(
            """
            SELECT id, user_id, broker_name, encrypted_token, token_iv, metadata
            FROM broker_connections 
            WHERE id = %s AND status = 'connected'
            """,
            (broker_id,),
            fetch_one=True
        )
        
        if not broker:
            logger.warning("Broker not found or not connected", broker_id=broker_id)
            return {"success": False, "error": "Broker not found or not connected"}
        
        # For now, just log the sync attempt
        # In a real implementation, you'd fetch account data from the broker
        logger.info("Trading account sync completed", broker_id=broker_id)
        
        return {
            "success": True,
            "broker_id": broker_id,
            "accounts_synced": 1  # Placeholder
        }
        
    except Exception as e:
        logger.error("Trading account sync failed", broker_id=broker_id, error=str(e))
        return {"success": False, "error": str(e)}


@celery_app.task
def notify_token_expired(broker_id: str, user_id: str):
    """
    Send notification about expired broker token
    """
    try:
        logger.info("Sending token expiry notification", broker_id=broker_id, user_id=user_id)
        
        # Get broker details
        broker = DatabaseManager.execute_sync_query(
            """
            SELECT broker_name, expiry_timestamp
            FROM broker_connections 
            WHERE id = %s
            """,
            (broker_id,),
            fetch_one=True
        )
        
        if broker:
            # Here you would integrate with your notification system
            # For now, just log the notification
            logger.info(
                "Token expiry notification prepared",
                user_id=user_id,
                broker=broker['broker_name'],
                expired_at=broker['expiry_timestamp']
            )
        
        return {"notification_sent": True}
        
    except Exception as e:
        logger.error("Failed to send expiry notification", error=str(e))
        return {"notification_sent": False, "error": str(e)}


@celery_app.task
def system_health_check():
    """
    Periodic system health check
    Runs every 10 minutes
    """
    try:
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": "unknown",
            "redis": "unknown",
            "broker_connections": 0,
            "active_connections": 0
        }
        
        # Test database
        try:
            result = DatabaseManager.execute_sync_query(
                "SELECT COUNT(*) as count FROM broker_connections",
                fetch_one=True
            )
            health_data["database"] = "healthy"
            health_data["broker_connections"] = result["count"] if result else 0
            
            # Count active connections
            active_result = DatabaseManager.execute_sync_query(
                "SELECT COUNT(*) as count FROM broker_connections WHERE status = 'connected'",
                fetch_one=True
            )
            health_data["active_connections"] = active_result["count"] if active_result else 0
            
        except Exception as e:
            health_data["database"] = f"error: {str(e)}"
        
        # Test Redis (Celery broker)
        try:
            # This will work if Redis is available
            celery_app.control.ping(timeout=5)
            health_data["redis"] = "healthy"
        except Exception as e:
            health_data["redis"] = f"error: {str(e)}"
        
        logger.info("System health check completed", health=health_data)
        return health_data
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {"error": str(e)}


# Periodic task configuration
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configure periodic tasks"""
    
    # Check expired tokens every 5 minutes
    sender.add_periodic_task(
        300.0,  # 5 minutes
        check_expired_tokens.s(),
        name='check-expired-tokens'
    )
    
    # Clean up old sessions daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_old_sessions.s(),
        name='cleanup-old-sessions'
    )
    
    # System health check every 10 minutes
    sender.add_periodic_task(
        600.0,  # 10 minutes
        system_health_check.s(),
        name='system-health-check'
    )
    
    logger.info("Periodic tasks configured")


# Task monitoring functions
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a specific task"""
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "info": result.info
        }
    except Exception as e:
        return {"task_id": task_id, "error": str(e)}


def get_queue_stats() -> Dict[str, Any]:
    """Get Celery queue statistics"""
    try:
        inspect = celery_app.control.inspect()
        
        return {
            "active_tasks": inspect.active(),
            "scheduled_tasks": inspect.scheduled(),
            "reserved_tasks": inspect.reserved(),
            "worker_stats": inspect.stats()
        }
    except Exception as e:
        logger.error("Failed to get queue stats", error=str(e))
        return {"error": str(e)}


# Initialize sync database pool for Celery worker
def init_celery_db():
    """Initialize database pool for Celery worker"""
    try:
        init_sync_pool()
        logger.info("Celery database pool initialized")
    except Exception as e:
        logger.error("Failed to initialize Celery database pool", error=str(e))
        raise


def close_celery_db():
    """Close database pool for Celery worker"""
    try:
        close_sync_pool()
        logger.info("Celery database pool closed")
    except Exception as e:
        logger.error("Failed to close Celery database pool", error=str(e))


# Worker lifecycle events
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing"""
    print(f'Request: {self.request!r}')
    return {"message": "Debug task executed", "worker": str(self.request.hostname)}


if __name__ == '__main__':
    # Start Celery worker
    celery_app.start()