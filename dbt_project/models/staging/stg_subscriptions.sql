{{
  config(
    materialized = 'view',
    tags         = ['staging', 'subscriptions']
  )
}}

/*
  stg_subscriptions
  ─────────────────────────────────────────────────────────────────────────────
  Cleans and types raw subscription records.
  Adds derived MRR, billing interval, and lifecycle state columns.
*/

with source as (

    select * from {{ source('raw', 'subscriptions') }}

),

renamed as (

    select
        -- Primary key
        subscription_id::uuid                               as subscription_id,

        -- Foreign keys
        account_id::uuid                                    as account_id,
        plan_id::uuid                                       as plan_id,

        -- Subscription details
        lower(trim(status))                                 as status,
        lower(trim(billing_interval))                       as billing_interval,  -- monthly | annual
        mrr::numeric(12,2)                                  as mrr,
        arr::numeric(12,2)                                  as arr,
        seats::integer                                      as seats,
        discount_pct::numeric(5,2)                          as discount_pct,

        -- Dates
        start_date::date                                    as start_date,
        end_date::date                                      as end_date,
        trial_start_date::date                              as trial_start_date,
        trial_end_date::date                                as trial_end_date,
        cancelled_at::timestamp with time zone              as cancelled_at,

        -- Derived: is currently active
        case
            when lower(trim(status)) = 'active'
             and (end_date is null or end_date::date >= current_date)
            then true
            else false
        end                                                 as is_active,

        -- Derived: is in trial
        case
            when lower(trim(status)) = 'trial' then true
            else false
        end                                                 as is_trial,

        -- Derived: tenure in months
        date_part('month',
            age(
                coalesce(end_date::date, current_date),
                start_date::date
            )
        ) + date_part('year',
            age(
                coalesce(end_date::date, current_date),
                start_date::date
            )
        ) * 12                                              as tenure_months,

        -- Derived: is annual billing (discount indicator)
        case when lower(trim(billing_interval)) = 'annual' then true else false end
                                                            as is_annual,

        -- ETL metadata
        _loaded_at::timestamp with time zone                as _loaded_at

    from source
    where subscription_id is not null
      and account_id is not null
      and plan_id is not null

)

select * from renamed
