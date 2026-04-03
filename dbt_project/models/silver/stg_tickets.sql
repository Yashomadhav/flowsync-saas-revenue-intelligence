-- Silver: stg_tickets
-- Cleaned support tickets with SLA and resolution metrics
{{ config(materialized='table', tags=['silver']) }}

WITH source AS (
    SELECT * FROM {{ ref('raw_tickets') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY ticket_id ORDER BY _loaded_at DESC) AS rn
    FROM source
    WHERE ticket_id IS NOT NULL AND ticket_id != ''
),

cleaned AS (
    SELECT
        ticket_id::UUID                                         AS ticket_id,
        account_id::UUID                                        AS account_id,
        NULLIF(user_id, '')::UUID                               AS user_id,
        TRIM(subject)                                           AS subject,
        LOWER(TRIM(category))                                   AS category,
        LOWER(TRIM(priority))                                   AS priority,
        LOWER(TRIM(status))                                     AS status,
        NULLIF(csat_score, '')::NUMERIC                         AS csat_score,
        NULLIF(created_at, '')::TIMESTAMPTZ                     AS created_at,
        NULLIF(resolved_at, '')::TIMESTAMPTZ                    AS resolved_at,
        NULLIF(first_response_at, '')::TIMESTAMPTZ              AS first_response_at,
        DATE_TRUNC('month', NULLIF(created_at, '')::TIMESTAMPTZ) AS ticket_month,
        -- Derived: resolution time in hours
        CASE
            WHEN NULLIF(resolved_at, '') IS NOT NULL AND NULLIF(created_at, '') IS NOT NULL
                THEN ROUND(
                    EXTRACT(EPOCH FROM (
                        NULLIF(resolved_at, '')::TIMESTAMPTZ -
                        NULLIF(created_at, '')::TIMESTAMPTZ
                    )) / 3600.0, 2
                )
            ELSE NULL
        END                                                     AS resolution_hours,
        -- Derived: first response time in hours
        CASE
            WHEN NULLIF(first_response_at, '') IS NOT NULL AND NULLIF(created_at, '') IS NOT NULL
                THEN ROUND(
                    EXTRACT(EPOCH FROM (
                        NULLIF(first_response_at, '')::TIMESTAMPTZ -
                        NULLIF(created_at, '')::TIMESTAMPTZ
                    )) / 3600.0, 2
                )
            ELSE NULL
        END                                                     AS first_response_hours,
        -- Derived: is resolved
        CASE WHEN LOWER(status) = 'resolved' THEN TRUE ELSE FALSE END AS is_resolved,
        -- Derived: is high priority
        CASE WHEN LOWER(priority) IN ('high', 'critical', 'urgent') THEN TRUE ELSE FALSE END AS is_high_priority,
        -- Derived: is open (unresolved)
        CASE WHEN LOWER(status) IN ('open', 'pending', 'in_progress') THEN TRUE ELSE FALSE END AS is_open,
        _loaded_at
    FROM deduped
    WHERE rn = 1
      AND account_id IS NOT NULL AND account_id != ''
)

SELECT * FROM cleaned
