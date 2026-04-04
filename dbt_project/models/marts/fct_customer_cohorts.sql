-- =============================================================================
-- fct_customer_cohorts.sql  (Marts / Gold Layer)
-- Fact: Cohort retention analysis — logo and revenue retention by cohort period
-- Grain: one row per cohort_month × months_since_created
-- Powers: Cohort Retention dashboard (heatmap, NRR by cohort, logo churn trend)
-- =============================================================================

{{ config(
    materialized='table',
    indexes=[
        {'columns': ['cohort_month'],           'type': 'btree'},
        {'columns': ['months_since_created'],   'type': 'btree'},
        {'columns': ['plan_name'],              'type': 'btree'},
        {'columns': ['company_size'],           'type': 'btree'},
        {'columns': ['acquisition_channel'],    'type': 'btree'},
    ]
) }}

with cohort_base as (
    select
        cohort_month,
        months_since_created,
        account_id,
        company_size,
        acquisition_channel,
        plan_name,
        region,
        industry,
        retention_status,
        mrr,
        cohort_size,
        cohort_starting_mrr,
        cohort_active_accounts,
        cohort_active_mrr,
        cohort_logo_retention_rate,
        cohort_revenue_retention_rate
    from {{ ref('int_cohort_base') }}
),

-- Aggregate to cohort × period grain (the heatmap grain)
cohort_period as (
    select
        cohort_month,
        months_since_created,

        -- Cohort metadata (constant per cohort)
        max(cohort_size)                                        as cohort_size,
        max(cohort_starting_mrr)                                as cohort_starting_mrr,

        -- Period metrics
        count(distinct case when retention_status in ('new','retained','reactivated')
              then account_id end)                              as active_accounts,
        count(distinct case when retention_status = 'churned'
              then account_id end)                              as churned_accounts,
        sum(case when retention_status in ('new','retained','reactivated')
            then mrr else 0 end)                                as active_mrr,

        -- Retention rates (pre-computed from int_cohort_base)
        max(cohort_logo_retention_rate)                         as logo_retention_rate,
        max(cohort_revenue_retention_rate)                      as revenue_retention_rate,

        -- Segmentation breakdowns
        mode() within group (order by company_size)             as dominant_company_size,
        mode() within group (order by acquisition_channel)      as dominant_channel,
        mode() within group (order by plan_name)                as dominant_plan

    from cohort_base
    group by cohort_month, months_since_created
),

-- Add NRR and GRR calculations per cohort period
with_rates as (
    select
        cp.*,

        -- Logo churn rate for this period
        {{ safe_divide('cp.churned_accounts', 'cp.cohort_size') }}
                                                                as logo_churn_rate,

        -- Revenue churn rate for this period
        1 - cp.revenue_retention_rate                           as revenue_churn_rate,

        -- NRR: revenue_retention_rate (can exceed 1.0 with expansion)
        cp.revenue_retention_rate                               as nrr,

        -- GRR: capped at 1.0 (no expansion credit)
        least(1.0, cp.revenue_retention_rate)                   as grr,

        -- ARPA for this cohort period
        {{ safe_divide('cp.active_mrr', 'cp.active_accounts') }}
                                                                as arpa,

        -- Cohort health classification
        case
            when cp.logo_retention_rate >= 0.90 then 'excellent'
            when cp.logo_retention_rate >= 0.75 then 'good'
            when cp.logo_retention_rate >= 0.60 then 'fair'
            else 'poor'
        end                                                     as cohort_health

    from cohort_period cp
),

-- Segmented cohort analysis (for retention by plan/size/channel)
segmented as (
    select
        cohort_month,
        months_since_created,
        company_size,
        acquisition_channel,
        plan_name,
        region,
        industry,

        count(distinct account_id)                              as segment_cohort_size,
        count(distinct case when retention_status in ('new','retained','reactivated')
              then account_id end)                              as segment_active_accounts,
        sum(case when retention_status in ('new','retained','reactivated')
            then mrr else 0 end)                                as segment_active_mrr,
        sum(mrr)                                                as segment_total_mrr,

        {{ safe_divide(
            'count(distinct case when retention_status in (\'new\',\'retained\',\'reactivated\') then account_id end)',
            'count(distinct account_id)'
        ) }}                                                    as segment_logo_retention_rate,

        {{ safe_divide(
            'sum(case when retention_status in (\'new\',\'retained\',\'reactivated\') then mrr else 0 end)',
            'max(cohort_starting_mrr)'
        ) }}                                                    as segment_revenue_retention_rate

    from cohort_base
    group by
        cohort_month, months_since_created,
        company_size, acquisition_channel, plan_name, region, industry
),

-- Final join: main cohort grain + segmented data
final as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['wr.cohort_month', 'wr.months_since_created']) }}
                                                                as cohort_period_key,

        -- Cohort dimensions
        wr.cohort_month,
        wr.months_since_created,
        wr.dominant_company_size                                as company_size,
        wr.dominant_channel                                     as acquisition_channel,
        wr.dominant_plan                                        as plan_name,

        -- Cohort size metrics
        wr.cohort_size,
        wr.cohort_starting_mrr,
        wr.active_accounts,
        wr.churned_accounts,
        wr.active_mrr,

        -- Retention rates
        round(wr.logo_retention_rate::numeric, 4)               as logo_retention_rate,
        round(wr.revenue_retention_rate::numeric, 4)            as revenue_retention_rate,
        round(wr.logo_churn_rate::numeric, 4)                   as logo_churn_rate,
        round(wr.revenue_churn_rate::numeric, 4)                as revenue_churn_rate,

        -- Revenue metrics
        round(wr.nrr::numeric, 4)                               as nrr,
        round(wr.grr::numeric, 4)                               as grr,
        round(wr.arpa::numeric, 2)                              as arpa,

        -- Health classification
        wr.cohort_health,

        -- Milestone flags
        (wr.months_since_created = 3)                           as is_3_month_mark,
        (wr.months_since_created = 6)                           as is_6_month_mark,
        (wr.months_since_created = 12)                          as is_12_month_mark,
        (wr.months_since_created = 24)                          as is_24_month_mark

    from with_rates wr
)

select * from final
order by cohort_month, months_since_created
