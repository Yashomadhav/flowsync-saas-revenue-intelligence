-- Silver: stg_accounts
-- Cleaned, typed, and deduplicated accounts
{{ config(materialized='table', tags=['silver']) }}

WITH source AS (
    SELECT * FROM {{ ref('raw_accounts') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY _loaded_at DESC) AS rn
    FROM source
    WHERE account_id IS NOT NULL
      AND account_id != ''
),

cleaned AS (
    SELECT
        account_id::UUID                                    AS account_id,
        TRIM(company_name)                                  AS company_name,
        INITCAP(TRIM(industry))                             AS industry,
        TRIM(region)                                        AS region,
        TRIM(country)                                       AS country,
        CASE
            WHEN UPPER(company_size) IN ('SMB', 'MID-MARKET', 'ENTERPRISE')
                THEN INITCAP(company_size)
            WHEN NULLIF(employee_count, '')::INTEGER <= 50  THEN 'SMB'
            WHEN NULLIF(employee_count, '')::INTEGER <= 500 THEN 'Mid-Market'
            ELSE 'Enterprise'
        END                                                 AS company_size,
        NULLIF(employee_count, '')::INTEGER                 AS employee_count,
        NULLIF(founded_year, '')::INTEGER                   AS founded_year,
        LOWER(TRIM(website))                                AS website,
        COALESCE(NULLIF(acquisition_channel, ''), 'Unknown') AS acquisition_channel,
        NULLIF(created_at, '')::TIMESTAMPTZ                 AS created_at,
        NULLIF(updated_at, '')::TIMESTAMPTZ                 AS updated_at,
        _loaded_at
    FROM deduped
    WHERE rn = 1
)

SELECT * FROM cleaned
