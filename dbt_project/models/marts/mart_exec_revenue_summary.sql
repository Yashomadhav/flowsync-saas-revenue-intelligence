-- =============================================================================
-- mart_exec_revenue_summary.sql  (Marts / Gold Layer)
-- Mart: Executive-level monthly revenue summary
-- Grain: one row per month (aggregated across all accounts)
-- Powers: Executive Overview dashboard — KPI cards, MRR trend, waterfall,
--         revenue by plan/region, top expanding/churning accounts
-- =============================================================================

{{ config(
    materialized='table',
    indexes=[
        {'columns': ['month_start_date'], 'type': 'btree'},
        {'columns': ['month_key'],        'type': 'btree'},
    ]
) }}

with mrr_movements as (
    select
        month_start_date,
        month_key,
        account_id,
        company_name,
        industry,
        company_size,
        region,
        acquisition_channel,
        plan_name,
        mrr,
        prev_mrr,
        mrr_delta,
        mrr_movement_type,
        new_mrr,
        expansion_mrr,
        contraction_mrr,
        churned_mrr,
        reactivation_mrr,
        retained_mrr,
        net_mrr_contribution,
        arr,
        is_churned,
        failed_payments
    from {{ ref('fct_mrr_movements') }}
),

-- Monthly aggregate (the main executive summary grain)
monthly_agg as (
    select
        month_start_date,
        month_key,

        -- ── Core Revenue Metrics ──────────────────────────────────────────────
        sum(mrr)                                                as total_mrr,
        sum(mrr) * 12                                           as total_arr,
        count(distinct case when mrr > 0 then account_id end)   as active_accounts,

        -- MRR Movement Components
        sum(new_mrr)                                            as new_mrr,
        sum(expansion_mrr)                                      as expansion_mrr,
        sum(contraction_mrr)                                    as contraction_mrr,
        sum(churned_mrr)                                        as churned_mrr,
        sum(reactivation_mrr)                                   as reactivation_mrr,
        sum(retained_mrr)                                       as retained_mrr,

        -- Net New MRR = New + Expansion + Reactivation - Contraction - Churn
        sum(new_mrr) + sum(expansion_mrr) + sum(reactivation_mrr)
        - sum(contraction_mrr) - sum(churned_mrr)               as net_new_mrr,

        -- Churned accounts count
        count(distinct case when is_churned then account_id end) as churned_accounts,

        -- Payment failures
        sum(failed_payments)                                    as total_failed_payments,

        -- ARPA = Total MRR / Active Accounts
        {{ safe_divide(
            'sum(mrr)',
            'count(distinct case when mrr > 0 then account_id end)'
        ) }}                                                    as arpa

    from mrr_movements
    group by month_start_date, month_key
),

-- Add prior month for MoM calculations
with_prior as (
    select
        m.*,
        lag(m.total_mrr)         over (order by m.month_start_date) as prev_total_mrr,
        lag(m.active_accounts)   over (order by m.month_start_date) as prev_active_accounts,
        lag(m.churned_accounts)  over (order by m.month_start_date) as prev_churned_accounts

    from monthly_agg m
),

-- Compute NRR, GRR, churn rates
with_rates as (
    select
        wp.*,

        -- MoM MRR growth
        wp.total_mrr - coalesce(wp.prev_total_mrr, 0)           as mrr_mom_delta,
        {{ safe_divide(
            'wp.total_mrr - coalesce(wp.prev_total_mrr, 0)',
            'coalesce(wp.prev_total_mrr, 1)'
        ) }}                                                    as mrr_mom_pct,

        -- Logo Churn Rate = Churned Accounts / Starting Accounts
        {{ safe_divide(
            'wp.churned_accounts',
            'coalesce(wp.prev_active_accounts, wp.active_accounts)'
        ) }}                                                    as logo_churn_rate,

        -- Revenue Churn Rate = (Churned MRR + Contraction) / Starting MRR
        {{ safe_divide(
            'wp.churned_mrr + wp.contraction_mrr',
            'coalesce(wp.prev_total_mrr, wp.total_mrr)'
        ) }}                                                    as revenue_churn_rate,

        -- NRR = (Starting MRR + Expansion + Reactivation - Contraction - Churn) / Starting MRR
        {{ safe_divide(
            'coalesce(wp.prev_total_mrr, wp.total_mrr) + wp.expansion_mrr + wp.reactivation_mrr - wp.contraction_mrr - wp.churned_mrr',
            'coalesce(wp.prev_total_mrr, wp.total_mrr)'
        ) }}                                                    as nrr,

        -- GRR = (Starting MRR - Contraction - Churn) / Starting MRR (capped at 1.0)
        least(1.0, {{ safe_divide(
            'coalesce(wp.prev_total_mrr, wp.total_mrr) - wp.contraction_mrr - wp.churned_mrr',
            'coalesce(wp.prev_total_mrr, wp.total_mrr)'
        ) }})                                                   as grr

    from with_prior wp
),

