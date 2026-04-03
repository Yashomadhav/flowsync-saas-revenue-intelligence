-- =============================================================================
-- FlowSync Revenue Intelligence — PostgreSQL Initialization
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- BRONZE LAYER — Raw tables (exact copy of source data, all TEXT)
-- =============================================================================

CREATE TABLE IF NOT EXISTS raw_accounts (
    _id TEXT, account_id TEXT, company_name TEXT, industry TEXT,
    region TEXT, country TEXT, company_size TEXT, employee_count TEXT,
    founded_year TEXT, website TEXT, acquisition_channel TEXT,
    created_at TEXT, updated_at TEXT, _loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_subscriptions (
    _id TEXT, subscription_id TEXT, account_id TEXT, plan_id TEXT,
    plan_name TEXT, status TEXT, mrr_amount TEXT, arr_amount TEXT,
    billing_cycle TEXT, seats_licensed TEXT, seats_used TEXT,
    trial_start_date TEXT, trial_end_date TEXT, start_date TEXT,
    end_date TEXT, cancelled_at TEXT, created_at TEXT, updated_at TEXT,
    _loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_invoices (
    _id TEXT, invoice_id TEXT, account_id TEXT, subscription_id TEXT,
    amount TEXT, currency TEXT, status TEXT, due_date TEXT,
    paid_date TEXT, failed_date TEXT, failure_reason TEXT,
    invoice_date TEXT, created_at TEXT, _loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_usage_events (
    _id TEXT, event_id TEXT, account_id TEXT, user_id TEXT,
    feature_name TEXT, event_type TEXT, session_id TEXT,
    duration_seconds TEXT, event_date TEXT, created_at TEXT,
    _loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_tickets (
    _id TEXT, ticket_id TEXT, account_id TEXT, user_id TEXT,
    subject TEXT, category TEXT, priority TEXT, status TEXT,
    csat_score TEXT, created_at TEXT, resolved_at TEXT,
    first_response_at TEXT, _loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_leads (
    _id TEXT, lead_id TEXT, company_name TEXT, contact_name TEXT,
    contact_email TEXT, industry TEXT, company_size TEXT,
    acquisition_channel TEXT, lead_source TEXT, status TEXT,
    trial_start_date TEXT, trial_end_date TEXT, converted_at TEXT,
    account_id TEXT, estimated_mrr TEXT, created_at TEXT,
    updated_at TEXT, _loaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- SILVER LAYER — Staging tables (cleaned, typed, deduplicated)
-- =============================================================================

CREATE TABLE IF NOT EXISTS stg_accounts (
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

CREATE TABLE IF NOT EXISTS stg_subscriptions (
    subscription_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID REFERENCES stg_accounts(account_id),
    plan_id             VARCHAR(50),
    plan_name           VARCHAR(100),
    status              VARCHAR(50),
    mrr_amount          NUMERIC(12,2),
    arr_amount          NUMERIC(12,2),
    billing_cycle       VARCHAR(20),
    seats_licensed      INTEGER,
    seats_used          INTEGER,
    trial_start_date    DATE,
    trial_end_date      DATE,
    start_date          DATE,
    end_date            DATE,
    cancelled_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ,
    _loaded_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stg_invoices (
    invoice_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID REFERENCES stg_accounts(account_id),
    subscription_id     UUID REFERENCES stg_subscriptions(subscription_id),
    amount              NUMERIC(12,2),
    currency            VARCHAR(3) DEFAULT 'USD',
    status              VARCHAR(50),
    due_date            DATE,
    paid_date           DATE,
    failed_date         DATE,
    failure_reason      VARCHAR(255),
    invoice_date        DATE,
    created_at          TIMESTAMPTZ,
    _loaded_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stg_usage_events (
    event_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID REFERENCES stg_accounts(account_id),
    user_id             UUID,
    feature_name        VARCHAR(100),
    event_type          VARCHAR(100),
    session_id          UUID,
    duration_seconds    INTEGER,
    event_date          DATE,
    created_at          TIMESTAMPTZ,
    _loaded_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stg_tickets (
    ticket_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id          UUID REFERENCES stg_accounts(account_id),
    user_id             UUID,
    subject             VARCHAR(500),
    category            VARCHAR(100),
    priority            VARCHAR(20),
    status              VARCHAR(50),
    csat_score          NUMERIC(3,1),
    created_at          TIMESTAMPTZ,
    resolved_at         TIMESTAMPTZ,
    first_response_at   TIMESTAMPTZ,
    _loaded_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stg_leads (
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

-- =============================================================================
-- GOLD LAYER — Fact tables and Marts
-- =============================================================================

CREATE TABLE IF NOT EXISTS fct_mrr_movements (
    id                  BIGSERIAL PRIMARY KEY,
    month_date          DATE NOT NULL,
    account_id          UUID NOT NULL,
    plan_id             VARCHAR(50),
    plan_name           VARCHAR(100),
    region              VARCHAR(100),
    industry            VARCHAR(100),
    company_size        VARCHAR(50),
    acquisition_channel VARCHAR(100),
    movement_type       VARCHAR(50) NOT NULL,
    starting_mrr        NUMERIC(12,2) DEFAULT 0,
    ending_mrr          NUMERIC(12,2) DEFAULT 0,
    new_mrr             NUMERIC(12,2) DEFAULT 0,
    expansion_mrr       NUMERIC(12,2) DEFAULT 0,
    contraction_mrr     NUMERIC(12,2) DEFAULT 0,
    churned_mrr         NUMERIC(12,2) DEFAULT 0,
    reactivation_mrr    NUMERIC(12,2) DEFAULT 0,
    net_new_mrr         NUMERIC(12,2) DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(month_date, account_id)
);

CREATE TABLE IF NOT EXISTS fct_account_monthly_health (
    id                      BIGSERIAL PRIMARY KEY,
    month_date              DATE NOT NULL,
    account_id              UUID NOT NULL,
    company_name            VARCHAR(255),
    plan_name               VARCHAR(100),
    mrr_amount              NUMERIC(12,2),
    health_score            NUMERIC(5,2),
    usage_score             NUMERIC(5,2),
    seat_utilization_score  NUMERIC(5,2),
    feature_adoption_score  NUMERIC(5,2),
    support_score           NUMERIC(5,2),
    csat_score_normalized   NUMERIC(5,2),
    payment_score           NUMERIC(5,2),
    tenure_score            NUMERIC(5,2),
    risk_level              VARCHAR(20),
    flag_usage_drop         BOOLEAN DEFAULT FALSE,
    flag_no_login           BOOLEAN DEFAULT FALSE,
    flag_support_overload   BOOLEAN DEFAULT FALSE,
    flag_payment_failure    BOOLEAN DEFAULT FALSE,
    flag_low_csat           BOOLEAN DEFAULT FALSE,
    flag_low_seat_util      BOOLEAN DEFAULT FALSE,
    monthly_sessions        INTEGER,
    active_users            INTEGER,
    seats_licensed          INTEGER,
    features_used           INTEGER,
    open_tickets            INTEGER,
    avg_csat                NUMERIC(3,1),
    days_since_login        INTEGER,
    tenure_months           INTEGER,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(month_date, account_id)
);

CREATE TABLE IF NOT EXISTS fct_customer_cohorts (
    id                  BIGSERIAL PRIMARY KEY,
    cohort_month        DATE NOT NULL,
    period_number       INTEGER NOT NULL,
    period_date         DATE NOT NULL,
    cohort_size         INTEGER,
    retained_customers  INTEGER,
    retention_rate      NUMERIC(6,4),
    starting_mrr        NUMERIC(12,2),
    retained_mrr        NUMERIC(12,2),
    revenue_retention   NUMERIC(6,4),
    plan_name           VARCHAR(100),
    company_size        VARCHAR(50),
    acquisition_channel VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fct_sales_conversion (
    id                      BIGSERIAL PRIMARY KEY,
    month_date              DATE NOT NULL,
    acquisition_channel     VARCHAR(100),
    industry                VARCHAR(100),
    company_size            VARCHAR(50),
    leads_created           INTEGER DEFAULT 0,
    trials_started          INTEGER DEFAULT 0,
    trials_converted        INTEGER DEFAULT 0,
    leads_lost              INTEGER DEFAULT 0,
    lead_to_trial_rate      NUMERIC(6,4),
    trial_to_paid_rate      NUMERIC(6,4),
    lead_to_paid_rate       NUMERIC(6,4),
    avg_sales_cycle_days    NUMERIC(8,2),
    avg_trial_duration_days NUMERIC(8,2),
    total_new_mrr           NUMERIC(12,2),
    avg_deal_size           NUMERIC(12,2),
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mart_exec_revenue_summary (
    id                      BIGSERIAL PRIMARY KEY,
    month_date              DATE NOT NULL UNIQUE,
    total_mrr               NUMERIC(12,2),
    total_arr               NUMERIC(12,2),
    new_mrr                 NUMERIC(12,2),
    expansion_mrr           NUMERIC(12,2),
    contraction_mrr         NUMERIC(12,2),
    churned_mrr             NUMERIC(12,2),
    reactivation_mrr        NUMERIC(12,2),
    net_new_mrr             NUMERIC(12,2),
    nrr                     NUMERIC(6,4),
    grr                     NUMERIC(6,4),
    logo_churn_rate         NUMERIC(6,4),
    revenue_churn_rate      NUMERIC(6,4),
    active_accounts         INTEGER,
    new_accounts            INTEGER,
    churned_accounts        INTEGER,
    arpa                    NUMERIC(12,2),
    mrr_mom_change          NUMERIC(6,4),
    arr_mom_change          NUMERIC(6,4),
    accounts_mom_change     NUMERIC(6,4),
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mart_customer_success_summary (
    id                      BIGSERIAL PRIMARY KEY,
    month_date              DATE NOT NULL,
    account_id              UUID NOT NULL,
    company_name            VARCHAR(255),
    plan_name               VARCHAR(100),
    region                  VARCHAR(100),
    industry                VARCHAR(100),
    company_size            VARCHAR(50),
    mrr_amount              NUMERIC(12,2),
    health_score            NUMERIC(5,2),
    risk_level              VARCHAR(20),
    risk_flags              TEXT[],
    tenure_months           INTEGER,
    monthly_sessions        INTEGER,
    seat_utilization        NUMERIC(5,4),
    open_tickets            INTEGER,
    avg_csat                NUMERIC(3,1),
    days_since_login        INTEGER,
    last_expansion_date     DATE,
    last_contraction_date   DATE,
    churn_probability       NUMERIC(5,4),
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(month_date, account_id)
);

-- =============================================================================
-- INDEXES for performance
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_fct_mrr_month ON fct_mrr_movements(month_date);
CREATE INDEX IF NOT EXISTS idx_fct_mrr_account ON fct_mrr_movements(account_id);
CREATE INDEX IF NOT EXISTS idx_fct_mrr_movement_type ON fct_mrr_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_fct_health_month ON fct_account_monthly_health(month_date);
CREATE INDEX IF NOT EXISTS idx_fct_health_account ON fct_account_monthly_health(account_id);
CREATE INDEX IF NOT EXISTS idx_fct_health_risk ON fct_account_monthly_health(risk_level);
CREATE INDEX IF NOT EXISTS idx_fct_cohorts_month ON fct_customer_cohorts(cohort_month);
CREATE INDEX IF NOT EXISTS idx_mart_exec_month ON mart_exec_revenue_summary(month_date);
CREATE INDEX IF NOT EXISTS idx_mart_cs_month ON mart_customer_success_summary(month_date);
CREATE INDEX IF NOT EXISTS idx_mart_cs_risk ON mart_customer_success_summary(risk_level);
CREATE INDEX IF NOT EXISTS idx_stg_subs_account ON stg_subscriptions(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_subs_status ON stg_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_stg_invoices_account ON stg_invoices(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_usage_account ON stg_usage_events(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_usage_date ON stg_usage_events(event_date);
CREATE INDEX IF NOT EXISTS idx_stg_tickets_account ON stg_tickets(account_id);
CREATE INDEX IF NOT EXISTS idx_stg_tickets_status ON stg_tickets(status);

-- =============================================================================
-- VIEWS for convenience
-- =============================================================================

CREATE OR REPLACE VIEW v_current_mrr AS
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
FROM stg_accounts a
JOIN stg_subscriptions s ON a.account_id = s.account_id
WHERE s.status = 'active';

CREATE OR REPLACE VIEW v_latest_health AS
SELECT DISTINCT ON (account_id)
    account_id,
    company_name,
    plan_name,
    mrr_amount,
    health_score,
    risk_level,
    flag_usage_drop,
    flag_no_login,
    flag_support_overload,
    flag_payment_failure,
    flag_low_csat,
    flag_low_seat_util,
    month_date
FROM fct_account_monthly_health
ORDER BY account_id, month_date DESC;

-- Done
SELECT 'FlowSync BI schema initialized successfully' AS status;
