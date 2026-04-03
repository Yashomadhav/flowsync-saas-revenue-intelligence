{{
  config(
    materialized = 'view',
    tags         = ['staging', 'leads']
  )
}}

with source as (
    select * from {{ source('raw', 'leads') }}
),
renamed as (
    select
        lead_id::uuid                                       as lead_id,
        account_id::uuid                                    as account_id,
        lower(trim(channel))                                as channel,
        lower(trim(source))                                 as source,
        lower(trim(stage))                                  as stage,
        lower(trim(industry))                               as industry,
        trim(company_size)                                  as company_size,
        created_at::timestamp with time zone                as created_at,
        trial_started_at::timestamp with time zone          as trial_started_at,
        converted_to_paid_at::timestamp with time zone      as converted_to_paid_at,
        est_deal_size::numeric(12,2)                        as est_deal_size,
        case when trial_started_at is not null then true else false end as started_trial,
        case when converted_to_paid_at is not null then true else false end as converted_paid,
        case
            when converted_to_paid_at is not null and trial_started_at is not null
            then (converted_to_paid_at::date - trial_started_at::date)
            else null
        end                                                 as trial_to_paid_days,
        date_trunc('month', created_at)::date               as lead_month,
        _loaded_at::timestamp with time zone                as _loaded_at
    from source
    where lead_id is not null
)
select * from renamed
