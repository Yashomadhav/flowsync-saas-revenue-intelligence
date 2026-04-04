-- =============================================================================
-- mart_customer_success_summary.sql  (Marts / Gold Layer)
-- Mart: Customer success snapshot — latest health, risk, and usage per account
-- Grain: one row per account (latest month snapshot)
-- Powers: Customer Health & Churn Risk dashboard — risk table, quadrant,
--         health distribution, support burden, usage drop trends
-- =============================================================================

{{ config(
    materialized='table',
    indexes=[
        {'columns': ['account_id'],        'type': 'btree'},
        {'columns': ['health_tier'],       'type': 'btree'},
        {'columns': ['churn_risk_level'],  'type': 'btree'},
        {'columns': ['plan_name'],         'type': 'btree'},
        {'columns': ['company_size'],      'type': 'btree'},
        {'columns': ['region'],            'type': 'btree'},
    ]
) }}

with latest_health as (
    -- Get the most recent health record per account
    select distinct on (account_id)
        account_id,
        company_name,
        industry,
        company_size,
        region,
        acquisition_channel,
        month_start_date                                        as snapshot_date,
        month_key                                               as snapshot_month,
        months_since_created,
        cohort_month,
        mrr,
        prev_mrr,
        plan_name,
        seat_utilization_rate,
        seats_purchased,
        seats_used,
        total_events,
        active_users,
        distinct_features_used,
        feature_adoption_score,
        active_days_in_month,
        last_active_date,
        days_since_last_activity,
        usage_intensity,
        events_mom_pct_change,
        total_tickets,
        unresolved_high_priority,
        avg_csat_score,
        support_burden_score,
        support_health_score,
        escalation_rate,
        failed_payments,
        health_score,
        health_tier,
        churn_risk_level,
        churn_risk_score,
        risk_flag_count,
        risk_reasons,
        risk_usage_drop,
        risk_no_login,
        risk_high_tickets,
        risk_payment_failure,
        risk_low_csat,
        risk_low_seat_util,
        usage_score,
        seat_util_score,
        feature_score,
        support_score,
        csat_score,
        payment_score,
        tenure_score
    from {{ ref('fct_account_monthly_health') }}
    order by account_id, month_start_date desc
),

-- 3-month health trend per account
health_trend as (
    select
        account_id,
        -- Health score 3 months ago
        max(case when month_rank = 3 then health_score end)     as health_score_3m_ago,
        -- Health score 1 month ago
        max(case when month_rank = 2 then health_score end)     as health_score_1m_ago,
        -- MRR 3 months ago
        max(case when month_rank = 3 then mrr end)              as mrr_3m_ago,
        -- Usage events 3 months ago
        max(case when month_rank = 3 then total_events end)     as events_3m_ago,
        -- Usage events 1 month ago
        max(case when month_rank = 2 then total_events end)     as events_1m_ago
    from (
        select
            account_id,
            health_score,
            mrr,
            total_events,
            row_number() over (
                partition by account_id
                order by month_start_date desc
            )                                                   as month_rank
        from {{ ref('fct_account_monthly_health') }}
    ) ranked
    where month_rank <= 3
    group by account_id
),

-- Lifetime MRR and tenure from subscriptions
account_lifetime as (
    select
        account_id,
        min(start_date)                                         as first_subscription_date,
        max(end_date)                                           as latest_subscription_date,
        sum(mrr)                                                as lifetime_mrr_sum,
        count(distinct subscription_id)                         as total_subscriptions
    from {{ ref('stg_subscriptions') }}
    group by account_id
),

-- Funnel data (for conversion context)
funnel_data as (
    select
        account_id,
        max(acquisition_channel)                                as lead_channel,
        max(days_lead_to_paid)                                  as days_to_convert,
        max(trial_engagement_score)                             as trial_engagement_score
    from {{ ref('fct_sales_conversion') }}
    where is_paid_conversion = true
    group by account_id
),

-- Cohort retention context
cohort_context as (
    select
        cb.account_id,
        cb.cohort_month,
        -- Latest retention status
        max(case when cb.months_since_created = 12
            then cb.retention_status end)                       as retention_status_12m,
        max(case when cb.months_since_created = 6
            then cb.retention_status end)                       as retention_status_6m,
        max(case when cb.months_since_created = 3
            then cb.retention_status end)                       as retention_status_3m
    from {{ ref('int_cohort_base') }} cb
    group by cb.account_id, cb.cohort_month
),

