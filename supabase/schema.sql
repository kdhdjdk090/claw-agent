-- =============================================================================
-- CLAW AI — Supabase Database Schema
-- Full auth + user management + plans + admin system
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. PLANS — subscription tiers
-- =============================================================================
CREATE TABLE IF NOT EXISTS plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,           -- 'free', 'pro', 'ultrathink', 'enterprise'
    display_name TEXT NOT NULL,
    description TEXT,
    price_monthly NUMERIC(10,2) DEFAULT 0,
    price_yearly NUMERIC(10,2) DEFAULT 0,
    -- Limits
    max_tokens_per_day BIGINT DEFAULT 50000,
    max_tokens_per_month BIGINT DEFAULT 1000000,
    max_sessions INTEGER DEFAULT 10,
    max_turns_per_session INTEGER DEFAULT 50,
    max_tools INTEGER DEFAULT 10,
    max_models INTEGER DEFAULT 1,
    -- Features
    council_access BOOLEAN DEFAULT FALSE,
    cloud_models BOOLEAN DEFAULT FALSE,
    ultrathink_mode BOOLEAN DEFAULT FALSE,
    mcp_access BOOLEAN DEFAULT FALSE,
    priority_support BOOLEAN DEFAULT FALSE,
    custom_skills BOOLEAN DEFAULT FALSE,
    api_access BOOLEAN DEFAULT FALSE,
    -- Allowed models (JSON array of model name patterns)
    allowed_models JSONB DEFAULT '["deepseek-v3.1:671b-cloud"]'::jsonb,
    -- Allowed tools (JSON array, null = all tools)
    allowed_tools JSONB DEFAULT NULL,
    -- Meta
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 2. USER PROFILES — extends Supabase auth.users
-- =============================================================================
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    display_name TEXT,
    avatar_url TEXT,
    plan_id UUID REFERENCES plans(id),
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'superadmin')),
    -- Usage tracking
    tokens_used_today BIGINT DEFAULT 0,
    tokens_used_month BIGINT DEFAULT 0,
    total_tokens_used BIGINT DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    total_turns INTEGER DEFAULT 0,
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    -- Preferences
    preferred_model TEXT,
    auto_approve BOOLEAN DEFAULT FALSE,
    theme TEXT DEFAULT 'light',
    -- Timestamps
    last_active TIMESTAMPTZ,
    tokens_reset_at TIMESTAMPTZ DEFAULT NOW(),
    month_reset_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 3. API KEYS — for programmatic access
-- =============================================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL,              -- SHA-256 hash of the key (never store raw)
    key_prefix TEXT NOT NULL,            -- First 8 chars for display: "claw_xxxx..."
    name TEXT DEFAULT 'Default',
    scopes JSONB DEFAULT '["chat","tools"]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 4. USAGE LOGS — per-session token tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    tool_calls INTEGER DEFAULT 0,
    duration_ms REAL DEFAULT 0,
    plan_id UUID REFERENCES plans(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 5. ADMIN AUDIT LOG
-- =============================================================================
CREATE TABLE IF NOT EXISTS admin_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID NOT NULL REFERENCES profiles(id),
    action TEXT NOT NULL,                -- 'ban_user', 'change_plan', 'create_plan', etc.
    target_user_id UUID REFERENCES profiles(id),
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 6. ANNOUNCEMENTS (admin → users)
-- =============================================================================
CREATE TABLE IF NOT EXISTS announcements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID NOT NULL REFERENCES profiles(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    type TEXT DEFAULT 'info' CHECK (type IN ('info', 'warning', 'critical', 'maintenance')),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- LEADS — Captured from ProfitProbe lead tracker
-- =============================================================================
CREATE TABLE IF NOT EXISTS leads (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT,
    email TEXT NOT NULL,
    phone TEXT,
    event_type TEXT DEFAULT 'form_submit',
    page_path TEXT,
    source TEXT,
    medium TEXT,
    campaign TEXT,
    campaign_id TEXT,
    keyword TEXT,
    search_term TEXT,
    lead_score INTEGER DEFAULT 0,
    click_ids JSONB DEFAULT '{}'::jsonb,
    payload JSONB DEFAULT '{}'::jsonb,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- SEED DATA — Default Plans
-- =============================================================================
INSERT INTO plans (name, display_name, description, price_monthly, price_yearly,
    max_tokens_per_day, max_tokens_per_month, max_sessions, max_turns_per_session,
    max_tools, max_models, council_access, cloud_models, ultrathink_mode,
    mcp_access, priority_support, custom_skills, api_access, allowed_models,
    sort_order)
VALUES
    ('free', 'Free', 'Basic access with local models only',
     0, 0, 50000, 1000000, 10, 50, 10, 1,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     '["deepseek-v3.1:671b-cloud","mistral","llama3"]'::jsonb, 1),

    ('pro', 'Pro', 'Cloud models + more tokens + tools',
     19.99, 199.99, 500000, 10000000, 100, 200, 26, 5,
     FALSE, TRUE, FALSE, TRUE, FALSE, TRUE, TRUE,
     '["deepseek-v3.1:671b-cloud","deepseek-reasoner","deepseek-chat","mistral","llama3","qwen2.5"]'::jsonb, 2),

    ('ultrathink', 'UltraThink', 'Full council access + ultrathink reasoning + unlimited',
     49.99, 499.99, 5000000, 100000000, -1, -1, 26, 14,
     TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE,
     '["*"]'::jsonb, 3),

    ('enterprise', 'Enterprise', 'Custom limits, SLA, dedicated support',
     199.99, 1999.99, -1, -1, -1, -1, 26, 14,
     TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE,
     '["*"]'::jsonb, 4)
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

-- Profiles: users can read their own, admins can read all
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Admins can view all profiles" ON profiles
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'superadmin'))
    );

