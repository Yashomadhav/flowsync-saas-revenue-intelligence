-- Gold: mart_customer_success_summary
-- Customer success mart: latest health, risk, support, and usage per account
-- Grain: one row per account (latest month snapshot)
{{ config(
    materialized='table',
    tags=['gold', 'mart', 'health'],
    indexes=[
        {'columns': ['account_id'], 'type': 'btree', 'unique': True},
        {'columns': ['risk_level'], 'type': 'btree'},
        {'columns': ['health_score'], 'type': 'btree'}
    ]
) }}

WITH latest_health AS (
    -- Most recent health snapshot per account
    SELECT DISTINCT ON (account_id)
        account_id,
        month                           AS latest_health_month,
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
        total_events,
        active_users,
        features_used,
        active_days,
        total_session_seconds,
        prev_month_events,
        usage_change_pct,
        total_tickets,
        high_priority_tickets,
        open_tickets,
        open_high_priority_tickets,
        avg_csat,
        avg_resolution_hours,
        total_invoices,
        failed_payments,
        paid_invoices,
        usage_score,
        seat_util_score,
        feature_score,
        support_score,
        csat_score,
        payment_score,
        tenure_score,
        health_score,
        risk_level,
        flag_usage_drop,
        flag_no_login,
        flag_open_tickets,
        flag_payment_failure,
        flag_low_csat,
        flag_low_seat_util,
        risk_flag_count
    FROM {{ ref('fct_account_monthly_health') }}
    ORDER BY account_id, month DESC
),

-- Latest MRR movement for each account
latest_mrr AS (
    SELECT DISTINCT ON (account_id)
        account_id,
        month                           AS latest_mrr_month,
        current_mrr,
        previous_mrr,
        movement_type,
        mrr_delta,
        mrr_growth_pct,
        churned_mrr,
        expansion_mrr,
        contraction_mrr
    FROM {{ ref('fct_mrr_movements') }}
    ORDER BY account_id, month DESC
),

-- 3-month MRR trend per account
mrr_trend_3m AS (
    SELECT
        account_id,
        AVG(current_mrr)                AS avg_mrr_3m,
        MIN(current_mrr)                AS min_mrr_3m,
        MAX(current_mrr)                AS max_mrr_3m,
        SUM(expansion_mrr)              AS total_expansion_3m,
        SUM(contraction_mrr)            AS total_contraction_3m
    FROM {{ ref('fct_mrr_movements') }}
    WHERE month >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '3 months'
    GROUP BY 1
),

-- Lifetime ticket summary per account
lifetime_tickets AS (
    SELECT
        account_id,
        COUNT(ticket_id)                AS lifetime_tickets,
        AVG(csat_score)                 AS lifetime_avg_csat,
        SUM(CASE WHEN is_high_priority THEN 1 ELSE 0 END) AS lifetime_high_priority,
        AVG(resolution_hours)           AS lifetime_avg_resolution_hours
    FROM {{ ref('stg_tickets') }}
    GROUP BY 1
),

-- Risk reason text generation
risk_reasons AS (
    SELECT
        account_id,
        ARRAY_REMOVE(ARRAY[
            CASE WHEN flag_usage_drop     THEN 'Usage dropped >40% MoM'     ELSE NULL END,
            CASE WHEN flag_no_login       THEN 'No login in 14+ days'        ELSE NULL END,
            CASE WHEN flag_open_tickets   THEN '2+ open high-priority tickets' ELSE NULL END,
            CASE WHEN flag_payment_failure THEN 'Failed payment this cycle'  ELSE NULL END,
            CASE WHEN flag_low_csat       THEN 'CSAT score below 3.0'        ELSE NULL END,
            CASE WHEN flag_low_seat_util  THEN 'Seat utilization below 25%'  ELSE NULL END
        ], NULL)                        AS risk_reasons
    FROM latest_health
)

SELECT
    lh.account_id,
    lh.company_name,
    lh.industry,
    lh.region,
    lh.company_size,
    lh.acquisition_channel,
    lh.plan_name,
    lh.plan_id,
    lh.billing_cycle,
    lh.tenure_months,
    -- MRR
    COALESCE(lm.current_mrr, lh.mrr_amount)     AS current_mrr,
    lm.previous_mrr,
    lm.movement_type                            AS latest_movement_type,
    lm.mrr_delta,
    lm.mrr_growth_pct,
    lm.expansion_mrr                            AS latest_expansion_mrr,
    lm.contraction_mrr                          AS latest_contraction_mrr,
    -- 3-month trend
    mt.avg_mrr_3m,
    mt.total_expansion_3m,
    mt.total_contraction_3m,
    -- Seats
    lh.seats_licensed,
    lh.seats_used,
    lh.seat_utilization_rate,
    -- Usage
    lh.total_events,
    lh.active_users,
    lh.features_used,
    lh.active_days,
    lh.usage_change_pct,
    -- Support
    lh.total_tickets,
    lh.open_tickets,
    lh.open_high_priority_tickets,
    lh.avg_csat,
    lt.lifetime_tickets,
    lt.lifetime_avg_csat,
    lt.lifetime_high_priority,
    -- Payments
    lh.failed_payments,
    -- Health score breakdown
    lh.usage_score,
    lh.seat_util_score,
    lh.feature_score,
    lh.support_score,
    lh.csat_score,
    lh.payment_score,
    lh.tenure_score,
    lh.health_score,
    lh.risk_level,
    lh.risk_flag_count,
    -- Risk flags
    lh.flag_usage_drop,
    lh.flag_no_login,
    lh.flag_open_tickets,
    lh.flag_payment_failure,
    lh.flag_low_csat,
    lh.flag_low_seat_util,
    -- Risk reasons as array
    rr.risk_reasons,
    -- Snapshot date
    lh.latest_health_month,
    CURRENT_TIMESTAMP                           AS dbt_updated_at
FROM latest_health lh
LEFT JOIN latest_mrr lm ON lh.account_id = lm.account_id
LEFT JOIN mrr_trend_3m mt ON lh.account_id = mt.account_id
LEFT JOIN lifetime_tickets lt ON lh.account_id = lt.account_id
LEFT JOIN risk_reasons rr ON lh.account_id = rr.account_id
ORDER BY lh.health_score ASC  -- Most at-risk first
