/*
  =============================================================================
  Macro: Cents to Dollars
  =============================================================================
  Converts a monetary amount from cents (integer) to dollars (decimal).
  DRY pattern for currency formatting — define once, use everywhere.

  Many source systems store amounts in cents to avoid floating-point issues.
  This macro standardizes the conversion project-wide.

  Usage:
    {{ cents_to_dollars('amount_in_cents') }}

  Output SQL:
    ROUND(CAST(amount_in_cents AS DECIMAL(18,2)) / 100, 2)

  Note: Our current dataset (Kaggle) already stores amounts in dollars,
  so this macro is included as a reusable pattern for future sources
  or portfolio demonstration of the DRY principle.
  =============================================================================
*/

{% macro cents_to_dollars(column_name) %}
    ROUND(CAST({{ column_name }} AS DECIMAL(18,2)) / 100, 2)
{% endmacro %}

