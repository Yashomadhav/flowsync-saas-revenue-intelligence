-- Gold: fct_account_monthly_health
-- Account health score computed monthly from usage, support, payments, and engagement
-- Grain: one row per account per month
{{ config(
    materialized='table',
    tags=['gold', 'health'],
    indexes=[
        {'columns': ['month'], 'type': 'btree'},
        {'columns': ['account_id'], 'type': 'btree'},
        {'columns': ['health_score'], 'type': 'btree'},
        {'columns': ['risk_level'], 'type': 'btree'}
    ]
) }}

WITH account_months AS (
    -- Generate account × month combinations for all active accounts
    SELECT DISTINCT
        s.account_id,
        DATE_TRUNC('month', gs.month_date)::DATE AS month
    FROM {{ ref('stg_subscriptions') }} s
    CROSS JOIN LATERAL (
        SELECT generate_series(
            DATE_TRUNC('month', s.start_date),
            DATE_TRUNC('month', COALESCE(s.end_date, CURRENT_DATE)),
            '1 month'::INTERVAL
        ) AS month_date
    ) gs
    WHERE s.start_date IS NOT NULL
),

-- ── Usage metrics per account per month ──────────────────────────────────────
usage_monthly AS (
    SELECT
        account_id,
        event_month                                         AS month,
        COUNT(DISTINCT event_id)                            AS total_events,
        COUNT(DISTINCT user_id)                             AS active_users,
        COUNT(DISTINCT feature_name)                        AS features_used,
        COUNT(DISTINCT DATE(event_date))                    AS active_days,
        SUM(COALESCE(duration_seconds, 0))                  AS total_session_seconds,
        AVG(COALESCE(duration_seconds, 0))                  AS avg_session_seconds
    FROM {{ ref('stg_usage_events') }}
    GROUP BY 1, 2
),

-- ── Previous month usage for trend detection ─────────────────────────────────
usage_prev AS (
    SELECT
        account_id,
        month,
        total_events,
        active_users,
        features_used,
        active_days,
        LAG(total_events) OVER (PARTITION BY account_id ORDER BY month) AS prev_events,
        LAG(active_days)  OVER (PARTITION BY account_id ORDER BY month) AS prev_active_days
    FROM usage_monthly
),

-- ── Support ticket metrics per account per month ──────────────────────────────
support_monthly AS (
    SELECT
        account_id,
        ticket_month                                        AS month,
        COUNT(ticket_id)                                    AS total_tickets,
        SUM(CASE WHEN is_high_priority THEN 1 ELSE 0 END)  AS high_priority_tickets,
        SUM(CASE WHEN is_open THEN 1 ELSE 0 END)           AS open_tickets,
        SUM(CASE WHEN is_high_priority AND is_open THEN 1 ELSE 0 END) AS open_high_priority,
        AVG(CASE WHEN csat_score IS NOT NULL THEN csat_score END) AS avg_csat,
        AVG(resolution_hours)                               AS avg_resolution_hours
    FROM {{ ref('stg_tickets') }}
    GROUP BY 1, 2
),

-- ── Invoice / payment metrics per account per month ───────────────────────────
payment_monthly AS (
    SELECT
        account_id,
        invoice_month                                       AS month,
        COUNT(invoice_id)                                   AS total_invoices,
        SUM(CASE WHEN is_failed THEN 1 ELSE 0 END)         AS failed_payments,
        SUM(CASE WHEN is_paid THEN 1 ELSE 0 END)           AS paid_invoices,
        SUM(CASE WHEN is_paid THEN amount ELSE 0 END)       AS paid_amount,
        SUM(CASE WHEN is_failed THEN amount ELSE 0 END)     AS failed_amount
    FROM {{ ref('stg_invoices') }}
    GROUP BY 1, 2
),

-- ── Subscription context ──────────────────────────────────────────────────────
sub_context AS (
    SELECT DISTINCT ON (account_id)
        account_id,
        plan_name,
        plan_id,
        seats_licensed,
        seats_used,
        seat_utilization_rate,
        start_date,
        billing_cycle,
        mrr_amount
    FROM {{ ref('stg_subscriptions') }}
    WHERE is_active = TRUE
    ORDER BY account_id, mrr_amount DESC
),

-- ── Account context ───────────────────────────────────────────────────────────
acct_context AS (
    SELECT
        account_id,
        company_name,
        industry,
        region,
        company_size,
        acquisition_channel,
        created_at::DATE AS account_created_date
    FROM {{ ref('stg_accounts') }}
),

