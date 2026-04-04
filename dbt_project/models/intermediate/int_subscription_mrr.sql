-- =============================================================================
-- int_subscription_mrr.sql
-- Intermediate: MRR per subscription per month with movement classification
-- Core model for all revenue waterfall / bridge calculations
-- =============================================================================

{{ config(materialized='incremental', unique_key='sub_month_key') }}

with subscriptions as (
    select
        subscription_id,
        account_id,
        plan_id,
        plan_name,
        mrr,
        status,
        billing_cycle,
        started_at,
        ended_at,
        cancelled_at,
        trial_started_at,
        trial_ended_at,
        seats_purchased,
        seats_used
    from {{ ref('stg_subscriptions') }}
),

plans as (
    select plan_id, plan_name, plan_tier_order, monthly_price
    from {{ ref('stg_plans') }}
),

accounts as (
    select account_id, company_name, industry, company_size, region, acquisition_channel
    from {{ ref('stg_accounts') }}
),

-- Month spine
months as (
    select month_start_date, month_key
    from {{ ref('stg_calendar') }}
    where calendar_date = month_start_date
      and month_start_date <= date_trunc('month', current_date)
      and month_start_date >= '2022-01-01'
),

-- Expand subscriptions across months they were active
sub_months as (
    select
        {{ dbt_utils.generate_surrogate_key(['s.subscription_id', 'm.month_key']) }}
                                                        as sub_month_key,
        s.subscription_id,
        s.account_id,
        s.plan_id,
        s.plan_name,
        s.mrr,
        s.status,
        s.billing_cycle,
        s.seats_purchased,
        s.seats_used,
        m.month_start_date,
        m.month_key,
        s.started_at::date                              as started_date,
        s.ended_at::date                                as ended_date,
        s.cancelled_at::date                            as cancelled_date

    from subscriptions s
    cross join months m
    where
        -- Subscription was active during this month
        m.month_start_date >= date_trunc('month', s.started_at::date)
        and (
            s.ended_at is null
            or m.month_start_date <= date_trunc('month', s.ended_at::date)
        )
        and s.status != 'trial'   -- exclude pure trials from MRR
),

-- Get previous month MRR per account for movement classification
with_prev as (
    select
        sm.*,
        -- Previous month MRR for this account (across all subscriptions)
        lag(sm.mrr) over (
            partition by sm.account_id
            order by sm.month_start_date
        )                                               as prev_month_mrr,

        -- Previous month plan for upgrade/downgrade detection
        lag(sm.plan_name) over (
            partition by sm.account_id
            order by sm.month_start_date
        )                                               as prev_plan_name,

        -- Is this the first month for this account?
        row_number() over (
            partition by sm.account_id
            order by sm.month_start_date
        )                                               as account_month_rank

    from sub_months sm
),

-- Classify MRR movements
classified as (
    select
        wp.*,

        -- MRR movement type
        case
            when wp.account_month_rank = 1
                then 'new'
            when wp.prev_month_mrr is null and wp.mrr > 0
                then 'reactivation'
            when wp.mrr > coalesce(wp.prev_month_mrr, 0)
                then 'expansion'
            when wp.mrr < coalesce(wp.prev_month_mrr, 0) and wp.mrr > 0
                then 'contraction'
            when wp.mrr = coalesce(wp.prev_month_mrr, 0)
                then 'retained'
            else 'retained'
        end                                             as mrr_movement_type,

        -- MRR delta (positive = growth, negative = shrinkage)
        wp.mrr - coalesce(wp.prev_month_mrr, 0)        as mrr_delta,

        -- Seat utilization rate
        {{ safe_divide('wp.seats_used', 'wp.seats_purchased') }}
                                                        as seat_utilization_rate

    from with_prev wp
),

-- Join account and plan dimensions
final as (
    select
        c.sub_month_key,
        c.subscription_id,
        c.account_id,
        a.company_name,
        a.industry,
        a.company_size,
        a.region,
        a.acquisition_channel,
        c.plan_id,
        c.plan_name,
        p.plan_tier_order,
        c.mrr,
        c.prev_month_mrr,
        c.mrr_delta,
        c.mrr_movement_type,
        c.billing_cycle,
        c.seats_purchased,
        c.seats_used,
        c.seat_utilization_rate,
        c.month_start_date,
        c.month_key,
        c.started_date,
        c.ended_date,
        c.cancelled_date,
        c.account_month_rank

    from classified c
    left join accounts a on c.account_id = a.account_id
    left join plans p on c.plan_id = p.plan_id
)

select * from final

{% if is_incremental() %}
    where month_start_date >= (select max(month_start_date) - interval '2 months' from {{ this }})
{% endif %}
