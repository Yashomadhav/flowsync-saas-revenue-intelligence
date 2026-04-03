-- Gold: mart_exec_revenue_summary
-- Executive-level monthly revenue summary with all key SaaS metrics
-- Grain: one row per month
{{ config(
    materialized='table',
    tags=['gold', 'mart', 'executive'],
    indexes=[
        {'columns': ['month'], 'type': 'btree', 'unique': True}
    ]
) }}

WITH monthly_movements AS (
    SELECT
        month,
        SUM(current_mrr)                                    AS total_mrr,
        SUM(new_mrr)                                        AS new_mrr,
        SUM(expansion_mrr)                                  AS expansion_mrr,
        SUM(contraction_mrr)                                AS contraction_mrr,
        SUM(churned_mrr)                                    AS churned_mrr,
        SUM(reactivation_mrr)                               AS reactivation_mrr,
        SUM(net_new_mrr)                                    AS net_new_mrr,
        COUNT(DISTINCT account_id)                          AS active_accounts,
        COUNT(DISTINCT CASE WHEN movement_type = 'new' THEN account_id END) AS new_accounts,
        COUNT(DISTINCT CASE WHEN churned_mrr > 0 THEN account_id END)       AS churned_accounts
    FROM {{ ref('fct_mrr_movements') }}
    GROUP BY 1
),

with_prev AS (
    SELECT
        curr.*,
        LAG(curr.total_mrr)         OVER (ORDER BY curr.month) AS prev_mrr,
        LAG(curr.active_accounts)   OVER (ORDER BY curr.month) AS prev_active_accounts
    FROM monthly_movements curr
),

with_rates AS (
    SELECT
        month,
        total_mrr,
        total_mrr * 12                                      AS arr,
        new_mrr,
        expansion_mrr,
        contraction_mrr,
        churned_mrr,
        reactivation_mrr,
        net_new_mrr,
        active_accounts,
        new_accounts,
        churned_accounts,
        prev_mrr,
        prev_active_accounts,
        -- MRR growth rate
        CASE
            WHEN prev_mrr > 0
                THEN ROUND((total_mrr - prev_mrr) / prev_mrr * 100, 2)
            ELSE NULL
        END                                                 AS mrr_growth_pct,
        -- ARPA: Average Revenue Per Account
        CASE
            WHEN active_accounts > 0
                THEN ROUND(total_mrr / active_accounts, 2)
            ELSE 0
        END                                                 AS arpa,
        -- Logo Churn Rate = churned accounts / starting accounts
        CASE
            WHEN COALESCE(prev_active_accounts, 0) > 0
                THEN ROUND(churned_accounts::NUMERIC / prev_active_accounts * 100, 2)
            ELSE 0
        END                                                 AS logo_churn_rate,
        -- Revenue Churn Rate = (churned MRR + contraction MRR) / starting MRR
        CASE
            WHEN COALESCE(prev_mrr, 0) > 0
                THEN ROUND((churned_mrr + contraction_mrr) / prev_mrr * 100, 2)
            ELSE 0
        END                                                 AS revenue_churn_rate,
        -- NRR = (starting MRR + expansion + reactivation - contraction - churn) / starting MRR
        CASE
            WHEN COALESCE(prev_mrr, 0) > 0
                THEN ROUND(
                    (COALESCE(prev_mrr, 0) + expansion_mrr + reactivation_mrr
                        - contraction_mrr - churned_mrr)
                    / prev_mrr * 100, 2
                )
            ELSE NULL
        END                                                 AS nrr,
        -- GRR = (starting MRR - contraction - churn) / starting MRR
        CASE
            WHEN COALESCE(prev_mrr, 0) > 0
                THEN ROUND(
                    (COALESCE(prev_mrr, 0) - contraction_mrr - churned_mrr)
                    / prev_mrr * 100, 2
                )
            ELSE NULL
        END                                                 AS grr
    FROM with_prev
),

-- Revenue by plan for the month
revenue_by_plan AS (
    SELECT
        month,
        plan_name,
        SUM(current_mrr)                                    AS plan_mrr,
        COUNT(DISTINCT account_id)                          AS plan_accounts
    FROM {{ ref('fct_mrr_movements') }}
    GROUP BY 1, 2
),

-- Revenue by region
revenue_by_region AS (
    SELECT
        month,
        region,
        SUM(current_mrr)                                    AS region_mrr,
        COUNT(DISTINCT account_id)                          AS region_accounts
    FROM {{ ref('fct_mrr_movements') }}
    GROUP BY 1, 2
),

-- Top expanding accounts this month
top_expanding AS (
    SELECT
        month,
        account_id,
        company_name,
        expansion_mrr,
        current_mrr,
        plan_name,
        ROW_NUMBER() OVER (PARTITION BY month ORDER BY expansion_mrr DESC) AS rn
    FROM {{ ref('fct_mrr_movements') }}
    WHERE expansion_mrr > 0
),

-- Top churn risk accounts (latest health scores)
top_churn_risk AS (
    SELECT DISTINCT ON (account_id)
        account_id,
        company_name,
        health_score,
        risk_level,
        risk_flag_count,
        mrr_amount,
        plan_name,
        month
    FROM {{ ref('fct_account_monthly_health') }}
    WHERE risk_level IN ('at_risk', 'critical')
    ORDER BY account_id, month DESC
)

SELECT
    r.month,
    r.total_mrr,
    r.arr,
    r.new_mrr,
    r.expansion_mrr,
    r.contraction_mrr,
    r.churned_mrr,
    r.reactivation_mrr,
    r.net_new_mrr,
    r.active_accounts,
    r.new_accounts,
    r.churned_accounts,
    r.mrr_growth_pct,
    r.arpa,
    r.logo_churn_rate,
    r.revenue_churn_rate,
    r.nrr,
    r.grr,
    CURRENT_TIMESTAMP                                       AS dbt_updated_at
FROM with_rates r
ORDER BY month
