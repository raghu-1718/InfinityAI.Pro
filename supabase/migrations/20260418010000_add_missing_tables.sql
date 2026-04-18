-- Migration: Add tables required by Engine A/B/C Supabase migration
-- This adds tables that the migrated Python services now depend on.

-- =====================================================
-- TRADING SESSIONS (Engine-A SessionManager)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.trading_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    active BOOLEAN DEFAULT FALSE,
    started_at TEXT,
    stopped_at TEXT,
    last_heartbeat TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- =====================================================
-- CIRCUIT BREAKER STATE (Engine-A CircuitBreaker)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.circuit_breaker_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    consecutive_losses INTEGER DEFAULT 0,
    session_pnl NUMERIC DEFAULT 0.0,
    halted BOOLEAN DEFAULT FALSE,
    halt_reason TEXT,
    updated_at TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- =====================================================
-- COUPONS (Engine-C CouponAuthManager)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.coupons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    type TEXT DEFAULT 'standard',
    max_uses INTEGER DEFAULT 1,
    current_uses INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- COUPON SESSIONS (Engine-C CouponAuthManager)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.coupon_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    coupon_code TEXT NOT NULL,
    session_token TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    activated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =====================================================
-- LIVE PRICES (Engine-C WebSocketManager)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.live_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    security_id TEXT,
    ltp NUMERIC,
    open_price NUMERIC,
    high_price NUMERIC,
    low_price NUMERIC,
    close_price NUMERIC,
    volume BIGINT,
    exchange TEXT,
    timestamp TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- FIX: Update logs table to match migrated code columns
-- The migrated code writes: user_id, type, description, severity, timestamp, metadata
-- =====================================================
ALTER TABLE public.logs ADD COLUMN IF NOT EXISTS user_id TEXT;
ALTER TABLE public.logs ADD COLUMN IF NOT EXISTS type TEXT;
ALTER TABLE public.logs ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE public.logs ADD COLUMN IF NOT EXISTS severity TEXT;
ALTER TABLE public.logs ADD COLUMN IF NOT EXISTS "timestamp" TEXT;
-- Rename 'level' and 'message' are kept for backwards compatibility

-- =====================================================
-- FIX: Update signals table to match Engine-B code columns
-- Engine-B writes: user_id, symbol, stored_at, timestamp, + dynamic fields
-- =====================================================
ALTER TABLE public.signals ADD COLUMN IF NOT EXISTS user_id TEXT;
ALTER TABLE public.signals ADD COLUMN IF NOT EXISTS stored_at TEXT;
ALTER TABLE public.signals ADD COLUMN IF NOT EXISTS "timestamp" TEXT;
ALTER TABLE public.signals ADD COLUMN IF NOT EXISTS signal TEXT;
ALTER TABLE public.signals ADD COLUMN IF NOT EXISTS confidence_score NUMERIC;
ALTER TABLE public.signals ADD COLUMN IF NOT EXISTS predicted_price NUMERIC;
ALTER TABLE public.signals ADD COLUMN IF NOT EXISTS current_price NUMERIC;
ALTER TABLE public.signals ADD COLUMN IF NOT EXISTS stop_loss NUMERIC;
ALTER TABLE public.signals ADD COLUMN IF NOT EXISTS target NUMERIC;
ALTER TABLE public.signals ADD COLUMN IF NOT EXISTS model_version TEXT;
ALTER TABLE public.signals ADD COLUMN IF NOT EXISTS analysis JSONB;

-- =====================================================
-- FIX: Update trades table to match Engine-C super_order_api columns
-- =====================================================
ALTER TABLE public.trades ADD COLUMN IF NOT EXISTS user_id TEXT;
ALTER TABLE public.trades ADD COLUMN IF NOT EXISTS order_id TEXT;
ALTER TABLE public.trades ADD COLUMN IF NOT EXISTS order_type TEXT;
ALTER TABLE public.trades ADD COLUMN IF NOT EXISTS exchange_segment TEXT;
ALTER TABLE public.trades ADD COLUMN IF NOT EXISTS security_id TEXT;
ALTER TABLE public.trades ADD COLUMN IF NOT EXISTS product_type TEXT;
ALTER TABLE public.trades ADD COLUMN IF NOT EXISTS validity TEXT;
ALTER TABLE public.trades ADD COLUMN IF NOT EXISTS legs JSONB;
ALTER TABLE public.trades ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- =====================================================
-- GREEKS DATA (Engine-C OptionsAnalytics)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.greeks_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    expiry TEXT,
    strike NUMERIC,
    option_type TEXT, -- 'CE' or 'PE'
    delta NUMERIC,
    gamma NUMERIC,
    theta NUMERIC,
    vega NUMERIC,
    implied_volatility NUMERIC,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =====================================================
-- RLS for new tables
-- =====================================================
ALTER TABLE public.trading_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.circuit_breaker_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coupons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coupon_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.live_prices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.greeks_data ENABLE ROW LEVEL SECURITY;

-- Backend services use service_role key which bypasses RLS
-- These policies are for direct frontend access (if needed)
CREATE POLICY "Service role full access trading_sessions"
    ON public.trading_sessions FOR ALL
    USING (false);

CREATE POLICY "Service role full access circuit_breaker_state"
    ON public.circuit_breaker_state FOR ALL
    USING (false);

CREATE POLICY "Public read coupons"
    ON public.coupons FOR SELECT
    USING (is_active = true);

CREATE POLICY "Service role full access coupon_sessions"
    ON public.coupon_sessions FOR ALL
    USING (false);

CREATE POLICY "Public read live_prices"
    ON public.live_prices FOR SELECT
    USING (true);

CREATE POLICY "Public read greeks_data"
    ON public.greeks_data FOR SELECT
    USING (true);

-- =====================================================
-- INDEXES for performance
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_trading_sessions_user ON public.trading_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_circuit_breaker_user ON public.circuit_breaker_state(user_id);
CREATE INDEX IF NOT EXISTS idx_coupon_sessions_user ON public.coupon_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_live_prices_symbol ON public.live_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_logs_user ON public.logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_type ON public.logs(type);
CREATE INDEX IF NOT EXISTS idx_signals_user ON public.signals(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_user ON public.trades(user_id);
CREATE INDEX IF NOT EXISTS idx_greeks_symbol ON public.greeks_data(symbol);
