-- =============================================================================
-- Migration 004: Marts (Gold) Layer Tables
-- FlowSync Revenue Intelligence
-- =============================================================================
-- Fact tables and aggregated business metric marts.
-- These are the tables FastAPI reads from directly.
-- =============================================================================

SET search_path TO marts, public;

-- ---------------------------------------------------------------------------
-- marts.fct_mrr_movements — Monthly MRR movement by account
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marts.fct_mrr_movements (
    id                  BIGSERIAL PRIMARY KEY,
    month_date          DATE NOT NULL,
    account_id          UUID NOT NULL,
    plan_id             TEXT,
    plan_name           TEXT,
    region              TEXT,
    industry            TEXT,
    company_size        TEXT,
    acquisition_channel TEXT,
    movement_type       TEXT NOT NULL CHECK (movement_type IN (
                            'new','expansion','contraction','churn','reactivation','retained'
                        )),
    starting_mrr        NUMERIC(12,4) DEFAULT 0,
    ending_mrr          NUMERIC(12,4) DEFAULT 0,
    new_mrr             NUMERIC(12,4) DEFAULT 0,
    expansion_mrr       NUMERIC(12,4) DEFAULT 0,
    contraction_mrr     NUMERIC(12,4) DEFAULT 0,
    churned_mrr         NUMERIC(12,4) DEFAULT 0,
    reactivation_mrr    NUMERIC(12,4) DEFAULT 0,
    net_new_mrr         NUMERIC(12,4) DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (month_date, account_id)
);
COMMENT ON TABLE marts.fct_mrr_movements IS 'Gold: monthly MRR movement fact table per account';

CREATE INDEX IF NOT EXISTS idx_fct_mrr_month_date    ON marts.fct_mrr_movements(month_date);
CREATE INDEX IF NOT EXISTS idx_fct_mrr_account_id    ON marts.fct_mrr_movements(account_id);
CREATE INDEX IF NOT EXISTS idx_fct_mrr_movement_type ON marts.fct_mrr_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_fct_mrr_plan_name     ON marts.fct_mrr_movements(plan_name);
CREATE INDEX IF NOT EXISTS idx_fct_mrr_region        ON marts.fct_mrr_movements(region);

-- ---------------------------------------------------------------------------
-- marts.fct_account_monthly_health — Monthly health score per account
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marts.fct_account_monthly_health (
    id                          BIGSERIAL PRIMARY KEY,
    month_date                  DATE NOT NULL,
    account_id                  UUID NOT NULL,
    company_name                TEXT,
    plan_name                   TEXT,
    mrr_amount                  NUMERIC(12,4),
    -- Composite health score (0-100)
    health_score                NUMERIC(5,2),
    -- Component scores (0-100 each)
    usage_score                 NUMERIC(5,2),
    seat_utilization_score      NUMERIC(5,2),
    feature_adoption_score      NUMERIC(5,2),
    support_score               NUMERIC(5,2),
    csat_score_normalized       NUMERIC(5,2),
    payment_score               NUMERIC(5,2),
    tenure_score                NUMERIC(5,2),
    -- Risk classification
    risk_level                  TEXT CHECK (risk_level IN ('healthy','at_risk','critical')),
    -- Risk flags
    flag_usage_drop             BOOLEAN DEFAULT FALSE,
    flag_no_login               BOOLEAN DEFAULT FALSE,
    flag_support_overload       BOOLEAN DEFAULT FALSE,
    flag_payment_failure        BOOLEAN DEFAULT FALSE,
    flag_low_csat               BOOLEAN DEFAULT FALSE,
    flag_low_seat_util          BOOLEAN DEFAULT FALSE,
    -- Raw metrics
    monthly_sessions            INTEGER,
    active_users                INTEGER,
    seats_licensed              INTEGER,
    features_used               INTEGER,
    open_tickets                INTEGER,
    avg_csat                    NUMERIC(3,1),
    days_since_login            INTEGER,
    tenure_months               INTEGER,
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (month_date, account_id)
);
COMMENT ON TABLE marts.fct_account_monthly_health IS 'Gold: monthly account health scores and risk flags';

