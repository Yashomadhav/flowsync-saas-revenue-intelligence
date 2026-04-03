-- Bronze: raw_leads
{{ config(materialized='view', tags=['bronze']) }}

SELECT
    _id, lead_id, company_name, contact_name, contact_email,
    industry, company_size, acquisition_channel, lead_source, status,
    trial_start_date, trial_end_date, converted_at, account_id,
    estimated_mrr, created_at, updated_at, _loaded_at
FROM {{ source('raw', 'raw_leads') }}
