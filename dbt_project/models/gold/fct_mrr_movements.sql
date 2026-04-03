-- Gold: fct_mrr_movements
-- Core MRR waterfall fact table: New, Expansion, Contraction, Churn, Reactivation
-- Grain: one row per account per month
{{ config(
    materialized='table',
    tags=['gold', 'revenue'],
    indexes=[
        {'columns': ['month'], 'type': 'btree'},
        {'columns': ['account_id'], 'type': 'btree'},
        {'columns': ['movement_type'], 'type': 'btree'}
    ]
) }}

WITH monthly_subscriptions AS (
    -- Get the MRR for each active subscription per month
    SELECT
        s.account_id,
        a.company_name,
        a.industry,
        a.region,
        a.company_size,
        a.acquisition_channel,
        s.plan_id,
        s.plan_name,
        s.mrr_amount,
        s.billing_cycle,
        -- Generate a series of months the subscription was active
        DATE_TRUNC('month', gs.month_date)::DATE AS month
    FROM {{ ref('stg_subscriptions') }} s
    JOIN {{ ref('stg_accounts') }} a ON s.account_id = a.account_id
    -- Expand each subscription across its active months
    CROSS JOIN LATERAL (
        SELECT generate_series(
            DATE_TRUNC('month', s.start_date),
            DATE_TRUNC('month', COALESCE(s.end_date, CURRENT_DATE)),
            '1 month'::INTERVAL
        ) AS month_date
    ) gs
    WHERE s.start_date IS NOT NULL
      AND s.mrr_amount > 0
),

account_monthly_mrr AS (
    -- Aggregate to account level per month
    SELECT
        account_id,
        company_name,
        industry,
        region,
        company_size,
        acquisition_channel,
        plan_id,
        plan_name,
        month,
        SUM(mrr_amount) AS mrr
    FROM monthly_subscriptions
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
),

with_prev_mrr AS (
    -- Bring in previous month MRR for movement calculation
    SELECT
        curr.account_id,
        curr.company_name,
        curr.industry,
        curr.region,
        curr.company_size,
        curr.acquisition_channel,
        curr.plan_id,
        curr.plan_name,
        curr.month,
        curr.mrr                                AS current_mrr,
        COALESCE(prev.mrr, 0)                   AS previous_mrr,
        -- Was this account active 2 months ago (for reactivation detection)?
        COALESCE(prev2.mrr, 0)                  AS mrr_2mo_ago
    FROM account_monthly_mrr curr
    LEFT JOIN account_monthly_mrr prev
        ON curr.account_id = prev.account_id
        AND prev.month = curr.month - INTERVAL '1 month'
    LEFT JOIN account_monthly_mrr prev2
        ON curr.account_id = prev2.account_id
        AND prev2.month = curr.month - INTERVAL '2 months'
),

with_next_mrr AS (
    -- Bring in next month to detect churn
    SELECT
        curr.*,
        COALESCE(nxt.mrr, 0) AS next_month_mrr
    FROM with_prev_mrr curr
    LEFT JOIN account_monthly_mrr nxt
        ON curr.account_id = nxt.account_id
        AND nxt.month = curr.month + INTERVAL '1 month'
),

movements AS (
    SELECT
        account_id,
        company_name,
        industry,
        region,
        company_size,
        acquisition_channel,
        plan_id,
        plan_name,
        month,
        current_mrr,
        previous_mrr,
        -- MRR Movement Classification
        CASE
            -- New: account had no MRR last month, has MRR this month, not a reactivation
            WHEN previous_mrr = 0 AND mrr_2mo_ago = 0 AND current_mrr > 0
                THEN 'new'
            -- Reactivation: account had no MRR last month but had MRR 2+ months ago
            WHEN previous_mrr = 0 AND mrr_2mo_ago > 0 AND current_mrr > 0
                THEN 'reactivation'
            -- Expansion: MRR increased
            WHEN current_mrr > previous_mrr AND previous_mrr > 0
                THEN 'expansion'
            -- Contraction: MRR decreased but still active
            WHEN current_mrr < previous_mrr AND current_mrr > 0
                THEN 'contraction'
            -- Retained: no change
            WHEN current_mrr = previous_mrr AND current_mrr > 0
                THEN 'retained'
            ELSE 'unknown'
        END                                                 AS movement_type,
        -- MRR delta amounts
        CASE
            WHEN previous_mrr = 0 AND current_mrr > 0
                THEN current_mrr
            ELSE 0
        END                                                 AS new_mrr,
        CASE
            WHEN current_mrr > previous_mrr AND previous_mrr > 0
                THEN current_mrr - previous_mrr
            ELSE 0
        END                                                 AS expansion_mrr,
        CASE
            WHEN current_mrr < previous_mrr AND current_mrr > 0
                THEN previous_mrr - current_mrr
            ELSE 0
        END                                                 AS contraction_mrr,
        CASE
            WHEN previous_mrr = 0 AND mrr_2mo_ago > 0 AND current_mrr > 0
                THEN current_mrr
            ELSE 0
        END                                                 AS reactivation_mrr,
        next_month_mrr
    FROM with_next_mrr
),

-- Add churned MRR: accounts that had MRR this month but zero next month
with_churn AS (
    SELECT
        m.*,
        CASE
            WHEN m.current_mrr > 0 AND m.next_month_mrr = 0
                THEN m.current_mrr
            ELSE 0
        END                                                 AS churned_mrr,
        -- Net New MRR = New + Expansion + Reactivation - Contraction - Churn
        (m.new_mrr + m.expansion_mrr + m.reactivation_mrr
            - m.contraction_mrr
            - CASE WHEN m.current_mrr > 0 AND m.next_month_mrr = 0
                   THEN m.current_mrr ELSE 0 END)           AS net_new_mrr
    FROM movements m
)

SELECT
    -- Keys
    {{ dbt_utils.generate_surrogate_key(['account_id', 'month']) }} AS mrr_movement_id,
    account_id,
    company_name,
    industry,
    region,
    company_size,
    acquisition_channel,
    plan_id,
    plan_name,
    month,
    -- MRR values
    current_mrr,
    previous_mrr,
    current_mrr * 12                                        AS arr,
    -- Movement classification
    movement_type,
    -- Movement amounts
    new_mrr,
    expansion_mrr,
    contraction_mrr,
    reactivation_mrr,
    churned_mrr,
    net_new_mrr,
    -- MRR change
    current_mrr - previous_mrr                              AS mrr_delta,
    CASE
        WHEN previous_mrr > 0
            THEN ROUND((current_mrr - previous_mrr) / previous_mrr * 100, 2)
        ELSE NULL
    END                                                     AS mrr_growth_pct,
    -- Metadata
    CURRENT_TIMESTAMP                                       AS dbt_updated_at
FROM with_churn
