-- =============================================================================
-- stg_customers.sql
-- Silver layer: cleaned and typed customer/user records
-- =============================================================================

with source as (
    select * from {{ source('raw', 'raw_accounts') }}
    -- Note: customers are derived from accounts in this data model
    -- Each account has a primary contact (customer) record
),

renamed as (
    select
        -- Primary key
        {{ dbt_utils.generate_surrogate_key(['account_id']) }} as customer_id,
        account_id::uuid                                        as account_id,

        -- Identity
        trim(company_name)                                      as company_name,
        lower(trim(primary_contact_email))                      as email,
        trim(primary_contact_name)                              as full_name,
        split_part(trim(primary_contact_name), ' ', 1)         as first_name,
        split_part(trim(primary_contact_name), ' ', 2)         as last_name,

        -- Role / persona
        trim(primary_contact_title)                             as job_title,
        case
            when lower(primary_contact_title) like '%ceo%'
              or lower(primary_contact_title) like '%founder%'
              or lower(primary_contact_title) like '%president%'
                then 'C-Suite'
            when lower(primary_contact_title) like '%cto%'
              or lower(primary_contact_title) like '%cio%'
              or lower(primary_contact_title) like '%vp%'
                then 'VP / Director'
            when lower(primary_contact_title) like '%manager%'
              or lower(primary_contact_title) like '%lead%'
                then 'Manager'
            when lower(primary_contact_title) like '%engineer%'
              or lower(primary_contact_title) like '%developer%'
              or lower(primary_contact_title) like '%analyst%'
                then 'Individual Contributor'
            else 'Other'
        end                                                     as persona_tier,

        -- Geography
        trim(country)                                           as country,
        trim(region)                                            as region,
        trim(city)                                              as city,

        -- Firmographics (from account)
        trim(industry)                                          as industry,
        trim(company_size)                                      as company_size,
        employee_count::integer                                 as employee_count,

        -- Acquisition
        trim(acquisition_channel)                               as acquisition_channel,
        trim(lead_source)                                       as lead_source,

        -- Timestamps
        created_at::timestamp with time zone                    as created_at,
        updated_at::timestamp with time zone                    as updated_at,

        -- Derived: tenure in days
        extract(day from now() - created_at::timestamp)::integer as tenure_days,

        -- Derived: tenure bucket
        case
            when extract(day from now() - created_at::timestamp) < 90   then '0-3 months'
            when extract(day from now() - created_at::timestamp) < 180  then '3-6 months'
            when extract(day from now() - created_at::timestamp) < 365  then '6-12 months'
            when extract(day from now() - created_at::timestamp) < 730  then '1-2 years'
            else '2+ years'
        end                                                     as tenure_bucket,

        -- Status flags
        is_active::boolean                                      as is_active,
        case
            when lower(account_status) = 'churned' then true
            else false
        end                                                     as is_churned,

        -- Metadata
        _loaded_at,
        _source_file

    from source
    where primary_contact_email is not null
      and primary_contact_email != ''
)

select * from renamed
