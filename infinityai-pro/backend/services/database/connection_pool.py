"""
Database Connection Pool Service for InfinityAI.Pro
Provides optimized connection pooling for Amazon Keyspaces (Cassandra) with Redis caching
"""

import os
import ssl
import logging
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy
from cassandra.connection import Connection
from cassandra import ConsistencyLevel
from cassandra.query import SimpleStatement, PreparedStatement
from typing import Dict, List, Optional, Any, Union
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import time
from datetime import datetime, timedelta
from services.cache.redis_service import cache
from services.security.azure_keyvault import config
import json

logger = logging.getLogger(__name__)

class CassandraConnectionPool:
    def __init__(self):
        # Database configuration from environment/Key Vault
        self.username = config.get("CASSANDRA_USERNAME") or os.getenv("CASSANDRA_USERNAME")
        self.password = config.get("CASSANDRA_PASSWORD") or os.getenv("CASSANDRA_PASSWORD")
        self.hosts = config.get("CASSANDRA_HOSTS", "cassandra.us-east-1.amazonaws.com:9142").split(",")
        self.keyspace = config.get("CASSANDRA_KEYSPACE", "infinityai_keyspace")
        self.port = int(config.get("CASSANDRA_PORT", "9142"))
        
        # Connection pool settings
        self.pool_size = config.get_int("DB_POOL_SIZE", 10)
        self.pool_timeout = config.get_int("DB_POOL_TIMEOUT", 30)
        self.pool_recycle = config.get_int("DB_POOL_RECYCLE", 3600)
        
        # Connection management
        self.cluster = None
        self.session = None
        self.prepared_statements = {}
        self.connection_lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=self.pool_size)
        self.last_health_check = 0
        self.health_check_interval = 60  # 1 minute
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Cassandra cluster connection with SSL and authentication"""
        try:
            if not self.username or not self.password:
                logger.error("❌ Cassandra credentials not provided")
                return False
            
            # SSL Context for Amazon Keyspaces
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Authentication
            auth_provider = PlainTextAuthProvider(username=self.username, password=self.password)
            
            # Load balancing policy
            load_balancing_policy = TokenAwarePolicy(DCAwareRoundRobinPolicy())
            
            # Create cluster
            self.cluster = Cluster(
                contact_points=self.hosts,
                port=self.port,
                auth_provider=auth_provider,
                ssl_context=ssl_context,
                load_balancing_policy=load_balancing_policy,
                protocol_version=4,
                compression=True,
                control_connection_timeout=10,
                connect_timeout=10,
                max_schema_agreement_wait=30,
            )
            
            # Create session
            self.session = self.cluster.connect()
            
            # Set keyspace
            if self.keyspace:
                self.session.set_keyspace(self.keyspace)
            
            # Set default consistency level
            self.session.default_consistency_level = ConsistencyLevel.LOCAL_QUORUM
            
            logger.info(f"✅ Cassandra connection pool initialized - Pool size: {self.pool_size}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cassandra connection: {e}")
            self.cluster = None
            self.session = None
            return False
    
    def is_connected(self) -> bool:
        """Check if database connection is active"""
        if not self.session:
            return False
        
        # Perform periodic health check
        current_time = time.time()
        if current_time - self.last_health_check > self.health_check_interval:
            try:
                # Simple query to check connection
                self.session.execute("SELECT now() FROM system.local LIMIT 1", timeout=5)
                self.last_health_check = current_time
                return True
            except Exception as e:
                logger.warning(f"⚠️ Database health check failed: {e}")
                return False
        
        return True
    
    def reconnect(self) -> bool:
        """Reconnect to database if connection is lost"""
        logger.info("🔄 Attempting to reconnect to Cassandra...")
        
        with self.connection_lock:
            # Close existing connections
            if self.session:
                try:
                    self.session.shutdown()
                except:
                    pass
            
            if self.cluster:
                try:
                    self.cluster.shutdown()
                except:
                    pass
            
            # Re-initialize connection
            return self._initialize_connection()
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic reconnection"""
        if not self.is_connected():
            if not self.reconnect():
                raise Exception("Unable to establish database connection")
        
        yield self.session
    
    def execute_query(self, query: Union[str, SimpleStatement, PreparedStatement], parameters: Optional[Dict] = None, use_cache: bool = False, cache_ttl: int = 300) -> Optional[List[Dict]]:
        """Execute query with caching support"""
        
        # Generate cache key if caching is enabled
        cache_key = None
        if use_cache:
            cache_key = f"query:{hash(str(query) + str(parameters))}"
            cached_result = cache.get(cache_key, "database")
            if cached_result:
                logger.debug(f"🎯 Database query cache hit: {cache_key}")
                return cached_result
        
        try:
            with self.get_session() as session:
                if isinstance(query, str):
                    query = SimpleStatement(query)
                
                if parameters:
                    result = session.execute(query, parameters)
                else:
                    result = session.execute(query)
                
                # Convert to list of dictionaries
                rows = []
                if result:
                    columns = result.column_names if hasattr(result, 'column_names') else []
                    for row in result:
                        if columns:
                            rows.append(dict(zip(columns, row)))
                        else:
                            rows.append(dict(row._asdict()) if hasattr(row, '_asdict') else row)
                
                # Cache result if caching is enabled
                if use_cache and cache_key:
                    cache.set(cache_key, rows, cache_ttl, "database")
                    logger.debug(f"💾 Cached database query result: {cache_key}")
                
                return rows
                
        except Exception as e:
            logger.error(f"❌ Database query failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            
            # Try to reconnect on connection errors
            if "connection" in str(e).lower():
                self.reconnect()
            
            return None
    
    def execute_batch(self, queries: List[tuple], use_transaction: bool = False) -> bool:
        """Execute multiple queries in batch"""
        try:
            with self.get_session() as session:
                if use_transaction:
                    # Use BatchStatement for atomic operations
                    from cassandra.query import BatchStatement
                    batch = BatchStatement(consistency_level=ConsistencyLevel.LOCAL_QUORUM)
                    
                    for query, params in queries:
                        if isinstance(query, str):
                            query = SimpleStatement(query)
                        batch.add(query, params or {})
                    
                    session.execute(batch)
                else:
                    # Execute queries individually
                    for query, params in queries:
                        session.execute(query, params or {})
                
                logger.info(f"✅ Executed batch of {len(queries)} queries")
                return True
                
        except Exception as e:
            logger.error(f"❌ Batch query execution failed: {e}")
            return False
    
    def prepare_statement(self, query: str, statement_id: str) -> bool:
        """Prepare and cache a statement for better performance"""
        try:
            with self.get_session() as session:
                prepared = session.prepare(query)
                self.prepared_statements[statement_id] = prepared
                logger.info(f"✅ Prepared statement cached: {statement_id}")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to prepare statement {statement_id}: {e}")
            return False
    
    def execute_prepared(self, statement_id: str, parameters: Dict, use_cache: bool = False, cache_ttl: int = 300) -> Optional[List[Dict]]:
        """Execute prepared statement with caching"""
        if statement_id not in self.prepared_statements:
            logger.error(f"❌ Prepared statement not found: {statement_id}")
            return None
        
        prepared_statement = self.prepared_statements[statement_id]
        return self.execute_query(prepared_statement, parameters, use_cache, cache_ttl)
    
    async def execute_async(self, query: Union[str, SimpleStatement], parameters: Optional[Dict] = None) -> Optional[List[Dict]]:
        """Execute query asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.execute_query,
            query,
            parameters
        )
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        try:
            stats = {
                "pool_size": self.pool_size,
                "connected": self.is_connected(),
                "keyspace": self.keyspace,
                "hosts": self.hosts,
                "prepared_statements": len(self.prepared_statements),
                "last_health_check": datetime.fromtimestamp(self.last_health_check).isoformat() if self.last_health_check else None
            }
            
            if self.cluster and self.session:
                # Get cluster metadata
                stats.update({
                    "cluster_name": getattr(self.cluster.metadata, 'cluster_name', 'N/A'),
                    "protocol_version": getattr(self.session, 'protocol_version', 'N/A'),
                    "compression": getattr(self.cluster, 'compression', 'N/A')
                })
            
            return stats
        except Exception as e:
            logger.error(f"❌ Error getting pool stats: {e}")
            return {"error": str(e), "connected": False}
    
    def shutdown(self):
        """Gracefully shutdown the connection pool"""
        logger.info("🔄 Shutting down Cassandra connection pool...")
        
        try:
            if self.executor:
                self.executor.shutdown(wait=True)
            
            if self.session:
                self.session.shutdown()
            
            if self.cluster:
                self.cluster.shutdown()
            
            logger.info("✅ Cassandra connection pool shut down successfully")
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

# Global connection pool instance
db_pool = CassandraConnectionPool()

class DatabaseService:
    """High-level database service with caching and optimization"""
    
    @staticmethod
    def create_keyspace_if_not_exists():
        """Create keyspace if it doesn't exist"""
        try:
            # Connect without keyspace
            temp_session = db_pool.cluster.connect()
            
            keyspace_query = f"""
            CREATE KEYSPACE IF NOT EXISTS {db_pool.keyspace}
            WITH REPLICATION = {{
                'class': 'SingleRegionStrategy'
            }}
            """
            
            temp_session.execute(keyspace_query)
            temp_session.shutdown()
            
            logger.info(f"✅ Keyspace {db_pool.keyspace} created/verified")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create keyspace: {e}")
            return False
    
    @staticmethod
    def create_tables():
        """Create application tables"""
        tables = {
            "trading_signals": """
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id UUID PRIMARY KEY,
                    symbol TEXT,
                    signal_type TEXT,
                    confidence FLOAT,
                    price DECIMAL,
                    timestamp TIMESTAMP,
                    metadata TEXT,
                    created_at TIMESTAMP
                )
            """,
            "user_positions": """
                CREATE TABLE IF NOT EXISTS user_positions (
                    user_id UUID,
                    symbol TEXT,
                    position_type TEXT,
                    quantity DECIMAL,
                    avg_price DECIMAL,
                    current_value DECIMAL,
                    pnl DECIMAL,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    PRIMARY KEY (user_id, symbol)
                )
            """,
            "ai_predictions": """
                CREATE TABLE IF NOT EXISTS ai_predictions (
                    id UUID PRIMARY KEY,
                    symbol TEXT,
                    model_name TEXT,
                    prediction_type TEXT,
                    predicted_price DECIMAL,
                    confidence FLOAT,
                    features TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """,
            "market_data_cache": """
                CREATE TABLE IF NOT EXISTS market_data_cache (
                    symbol TEXT,
                    data_type TEXT,
                    interval TEXT,
                    data TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    PRIMARY KEY (symbol, data_type, interval)
                )
            """
        }
        
        success_count = 0
        for table_name, create_query in tables.items():
            try:
                db_pool.execute_query(create_query)
                logger.info(f"✅ Table {table_name} created/verified")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to create table {table_name}: {e}")
        
        logger.info(f"📊 Database initialization: {success_count}/{len(tables)} tables created")
        return success_count == len(tables)
    
    @staticmethod
    def store_trading_signal(symbol: str, signal_type: str, confidence: float, price: float, metadata: Dict = None):
        """Store trading signal in database"""
        import uuid
        from datetime import datetime
        
        query = """
        INSERT INTO trading_signals (id, symbol, signal_type, confidence, price, timestamp, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        parameters = {
            "id": uuid.uuid4(),
            "symbol": symbol,
            "signal_type": signal_type,
            "confidence": confidence,
            "price": price,
            "timestamp": datetime.utcnow(),
            "metadata": json.dumps(metadata) if metadata else "{}",
            "created_at": datetime.utcnow()
        }
        
        result = db_pool.execute_query(query, parameters)
        return result is not None
    
    @staticmethod
    def get_recent_signals(symbol: str = None, limit: int = 100, use_cache: bool = True) -> List[Dict]:
        """Get recent trading signals"""
        if symbol:
            query = "SELECT * FROM trading_signals WHERE symbol = ? LIMIT ?"
            parameters = {"symbol": symbol, "limit": limit}
        else:
            query = "SELECT * FROM trading_signals LIMIT ?"
            parameters = {"limit": limit}
        
        return db_pool.execute_query(query, parameters, use_cache=use_cache, cache_ttl=300) or []

# Initialize prepared statements
def initialize_prepared_statements():
    """Initialize commonly used prepared statements"""
    statements = {
        "insert_signal": """
            INSERT INTO trading_signals (id, symbol, signal_type, confidence, price, timestamp, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        "get_user_positions": "SELECT * FROM user_positions WHERE user_id = ?",
        "update_position": """
            UPDATE user_positions SET quantity = ?, avg_price = ?, current_value = ?, pnl = ?, updated_at = ?
            WHERE user_id = ? AND symbol = ?
        """,
        "get_predictions": "SELECT * FROM ai_predictions WHERE symbol = ? AND expires_at > ? LIMIT ?"
    }
    
    success_count = 0
    for stmt_id, query in statements.items():
        if db_pool.prepare_statement(query, stmt_id):
            success_count += 1
    
    logger.info(f"📝 Prepared statements: {success_count}/{len(statements)} cached")

# Health check function
async def health_check():
    """Health check for database service"""
    try:
        stats = db_pool.get_pool_stats()
        if stats.get("connected"):
            return {
                "service": "cassandra_pool",
                "status": "healthy",
                "stats": stats
            }
        else:
            return {
                "service": "cassandra_pool",
                "status": "unhealthy",
                "error": "Database connection failed",
                "stats": stats
            }
    except Exception as e:
        return {
            "service": "cassandra_pool",
            "status": "unhealthy",
            "error": str(e)
        }

# Initialization function
async def initialize_database():
    """Initialize database with keyspace and tables"""
    logger.info("🗄️ Initializing database...")
    
    # Create keyspace
    DatabaseService.create_keyspace_if_not_exists()
    
    # Create tables
    DatabaseService.create_tables()
    
    # Initialize prepared statements
    initialize_prepared_statements()
    
    logger.info("✅ Database initialization completed")