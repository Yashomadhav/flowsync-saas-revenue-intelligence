-- Bronze: raw_accounts
-- Pass-through view of the raw accounts table loaded by the ETL pipeline
{{ config(materialized='view', tags=['bronze']) }}

SELECT
    _id,
    account_id,
    company_name,
    industry,
    region,
    country,
    company_size,
    employee_count,
    founded_year,
    website,
    acquisition_channel,
    created_at,
    updated_at,
    _loaded_at
FROM {{ source('raw', 'raw_accounts') }}
