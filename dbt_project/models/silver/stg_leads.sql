-- Silver: stg_leads
-- Cleaned leads with funnel stage classification and conversion metrics
{{ config(materialized='table', tags=['silver']) }}

WITH source AS (
    SELECT * FROM {{ ref('raw_leads') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY lead_id ORDER BY _loaded_at DESC) AS rn
    FROM source
    WHERE lead_id IS NOT NULL AND lead_id != ''
),

cleaned AS (
    SELECT
        lead_id::UUID                                           AS lead_id,
        TRIM(company_name)                                      AS company_name,
        TRIM(contact_name)                                      AS contact_name,
        LOWER(TRIM(contact_email))                              AS contact_email,
        INITCAP(TRIM(industry))                                 AS industry,
        CASE
            WHEN UPPER(company_size) IN ('SMB', 'MID-MARKET', 'ENTERPRISE')
                THEN INITCAP(company_size)
            ELSE 'SMB'
        END                                                     AS company_size,
        COALESCE(NULLIF(acquisition_channel, ''), 'Unknown')    AS acquisition_channel,
        COALESCE(NULLIF(lead_source, ''), 'Unknown')            AS lead_source,
        LOWER(TRIM(status))                                     AS status,
        -- Funnel stage classification
        CASE
            WHEN LOWER(status) = 'converted'                    THEN 'paid'
            WHEN LOWER(status) IN ('trial', 'trial_active')     THEN 'trial'
            WHEN LOWER(status) IN ('qualified', 'demo')         THEN 'qualified'
            WHEN LOWER(status) IN ('disqualified', 'lost')      THEN 'lost'
            ELSE 'lead'
        END                                                     AS funnel_stage,
        NULLIF(trial_start_date, '')::DATE                      AS trial_start_date,
        NULLIF(trial_end_date, '')::DATE                        AS trial_end_date,
        NULLIF(converted_at, '')::TIMESTAMPTZ                   AS converted_at,
        NULLIF(account_id, '')::UUID                            AS account_id,
        NULLIF(estimated_mrr, '')::NUMERIC                      AS estimated_mrr,
        NULLIF(created_at, '')::TIMESTAMPTZ                     AS created_at,
        NULLIF(updated_at, '')::TIMESTAMPTZ                     AS updated_at,
        DATE_TRUNC('month', NULLIF(created_at, '')::TIMESTAMPTZ) AS lead_month,
        -- Derived: is converted to paid
        CASE WHEN LOWER(status) = 'converted' THEN TRUE ELSE FALSE END AS is_converted,
        -- Derived: had trial
        CASE WHEN NULLIF(trial_start_date, '') IS NOT NULL THEN TRUE ELSE FALSE END AS had_trial,
        -- Derived: trial-to-paid (had trial AND converted)
        CASE
            WHEN NULLIF(trial_start_date, '') IS NOT NULL
             AND LOWER(status) = 'converted' THEN TRUE
            ELSE FALSE
        END                                                     AS trial_converted,
        -- Derived: days from lead to conversion
        CASE
            WHEN NULLIF(converted_at, '') IS NOT NULL AND NULLIF(created_at, '') IS NOT NULL
                THEN EXTRACT(DAY FROM (
                    NULLIF(converted_at, '')::TIMESTAMPTZ -
                    NULLIF(created_at, '')::TIMESTAMPTZ
                ))::INTEGER
            ELSE NULL
        END                                                     AS days_to_convert,
        -- Derived: trial duration in days
        CASE
            WHEN NULLIF(trial_start_date, '') IS NOT NULL AND NULLIF(trial_end_date, '') IS NOT NULL
                THEN NULLIF(trial_end_date, '')::DATE - NULLIF(trial_start_date, '')::DATE
            ELSE NULL
        END                                                     AS trial_duration_days,
        _loaded_at
    FROM deduped
    WHERE rn = 1
)

SELECT * FROM cleaned
