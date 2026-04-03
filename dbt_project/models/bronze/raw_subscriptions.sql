-- Bronze: raw_subscriptions
{{ config(materialized='view', tags=['bronze']) }}

SELECT
    _id, subscription_id, account_id, plan_id, plan_name, status,
    mrr_amount, arr_amount, billing_cycle, seats_licensed, seats_used,
    trial_start_date, trial_end_date, start_date, end_date, cancelled_at,
    created_at, updated_at, _loaded_at
FROM {{ source('raw', 'raw_subscriptions') }}