CREATE INDEX IF NOT EXISTS idx_fct_health_month_date  ON marts.fct_account_monthly_health(month_date);
CREATE INDEX IF NOT EXISTS idx_fct_health_account_id  ON marts.fct_account_monthly_health(account_id);
CREATE INDEX IF NOT EXISTS idx_fct_health_risk_level  ON marts.fct_account_monthly_health(risk_level);
CREATE INDEX IF NOT EXISTS idx_fct_health_score       ON marts.fct_account_monthly_health(health_score);

-- ---------------------------------------------------------------------------
-- marts.fct_customer_cohorts — Cohort retention by month
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marts.fct_customer_cohorts (
    id                  BIGSERIAL PRIMARY KEY,
    cohort_month        DATE NOT NULL,
    period_month        DATE NOT NULL,
    months_since_start  INTEGER NOT NULL,
    -- Customer retention
    cohort_size         INTEGER,
    retained_customers  INTEGER,
    customer_retention_rate NUMERIC(6,4),
    -- Revenue retention
    cohort_starting_mrr NUMERIC(12,4),
    retained_mrr        NUMERIC(12,4),
    revenue_retention_rate NUMERIC(6,4),
    -- Segmentation
    plan_name           TEXT,
    company_size        TEXT,
    acquisition_channel TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (cohort_month, period_month, plan_name, company_size, acquisition_channel)
);
COMMENT ON TABLE marts.fct_customer_cohorts IS 'Gold: cohort retention analysis by month';

CREATE INDEX IF NOT EXISTS idx_fct_cohorts_cohort_month ON marts.fct_customer_cohorts(cohort_month);
CREATE INDEX IF NOT EXISTS idx_fct_cohorts_period_month ON marts.fct_customer_cohorts(period_month);
CREATE INDEX IF NOT EXISTS idx_fct_cohorts_plan_name    ON marts.fct_customer_cohorts(plan_name);

-- ---------------------------------------------------------------------------
-- marts.fct_sales_conversion — Lead-to-paid funnel metrics
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marts.fct_sales_conversion (
    id                      BIGSERIAL PRIMARY KEY,
    lead_id                 UUID NOT NULL UNIQUE,
    company_name            TEXT,
    industry                TEXT,
    company_size            TEXT,
    acquisition_channel     TEXT,
    lead_source             TEXT,
    status                  TEXT,
    trial_start_date        DATE,
    trial_end_date          DATE,
    converted_at            TIMESTAMPTZ,
    account_id              UUID,
    estimated_mrr           NUMERIC(12,4),
    actual_mrr              NUMERIC(12,4),
    days_to_convert         INTEGER,
    trial_duration_days     INTEGER GENERATED ALWAYS AS (
        CASE WHEN trial_end_date IS NOT NULL AND trial_start_date IS NOT NULL
             THEN (trial_end_date - trial_start_date)
             ELSE NULL END
    ) STORED,
    is_converted            BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMPTZ,
    updated_at              TIMESTAMPTZ
);
COMMENT ON TABLE marts.fct_sales_conversion IS 'Gold: lead-to-paid conversion funnel fact table';

CREATE INDEX IF NOT EXISTS idx_fct_conv_channel    ON marts.fct_sales_conversion(acquisition_channel);
CREATE INDEX IF NOT EXISTS idx_fct_conv_status     ON marts.fct_sales_conversion(status);
CREATE INDEX IF NOT EXISTS idx_fct_conv_converted  ON marts.fct_sales_conversion(is_converted);
CREATE INDEX IF NOT EXISTS idx_fct_conv_created_at ON marts.fct_sales_conversion(created_at);

