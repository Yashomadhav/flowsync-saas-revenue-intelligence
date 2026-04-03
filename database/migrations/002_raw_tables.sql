-- =============================================================================
-- Migration 002: Raw (Bronze) Layer Tables
-- FlowSync Revenue Intelligence
-- =============================================================================
-- All columns are TEXT to preserve exact source data.
-- Timestamps added for lineage tracking.
-- =============================================================================

SET search_path TO raw, public;

-- ---------------------------------------------------------------------------
-- raw.raw_plans — Subscription plan catalog
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.raw_plans (
    _row_id         BIGSERIAL PRIMARY KEY,
    plan_id         TEXT,
    plan_name       TEXT,
    tier            TEXT,
    monthly_price   TEXT,
    annual_price    TEXT,
    price_per_seat  TEXT,
    min_seats       TEXT,
    max_seats       TEXT,
    seat_based      TEXT,
    is_annual       TEXT,
    features        TEXT,
    _loaded_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    _source_file    TEXT
);
COMMENT ON TABLE raw.raw_plans IS 'Bronze: raw plan catalog from source system';

-- ---------------------------------------------------------------------------
-- raw.raw_features — Product feature catalog
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.raw_features (
    _row_id         BIGSERIAL PRIMARY KEY,
    feature_id      TEXT,
    feature_name    TEXT,
    category        TEXT,
    plan_tier       TEXT,
    description     TEXT,
    _loaded_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    _source_file    TEXT
);
COMMENT ON TABLE raw.raw_features IS 'Bronze: raw product feature catalog';

-- ---------------------------------------------------------------------------
-- raw.raw_calendar — Date dimension
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.raw_calendar (
    _row_id         BIGSERIAL PRIMARY KEY,
    date            TEXT,
    year            TEXT,
    quarter         TEXT,
    month           TEXT,
    month_name      TEXT,
    week            TEXT,
    day_of_week     TEXT,
    day_name        TEXT,
    is_weekend      TEXT,
    fiscal_year     TEXT,
    fiscal_quarter  TEXT,
    _loaded_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    _source_file    TEXT
);
COMMENT ON TABLE raw.raw_calendar IS 'Bronze: raw date dimension table';

-- ---------------------------------------------------------------------------
-- raw.raw_accounts — Customer account records
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.raw_accounts (
    _row_id              BIGSERIAL PRIMARY KEY,
    account_id           TEXT,
    company_name         TEXT,
    industry             TEXT,
    region               TEXT,
    country              TEXT,
    company_size         TEXT,
    employee_count       TEXT,
    founded_year         TEXT,
    website              TEXT,
    acquisition_channel  TEXT,
    created_at           TEXT,
    updated_at           TEXT,
    _loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    _source_file         TEXT
);
COMMENT ON TABLE raw.raw_accounts IS 'Bronze: raw account/company records';

-- ---------------------------------------------------------------------------
-- raw.raw_subscriptions — Subscription lifecycle records
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.raw_subscriptions (
    _row_id              BIGSERIAL PRIMARY KEY,
    subscription_id      TEXT,
    account_id           TEXT,
    plan_id              TEXT,
    plan_name            TEXT,
    status               TEXT,
    mrr_amount           TEXT,
    arr_amount           TEXT,
    billing_cycle        TEXT,
    seats_licensed       TEXT,
    seats_used           TEXT,
    trial_start_date     TEXT,
    trial_end_date       TEXT,
    start_date           TEXT,
    end_date             TEXT,
    cancelled_at         TEXT,
    created_at           TEXT,
    updated_at           TEXT,
    _loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    _source_file         TEXT
);
COMMENT ON TABLE raw.raw_subscriptions IS 'Bronze: raw subscription lifecycle records';

