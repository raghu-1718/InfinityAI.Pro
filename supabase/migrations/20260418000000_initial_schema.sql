-- Enable pgcrypto for AES-256 encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- USERS TABLE
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uid TEXT UNIQUE NOT NULL, -- Firebase UID or external UID mapped
    email TEXT,
    display_name TEXT,
    photo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    dhan_connected BOOLEAN DEFAULT FALSE,
    dhan_client_id TEXT,
    settings JSONB DEFAULT '{}'::jsonb
);

-- USER CREDENTIALS (AES-256 Encrypted via pgcrypto)
-- We store the broker token encrypted using a symmetric key. 
-- The key will be provided via the backend logic or postgres secret.
CREATE TABLE IF NOT EXISTS public.user_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_uid TEXT NOT NULL REFERENCES public.users(uid) ON DELETE CASCADE,
    broker_client_id TEXT NOT NULL,
    -- Store encrypted binary data
    broker_access_token BYTEA NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_uid)
);

-- PORTFOLIOS TABLE
CREATE TABLE IF NOT EXISTS public.portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_uid TEXT NOT NULL REFERENCES public.users(uid) ON DELETE CASCADE,
    balance NUMERIC DEFAULT 0.0,
    currency TEXT DEFAULT 'INR',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- TRADES TABLE
CREATE TABLE IF NOT EXISTS public.trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_uid TEXT NOT NULL REFERENCES public.users(uid) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price NUMERIC NOT NULL,
    side TEXT NOT NULL, -- 'BUY' or 'SELL'
    status TEXT NOT NULL, -- 'PENDING', 'EXECUTED', 'FAILED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SIGNALS TABLE
CREATE TABLE IF NOT EXISTS public.signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_uid TEXT NOT NULL REFERENCES public.users(uid) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    signal_type TEXT NOT NULL, -- 'BUY', 'SELL', 'HOLD'
    confidence NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LOGS TABLE
CREATE TABLE IF NOT EXISTS public.logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ROW LEVEL SECURITY (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.signals ENABLE ROW LEVEL SECURITY;

-- Note: In a production environment with authenticated Supabase users, we would use auth.uid()
-- Here we'll create simple policies assuming backend access (service_role) bypasses RLS
CREATE POLICY "Users can view their own profile" 
    ON public.users FOR SELECT 
    USING (auth.uid()::text = uid);

CREATE POLICY "Users can update their own profile" 
    ON public.users FOR UPDATE 
    USING (auth.uid()::text = uid);

-- user_credentials is strictly private (only service_role can access via backend)
CREATE POLICY "Strictly private credentials" 
    ON public.user_credentials FOR ALL 
    USING (false);

CREATE POLICY "Users can view their trades" 
    ON public.trades FOR SELECT 
    USING (auth.uid()::text = user_uid);

CREATE POLICY "Users can view their portfolios" 
    ON public.portfolios FOR SELECT 
    USING (auth.uid()::text = user_uid);

CREATE POLICY "Users can view their signals" 
    ON public.signals FOR SELECT 
    USING (auth.uid()::text = user_uid);
