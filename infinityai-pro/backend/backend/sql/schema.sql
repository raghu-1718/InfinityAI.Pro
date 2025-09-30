-- InfinityAI.Pro Database Schema
-- User Authentication and Broker Connection Management

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Broker connections table for encrypted token storage
CREATE TABLE IF NOT EXISTS broker_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    broker_name TEXT NOT NULL, -- dhan, zerodha, upstox, etc.
    encrypted_token BYTEA NOT NULL,
    token_iv BYTEA,
    expiry_timestamp TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL DEFAULT 'pending', -- pending | connected | expired | invalid | disabled
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_validated_at TIMESTAMP WITH TIME ZONE,
    validation_attempts INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb, -- store additional broker-specific data
    UNIQUE(user_id, broker_name) -- one connection per broker per user
);

-- User sessions for JWT token management
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    is_revoked BOOLEAN DEFAULT false,
    user_agent TEXT,
    ip_address INET
);

-- Trading accounts linked to broker connections
CREATE TABLE IF NOT EXISTS trading_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    broker_connection_id UUID REFERENCES broker_connections(id) ON DELETE CASCADE,
    account_id TEXT NOT NULL, -- broker's account identifier
    account_name TEXT,
    account_type TEXT, -- equity, commodity, currency, etc.
    balance DECIMAL(15,2) DEFAULT 0.00,
    available_margin DECIMAL(15,2) DEFAULT 0.00,
    used_margin DECIMAL(15,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_synced_at TIMESTAMP WITH TIME ZONE
);

-- Audit log for security tracking
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    details JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_broker_connections_user_id ON broker_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_broker_connections_status ON broker_connections(status);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_trading_accounts_user_id ON trading_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_broker_connections_updated_at BEFORE UPDATE ON broker_connections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_trading_accounts_updated_at BEFORE UPDATE ON trading_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();