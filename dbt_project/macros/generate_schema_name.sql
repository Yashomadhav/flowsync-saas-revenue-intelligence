{#
  generate_schema_name.sql
  Overrides dbt's default schema naming to use custom schema names directly
  without prepending the target schema prefix.

  Default dbt behavior: <target_schema>_<custom_schema>
  This override: <custom_schema> (in prod) or <target_schema>_<custom_schema> (in dev)

  Usage in dbt_project.yml:
    models:
      flowsync_bi:
        staging:
          +schema: staging
        intermediate:
          +schema: intermediate
        marts:
          +schema: marts
#}

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}

    {%- if target.name == 'prod' -%}
        {#- In production: use the custom schema name directly -#}
        {%- if custom_schema_name is none -%}
            {{ default_schema }}
        {%- else -%}
            {{ custom_schema_name | trim }}
        {%- endif -%}

    {%- else -%}
        {#- In dev/ci: prefix with target schema to isolate environments -#}
        {%- if custom_schema_name is none -%}
            {{ default_schema }}
        {%- else -%}
            {{ default_schema }}_{{ custom_schema_name | trim }}
        {%- endif -%}
    {%- endif -%}

{%- endmacro %}
