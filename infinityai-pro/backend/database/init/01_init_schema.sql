-- InfinityAI.Pro Trading System Database Schema
-- Copyright 2025 InfinityAI.Pro

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create application user and database
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'infinityai_app') THEN
        CREATE ROLE infinityai_app LOGIN PASSWORD 'infinityai_app_secure';
    END IF;
END
$$;

-- Grant permissions
GRANT CONNECT ON DATABASE infinityai TO infinityai_app;
GRANT USAGE ON SCHEMA public TO infinityai_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO infinityai_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO infinityai_app;

-- ============================================================================
-- ACCOUNTS & USERS
-- ============================================================================

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_number VARCHAR(50) UNIQUE NOT NULL,
    broker_type VARCHAR(20) NOT NULL DEFAULT 'dhan',
    broker_account_id VARCHAR(100) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL DEFAULT 'INDIVIDUAL', -- INDIVIDUAL, CORPORATE, etc.
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, SUSPENDED, CLOSED
    risk_profile VARCHAR(20) NOT NULL DEFAULT 'MODERATE', -- CONSERVATIVE, MODERATE, AGGRESSIVE
    daily_max_loss DECIMAL(15,2) DEFAULT 10000.00,
    position_limit DECIMAL(15,2) DEFAULT 100000.00,
    max_position_size_percent DECIMAL(5,2) DEFAULT 80.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TRADING ENTITIES
-- ============================================================================

CREATE TABLE symbols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) UNIQUE NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    instrument_type VARCHAR(20) NOT NULL, -- EQUITY, OPTION, FUTURE, INDEX
    underlying_symbol VARCHAR(50),
    expiry_date DATE,
    strike_price DECIMAL(15,2),
    option_type VARCHAR(4), -- CALL, PUT
    lot_size INTEGER DEFAULT 1,
    tick_size DECIMAL(10,4) DEFAULT 0.01,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    symbol_id UUID NOT NULL REFERENCES symbols(id),
    position_type VARCHAR(10) NOT NULL, -- LONG, SHORT
    quantity INTEGER NOT NULL,
    avg_price DECIMAL(15,4) NOT NULL,
    current_price DECIMAL(15,4),
    unrealized_pnl DECIMAL(15,2) DEFAULT 0,
    realized_pnl DECIMAL(15,2) DEFAULT 0,
    stop_loss DECIMAL(15,4),
    target_price DECIMAL(15,4),
    status VARCHAR(20) DEFAULT 'OPEN', -- OPEN, CLOSED, PARTIAL
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- ORDERS & TRADES
-- ============================================================================

CREATE TABLE trade_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    idempotency_key VARCHAR(100) UNIQUE NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(id),
    symbol_id UUID NOT NULL REFERENCES symbols(id),
    order_type VARCHAR(20) NOT NULL, -- MARKET, LIMIT, STOP, STOP_LIMIT
    side VARCHAR(10) NOT NULL, -- BUY, SELL
    quantity INTEGER NOT NULL,
    price DECIMAL(15,4),
    stop_price DECIMAL(15,4),
    time_in_force VARCHAR(10) DEFAULT 'DAY', -- DAY, IOC, FOK, GTC
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, SUBMITTING, SUBMITTED, FILLED, PARTIAL, REJECTED, CANCELLED
    broker_order_id VARCHAR(100),
    filled_quantity INTEGER DEFAULT 0,
    avg_fill_price DECIMAL(15,4),
    commission DECIMAL(10,2) DEFAULT 0,
    rejection_reason TEXT,
    strategy_id UUID,
    signal_id VARCHAR(100),
    engine_name VARCHAR(20),
    metadata JSONB,
    submitted_at TIMESTAMP WITH TIME ZONE,
    filled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE trade_fills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trade_request_id UUID NOT NULL REFERENCES trade_requests(id),
    broker_fill_id VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    commission DECIMAL(10,2) DEFAULT 0,
    fill_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- RISK MANAGEMENT
-- ============================================================================

