"""
Broker connection management for InfinityAI.Pro
Handles broker token storage, validation, and management with encryption
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional, Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import structlog

from .database import DatabaseManager
from .crypto import TokenEncryption
from .auth import get_current_active_user
from .schemas import (
    BrokerIn, BrokerOut, BrokerUpdateIn, BrokerValidationResult,
    APIResponse, BrokerStatus, TradingAccountOut
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/brokers", tags=["Broker Management"])


class BrokerManager:
    """Broker connection manager class"""
    
    @staticmethod
    async def create_broker_connection(
        user_id: UUID, 
        broker_data: BrokerIn
    ) -> dict:
        """Create new broker connection with encrypted token"""
        try:
            # Encrypt the broker token
            encrypted_token, token_iv = TokenEncryption.encrypt_token(broker_data.token)
            
            # Insert broker connection
            query = """
                INSERT INTO broker_connections 
                (user_id, broker_name, encrypted_token, token_iv, expiry_timestamp, metadata, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id, broker_name) 
                DO UPDATE SET 
                    encrypted_token = EXCLUDED.encrypted_token,
                    token_iv = EXCLUDED.token_iv,
                    expiry_timestamp = EXCLUDED.expiry_timestamp,
                    metadata = EXCLUDED.metadata,
                    status = 'pending',
                    validation_attempts = 0,
                    updated_at = now()
                RETURNING id, broker_name, status, expiry_timestamp, last_validated_at, 
                         validation_attempts, created_at, updated_at, metadata
            """
            
            result = await DatabaseManager.execute_query(
                query, (
                    user_id,
                    broker_data.broker_name,
                    encrypted_token,
                    token_iv,
                    broker_data.expiry_timestamp,
                    broker_data.metadata,
                    BrokerStatus.PENDING
                ),
                fetch_one=True
            )
            
            if result:
                logger.info(
                    "Broker connection created/updated", 
                    user_id=user_id, 
                    broker=broker_data.broker_name,
                    connection_id=result['id']
                )
            
            return result
            
        except Exception as e:
            logger.error("Failed to create broker connection", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create broker connection"
            )
    
    @staticmethod
    async def get_user_brokers(user_id: UUID) -> List[dict]:
        """Get all broker connections for a user"""
        query = """
            SELECT id, broker_name, status, expiry_timestamp, last_validated_at,
                   validation_attempts, created_at, updated_at, metadata
            FROM broker_connections 
            WHERE user_id = $1 
            ORDER BY created_at DESC
        """
        
        results = await DatabaseManager.execute_query(
            query, (user_id,), fetch_all=True
        )
        
        return results or []
    
    @staticmethod
    async def get_broker_by_id(broker_id: UUID, user_id: UUID) -> Optional[dict]:
        """Get specific broker connection by ID"""
        query = """
            SELECT id, user_id, broker_name, encrypted_token, token_iv, status, 
                   expiry_timestamp, last_validated_at, validation_attempts, 
                   created_at, updated_at, metadata
            FROM broker_connections 
            WHERE id = $1 AND user_id = $2
        """
        
        return await DatabaseManager.execute_query(
            query, (broker_id, user_id), fetch_one=True
        )
    
    @staticmethod
    async def update_broker_connection(
        broker_id: UUID, 
        user_id: UUID, 
        update_data: BrokerUpdateIn
    ) -> Optional[dict]:
        """Update broker connection"""
        try:
            # Build update query dynamically
            set_clauses = []
            params = []
            param_count = 1
            
            if update_data.token is not None:
                # Encrypt new token
                encrypted_token, token_iv = TokenEncryption.encrypt_token(update_data.token)
                set_clauses.extend([
                    f"encrypted_token = ${param_count}",
                    f"token_iv = ${param_count + 1}",
                    f"status = ${param_count + 2}",
                    f"validation_attempts = ${param_count + 3}"
                ])
                params.extend([encrypted_token, token_iv, BrokerStatus.PENDING, 0])
                param_count += 4
            
            if update_data.expiry_timestamp is not None:
                set_clauses.append(f"expiry_timestamp = ${param_count}")
                params.append(update_data.expiry_timestamp)
                param_count += 1
            
            if update_data.metadata is not None:
                set_clauses.append(f"metadata = ${param_count}")
                params.append(update_data.metadata)
                param_count += 1
            
            if not set_clauses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No update data provided"
                )
            
            # Add WHERE clause parameters
            params.extend([broker_id, user_id])
            
            query = f"""
                UPDATE broker_connections 
                SET {', '.join(set_clauses)}, updated_at = now()
                WHERE id = ${param_count} AND user_id = ${param_count + 1}
                RETURNING id, broker_name, status, expiry_timestamp, last_validated_at,
                         validation_attempts, created_at, updated_at, metadata
            """
            
            result = await DatabaseManager.execute_query(
                query, tuple(params), fetch_one=True
            )
            
            if result:
                logger.info("Broker connection updated", broker_id=broker_id, user_id=user_id)
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to update broker connection", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update broker connection"
            )
    
    @staticmethod
    async def delete_broker_connection(broker_id: UUID, user_id: UUID) -> bool:
        """Delete broker connection"""
        try:
            query = """
                DELETE FROM broker_connections 
                WHERE id = $1 AND user_id = $2
            """
            
            result = await DatabaseManager.execute_query(query, (broker_id, user_id))
            
            if result and "DELETE 1" in str(result):
                logger.info("Broker connection deleted", broker_id=broker_id, user_id=user_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to delete broker connection", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete broker connection"
            )
    
    @staticmethod
    async def get_decrypted_token(broker_id: UUID, user_id: UUID) -> Optional[str]:
        """Get decrypted broker token (for internal use only)"""
        try:
            query = """
                SELECT encrypted_token, token_iv 
                FROM broker_connections 
                WHERE id = $1 AND user_id = $2
            """
            
            result = await DatabaseManager.execute_query(
                query, (broker_id, user_id), fetch_one=True
            )
            
            if result and result['encrypted_token']:
                return TokenEncryption.decrypt_token(
                    result['encrypted_token'], 
                    result.get('token_iv')
                )
            
            return None
            
        except Exception as e:
            logger.error("Failed to decrypt broker token", error=str(e))
            return None
    
    @staticmethod
    async def update_broker_status(
        broker_id: UUID,
        status: BrokerStatus,
        validation_message: Optional[str] = None,
        account_info: Optional[dict] = None
    ) -> bool:
        """Update broker connection status and validation info"""
        try:
            # Prepare metadata update
            metadata_update = {}
            if validation_message:
                metadata_update['last_validation_message'] = validation_message
            if account_info:
                metadata_update['account_info'] = account_info
            
            query = """
                UPDATE broker_connections 
                SET status = $1, 
                    last_validated_at = $2,
                    validation_attempts = validation_attempts + 1,
                    metadata = COALESCE(metadata, '{}'::jsonb) || $3::jsonb
                WHERE id = $4
            """
            
            await DatabaseManager.execute_query(
                query, (status, datetime.utcnow(), metadata_update, broker_id)
            )
            
            logger.info("Broker status updated", broker_id=broker_id, status=status)
            return True
            
        except Exception as e:
            logger.error("Failed to update broker status", error=str(e))
            return False
    
    @staticmethod
    async def get_expired_connections() -> List[dict]:
        """Get broker connections that have expired"""
        query = """
            SELECT id, user_id, broker_name, expiry_timestamp
            FROM broker_connections 
            WHERE expiry_timestamp IS NOT NULL 
            AND expiry_timestamp < now()
            AND status != 'expired'
        """
        
        return await DatabaseManager.execute_query(query, fetch_all=True) or []
    
    @staticmethod
    async def mark_expired_connections() -> int:
        """Mark expired broker connections"""
        try:
            query = """
                UPDATE broker_connections 
                SET status = 'expired', updated_at = now()
                WHERE expiry_timestamp IS NOT NULL 
                AND expiry_timestamp < now()
                AND status != 'expired'
            """
            
            result = await DatabaseManager.execute_query(query)
            count = int(result.split()[1]) if result and "UPDATE" in result else 0
            
            if count > 0:
                logger.info("Marked expired broker connections", count=count)
            
            return count
            
        except Exception as e:
            logger.error("Failed to mark expired connections", error=str(e))
            return 0


class BrokerValidator:
    """Broker validation utilities"""
    
    @staticmethod
    async def validate_dhan_token(token: str) -> tuple[bool, str, Optional[dict]]:
        """Validate Dhan broker token"""
        try:
            # Import your existing Dhan integration
            from dhanhq import dhanhq
            
            # Test the token with a simple API call
            dhan = dhanhq(user_id="", access_token=token)
            
            # Try to get account info
            account_info = dhan.get_account_data()
            
            if account_info and not account_info.get('error'):
                return True, "Token validated successfully", {
                    "account_id": account_info.get("account_id"),
                    "client_name": account_info.get("client_name"),
                    "balance": account_info.get("balance")
                }
            else:
                return False, "Invalid token or account access denied", None
                
        except Exception as e:
            return False, f"Validation failed: {str(e)}", None
    
    @staticmethod
    async def validate_broker_token(broker_name: str, token: str) -> tuple[bool, str, Optional[dict]]:
        """Generic broker token validation"""
        try:
            if broker_name == "dhan":
                return await BrokerValidator.validate_dhan_token(token)
            elif broker_name == "zerodha":
                # Implement Zerodha validation
                return await BrokerValidator.validate_zerodha_token(token)
            elif broker_name == "upstox":
                # Implement Upstox validation
                return await BrokerValidator.validate_upstox_token(token)
            else:
                # Mock validation for unsupported brokers
                return await BrokerValidator.mock_validation(token)
                
        except Exception as e:
            logger.error("Broker validation failed", broker=broker_name, error=str(e))
            return False, f"Validation error: {str(e)}", None
    
    @staticmethod
    async def validate_zerodha_token(token: str) -> tuple[bool, str, Optional[dict]]:
        """Validate Zerodha broker token (placeholder)"""
        # Implement Zerodha KiteConnect validation
        return False, "Zerodha validation not implemented yet", None
    
    @staticmethod
    async def validate_upstox_token(token: str) -> tuple[bool, str, Optional[dict]]:
        """Validate Upstox broker token (placeholder)"""
        # Implement Upstox validation
        return False, "Upstox validation not implemented yet", None
    
    @staticmethod
    async def mock_validation(token: str) -> tuple[bool, str, Optional[dict]]:
        """Mock validation for testing"""
        if len(token) > 10:  # Simple mock validation
            return True, "Mock validation successful", {"account_id": "MOCK123", "balance": 10000.0}
        else:
            return False, "Token too short", None


# API Endpoints
@router.post("/", response_model=BrokerOut, status_code=status.HTTP_201_CREATED)
async def add_broker_connection(
    broker_data: BrokerIn,
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Add new broker connection"""
    try:
        # Create broker connection
        broker = await BrokerManager.create_broker_connection(
            current_user["id"], broker_data
        )
        
        if broker:
            # Schedule Celery validation task
            from .tasks import validate_broker_token
            validate_broker_token.delay(str(broker["id"]), broker_data.broker_name)
        
        return BrokerOut(**broker)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add broker connection", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add broker connection"
        )


