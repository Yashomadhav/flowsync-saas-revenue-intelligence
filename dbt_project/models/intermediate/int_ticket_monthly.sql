-- =============================================================================
-- int_ticket_monthly.sql
-- Intermediate: Monthly support ticket aggregates per account
-- Powers health scoring (support burden) and churn risk signals
-- =============================================================================

{{ config(materialized='incremental', unique_key='account_month_key') }}

with tickets as (
    select
        ticket_id,
        account_id,
        priority,
        status,
        category,
        csat_score,
        created_at,
        resolved_at,
        first_response_at,
        is_escalated
    from {{ ref('stg_support_tickets') }}
),

calendar as (
    select month_start_date, month_key
    from {{ ref('stg_calendar') }}
    where calendar_date = month_start_date
),

-- Aggregate tickets to monthly grain per account
monthly_tickets as (
    select
        t.account_id,
        c.month_key,
        c.month_start_date,

        -- Volume
        count(t.ticket_id)                                      as total_tickets,
        count(case when t.priority = 'critical' then 1 end)     as critical_tickets,
        count(case when t.priority = 'high'     then 1 end)     as high_tickets,
        count(case when t.priority = 'medium'   then 1 end)     as medium_tickets,
        count(case when t.priority = 'low'      then 1 end)     as low_tickets,

        -- Status breakdown
        count(case when t.status in ('open', 'in_progress') then 1 end)
                                                                as open_tickets,
        count(case when t.status = 'resolved' then 1 end)       as resolved_tickets,
        count(case when t.status = 'escalated' then 1 end)      as escalated_tickets,

        -- Unresolved high-priority (risk flag)
        count(case when t.priority in ('high', 'critical')
                    and t.status in ('open', 'in_progress', 'escalated')
                   then 1 end)                                  as unresolved_high_priority,

        -- CSAT
        avg(t.csat_score)                                       as avg_csat_score,
        count(case when t.csat_score is not null then 1 end)    as csat_responses,
        count(case when t.csat_score < 3 then 1 end)            as low_csat_count,

        -- Resolution time (hours)
        avg(
            case when t.resolved_at is not null
            then extract(epoch from (t.resolved_at - t.created_at)) / 3600.0
            end
        )                                                       as avg_resolution_hours,

        -- First response time (hours)
        avg(
            case when t.first_response_at is not null
            then extract(epoch from (t.first_response_at - t.created_at)) / 3600.0
            end
        )                                                       as avg_first_response_hours,

        -- Escalation rate
        {{ safe_divide(
            'count(case when t.is_escalated then 1 end)::float',
            'nullif(count(t.ticket_id), 0)'
        ) }}                                                    as escalation_rate,

        -- Resolution rate
        {{ safe_divide(
            'count(case when t.status = \'resolved\' then 1 end)::float',
            'nullif(count(t.ticket_id), 0)'
        ) }}                                                    as resolution_rate

    from tickets t
    inner join calendar c
        on date_trunc('month', t.created_at) = c.month_start_date
    group by t.account_id, c.month_key, c.month_start_date
),

-- Add MoM comparison and risk flags
with_flags as (
    select
        {{ dbt_utils.generate_surrogate_key(['account_id', 'month_key']) }}
                                                                as account_month_key,
        mt.*,

        -- Previous month ticket count
        lag(mt.total_tickets) over (
            partition by mt.account_id order by mt.month_start_date
        )                                                       as prev_month_tickets,

        -- Risk flags
        -- Flag: 2+ unresolved high-priority tickets
        case
            when mt.unresolved_high_priority >= 2 then true else false
        end                                                     as has_high_priority_flag,

        -- Flag: CSAT below 3
        case
            when mt.avg_csat_score < 3 and mt.csat_responses > 0 then true else false
        end                                                     as has_low_csat_flag,

        -- Support burden score (0-100, higher = more burden)
        least(100,
            (mt.total_tickets * 5)
            + (mt.critical_tickets * 20)
            + (mt.high_tickets * 10)
            + (mt.unresolved_high_priority * 15)
            + (case when mt.avg_csat_score < 3 then 20 else 0 end)
        )                                                       as support_burden_score,

        -- Support health component (inverse of burden, 0-100)
        greatest(0,
            100 - least(100,
                (mt.total_tickets * 5)
                + (mt.critical_tickets * 20)
                + (mt.high_tickets * 10)
                + (mt.unresolved_high_priority * 15)
                + (case when mt.avg_csat_score < 3 then 20 else 0 end)
            )
        )                                                       as support_health_score

    from monthly_tickets mt
)

select * from with_flags

{% if is_incremental() %}
    where month_start_date >= (select max(month_start_date) - interval '2 months' from {{ this }})
{% endif %}
