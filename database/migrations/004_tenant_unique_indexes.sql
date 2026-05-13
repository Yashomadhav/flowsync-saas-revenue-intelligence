-- =============================================================================
-- Tenant-scoped unique indexes for multi-tenant upsert support
-- These partial indexes enable ON CONFLICT with tenant_id filtering
-- =============================================================================

BEGIN;

-- Drop old single-column unique constraints if they exist
DROP INDEX IF EXISTS raw.idx_raw_accounts_account_id;
DROP INDEX IF EXISTS raw.idx_raw_subscriptions_subscription_id;
DROP INDEX IF EXISTS raw.idx_raw_invoices_invoice_id;
DROP INDEX IF EXISTS raw.idx_raw_usage_events_event_id;
DROP INDEX IF EXISTS raw.idx_raw_tickets_ticket_id;
DROP INDEX IF EXISTS raw.idx_raw_leads_lead_id;

-- Create tenant-scoped unique indexes
CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_accounts_tenant_account
    ON raw.raw_accounts (account_id, tenant_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_subscriptions_tenant_sub
    ON raw.raw_subscriptions (subscription_id, tenant_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_invoices_tenant_invoice
    ON raw.raw_invoices (invoice_id, tenant_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_usage_events_tenant_event
    ON raw.raw_usage_events (event_id, tenant_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_tickets_tenant_ticket
    ON raw.raw_tickets (ticket_id, tenant_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_leads_tenant_lead
    ON raw.raw_leads (lead_id, tenant_id);

-- Partitioning prep: add date columns needed for future range partitioning
-- (For now these are regular indexes; full partitioning requires table recreation)
CREATE INDEX IF NOT EXISTS idx_raw_usage_events_date
    ON raw.raw_usage_events (event_date);

CREATE INDEX IF NOT EXISTS idx_raw_invoices_date
    ON raw.raw_invoices (invoice_date);

COMMIT;
