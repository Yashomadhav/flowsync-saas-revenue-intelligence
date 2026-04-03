{{
  config(
    materialized = 'view',
    tags         = ['staging', 'invoices']
  )
}}

/*
  stg_invoices
  ─────────────────────────────────────────────────────────────────────────────
  Cleans and types raw invoice records.
  Adds payment status flags and days-to-pay calculations.
*/

with source as (

    select * from {{ source('raw', 'invoices') }}

),

renamed as (

    select
        -- Primary key
        invoice_id::uuid                                    as invoice_id,

        -- Foreign keys
        account_id::uuid                                    as account_id,
        subscription_id::uuid                               as subscription_id,

        -- Invoice details
        amount::numeric(12,2)                               as amount,
        lower(trim(status))                                 as status,
        lower(trim(currency))                               as currency,

        -- Dates
        invoice_date::date                                  as invoice_date,
        due_date::date                                      as due_date,
        paid_date::date                                     as paid_date,

        -- Derived: payment flags
        case when lower(trim(status)) = 'paid'    then true else false end
                                                            as is_paid,
        case when lower(trim(status)) = 'failed'  then true else false end
                                                            as is_failed,
        case when lower(trim(status)) = 'pending' then true else false end
                                                            as is_pending,
        case when lower(trim(status)) = 'refunded' then true else false end
                                                            as is_refunded,

        -- Derived: days to pay (null if not paid)
        case
            when lower(trim(status)) = 'paid' and paid_date is not null
            then (paid_date::date - invoice_date::date)
            else null
        end                                                 as days_to_pay,

        -- Derived: is overdue (past due date and not paid)
        case
            when lower(trim(status)) not in ('paid', 'void', 'refunded')
             and due_date::date < current_date
            then true
            else false
        end                                                 as is_overdue,

        -- Derived: billing month (for aggregation)
        date_trunc('month', invoice_date::date)::date       as billing_month,

        -- ETL metadata
        _loaded_at::timestamp with time zone                as _loaded_at

    from source
    where invoice_id is not null
      and account_id is not null
      and amount is not null
      and amount::numeric > 0

)

select * from renamed
