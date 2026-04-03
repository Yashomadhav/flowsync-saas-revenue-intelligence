{{
  config(
    materialized = 'view',
    tags         = ['staging', 'usage']
  )
}}

/*
  stg_usage_events
  ─────────────────────────────────────────────────────────────────────────────
  Cleans and types raw product usage telemetry.
  Adds event date parts and session quality flags.
*/

with source as (

    select * from {{ source('raw', 'usage_events') }}

),

renamed as (

    select
        -- Primary key
        event_id::uuid                                      as event_id,

        -- Foreign keys
        account_id::uuid                                    as account_id,
        user_id::uuid                                       as user_id,

        -- Event details
        lower(trim(event_type))                             as event_type,
        lower(trim(feature_name))                           as feature_name,
        lower(trim(feature_category))                       as feature_category,
        lower(trim(platform))                               as platform,

        -- Timestamps
        event_date::date                                    as event_date,
        event_timestamp::timestamp with time zone           as event_timestamp,

        -- Metrics
        session_duration_minutes::numeric(8,2)              as session_duration_minutes,
        actions_count::integer                              as actions_count,

        -- Derived: event date parts (for aggregation)
        date_trunc('month', event_date::date)::date         as event_month,
        date_trunc('week',  event_date::date)::date         as event_week,
        extract(dow from event_date::date)::integer         as day_of_week,

        -- Derived: session quality
        case
            when session_duration_minutes::numeric >= 30 then 'deep'
            when session_duration_minutes::numeric >= 10 then 'medium'
            when session_duration_minutes::numeric >= 1  then 'light'
            else 'bounce'
        end                                                 as session_quality,

        -- Derived: is core feature usage
        case
            when lower(trim(feature_category)) in ('core', 'workflow', 'automation')
            then true else false
        end                                                 as is_core_feature,

        -- ETL metadata
        _loaded_at::timestamp with time zone                as _loaded_at

    from source
    where event_id is not null
      and account_id is not null
      and user_id is not null
      and event_date is not null

)

select * from renamed
