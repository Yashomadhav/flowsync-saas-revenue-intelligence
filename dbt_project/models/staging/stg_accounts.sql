{{
  config(
    materialized = 'view',
    tags         = ['staging', 'accounts']
  )
}}

/*
  stg_accounts
  ─────────────────────────────────────────────────────────────────────────────
  Cleans and types the raw accounts source.
  One row per account. Adds derived firmographic buckets.
*/

with source as (

    select * from {{ source('raw', 'accounts') }}

),

renamed as (

    select
        -- Primary key
        account_id::uuid                                    as account_id,

        -- Firmographics
        trim(company_name)                                  as company_name,
        lower(trim(industry))                               as industry,
        upper(trim(region))                                 as region,
        trim(company_size)                                  as company_size,
        lower(trim(acquisition_channel))                    as acquisition_channel,
        lower(trim(country))                                as country,

        -- Derived: numeric employee midpoint for sorting
        case trim(company_size)
            when '1-10'      then 5
            when '11-50'     then 30
            when '51-200'    then 125
            when '201-1000'  then 600
            when '1000+'     then 2500
            else null
        end                                                 as employee_midpoint,

        -- Derived: company size tier
        case trim(company_size)
            when '1-10'      then 'smb'
            when '11-50'     then 'smb'
            when '51-200'    then 'mid_market'
            when '201-1000'  then 'enterprise'
            when '1000+'     then 'enterprise'
            else 'unknown'
        end                                                 as size_tier,

        -- Timestamps
        created_at::timestamp with time zone                as created_at,
        coalesce(
            updated_at::timestamp with time zone,
            created_at::timestamp with time zone
        )                                                   as updated_at,

        -- ETL metadata
        _loaded_at::timestamp with time zone                as _loaded_at,
        _source_file                                        as _source_file

    from source
    where account_id is not null
      and company_name is not null

)

select * from renamed
