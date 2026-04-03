-- Bronze: raw_invoices
{{ config(materialized='view', tags=['bronze']) }}

SELECT
    _id, invoice_id, account_id, subscription_id, amount, currency,
    status, due_date, paid_date, failed_date, failure_reason,
    invoice_date, created_at, _loaded_at
FROM {{ source('raw', 'raw_invoices') }}