CREATE POLICY "Admins can update all profiles" ON profiles
    FOR UPDATE USING (
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'superadmin'))
    );

-- Plans: everyone can read
ALTER TABLE plans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read plans" ON plans
    FOR SELECT USING (TRUE);

CREATE POLICY "Only admins can modify plans" ON plans
    FOR ALL USING (
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'superadmin'))
    );

-- Usage logs: users see own, admins see all
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own usage" ON usage_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own usage" ON usage_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Admins can view all usage" ON usage_logs
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'superadmin'))
    );

-- API keys: users see own
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own API keys" ON api_keys
    FOR ALL USING (auth.uid() = user_id);

-- Admin audit log: admins only
ALTER TABLE admin_audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins can view audit log" ON admin_audit_log
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'superadmin'))
    );

CREATE POLICY "Admins can insert audit log" ON admin_audit_log
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'superadmin'))
    );

-- Leads: admins can view and delete, service role can insert
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins can view all leads" ON leads
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'superadmin'))
    );

CREATE POLICY "Admins can delete leads" ON leads
    FOR DELETE USING (
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'superadmin'))
    );

CREATE POLICY "Service role can insert leads" ON leads
    FOR INSERT WITH CHECK (TRUE);

-- Announcements: everyone reads, admins write
ALTER TABLE announcements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read announcements" ON announcements
    FOR SELECT USING (TRUE);

CREATE POLICY "Admins can manage announcements" ON announcements
    FOR ALL USING (
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'superadmin'))
    );

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    free_plan_id UUID;
BEGIN
    SELECT id INTO free_plan_id FROM plans WHERE name = 'free' LIMIT 1;

    INSERT INTO profiles (id, email, display_name, plan_id, role)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)),
        free_plan_id,
        'user'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Reset daily token counters (call via Supabase cron or pg_cron)
CREATE OR REPLACE FUNCTION reset_daily_tokens()
RETURNS void AS $$
BEGIN
    UPDATE profiles
    SET tokens_used_today = 0, tokens_reset_at = NOW()
    WHERE tokens_reset_at < NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Reset monthly token counters
CREATE OR REPLACE FUNCTION reset_monthly_tokens()
RETURNS void AS $$
BEGIN
    UPDATE profiles
    SET tokens_used_month = 0, month_reset_at = NOW()
    WHERE month_reset_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- INDEXES
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_plan ON profiles(plan_id);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_created ON usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_admin_audit_log_admin ON admin_audit_log(admin_id);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at);
