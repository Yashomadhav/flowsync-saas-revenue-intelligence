-- =============================================================================
-- stg_calendar.sql
-- Silver layer: date dimension / calendar spine
-- Generates a complete date spine for the analytics period
-- =============================================================================

{{ config(materialized='table') }}

with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2022-01-01' as date)",
        end_date="cast(current_date + interval '365 days' as date)"
    ) }}
),

calendar as (
    select
        -- Primary key
        cast(date_day as date)                                  as calendar_date,

        -- Date parts
        extract(year  from date_day)::integer                   as year,
        extract(month from date_day)::integer                   as month,
        extract(day   from date_day)::integer                   as day_of_month,
        extract(dow   from date_day)::integer                   as day_of_week,       -- 0=Sun, 6=Sat
        extract(doy   from date_day)::integer                   as day_of_year,
        extract(week  from date_day)::integer                   as week_of_year,
        extract(quarter from date_day)::integer                 as quarter,

        -- Month / Year keys (for joining to monthly aggregates)
        to_char(date_day, 'YYYY-MM')                            as month_key,
        to_char(date_day, 'YYYY-MM-01')::date                  as month_start_date,
        (date_trunc('month', date_day) + interval '1 month - 1 day')::date
                                                                as month_end_date,

        -- Quarter keys
        to_char(date_day, 'YYYY') || '-Q' || extract(quarter from date_day)::text
                                                                as quarter_key,
        date_trunc('quarter', date_day)::date                   as quarter_start_date,

        -- Year key
        extract(year from date_day)::integer                    as fiscal_year,

        -- Human-readable labels
        to_char(date_day, 'Month YYYY')                         as month_name_long,
        to_char(date_day, 'Mon YYYY')                           as month_name_short,
        to_char(date_day, 'Day')                                as day_name_long,
        to_char(date_day, 'Dy')                                 as day_name_short,

        -- Boolean flags
        case when extract(dow from date_day) in (0, 6) then true else false end
                                                                as is_weekend,
        case when extract(dow from date_day) not in (0, 6) then true else false end
                                                                as is_weekday,
        case when date_day = date_trunc('month', date_day) then true else false end
                                                                as is_month_start,
        case when date_day = date_trunc('month', date_day) + interval '1 month - 1 day'
             then true else false end                           as is_month_end,
        case when date_day = date_trunc('quarter', date_day) then true else false end
                                                                as is_quarter_start,
        case when date_day <= current_date then true else false end
                                                                as is_past_or_today,
        case when date_day = current_date then true else false end
                                                                as is_today,

        -- Relative periods (for rolling window calculations)
        (current_date - cast(date_day as date))::integer        as days_ago,
        (extract(year from age(current_date, date_day)) * 12
         + extract(month from age(current_date, date_day)))::integer
                                                                as months_ago,

        -- Fiscal period (same as calendar for FlowSync)
        extract(year from date_day)::integer                    as fiscal_year_num,
        extract(quarter from date_day)::integer                 as fiscal_quarter_num,
        extract(month from date_day)::integer                   as fiscal_month_num

    from date_spine
)

select * from calendar
order by calendar_date
