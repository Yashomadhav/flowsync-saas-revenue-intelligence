-- =============================================================================
-- fct_mrr_movements.sql  (Marts / Gold Layer)
-- Fact: MRR movements per account per month
-- Grain: one row per account per month with full movement breakdown
-- Powers: Revenue Movements dashboard, MRR bridge chart, waterfall
-- =============================================================================

{{ config(
    materialized='incremental',
    unique_key='account_month_key',
    indexes=[
        {'columns': ['month_start_date'], 'type': 'btree'},
        {'columns': ['account_id'],       'type': 'btree'},
        {'columns': ['mrr_movement_type'],'type': 'btree'},
    ]
) }}

with sub_mrr as (
    -- Aggregate subscription-level MRR to account-month grain
    select
        account_id,
        company_name,
        industry,
        company_size,
        region,
        acquisition_channel,
        plan_name,
        plan_tier_order,
        month_start_date,
        month_key,
        sum(mrr)                                                as total_mrr,
        sum(prev_month_mrr)                                     as prev_total_mrr,
        sum(mrr_delta)                                          as total_mrr_delta,
        -- Aggregate movement type (take the most significant)
        max(mrr_movement_type)                                  as mrr_movement_type,
        min(account_month_rank)                                 as account_month_rank,
        avg(seat_utilization_rate)                              as avg_seat_utilization
    from {{ ref('int_subscription_mrr') }}
    group by
        account_id, company_name, industry, company_size, region,
        acquisition_channel, plan_name, plan_tier_order,
        month_start_date, month_key
),

-- Detect churned accounts (had MRR last month, none this month)
all_account_months as (
    select
        account_id,
        month_start_date,
        month_key
    from {{ ref('int_account_months') }}
),

-- Accounts that had MRR last month but not this month = churned
churned_accounts as (
    select
        prev_month.account_id,
        curr_month.month_start_date,
        curr_month.month_key,
        prev_month.total_mrr                                    as churned_mrr
    from sub_mrr prev_month
    inner join all_account_months curr_month
        on prev_month.account_id = curr_month.account_id
        and curr_month.month_start_date = prev_month.month_start_date + interval '1 month'
    where prev_month.total_mrr > 0
      and not exists (
          select 1 from sub_mrr next_month
          where next_month.account_id = prev_month.account_id
            and next_month.month_start_date = prev_month.month_start_date + interval '1 month'
            and next_month.total_mrr > 0
      )
),

-- Combine active and churned
combined as (
    -- Active accounts with MRR
    select
        {{ dbt_utils.generate_surrogate_key(['s.account_id', 's.month_key']) }}
                                                                as account_month_key,
        s.account_id,
        s.company_name,
        s.industry,
        s.company_size,
        s.region,
        s.acquisition_channel,
        s.plan_name,
        s.plan_tier_order,
        s.month_start_date,
        s.month_key,
        s.total_mrr                                             as mrr,
        coalesce(s.prev_total_mrr, 0)                           as prev_mrr,
        s.total_mrr_delta                                       as mrr_delta,
        s.mrr_movement_type,
        s.avg_seat_utilization,

        -- Movement components (for waterfall)
        case when s.mrr_movement_type = 'new'
             then s.total_mrr else 0 end                        as new_mrr,
        case when s.mrr_movement_type = 'expansion'
             then s.total_mrr_delta else 0 end                  as expansion_mrr,
        case when s.mrr_movement_type = 'contraction'
             then abs(s.total_mrr_delta) else 0 end             as contraction_mrr,
        0::numeric                                              as churned_mrr,
        case when s.mrr_movement_type = 'reactivation'
             then s.total_mrr else 0 end                        as reactivation_mrr,
        case when s.mrr_movement_type = 'retained'
             then s.total_mrr else 0 end                        as retained_mrr,

        false                                                   as is_churned

    from sub_mrr s

    union all

    -- Churned accounts (MRR = 0 this month, had MRR last month)
    select
        {{ dbt_utils.generate_surrogate_key(['c.account_id', 'to_char(c.month_start_date, \'YYYY-MM\')']) }}
                                                                as account_month_key,
        c.account_id,
        a.company_name,
        a.industry,
        a.company_size,
        a.region,
        a.acquisition_channel,
        null::text                                              as plan_name,
        null::integer                                           as plan_tier_order,
        c.month_start_date,
        c.month_key,
        0::numeric                                              as mrr,
        c.churned_mrr                                           as prev_mrr,
        -c.churned_mrr                                          as mrr_delta,
        'churned'                                               as mrr_movement_type,
        null::numeric                                           as avg_seat_utilization,
        0::numeric                                              as new_mrr,
        0::numeric                                              as expansion_mrr,
        0::numeric                                              as contraction_mrr,
        c.churned_mrr                                           as churned_mrr,
        0::numeric                                              as reactivation_mrr,
        0::numeric                                              as retained_mrr,
        true                                                    as is_churned

    from churned_accounts c
    left join {{ ref('stg_accounts') }} a on c.account_id = a.account_id
),

-- Add invoice payment data
invoices as (
    select
        account_id,
        to_char(invoice_date, 'YYYY-MM')                        as month_key,
        count(case when payment_status = 'failed' then 1 end)   as failed_payments,
        count(case when payment_status = 'paid'   then 1 end)   as successful_payments,
        sum(case when payment_status = 'paid' then amount_paid else 0 end)
                                                                as total_paid
    from {{ ref('stg_invoices') }}
    group by account_id, to_char(invoice_date, 'YYYY-MM')
),

final as (
    select
        c.*,
        coalesce(i.failed_payments, 0)                          as failed_payments,
        coalesce(i.successful_payments, 0)                      as successful_payments,
        coalesce(i.total_paid, 0)                               as total_invoiced_paid,

        -- Payment failure flag
        (coalesce(i.failed_payments, 0) > 0)                    as has_payment_failure,

        -- Net MRR contribution
        c.new_mrr + c.expansion_mrr + c.reactivation_mrr
        - c.contraction_mrr - c.churned_mrr                     as net_mrr_contribution,

        -- ARR equivalent
        c.mrr * 12                                              as arr

    from combined c
    left join invoices i
        on c.account_id = i.account_id
        and c.month_key = i.month_key
)

select * from final

{% if is_incremental() %}
    where month_start_date >= (select max(month_start_date) - interval '2 months' from {{ this }})
{% endif %}