-- ---------------------------------------------------------------------------
-- marts.mart_exec_revenue_summary — Monthly executive KPI rollup
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marts.mart_exec_revenue_summary (
    id                  BIGSERIAL PRIMARY KEY,
    month_date          DATE NOT NULL UNIQUE,
    -- Core MRR metrics
    total_mrr           NUMERIC(14,4),
    total_arr           NUMERIC(14,4),
    -- MRR movements
    new_mrr             NUMERIC(12,4),
    expansion_mrr       NUMERIC(12,4),
    contraction_mrr     NUMERIC(12,4),
    churned_mrr         NUMERIC(12,4),
    reactivation_mrr    NUMERIC(12,4),
    net_new_mrr         NUMERIC(12,4),
    -- Retention metrics (stored as ratios, e.g. 1.12 = 112%)
    nrr                 NUMERIC(8,4),
    grr                 NUMERIC(8,4),
    -- Churn metrics (stored as ratios, e.g. 0.028 = 2.8%)
    logo_churn_rate     NUMERIC(8,4),
    revenue_churn_rate  NUMERIC(8,4),
    -- Account counts
    active_accounts     INTEGER,
    new_accounts        INTEGER,
    churned_accounts    INTEGER,
    -- Per-account metrics
    arpa                NUMERIC(12,4),
    -- Month-over-month changes
    mrr_mom_change      NUMERIC(8,4),
    arr_mom_change      NUMERIC(8,4),
    accounts_mom_change NUMERIC(8,4),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE marts.mart_exec_revenue_summary IS 'Gold: monthly executive revenue KPI rollup';

CREATE INDEX IF NOT EXISTS idx_mart_exec_month_date ON marts.mart_exec_revenue_summary(month_date);

-- ---------------------------------------------------------------------------
-- marts.mart_customer_success_summary — Monthly customer success rollup
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marts.mart_customer_success_summary (
    id                      BIGSERIAL PRIMARY KEY,
    month_date              DATE NOT NULL UNIQUE,
    -- Health distribution
    healthy_accounts        INTEGER DEFAULT 0,
    at_risk_accounts        INTEGER DEFAULT 0,
    critical_accounts       INTEGER DEFAULT 0,
    avg_health_score        NUMERIC(5,2),
    -- Risk flag counts
    accounts_usage_drop     INTEGER DEFAULT 0,
    accounts_no_login       INTEGER DEFAULT 0,
    accounts_support_burden INTEGER DEFAULT 0,
    accounts_payment_fail   INTEGER DEFAULT 0,
    accounts_low_csat       INTEGER DEFAULT 0,
    accounts_low_seat_util  INTEGER DEFAULT 0,
    -- Support metrics
    total_open_tickets      INTEGER DEFAULT 0,
    avg_csat_score          NUMERIC(3,1),
    avg_resolution_hours    NUMERIC(8,2),
    -- Usage metrics
    avg_monthly_sessions    NUMERIC(8,2),
    avg_seat_utilization    NUMERIC(5,2),
    avg_features_used       NUMERIC(5,2),
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE marts.mart_customer_success_summary IS 'Gold: monthly customer success KPI rollup';

CREATE INDEX IF NOT EXISTS idx_mart_cs_month_date ON marts.mart_customer_success_summary(month_date);

-- ---------------------------------------------------------------------------
-- marts.mart_revenue_by_segment — Revenue breakdown by plan/region/industry
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marts.mart_revenue_by_segment (
    id              BIGSERIAL PRIMARY KEY,
    month_date      DATE NOT NULL,
    segment_type    TEXT NOT NULL CHECK (segment_type IN ('plan','region','industry','company_size','channel')),
    segment_value   TEXT NOT NULL,
    total_mrr       NUMERIC(12,4),
    account_count   INTEGER,
    avg_mrr         NUMERIC(12,4),
    pct_of_total    NUMERIC(6,4),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (month_date, segment_type, segment_value)
);
COMMENT ON TABLE marts.mart_revenue_by_segment IS 'Gold: revenue breakdown by various segments';

CREATE INDEX IF NOT EXISTS idx_mart_seg_month_date    ON marts.mart_revenue_by_segment(month_date);
CREATE INDEX IF NOT EXISTS idx_mart_seg_segment_type  ON marts.mart_revenue_by_segment(segment_type);

SELECT 'Migration 004: Marts tables created' AS status;
