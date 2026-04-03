-- Silver: stg_subscriptions
-- Cleaned, typed subscriptions with normalized MRR
{{ config(materialized='table', tags=['silver']) }}

WITH source AS (
    SELECT * FROM {{ ref('raw_subscriptions') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY subscription_id ORDER BY _loaded_at DESC) AS rn
    FROM source
    WHERE subscription_id IS NOT NULL AND subscription_id != ''
),

cleaned AS (
    SELECT
        subscription_id::UUID                               AS subscription_id,
        account_id::UUID                                    AS account_id,
        LOWER(TRIM(plan_id))                                AS plan_id,
        INITCAP(TRIM(plan_name))                            AS plan_name,
        LOWER(TRIM(status))                                 AS status,
        -- Normalize MRR: annual billing → divide by 12
        CASE
            WHEN LOWER(billing_cycle) = 'annual'
                THEN ROUND(NULLIF(mrr_amount, '')::NUMERIC / 12, 2)
            ELSE NULLIF(mrr_amount, '')::NUMERIC
        END                                                 AS mrr_amount,
        NULLIF(arr_amount, '')::NUMERIC                     AS arr_amount,
        LOWER(TRIM(billing_cycle))                          AS billing_cycle,
        NULLIF(seats_licensed, '')::INTEGER                 AS seats_licensed,
        NULLIF(seats_used, '')::INTEGER                     AS seats_used,
        -- Seat utilization rate
        CASE
            WHEN NULLIF(seats_licensed, '')::INTEGER > 0
                THEN ROUND(
                    NULLIF(seats_used, '')::NUMERIC /
                    NULLIF(seats_licensed, '')::NUMERIC, 4
                )
            ELSE NULL
        END                                                 AS seat_utilization_rate,
        NULLIF(trial_start_date, '')::DATE                  AS trial_start_date,
        NULLIF(trial_end_date, '')::DATE                    AS trial_end_date,
        NULLIF(start_date, '')::DATE                        AS start_date,
        NULLIF(end_date, '')::DATE                          AS end_date,
        NULLIF(cancelled_at, '')::TIMESTAMPTZ               AS cancelled_at,
        NULLIF(created_at, '')::TIMESTAMPTZ                 AS created_at,
        NULLIF(updated_at, '')::TIMESTAMPTZ                 AS updated_at,
        -- Derived fields
        CASE WHEN NULLIF(trial_start_date, '') IS NOT NULL THEN TRUE ELSE FALSE END AS had_trial,
        CASE WHEN LOWER(status) = 'active' THEN TRUE ELSE FALSE END                AS is_active,
        _loaded_at
    FROM deduped
    WHERE rn = 1
      AND account_id IS NOT NULL
      AND account_id != ''
)

SELECT * FROM cleaned
