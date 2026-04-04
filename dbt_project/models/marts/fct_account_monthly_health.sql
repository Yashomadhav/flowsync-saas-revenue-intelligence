-- =============================================================================
-- fct_account_monthly_health.sql  (Marts / Gold Layer)
-- Fact: Account health score and churn risk per month
-- Grain: one row per account per month
-- Powers: Customer Health & Churn Risk dashboard
-- =============================================================================

{{ config(
    materialized='incremental',
    unique_key='account_month_key',
    indexes=[
        {'columns': ['month_start_date'],  'type': 'btree'},
        {'columns': ['account_id'],        'type': 'btree'},
        {'columns': ['health_tier'],       'type': 'btree'},
        {'columns': ['churn_risk_level'],  'type': 'btree'},
    ]
) }}

with account_months as (
    select
        account_month_key,
        account_id,
        company_name,
        industry,
        company_size,
        region,
        acquisition_channel,
        month_start_date,
        month_key,
        months_since_created,
        cohort_month
    from {{ ref('int_account_months') }}
),

mrr as (
    select
        account_id,
        month_start_date,
        sum(mrr)                                                as mrr,
        sum(prev_month_mrr)                                     as prev_mrr,
        max(plan_name)                                          as plan_name,
        avg(seat_utilization_rate)                              as seat_utilization_rate,
        sum(seats_purchased)                                    as seats_purchased,
        sum(seats_used)                                         as seats_used
    from {{ ref('int_subscription_mrr') }}
    group by account_id, month_start_date
),

usage as (
    select
        account_id,
        month_start_date,
        total_events,
        active_users,
        distinct_features_used,
        feature_adoption_score,
        active_days_in_month,
        last_active_date,
        days_since_last_activity,
        usage_intensity,
        has_usage_drop_flag,
        has_no_login_flag,
        events_mom_pct_change
    from {{ ref('int_usage_monthly') }}
),

tickets as (
    select
        account_id,
        month_start_date,
        total_tickets,
        unresolved_high_priority,
        avg_csat_score,
        support_burden_score,
        support_health_score,
        has_high_priority_flag,
        has_low_csat_flag,
        escalation_rate
    from {{ ref('int_ticket_monthly') }}
),

invoices as (
    select
        account_id,
        to_char(invoice_date, 'YYYY-MM')                        as month_key,
        count(case when payment_status = 'failed' then 1 end)   as failed_payments
    from {{ ref('stg_invoices') }}
    group by account_id, to_char(invoice_date, 'YYYY-MM')
),

-- Join all signals
joined as (
    select
        am.account_month_key,
        am.account_id,
        am.company_name,
        am.industry,
        am.company_size,
        am.region,
        am.acquisition_channel,
        am.month_start_date,
        am.month_key,
        am.months_since_created,
        am.cohort_month,

        -- MRR signals
        coalesce(m.mrr, 0)                                      as mrr,
        coalesce(m.prev_mrr, 0)                                 as prev_mrr,
        m.plan_name,
        coalesce(m.seat_utilization_rate, 0)                    as seat_utilization_rate,
        coalesce(m.seats_purchased, 0)                          as seats_purchased,
        coalesce(m.seats_used, 0)                               as seats_used,

        -- Usage signals
        coalesce(u.total_events, 0)                             as total_events,
        coalesce(u.active_users, 0)                             as active_users,
        coalesce(u.distinct_features_used, 0)                   as distinct_features_used,
        coalesce(u.feature_adoption_score, 0)                   as feature_adoption_score,
        coalesce(u.active_days_in_month, 0)                     as active_days_in_month,
        u.last_active_date,
        coalesce(u.days_since_last_activity, 31)                as days_since_last_activity,
        coalesce(u.usage_intensity, 'inactive')                 as usage_intensity,
        coalesce(u.has_usage_drop_flag, false)                  as has_usage_drop_flag,
        coalesce(u.has_no_login_flag, true)                     as has_no_login_flag,
        u.events_mom_pct_change,

        -- Support signals
        coalesce(t.total_tickets, 0)                            as total_tickets,
        coalesce(t.unresolved_high_priority, 0)                 as unresolved_high_priority,
        t.avg_csat_score,
        coalesce(t.support_burden_score, 0)                     as support_burden_score,
        coalesce(t.support_health_score, 100)                   as support_health_score,
        coalesce(t.has_high_priority_flag, false)               as has_high_priority_flag,
        coalesce(t.has_low_csat_flag, false)                    as has_low_csat_flag,
        coalesce(t.escalation_rate, 0)                          as escalation_rate,

        -- Payment signals
        coalesce(i.failed_payments, 0)                          as failed_payments,
        (coalesce(i.failed_payments, 0) > 0)                    as has_payment_failure

    from account_months am
    left join mrr m
        on am.account_id = m.account_id
        and am.month_start_date = m.month_start_date
    left join usage u
        on am.account_id = u.account_id
        and am.month_start_date = u.month_start_date
    left join tickets t
        on am.account_id = t.account_id
        and am.month_start_date = t.month_start_date
    left join invoices i
        on am.account_id = i.account_id
        and am.month_key = i.month_key
    where coalesce(m.mrr, 0) > 0  -- only score accounts with active subscriptions
),

