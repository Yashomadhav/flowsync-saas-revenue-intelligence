-- Gold: fct_sales_conversion
-- Funnel conversion metrics: Lead → Trial → Paid
-- Grain: one row per lead
{{ config(
    materialized='table',
    tags=['gold', 'funnel'],
    indexes=[
        {'columns': ['lead_month'], 'type': 'btree'},
        {'columns': ['acquisition_channel'], 'type': 'btree'},
        {'columns': ['funnel_stage'], 'type': 'btree'}
    ]
) }}

WITH leads AS (
    SELECT
        lead_id,
        company_name,
        industry,
        company_size,
        acquisition_channel,
        lead_source,
        status,
        funnel_stage,
        trial_start_date,
        trial_end_date,
        converted_at,
        account_id,
        estimated_mrr,
        created_at,
        lead_month,
        is_converted,
        had_trial,
        trial_converted,
        days_to_convert,
        trial_duration_days
    FROM {{ ref('stg_leads') }}
),

-- Join with subscription data for converted accounts
converted_subs AS (
    SELECT
        s.account_id,
        s.plan_name,
        s.plan_id,
        s.mrr_amount                AS actual_mrr,
        s.start_date                AS paid_start_date,
        s.billing_cycle
    FROM {{ ref('stg_subscriptions') }} s
    WHERE s.is_active = TRUE
      OR s.start_date IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY s.account_id ORDER BY s.start_date ASC) = 1
),

-- Join with usage during trial period
trial_usage AS (
    SELECT
        u.account_id,
        COUNT(DISTINCT u.event_id)          AS trial_events,
        COUNT(DISTINCT u.user_id)           AS trial_active_users,
        COUNT(DISTINCT u.feature_name)      AS trial_features_used,
        COUNT(DISTINCT DATE(u.event_date))  AS trial_active_days
    FROM {{ ref('stg_usage_events') }} u
    JOIN leads l ON u.account_id = l.account_id
    WHERE l.trial_start_date IS NOT NULL
      AND u.event_date BETWEEN l.trial_start_date AND COALESCE(l.trial_end_date, l.trial_start_date + 14)
    GROUP BY 1
),

assembled AS (
    SELECT
        l.lead_id,
        l.company_name,
        l.industry,
        l.company_size,
        l.acquisition_channel,
        l.lead_source,
        l.status,
        l.funnel_stage,
        l.trial_start_date,
        l.trial_end_date,
        l.converted_at,
        l.account_id,
        l.estimated_mrr,
        l.created_at,
        l.lead_month,
        l.is_converted,
        l.had_trial,
        l.trial_converted,
        l.days_to_convert,
        l.trial_duration_days,
        -- Subscription data for converted leads
        cs.plan_name,
        cs.plan_id,
        cs.actual_mrr,
        cs.paid_start_date,
        cs.billing_cycle,
        -- Trial usage signals
        COALESCE(tu.trial_events, 0)        AS trial_events,
        COALESCE(tu.trial_active_users, 0)  AS trial_active_users,
        COALESCE(tu.trial_features_used, 0) AS trial_features_used,
        COALESCE(tu.trial_active_days, 0)   AS trial_active_days,
        -- Trial engagement score (0–100)
        LEAST(100, ROUND(
            (COALESCE(tu.trial_active_days, 0)::NUMERIC / 14.0 * 40) +
            (LEAST(COALESCE(tu.trial_features_used, 0), 5)::NUMERIC / 5.0 * 30) +
            (LEAST(COALESCE(tu.trial_events, 0), 50)::NUMERIC / 50.0 * 30)
        , 1))                               AS trial_engagement_score
    FROM leads l
    LEFT JOIN converted_subs cs ON l.account_id = cs.account_id AND l.is_converted = TRUE
    LEFT JOIN trial_usage tu ON l.account_id = tu.account_id
)

SELECT
    lead_id,
    company_name,
    industry,
    company_size,
    acquisition_channel,
    lead_source,
    status,
    funnel_stage,
    lead_month,
    -- Funnel stage flags
    TRUE                                    AS is_lead,
    had_trial                               AS is_trial,
    is_converted                            AS is_paid,
    trial_converted,
    -- Dates
    created_at                              AS lead_created_at,
    trial_start_date,
    trial_end_date,
    converted_at,
    paid_start_date,
    -- Duration metrics
    days_to_convert,
    trial_duration_days,
    -- Revenue
    estimated_mrr,
    actual_mrr,
    plan_name,
    plan_id,
    billing_cycle,
    -- Trial engagement
    trial_events,
    trial_active_users,
    trial_features_used,
    trial_active_days,
    trial_engagement_score,
    -- Conversion quality: actual vs estimated MRR
    CASE
        WHEN estimated_mrr > 0 AND actual_mrr IS NOT NULL
            THEN ROUND(actual_mrr / estimated_mrr * 100, 2)
        ELSE NULL
    END                                     AS mrr_vs_estimate_pct,
    CURRENT_TIMESTAMP                       AS dbt_updated_at
FROM assembled