final as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['lh.account_id']) }}
                                                                as customer_success_key,

        -- Account identity
        lh.account_id,
        lh.company_name,
        lh.industry,
        lh.company_size,
        lh.region,
        lh.acquisition_channel,
        lh.plan_name,

        -- Snapshot timing
        lh.snapshot_date,
        lh.snapshot_month,
        lh.months_since_created,
        lh.cohort_month,

        -- Revenue
        round(lh.mrr::numeric, 2)                               as mrr,
        round(lh.mrr * 12::numeric, 2)                          as arr,
        round(coalesce(lh.prev_mrr, 0)::numeric, 2)             as prev_mrr,
        round((lh.mrr - coalesce(lh.prev_mrr, 0))::numeric, 2) as mrr_delta,

        -- Seat metrics
        lh.seats_purchased,
        lh.seats_used,
        round(lh.seat_utilization_rate::numeric, 3)             as seat_utilization_rate,

        -- Usage metrics
        lh.total_events,
        lh.active_users,
        lh.distinct_features_used,
        round(lh.feature_adoption_score::numeric, 1)            as feature_adoption_score,
        lh.active_days_in_month,
        lh.last_active_date,
        lh.days_since_last_activity,
        lh.usage_intensity,
        round(coalesce(lh.events_mom_pct_change, 0)::numeric, 2) as events_mom_pct_change,

        -- Support metrics
        lh.total_tickets,
        lh.unresolved_high_priority,
        round(coalesce(lh.avg_csat_score, 0)::numeric, 2)       as avg_csat_score,
        round(lh.support_burden_score::numeric, 1)              as support_burden_score,
        round(lh.support_health_score::numeric, 1)              as support_health_score,
        round(coalesce(lh.escalation_rate, 0)::numeric, 3)      as escalation_rate,

        -- Payment
        lh.failed_payments,

        -- ── Health Score ──────────────────────────────────────────────────────
        round(lh.health_score::numeric, 1)                      as health_score,
        lh.health_tier,
        lh.churn_risk_level,
        round(lh.churn_risk_score::numeric, 1)                  as churn_risk_score,
        lh.risk_flag_count,
        lh.risk_reasons,

        -- Risk flags
        lh.risk_usage_drop,
        lh.risk_no_login,
        lh.risk_high_tickets,
        lh.risk_payment_failure,
        lh.risk_low_csat,
        lh.risk_low_seat_util,

        -- Health score components
        round(lh.usage_score::numeric, 1)                       as usage_score,
        round(lh.seat_util_score::numeric, 1)                   as seat_util_score,
        round(lh.feature_score::numeric, 1)                     as feature_score,
        round(lh.support_score::numeric, 1)                     as support_score,
        round(lh.csat_score::numeric, 1)                        as csat_score,
        round(lh.payment_score::numeric, 1)                     as payment_score,
        round(lh.tenure_score::numeric, 1)                      as tenure_score,

        -- ── Health Trend ──────────────────────────────────────────────────────
        round(coalesce(ht.health_score_1m_ago, lh.health_score)::numeric, 1)
                                                                as health_score_1m_ago,
        round(coalesce(ht.health_score_3m_ago, lh.health_score)::numeric, 1)
                                                                as health_score_3m_ago,
        round((lh.health_score - coalesce(ht.health_score_1m_ago, lh.health_score))::numeric, 1)
                                                                as health_score_mom_delta,
        round((lh.health_score - coalesce(ht.health_score_3m_ago, lh.health_score))::numeric, 1)
                                                                as health_score_3m_delta,

        -- Health trend direction
        case
            when lh.health_score > coalesce(ht.health_score_1m_ago, lh.health_score) + 5
                then 'improving'
            when lh.health_score < coalesce(ht.health_score_1m_ago, lh.health_score) - 5
                then 'declining'
            else 'stable'
        end                                                     as health_trend,

        -- Usage trend
        round(coalesce(ht.events_3m_ago, 0)::numeric, 0)        as events_3m_ago,
        round(coalesce(ht.events_1m_ago, 0)::numeric, 0)        as events_1m_ago,

        -- ── Lifetime Metrics ──────────────────────────────────────────────────
        al.first_subscription_date,
        al.total_subscriptions,
        round(coalesce(al.lifetime_mrr_sum, 0)::numeric, 2)     as lifetime_mrr_sum,

        -- ── Acquisition Context ───────────────────────────────────────────────
        coalesce(fd.lead_channel, lh.acquisition_channel)       as lead_channel,
        fd.days_to_convert,
        round(coalesce(fd.trial_engagement_score, 0)::numeric, 1)
                                                                as trial_engagement_score,

        -- ── Cohort Retention Context ──────────────────────────────────────────
        cc.retention_status_3m,
        cc.retention_status_6m,
        cc.retention_status_12m,

        -- ── Composite Risk Priority Score ─────────────────────────────────────
        -- Higher = more urgent to address (for sorting the risk table)
        round(
            (lh.churn_risk_score * 0.5)
            + (lh.mrr * 0.0001)  -- weight by MRR impact
            + (lh.risk_flag_count * 5)
        ::numeric, 1)                                           as risk_priority_score

    from latest_health lh
    left join health_trend ht on lh.account_id = ht.account_id
    left join account_lifetime al on lh.account_id = al.account_id
    left join funnel_data fd on lh.account_id = fd.account_id
    left join cohort_context cc on lh.account_id = cc.account_id
)

select * from final
order by risk_priority_score desc
