-- Bronze: raw_tickets
{{ config(materialized='view', tags=['bronze']) }}

SELECT
    _id, ticket_id, account_id, user_id, subject, category,
    priority, status, csat_score, created_at, resolved_at,
    first_response_at, _loaded_at
FROM {{ source('raw', 'raw_tickets') }}