-- ── Health Score Calculation ──────────────────────────────────────────────────
-- Weighted composite out of 100:
--   Usage frequency      25%
--   Seat utilization     20%
--   Feature adoption     15%
--   Support health       15%
--   CSAT                 10%
--   Payment health       10%
--   Tenure stability      5%
scored as (
    select
        j.*,

        -- Component scores (each 0-100)

        -- 1. Usage frequency score (25%)
        case j.usage_intensity
            when 'power_user' then 100
            when 'regular'    then 80
            when 'occasional' then 50
            when 'minimal'    then 20
            else 0
        end                                                     as usage_score,

        -- 2. Seat utilization score (20%)
        case
            when j.seat_utilization_rate >= 0.80 then 100
            when j.seat_utilization_rate >= 0.60 then 80
            when j.seat_utilization_rate >= 0.40 then 60
            when j.seat_utilization_rate >= 0.25 then 40
            else 10
        end                                                     as seat_util_score,

        -- 3. Feature adoption score (15%) — normalize to 0-100
        least(100, j.feature_adoption_score * 10)               as feature_score,

        -- 4. Support health score (15%) — already 0-100
        j.support_health_score                                  as support_score,

        -- 5. CSAT score (10%) — normalize 1-5 to 0-100
        case
            when j.avg_csat_score is null then 70  -- neutral if no data
            else ((j.avg_csat_score - 1) / 4.0) * 100
        end                                                     as csat_score,

        -- 6. Payment health score (10%)
        case
            when j.failed_payments = 0 then 100
            when j.failed_payments = 1 then 50
            else 0
        end                                                     as payment_score,

        -- 7. Tenure stability score (5%)
        case
            when j.months_since_created >= 24 then 100
            when j.months_since_created >= 12 then 80
            when j.months_since_created >= 6  then 60
            when j.months_since_created >= 3  then 40
            else 20
        end                                                     as tenure_score

    from joined j
),

-- Compute weighted composite health score
with_health as (
    select
        s.*,

        -- Weighted health score (0-100)
        round(
            (s.usage_score      * 0.25)
            + (s.seat_util_score  * 0.20)
            + (s.feature_score    * 0.15)
            + (s.support_score    * 0.15)
            + (s.csat_score       * 0.10)
            + (s.payment_score    * 0.10)
            + (s.tenure_score     * 0.05)
        , 1)                                                    as health_score,

        -- Risk flags (boolean)
        s.has_usage_drop_flag                                   as risk_usage_drop,
        s.has_no_login_flag                                     as risk_no_login,
        s.has_high_priority_flag                                as risk_high_tickets,
        s.has_payment_failure                                   as risk_payment_failure,
        s.has_low_csat_flag                                     as risk_low_csat,
        (s.seat_utilization_rate < 0.25)                        as risk_low_seat_util,

        -- Count of active risk flags
        (s.has_usage_drop_flag::int
         + s.has_no_login_flag::int
         + s.has_high_priority_flag::int
         + s.has_payment_failure::int
         + s.has_low_csat_flag::int
         + (s.seat_utilization_rate < 0.25)::int)              as risk_flag_count

    from scored s
),

final as (
    select
        wh.*,

        -- Health tier classification
        case
            when wh.health_score >= 80 then 'healthy'
            when wh.health_score >= 60 then 'at_risk'
            when wh.health_score >= 40 then 'high_risk'
            else 'critical'
        end                                                     as health_tier,

        -- Churn risk level (combines health score + flag count)
        case
            when wh.health_score < 40 or wh.risk_flag_count >= 4 then 'critical'
            when wh.health_score < 60 or wh.risk_flag_count >= 3 then 'high'
            when wh.health_score < 75 or wh.risk_flag_count >= 2 then 'medium'
            when wh.health_score < 85 or wh.risk_flag_count >= 1 then 'low'
            else 'minimal'
        end                                                     as churn_risk_level,

        -- Churn risk score (0-100, higher = more risk)
        100 - wh.health_score                                   as churn_risk_score,

        -- Risk reasons (pipe-delimited string for display)
        trim(both '|' from
            case when wh.risk_usage_drop      then 'Usage drop >40%|'    else '' end ||
            case when wh.risk_no_login        then 'No login 14d|'       else '' end ||
            case when wh.risk_high_tickets    then '2+ high tickets|'    else '' end ||
            case when wh.risk_payment_failure then 'Payment failed|'     else '' end ||
            case when wh.risk_low_csat        then 'CSAT < 3|'           else '' end ||
            case when wh.risk_low_seat_util   then 'Seat util < 25%|'    else '' end
        )                                                       as risk_reasons

    from with_health wh
)

select * from final

{% if is_incremental() %}
    where month_start_date >= (select max(month_start_date) - interval '2 months' from {{ this }})
{% endif %}
