-- =============================================================================
-- FlowSync Auth Schema Migration
-- Adds multi-tenant authentication: tenants, users, API keys, audit logs
-- =============================================================================

BEGIN;

-- Create auth schema
CREATE SCHEMA IF NOT EXISTS auth;

-- ─── Tenants ────────────────────────────────────────────────────────────────

CREATE TABLE auth.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    is_active BOOLEAN NOT NULL DEFAULT true,
    max_users INTEGER NOT NULL DEFAULT 5,
    max_api_keys INTEGER NOT NULL DEFAULT 10,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tenants_slug ON auth.tenants(slug);
CREATE INDEX idx_tenants_active ON auth.tenants(is_active) WHERE is_active = true;

-- ─── Users ──────────────────────────────────────────────────────────────────

CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES auth.tenants(id) ON DELETE CASCADE,
    email VARCHAR(320) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    full_name VARCHAR(200),
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN NOT NULL DEFAULT true,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_email UNIQUE (email)
);

CREATE INDEX idx_users_tenant ON auth.users(tenant_id);
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_active ON auth.users(tenant_id, is_active) WHERE is_active = true;

-- ─── API Keys ───────────────────────────────────────────────────────────────

CREATE TABLE auth.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES auth.tenants(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES auth.users(id),
    name VARCHAR(100) NOT NULL,
    key_prefix VARCHAR(12) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    scopes TEXT NOT NULL DEFAULT 'read',
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_api_key_hash UNIQUE (key_hash)
);

CREATE INDEX idx_api_keys_tenant ON auth.api_keys(tenant_id);
CREATE INDEX idx_api_keys_hash ON auth.api_keys(key_hash) WHERE is_active = true;

-- ─── Audit Logs ─────────────────────────────────────────────────────────────

CREATE TABLE auth.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES auth.tenants(id) ON DELETE CASCADE,
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    ip_address VARCHAR(45),
    user_agent TEXT,
    details TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_tenant_time ON auth.audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_user ON auth.audit_logs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_action ON auth.audit_logs(action);

-- ─── Add tenant_id to raw tables for multi-tenancy ──────────────────────────

ALTER TABLE raw.raw_accounts ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE raw.raw_subscriptions ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE raw.raw_invoices ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE raw.raw_usage_events ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE raw.raw_tickets ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE raw.raw_leads ADD COLUMN IF NOT EXISTS tenant_id UUID;

CREATE INDEX IF NOT EXISTS idx_raw_accounts_tenant ON raw.raw_accounts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_raw_subscriptions_tenant ON raw.raw_subscriptions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_raw_invoices_tenant ON raw.raw_invoices(tenant_id);
CREATE INDEX IF NOT EXISTS idx_raw_usage_events_tenant ON raw.raw_usage_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_raw_tickets_tenant ON raw.raw_tickets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_raw_leads_tenant ON raw.raw_leads(tenant_id);

-- ─── Updated_at trigger ─────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION auth.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tenants_updated_at
    BEFORE UPDATE ON auth.tenants
    FOR EACH ROW EXECUTE FUNCTION auth.update_updated_at();

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION auth.update_updated_at();

COMMIT;