-- ---------------------------------------------------------------------------
-- raw.raw_invoices — Invoice and payment records
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.raw_invoices (
    _row_id              BIGSERIAL PRIMARY KEY,
    invoice_id           TEXT,
    account_id           TEXT,
    subscription_id      TEXT,
    amount               TEXT,
    currency             TEXT,
    status               TEXT,
    due_date             TEXT,
    paid_date            TEXT,
    failed_date          TEXT,
    failure_reason       TEXT,
    invoice_date         TEXT,
    created_at           TEXT,
    _loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    _source_file         TEXT
);
COMMENT ON TABLE raw.raw_invoices IS 'Bronze: raw invoice and payment records';

-- ---------------------------------------------------------------------------
-- raw.raw_usage_events — Product usage event stream
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.raw_usage_events (
    _row_id              BIGSERIAL PRIMARY KEY,
    event_id             TEXT,
    account_id           TEXT,
    user_id              TEXT,
    feature_name         TEXT,
    event_type           TEXT,
    session_id           TEXT,
    duration_seconds     TEXT,
    event_date           TEXT,
    created_at           TEXT,
    _loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    _source_file         TEXT
);
COMMENT ON TABLE raw.raw_usage_events IS 'Bronze: raw product usage event stream';

-- ---------------------------------------------------------------------------
-- raw.raw_tickets — Support ticket records
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.raw_tickets (
    _row_id              BIGSERIAL PRIMARY KEY,
    ticket_id            TEXT,
    account_id           TEXT,
    user_id              TEXT,
    subject              TEXT,
    category             TEXT,
    priority             TEXT,
    status               TEXT,
    csat_score           TEXT,
    created_at           TEXT,
    resolved_at          TEXT,
    first_response_at    TEXT,
    _loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    _source_file         TEXT
);
COMMENT ON TABLE raw.raw_tickets IS 'Bronze: raw support ticket records';

-- ---------------------------------------------------------------------------
-- raw.raw_leads — Sales lead and opportunity records
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.raw_leads (
    _row_id              BIGSERIAL PRIMARY KEY,
    lead_id              TEXT,
    company_name         TEXT,
    contact_name         TEXT,
    contact_email        TEXT,
    industry             TEXT,
    company_size         TEXT,
    acquisition_channel  TEXT,
    lead_source          TEXT,
    status               TEXT,
    trial_start_date     TEXT,
    trial_end_date       TEXT,
    converted_at         TEXT,
    account_id           TEXT,
    estimated_mrr        TEXT,
    created_at           TEXT,
    updated_at           TEXT,
    _loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    _source_file         TEXT
);
COMMENT ON TABLE raw.raw_leads IS 'Bronze: raw sales lead and opportunity records';

-- ---------------------------------------------------------------------------
-- Indexes on raw tables (for join performance during staging transforms)
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_raw_accounts_account_id       ON raw.raw_accounts(account_id);
CREATE INDEX IF NOT EXISTS idx_raw_subscriptions_account_id  ON raw.raw_subscriptions(account_id);
CREATE INDEX IF NOT EXISTS idx_raw_subscriptions_sub_id      ON raw.raw_subscriptions(subscription_id);
CREATE INDEX IF NOT EXISTS idx_raw_invoices_account_id       ON raw.raw_invoices(account_id);
CREATE INDEX IF NOT EXISTS idx_raw_invoices_sub_id           ON raw.raw_invoices(subscription_id);
CREATE INDEX IF NOT EXISTS idx_raw_usage_account_id          ON raw.raw_usage_events(account_id);
CREATE INDEX IF NOT EXISTS idx_raw_usage_event_date          ON raw.raw_usage_events(event_date);
CREATE INDEX IF NOT EXISTS idx_raw_tickets_account_id        ON raw.raw_tickets(account_id);
CREATE INDEX IF NOT EXISTS idx_raw_leads_account_id          ON raw.raw_leads(account_id);
CREATE INDEX IF NOT EXISTS idx_raw_loaded_at_accounts        ON raw.raw_accounts(_loaded_at);
CREATE INDEX IF NOT EXISTS idx_raw_loaded_at_events          ON raw.raw_usage_events(_loaded_at);

SELECT 'Migration 002: Raw tables created' AS status;
