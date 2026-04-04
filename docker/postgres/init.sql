-- =============================================================================
-- FlowSync Revenue Intelligence — PostgreSQL Initialization (Docker)
-- Self-contained: no \ir includes needed. Creates all schemas + tables.
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================================================
-- SCHEMAS  (medallion architecture)
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- Grant usage to the app user (already the owner, but explicit is safer)
GRANT USAGE ON SCHEMA raw     TO CURRENT_USER;
GRANT USAGE ON SCHEMA staging TO CURRENT_USER;
GRANT USAGE ON SCHEMA marts   TO CURRENT_USER;

-- =============================================================================
-- BRONZE / RAW LAYER  (raw.*)
-- =============================================================================

CREATE TABLE IF NOT EXISTS raw.raw_accounts (
    _id             TEXT,
    account_id      TEXT,
    company_name    TEXT,
    industry        TEXT,
    region          TEXT,
    country         TEXT,
    company_size    TEXT,
    employee_count  TEXT,
    founded_year    TEXT,
    website         TEXT,
    acquisition_channel TEXT,
    created_at      TEXT,
    updated_at      TEXT,
    _loaded_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_subscriptions (
    _id             TEXT,
    subscription_id TEXT,
    account_id      TEXT,
    plan_id         TEXT,
    plan_name       TEXT,
    status          TEXT,
    mrr_amount      TEXT,
    arr_amount      TEXT,
    billing_cycle   TEXT,
    seats_licensed  TEXT,
    seats_used      TEXT,
    trial_start_date TEXT,
    trial_end_date  TEXT,
    start_date      TEXT,
    end_date        TEXT,
    cancelled_at    TEXT,
    created_at      TEXT,
    updated_at      TEXT,
    _loaded_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_invoices (
    _id             TEXT,
    invoice_id      TEXT,
    account_id      TEXT,
    subscription_id TEXT,
    amount          TEXT,
    currency        TEXT,
    status          TEXT,
    due_date        TEXT,
    paid_date       TEXT,
    failed_date     TEXT,
    failure_reason  TEXT,
    invoice_date    TEXT,
    created_at      TEXT,
    _loaded_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_usage_events (
    _id              TEXT,
    event_id         TEXT,
    account_id       TEXT,
    user_id          TEXT,
    feature_name     TEXT,
    event_type       TEXT,
    session_id       TEXT,
    duration_seconds TEXT,
    event_date       TEXT,
    created_at       TEXT,
    _loaded_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_tickets (
    _id               TEXT,
    ticket_id         TEXT,
    account_id        TEXT,
    user_id           TEXT,
    subject           TEXT,
    category          TEXT,
    priority          TEXT,
    status            TEXT,
    csat_score        TEXT,
    created_at        TEXT,
    resolved_at       TEXT,
    first_response_at TEXT,
    _loaded_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_leads (
    _id               TEXT,
    lead_id           TEXT,
    company_name      TEXT,
    contact_name      TEXT,
    contact_email     TEXT,
    industry          TEXT,
    company_size      TEXT,
    acquisition_channel TEXT,
    lead_source       TEXT,
    status            TEXT,
    trial_start_date  TEXT,
    trial_end_date    TEXT,
    converted_at      TEXT,
    account_id        TEXT,
    estimated_mrr     TEXT,
    created_at        TEXT,
    updated_at        TEXT,
    _loaded_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_plans (
    _id          TEXT,
    plan_id      TEXT,
    plan_name    TEXT,
    monthly_price TEXT,
    annual_price  TEXT,
    tier          TEXT,
    max_seats     TEXT,
    features      TEXT,
    created_at    TEXT,
    _loaded_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_features (
    _id          TEXT,
    feature_id   TEXT,
    feature_name TEXT,
    category     TEXT,
    plan_tier    TEXT,
    created_at   TEXT,
    _loaded_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.raw_customers (
    _id          TEXT,
    customer_id  TEXT,
    account_id   TEXT,
    email        TEXT,
    first_name   TEXT,
    last_name    TEXT,
    role         TEXT,
    is_admin     TEXT,
    created_at   TEXT,
    last_login   TEXT,
    _loaded_at   TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- SILVER / STAGING LAYER  (staging.*)
-- =============================================================================

CREATE TABLE IF NOT EXISTS staging.stg_accounts (
    account_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name        VARCHAR(255) NOT NULL,
    industry            VARCHAR(100),
    region              VARCHAR(100),
    country             VARCHAR(100),
    company_size        VARCHAR(50),
    employee_count      INTEGER,
    founded_year        INTEGER,
    website             VARCHAR(255),
    acquisition_channel VARCHAR(100),
    created_at          TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ,
    _loaded_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_plans (
    plan_id       VARCHAR(50) PRIMARY KEY,
    plan_name     VARCHAR(100) NOT NULL,
    monthly_price NUMERIC(12,2),
    annual_price  NUMERIC(12,2),
    tier          VARCHAR(50),
    max_seats     INTEGER,
    _loaded_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_subscriptions (
    subscription_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id       UUID REFERENCES staging.stg_accounts(account_id),
    plan_id          VARCHAR(50),
    plan_name        VARCHAR(100),
    status           VARCHAR(50),
    mrr_amount       NUMERIC(12,2),
    arr_amount       NUMERIC(12,2),
    billing_cycle    VARCHAR(20),
    seats_licensed   INTEGER,
    seats_used       INTEGER,
    trial_start_date DATE,
    trial_end_date   DATE,
    start_date       DATE,
    end_date         DATE,
    cancelled_at     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ,
    updated_at       TIMESTAMPTZ,
    _loaded_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_invoices (
    invoice_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id      UUID REFERENCES staging.stg_accounts(account_id),
    subscription_id UUID REFERENCES staging.stg_subscriptions(subscription_id),
    amount          NUMERIC(12,2),
    currency        VARCHAR(3) DEFAULT 'USD',
    status          VARCHAR(50),
    due_date        DATE,
    paid_date       DATE,
    failed_date     DATE,
    failure_reason  VARCHAR(255),
    invoice_date    DATE,
    created_at      TIMESTAMPTZ,
    _loaded_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_usage_events (
    event_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id       UUID REFERENCES staging.stg_accounts(account_id),
    user_id          UUID,
    feature_name     VARCHAR(100),
    event_type       VARCHAR(100),
    session_id       UUID,
    duration_seconds INTEGER,
    event_date       DATE,
    created_at       TIMESTAMPTZ,
    _loaded_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_support_tickets (
    ticket_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id        UUID REFERENCES staging.stg_accounts(account_id),
    user_id           UUID,
    subject           VARCHAR(500),
    category          VARCHAR(100),
    priority          VARCHAR(20),
    status            VARCHAR(50),
    csat_score        NUMERIC(3,1),
    created_at        TIMESTAMPTZ,
    resolved_at       TIMESTAMPTZ,
    first_response_at TIMESTAMPTZ,
    _loaded_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_leads (
    lead_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name        VARCHAR(255),
    contact_name        VARCHAR(255),
    contact_email       VARCHAR(255),
    industry            VARCHAR(100),
    company_size        VARCHAR(50),
    acquisition_channel VARCHAR(100),
    lead_source         VARCHAR(100),
    status              VARCHAR(50),
    trial_start_date    DATE,
    trial_end_date      DATE,
    converted_at        TIMESTAMPTZ,
    account_id          UUID,
    estimated_mrr       NUMERIC(12,2),
    created_at          TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ,
    _loaded_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id  UUID REFERENCES staging.stg_accounts(account_id),
    email       VARCHAR(255),
    first_name  VARCHAR(100),
    last_name   VARCHAR(100),
    role        VARCHAR(100),
    is_admin    BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ,
    last_login  TIMESTAMPTZ,
    _loaded_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_features (
    feature_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_name VARCHAR(100) NOT NULL,
    category     VARCHAR(100),
    plan_tier    VARCHAR(50),
    created_at   TIMESTAMPTZ,
    _loaded_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.stg_calendar (
    date_day        DATE PRIMARY KEY,
    year            INTEGER,
    quarter         INTEGER,
    month           INTEGER,
    month_name      VARCHAR(20),
    week_of_year    INTEGER,
    day_of_week     INTEGER,
    day_name        VARCHAR(20),
    is_weekend      BOOLEAN,
    is_month_start  BOOLEAN,
    is_month_end    BOOLEAN,
    fiscal_year     INTEGER,
    fiscal_quarter  INTEGER
);

-- =============================================================================
-- GOLD / MARTS LAYER  (marts.*)
-- =============================================================================

CREATE TABLE IF NOT EXISTS marts.fct_mrr_movements (
    id                  BIGSERIAL PRIMARY KEY,
    account_id          UUID        NOT NULL,
    month_key           DATE        NOT NULL,
    mrr                 NUMERIC(12,2) DEFAULT 0,
    mrr_movement_type   VARCHAR(50),
    new_mrr             NUMERIC(12,2) DEFAULT 0,
    expansion_mrr       NUMERIC(12,2) DEFAULT 0,
    contraction_mrr     NUMERIC(12,2) DEFAULT 0,
    churned_mrr         NUMERIC(12,2) DEFAULT 0,
    reactivation_mrr    NUMERIC(12,2) DEFAULT 0,
    net_mrr_contribution NUMERIC(12,2) DEFAULT 0,
    plan_name           VARCHAR(100),
    region              VARCHAR(100),
    industry            VARCHAR(100),
    company_size        VARCHAR(50),
    acquisition_channel VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(account_id, month_key)
);

CREATE TABLE IF NOT EXISTS marts.fct_account_monthly_health (
    id                      BIGSERIAL PRIMARY KEY,
    account_id              UUID        NOT NULL,
    month_key               DATE        NOT NULL,
    company_name            VARCHAR(255),
    plan_name               VARCHAR(100),
    mrr                     NUMERIC(12,2),
    health_score            NUMERIC(5,2),
    health_tier             VARCHAR(20),
    churn_risk_level        VARCHAR(20),
    churn_risk_score        NUMERIC(5,2),
    risk_flag_count         INTEGER DEFAULT 0,
    risk_reasons            TEXT[],
    company_size            VARCHAR(50),
    region                  VARCHAR(100),
    industry                VARCHAR(100),
    acquisition_channel     VARCHAR(100),
    monthly_sessions        INTEGER,
    active_users            INTEGER,
    seats_licensed          INTEGER,
    seats_used              INTEGER,
    features_used           INTEGER,
    open_tickets            INTEGER,
    avg_csat                NUMERIC(3,1),
    days_since_login        INTEGER,
    tenure_months           INTEGER,
    usage_score             NUMERIC(5,2),
    seat_utilization_score  NUMERIC(5,2),
    feature_adoption_score  NUMERIC(5,2),
    support_score           NUMERIC(5,2),
    payment_score           NUMERIC(5,2),
    tenure_score            NUMERIC(5,2),
    flag_usage_drop         BOOLEAN DEFAULT FALSE,
    flag_no_login           BOOLEAN DEFAULT FALSE,
    flag_support_overload   BOOLEAN DEFAULT FALSE,
    flag_payment_failure    BOOLEAN DEFAULT FALSE,
    flag_low_csat           BOOLEAN DEFAULT FALSE,
    flag_low_seat_util      BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(account_id, month_key)
);

CREATE TABLE IF NOT EXISTS marts.fct_customer_cohorts (
    id                    BIGSERIAL PRIMARY KEY,
    cohort_month          DATE        NOT NULL,
    months_since_created  INTEGER     NOT NULL,
    cohort_size           INTEGER,
    active_accounts       INTEGER,
    logo_retention_rate   NUMERIC(8,4),
    cohort_mrr            NUMERIC(12,2),
    starting_mrr          NUMERIC(12,2),
    revenue_retention_rate NUMERIC(8,4),
    nrr                   NUMERIC(8,4),
    grr                   NUMERIC(8,4),
    cohort_health         VARCHAR(20),
    plan_name             VARCHAR(100),
    company_size          VARCHAR(50),
    acquisition_channel   VARCHAR(100),
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(cohort_month, months_since_created)
);

CREATE TABLE IF NOT EXISTS marts.fct_sales_conversion (
    id                      BIGSERIAL PRIMARY KEY,
    lead_id                 UUID,
    funnel_stage            VARCHAR(50),
    acquisition_channel     VARCHAR(100),
    industry                VARCHAR(100),
    company_size            VARCHAR(50),
    is_paid_conversion      BOOLEAN DEFAULT FALSE,
    days_lead_to_paid       INTEGER,
    converted_mrr           NUMERIC(12,2),
    lead_created_month      DATE,
    trial_start_date        DATE,
    trial_end_date          DATE,
    converted_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS marts.mart_exec_revenue_summary (
    id                  BIGSERIAL PRIMARY KEY,
    month_key           DATE        NOT NULL UNIQUE,
    total_mrr           NUMERIC(12,2),
    total_arr           NUMERIC(12,2),
    active_accounts     INTEGER,
    arpa                NUMERIC(12,2),
    new_mrr             NUMERIC(12,2),
    expansion_mrr       NUMERIC(12,2),
    contraction_mrr     NUMERIC(12,2),
    churned_mrr         NUMERIC(12,2),
    reactivation_mrr    NUMERIC(12,2),
    net_new_mrr         NUMERIC(12,2),
    nrr                 NUMERIC(8,4),
    grr                 NUMERIC(8,4),
    logo_churn_rate     NUMERIC(8,4),
    revenue_churn_rate  NUMERIC(8,4),
    mrr_mom_pct         NUMERIC(8,4),
    churned_accounts    INTEGER,
    starting_accounts   INTEGER,
    starting_mrr        NUMERIC(12,2),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS marts.mart_customer_success_summary (
    id                  BIGSERIAL PRIMARY KEY,
    account_id          UUID        NOT NULL,
    snapshot_month      DATE        NOT NULL,
    company_name        VARCHAR(255),
    health_score        NUMERIC(5,2),
    health_tier         VARCHAR(20),
    churn_risk_level    VARCHAR(20),
    risk_priority_score NUMERIC(8,4),
    mrr                 NUMERIC(12,2),
    arr                 NUMERIC(12,2),
    plan_name           VARCHAR(100),
    company_size        VARCHAR(50),
    region              VARCHAR(100),
    industry            VARCHAR(100),
    risk_reasons        TEXT[],
    health_trend        VARCHAR(20),
    acquisition_channel VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(account_id, snapshot_month)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- fct_mrr_movements
CREATE INDEX IF NOT EXISTS idx_fct_mrr_month    ON marts.fct_mrr_movements(month_key);
CREATE INDEX IF NOT EXISTS idx_fct_mrr_account  ON marts.fct_mrr_movements(account_id);
CREATE INDEX IF NOT EXISTS idx_fct_mrr_type     ON marts.fct_mrr_movements(mrr_movement_type);
CREATE INDEX IF NOT EXISTS idx_fct_mrr_plan     ON marts.fct_mrr_movements(plan_name);
CREATE INDEX IF NOT EXISTS idx_fct_mrr_region   ON marts.fct_mrr_movements(region);

-- fct_account_monthly_health
CREATE INDEX IF NOT EXISTS idx_fct_health_month   ON marts.fct_account_monthly_health(month_key);
CREATE INDEX IF NOT EXISTS idx_fct_health_account ON marts.fct_account_monthly_health(account_id);
CREATE INDEX IF NOT EXISTS idx_fct_health_risk    ON marts.fct_account_monthly_health(churn_risk_level);
CREATE INDEX IF NOT EXISTS idx_fct_health_tier    ON marts.fct_account_monthly_health(health_tier);

-- fct_customer_cohorts
CREATE INDEX IF NOT EXISTS idx_fct_cohorts_month  ON marts.fct_customer_cohorts(cohort_month);

-- fct_sales_conversion
CREATE INDEX IF NOT EXISTS idx_fct_funnel_channel ON marts.fct_sales_conversion(acquisition_channel);
CREATE INDEX IF NOT EXISTS idx_fct_funnel_month   ON marts.fct_sales_conversion(lead_created_month);

-- mart_exec_revenue_summary
CREATE INDEX IF NOT EXISTS idx_mart_exec_month    ON marts.mart_exec_revenue_summary(month_key);

-- mart_customer_success_summary
CREATE INDEX IF NOT EXISTS idx_mart_cs_month      ON marts.mart_customer_success_summary(snapshot_month);
CREATE INDEX IF NOT EXISTS idx_mart_cs_account    ON marts.mart_customer_success_summary(account_id);
CREATE INDEX IF NOT EXISTS idx_mart_cs_risk       ON marts.mart_customer_success_summary(churn_risk_level);

-- staging indexes
CREATE INDEX IF NOT EXISTS idx_stg_subs_account   ON staging.stg_subscriptions(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_subs_status    ON staging.stg_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_stg_inv_account    ON staging.stg_invoices(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_usage_account  ON staging.stg_usage_events(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_usage_date     ON staging.stg_usage_events(event_date);
CREATE INDEX IF NOT EXISTS idx_stg_tickets_acct   ON staging.stg_support_tickets(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_tickets_status ON staging.stg_support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_stg_leads_channel  ON staging.stg_leads(acquisition_channel);

-- =============================================================================
-- CONVENIENCE VIEWS
-- =============================================================================

CREATE OR REPLACE VIEW marts.v_current_mrr AS
SELECT
    a.account_id,
    a.company_name,
    a.industry,
    a.region,
    a.company_size,
    a.acquisition_channel,
    s.plan_name,
    s.mrr_amount,
    s.seats_licensed,
    s.seats_used,
    s.status,
    s.start_date
FROM staging.stg_accounts a
JOIN staging.stg_subscriptions s ON a.account_id = s.account_id
WHERE s.status = 'active';

CREATE OR REPLACE VIEW marts.v_latest_health AS
SELECT DISTINCT ON (account_id)
    account_id,
    company_name,
    plan_name,
    mrr,
    health_score,
    health_tier,
    churn_risk_level,
    churn_risk_score,
    risk_flag_count,
    risk_reasons,
    month_key
FROM marts.fct_account_monthly_health
ORDER BY account_id, month_key DESC;

-- =============================================================================
-- ALSO create public-schema aliases so legacy code still works
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.raw_accounts        (LIKE raw.raw_accounts);
CREATE TABLE IF NOT EXISTS public.raw_subscriptions   (LIKE raw.raw_subscriptions);
CREATE TABLE IF NOT EXISTS public.raw_invoices        (LIKE raw.raw_invoices);
CREATE TABLE IF NOT EXISTS public.raw_usage_events    (LIKE raw.raw_usage_events);
CREATE TABLE IF NOT EXISTS public.raw_tickets         (LIKE raw.raw_tickets);
CREATE TABLE IF NOT EXISTS public.raw_leads           (LIKE raw.raw_leads);

-- =============================================================================
-- DONE
-- =============================================================================
SELECT 'FlowSync BI schema initialized successfully — schemas: raw, staging, marts' AS status;
