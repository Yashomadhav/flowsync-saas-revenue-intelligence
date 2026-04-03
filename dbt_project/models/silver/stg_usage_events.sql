-- Silver: stg_usage_events
-- Cleaned usage events with session aggregations
{{ config(materialized='table', tags=['silver']) }}

WITH source AS (
    SELECT * FROM {{ ref('raw_usage_events') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY _loaded_at DESC) AS rn
    FROM source
    WHERE event_id IS NOT NULL AND event_id != ''
),

cleaned AS (
    SELECT
        event_id::UUID                                      AS event_id,
        account_id::UUID                                    AS account_id,
        NULLIF(user_id, '')::UUID                           AS user_id,
        LOWER(TRIM(feature_name))                           AS feature_name,
        LOWER(TRIM(event_type))                             AS event_type,
        NULLIF(session_id, '')::UUID                        AS session_id,
        NULLIF(duration_seconds, '')::INTEGER               AS duration_seconds,
        NULLIF(event_date, '')::DATE                        AS event_date,
        DATE_TRUNC('month', NULLIF(event_date, '')::DATE)   AS event_month,
        NULLIF(created_at, '')::TIMESTAMPTZ                 AS created_at,
        _loaded_at
    FROM deduped
    WHERE rn = 1
      AND account_id IS NOT NULL AND account_id != ''
      AND event_date IS NOT NULL AND event_date != ''
)

SELECT * FROM cleaned