CREATE TABLE risk_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    limit_type VARCHAR(50) NOT NULL, -- DAILY_LOSS, POSITION_SIZE, SYMBOL_EXPOSURE, SECTOR_EXPOSURE
    limit_value DECIMAL(15,2) NOT NULL,
    current_value DECIMAL(15,2) DEFAULT 0,
    warning_threshold DECIMAL(5,2) DEFAULT 80.00, -- Percentage
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE stop_loss_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    position_id UUID NOT NULL REFERENCES positions(id),
    stop_price DECIMAL(15,4) NOT NULL,
    order_type VARCHAR(20) DEFAULT 'STOP_MARKET', -- STOP_MARKET, STOP_LIMIT
    limit_price DECIMAL(15,4),
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, TRIGGERED, CANCELLED
    broker_order_id VARCHAR(100),
    triggered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SIGNALS & STRATEGIES
-- ============================================================================

CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id VARCHAR(100) UNIQUE NOT NULL,
    symbol_id UUID NOT NULL REFERENCES symbols(id),
    signal_type VARCHAR(20) NOT NULL, -- BUY_CALL, SELL_PUT, LONG, SHORT
    confidence DECIMAL(5,4) NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    target_price DECIMAL(15,4),
    stop_loss DECIMAL(15,4),
    quantity INTEGER,
    strategy_name VARCHAR(100),
    engine_name VARCHAR(20) NOT NULL,
    metadata JSONB,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL, -- MOMENTUM, MEAN_REVERSION, ARBITRAGE
    is_active BOOLEAN DEFAULT TRUE,
    max_positions INTEGER DEFAULT 5,
    max_capital DECIMAL(15,2) DEFAULT 100000.00,
    risk_per_trade DECIMAL(5,4) DEFAULT 0.02,
    parameters JSONB,
    performance_stats JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- MONITORING & LOGS
-- ============================================================================

CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_type VARCHAR(20) DEFAULT 'GAUGE', -- GAUGE, COUNTER, HISTOGRAM
    tags JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL, -- ORDER, POSITION, ACCOUNT, SYSTEM
    entity_id UUID,
    action VARCHAR(50) NOT NULL, -- CREATE, UPDATE, DELETE, EXECUTE
    user_id UUID,
    engine_name VARCHAR(20),
    old_values JSONB,
    new_values JSONB,
    metadata JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE error_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    context JSONB,
    engine_name VARCHAR(20),
    severity VARCHAR(20) DEFAULT 'ERROR', -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- RECONCILIATION
-- ============================================================================

CREATE TABLE broker_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    symbol VARCHAR(50) NOT NULL,
    broker_symbol VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    avg_price DECIMAL(15,4) NOT NULL,
    current_price DECIMAL(15,4),
    unrealized_pnl DECIMAL(15,2),
    broker_data JSONB,
    snapshot_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reconciliation_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_date DATE NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(id),
    total_positions_system INTEGER DEFAULT 0,
    total_positions_broker INTEGER DEFAULT 0,
    position_discrepancies INTEGER DEFAULT 0,
    total_balance_system DECIMAL(15,2) DEFAULT 0,
    total_balance_broker DECIMAL(15,2) DEFAULT 0,
    balance_difference DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, COMPLETED, FAILED
    discrepancies JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- CIRCUIT BREAKERS & KILL SWITCHES
-- ============================================================================

CREATE TABLE circuit_breakers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    breaker_type VARCHAR(50) NOT NULL, -- LATENCY, ERROR_RATE, LOSS_LIMIT, MANUAL
    threshold_value DECIMAL(15,4) NOT NULL,
    current_value DECIMAL(15,4) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'CLOSED', -- CLOSED, OPEN, HALF_OPEN
    failure_count INTEGER DEFAULT 0,
    last_failure TIMESTAMP WITH TIME ZONE,
    recovery_timeout INTEGER DEFAULT 60, -- seconds
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE kill_switches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    switch_type VARCHAR(50) NOT NULL, -- ACCOUNT, STRATEGY, SYMBOL, GLOBAL
    entity_id UUID, -- account_id, strategy_id, symbol_id, or NULL for global
    is_active BOOLEAN DEFAULT FALSE,
    reason TEXT,
    triggered_by VARCHAR(100), -- user_id or system
    triggered_at TIMESTAMP WITH TIME ZONE,
    cleared_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_trade_requests_idempotency ON trade_requests(idempotency_key);
