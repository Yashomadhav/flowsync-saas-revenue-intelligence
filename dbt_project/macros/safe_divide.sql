{#
  safe_divide(numerator, denominator)
  Returns numerator / denominator, or NULL if denominator is zero or NULL.
  Prevents division-by-zero errors across all models.

  Usage:
    {{ safe_divide('revenue', 'accounts') }}
    {{ safe_divide('mrr::float', 'nullif(starting_mrr, 0)') }}
#}

{% macro safe_divide(numerator, denominator) %}
    case
        when ({{ denominator }}) = 0 or ({{ denominator }}) is null
        then null
        else ({{ numerator }}) / ({{ denominator }})
    end
{% endmacro %}
