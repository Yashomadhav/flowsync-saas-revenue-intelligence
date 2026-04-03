{{
  config(
    materialized = 'view',
    tags         = ['staging', 'plans']
  )
}}

/*
  stg_plans
  ─────────────────────────────────────────────────────────────────────────────
  Cleans and types the raw plans catalog.
  One row per plan. Adds tier ordering for sorting.
*/

with source as (

    select * from {{ source('raw', 'plans') }}

),

renamed as (

    select
        plan_id::uuid                                       as plan_id,
        lower(trim(plan_name))                              as plan_name,
        trim(plan_display_name)                             as plan_display_name,
        monthly_price::numeric(10,2)                        as monthly_price,
        annual_price::numeric(10,2)                         as annual_price,
        max_seats::integer                                  as max_seats,
        max_workflows::integer                              as max_workflows,
        has_sso::boolean                                    as has_sso,
        has_api_access::boolean                             as has_api_access,
        has_advanced_analytics::boolean                     as has_advanced_analytics,
        support_tier                                        as support_tier,

        -- Derived: plan tier order (for sorting)
        case lower(trim(plan_name))
            when 'starter'    then 1
            when 'growth'     then 2
            when 'business'   then 3
            when 'enterprise' then 4
            else 99
        end                                                 as plan_tier_order,

        -- Derived: is enterprise
        case when lower(trim(plan_name)) = 'enterprise' then true else false end
                                                            as is_enterprise,

        _loaded_at::timestamp with time zone                as _loaded_at

    from source
    where plan_id is not null
      and plan_name is not null

)

select * from renamed
