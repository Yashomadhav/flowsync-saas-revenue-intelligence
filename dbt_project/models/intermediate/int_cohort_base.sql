-- =============================================================================
-- int_cohort_base.sql
-- Intermediate: Cohort base table for retention analysis
-- One row per account per cohort-month combination.
-- Tracks whether each account was retained, churned, or reactivated
-- at each period relative to their acquisition cohort.
-- =============================================================================

{{ config(materialized='table') }}

with account_months as (
    select
        account_id,
        company_name,
        industry,
        company_size,
        region,
        acquisition_channel,
        cohort_month,
        cohort_month_date,
        month_start_date,
        month_key,
        months_since_created,
        is_first_month
    from {{ ref('int_account_months') }}
),

-- MRR per account per month (from subscription MRR model)
mrr_by_month as (
    select
        account_id,
        month_start_date,
        month_key,
        sum(mrr)                                                as account_mrr,
        max(plan_name)                                          as plan_name,
        max(plan_tier_order)                                    as plan_tier_order
    from {{ ref('int_subscription_mrr') }}
    group by account_id, month_start_date, month_key
),

-- Join account-months with MRR to determine activity
account_month_mrr as (
    select
        am.account_id,
        am.company_name,
        am.industry,
        am.company_size,
        am.region,
        am.acquisition_channel,
        am.cohort_month,
        am.cohort_month_date,
        am.month_start_date,
        am.month_key,
        am.months_since_created,
        am.is_first_month,

        -- MRR this month (null = no active subscription)
        coalesce(m.account_mrr, 0)                             as mrr,
        m.plan_name,
        m.plan_tier_order,

        -- Was the account active (had MRR) this month?
        (coalesce(m.account_mrr, 0) > 0)                       as is_active_this_month

    from account_months am
    left join mrr_by_month m
        on am.account_id = m.account_id
        and am.month_start_date = m.month_start_date
),

-- Get starting MRR for each cohort (month 0)
cohort_starting_mrr as (
    select
        account_id,
        cohort_month,
        mrr                                                     as starting_mrr,
        plan_name                                               as starting_plan
    from account_month_mrr
    where is_first_month = true
),

-- Add previous month activity for churn/reactivation detection
with_prev as (
    select
        amm.*,
        csm.starting_mrr,
        csm.starting_plan,

        -- Previous month active status
        lag(amm.is_active_this_month) over (
            partition by amm.account_id
            order by amm.month_start_date
        )                                                       as was_active_prev_month,

        -- Previous month MRR
        lag(amm.mrr) over (
            partition by amm.account_id
            order by amm.month_start_date
        )                                                       as prev_month_mrr

    from account_month_mrr amm
    left join cohort_starting_mrr csm
        on amm.account_id = csm.account_id
        and amm.cohort_month = csm.cohort_month
),

-- Classify retention status per account per month
classified as (
    select
        wp.*,

        -- Retention status
        case
            when wp.is_first_month then 'new'
            when wp.is_active_this_month and wp.was_active_prev_month then 'retained'
            when wp.is_active_this_month and not coalesce(wp.was_active_prev_month, false)
                then 'reactivated'
            when not wp.is_active_this_month and coalesce(wp.was_active_prev_month, false)
                then 'churned'
            when not wp.is_active_this_month and not coalesce(wp.was_active_prev_month, false)
                then 'inactive'
            else 'unknown'
        end                                                     as retention_status,

        -- Revenue retention rate vs starting MRR
        {{ safe_divide('wp.mrr::float', 'nullif(wp.starting_mrr, 0)') }}
                                                                as revenue_retention_rate,

        -- MRR delta vs starting
        wp.mrr - coalesce(wp.starting_mrr, 0)                  as mrr_vs_starting

    from with_prev wp
),

-- Aggregate to cohort × period grain for heatmap
-- (one row per cohort_month × months_since_created)
cohort_period_summary as (
    select
        cohort_month,
        cohort_month_date,
        months_since_created,

        -- Account counts
        count(distinct account_id)                              as total_accounts_in_cohort,
        count(distinct case when retention_status in ('new', 'retained', 'reactivated')
                            then account_id end)                as active_accounts,
        count(distinct case when retention_status = 'churned'
                            then account_id end)                as churned_accounts,
        count(distinct case when retention_status = 'reactivated'
                            then account_id end)                as reactivated_accounts,

        -- MRR
        sum(mrr)                                                as cohort_mrr,
        sum(starting_mrr)                                       as cohort_starting_mrr,
        avg(mrr)                                                as avg_account_mrr,

        -- Retention rates
        {{ safe_divide(
            'count(distinct case when retention_status in (\'new\', \'retained\', \'reactivated\') then account_id end)::float',
            'nullif(count(distinct account_id), 0)'
        ) }}                                                    as logo_retention_rate,

        {{ safe_divide(
            'sum(mrr)::float',
            'nullif(sum(starting_mrr), 0)'
        ) }}                                                    as revenue_retention_rate,

        -- Segment breakdowns (for filtering)
        mode() within group (order by industry)                 as dominant_industry,
        mode() within group (order by company_size)             as dominant_company_size,
        mode() within group (order by acquisition_channel)      as dominant_channel

    from classified
    group by cohort_month, cohort_month_date, months_since_created
),

-- Final: account-level cohort detail (for drill-down)
final as (
    select
        {{ dbt_utils.generate_surrogate_key(['account_id', 'cohort_month', 'months_since_created']) }}
                                                                as cohort_record_key,
        c.account_id,
        c.company_name,
        c.industry,
        c.company_size,
        c.region,
        c.acquisition_channel,
        c.cohort_month,
        c.cohort_month_date,
        c.month_start_date,
        c.month_key,
        c.months_since_created,
        c.is_first_month,
        c.mrr,
        c.starting_mrr,
        c.starting_plan,
        c.plan_name,
        c.plan_tier_order,
        c.is_active_this_month,
        c.was_active_prev_month,
        c.retention_status,
        c.revenue_retention_rate,
        c.mrr_vs_starting,

        -- Cohort-level aggregates (denormalized for convenience)
        cps.total_accounts_in_cohort,
        cps.active_accounts                                     as cohort_active_accounts,
        cps.logo_retention_rate                                 as cohort_logo_retention_rate,
        cps.revenue_retention_rate                              as cohort_revenue_retention_rate,
        cps.cohort_mrr                                          as cohort_total_mrr

    from classified c
    left join cohort_period_summary cps
        on c.cohort_month = cps.cohort_month
        and c.months_since_created = cps.months_since_created
)

select * from final
