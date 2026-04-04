-- =============================================================================
-- stg_features.sql
-- Silver layer: cleaned product feature catalog
-- =============================================================================

with source as (
    select * from {{ source('raw', 'raw_features') }}
),

renamed as (
    select
        -- Primary key
        feature_id::uuid                                        as feature_id,
        trim(feature_name)                                      as feature_name,
        trim(feature_slug)                                      as feature_slug,

        -- Classification
        trim(feature_category)                                  as feature_category,
        trim(feature_tier)                                      as feature_tier,

        -- Tier ordering for sorting
        case trim(feature_tier)
            when 'starter'    then 1
            when 'growth'     then 2
            when 'business'   then 3
            when 'enterprise' then 4
            else 99
        end                                                     as tier_order,

        -- Availability flags
        is_core::boolean                                        as is_core,
        is_premium::boolean                                     as is_premium,
        is_beta::boolean                                        as is_beta,
        is_deprecated::boolean                                  as is_deprecated,

        -- Engagement metadata
        coalesce(avg_weekly_usage_per_account::numeric, 0)      as avg_weekly_usage_per_account,
        coalesce(adoption_rate_pct::numeric, 0)                 as adoption_rate_pct,

        -- Descriptions
        trim(description)                                       as description,
        trim(documentation_url)                                 as documentation_url,

        -- Timestamps
        released_at::date                                       as released_at,
        deprecated_at::date                                     as deprecated_at,
        created_at::timestamp with time zone                    as created_at,
        updated_at::timestamp with time zone                    as updated_at,

        -- Metadata
        _loaded_at,
        _source_file

    from source
    where feature_id is not null
      and is_deprecated::boolean is false
),

-- Add feature importance score (used in health scoring)
with_importance as (
    select
        *,
        case
            when is_core and tier_order <= 2 then 'high'
            when is_core and tier_order > 2  then 'medium'
            when is_premium                  then 'medium'
            else 'low'
        end                                                     as importance_tier,

        -- Weight for health score calculation
        case
            when is_core and tier_order <= 2 then 3.0
            when is_core and tier_order > 2  then 2.0
            when is_premium                  then 1.5
            else 1.0
        end                                                     as health_weight

    from renamed
)

select * from with_importance
