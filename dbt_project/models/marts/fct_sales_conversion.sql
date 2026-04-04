-- =============================================================================
-- fct_sales_conversion.sql  (Marts / Gold Layer)
-- Fact: Sales funnel conversion metrics per lead
-- Grain: one row per lead (with funnel stage, durations, conversion flags)
-- Powers: Funnel & Growth dashboard
-- =============================================================================

{{ config(
    materialized='table',
    indexes=[
        {'columns': ['funnel_stage'],           'type': 'btree'},
        {'columns': ['acquisition_channel'],    'type': 'btree'},
        {'columns': ['lead_created_month'],     'type': 'btree'},
        {'columns': ['is_paid_conversion'],     'type': 'btree'},
    ]
) }}

with funnel as (
    select
        lead_id,
        account_id,
        acquisition_channel,
        lead_source,
        lead_status,
        funnel_stage,
        funnel_stage_order,
        lead_created_at,
        trial_started_at,
        paid_converted_at,
        is_lead,
        is_trial,
        is_paid_conversion,
        is_lost,
        days_lead_to_trial,
        days_trial_to_paid,
        days_lead_to_paid,
        conversion_velocity,
        trial_engagement_score,
        lead_score
    from {{ ref('int_funnel_progression') }}
),

-- Join account attributes for segmentation
accounts as (
    select
        account_id,
        company_name,
        company_size,
        industry,
        region,
        plan_name
    from {{ ref('stg_accounts') }}
),

-- Join subscription data for first-month MRR
subscriptions as (
    select
        account_id,
        min(start_date)                                         as first_sub_date,
        sum(mrr)                                                as first_month_mrr,
        max(plan_name)                                          as plan_name
    from {{ ref('stg_subscriptions') }}
    where subscription_status = 'active'
    group by account_id
),

joined as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['f.lead_id']) }}   as conversion_key,

        f.lead_id,
        f.account_id,
        f.acquisition_channel,
        f.lead_source,
        f.lead_status,
        f.funnel_stage,
        f.funnel_stage_order,

        -- Timestamps
        f.lead_created_at,
        f.trial_started_at,
        f.paid_converted_at,
        to_char(f.lead_created_at, 'YYYY-MM')                   as lead_created_month,
        to_char(f.trial_started_at, 'YYYY-MM')                  as trial_started_month,
        to_char(f.paid_converted_at, 'YYYY-MM')                 as paid_converted_month,

        -- Conversion flags
        f.is_lead,
        f.is_trial,
        f.is_paid_conversion,
        f.is_lost,

        -- Duration metrics
        f.days_lead_to_trial,
        f.days_trial_to_paid,
        f.days_lead_to_paid,
        f.conversion_velocity,

        -- Engagement
        f.trial_engagement_score,
        f.lead_score,

        -- Account attributes
        coalesce(a.company_name, 'Unknown')                     as company_name,
        coalesce(a.company_size, 'unknown')                     as company_size,
        coalesce(a.industry, 'unknown')                         as industry,
        coalesce(a.region, 'unknown')                           as region,

        -- Subscription data (for converted leads)
        s.first_sub_date,
        coalesce(s.first_month_mrr, 0)                          as first_month_mrr,
        coalesce(s.plan_name, a.plan_name)                      as plan_name,

        -- Revenue impact
        case
            when f.is_paid_conversion then coalesce(s.first_month_mrr, 0)
            else 0
        end                                                     as converted_mrr,

        case
            when f.is_paid_conversion then coalesce(s.first_month_mrr, 0) * 12
            else 0
        end                                                     as converted_arr,

        -- Velocity classification
        case
            when f.days_lead_to_paid <= 14  then 'fast'
            when f.days_lead_to_paid <= 30  then 'normal'
            when f.days_lead_to_paid <= 60  then 'slow'
            when f.days_lead_to_paid is not null then 'very_slow'
            else 'in_progress'
        end                                                     as sales_cycle_bucket,

        -- Trial quality classification
        case
            when f.trial_engagement_score >= 80 then 'high_engagement'
            when f.trial_engagement_score >= 50 then 'medium_engagement'
            when f.trial_engagement_score >= 20 then 'low_engagement'
            when f.trial_engagement_score is not null then 'minimal_engagement'
            else 'no_trial'
        end                                                     as trial_quality

    from funnel f
    left join accounts a on f.account_id = a.account_id
    left join subscriptions s on f.account_id = s.account_id
),

-- Monthly funnel summary (for trend charts)
monthly_summary as (
    select
        lead_created_month                                      as month_key,
        acquisition_channel,
        company_size,
        plan_name,
        count(*)                                                as total_leads,
        count(case when is_trial then 1 end)                    as trial_starts,
        count(case when is_paid_conversion then 1 end)          as paid_conversions,
        count(case when is_lost then 1 end)                     as lost_leads,
        {{ safe_divide(
            'count(case when is_trial then 1 end)',
            'count(*)'
        ) }}                                                    as lead_to_trial_rate,
        {{ safe_divide(
            'count(case when is_paid_conversion then 1 end)',
            'count(case when is_trial then 1 end)'
        ) }}                                                    as trial_to_paid_rate,
        {{ safe_divide(
            'count(case when is_paid_conversion then 1 end)',
            'count(*)'
        ) }}                                                    as overall_conversion_rate,
        avg(case when is_paid_conversion then days_lead_to_paid end)
                                                                as avg_days_to_convert,
        avg(case when is_trial then trial_engagement_score end) as avg_trial_engagement,
        sum(converted_mrr)                                      as total_converted_mrr,
        avg(case when is_paid_conversion then first_month_mrr end)
                                                                as avg_first_month_mrr
    from joined
    group by lead_created_month, acquisition_channel, company_size, plan_name
)

-- Final output: lead-level grain with monthly summary columns joined
select
    j.*,
    ms.total_leads                                              as channel_month_total_leads,
    ms.trial_starts                                             as channel_month_trial_starts,
    ms.paid_conversions                                         as channel_month_paid_conversions,
    round(ms.lead_to_trial_rate::numeric, 4)                    as channel_lead_to_trial_rate,
    round(ms.trial_to_paid_rate::numeric, 4)                    as channel_trial_to_paid_rate,
    round(ms.overall_conversion_rate::numeric, 4)               as channel_overall_conversion_rate,
    round(ms.avg_days_to_convert::numeric, 1)                   as channel_avg_days_to_convert,
    round(ms.avg_trial_engagement::numeric, 1)                  as channel_avg_trial_engagement,
    round(ms.total_converted_mrr::numeric, 2)                   as channel_month_converted_mrr,
    round(ms.avg_first_month_mrr::numeric, 2)                   as channel_avg_first_month_mrr

from joined j
left join monthly_summary ms
    on j.lead_created_month = ms.month_key
    and j.acquisition_channel = ms.acquisition_channel
    and j.company_size = ms.company_size
    and coalesce(j.plan_name, 'unknown') = coalesce(ms.plan_name, 'unknown')
