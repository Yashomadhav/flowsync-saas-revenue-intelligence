-- =============================================================================
-- Migration 003: Staging (Silver) Layer Tables
-- FlowSync Revenue Intelligence
-- =============================================================================
-- Typed, cleaned, deduplicated versions of raw tables.
-- Primary keys enforced, foreign key references documented.
-- =============================================================================

SET search_path TO staging, public;

-- ---------------------------------------------------------------------------
-- staging.stg_plans
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_plans (
    plan_id         TEXT PRIMARY KEY,
    plan_name       TEXT NOT NULL,
    tier            INTEGER NOT NULL DEFAULT 1,
    monthly_price   NUMERIC(10,2) NOT NULL,
    annual_price    NUMERIC(10,2),
    price_per_seat  NUMERIC(10,2),
    min_seats       INTEGER DEFAULT 1,
    max_seats       INTEGER,
    seat_based      BOOLEAN DEFAULT FALSE,
    is_annual       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE staging.stg_plans IS 'Silver: cleaned plan catalog with typed columns';

-- ---------------------------------------------------------------------------
-- staging.stg_features
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_features (
    feature_id      TEXT PRIMARY KEY,
    feature_name    TEXT NOT NULL,
    category        TEXT,
    plan_tier       INTEGER,
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE staging.stg_features IS 'Silver: cleaned product feature catalog';

-- ---------------------------------------------------------------------------
-- staging.stg_calendar
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_calendar (
    date            DATE PRIMARY KEY,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      TEXT NOT NULL,
    week            INTEGER,
    day_of_week     INTEGER,
    day_name        TEXT,
    is_weekend      BOOLEAN DEFAULT FALSE,
    fiscal_year     INTEGER,
    fiscal_quarter  INTEGER
);
COMMENT ON TABLE staging.stg_calendar IS 'Silver: date dimension table';

-- ---------------------------------------------------------------------------
-- staging.stg_accounts
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_accounts (
    account_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name        TEXT NOT NULL,
    industry            TEXT,
    region              TEXT,
    country             TEXT,
    company_size        TEXT,
    employee_count      INTEGER,
    founded_year        INTEGER,
    website             TEXT,
    acquisition_channel TEXT,
    created_at          TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ,
    _ingested_at        TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE staging.stg_accounts IS 'Silver: cleaned account records with UUID PKs';

CREATE INDEX IF NOT EXISTS idx_stg_accounts_industry   ON staging.stg_accounts(industry);
CREATE INDEX IF NOT EXISTS idx_stg_accounts_region     ON staging.stg_accounts(region);
CREATE INDEX IF NOT EXISTS idx_stg_accounts_channel    ON staging.stg_accounts(acquisition_channel);
CREATE INDEX IF NOT EXISTS idx_stg_accounts_size       ON staging.stg_accounts(company_size);

-- ---------------------------------------------------------------------------
-- staging.stg_subscriptions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_subscriptions (
    subscription_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID NOT NULL REFERENCES staging.stg_accounts(account_id) ON DELETE CASCADE,
    plan_id             TEXT,
    plan_name           TEXT,
    status              TEXT NOT NULL CHECK (status IN ('active','cancelled','trial','paused','expired')),
    mrr_amount          NUMERIC(12,4),
    arr_amount          NUMERIC(12,4),
    billing_cycle       TEXT CHECK (billing_cycle IN ('monthly','annual')),
    seats_licensed      INTEGER,
    seats_used          INTEGER,
    trial_start_date    DATE,
    trial_end_date      DATE,
    start_date          DATE,
    end_date            DATE,
    cancelled_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ,
    _ingested_at        TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE staging.stg_subscriptions IS 'Silver: cleaned subscription lifecycle records';

CREATE INDEX IF NOT EXISTS idx_stg_subs_account_id  ON staging.stg_subscriptions(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_subs_plan_name   ON staging.stg_subscriptions(plan_name);
CREATE INDEX IF NOT EXISTS idx_stg_subs_status      ON staging.stg_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_stg_subs_start_date  ON staging.stg_subscriptions(start_date);
CREATE INDEX IF NOT EXISTS idx_stg_subs_end_date    ON staging.stg_subscriptions(end_date);

-- ---------------------------------------------------------------------------
-- staging.stg_invoices
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_invoices (
    invoice_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID NOT NULL REFERENCES staging.stg_accounts(account_id) ON DELETE CASCADE,
    subscription_id     UUID REFERENCES staging.stg_subscriptions(subscription_id),
    amount              NUMERIC(12,4),
    currency            TEXT DEFAULT 'USD',
    status              TEXT CHECK (status IN ('paid','failed','pending','void','refunded')),
    due_date            DATE,
    paid_date           DATE,
    failed_date         DATE,
    failure_reason      TEXT,
    invoice_date        DATE,
    created_at          TIMESTAMPTZ,
    _ingested_at        TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE staging.stg_invoices IS 'Silver: cleaned invoice and payment records';

CREATE INDEX IF NOT EXISTS idx_stg_inv_account_id   ON staging.stg_invoices(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_inv_status       ON staging.stg_invoices(status);
CREATE INDEX IF NOT EXISTS idx_stg_inv_invoice_date ON staging.stg_invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_stg_inv_sub_id       ON staging.stg_invoices(subscription_id);

-- ---------------------------------------------------------------------------
-- staging.stg_usage_events
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_usage_events (
    event_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID NOT NULL REFERENCES staging.stg_accounts(account_id) ON DELETE CASCADE,
    user_id             UUID,
    feature_name        TEXT,
    event_type          TEXT,
    session_id          UUID,
    duration_seconds    INTEGER,
    event_date          DATE,
    created_at          TIMESTAMPTZ,
    _ingested_at        TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE staging.stg_usage_events IS 'Silver: cleaned product usage event stream';

CREATE INDEX IF NOT EXISTS idx_stg_usage_account_id   ON staging.stg_usage_events(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_usage_event_date   ON staging.stg_usage_events(event_date);
CREATE INDEX IF NOT EXISTS idx_stg_usage_feature_name ON staging.stg_usage_events(feature_name);
CREATE INDEX IF NOT EXISTS idx_stg_usage_event_type   ON staging.stg_usage_events(event_type);

-- ---------------------------------------------------------------------------
-- staging.stg_tickets
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_tickets (
    ticket_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID NOT NULL REFERENCES staging.stg_accounts(account_id) ON DELETE CASCADE,
    user_id             UUID,
    subject             TEXT,
    category            TEXT,
    priority            TEXT CHECK (priority IN ('low','medium','high','critical')),
    status              TEXT CHECK (status IN ('open','in_progress','resolved','closed')),
    csat_score          NUMERIC(3,1) CHECK (csat_score BETWEEN 1 AND 5),
    created_at          TIMESTAMPTZ,
    resolved_at         TIMESTAMPTZ,
    first_response_at   TIMESTAMPTZ,
    resolution_hours    NUMERIC(8,2) GENERATED ALWAYS AS (
        CASE WHEN resolved_at IS NOT NULL AND created_at IS NOT NULL
             THEN EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600.0
             ELSE NULL END
    ) STORED,
    _ingested_at        TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE staging.stg_tickets IS 'Silver: cleaned support ticket records';

CREATE INDEX IF NOT EXISTS idx_stg_tickets_account_id ON staging.stg_tickets(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_tickets_priority   ON staging.stg_tickets(priority);
CREATE INDEX IF NOT EXISTS idx_stg_tickets_status     ON staging.stg_tickets(status);
CREATE INDEX IF NOT EXISTS idx_stg_tickets_created_at ON staging.stg_tickets(created_at);

-- ---------------------------------------------------------------------------
-- staging.stg_leads
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.stg_leads (
    lead_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name        TEXT,
    contact_name        TEXT,
    contact_email       TEXT,
    industry            TEXT,
    company_size        TEXT,
    acquisition_channel TEXT,
    lead_source         TEXT,
    status              TEXT CHECK (status IN ('new','qualified','trial','converted','lost','disqualified')),
    trial_start_date    DATE,
    trial_end_date      DATE,
    converted_at        TIMESTAMPTZ,
    account_id          UUID REFERENCES staging.stg_accounts(account_id),
    estimated_mrr       NUMERIC(12,4),
    created_at          TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ,
    days_to_convert     INTEGER GENERATED ALWAYS AS (
        CASE WHEN converted_at IS NOT NULL AND created_at IS NOT NULL
             THEN EXTRACT(DAY FROM (converted_at - created_at))::INTEGER
             ELSE NULL END
    ) STORED,
    _ingested_at        TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE staging.stg_leads IS 'Silver: cleaned sales lead and opportunity records';

CREATE INDEX IF NOT EXISTS idx_stg_leads_status   ON staging.stg_leads(status);
CREATE INDEX IF NOT EXISTS idx_stg_leads_channel  ON staging.stg_leads(acquisition_channel);
CREATE INDEX IF NOT EXISTS idx_stg_leads_industry ON staging.stg_leads(industry);

SELECT 'Migration 003: Staging tables created' AS status;
