"""
Database connection utilities for InfinityAI.Pro
Handles PostgreSQL connections and provides both async and sync interfaces
"""

import os
import asyncio
import asyncpg
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
import structlog

logger = structlog.get_logger(__name__)

# Database configuration
DB_DSN = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/infinityai")

# Global connection pool
pool: Optional[asyncpg.pool.Pool] = None
sync_pool: Optional[ThreadedConnectionPool] = None


async def init_db_pool(min_size: int = 1, max_size: int = 20):
    """Initialize async database connection pool"""
    global pool
    try:
        pool = await asyncpg.create_pool(
            dsn=DB_DSN,
            min_size=min_size,
            max_size=max_size,
            command_timeout=60,
            server_settings={
                'jit': 'off',  # Disable JIT for better performance with small queries
            }
        )
        logger.info("Database connection pool initialized", min_size=min_size, max_size=max_size)
        return pool
    except Exception as e:
        logger.error("Failed to initialize database pool", error=str(e))
        raise


async def close_db_pool():
    """Close async database connection pool"""
    global pool
    if pool:
        await pool.close()
        pool = None
        logger.info("Database connection pool closed")


def init_sync_pool(min_conn: int = 1, max_conn: int = 20):
    """Initialize synchronous database connection pool for Celery"""
    global sync_pool
    try:
        sync_pool = ThreadedConnectionPool(
            minconn=min_conn,
            maxconn=max_conn,
            dsn=DB_DSN
        )
        logger.info("Sync database connection pool initialized", min_conn=min_conn, max_conn=max_conn)
        return sync_pool
    except Exception as e:
        logger.error("Failed to initialize sync database pool", error=str(e))
        raise


def close_sync_pool():
    """Close synchronous database connection pool"""
    global sync_pool
    if sync_pool:
        sync_pool.closeall()
        sync_pool = None
        logger.info("Sync database connection pool closed")


@asynccontextmanager
async def get_db_connection():
    """Get async database connection from pool"""
    if not pool:
        raise RuntimeError("Database pool not initialized")
    
    connection = None
    try:
        connection = await pool.acquire()
        yield connection
    finally:
        if connection:
            await pool.release(connection)


def get_sync_connection():
    """Get synchronous database connection for Celery tasks"""
    if not sync_pool:
        # Initialize sync pool if not already done
        init_sync_pool()
    
    return sync_pool.getconn()


def return_sync_connection(connection):
    """Return synchronous database connection to pool"""
    if sync_pool and connection:
        sync_pool.putconn(connection)


class DatabaseManager:
    """Database manager class with common operations"""
    
    @staticmethod
    async def execute_query(
        query: str,
        params: tuple = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Optional[Any]:
        """Execute a database query with optional fetch"""
        async with get_db_connection() as conn:
            try:
                if fetch_one:
                    result = await conn.fetchrow(query, *(params or ()))
                    return dict(result) if result else None
                elif fetch_all:
                    results = await conn.fetch(query, *(params or ()))
                    return [dict(row) for row in results]
                else:
                    return await conn.execute(query, *(params or ()))
            except Exception as e:
                logger.error("Database query failed", query=query, error=str(e))
                raise
    
    @staticmethod
    async def execute_transaction(operations: List[Dict[str, Any]]) -> List[Any]:
        """Execute multiple operations in a transaction"""
        async with get_db_connection() as conn:
            async with conn.transaction():
                results = []
                for op in operations:
                    query = op.get('query')
                    params = op.get('params', ())
                    fetch_one = op.get('fetch_one', False)
                    fetch_all = op.get('fetch_all', False)
                    
                    try:
                        if fetch_one:
                            result = await conn.fetchrow(query, *params)
                            results.append(dict(result) if result else None)
                        elif fetch_all:
                            result = await conn.fetch(query, *params)
                            results.append([dict(row) for row in result])
                        else:
                            result = await conn.execute(query, *params)
                            results.append(result)
                    except Exception as e:
                        logger.error("Transaction operation failed", query=query, error=str(e))
                        raise
                return results
    
    @staticmethod
    def execute_sync_query(
        query: str,
        params: tuple = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Optional[Any]:
        """Execute synchronous query for Celery tasks"""
        conn = None
        try:
            conn = get_sync_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cur.execute(query, params or ())
            
            if fetch_one:
                result = cur.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                results = cur.fetchall()
                return [dict(row) for row in results]
            else:
                conn.commit()
                return cur.rowcount
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error("Sync database query failed", query=query, error=str(e))
            raise
        finally:
            if conn:
                return_sync_connection(conn)


async def create_tables():
    """Create database tables from schema"""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")
    
    if not os.path.exists(schema_path):
        logger.error("Schema file not found", path=schema_path)
        return False
    
    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        async with get_db_connection() as conn:
            await conn.execute(schema_sql)
        
        logger.info("Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        return False


async def test_connection() -> bool:
    """Test database connection"""
    try:
        async with get_db_connection() as conn:
            result = await conn.fetchrow("SELECT 1 as test")
            return result and result['test'] == 1
    except Exception as e:
        logger.error("Database connection test failed", error=str(e))
        return False


# Health check function
async def get_database_health() -> Dict[str, Any]:
    """Get database health status"""
    try:
        if not pool:
            return {"status": "unhealthy", "error": "Database pool not initialized"}
        
        # Test connection
        is_connected = await test_connection()
        
        # Get pool stats
        pool_stats = {
            "size": pool.get_size(),
            "available": pool.get_idle_size(),
            "max_size": pool.get_max_size(),
            "min_size": pool.get_min_size()
        }
        
        if is_connected:
            return {
                "status": "healthy",
                "pool_stats": pool_stats,
                "connection_test": "passed"
            }
        else:
            return {
                "status": "unhealthy",
                "error": "Connection test failed",
                "pool_stats": pool_stats
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }