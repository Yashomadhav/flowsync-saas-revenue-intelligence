-- Bronze: raw_usage_events
{{ config(materialized='view', tags=['bronze']) }}

SELECT
    _id, event_id, account_id, user_id, feature_name, event_type,
    session_id, duration_seconds, event_date, created_at, _loaded_at
FROM {{ source('raw', 'raw_usage_events') }}