-- ── Assemble all signals ──────────────────────────────────────────────────────
assembled AS (
    SELECT
        am.account_id,
        am.month,
        ac.company_name,
        ac.industry,
        ac.region,
        ac.company_size,
        ac.acquisition_channel,
        sc.plan_name,
        sc.plan_id,
        sc.seats_licensed,
        sc.seats_used,
        sc.seat_utilization_rate,
        sc.mrr_amount,
        sc.billing_cycle,
        -- Tenure in months
        EXTRACT(MONTH FROM AGE(am.month, ac.account_created_date))::INTEGER AS tenure_months,
        -- Usage signals
        COALESCE(u.total_events, 0)         AS total_events,
        COALESCE(u.active_users, 0)         AS active_users,
        COALESCE(u.features_used, 0)        AS features_used,
        COALESCE(u.active_days, 0)          AS active_days,
        COALESCE(u.total_session_seconds, 0) AS total_session_seconds,
        -- Usage trend
        COALESCE(up.prev_events, 0)         AS prev_month_events,
        CASE
            WHEN COALESCE(up.prev_events, 0) > 0
                THEN ROUND((COALESCE(u.total_events, 0) - up.prev_events)::NUMERIC
                     / up.prev_events * 100, 2)
            ELSE NULL
        END                                 AS usage_change_pct,
        -- Support signals
        COALESCE(s.total_tickets, 0)        AS total_tickets,
        COALESCE(s.high_priority_tickets, 0) AS high_priority_tickets,
        COALESCE(s.open_tickets, 0)         AS open_tickets,
        COALESCE(s.open_high_priority, 0)   AS open_high_priority_tickets,
        s.avg_csat,
        s.avg_resolution_hours,
        -- Payment signals
        COALESCE(p.total_invoices, 0)       AS total_invoices,
        COALESCE(p.failed_payments, 0)      AS failed_payments,
        COALESCE(p.paid_invoices, 0)        AS paid_invoices
    FROM account_months am
    LEFT JOIN acct_context ac ON am.account_id = ac.account_id
    LEFT JOIN sub_context sc ON am.account_id = sc.account_id
    LEFT JOIN usage_monthly u ON am.account_id = u.account_id AND am.month = u.month
    LEFT JOIN usage_prev up ON am.account_id = up.account_id AND am.month = up.month
    LEFT JOIN support_monthly s ON am.account_id = s.account_id AND am.month = s.month
    LEFT JOIN payment_monthly p ON am.account_id = p.account_id AND am.month = p.month
),

-- ── Health Score Computation (0–100) ─────────────────────────────────────────
-- Weights: usage 25%, seat_util 20%, feature_adoption 15%, support 15%, csat 10%, payment 10%, tenure 5%
scored AS (
    SELECT
        *,
        -- 1. Usage frequency score (0–25): based on active_days in month (max 20 days = full score)
        LEAST(25, ROUND(active_days::NUMERIC / 20.0 * 25, 1))          AS usage_score,
        -- 2. Seat utilization score (0–20)
        CASE
            WHEN seats_licensed IS NULL OR seats_licensed = 0 THEN 10
            ELSE LEAST(20, ROUND(COALESCE(seat_utilization_rate, 0) * 20, 1))
        END                                                             AS seat_util_score,
        -- 3. Feature adoption score (0–15): based on distinct features used (max 8 = full score)
        LEAST(15, ROUND(features_used::NUMERIC / 8.0 * 15, 1))         AS feature_score,
        -- 4. Support burden score (0–15): penalize for open high-priority tickets
        GREATEST(0, 15 - (open_high_priority_tickets * 5))             AS support_score,
        -- 5. CSAT score (0–10): scale 1–5 CSAT to 0–10
        CASE
            WHEN avg_csat IS NULL THEN 7  -- neutral if no tickets
            ELSE LEAST(10, ROUND((avg_csat - 1) / 4.0 * 10, 1))
        END                                                             AS csat_score,
        -- 6. Payment reliability score (0–10): penalize for failed payments
        GREATEST(0, 10 - (failed_payments * 5))                        AS payment_score,
        -- 7. Tenure stability score (0–5): longer tenure = more stable
        LEAST(5, ROUND(COALESCE(tenure_months, 0)::NUMERIC / 24.0 * 5, 1)) AS tenure_score
    FROM assembled
),

final_scored AS (
    SELECT
        *,
        -- Total health score
        ROUND(
            usage_score + seat_util_score + feature_score +
            support_score + csat_score + payment_score + tenure_score
        , 1)                                                            AS health_score,
        -- Risk flags
        CASE WHEN usage_change_pct <= -40 THEN TRUE ELSE FALSE END      AS flag_usage_drop,
        CASE WHEN active_days = 0 THEN TRUE ELSE FALSE END              AS flag_no_login,
        CASE WHEN open_high_priority_tickets >= 2 THEN TRUE ELSE FALSE END AS flag_open_tickets,
        CASE WHEN failed_payments >= 1 THEN TRUE ELSE FALSE END         AS flag_payment_failure,
        CASE WHEN avg_csat < 3 THEN TRUE ELSE FALSE END                 AS flag_low_csat,
        CASE WHEN COALESCE(seat_utilization_rate, 1) < 0.25 THEN TRUE ELSE FALSE END AS flag_low_seat_util
    FROM scored
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['account_id', 'month']) }}     AS health_id,
    account_id,
    month,
    company_name,
    industry,
    region,
    company_size,
    acquisition_channel,
    plan_name,
    plan_id,
    seats_licensed,
    seats_used,
    seat_utilization_rate,
    mrr_amount,
    billing_cycle,
    tenure_months,
    -- Usage
    total_events,
    active_users,
    features_used,
    active_days,
    total_session_seconds,
    prev_month_events,
    usage_change_pct,
    -- Support
    total_tickets,
    high_priority_tickets,
    open_tickets,
    open_high_priority_tickets,
    avg_csat,
    avg_resolution_hours,
    -- Payments
    total_invoices,
    failed_payments,
    paid_invoices,
    -- Score components
    usage_score,
    seat_util_score,
    feature_score,
    support_score,
    csat_score,
    payment_score,
    tenure_score,
    -- Final score
    health_score,
    -- Risk classification
    CASE
        WHEN health_score >= 75 THEN 'healthy'
        WHEN health_score >= 50 THEN 'at_risk'
        ELSE 'critical'
    END                                                                 AS risk_level,
    -- Risk flags
    flag_usage_drop,
    flag_no_login,
    flag_open_tickets,
    flag_payment_failure,
    flag_low_csat,
    flag_low_seat_util,
    -- Count of active risk flags
    (flag_usage_drop::INT + flag_no_login::INT + flag_open_tickets::INT +
     flag_payment_failure::INT + flag_low_csat::INT + flag_low_seat_util::INT) AS risk_flag_count,
    CURRENT_TIMESTAMP                                                   AS dbt_updated_at
FROM final_scored