-- Revenue by plan (for plan breakdown chart)
by_plan as (
    select
        month_key,
        plan_name,
        sum(mrr)                                                as plan_mrr,
        count(distinct case when mrr > 0 then account_id end)   as plan_accounts
    from mrr_movements
    where plan_name is not null
    group by month_key, plan_name
),

-- Revenue by region
by_region as (
    select
        month_key,
        region,
        sum(mrr)                                                as region_mrr,
        count(distinct case when mrr > 0 then account_id end)   as region_accounts
    from mrr_movements
    where region is not null
    group by month_key, region
),

-- Revenue by industry
by_industry as (
    select
        month_key,
        industry,
        sum(mrr)                                                as industry_mrr,
        count(distinct case when mrr > 0 then account_id end)   as industry_accounts
    from mrr_movements
    where industry is not null
    group by month_key, industry
),

-- Top expanding accounts (for the expanding accounts table)
top_expanding as (
    select
        month_key,
        account_id,
        company_name,
        plan_name,
        region,
        industry,
        company_size,
        mrr,
        expansion_mrr,
        mrr_delta,
        row_number() over (
            partition by month_key
            order by expansion_mrr desc
        )                                                       as expansion_rank
    from mrr_movements
    where mrr_movement_type = 'expansion'
),

-- Top churn-risk accounts (high MRR + is_churned or contraction)
top_churn_risk as (
    select
        month_key,
        account_id,
        company_name,
        plan_name,
        region,
        industry,
        company_size,
        mrr,
        churned_mrr,
        contraction_mrr,
        mrr_movement_type,
        row_number() over (
            partition by month_key
            order by (churned_mrr + contraction_mrr) desc
        )                                                       as churn_risk_rank
    from mrr_movements
    where mrr_movement_type in ('churned', 'contraction')
)

-- Final output: monthly summary with all computed metrics
select
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['wr.month_key']) }}    as exec_summary_key,

    -- Time dimensions
    wr.month_start_date,
    wr.month_key,
    extract(year from wr.month_start_date)::int                 as year,
    extract(month from wr.month_start_date)::int                as month_num,
    to_char(wr.month_start_date, 'Mon YYYY')                    as month_label,

    -- Core KPIs
    round(wr.total_mrr::numeric, 2)                             as total_mrr,
    round(wr.total_arr::numeric, 2)                             as total_arr,
    wr.active_accounts,
    round(wr.arpa::numeric, 2)                                  as arpa,

    -- MRR Movement Waterfall
    round(wr.new_mrr::numeric, 2)                               as new_mrr,
    round(wr.expansion_mrr::numeric, 2)                         as expansion_mrr,
    round(wr.contraction_mrr::numeric, 2)                       as contraction_mrr,
    round(wr.churned_mrr::numeric, 2)                           as churned_mrr,
    round(wr.reactivation_mrr::numeric, 2)                      as reactivation_mrr,
    round(wr.retained_mrr::numeric, 2)                          as retained_mrr,
    round(wr.net_new_mrr::numeric, 2)                           as net_new_mrr,

    -- Churn metrics
    wr.churned_accounts,
    round(wr.logo_churn_rate::numeric, 4)                       as logo_churn_rate,
    round(wr.revenue_churn_rate::numeric, 4)                    as revenue_churn_rate,

    -- Retention metrics
    round(wr.nrr::numeric, 4)                                   as nrr,
    round(wr.grr::numeric, 4)                                   as grr,

    -- MoM growth
    round(wr.mrr_mom_delta::numeric, 2)                         as mrr_mom_delta,
    round(wr.mrr_mom_pct::numeric, 4)                           as mrr_mom_pct,

    -- Payment health
    wr.total_failed_payments,

    -- Prior month reference
    round(coalesce(wr.prev_total_mrr, 0)::numeric, 2)           as prev_total_mrr,
    coalesce(wr.prev_active_accounts, 0)                        as prev_active_accounts

from with_rates wr
order by wr.month_start_date
