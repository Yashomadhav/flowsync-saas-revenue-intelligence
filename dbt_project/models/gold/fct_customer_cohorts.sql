-- Gold: fct_customer_cohorts
-- Cohort retention analysis: customer and revenue retention by cohort month
-- Grain: one row per cohort_month × period_number
{{ config(
    materialized='table',
    tags=['gold', 'cohorts'],
    indexes=[
        {'columns': ['cohort_month'], 'type': 'btree'},
        {'columns': ['period_number'], 'type': 'btree'}
    ]
) }}

WITH cohort_base AS (
    -- Identify each account's cohort month (first paid subscription month)
    SELECT
        s.account_id,
        a.company_name,
        a.company_size,
        a.acquisition_channel,
        a.industry,
        a.region,
        s.plan_name,
        s.plan_id,
        DATE_TRUNC('month', MIN(s.start_date))::DATE    AS cohort_month,
        MIN(s.mrr_amount)                               AS initial_mrr
    FROM {{ ref('stg_subscriptions') }} s
    JOIN {{ ref('stg_accounts') }} a ON s.account_id = a.account_id
    WHERE s.start_date IS NOT NULL
      AND s.mrr_amount > 0
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
),

cohort_sizes AS (
    -- Count accounts and sum MRR per cohort
    SELECT
        cohort_month,
        COUNT(DISTINCT account_id)  AS cohort_size,
        SUM(initial_mrr)            AS cohort_starting_mrr
    FROM cohort_base
    GROUP BY 1
),

-- Monthly MRR per account (from MRR movements fact)
account_monthly AS (
    SELECT
        account_id,
        month,
        current_mrr
    FROM {{ ref('fct_mrr_movements') }}
    WHERE current_mrr > 0
),

-- Cross join cohort accounts with their activity months
cohort_activity AS (
    SELECT
        cb.account_id,
        cb.cohort_month,
        cb.company_size,
        cb.acquisition_channel,
        cb.plan_name,
        cb.plan_id,
        cb.initial_mrr,
        am.month                                        AS activity_month,
        am.current_mrr,
        -- Period number: 0 = cohort month, 1 = 1 month later, etc.
        EXTRACT(YEAR FROM AGE(am.month, cb.cohort_month)) * 12 +
        EXTRACT(MONTH FROM AGE(am.month, cb.cohort_month)) AS period_number
    FROM cohort_base cb
    JOIN account_monthly am ON cb.account_id = am.account_id
    WHERE am.month >= cb.cohort_month
),

-- Aggregate retention by cohort × period
cohort_retention AS (
    SELECT
        ca.cohort_month,
        ca.period_number::INTEGER                       AS period_number,
        cs.cohort_size,
        cs.cohort_starting_mrr,
        COUNT(DISTINCT ca.account_id)                   AS retained_accounts,
        SUM(ca.current_mrr)                             AS retained_mrr,
        -- Retention rates
        ROUND(
            COUNT(DISTINCT ca.account_id)::NUMERIC /
            NULLIF(cs.cohort_size, 0) * 100, 2
        )                                               AS customer_retention_rate,
        ROUND(
            SUM(ca.current_mrr) /
            NULLIF(cs.cohort_starting_mrr, 0) * 100, 2
        )                                               AS revenue_retention_rate,
        -- NRR: retained + expansion / starting MRR
        ROUND(
            SUM(ca.current_mrr) /
            NULLIF(cs.cohort_starting_mrr, 0) * 100, 2
        )                                               AS nrr_pct
    FROM cohort_activity ca
    JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
    GROUP BY 1, 2, 3, 4
),

-- Cohort breakdown by dimension (plan, size, channel)
cohort_by_plan AS (
    SELECT
        ca.cohort_month,
        ca.period_number::INTEGER                       AS period_number,
        ca.plan_name,
        COUNT(DISTINCT ca.account_id)                   AS retained_accounts,
        SUM(ca.current_mrr)                             AS retained_mrr
    FROM cohort_activity ca
    GROUP BY 1, 2, 3
),

cohort_by_size AS (
    SELECT
        ca.cohort_month,
        ca.period_number::INTEGER                       AS period_number,
        ca.company_size,
        COUNT(DISTINCT ca.account_id)                   AS retained_accounts,
        SUM(ca.current_mrr)                             AS retained_mrr
    FROM cohort_activity ca
    GROUP BY 1, 2, 3
),

cohort_by_channel AS (
    SELECT
        ca.cohort_month,
        ca.period_number::INTEGER                       AS period_number,
        ca.acquisition_channel,
        COUNT(DISTINCT ca.account_id)                   AS retained_accounts,
        SUM(ca.current_mrr)                             AS retained_mrr
    FROM cohort_activity ca
    GROUP BY 1, 2, 3
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['cohort_month', 'period_number']) }} AS cohort_id,
    cohort_month,
    period_number,
    cohort_size,
    cohort_starting_mrr,
    retained_accounts,
    retained_mrr,
    customer_retention_rate,
    revenue_retention_rate,
    nrr_pct,
    -- Churned accounts in this period
    cohort_size - retained_accounts                     AS churned_accounts,
    cohort_starting_mrr - retained_mrr                  AS churned_mrr,
    -- Logo churn rate for this period
    ROUND(
        (cohort_size - retained_accounts)::NUMERIC /
        NULLIF(cohort_size, 0) * 100, 2
    )                                                   AS logo_churn_rate,
    CURRENT_TIMESTAMP                                   AS dbt_updated_at
FROM cohort_retention
ORDER BY cohort_month, period_number
