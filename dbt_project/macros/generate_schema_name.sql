/*
  =============================================================================
  Custom Schema Name Macro
  =============================================================================
  Override dbt's default schema naming to use CLEAN schema names.

  Default dbt behavior:
    +schema: staging  → ANALYTICS.STAGING_staging  (ugly, redundant)

  Our behavior:
    +schema: staging  → ANALYTICS.STAGING          (clean, matches our design)

  Logic:
    - If a custom schema is specified → use it as-is (uppercase)
    - If no custom schema → use the default schema from profiles.yml
  =============================================================================
*/

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema | upper }}
    {%- else -%}
        {{ custom_schema_name | trim | upper }}
    {%- endif -%}
{%- endmacro %}