@router.get("/", response_model=List[BrokerOut])
async def get_broker_connections(
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Get all broker connections for current user"""
    brokers = await BrokerManager.get_user_brokers(current_user["id"])
    return [BrokerOut(**broker) for broker in brokers]


@router.get("/{broker_id}", response_model=BrokerOut)
async def get_broker_connection(
    broker_id: UUID,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Get specific broker connection"""
    broker = await BrokerManager.get_broker_by_id(broker_id, current_user["id"])
    
    if not broker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker connection not found"
        )
    
    # Remove sensitive fields
    broker_data = {k: v for k, v in broker.items() 
                   if k not in ['encrypted_token', 'token_iv']}
    
    return BrokerOut(**broker_data)


@router.put("/{broker_id}", response_model=BrokerOut)
async def update_broker_connection(
    broker_id: UUID,
    update_data: BrokerUpdateIn,
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Update broker connection"""
    # Check if broker exists
    existing_broker = await BrokerManager.get_broker_by_id(broker_id, current_user["id"])
    if not existing_broker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker connection not found"
        )
    
    # Update broker
    broker = await BrokerManager.update_broker_connection(
        broker_id, current_user["id"], update_data
    )
    
    if broker and update_data.token:
        # Schedule validation for updated token
        from .tasks import validate_broker_token
        validate_broker_token.delay(str(broker_id), existing_broker["broker_name"])
    
    return BrokerOut(**broker)


@router.delete("/{broker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_broker_connection(
    broker_id: UUID,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Delete broker connection"""
    success = await BrokerManager.delete_broker_connection(broker_id, current_user["id"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker connection not found"
        )


@router.post("/{broker_id}/validate", response_model=BrokerValidationResult)
async def manually_validate_broker(
    broker_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Manually trigger broker validation"""
    broker = await BrokerManager.get_broker_by_id(broker_id, current_user["id"])
    
    if not broker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker connection not found"
        )
    
    # Schedule immediate validation
    from .tasks import validate_broker_token
    validate_broker_token.delay(str(broker_id), broker["broker_name"])
    
    return BrokerValidationResult(
        broker_id=broker_id,
        status=BrokerStatus.PENDING,
        message="Validation scheduled",
        validated_at=datetime.utcnow()
    )


# Note: Broker validation is now handled by Celery tasks in tasks.py


@router.get("/health")
async def broker_health():
    """Broker service health check"""
    try:
        # Test database connectivity
        test_query = "SELECT COUNT(*) as count FROM broker_connections LIMIT 1"
        result = await DatabaseManager.execute_query(test_query, fetch_one=True)
        
        # Test encryption
        from .crypto import get_crypto_health
        crypto_health = get_crypto_health()
        
        return {
            "status": "healthy" if crypto_health["status"] == "healthy" else "degraded",
            "service": "broker_management",
            "database_test": "passed" if result is not None else "failed",
            "encryption_test": crypto_health["status"],
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "broker_management",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }