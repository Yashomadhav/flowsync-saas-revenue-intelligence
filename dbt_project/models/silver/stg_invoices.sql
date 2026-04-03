-- Silver: stg_invoices
-- Cleaned invoices with payment status enrichment
{{ config(materialized='table', tags=['silver']) }}

WITH source AS (
    SELECT * FROM {{ ref('raw_invoices') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY invoice_id ORDER BY _loaded_at DESC) AS rn
    FROM source
    WHERE invoice_id IS NOT NULL AND invoice_id != ''
),

cleaned AS (
    SELECT
        invoice_id::UUID                                    AS invoice_id,
        account_id::UUID                                    AS account_id,
        subscription_id::UUID                               AS subscription_id,
        NULLIF(amount, '')::NUMERIC                         AS amount,
        COALESCE(NULLIF(currency, ''), 'USD')               AS currency,
        LOWER(TRIM(status))                                 AS status,
        NULLIF(due_date, '')::DATE                          AS due_date,
        NULLIF(paid_date, '')::DATE                         AS paid_date,
        NULLIF(failed_date, '')::DATE                       AS failed_date,
        NULLIF(failure_reason, '')                          AS failure_reason,
        NULLIF(invoice_date, '')::DATE                      AS invoice_date,
        DATE_TRUNC('month', NULLIF(invoice_date, '')::DATE) AS invoice_month,
        NULLIF(created_at, '')::TIMESTAMPTZ                 AS created_at,
        -- Derived fields
        CASE WHEN LOWER(status) = 'paid'    THEN TRUE ELSE FALSE END AS is_paid,
        CASE WHEN LOWER(status) = 'failed'  THEN TRUE ELSE FALSE END AS is_failed,
        CASE WHEN LOWER(status) = 'pending' THEN TRUE ELSE FALSE END AS is_pending,
        -- Days to pay
        CASE
            WHEN NULLIF(paid_date, '') IS NOT NULL AND NULLIF(invoice_date, '') IS NOT NULL
                THEN NULLIF(paid_date, '')::DATE - NULLIF(invoice_date, '')::DATE
            ELSE NULL
        END                                                 AS days_to_pay,
        _loaded_at
    FROM deduped
    WHERE rn = 1
      AND account_id IS NOT NULL AND account_id != ''
)

SELECT * FROM cleaned
