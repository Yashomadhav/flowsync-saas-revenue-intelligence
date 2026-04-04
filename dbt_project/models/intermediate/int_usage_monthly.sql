-- =============================================================================
-- int_usage_monthly.sql
-- Intermediate: Monthly product usage aggregates per account
-- Powers health scoring, churn risk, and feature adoption analytics
-- =============================================================================

{{ config(materialized='incremental', unique_key='account_month_key') }}

with usage_events as (
    select
        event_id,
        account_id,
        user_id,
        feature_id,
        event_type,
        occurred_at,
        session_id,
        duration_seconds
    from {{ ref('stg_usage_events') }}
),

features as (
    select feature_id, feature_name, feature_category, feature_tier,
           is_core, is_premium, health_weight, importance_tier
    from {{ ref('stg_features') }}
),

calendar as (
    select month_start_date, month_key
    from {{ ref('stg_calendar') }}
    where calendar_date = month_start_date
),

-- Aggregate usage events to monthly grain per account
monthly_usage as (
    select
        u.account_id,
        c.month_key,
        c.month_start_date,

        -- Volume metrics
        count(distinct u.event_id)                              as total_events,
        count(distinct u.user_id)                               as active_users,
        count(distinct u.session_id)                            as total_sessions,
        count(distinct u.feature_id)                            as distinct_features_used,

        -- Engagement depth
        sum(u.duration_seconds)                                 as total_duration_seconds,
        avg(u.duration_seconds)                                 as avg_session_duration_seconds,
        count(distinct u.event_id)::float
            / nullif(count(distinct date_trunc('day', u.occurred_at)), 0)
                                                                as avg_events_per_active_day,

        -- Active days
        count(distinct date_trunc('day', u.occurred_at))        as active_days_in_month,

        -- Core feature usage
        count(distinct case when f.is_core then u.feature_id end)
                                                                as core_features_used,

        -- Premium feature usage
        count(distinct case when f.is_premium then u.feature_id end)
                                                                as premium_features_used,

        -- Weighted feature adoption score (sum of health_weights for used features)
        sum(distinct case when u.feature_id is not null then f.health_weight else 0 end)
                                                                as feature_adoption_score,

        -- Last activity date
        max(u.occurred_at)::date                                as last_active_date,

        -- Days since last activity (as of month end)
        extract(day from
            (c.month_start_date + interval '1 month - 1 day') - max(u.occurred_at)::date
        )::integer                                              as days_since_last_activity

    from usage_events u
    inner join calendar c
        on date_trunc('month', u.occurred_at) = c.month_start_date
    left join features f on u.feature_id = f.feature_id
    group by u.account_id, c.month_key, c.month_start_date
),

-- Add month-over-month comparison
with_mom as (
    select
        mu.*,

        -- Previous month metrics for MoM comparison
        lag(mu.total_events) over (
            partition by mu.account_id order by mu.month_start_date
        )                                                       as prev_month_events,

        lag(mu.active_users) over (
            partition by mu.account_id order by mu.month_start_date
        )                                                       as prev_month_active_users,

        lag(mu.distinct_features_used) over (
            partition by mu.account_id order by mu.month_start_date
        )                                                       as prev_month_features_used

    from monthly_usage mu
),

-- Calculate MoM deltas and risk flags
final as (
    select
        {{ dbt_utils.generate_surrogate_key(['account_id', 'month_key']) }}
                                                                as account_month_key,
        wm.*,

        -- MoM event change
        wm.total_events - coalesce(wm.prev_month_events, 0)    as events_mom_delta,

        -- MoM event change rate
        {{ safe_divide(
            '(wm.total_events - coalesce(wm.prev_month_events, 0))::float',
            'nullif(wm.prev_month_events, 0)'
        ) }}                                                    as events_mom_pct_change,

        -- Usage drop flag (>40% decline)
        case
            when wm.prev_month_events > 0
             and {{ safe_divide(
                    '(wm.total_events - wm.prev_month_events)::float',
                    'wm.prev_month_events'
                 ) }} < -0.40
            then true else false
        end                                                     as has_usage_drop_flag,

        -- No login flag (no activity in last 14 days of month)
        case
            when wm.days_since_last_activity >= 14 then true else false
        end                                                     as has_no_login_flag,

        -- Usage intensity bucket
        case
            when wm.total_events >= 500  then 'power_user'
            when wm.total_events >= 100  then 'regular'
            when wm.total_events >= 20   then 'occasional'
            when wm.total_events > 0     then 'minimal'
            else 'inactive'
        end                                                     as usage_intensity

    from with_mom wm
)

select * from final

{% if is_incremental() %}
    where month_start_date >= (select max(month_start_date) - interval '2 months' from {{ this }})
{% endif %}
