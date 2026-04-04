-- =============================================================================
-- int_funnel_progression.sql
-- Intermediate: Lead-to-trial-to-paid funnel progression tracking
-- Powers funnel conversion analytics, channel attribution, sales cycle metrics
-- =============================================================================

{{ config(materialized='table') }}

with leads as (
    select
        lead_id,
        account_id,
        contact_email,
        company_name,
        acquisition_channel,
        lead_source,
        lead_status,
        lead_score,
        industry,
        company_size,
        region,
        created_at                                              as lead_created_at,
        qualified_at,
        demo_requested_at,
        demo_completed_at,
        trial_started_at,
        trial_ended_at,
        converted_at,
        lost_at,
        lost_reason,
        assigned_to,
        estimated_arr
    from {{ ref('stg_leads') }}
),

subscriptions as (
    select
        subscription_id,
        account_id,
        plan_id,
        plan_name,
        mrr,
        started_at,
        trial_started_at,
        trial_ended_at,
        status
    from {{ ref('stg_subscriptions') }}
),

-- Get first paid subscription per account (for conversion linkage)
first_paid_sub as (
    select distinct on (account_id)
        account_id,
        subscription_id,
        plan_id,
        plan_name,
        mrr                                                     as first_mrr,
        started_at                                              as paid_started_at
    from subscriptions
    where status != 'trial'
    order by account_id, started_at asc
),

-- Enrich leads with subscription data
enriched as (
    select
        l.lead_id,
        l.account_id,
        l.contact_email,
        l.company_name,
        l.acquisition_channel,
        l.lead_source,
        l.lead_status,
        l.lead_score,
        l.industry,
        l.company_size,
        l.region,
        l.lead_created_at,
        l.qualified_at,
        l.demo_requested_at,
        l.demo_completed_at,
        l.trial_started_at,
        l.trial_ended_at,
        l.converted_at,
        l.lost_at,
        l.lost_reason,
        l.estimated_arr,

        -- Subscription linkage
        fps.subscription_id,
        fps.plan_name                                           as converted_plan,
        fps.first_mrr                                           as converted_mrr,
        fps.paid_started_at,

        -- ── Funnel Stage Classification ──────────────────────────────────────
        case
            when l.converted_at is not null or fps.paid_started_at is not null
                then 'paid'
            when l.trial_started_at is not null
                then 'trial'
            when l.demo_completed_at is not null
                then 'demo_completed'
            when l.demo_requested_at is not null
                then 'demo_requested'
            when l.qualified_at is not null
                then 'qualified'
            when l.lost_at is not null
                then 'lost'
            else 'lead'
        end                                                     as funnel_stage,

        -- ── Boolean Stage Flags ───────────────────────────────────────────────
        true                                                    as is_lead,
        (l.qualified_at is not null)                            as is_qualified,
        (l.demo_requested_at is not null)                       as is_demo_requested,
        (l.demo_completed_at is not null)                       as is_demo_completed,
        (l.trial_started_at is not null)                        as is_trial,
        (l.converted_at is not null or fps.paid_started_at is not null)
                                                                as is_paid,
        (l.lost_at is not null)                                 as is_lost,

        -- ── Duration Metrics (days) ───────────────────────────────────────────
        -- Lead to qualified
        case when l.qualified_at is not null
            then extract(day from l.qualified_at - l.lead_created_at)::integer
        end                                                     as days_lead_to_qualified,

        -- Qualified to demo
        case when l.demo_completed_at is not null and l.qualified_at is not null
            then extract(day from l.demo_completed_at - l.qualified_at)::integer
        end                                                     as days_qualified_to_demo,

        -- Demo to trial
        case when l.trial_started_at is not null and l.demo_completed_at is not null
            then extract(day from l.trial_started_at - l.demo_completed_at)::integer
        end                                                     as days_demo_to_trial,

        -- Trial to paid
        case when fps.paid_started_at is not null and l.trial_started_at is not null
            then extract(day from fps.paid_started_at - l.trial_started_at)::integer
        end                                                     as days_trial_to_paid,

        -- Total lead to paid (full sales cycle)
        case when fps.paid_started_at is not null
            then extract(day from fps.paid_started_at - l.lead_created_at)::integer
        end                                                     as days_lead_to_paid,

        -- Trial duration
        case when l.trial_ended_at is not null and l.trial_started_at is not null
            then extract(day from l.trial_ended_at - l.trial_started_at)::integer
        end                                                     as trial_duration_days,

        -- ── Month Keys for time-series analysis ───────────────────────────────
        to_char(l.lead_created_at, 'YYYY-MM')                  as lead_month,
        to_char(l.trial_started_at, 'YYYY-MM')                 as trial_month,
        to_char(coalesce(l.converted_at, fps.paid_started_at), 'YYYY-MM')
                                                                as conversion_month

    from leads l
    left join first_paid_sub fps on l.account_id = fps.account_id
),

-- Add funnel stage ordering for reporting
final as (
    select
        e.*,

        -- Numeric stage for ordering/filtering
        case e.funnel_stage
            when 'lead'           then 1
            when 'qualified'      then 2
            when 'demo_requested' then 3
            when 'demo_completed' then 4
            when 'trial'          then 5
            when 'paid'           then 6
            when 'lost'           then 0
        end                                                     as funnel_stage_order,

        -- Conversion velocity bucket
        case
            when e.days_lead_to_paid <= 14  then 'fast'
            when e.days_lead_to_paid <= 30  then 'normal'
            when e.days_lead_to_paid <= 60  then 'slow'
            when e.days_lead_to_paid > 60   then 'very_slow'
            else 'in_progress'
        end                                                     as conversion_velocity

    from enriched e
)

select * from final
