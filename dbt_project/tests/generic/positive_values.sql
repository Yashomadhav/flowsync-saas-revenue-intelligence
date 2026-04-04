{#
  positive_values.sql
  Generic dbt test: asserts that all values in a column are > 0.
  Fails if any row has a value <= 0.

  Usage in schema.yml:
    columns:
      - name: mrr
        tests:
          - positive_values
#}

{% test positive_values(model, column_name) %}

select
    {{ column_name }},
    count(*) as failing_rows
from {{ model }}
where {{ column_name }} <= 0
group by {{ column_name }}

{% endtest %}