CREATE INDEX idx_trade_requests_status ON trade_requests(status);
CREATE INDEX idx_trade_requests_account ON trade_requests(account_id);
CREATE INDEX idx_trade_requests_symbol ON trade_requests(symbol_id);
CREATE INDEX idx_trade_requests_created ON trade_requests(created_at);

CREATE INDEX idx_positions_account ON positions(account_id);
CREATE INDEX idx_positions_symbol ON positions(symbol_id);
CREATE INDEX idx_positions_status ON positions(status);

CREATE INDEX idx_signals_processed ON signals(processed);
CREATE INDEX idx_signals_created ON signals(created_at);
CREATE INDEX idx_signals_symbol ON signals(symbol_id);

CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- Time-series indexes
CREATE INDEX idx_system_metrics_name_time ON system_metrics(metric_name, timestamp);
CREATE INDEX idx_error_logs_created ON error_logs(created_at);

-- Composite indexes for complex queries
CREATE INDEX idx_positions_account_status ON positions(account_id, status);
CREATE INDEX idx_trade_requests_account_status ON trade_requests(account_id, status);

-- GIN indexes for JSONB columns
CREATE INDEX idx_trade_requests_metadata ON trade_requests USING GIN(metadata);
CREATE INDEX idx_signals_metadata ON signals USING GIN(metadata);
CREATE INDEX idx_strategies_parameters ON strategies USING GIN(parameters);

-- ============================================================================
-- TRIGGERS FOR AUTO-UPDATES
-- ============================================================================

-- Update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trade_requests_updated_at BEFORE UPDATE ON trade_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_risk_limits_updated_at BEFORE UPDATE ON risk_limits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_circuit_breakers_updated_at BEFORE UPDATE ON circuit_breakers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample account
INSERT INTO accounts (account_number, broker_account_id, account_name, daily_max_loss, position_limit) 
VALUES ('INF001', '1101302170', 'InfinityAI Test Account', 25000.00, 500000.00)
ON CONFLICT (account_number) DO NOTHING;

-- Insert sample symbols
INSERT INTO symbols (symbol, exchange, instrument_type, lot_size) VALUES
('NIFTY', 'NSE', 'INDEX', 1),
('BANKNIFTY', 'NSE', 'INDEX', 1),
('RELIANCE', 'NSE', 'EQUITY', 1),
('TCS', 'NSE', 'EQUITY', 1),
('INFY', 'NSE', 'EQUITY', 1),
('HDFCBANK', 'NSE', 'EQUITY', 1),
('ITC', 'NSE', 'EQUITY', 1),
('SBIN', 'NSE', 'EQUITY', 1)
ON CONFLICT (symbol) DO NOTHING;

-- Insert sample strategies
INSERT INTO strategies (name, description, strategy_type, parameters) VALUES
('Momentum Breakout', 'RSI and EMA based momentum strategy', 'MOMENTUM', '{"rsi_period": 14, "ema_fast": 9, "ema_slow": 21}'),
('Mean Reversion', 'Bollinger Bands mean reversion', 'MEAN_REVERSION', '{"bb_period": 20, "bb_std": 2.0}'),
('AI Ensemble', 'Multi-model AI predictions', 'AI_ENSEMBLE', '{"models": ["gpt4", "claude", "gemini"], "confidence_threshold": 0.7}')
ON CONFLICT (name) DO NOTHING;

-- Insert circuit breakers
INSERT INTO circuit_breakers (name, breaker_type, threshold_value) VALUES
('Daily Loss Limit', 'LOSS_LIMIT', 20000.00),
('Error Rate Threshold', 'ERROR_RATE', 5.00),
('Latency Threshold', 'LATENCY', 500.00),
('Broker Rejection Rate', 'REJECTION_RATE', 1.00)
ON CONFLICT (name) DO NOTHING;

COMMIT;