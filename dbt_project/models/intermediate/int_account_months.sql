-- =============================================================================
-- int_account_months.sql
-- Intermediate: Account × Month spine
-- Creates one row per account per calendar month they were active.
-- This is the foundational grain for all monthly aggregations.
-- =============================================================================

{{ config(materialized='incremental', unique_key='account_month_key') }}

with accounts as (
    select
        account_id,
        company_name,
        industry,
        company_size,
        region,
        country,
        acquisition_channel,
        account_status,
        is_active,
        created_at::date as account_created_date
    from {{ ref('stg_accounts') }}
),

-- Generate a month spine from the earliest account creation to today
month_spine as (
    select distinct month_start_date, month_key
    from {{ ref('stg_calendar') }}
    where calendar_date = month_start_date   -- one row per month
      and month_start_date <= date_trunc('month', current_date)
      and month_start_date >= '2022-01-01'
),

-- Cross join accounts × months, filtered to months after account creation
account_months as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['a.account_id', 'm.month_key']) }}
                                                        as account_month_key,

        -- Dimensions
        a.account_id,
        a.company_name,
        a.industry,
        a.company_size,
        a.region,
        a.country,
        a.acquisition_channel,
        a.account_status,
        a.is_active,
        a.account_created_date,

        -- Month dimensions
        m.month_start_date,
        m.month_key,
        extract(year  from m.month_start_date)::integer as month_year,
        extract(month from m.month_start_date)::integer as month_num,

        -- Cohort: the month the account was created
        to_char(a.account_created_date, 'YYYY-MM')      as cohort_month,
        date_trunc('month', a.account_created_date)::date as cohort_month_date,

        -- Months since account creation (for cohort analysis)
        (extract(year  from m.month_start_date) - extract(year  from date_trunc('month', a.account_created_date))) * 12
        + (extract(month from m.month_start_date) - extract(month from date_trunc('month', a.account_created_date)))
                                                        as months_since_created,

        -- Is this the account's first month?
        case
            when to_char(m.month_start_date, 'YYYY-MM') = to_char(a.account_created_date, 'YYYY-MM')
            then true else false
        end                                             as is_first_month

    from accounts a
    cross join month_spine m
    where m.month_start_date >= date_trunc('month', a.account_created_date)
)

select * from account_months

{% if is_incremental() %}
    where month_start_date >= (select max(month_start_date) - interval '2 months' from {{ this }})
{% endif %}
