/*
  =============================================================================
  Macro: Safe Divide
  =============================================================================
  Division-by-zero safe division with optional rounding.
  Returns NULL instead of raising an error when denominator is 0 or NULL.

  Used in:
    - fact_daily_prices (daily_return calculation)
    - fact_exchange_rates (rate_change could use this pattern)
    - Any future calculated measure involving division

  Usage:
    {{ safe_divide('numerator_column', 'denominator_column', 6) }}

  Output SQL:
    CASE
      WHEN denominator_column IS NOT NULL AND denominator_column != 0
      THEN ROUND(numerator_column / denominator_column, 6)
      ELSE NULL
    END
  =============================================================================
*/

{% macro safe_divide(numerator, denominator, precision=6) %}
    CASE
        WHEN {{ denominator }} IS NOT NULL AND {{ denominator }} != 0
        THEN ROUND(CAST({{ numerator }} AS FLOAT) / CAST({{ denominator }} AS FLOAT), {{ precision }})
        ELSE NULL
    END
{% endmacro %}

